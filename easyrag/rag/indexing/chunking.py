"""Canonical chunking module for teaching-first indexing flow."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from easyrag.support.optional_deps import Document
from easyrag.rag.indexing.chunking_core import (
    ChunkingConfig,
    build_chunker_registry,
    semantic_chunk,
    select_chunk_strategy,
    sliding_window_chunk,
    structured_chunk,
)

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG

_HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def document_prefers_structured(document: Document) -> bool:
    """Return whether a document likely benefits from structure-aware chunking."""

    path = str(document.metadata.get("path", "")).lower()
    if path.endswith((".md", ".mdx", ".rst")):
        return True
    if path.endswith(".pdf") and _HEADING_PATTERN.search(document.page_content):
        return True
    return str(document.metadata.get("title", "")).lower().startswith("readme")


def chunk_with_strategy(
    document: Document,
    *,
    config: ChunkingConfig,
    strategy: str,
    rag: "EasyRAG" | None = None,
) -> list[Document]:
    """Run the selected chunking strategy with graceful fallback."""

    if rag is not None and strategy in rag.chunker_registry:
        chunker = rag.chunker_registry[strategy]
        try:
            if strategy == "semantic":
                chunks = chunker(document, config=config, embedding_func=rag.embedding_func)
            else:
                chunks = chunker(document, config=config)
            if chunks:
                return chunks
        except Exception:
            pass

    if strategy == "structured":
        chunks = structured_chunk(document, config=config)
        if chunks:
            return chunks
    if strategy == "semantic":
        chunks = semantic_chunk(document, config=config, embedding_func=None if rag is None else rag.embedding_func)
        if chunks:
            return chunks
    return sliding_window_chunk(document, config=config)


def chunk_documents(
    documents: list[Document],
    *,
    config: ChunkingConfig | None = None,
    chunk_strategy_override: str | None = None,
    rag: "EasyRAG" | None = None,
) -> list[Document]:
    """Split documents into primary-strategy chunks with overlap metadata."""

    chunking = config or ChunkingConfig()
    chunks: list[Document] = []
    for document in documents:
        strategy = chunk_strategy_override or select_chunk_strategy(document)
        if strategy == "semantic" and document_prefers_structured(document):
            strategy = "structured"
        chunks.extend(chunk_with_strategy(document, config=chunking, strategy=strategy, rag=rag))
    return chunks


__all__ = [
    "ChunkingConfig",
    "build_chunker_registry",
    "chunk_documents",
    "chunk_with_strategy",
    "document_prefers_structured",
    "semantic_chunk",
    "select_chunk_strategy",
    "sliding_window_chunk",
    "structured_chunk",
]
