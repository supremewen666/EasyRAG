"""Build or maintain the local RAG index for EasyRAG documentation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from easyrag.config import get_rag_working_dir, get_rag_workspace, get_repo_root  # noqa: E402
from easyrag.rag import EasyRAG  # noqa: E402
from easyrag.rag.indexing import rebuild_document_index  # noqa: E402
from easyrag.rag.indexing.maintenance import write_legacy_snapshot  # noqa: E402
from easyrag.support.async_utils import run_sync  # noqa: E402


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


def main(argv: list[str] | None = None) -> None:
    """Build, rebuild, update, or delete EasyRAG document index entries."""

    args = _parse_args(argv)
    action = "rebuild" if args.action == "update" else args.action
    targeted_doc_ids = list(
        dict.fromkeys(
            str(doc_id).strip() for doc_id in args.doc_ids if str(doc_id).strip()
        )
    )

    if action == "delete":
        rag = EasyRAG(working_dir=get_rag_working_dir(), workspace=get_rag_workspace())
        _run_async(rag.initialize_storages())
        try:
            stats = _run_async(rag.adelete_documents(targeted_doc_ids))
            aggregate = _run_async(rag.get_stats())
        finally:
            _run_async(rag.finalize_storages())
        if targeted_doc_ids:
            remaining_documents = [
                document
                for document in EasyRAG.load_repo_documents(get_repo_root())
                if str(document.metadata.get("doc_id", "")).strip()
                not in set(targeted_doc_ids)
            ]
            write_legacy_snapshot(remaining_documents)
        _print_summary(
            rag, stats, aggregate, action=action, targeted_doc_ids=targeted_doc_ids
        )
        return

    rebuild_document_index(get_repo_root(), doc_ids=targeted_doc_ids or None)
    rag = EasyRAG(working_dir=get_rag_working_dir(), workspace=get_rag_workspace())
    _run_async(rag.initialize_storages())
    try:
        aggregate = _run_async(rag.get_stats())
        current_documents = EasyRAG.load_repo_documents(get_repo_root())
        filtered_documents = (
            [
                document
                for document in current_documents
                if str(document.metadata.get("doc_id", "")).strip()
                in set(targeted_doc_ids)
            ]
            if targeted_doc_ids
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

    _print_summary(
        rag, stats, aggregate, action=action, targeted_doc_ids=targeted_doc_ids
    )


if __name__ == "__main__":
    main(sys.argv[1:])
