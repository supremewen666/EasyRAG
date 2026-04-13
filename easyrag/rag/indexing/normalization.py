"""Text normalization helpers for repository and manual document inputs."""

from __future__ import annotations

import re

_BLANK_LINE_PATTERN = re.compile(r"\n{3,}")


def normalize_document_text(text: str) -> str:
    """Normalize text while keeping markdown-like readability intact."""

    cleaned = str(text).replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    normalized_lines = [line.rstrip() for line in cleaned.split("\n")]
    normalized = "\n".join(normalized_lines)
    normalized = _BLANK_LINE_PATTERN.sub("\n\n", normalized)
    return normalized.strip()
