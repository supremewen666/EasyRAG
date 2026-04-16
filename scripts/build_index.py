"""Build or maintain the local RAG index for EasyRAG documentation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _reexec_with_project_venv() -> None:
    """Prefer the repository virtualenv when the script is launched globally."""

    project_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if (
        sys.prefix != sys.base_prefix
        or not project_python.exists()
        or os.getenv("EASYRAG_SKIP_VENV_REEXEC", "").strip() == "1"
    ):
        return
    os.execv(str(project_python), [str(project_python), __file__, *sys.argv[1:]])


_reexec_with_project_venv()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from easyrag.config import get_rag_working_dir, get_rag_workspace, get_repo_root  # noqa: E402
from easyrag.rag import EasyRAG  # noqa: E402
from easyrag.rag.indexing import rebuild_document_index  # noqa: E402
from easyrag.rag.indexing.maintenance import write_legacy_snapshot  # noqa: E402
from easyrag.support.async_utils import run_sync  # noqa: E402

if TYPE_CHECKING:
    from easyrag.rag.indexing.maintenance import RAGFactory


def _run_async(awaitable: object) -> object:
    """Run async EasyRAG operations from the build script."""

    return run_sync(awaitable)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for index maintenance."""

    parser = argparse.ArgumentParser(
        description="Build or maintain the EasyRAG RAG index."
    )
    parser.add_argument(
        "--action",
        choices=("rebuild", "update", "delete"),
        default="rebuild",
        help="Index maintenance action. `update` is an alias of `rebuild`.",
    )
    parser.add_argument(
        "--doc-id",
        dest="doc_ids",
        action="append",
        default=[],
        help="Document ID to target. Repeat for multiple documents.",
    )
    return parser.parse_args([] if argv is None else argv)


def _print_summary(
    rag: EasyRAG,
    stats: dict[str, int],
    aggregate: dict[str, int],
    *,
    action: str,
    targeted_doc_ids: list[str],
) -> None:
    """Print a compact summary of the index maintenance result."""

    print(f"repo_root={get_repo_root()}")
    print(f"workspace={rag.workspace}")
    print(f"working_dir={rag.workspace_dir}")
    print(f"action={action}")
    print(f"targeted_doc_ids={targeted_doc_ids}")
    print(f"documents={stats.get('documents', 0)}")
    print(f"pdf_documents={stats.get('pdf_documents', 0)}")
    print(f"chunks={stats.get('chunks', 0)}")
    print(f"entities={aggregate.get('entity_vectors', 0)}")
    print(f"relations={aggregate.get('relation_vectors', 0)}")
    print(f"chunk_strategy_counts={aggregate.get('chunk_strategy_counts', {})}")
    print(f"vector_backend={aggregate.get('vector_backend', 'unknown')}")


def build_repository_index(
    *,
    action: str = "rebuild",
    targeted_doc_ids: list[str] | None = None,
    repo_root: str | Path | None = None,
    working_dir: str | Path | None = None,
    workspace: str | None = None,
    index_path: str | Path | None = None,
    rag_factory: "RAGFactory | None" = None,
) -> dict[str, object]:
    """Build or maintain one repository index and return the resulting summary."""

    root = Path(repo_root).resolve() if repo_root is not None else get_repo_root()
    working_dir_path = (
        Path(working_dir).resolve()
        if working_dir is not None
        else get_rag_working_dir()
    )
    workspace_name = workspace or get_rag_workspace()
    targeted = list(dict.fromkeys(targeted_doc_ids or []))
    rag_builder = rag_factory or (
        lambda resolved_working_dir, resolved_workspace: EasyRAG(
            working_dir=resolved_working_dir, workspace=resolved_workspace
        )
    )

    if action == "delete":
        rag = rag_builder(working_dir_path, workspace_name)
        _run_async(rag.initialize_storages())
        try:
            stats = _run_async(rag.adelete_documents(targeted))
            aggregate = _run_async(rag.get_stats())
        finally:
            _run_async(rag.finalize_storages())
        if targeted:
            remaining_documents = [
                document
                for document in EasyRAG.load_repo_documents(root)
                if str(document.metadata.get("doc_id", "")).strip() not in set(targeted)
            ]
            write_legacy_snapshot(remaining_documents, index_path=index_path)
        return {
            "repo_root": root,
            "workspace": workspace_name,
            "working_dir": working_dir_path / workspace_name,
            "action": action,
            "targeted_doc_ids": targeted,
            "stats": stats,
            "aggregate": aggregate,
        }

    rebuild_document_index(
        root,
        doc_ids=targeted or None,
        working_dir=working_dir_path,
        workspace=workspace_name,
        index_path=index_path,
        rag_factory=rag_factory,
    )
    rag = rag_builder(working_dir_path, workspace_name)
    _run_async(rag.initialize_storages())
    try:
        aggregate = _run_async(rag.get_stats())
        current_documents = EasyRAG.load_repo_documents(root)
        filtered_documents = (
            [
                document
                for document in current_documents
                if str(document.metadata.get("doc_id", "")).strip() in set(targeted)
            ]
            if targeted
            else current_documents
        )
        stats = {
            "documents": len(filtered_documents),
            "pdf_documents": sum(
                1
                for document in filtered_documents
                if document.metadata.get("source_type") == "pdf"
            ),
            "chunks": int(aggregate.get("chunks", 0)),
        }
    finally:
        _run_async(rag.finalize_storages())

    return {
        "repo_root": root,
        "workspace": workspace_name,
        "working_dir": working_dir_path / workspace_name,
        "action": action,
        "targeted_doc_ids": targeted,
        "stats": stats,
        "aggregate": aggregate,
    }


def main(argv: list[str] | None = None) -> None:
    """Build, rebuild, update, or delete EasyRAG document index entries."""

    args = _parse_args(argv)
    action = "rebuild" if args.action == "update" else args.action
    targeted_doc_ids = list(
        dict.fromkeys(
            str(doc_id).strip() for doc_id in args.doc_ids if str(doc_id).strip()
        )
    )

    summary = build_repository_index(
        action=action,
        targeted_doc_ids=targeted_doc_ids,
        repo_root=get_repo_root(),
        working_dir=get_rag_working_dir(),
        workspace=get_rag_workspace(),
    )
    rag = EasyRAG(working_dir=get_rag_working_dir(), workspace=get_rag_workspace())

    _print_summary(
        rag,
        dict(summary["stats"]),
        dict(summary["aggregate"]),
        action=action,
        targeted_doc_ids=targeted_doc_ids,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
