"""Rule-based answer-grounding checks for EasyRAG evaluation."""

from __future__ import annotations

import re

from easyrag.rag.generation.selection import (
    has_citation_marker,
    normalize_citation_snippet,
)
from easyrag.rag.utils import tokenize

_SUPPORTING_CITATION_LINE = re.compile(r"^\[\d+\]\s+")


def answer_abstained(answer: str) -> bool:
    """Return whether the answer is an abstention."""

    lowered = answer.lower()
    return (
        "cannot answer" in lowered
        or "insufficient evidence" in lowered
        or "no grounded citations" in lowered
    )


def answer_has_citations(answer: str) -> bool:
    """Return whether the answer contains citation markers."""

    return has_citation_marker(answer)


def split_answer_sentences(answer: str) -> list[str]:
    """Split answer text into evaluation-ready sentences."""

    lines = []
    for raw_line in answer.splitlines():
        line = raw_line.strip()
        if (
            not line
            or line == "Supporting citations:"
            or _SUPPORTING_CITATION_LINE.match(line)
        ):
            continue
        lines.append(line)
    parts: list[str] = []
    for line in lines:
        parts.extend(
            part.strip() for part in re.split(r"(?<=[.!?])\s+", line) if part.strip()
        )
    return parts


def sentence_support_ratio(answer: str, evidence_snippets: list[str]) -> float:
    """Return the fraction of answer sentences supported by evidence snippets."""

    if answer_abstained(answer):
        return 1.0
    sentences = split_answer_sentences(answer)
    if not sentences:
        return 0.0

    normalized_evidence = [
        normalize_citation_snippet(snippet).lower()
        for snippet in evidence_snippets
        if snippet.strip()
    ]
    supported = 0
    for sentence in sentences:
        normalized_sentence = normalize_citation_snippet(sentence).lower()
        sentence_tokens = [
            token for token in tokenize(normalized_sentence) if len(token) > 3
        ]
        sentence_is_supported = False
        for snippet in normalized_evidence:
            snippet_tokens = {token for token in tokenize(snippet) if len(token) > 3}
            overlap = len(snippet_tokens & set(sentence_tokens))
            if normalized_sentence in snippet or overlap >= 2:
                sentence_is_supported = True
                break
        if sentence_is_supported:
            supported += 1
    return supported / len(sentences)
