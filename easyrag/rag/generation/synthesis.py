"""Answer-synthesis helpers for teaching-first generation flows."""

from __future__ import annotations

import re
from typing import Any

from easyrag.rag.generation.output import split_answer_sections
from easyrag.rag.generation.selection import (
    has_citation_marker,
    normalize_citation_snippet,
)
from easyrag.rag.types import AnswerParam
from easyrag.rag.utils import tokenize

_ABSTAIN_TEXT = "I cannot answer the question from the retrieved evidence alone."
_SUPPORTING_CITATIONS_HEADER = "Supporting citations:"


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", normalize_citation_snippet(text))
    return [part.strip() for part in parts if part.strip()]


def _build_reference_lines(citations: list[dict[str, str]]) -> list[str]:
    references: list[str] = []
    for index, citation in enumerate(citations, start=1):
        references.append(
            f"[{index}] {citation.get('title', 'Document')} - {citation.get('location', '')}"
        )
    return references


def _citations_support_question(question: str, citations: list[dict[str, str]]) -> bool:
    question_tokens = {token for token in tokenize(question) if len(token) > 3}
    if not question_tokens:
        return bool(citations)
    required_overlap = min(2, len(question_tokens))
    for citation in citations:
        snippet_tokens = {
            token for token in tokenize(citation.get("snippet", "")) if len(token) > 3
        }
        if len(question_tokens & snippet_tokens) >= required_overlap:
            return True
    return False


def _classify_evidence_support(
    question: str, citations: list[dict[str, str]]
) -> str:
    """Return one coarse support label for the selected evidence."""

    if not citations:
        return "none"
    if _citations_support_question(question, citations):
        return "supported"
    return "weak"


def _ensure_citation_markers(
    answer: str, citations: list[dict[str, str]], *, require_citations: bool
) -> str:
    if not citations or not require_citations:
        return answer
    if has_citation_marker(answer):
        return answer
    references = _build_reference_lines(citations)
    return (
        answer.rstrip()
        + "\n\n"
        + _SUPPORTING_CITATIONS_HEADER
        + "\n"
        + "\n".join(references)
    )


def _fallback_answer(
    question: str, citations: list[dict[str, str]], param: AnswerParam
) -> str:
    if not citations:
        return (
            _ABSTAIN_TEXT
            if param.allow_abstain
            else "No grounded citations were available for this question."
        )

    keywords = [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_]+", question)
        if len(token) > 3
    ]
    ranked: list[tuple[int, int, str, dict[str, str]]] = []
    for index, citation in enumerate(citations, start=1):
        for sentence in _split_sentences(citation.get("snippet", "")):
            lowered = sentence.lower()
            score = sum(lowered.count(keyword) for keyword in keywords)
            if score > 0:
                ranked.append((score, index, sentence, citation))

    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    selected_sentences: list[tuple[int, str, dict[str, str]]] = []
    seen_sentences: set[str] = set()
    for _, index, sentence, citation in ranked:
        if sentence in seen_sentences:
            continue
        selected_sentences.append((index, sentence, citation))
        seen_sentences.add(sentence)
        if len(selected_sentences) == min(3, len(citations)):
            break

    if not selected_sentences and citations:
        selected_sentences.append(
            (
                1,
                normalize_citation_snippet(citations[0].get("snippet", "")),
                citations[0],
            )
        )

    if not selected_sentences:
        return (
            _ABSTAIN_TEXT
            if param.allow_abstain
            else "No grounded citations were available for this question."
        )

    selected_sentences.sort(key=lambda item: item[0])
    answer_body = " ".join(
        sentence if sentence.endswith((".", "!", "?")) else f"{sentence}."
        for _, sentence, _ in selected_sentences
    )
    used_indices: list[int] = []
    for index, _, _ in selected_sentences:
        if index not in used_indices:
            used_indices.append(index)
    if param.require_citations:
        answer_body = (
            answer_body.rstrip()
            + " "
            + " ".join(f"[{index}]" for index in used_indices)
        )
    return _ensure_citation_markers(
        answer_body.strip(), citations, require_citations=param.require_citations
    )


def synthesize_answer(
    question: str,
    citations: list[dict[str, str]],
    *,
    prompt: str,
    param: AnswerParam,
    answer_model_func: Any | None,
) -> tuple[str, dict[str, Any]]:
    """Synthesize one answer from a packed evidence set."""

    evidence_mode = param.evidence_mode.strip().lower()
    evidence_support = _classify_evidence_support(question, citations)
    base_metadata: dict[str, Any] = {
        "evidence_support": evidence_support,
        "additional_context": "",
        "additional_context_present": False,
        "prior_knowledge_used": False,
    }

    if not citations:
        fallback = _fallback_answer(question, citations, param)
        metadata = {
            "abstained": fallback == _ABSTAIN_TEXT,
            "answer_model_used": False,
            "fallback_used": True,
            **base_metadata,
        }
        if param.allow_abstain:
            metadata["insufficient_evidence"] = True
        return fallback, metadata
    if (
        citations
        and evidence_mode == "grounded_only"
        and evidence_support != "supported"
        and param.allow_abstain
    ):
        return _ABSTAIN_TEXT, {
            "abstained": True,
            "answer_model_used": False,
            "fallback_used": True,
            "insufficient_evidence": True,
            **base_metadata,
        }
    if (
        citations
        and evidence_mode == "grounded_plus_prior"
        and evidence_support == "weak"
        and answer_model_func is None
        and param.allow_abstain
    ):
        return _ABSTAIN_TEXT, {
            "abstained": True,
            "answer_model_used": False,
            "fallback_used": True,
            "insufficient_evidence": True,
            **base_metadata,
        }

    if answer_model_func is not None:
        try:
            generated = answer_model_func(
                prompt,
                question=question,
                citations=citations,
                style=param.style,
            )
            answer, additional_context = split_answer_sections(str(generated or ""))
            if answer:
                grounded_answer = _ensure_citation_markers(
                    answer, citations, require_citations=param.require_citations
                )
                return grounded_answer, {
                    **base_metadata,
                    "abstained": grounded_answer == _ABSTAIN_TEXT,
                    "answer_model_used": True,
                    "fallback_used": False,
                    "additional_context": additional_context,
                    "additional_context_present": bool(additional_context),
                    "prior_knowledge_used": bool(additional_context),
                }
        except Exception as exc:
            fallback = _fallback_answer(question, citations, param)
            return fallback, {
                "abstained": fallback == _ABSTAIN_TEXT,
                "answer_model_used": True,
                "fallback_used": True,
                "answer_model_error": str(exc),
                **base_metadata,
            }

    fallback = _fallback_answer(question, citations, param)
    return fallback, {
        "abstained": fallback == _ABSTAIN_TEXT,
        "answer_model_used": False,
        "fallback_used": True,
        **base_metadata,
    }
