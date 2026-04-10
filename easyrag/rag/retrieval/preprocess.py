"""Query preprocessing for EasyRAG EasyRAG."""

from __future__ import annotations

import re
from dataclasses import dataclass

from easyrag.rag.types import QueryModelFunc, QueryParam


def normalize_query(query: str) -> str:
    """Normalize query whitespace and trim punctuation noise."""

    normalized = re.sub(r"\s+", " ", query).strip()
    return normalized.strip(" ?")


@dataclass
class QueryPreparation:
    """Prepared query variants for retrieval."""

    original_query: str
    normalized_query: str
    rewritten_query: str
    expanded_queries: list[str]
    retrieval_queries: list[str]


class QueryPreprocessor:
    """Apply query rewriting and MQE before retrieval."""

    def __init__(self, query_model_func: QueryModelFunc | None) -> None:
        self.query_model_func = query_model_func

    def prepare(self, query: str, param: QueryParam) -> QueryPreparation:
        """Normalize, rewrite, and expand the incoming query."""

        normalized = normalize_query(query)
        rewritten = normalized
        if param.rewrite_enabled and self.query_model_func is not None:
            try:
                candidate = self.query_model_func(
                    f"Original query: {normalized}",
                    task="rewrite",
                )
                if isinstance(candidate, str) and candidate.strip():
                    rewritten = candidate.strip()
            except Exception:
                rewritten = normalized

        expanded: list[str] = []
        if param.mqe_enabled and self.query_model_func is not None:
            try:
                generated = self.query_model_func(
                    f"Generate {param.mqe_variants} repository-search variants for: {rewritten}",
                    task="mqe",
                    count=param.mqe_variants,
                )
                if isinstance(generated, str):
                    expanded = [generated.strip()] if generated.strip() else []
                else:
                    expanded = [item.strip() for item in generated if item.strip()]
            except Exception:
                expanded = []

        retrieval_queries: list[str] = []
        for candidate in [normalized, rewritten, *expanded]:
            value = normalize_query(candidate)
            if value and value not in retrieval_queries:
                retrieval_queries.append(value)

        return QueryPreparation(
            original_query=query,
            normalized_query=normalized,
            rewritten_query=rewritten,
            expanded_queries=expanded,
            retrieval_queries=retrieval_queries or [normalized],
        )
