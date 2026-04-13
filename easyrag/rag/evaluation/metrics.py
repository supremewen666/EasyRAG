"""Deterministic retrieval metrics for EasyRAG evaluation."""

from __future__ import annotations


def hit_rate_at_k(relevances: list[bool]) -> float:
    """Return 1.0 when any relevant item appears in the ranked list."""

    return 1.0 if any(relevances) else 0.0


def recall_at_k(relevances: list[bool], *, expected_total: int) -> float:
    """Return recall over the retrieved prefix."""

    if expected_total <= 0:
        return 0.0
    return min(sum(1 for value in relevances if value), expected_total) / expected_total


def precision_at_k(relevances: list[bool]) -> float:
    """Return precision over the retrieved prefix."""

    if not relevances:
        return 0.0
    return sum(1 for value in relevances if value) / len(relevances)


def mrr_at_k(relevances: list[bool]) -> float:
    """Return reciprocal rank of the first relevant item."""

    for index, value in enumerate(relevances, start=1):
        if value:
            return 1.0 / index
    return 0.0
