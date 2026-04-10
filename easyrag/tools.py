"""Lightweight tool wrappers built on top of the canonical EasyRAG API."""

from __future__ import annotations

import asyncio
import json
from typing import Callable

from easyrag.config import get_rag_working_dir, get_rag_workspace
from easyrag.rag import EasyRAG, QueryParam
from easyrag.support.optional_deps import tool


def _run_async(awaitable: object) -> object:
    """Run async EasyRAG calls from synchronous helper wrappers."""

    try:
        return asyncio.run(awaitable)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(awaitable)
        finally:
            loop.close()


def _serialize_citations(citations: list[dict[str, str]]) -> str:
    """Serialize citations into a compact JSON payload."""

    return json.dumps(citations, ensure_ascii=False, indent=2)


def create_search_docs_tool(
    rag_getter: Callable[[], EasyRAG],
    *,
    default_mode: str = "hybrid",
    rewrite_enabled: bool = True,
    mqe_enabled: bool = True,
):
    """Create a tool bound to a lazily provided EasyRAG instance."""

    @tool(description="Search indexed repository knowledge chunks and return grounded citations.")
    def search_repo_knowledge(query: str) -> str:
        rag = rag_getter()
        result = _run_async(
            rag.aquery(
                query,
                QueryParam(
                    mode=default_mode,
                    top_k=8,
                    chunk_top_k=5,
                    enable_rerank=default_mode == "mix",
                    rewrite_enabled=rewrite_enabled,
                    mqe_enabled=mqe_enabled,
                ),
            )
        )
        return _serialize_citations(result.citations)

    return search_repo_knowledge


@tool
def search_docs_tool(query: str) -> str:
    """Compatibility wrapper that runs naive retrieval and returns JSON citations."""

    rag = EasyRAG(working_dir=get_rag_working_dir(), workspace=get_rag_workspace())
    _run_async(rag.initialize_storages())
    try:
        result = _run_async(
            rag.aquery(
                query,
                QueryParam(
                    mode="naive",
                    top_k=5,
                    chunk_top_k=5,
                    rewrite_enabled=False,
                    mqe_enabled=False,
                ),
            )
        )
    except Exception:
        result = None
    finally:
        _run_async(rag.finalize_storages())

    serialized = [] if result is None else list(result.citations)
    return _serialize_citations(serialized)


def get_default_rag_tool():
    """Return a default tool bound to the configured standard workspace."""

    rag = EasyRAG(working_dir=get_rag_working_dir(), workspace=get_rag_workspace())
    _run_async(rag.initialize_storages())
    mode = "mix" if rag.can_rerank() else "hybrid"
    return create_search_docs_tool(lambda: rag, default_mode=mode, rewrite_enabled=True, mqe_enabled=True)


__all__ = ["create_search_docs_tool", "get_default_rag_tool", "search_docs_tool"]
