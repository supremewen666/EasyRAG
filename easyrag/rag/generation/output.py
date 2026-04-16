"""Helpers for structured answer rendering and parsing."""

from __future__ import annotations

_ADDITIONAL_CONTEXT_HEADER = (
    "Additional context (not directly supported by retrieved evidence):"
)


def split_answer_sections(answer: str) -> tuple[str, str]:
    """Split a generated answer into grounded answer and supplemental context."""

    lines = str(answer or "").splitlines()
    grounded_lines: list[str] = []
    additional_lines: list[str] = []
    in_additional = False
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith(_ADDITIONAL_CONTEXT_HEADER):
            in_additional = True
            remainder = stripped[len(_ADDITIONAL_CONTEXT_HEADER) :].strip()
            if remainder:
                additional_lines.append(remainder)
            continue
        if in_additional:
            additional_lines.append(stripped)
        else:
            grounded_lines.append(line)
    grounded_answer = "\n".join(line.rstrip() for line in grounded_lines).strip()
    additional_context = "\n".join(line for line in additional_lines if line).strip()
    return grounded_answer, additional_context


__all__ = ["_ADDITIONAL_CONTEXT_HEADER", "split_answer_sections"]
