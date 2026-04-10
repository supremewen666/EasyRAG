"""Shared text-processing helpers for the EasyRAG subsystem."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

_HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_CODE_PATTERN = re.compile(r"`([^`]{2,64})`")
_ENTITY_PATTERN = re.compile(r"\b[A-Z][A-Za-z0-9_./-]{2,}\b|\b[a-z0-9_]+(?:_[a-z0-9_]+)+\b")
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def slugify(value: str) -> str:
    """Create a filesystem- and graph-friendly identifier suffix."""

    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "item"


def tokenize(text: str) -> list[str]:
    """Normalize text into lowercase lexical tokens."""

    return _TOKEN_PATTERN.findall(text.lower())


def summarize_document(text: str) -> str:
    """Build a short summary snippet for global retrieval."""

    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:280]


def extract_entity_candidates(text: str, metadata: dict[str, Any]) -> list[str]:
    """Extract deterministic entity candidates from one text region."""

    candidates: list[str] = []
    title = str(metadata.get("title", "")).strip()
    if title:
        candidates.append(title)

    for heading in _HEADING_PATTERN.findall(text):
        candidates.append(heading.strip())
    for code_symbol in _CODE_PATTERN.findall(text):
        candidates.append(code_symbol.strip())
    for match in _ENTITY_PATTERN.findall(text):
        candidates.append(match.strip())

    path = str(metadata.get("relative_path") or metadata.get("path") or "").strip()
    if path:
        for part in Path(path).parts:
            if part and part not in {".", ".."}:
                candidates.append(Path(part).stem or part)

    counter = Counter()
    display: dict[str, str] = {}
    for raw_candidate in candidates:
        value = raw_candidate.strip().strip("#").strip("-").strip()
        if len(value) < 3:
            continue
        normalized = re.sub(r"\s+", " ", value)
        key = normalized.lower()
        if key in {"readme", "docs", "document"}:
            continue
        counter[key] += 1
        display.setdefault(key, normalized)

    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [display[key] for key, _ in ranked[:12]]


def dedupe_strings(values: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""

    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
