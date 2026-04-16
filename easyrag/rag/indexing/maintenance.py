"""Workspace maintenance helpers for indexing flows."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Sequence

from easyrag.config import (
    get_rag_index_path,
    get_rag_working_dir,
    get_rag_workspace,
    get_repo_root,
)
from easyrag.rag.indexing.chunking import ChunkingConfig, chunk_documents
from easyrag.rag.indexing.loaders import load_repo_documents
from easyrag.support.async_utils import run_sync
from easyrag.support.optional_deps import Document

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG

RAGFactory = Callable[[Path, str], "EasyRAG"]


def _run_async(awaitable: object) -> object:
    """Run an async EasyRAG call from synchronous indexing helpers."""

    return run_sync(awaitable)


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


def write_legacy_snapshot(
    documents: Sequence[Document], *, index_path: str | Path | None = None
) -> None:
    """Write the compatibility JSON snapshot for local inspection and tests."""

    payload = [
        {
            "page_content": chunk.page_content,
            "metadata": chunk.metadata,
            "tokens": _tokenize(chunk.page_content),
        }
        for chunk in chunk_documents(documents, config=ChunkingConfig())
    ]
    resolved_index_path = (
        Path(index_path).resolve() if index_path is not None else get_rag_index_path()
    )
    resolved_index_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_index_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def _build_workspace(
    documents: list[Document],
    working_dir: Path,
    workspace: str,
    *,
    target_doc_ids: list[str] | None = None,
    full_sync: bool = False,
    rag_factory: RAGFactory | None = None,
) -> None:
    """Populate or synchronize one EasyRAG workspace in a single async lifecycle."""

    from easyrag.rag.orchestrator import EasyRAG

    rag = (
        rag_factory(working_dir, workspace)
        if rag_factory is not None
        else EasyRAG(working_dir=working_dir, workspace=workspace)
    )
    await rag.initialize_storages()
    try:
        selected_doc_ids = list(
            dict.fromkeys(
                target_doc_ids
                or [
                    str(document.metadata.get("doc_id", "")).strip()
                    for document in documents
                    if str(document.metadata.get("doc_id", "")).strip()
                ]
            )
        )
        selected_documents = (
            [
                document
                for document in documents
                if str(document.metadata.get("doc_id", "")).strip()
                in set(selected_doc_ids)
            ]
            if target_doc_ids
            else documents
        )
        if full_sync:
            existing_doc_ids = [
                str(status.get("document_id", "")).strip()
                for status in await rag.doc_status_storage.list_statuses()
                if str(status.get("document_id", "")).strip()
            ]
            stale_doc_ids = sorted(
                set(existing_doc_ids)
                - {
                    str(document.metadata.get("doc_id", "")).strip()
                    for document in documents
                }
            )
            if stale_doc_ids:
                await rag.adelete_documents(stale_doc_ids)
        elif selected_doc_ids:
            missing_doc_ids = sorted(
                set(selected_doc_ids)
                - {
                    str(document.metadata.get("doc_id", "")).strip()
                    for document in selected_documents
                }
            )
            if missing_doc_ids:
                await rag.adelete_documents(missing_doc_ids)
        if selected_documents:
            await rag.ainsert_documents(selected_documents)
    finally:
        await rag.finalize_storages()


def build_vector_index(
    documents: list[Document],
    *,
    working_dir: str | Path | None = None,
    workspace: str | None = None,
    index_path: str | Path | None = None,
    rag_factory: RAGFactory | None = None,
) -> None:
    """Build the EasyRAG workspace and a legacy JSON snapshot for compatibility."""

    resolved_working_dir, resolved_workspace = _resolve_legacy_storage_location()
    working_dir_path = (
        Path(working_dir).resolve()
        if working_dir is not None
        else resolved_working_dir.resolve()
    )
    workspace_name = workspace or resolved_workspace
    _run_async(
        _build_workspace(
            documents,
            working_dir_path,
            workspace_name,
            rag_factory=rag_factory,
        )
    )
    write_legacy_snapshot(documents, index_path=index_path)


def rebuild_document_index(
    repo_root: str | Path | None = None,
    *,
    doc_ids: list[str] | tuple[str, ...] | None = None,
    working_dir: str | Path | None = None,
    workspace: str | None = None,
    index_path: str | Path | None = None,
    rag_factory: RAGFactory | None = None,
) -> Path:
    """Discover repository docs and rebuild the default EasyRAG workspace."""

    root = Path(repo_root).resolve() if repo_root is not None else get_repo_root()
    working_dir_path = (
        Path(working_dir).resolve()
        if working_dir is not None
        else get_rag_working_dir()
    )
    workspace_name = workspace or get_rag_workspace()
    documents = load_repo_documents(root)
    normalized_doc_ids = list(
        dict.fromkeys(
            str(doc_id).strip() for doc_id in (doc_ids or []) if str(doc_id).strip()
        )
    )
    _run_async(
        _build_workspace(
            documents,
            working_dir_path,
            workspace_name,
            target_doc_ids=normalized_doc_ids or None,
            full_sync=not normalized_doc_ids,
            rag_factory=rag_factory,
        )
    )
    write_legacy_snapshot(documents, index_path=index_path)
    return working_dir_path / workspace_name


__all__ = ["build_vector_index", "rebuild_document_index", "write_legacy_snapshot"]
