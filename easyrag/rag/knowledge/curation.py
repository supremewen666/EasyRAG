"""Manual KG curation payload helpers."""

from __future__ import annotations

from typing import Any, Sequence

from easyrag.rag.utils import dedupe_strings


def build_entity_payload(
    *,
    entity_id: str,
    label: str,
    entity_types: Sequence[str] | None = None,
    description: str = "",
    aliases: Sequence[str] | None = None,
    metadata: dict[str, Any] | None = None,
    provenance: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build one manual entity node payload."""

    return {
        "id": entity_id,
        "kind": "entity",
        "label": label,
        "entity_types": list(entity_types or []),
        "description": description,
        "aliases": dedupe_strings(
            [str(value).strip() for value in list(aliases or []) if str(value).strip()]
        ),
        "metadata": dict(metadata or {}),
        "provenance": dedupe_strings(
            [
                str(value).strip()
                for value in list(provenance or [])
                if str(value).strip()
            ]
        ),
    }


async def build_relation_payload(
    graph_storage: Any,
    *,
    source_entity_id: str,
    target_entity_id: str,
    relation: str,
    relation_id: str,
    description: str = "",
    weight: float = 1.0,
    metadata: dict[str, Any] | None = None,
    provenance: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build one semantic relation record payload after validating endpoints."""

    source = await graph_storage.get_node(source_entity_id)
    target = await graph_storage.get_node(target_entity_id)
    if source is None or target is None:
        raise ValueError("Relation endpoints must refer to existing entity ids.")
    return {
        "id": relation_id,
        "source_entity_id": source_entity_id,
        "target_entity_id": target_entity_id,
        "relation": relation.strip() or "related_to",
        "description": description,
        "weight": float(weight),
        "metadata": dict(metadata or {}),
        "provenance": dedupe_strings(
            [
                str(value).strip()
                for value in list(provenance or [])
                if str(value).strip()
            ]
        ),
    }
