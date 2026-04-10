"""Workspace maintenance helpers for indexing flows."""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

from easyrag.config import get_rag_index_path, get_rag_working_dir, get_rag_workspace, get_repo_root
from easyrag.rag.indexing.chunking import ChunkingConfig, chunk_documents
from easyrag.rag.indexing.loaders import load_repo_documents
from easyrag.support.optional_deps import Document

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def _run_async(awaitable: object) -> object:
    """Run an async EasyRAG call from synchronous indexing helpers."""

    try:
        return asyncio.run(awaitable)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(awaitable)
        finally:
            loop.close()


def _resolve_legacy_storage_location() -> tuple[Path, str]:
    """Map the legacy index path env var onto a working dir and workspace."""

    if "EASYRAG_WORKING_DIR" in os.environ or "EASYRAG_WORKSPACE" in os.environ:
        return get_rag_working_dir(), get_rag_workspace()

    legacy_index_path = get_rag_index_path()
    if "EASYRAG_INDEX_PATH" in os.environ:
        return legacy_index_path.parent, legacy_index_path.stem
    return get_rag_working_dir(), get_rag_workspace()


def _tokenize(text: str) -> list[str]:
    """Tokenize text for the legacy JSON snapshot."""

    return _TOKEN_PATTERN.findall(text.lower())


def _write_legacy_snapshot(documents: list[Document]) -> None:
    """Write the compatibility JSON snapshot for local inspection and tests."""

    payload = [
        {
            "page_content": chunk.page_content,
            "metadata": chunk.metadata,
            "tokens": _tokenize(chunk.page_content),
        }
        for chunk in chunk_documents(documents, config=ChunkingConfig())
    ]
    index_path = get_rag_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


async def _build_workspace(
    documents: list[Document],
    working_dir: Path,
    workspace: str,
    *,
    target_doc_ids: list[str] | None = None,
    full_sync: bool = False,
) -> None:
    """Populate or synchronize one EasyRAG workspace in a single async lifecycle."""

    from easyrag.rag.orchestrator import EasyRAG

    rag = EasyRAG(working_dir=working_dir, workspace=workspace)
    await rag.initialize_storages()
    try:
        selected_doc_ids = list(
            dict.fromkeys(
                target_doc_ids
                or [str(document.metadata.get("doc_id", "")).strip() for document in documents if str(document.metadata.get("doc_id", "")).strip()]
            )
        )
        selected_documents = (
            [document for document in documents if str(document.metadata.get("doc_id", "")).strip() in set(selected_doc_ids)]
            if target_doc_ids
            else documents
        )
        if full_sync:
            existing_doc_ids = [
                str(status.get("document_id", "")).strip()
                for status in await rag.doc_status_storage.list_statuses()
                if str(status.get("document_id", "")).strip()
            ]
            stale_doc_ids = sorted(set(existing_doc_ids) - {str(document.metadata.get("doc_id", "")).strip() for document in documents})
            if stale_doc_ids:
                await rag.adelete_documents(stale_doc_ids)
        elif selected_doc_ids:
            missing_doc_ids = sorted(set(selected_doc_ids) - {str(document.metadata.get("doc_id", "")).strip() for document in selected_documents})
            if missing_doc_ids:
                await rag.adelete_documents(missing_doc_ids)
        if selected_documents:
            await rag.ainsert_documents(selected_documents)
    finally:
        await rag.finalize_storages()


def build_vector_index(documents: list[Document]) -> None:
    """Build the EasyRAG workspace and a legacy JSON snapshot for compatibility."""

    working_dir, workspace = _resolve_legacy_storage_location()
    _run_async(_build_workspace(documents, working_dir, workspace))
    _write_legacy_snapshot(documents)


def rebuild_document_index(
    repo_root: str | Path | None = None,
    *,
    doc_ids: list[str] | tuple[str, ...] | None = None,
) -> Path:
    """Discover repository docs and rebuild the default EasyRAG workspace."""

    root = Path(repo_root).resolve() if repo_root is not None else get_repo_root()
    documents = load_repo_documents(root)
    normalized_doc_ids = list(dict.fromkeys(str(doc_id).strip() for doc_id in (doc_ids or []) if str(doc_id).strip()))
    _run_async(
        _build_workspace(
            documents,
            get_rag_working_dir(),
            get_rag_workspace(),
            target_doc_ids=normalized_doc_ids or None,
            full_sync=not normalized_doc_ids,
        )
    )
    _write_legacy_snapshot(documents)
    return get_rag_working_dir() / get_rag_workspace()


__all__ = ["build_vector_index", "rebuild_document_index"]
