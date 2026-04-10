"""Chunking strategies for EasyRAG EasyRAG."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

import numpy as np

from easyrag.support.optional_deps import Document

_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?\.])\s+|\n{2,}")
_MARKDOWN_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class ChunkingConfig:
    """Configuration shared across all chunking strategies."""

    sliding_window_size: int = 900
    sliding_window_overlaps: tuple[int, ...] = (120, 180, 240)
    structured_max_section_chars: int = 1400
    structured_secondary_overlap: int = 140
    semantic_target_chars: int = 1100
    semantic_sentence_overlap: int = 1
    semantic_min_sentences: int = 3
    semantic_similarity_threshold: float = 0.72


def _copy_metadata(document: Document, **updates: object) -> dict[str, object]:
    """Clone document metadata and apply updates."""

    metadata = dict(document.metadata)
    metadata.update(updates)
    return metadata


def _select_sliding_overlap(length: int, overlaps: tuple[int, ...]) -> int:
    """Pick a sliding overlap based on input length."""

    if not overlaps:
        return 0
    if length <= 1200:
        return overlaps[0]
    if length <= 3000 or len(overlaps) == 1:
        return overlaps[min(1, len(overlaps) - 1)]
    return overlaps[-1]


def sliding_window_chunk(document: Document, *, config: ChunkingConfig) -> list[Document]:
    """Chunk by fixed-size character windows with adaptive overlap."""

    text = document.page_content.strip()
    if not text:
        return []
    overlap = _select_sliding_overlap(len(text), config.sliding_window_overlaps)
    overlap_policy = f"chars:{overlap}"

    chunks: list[Document] = []
    start = 0
    chunk_number = 0
    doc_id = str(document.metadata.get("doc_id", "doc::item"))
    while start < len(text):
        end = min(len(text), start + config.sliding_window_size)
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                Document(
                    page_content=chunk_text,
                    metadata=_copy_metadata(
                        document,
                        chunk_id=chunk_number,
                        chunk_uid=f"{doc_id}::chunk::{chunk_number}",
                        start_offset=start,
                        end_offset=end,
                        chunk_strategy="sliding_window",
                        overlap_policy=overlap_policy,
                    ),
                )
            )
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        chunk_number += 1
    return chunks


def structured_chunk(document: Document, *, config: ChunkingConfig) -> list[Document]:
    """Chunk by document headings, falling back to sub-windowing large sections."""

    text = document.page_content.strip()
    matches = list(_MARKDOWN_HEADING_PATTERN.finditer(text))
    if not matches:
        return []

    doc_id = str(document.metadata.get("doc_id", "doc::item"))
    chunks: list[Document] = []
    chunk_number = 0
    for index, match in enumerate(matches):
        section_start = match.start()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section_text = text[section_start:section_end].strip()
        if not section_text:
            continue
        section_title = match.group(2).strip()
        if len(section_text) <= config.structured_max_section_chars:
            chunks.append(
                Document(
                    page_content=section_text,
                    metadata=_copy_metadata(
                        document,
                        title=section_title,
                        chunk_id=chunk_number,
                        chunk_uid=f"{doc_id}::chunk::{chunk_number}",
                        start_offset=section_start,
                        end_offset=section_end,
                        chunk_strategy="structured",
                        overlap_policy="heading+none",
                    ),
                )
            )
            chunk_number += 1
            continue

        sub_document = Document(page_content=section_text, metadata=_copy_metadata(document, title=section_title, doc_id=doc_id))
        for sub_chunk in sliding_window_chunk(
            sub_document,
            config=ChunkingConfig(
                sliding_window_size=config.structured_max_section_chars,
                sliding_window_overlaps=(config.structured_secondary_overlap,),
                structured_max_section_chars=config.structured_max_section_chars,
                structured_secondary_overlap=config.structured_secondary_overlap,
                semantic_target_chars=config.semantic_target_chars,
                semantic_sentence_overlap=config.semantic_sentence_overlap,
                semantic_min_sentences=config.semantic_min_sentences,
                semantic_similarity_threshold=config.semantic_similarity_threshold,
            ),
        ):
            metadata = dict(sub_chunk.metadata)
            metadata["chunk_id"] = chunk_number
            metadata["chunk_uid"] = f"{doc_id}::chunk::{chunk_number}"
            metadata["chunk_strategy"] = "structured"
            metadata["overlap_policy"] = f"heading+chars:{config.structured_secondary_overlap}"
            chunks.append(Document(page_content=sub_chunk.page_content, metadata=metadata))
            chunk_number += 1
    return chunks


def semantic_chunk(
    document: Document,
    *,
    config: ChunkingConfig,
    embedding_func: Callable[[list[str]], list[list[float]]] | None,
) -> list[Document]:
    """Chunk by semantic boundaries derived from sentence embeddings."""

    text = document.page_content.strip()
    sentences = [part.strip() for part in _SENTENCE_SPLIT_PATTERN.split(text) if part.strip()]
    if len(sentences) < config.semantic_min_sentences or embedding_func is None:
        return []

    try:
        embeddings = np.array(embedding_func(sentences), dtype=np.float32)
    except Exception:
        return []
    if embeddings.ndim != 2 or len(embeddings) != len(sentences):
        return []

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = np.divide(embeddings, np.maximum(norms, 1e-12))
    similarities = []
    for index in range(1, len(sentences)):
        similarities.append(float(np.dot(normalized[index - 1], normalized[index])))

    doc_id = str(document.metadata.get("doc_id", "doc::item"))
    chunks: list[Document] = []
    chunk_number = 0
    start_index = 0
    running_chars = 0
    for index, sentence in enumerate(sentences):
        running_chars += len(sentence)
        boundary = False
        if index > 0 and similarities[index - 1] < config.semantic_similarity_threshold:
            boundary = True
        if running_chars >= config.semantic_target_chars:
            boundary = True
        if not boundary and index < len(sentences) - 1:
            continue

        begin = max(0, start_index - config.semantic_sentence_overlap)
        chunk_sentences = sentences[begin : index + 1]
        chunk_text = " ".join(chunk_sentences).strip()
        if chunk_text:
            chunks.append(
                Document(
                    page_content=chunk_text,
                    metadata=_copy_metadata(
                        document,
                        chunk_id=chunk_number,
                        chunk_uid=f"{doc_id}::chunk::{chunk_number}",
                        chunk_strategy="semantic",
                        overlap_policy=f"sentences:{config.semantic_sentence_overlap}",
                        sentence_start=begin,
                        sentence_end=index,
                    ),
                )
            )
            chunk_number += 1
        start_index = index + 1
        running_chars = 0
    return chunks


def select_chunk_strategy(document: Document, override: str | None = None) -> str:
    """Choose the primary chunking strategy for a document."""

    if override:
        return override
    path = str(document.metadata.get("path", "")).lower()
    name = str(document.metadata.get("title", "")).lower()
    if path.endswith((".md", ".mdx", ".rst")) or name.startswith("readme"):
        return "structured"
    if path.endswith(".pdf"):
        return "semantic"
    return "semantic"


def build_chunker_registry() -> dict[str, Callable[..., list[Document]]]:
    """Return the default chunking strategy registry."""

    return {
        "sliding_window": sliding_window_chunk,
        "structured": structured_chunk,
        "semantic": semantic_chunk,
    }
