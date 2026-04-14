"""Vector synchronization helpers derived from graph state."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG


def _build_entity_vector_payload(node: dict[str, Any]) -> dict[str, Any]:
    """Convert one aggregated entity node into an entity vector record."""

    entity_types = list(node.get("entity_types", []) or [])
    description = str(node.get("description", "")).strip()
    text_parts = [str(node.get("label", "")).strip()]
    if entity_types:
        text_parts.append(f"types: {', '.join(entity_types)}")
    if description:
        text_parts.append(description)
    return {
        "id": str(node["id"]),
        "text": ". ".join(part for part in text_parts if part),
        "metadata": {
            "label": str(node.get("label", "")),
            "kind": "entity",
            "entity_types": entity_types,
            "description": description,
            "aliases": list(node.get("aliases", []) or []),
            "doc_ids": list(node.get("doc_ids", []) or []),
            "provenance": list(node.get("provenance", []) or []),
        },
    }


async def sync_entity_vectors(
    rag: "EasyRAG",
    entity_ids: list[str],
    *,
    removed_entity_ids: list[str] | None = None,
) -> dict[str, int]:
    """Synchronize aggregated entity vectors from the graph layer."""

    deleted = 0
    if removed_entity_ids:
        deleted = await rag.vector_storage.delete("entity", removed_entity_ids)

    payloads: list[dict[str, Any]] = []
    for entity_id in dict.fromkeys(entity_ids):
        node = await rag.graph_storage.get_node(entity_id)
        if node is None or str(node.get("kind", "")) != "entity":
            continue
        payloads.append(_build_entity_vector_payload(node))
    if payloads:
        await rag.vector_storage.upsert("entity", payloads)
    return {"upserted": len(payloads), "deleted": deleted}


def _build_relation_vector_payload(
    relation: dict[str, Any],
    source_node: dict[str, Any],
    target_node: dict[str, Any],
) -> dict[str, Any]:
    """Convert one semantic relation record into a relation vector record."""

    source_label = str(
        source_node.get("label", relation.get("source_entity_id", ""))
    ).strip()
    target_label = str(
        target_node.get("label", relation.get("target_entity_id", ""))
    ).strip()
    relation_name = str(relation.get("relation", "related_to")).strip() or "related_to"
    description = str(relation.get("description", "")).strip()
    text = (
        description
        or f"{source_label} {relation_name.replace('_', ' ')} {target_label}"
    )
    metadata = dict(relation.get("metadata", {}))
    metadata.update(
        {
            "kind": "relation",
            "relation": relation_name,
            "source_entity_id": str(relation.get("source_entity_id", "")),
            "target_entity_id": str(relation.get("target_entity_id", "")),
            "source_label": source_label,
            "target_label": target_label,
            "provenance": list(relation.get("provenance", []) or []),
        }
    )
    return {
        "id": str(relation["id"]),
        "text": text,
        "metadata": metadata,
    }


async def sync_relation_vectors(
    rag: "EasyRAG",
    relation_ids: list[str],
    *,
    removed_relation_ids: list[str] | None = None,
) -> dict[str, int]:
    """Synchronize semantic relation vectors from graph relation records."""

    deleted = 0
    if removed_relation_ids:
        deleted = await rag.vector_storage.delete("relation", removed_relation_ids)

    payloads: list[dict[str, Any]] = []
    for relation_id in dict.fromkeys(relation_ids):
        relation = await rag.graph_storage.get_relation(relation_id)
        if relation is None:
            continue
        source_node = await rag.graph_storage.get_node(
            str(relation.get("source_entity_id", ""))
        )
        target_node = await rag.graph_storage.get_node(
            str(relation.get("target_entity_id", ""))
        )
        if source_node is None or target_node is None:
            continue
        payloads.append(
            _build_relation_vector_payload(relation, source_node, target_node)
        )
    if payloads:
        await rag.vector_storage.upsert("relation", payloads)
    return {"upserted": len(payloads), "deleted": deleted}
