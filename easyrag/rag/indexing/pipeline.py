"""Document-to-storage ingestion helpers for canonical indexing flow."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from easyrag.support.optional_deps import Document
from easyrag.rag.indexing.chunking import chunk_documents
from easyrag.rag.knowledge.extraction import extract_chunk_knowledge
from easyrag.rag.knowledge.sync import sync_entity_vectors, sync_relation_vectors
from easyrag.rag.utils import slugify, summarize_document

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG


def _build_embedding_input(text: str, metadata: dict[str, Any]) -> str | dict[str, Any]:
    """Build embedding input that can preserve image assets for VL models."""

    image_paths = [str(path) for path in metadata.get("image_paths", []) if str(path).strip()]
    if not image_paths:
        return text
    return {
        "text": text,
        "image_paths": image_paths,
    }


def build_insert_payloads(
    rag: "EasyRAG",
    documents: list[Document],
    *,
    chunk_strategy_override: str | None = None,
) -> dict[str, Any]:
    """Transform documents into storage payloads."""

    payloads: dict[str, Any] = {
        "documents": [],
        "chunks": [],
        "summaries": [],
        "graph_nodes": [],
        "graph_edges": [],
        "vector_chunks": [],
        "vector_summaries": [],
        "relation_records": [],
        "statuses": [],
        "chunk_strategy_counts": {},
        "entity_ids": [],
        "relation_ids": [],
    }
    entity_nodes: dict[str, dict[str, Any]] = {}
    entity_document_edges: set[tuple[str, str]] = set()
    pdf_documents = 0

    all_chunks = chunk_documents(
        documents,
        config=rag.chunking_config,
        chunk_strategy_override=chunk_strategy_override,
        rag=rag,
    )
    chunks_by_doc: dict[str, list[Document]] = {}
    for chunk in all_chunks:
        chunks_by_doc.setdefault(str(chunk.metadata["doc_id"]), []).append(chunk)

    for document in documents:
        doc_id = str(document.metadata["doc_id"])
        path = str(document.metadata.get("path", ""))
        title = str(document.metadata.get("title", "Document"))
        summary_id = f"summary::{doc_id}"
        summary_text = summarize_document(document.page_content)
        source_type = str(document.metadata.get("source_type", "doc"))
        if source_type == "pdf":
            pdf_documents += 1

        payloads["documents"].append(
            {
                "id": doc_id,
                "title": title,
                "path": path,
                "relative_path": str(document.metadata.get("relative_path", path)),
                "text": document.page_content,
                "summary_id": summary_id,
                "metadata": dict(document.metadata),
            }
        )
        payloads["summaries"].append(
            {
                "id": summary_id,
                "document_id": doc_id,
                "title": f"{title} summary",
                "path": path,
                "text": summary_text,
                "metadata": {"source_type": "summary", "doc_id": doc_id, "path": path, "title": title},
            }
        )
        payloads["graph_nodes"].extend(
            [
                {"id": doc_id, "kind": "document", "label": title, "path": path, "doc_id": doc_id},
                {
                    "id": summary_id,
                    "kind": "summary",
                    "label": f"{title} summary",
                    "path": path,
                    "text": summary_text,
                    "doc_id": doc_id,
                    "document_id": doc_id,
                },
            ]
        )
        payloads["graph_edges"].append(
            {
                "source": doc_id,
                "target": summary_id,
                "relation": "document_summary",
                "relations": ["document_summary"],
                "weight": 1.0,
                "metadata": {"doc_id": doc_id},
            }
        )
        payloads["vector_summaries"].append(
            {
                "id": summary_id,
                "text": summary_text,
                "metadata": {"doc_id": doc_id, "title": title, "path": path, "kind": "summary"},
            }
        )

        chunk_count = 0
        for chunk in chunks_by_doc.get(doc_id, []):
            chunk_id = str(chunk.metadata["chunk_uid"])
            strategy = str(chunk.metadata.get("chunk_strategy", "unknown"))
            payloads["chunk_strategy_counts"][strategy] = payloads["chunk_strategy_counts"].get(strategy, 0) + 1
            chunk_count += 1
            chunk_record = {
                "id": chunk_id,
                "document_id": doc_id,
                "text": chunk.page_content,
                "title": title,
                "path": path,
                "metadata": dict(chunk.metadata),
            }
            payloads["chunks"].append(chunk_record)
            payloads["graph_nodes"].append(
                {
                    "id": chunk_id,
                    "kind": "chunk",
                    "label": f"{title} chunk {chunk.metadata.get('chunk_id', 0)}",
                    "path": path,
                    "text": chunk.page_content[:240],
                    "chunk_strategy": strategy,
                    "doc_id": doc_id,
                    "document_id": doc_id,
                }
            )
            payloads["graph_edges"].append(
                {
                    "source": doc_id,
                    "target": chunk_id,
                    "relation": "document_chunk",
                    "relations": ["document_chunk"],
                    "weight": 1.0,
                    "metadata": {"doc_id": doc_id},
                }
            )
            payloads["vector_chunks"].append(
                {
                    "id": chunk_id,
                    "text": chunk.page_content,
                    "embedding_input": _build_embedding_input(chunk.page_content, dict(chunk.metadata)),
                    "metadata": {
                        "doc_id": doc_id,
                        "title": title,
                        "path": path,
                        "kind": "chunk",
                        "chunk_strategy": strategy,
                        "page_number": chunk.metadata.get("page_number"),
                        "image_paths": list(chunk.metadata.get("image_paths", []) or []),
                    },
                }
            )

            knowledge = extract_chunk_knowledge(
                chunk.page_content,
                dict(chunk.metadata),
                kg_config=rag.kg_extraction_config,
                llm_model_func=rag.llm_model_func,
            )
            chunk_entity_ids: dict[str, str] = {}
            for entity in knowledge["entities"]:
                entity_name = str(entity.get("name", "")).strip()
                if not entity_name:
                    continue
                entity_id = f"entity::{slugify(entity_name)}"
                chunk_entity_ids[entity_name.lower()] = entity_id
                payloads["entity_ids"].append(entity_id)

                entity_node = entity_nodes.setdefault(
                    entity_id,
                    {
                        "id": entity_id,
                        "kind": "entity",
                        "label": entity_name,
                        "owners": {},
                    },
                )
                entity_node["owners"].setdefault(doc_id, {"count": 0, "types": [], "descriptions": []})
                owner = entity_node["owners"][doc_id]
                owner["count"] = int(owner.get("count", 0)) + 1
                owner["types"] = sorted(
                    set(list(owner.get("types", [])) + [str(entity.get("type", "")).strip().lower()])
                    - {""}
                )
                description = str(entity.get("description", "")).strip()
                if description and description not in owner["descriptions"]:
                    owner["descriptions"].append(description)

                if (entity_id, doc_id) not in entity_document_edges:
                    payloads["graph_edges"].append(
                        {
                            "source": entity_id,
                            "target": doc_id,
                            "relation": "entity_document",
                            "relations": ["entity_document"],
                            "weight": 1.0,
                            "metadata": {"doc_id": doc_id},
                        }
                    )
                    entity_document_edges.add((entity_id, doc_id))

                payloads["graph_edges"].append(
                    {
                        "source": entity_id,
                        "target": chunk_id,
                        "relation": "entity_chunk",
                        "relations": ["entity_chunk"],
                        "weight": 1.0,
                        "metadata": {"doc_id": doc_id},
                    }
                )

            for relation in knowledge["relations"]:
                source_id = chunk_entity_ids.get(str(relation.get("source", "")).strip().lower())
                target_id = chunk_entity_ids.get(str(relation.get("target", "")).strip().lower())
                if not source_id or not target_id or source_id == target_id:
                    continue
                relation_name = str(relation.get("relation", "related_to")).strip() or "related_to"
                relation_description = str(relation.get("description", "")).strip()
                relation_id = f"relation::{slugify(f'{chunk_id}::{source_id}::{relation_name}::{target_id}')}"
                payloads["relation_records"].append(
                    {
                        "id": relation_id,
                        "source_entity_id": source_id,
                        "target_entity_id": target_id,
                        "relation": relation_name,
                        "description": relation_description,
                        "weight": 1.0,
                        "metadata": {
                            "chunk_id": chunk_id,
                            "path": path,
                            "title": title,
                            "kind": "relation",
                            "doc_id": doc_id,
                        },
                        "provenance": [doc_id],
                    }
                )
                payloads["relation_ids"].append(relation_id)

        payloads["statuses"].append(
            {
                "document_id": doc_id,
                "status": "indexed",
                "metadata": {"path": path, "chunk_count": chunk_count},
            }
        )

    payloads["graph_nodes"].extend(entity_nodes.values())
    payloads["pdf_documents"] = pdf_documents
    payloads["entity_ids"] = list(dict.fromkeys(payloads["entity_ids"]))
    payloads["relation_ids"] = list(dict.fromkeys(payloads["relation_ids"]))
    return payloads


async def ingest_documents(rag: "EasyRAG", documents: list[Document]) -> dict[str, int]:
    """Insert documents into the EasyRAG workspace."""

    doc_ids = list(
        dict.fromkeys(
            str(document.metadata.get("doc_id", "")).strip()
            for document in documents
            if str(document.metadata.get("doc_id", "")).strip()
        )
    )
    if doc_ids:
        await rag.adelete_documents(doc_ids)

    payloads = build_insert_payloads(rag, documents)
    await rag.kv_storage.upsert_documents(payloads["documents"])
    await rag.kv_storage.upsert_chunks(payloads["chunks"])
    await rag.kv_storage.upsert_summaries(payloads["summaries"])
    await rag.vector_storage.upsert("chunk", payloads["vector_chunks"])
    await rag.vector_storage.upsert("summary", payloads["vector_summaries"])
    await rag.graph_storage.upsert_nodes(payloads["graph_nodes"])
    await rag.graph_storage.upsert_edges(payloads["graph_edges"])
    await rag.graph_storage.upsert_relation_records(payloads["relation_records"])
    entity_vector_stats = await sync_entity_vectors(rag, payloads["entity_ids"])
    relation_vector_stats = await sync_relation_vectors(rag, payloads["relation_ids"])
    for status in payloads["statuses"]:
        await rag.doc_status_storage.mark_status(status["document_id"], status["status"], metadata=status["metadata"])
    return {
        "documents": len(payloads["documents"]),
        "chunks": len(payloads["chunks"]),
        "entities": entity_vector_stats["upserted"],
        "relations": relation_vector_stats["upserted"],
        "pdf_documents": payloads["pdf_documents"],
    }


__all__ = ["build_insert_payloads", "ingest_documents"]
