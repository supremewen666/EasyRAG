"""Rank fusion helpers for retrieval pipelines."""

from __future__ import annotations

from easyrag.rag.types import QueryParam
from easyrag.rag.retrieval.provenance import (
    merge_record_vector_backends,
    normalize_vector_backends,
)


def merge_ranked_records(
    rank_groups: list[tuple[float, list[dict[str, object]]]],
) -> list[dict[str, object]]:
    """Merge ranked record lists by accumulating weighted scores."""

    merged: dict[str, dict[str, object]] = {}
    for weight, records in rank_groups:
        for position, record in enumerate(records):
            record_id = str(record["id"])
            candidate = merged.setdefault(record_id, normalize_vector_backends(dict(record)))
            score = float(record.get("score", len(records) - position))
            candidate["score"] = float(candidate.get("score", 0.0)) + score * weight
            merge_record_vector_backends(candidate, record)
    return sorted(
        merged.values(), key=lambda item: float(item.get("score", 0.0)), reverse=True
    )


def rrf_fuse(
    record_groups: list[list[dict[str, object]]], *, k: int = 60
) -> list[dict[str, object]]:
    """Fuse multiple ranked lists with reciprocal rank fusion."""

    merged: dict[str, dict[str, object]] = {}
    for records in record_groups:
        for rank, record in enumerate(records, start=1):
            record_id = str(record["id"])
            candidate = merged.setdefault(record_id, normalize_vector_backends(dict(record)))
            candidate["score"] = float(candidate.get("score", 0.0)) + 1.0 / (k + rank)
            merge_record_vector_backends(candidate, record)
    return sorted(
        merged.values(), key=lambda item: float(item.get("score", 0.0)), reverse=True
    )


def trim_records(
    records: list[dict[str, object]], limit: int
) -> list[dict[str, object]]:
    """Keep the leading ranked records."""

    return records[: max(limit, 0)]


def combine_mode_results(
    param: QueryParam, *groups: tuple[float, list[dict[str, object]]]
) -> list[dict[str, object]]:
    """Combine mode-level result groups using the requested fusion strategy."""

    records = [group for _, group in groups]
    if param.retrieval_fusion == "rrf":
        return rrf_fuse(records)
    return merge_ranked_records(list(groups))
