"""Helpers for tracking vector backend provenance across retrieval stages."""

from __future__ import annotations

from collections.abc import Iterable

NON_FALLBACK_VECTOR_BACKENDS = {"hnsw_embedding", "dense_embedding", "qdrant"}
_BACKEND_PRIORITY = ("hnsw_embedding", "dense_embedding", "qdrant", "fallback_token")


def _unique_preserving_order(values: Iterable[str]) -> list[str]:
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if normalized and normalized not in ordered:
            ordered.append(normalized)
    return ordered


def normalize_vector_backends(record: dict[str, object]) -> dict[str, object]:
    """Normalize one record to include vector_backends plus a primary label."""

    raw_values = record.get("vector_backends", [])
    values: list[str] = []
    if isinstance(raw_values, (list, tuple, set)):
        values.extend(str(value) for value in raw_values)
    elif str(raw_values).strip():
        values.append(str(raw_values))
    primary = str(record.get("vector_backend", "")).strip()
    if primary:
        values.append(primary)
    ordered = _order_vector_backends(_unique_preserving_order(values))
    if ordered:
        record["vector_backends"] = ordered
        record["vector_backend"] = select_primary_vector_backend(ordered)
    return record


def merge_record_vector_backends(
    base_record: dict[str, object], incoming_record: dict[str, object]
) -> dict[str, object]:
    """Merge vector backend provenance from two records in place."""

    values = _unique_preserving_order(
        list(get_record_vector_backends(base_record))
        + list(get_record_vector_backends(incoming_record))
    )
    ordered = _order_vector_backends(values)
    if ordered:
        base_record["vector_backends"] = ordered
        base_record["vector_backend"] = select_primary_vector_backend(ordered)
    return base_record


def get_record_vector_backends(record: dict[str, object]) -> tuple[str, ...]:
    """Return normalized vector backends for one record."""

    copy = normalize_vector_backends(dict(record))
    raw_values = copy.get("vector_backends", [])
    if isinstance(raw_values, (list, tuple, set)):
        return tuple(str(value) for value in raw_values if str(value).strip())
    primary = str(copy.get("vector_backend", "")).strip()
    return (primary,) if primary else ()


def collect_vector_backends(*record_groups: list[dict[str, object]]) -> set[str]:
    """Collect unique backends across one or more record groups."""

    observed: set[str] = set()
    for group in record_groups:
        for record in group:
            observed.update(get_record_vector_backends(record))
    return observed


def has_non_fallback_backend(backends: Iterable[str]) -> bool:
    """Return whether any backend is a true vector backend."""

    return any(str(value) in NON_FALLBACK_VECTOR_BACKENDS for value in backends)


def query_used_token_fallback(backends: Iterable[str]) -> bool:
    """Return whether retrieval truly degraded to token fallback."""

    normalized = {str(value).strip() for value in backends if str(value).strip()}
    return "fallback_token" in normalized and not has_non_fallback_backend(normalized)


def select_primary_vector_backend(
    backends: Iterable[str], *, default: str = "fallback_token"
) -> str:
    """Select the highest-priority backend from the provided values."""

    normalized = {str(value).strip() for value in backends if str(value).strip()}
    for candidate in _BACKEND_PRIORITY:
        if candidate in normalized:
            return candidate
    return default


def _order_vector_backends(backends: Iterable[str]) -> list[str]:
    normalized = {str(value).strip() for value in backends if str(value).strip()}
    ordered = [candidate for candidate in _BACKEND_PRIORITY if candidate in normalized]
    ordered.extend(
        sorted(value for value in normalized if value not in set(_BACKEND_PRIORITY))
    )
    return ordered


__all__ = [
    "NON_FALLBACK_VECTOR_BACKENDS",
    "collect_vector_backends",
    "get_record_vector_backends",
    "has_non_fallback_backend",
    "merge_record_vector_backends",
    "normalize_vector_backends",
    "query_used_token_fallback",
    "select_primary_vector_backend",
]
