"""Context-packing helpers for grounded answer generation."""

from __future__ import annotations

from easyrag.rag.generation.selection import normalize_citation_snippet


def build_context_block(citations: list[dict[str, str]]) -> str:
    """Build a prompt-ready context block from selected citations."""

    blocks: list[str] = []
    for index, citation in enumerate(citations, start=1):
        blocks.append(
            f"[{index}] {citation.get('title', 'Document')} ({citation.get('location', '')})\n"
            f"{normalize_citation_snippet(citation.get('snippet', ''))}"
        )
    return "\n\n".join(blocks)
