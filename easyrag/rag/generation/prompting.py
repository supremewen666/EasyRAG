"""Prompt builders for retrieval-grounded answer synthesis."""

from __future__ import annotations

from easyrag.rag.types import AnswerParam


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
