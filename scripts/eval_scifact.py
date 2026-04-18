"""Run retrieval evaluation against repository-local SciFact exports."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_ROOT = PROJECT_ROOT / "sample_data" / "scifact"


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

from easyrag.config import get_rag_working_dir, get_rag_workspace  # noqa: E402
from easyrag.rag import EasyRAG, EvalCase, QueryParam  # noqa: E402
from easyrag.rag.evaluation import evaluate_retrieval  # noqa: E402
from easyrag.rag.utils import slugify  # noqa: E402
from easyrag.support.async_utils import run_sync  # noqa: E402


def _run_async(awaitable: object) -> object:
    """Run async EasyRAG operations from this CLI."""

    return run_sync(awaitable)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for SciFact retrieval evaluation."""

    parser = argparse.ArgumentParser(
        description="Evaluate an indexed SciFact sample or full export with EasyRAG."
    )
    parser.add_argument(
        "--eval-root",
        type=Path,
        default=SAMPLE_ROOT,
        help="Benchmark root containing docs/ plus queries/qrels files.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root that was used when building the index. Defaults to eval-root.",
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        default=None,
        help="EasyRAG storage root. Defaults to <repo-root>/.easyrag/rag_storage.",
    )
    parser.add_argument(
        "--workspace",
        default=get_rag_workspace(),
        help="Workspace name to evaluate.",
    )
    parser.add_argument(
        "--split",
        choices=("train", "test"),
        default="train",
        help="Qrels split to load when qrels_train/qrels_test files are present.",
    )
    parser.add_argument(
        "--mode",
        choices=("naive", "local", "global", "hybrid", "mix"),
        default="naive",
        help="Retrieval mode used during evaluation.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of ranked results to retain per query.",
    )
    parser.add_argument(
        "--chunk-top-k",
        type=int,
        default=5,
        help="Maximum number of hydrated chunks to keep per query.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of eval cases to run.",
    )
    parser.add_argument(
        "--preview-cases",
        type=int,
        default=5,
        help="How many case reports to print in human-readable mode.",
    )
    parser.add_argument(
        "--enable-rewrite",
        action="store_true",
        help="Enable query rewrite during evaluation.",
    )
    parser.add_argument(
        "--enable-mqe",
        action="store_true",
        help="Enable multi-query expansion during evaluation.",
    )
    parser.add_argument(
        "--enable-rerank",
        action="store_true",
        help="Enable reranking during evaluation when the mode supports it.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Optional minimum retrieval score filter.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help="Optional JSON file to write the full report to.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full report as JSON instead of a human-readable summary.",
    )
    return parser.parse_args([] if argv is None else argv)


