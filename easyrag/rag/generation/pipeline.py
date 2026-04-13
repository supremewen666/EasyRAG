"""End-to-end generation pipeline built on top of ``QueryResult``."""

from __future__ import annotations

from typing import Any

from easyrag.rag.generation.packing import build_context_block
from easyrag.rag.generation.prompting import build_generation_prompt
from easyrag.rag.generation.selection import select_answer_citations
from easyrag.rag.generation.synthesis import synthesize_answer
from easyrag.rag.types import AnswerParam, AnswerResult, QueryResult


def generate_answer(
    question: str,
    query_result: QueryResult,
    *,
    answer_param: AnswerParam,
    answer_model_func: Any | None = None,
) -> AnswerResult:
    """Generate one grounded answer from a retrieval result."""

    selected_citations = select_answer_citations(
        query_result.citations,
        max_items=max(0, answer_param.max_citations),
        max_chars=max(0, answer_param.max_context_chars),
    )
    context_block = build_context_block(selected_citations)
    prompt = build_generation_prompt(question, context_block, answer_param)
    answer, synthesis_metadata = synthesize_answer(
        question,
        selected_citations,
        prompt=prompt,
        param=answer_param,
        answer_model_func=answer_model_func,
    )
    return AnswerResult(
        question=question,
        answer=answer,
        citations=list(query_result.citations),
        selected_citations=selected_citations,
        context_block=context_block,
        prompt=prompt,
        metadata={
            "style": answer_param.style,
            "require_citations": answer_param.require_citations,
            "allow_abstain": answer_param.allow_abstain,
            "retrieval_mode": query_result.mode,
            "retrieval_metadata": dict(query_result.metadata),
            "raw_citation_count": len(query_result.citations),
            "selected_citation_count": len(selected_citations),
            "context_chars": len(context_block),
            **synthesis_metadata,
        },
    )
