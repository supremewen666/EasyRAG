"""Prompt builders for retrieval-grounded answer synthesis."""

from __future__ import annotations

from easyrag.rag.types import AnswerParam
from easyrag.rag.generation.output import _ADDITIONAL_CONTEXT_HEADER


def build_generation_prompt(
    question: str, context_block: str, param: AnswerParam
) -> str:
    """Build one compact answer-synthesis prompt."""

    style = param.style.strip().lower()
    if style == "extractive":
        answer_instruction = (
            "Prefer extractive phrasing and keep the wording close to the evidence."
        )
    elif style == "abstractive":
        answer_instruction = "Write a concise abstractive answer, but stay fully grounded in the evidence."
    else:
        answer_instruction = (
            "Write a concise citation-aware answer grounded in the evidence."
        )

    evidence_mode = param.evidence_mode.strip().lower()
    if evidence_mode == "grounded_only":
        instructions = [
            "You answer questions using only the retrieved evidence.",
            answer_instruction,
        ]
        if param.allow_abstain:
            instructions.append("If the evidence is incomplete, say so clearly.")
        if param.require_citations:
            instructions.append(
                "Use citation markers like [1] and [2] when you make a claim."
            )
    else:
        instructions = [
            "Use retrieved evidence as the primary source for the main answer.",
            answer_instruction,
            "Write the grounded main answer first.",
            f"If you add helpful prior knowledge that is not directly supported by retrieved evidence, place it in a separate section titled `{_ADDITIONAL_CONTEXT_HEADER}`.",
            "Do not mix unsupported supplements into the grounded main answer.",
        ]
        if param.allow_abstain:
            instructions.append(
                "If no retrieved evidence is available, say so clearly instead of relying only on prior knowledge."
            )
        if param.require_citations:
            instructions.append(
                "Use citation markers like [1] and [2] for grounded claims in the main answer."
            )

    return "\n".join(
        [
            *instructions,
            "",
            f"Question: {question}",
            "",
            "Retrieved evidence:",
            context_block,
            "",
            "Write a short grounded answer.",
        ]
    )
