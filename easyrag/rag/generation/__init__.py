"""Canonical answer-generation helpers built on top of retrieval results."""

from easyrag.rag.generation.packing import build_context_block
from easyrag.rag.generation.pipeline import generate_answer
from easyrag.rag.generation.prompting import build_generation_prompt
from easyrag.rag.generation.selection import (
    normalize_citation_snippet,
    select_answer_citations,
)
from easyrag.rag.generation.synthesis import synthesize_answer

__all__ = [
    "build_context_block",
    "build_generation_prompt",
    "generate_answer",
    "normalize_citation_snippet",
    "select_answer_citations",
    "synthesize_answer",
]
