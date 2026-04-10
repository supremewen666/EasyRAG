"""Core query and model-facing types for EasyRAG's RAG subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from easyrag.support.optional_deps import Document

QueryMode = str

DEFAULT_KG_ENTITY_TYPES: tuple[str, ...] = (
    "component",
    "module",
    "file",
    "service",
    "tool",
    "workflow",
    "concept",
    "config",
    "dependency",
    "interface",
)


@dataclass(frozen=True)
class QueryParam:
    """Configuration for one repository knowledge query."""

    mode: QueryMode = "hybrid"
    top_k: int = 8
    chunk_top_k: int = 6
    max_entity_tokens: int = 6000
    max_relation_tokens: int = 8000
    max_total_tokens: int = 30000
    enable_rerank: bool = False
    user_prompt: str = ""
    stream: bool = False
    rewrite_enabled: bool = True
    mqe_enabled: bool = True
    mqe_variants: int = 3
    retrieval_fusion: str = "rrf"
    chunk_strategy_override: str | None = None


@dataclass(frozen=True)
class KGExtractionConfig:
    """Configuration for LLM-backed graph extraction during ingestion."""

    entity_types: tuple[str, ...] = DEFAULT_KG_ENTITY_TYPES
    max_entities_per_chunk: int = 12
    max_relations_per_chunk: int = 16
    fallback_to_rules: bool = True


@dataclass
class QueryResult:
    """Structured retrieval result returned by ``EasyRAG.aquery``."""

    mode: QueryMode
    chunks: list[Document] = field(default_factory=list)
    citations: list[dict[str, str]] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


RerankerFunc = Callable[[str, list[dict[str, Any]]], list[dict[str, Any]]]
LLMFunc = Callable[..., Any]
EmbeddingFunc = Callable[[list[str]], list[list[float]]]
QueryModelFunc = Callable[..., str | list[str]]
ChunkerFunc = Callable[[Document], list[Document]]
