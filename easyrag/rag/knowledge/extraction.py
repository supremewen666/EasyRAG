"""Structured KG extraction helpers for EasyRAG ingestion."""

from __future__ import annotations

import re
from typing import Any

from easyrag.rag.types import KGExtractionConfig
from easyrag.rag.utils import dedupe_strings, extract_entity_candidates

_SNAKE_CASE_PATTERN = re.compile(r"[^a-z0-9]+")
_CONFIG_SUFFIXES = (".json", ".yaml", ".yml", ".toml", ".ini", ".env")
_FILE_SUFFIXES = (
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
    ".mdx",
    ".rst",
    ".txt",
    ".pdf",
    ".sh",
    ".sql",
)


def _clean_value(value: Any) -> str:
    """Normalize model output into one trimmed string."""

    return str(value or "").strip()


def _normalize_relation_name(value: Any) -> str:
    """Convert relation labels into compact snake_case names."""

    normalized = _SNAKE_CASE_PATTERN.sub("_", _clean_value(value).lower()).strip("_")
    return normalized or "related_to"


def _infer_rule_entity_type(name: str, allowed_types: set[str]) -> str:
    """Pick a best-effort architecture-oriented type for heuristic extraction."""

    lowered = name.lower()
    if "config" in allowed_types and (
        lowered.endswith(_CONFIG_SUFFIXES)
        or any(token in lowered for token in ("config", "setting", "env"))
    ):
        return "config"
    if "file" in allowed_types and (
        "/" in name or "\\" in name or lowered.endswith(_FILE_SUFFIXES)
    ):
        return "file"
    if "workflow" in allowed_types and any(
        token in lowered
        for token in ("workflow", "pipeline", "process", "retrieval", "ingest")
    ):
        return "workflow"
    if "service" in allowed_types and any(
        token in lowered for token in ("service", "server", "api")
    ):
        return "service"
    if "tool" in allowed_types and any(
        token in lowered for token in ("tool", "script", "cli", "command")
    ):
        return "tool"
    if "dependency" in allowed_types and any(
        token in lowered for token in ("dependency", "package", "library", "sdk")
    ):
        return "dependency"
    if "module" in allowed_types and any(
        token in lowered for token in ("module", "package", "layer")
    ):
        return "module"
    if "component" in allowed_types and any(
        token in lowered for token in ("component", "system", "engine")
    ):
        return "component"
    if "interface" in allowed_types and any(
        token in lowered for token in ("interface", "contract", "schema")
    ):
        return "interface"
    if "concept" in allowed_types:
        return "concept"
    return next(iter(sorted(allowed_types))) if allowed_types else "concept"


def _normalize_entities(
    entities: list[dict[str, Any]],
    *,
    kg_config: KGExtractionConfig,
) -> list[dict[str, str]]:
    """Filter and normalize entity payloads."""

    allowed_types = set(kg_config.entity_types)
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in entities:
        name = _clean_value(item.get("name"))
        if len(name) < 2:
            continue
        key = name.lower()
        if key in seen:
            continue
        entity_type = _clean_value(item.get("type")).lower()
        if entity_type not in allowed_types:
            entity_type = _infer_rule_entity_type(name, allowed_types)
        normalized.append(
            {
                "name": name,
                "type": entity_type,
                "description": _clean_value(item.get("description")),
            }
        )
        seen.add(key)
        if len(normalized) >= kg_config.max_entities_per_chunk:
            break
    return normalized


def _normalize_relations(
    relations: list[dict[str, Any]],
    *,
    entities: list[dict[str, str]],
    kg_config: KGExtractionConfig,
) -> list[dict[str, str]]:
    """Filter and normalize relation payloads."""

    entity_name_map = {item["name"].lower(): item["name"] for item in entities}
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in relations:
        source_key = _clean_value(item.get("source")).lower()
        target_key = _clean_value(item.get("target")).lower()
        if source_key not in entity_name_map or target_key not in entity_name_map:
            continue
        source = entity_name_map[source_key]
        target = entity_name_map[target_key]
        if source == target:
            continue
        relation = _normalize_relation_name(item.get("relation"))
        signature = (source.lower(), target.lower(), relation)
        if signature in seen:
            continue
        normalized.append(
            {
                "source": source,
                "target": target,
                "relation": relation,
                "description": _clean_value(item.get("description")),
            }
        )
        seen.add(signature)
        if len(normalized) >= kg_config.max_relations_per_chunk:
            break
    return normalized


def _fallback_extract(
    text: str,
    metadata: dict[str, Any],
    *,
    kg_config: KGExtractionConfig,
) -> dict[str, list[dict[str, str]]]:
    """Build heuristic entities and relations when the LLM path is unavailable."""

    candidates = extract_entity_candidates(text, metadata)
    entities = _normalize_entities(
        [
            {
                "name": candidate,
                "type": _infer_rule_entity_type(candidate, set(kg_config.entity_types)),
                "description": "",
            }
            for candidate in candidates
        ],
        kg_config=kg_config,
    )
    relations: list[dict[str, str]] = []
    names = [item["name"] for item in entities]
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            relations.append(
                {
                    "source": left,
                    "target": right,
                    "relation": "co_occurs",
                    "description": "",
                }
            )
            if len(relations) >= kg_config.max_relations_per_chunk:
                return {"entities": entities, "relations": relations}
    return {"entities": entities, "relations": relations}


def extract_chunk_knowledge(
    text: str,
    metadata: dict[str, Any],
    *,
    kg_config: KGExtractionConfig,
    llm_model_func: Any,
) -> dict[str, list[dict[str, str]]]:
    """Extract one chunk's entities and relations with fallback behavior."""

    llm_entities: list[dict[str, Any]] = []
    llm_relations: list[dict[str, Any]] = []
    if llm_model_func is not None:
        try:
            payload = llm_model_func(
                text,
                entity_types=list(kg_config.entity_types),
                max_entities=kg_config.max_entities_per_chunk,
                max_relations=kg_config.max_relations_per_chunk,
                metadata=metadata,
            )
            if isinstance(payload, dict):
                llm_entities = [
                    item
                    for item in payload.get("entities", [])
                    if isinstance(item, dict)
                ]
                llm_relations = [
                    item
                    for item in payload.get("relations", [])
                    if isinstance(item, dict)
                ]
        except Exception:
            llm_entities = []
            llm_relations = []

    entities = _normalize_entities(llm_entities, kg_config=kg_config)
    relations = _normalize_relations(
        llm_relations, entities=entities, kg_config=kg_config
    )
    if entities or relations:
        return {"entities": entities, "relations": relations}
    if not kg_config.fallback_to_rules:
        return {"entities": entities, "relations": relations}
    fallback = _fallback_extract(text, metadata, kg_config=kg_config)
    fallback["entities"] = [
        {
            **item,
            "description": item["description"]
            or f"Derived heuristically from {metadata.get('title', 'document')}.",
        }
        for item in fallback["entities"]
    ]
    fallback["relations"] = [
        {
            **item,
            "description": item["description"]
            or "Derived heuristically from shared chunk context.",
        }
        for item in fallback["relations"]
    ]
    return fallback


def summarize_entity_descriptions(values: list[str]) -> str:
    """Join short entity descriptions into one compact summary."""

    parts = dedupe_strings(
        [_clean_value(value) for value in values if _clean_value(value)]
    )
    return " ".join(parts[:3])[:280]
