"""Hydration and citation helpers for retrieval results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from easyrag.support.optional_deps import Document
from easyrag.rag.retrieval.provenance import (
    normalize_vector_backends,
    select_primary_vector_backend,
)

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG


async def hydrate_record(
    rag: "EasyRAG", record: dict[str, object]
) -> dict[str, object] | None:
    """Hydrate a ranked record with full text and metadata for citations/rerank."""

    record_id = str(record["id"])
    if "::chunk::" in record_id:
        chunk = await rag.kv_storage.get_chunk(record_id)
        if chunk is None:
            return None
        hydrated = {
            "id": record_id,
            "text": str(chunk.get("text", "")),
            "title": str(chunk.get("title", "")),
            "path": str(chunk.get("path", "")),
            "metadata": dict(chunk.get("metadata", {})),
            "score": float(record.get("score", 0.0)),
            "vector_backend": str(record.get("vector_backend", "")),
            "vector_backends": list(record.get("vector_backends", []) or []),
        }
        return normalize_vector_backends(hydrated)
    if record_id.startswith("summary::"):
        summary = await rag.kv_storage.get_summary(record_id)
        if summary is None:
            return None
        hydrated = {
            "id": record_id,
            "text": str(summary.get("text", "")),
            "title": str(summary.get("title", "")),
            "path": str(summary.get("path", "")),
            "metadata": dict(summary.get("metadata", {})),
            "score": float(record.get("score", 0.0)),
            "vector_backend": str(record.get("vector_backend", "")),
            "vector_backends": list(record.get("vector_backends", []) or []),
        }
        return normalize_vector_backends(hydrated)
    return normalize_vector_backends(dict(record))


async def hydrate_records(
    rag: "EasyRAG", records: list[dict[str, object]]
) -> list[dict[str, object]]:
    """Hydrate ranked records in order."""

    hydrated: list[dict[str, object]] = []
    for record in records:
        item = await hydrate_record(rag, record)
        if item is not None:
            hydrated.append(item)
    return hydrated


async def chunks_to_documents(records: list[dict[str, object]]) -> list[Document]:
    """Convert hydrated records into document objects."""

    return [
        Document(
            page_content=str(record.get("text", "")),
            metadata=dict(record.get("metadata", {})),
        )
        for record in records
        if str(record.get("text", "")).strip()
    ]


def build_citations(chunks: list[Document]) -> list[dict[str, str]]:
    """Convert hydrated documents into API-friendly citation payloads."""

    return [
        {
            "source_type": str(document.metadata.get("source_type", "doc")),
            "title": str(document.metadata.get("title", "Document")),
            "location": str(document.metadata.get("path", "")),
            "snippet": document.page_content[:400].strip(),
        }
        for document in chunks
    ]


def detect_vector_backend(records: list[dict[str, object]]) -> str:
    """Return the best backend label implied by the retrieved records."""

    vector_backends: set[str] = set()
    for item in records:
        normalized = normalize_vector_backends(dict(item))
        vector_backends.update(
            str(value)
            for value in normalized.get("vector_backends", [])
            if str(value).strip()
        )
    return select_primary_vector_backend(vector_backends)
