"""Evidence-selection helpers for answer generation."""

from __future__ import annotations

import re


def normalize_citation_snippet(text: str) -> str:
    """Normalize citation text while keeping it readable for teaching."""

    cleaned = str(text).replace("\x00", "").replace("#", " ")
    return " ".join(cleaned.split())


def select_answer_citations(
    citations: list[dict[str, str]],
    *,
    max_items: int,
    max_chars: int,
) -> list[dict[str, str]]:
    """Select a compact evidence set using item and character budgets."""

    selected: list[dict[str, str]] = []
    budget = 0
    for citation in citations:
        cleaned = dict(citation)
        snippet = normalize_citation_snippet(cleaned.get("snippet", ""))[:220]
        if not snippet:
            continue
        snippet_chars = len(snippet)
        if selected and (len(selected) >= max_items or budget + snippet_chars > max_chars):
            break
        cleaned["snippet"] = snippet
        selected.append(cleaned)
        budget += snippet_chars
    return selected


_CITATION_MARKER_PATTERN = re.compile(r"\[\d+\]")


def has_citation_marker(text: str) -> bool:
    """Return whether an answer already contains citation markers."""

    return bool(_CITATION_MARKER_PATTERN.search(text))