def _load_json(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array from disk."""

    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return [dict(item) for item in payload]


def _resolve_repo_root(eval_root: Path, repo_root: Path | None) -> Path:
    """Resolve the repository root used for doc-id generation."""

    return (repo_root or eval_root).resolve()


def _resolve_working_dir(repo_root: Path, working_dir: Path | None) -> Path:
    """Resolve the EasyRAG working directory for the target workspace."""

    del repo_root
    if working_dir is not None:
        return working_dir.resolve()
    return get_rag_working_dir().resolve()


def _doc_id_from_corpus_id(eval_root: Path, repo_root: Path, corpus_id: str) -> str:
    """Translate one SciFact corpus id into the indexed EasyRAG document id."""

    document_path = (eval_root / "docs" / f"{corpus_id}.md").resolve()
    if not document_path.exists():
        raise SystemExit(f"Missing materialized document for corpus_id={corpus_id}: {document_path}")
    try:
        relative_path = document_path.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise SystemExit(
            f"Document {document_path} is not under repo_root={repo_root}. "
            "Pass --repo-root that matches the root used during indexing."
        ) from exc
    return f"doc::{slugify(relative_path)}"


def _group_qrels_into_eval_cases(
    *,
    eval_root: Path,
    repo_root: Path,
    queries: list[dict[str, Any]],
    qrels: list[dict[str, Any]],
    split: str,
) -> list[EvalCase]:
    """Build grouped EvalCase objects from SciFact qrels rows."""

    queries_by_id = {
        str(row.get("_id", "")).strip(): str(row.get("text", "")).strip()
        for row in queries
        if str(row.get("_id", "")).strip() and str(row.get("text", "")).strip()
    }

    grouped: dict[str, dict[str, Any]] = {}
    for row in qrels:
        score = float(row.get("score", 1) or 0)
        if score <= 0:
            continue
        query_id = str(row.get("query-id", "")).strip()
        corpus_id = str(row.get("corpus-id", "")).strip()
        if not query_id or not corpus_id or query_id not in queries_by_id:
            continue
        document_id = _doc_id_from_corpus_id(eval_root, repo_root, corpus_id)
        group = grouped.setdefault(
            query_id,
            {
                "question": queries_by_id[query_id],
                "expected_document_ids": [],
                "corpus_ids": [],
            },
        )
        if document_id not in group["expected_document_ids"]:
            group["expected_document_ids"].append(document_id)
        if corpus_id not in group["corpus_ids"]:
            group["corpus_ids"].append(corpus_id)

    cases: list[EvalCase] = []
    for query_id, payload in grouped.items():
        cases.append(
            EvalCase(
                question=str(payload["question"]),
                expected_document_ids=tuple(payload["expected_document_ids"]),
                expected_snippets=(),
                reference_answer="",
                expected_to_abstain=False,
                metadata={
                    "query_id": query_id,
                    "corpus_ids": list(payload["corpus_ids"]),
                    "split": split,
                    "source": "qrels",
                },
            )
        )
    return cases


def _load_cases_from_qrels(
    eval_root: Path,
    repo_root: Path,
    *,
    split: str,
) -> tuple[list[EvalCase], str] | None:
    """Load EvalCase objects from queries/qrels exports when available."""

    queries_path = eval_root / "queries.json"
    qrels_candidates = [eval_root / f"qrels_{split}.json", eval_root / "qrels.json"]
    qrels_path = next((path for path in qrels_candidates if path.exists()), None)
    if not queries_path.exists() or qrels_path is None:
        return None
    queries = _load_json(queries_path)
    qrels = _load_json(qrels_path)
    cases = _group_qrels_into_eval_cases(
        eval_root=eval_root,
        repo_root=repo_root,
        queries=queries,
        qrels=qrels,
        split=split,
    )
    return cases, qrels_path.name


def _load_cases_from_eval_json(
    eval_root: Path,
    repo_root: Path,
) -> tuple[list[EvalCase], str]:
    """Load EvalCase objects from a precomputed eval_cases.json file."""

    eval_cases_path = eval_root / "eval_cases.json"
    rows = _load_json(eval_cases_path)
    cases: list[EvalCase] = []
    for row in rows:
        metadata = dict(row.get("metadata", {}))
        corpus_ids = list(metadata.get("corpus_ids", []) or [])
        if not corpus_ids and str(metadata.get("corpus_id", "")).strip():
            corpus_ids = [str(metadata["corpus_id"]).strip()]
        expected_document_ids = tuple(
            _doc_id_from_corpus_id(eval_root, repo_root, corpus_id)
            for corpus_id in corpus_ids
        ) or tuple(str(value) for value in row.get("expected_document_ids", []) or [])
        cases.append(
            EvalCase(
                question=str(row.get("question", "")).strip(),
                expected_document_ids=expected_document_ids,
                expected_snippets=tuple(
                    str(value) for value in row.get("expected_snippets", []) or []
                ),
                reference_answer=str(row.get("reference_answer", "")),
                expected_to_abstain=bool(row.get("expected_to_abstain", False)),
                metadata=metadata,
            )
        )
    return cases, eval_cases_path.name


def load_eval_cases(
    eval_root: Path,
    repo_root: Path,
    *,
    split: str,
    limit: int | None = None,
) -> tuple[list[EvalCase], str]:
    """Load retrieval eval cases from the benchmark root."""

    resolved_eval_root = eval_root.resolve()
    resolved_repo_root = repo_root.resolve()
    loaded = _load_cases_from_qrels(
        resolved_eval_root,
        resolved_repo_root,
        split=split,
    )
    if loaded is None:
        loaded = _load_cases_from_eval_json(
            resolved_eval_root,
            resolved_repo_root,
        )
    cases, source_name = loaded
    if limit is not None:
        cases = cases[: max(limit, 0)]
    if not cases:
        raise SystemExit(
            f"No eval cases found under {resolved_eval_root}. "
            "Import SciFact first or point --eval-root at a populated export."
        )
    return cases, source_name


def summarize_alignment(
    cases: list[EvalCase],
    indexed_doc_ids: set[str],
) -> dict[str, Any]:
    """Summarize how well eval expectations align with the indexed workspace."""

    expected_doc_ids = sorted(
        {doc_id for case in cases for doc_id in case.expected_document_ids if doc_id}
    )
    matched_doc_ids = sorted(set(expected_doc_ids) & indexed_doc_ids)
    missing_doc_ids = [doc_id for doc_id in expected_doc_ids if doc_id not in indexed_doc_ids]
    return {
        "indexed_documents": len(indexed_doc_ids),
        "expected_unique_documents": len(expected_doc_ids),
        "matched_expected_documents": len(matched_doc_ids),
        "missing_expected_documents": len(missing_doc_ids),
        "matched_doc_ids": matched_doc_ids,
        "missing_doc_ids_preview": missing_doc_ids[:10],
        "has_overlap": bool(matched_doc_ids),
    }


async def _run_evaluation(
    *,
    working_dir: Path,
    workspace: str,
    cases: list[EvalCase],
    query_param: QueryParam,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run retrieval evaluation and collect index diagnostics."""

    rag = EasyRAG(working_dir=working_dir, workspace=workspace)
    await rag.initialize_storages()
    try:
        stats = await rag.get_stats()
        statuses = await rag.doc_status_storage.list_statuses()
        indexed_doc_ids = {
            str(status.get("document_id", "")).strip()
            for status in statuses
            if str(status.get("document_id", "")).strip()
        }
        alignment = summarize_alignment(cases, indexed_doc_ids)
        report = await evaluate_retrieval(rag, cases, query_param)
        return stats, alignment, report
    finally:
        await rag.finalize_storages()


def _print_human_report(payload: dict[str, Any], *, preview_cases: int) -> None:
    """Print a concise human-readable report."""

    benchmark = dict(payload.get("benchmark", {}) or {})
    index = dict(payload.get("index", {}) or {})
    alignment = dict(payload.get("alignment", {}) or {})
    retrieval = dict(payload.get("retrieval", {}) or {})
    metrics = dict(retrieval.get("metrics", {}) or {})

    print("=== EasyRAG SciFact Eval ===")
    print(f"eval_root={benchmark.get('eval_root', '')}")
    print(f"repo_root={benchmark.get('repo_root', '')}")
    print(f"workspace={benchmark.get('workspace', '')}")
    print(f"working_dir={benchmark.get('working_dir', '')}")
    print(f"case_source={benchmark.get('case_source', '')}")
    print(f"split={benchmark.get('split', '')}")
    print(f"cases={benchmark.get('cases', 0)}")
    print(f"mode={benchmark.get('mode', '')}")
    print(f"top_k={benchmark.get('top_k', 0)}")
    print(f"chunk_top_k={benchmark.get('chunk_top_k', 0)}")
    print()
    print("Index:")
    print(f"documents={index.get('documents', 0)}")
    print(f"chunks={index.get('chunks', 0)}")
    print(f"chunk_vectors={index.get('chunk_vectors', 0)}")
    print(f"summary_vectors={index.get('summary_vectors', 0)}")
    print(f"vector_backend={index.get('vector_backend', 'unknown')}")
    print()
    print("Alignment:")
    print(f"indexed_documents={alignment.get('indexed_documents', 0)}")
    print(f"expected_unique_documents={alignment.get('expected_unique_documents', 0)}")
    print(f"matched_expected_documents={alignment.get('matched_expected_documents', 0)}")
    print(f"missing_expected_documents={alignment.get('missing_expected_documents', 0)}")
    if not alignment.get("has_overlap", False):
        print("warning=no_expected_document_ids_overlap_with_index")
        print(
            "hint=Rebuild the index with EASYRAG_REPO_ROOT matching eval_root, or rerun this script with --repo-root matching the indexed root."
        )
    missing_preview = list(alignment.get("missing_doc_ids_preview", []) or [])
    if missing_preview:
        print(f"missing_doc_ids_preview={missing_preview}")
    print()
    print("Metrics:")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    cases = list(retrieval.get("cases", []) or [])[: max(preview_cases, 0)]
    if not cases:
        return
    print()
    print("Case previews:")
    for index, case in enumerate(cases, start=1):
        print(f"[{index}] question={case.get('question', '')}")
        print(f"expected_document_ids={case.get('expected_document_ids', [])}")
        print(f"retrieved_document_ids={case.get('retrieved_document_ids', [])[:5]}")
        print(
            "metrics={metrics}".format(
                metrics=json.dumps(case.get("metrics", {}), ensure_ascii=False)
            )
        )


def main(argv: list[str] | None = None) -> None:
    """Run SciFact retrieval evaluation against one EasyRAG workspace."""

    args = _parse_args(argv)
    eval_root = args.eval_root.resolve()
    repo_root = _resolve_repo_root(eval_root, args.repo_root)
    working_dir = _resolve_working_dir(repo_root, args.working_dir)
    workspace = str(args.workspace).strip() or "default"
    cases, case_source = load_eval_cases(
        eval_root,
        repo_root,
        split=args.split,
        limit=args.limit,
    )
    query_param = QueryParam(
        mode=args.mode,
        top_k=max(args.top_k, 1),
        chunk_top_k=max(args.chunk_top_k, 1),
        enable_rerank=args.enable_rerank,
        rewrite_enabled=args.enable_rewrite,
        mqe_enabled=args.enable_mqe,
        min_score=args.min_score,
    )
    stats, alignment, retrieval = _run_async(
        _run_evaluation(
            working_dir=working_dir,
            workspace=workspace,
            cases=cases,
            query_param=query_param,
        )
    )
    payload = {
        "benchmark": {
            "eval_root": str(eval_root),
            "repo_root": str(repo_root),
            "workspace": workspace,
            "working_dir": str(working_dir / workspace),
            "case_source": case_source,
            "split": args.split,
            "cases": len(cases),
            "mode": query_param.mode,
            "top_k": query_param.top_k,
            "chunk_top_k": query_param.chunk_top_k,
        },
        "index": dict(stats),
        "alignment": alignment,
        "query_param": asdict(query_param),
        "retrieval": retrieval,
    }

    if args.report_path is not None:
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    _print_human_report(payload, preview_cases=args.preview_cases)


if __name__ == "__main__":
    main(sys.argv[1:])
