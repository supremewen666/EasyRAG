"""Import SciFact sample or full corpus into repository-local data directories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from easyrag.rag.utils import slugify

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_ROOT = PROJECT_ROOT / "sample_data" / "scifact"
FULL_ROOT = PROJECT_ROOT / "sample_data" / "scifact_full"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import sample or full mteb/scifact data into sample_data."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("import", "show", "import-full", "show-full"),
        default="import",
        help="Import sampled data or show the already imported sample.",
    )
    parser.add_argument(
        "--max-corpus",
        type=int,
        default=24,
        help="Maximum number of corpus documents to store.",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=8,
        help="Maximum number of queries to store.",
    )
    parser.add_argument(
        "--split",
        choices=("train", "test"),
        default="train",
        help="SciFact qrels split to sample from.",
    )
    parser.add_argument(
        "--full-root",
        type=Path,
        default=FULL_ROOT,
        help="Target directory for the full SciFact export.",
    )
    return parser.parse_args([] if argv is None else argv)


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sample_doc_relative_path(corpus_id: str) -> str:
    return f"docs/{corpus_id}.md"


def _sample_doc_id(corpus_id: str) -> str:
    return f"doc::{slugify(_sample_doc_relative_path(corpus_id))}"


def _write_sample_docs(corpus_rows: list[dict[str, Any]]) -> None:
    docs_root = SAMPLE_ROOT / "docs"
    docs_root.mkdir(parents=True, exist_ok=True)
    for row in corpus_rows:
        corpus_id = str(row["_id"]).strip()
        title = str(row.get("title", "")).strip()
        text = str(row.get("text", "")).strip()
        lines = []
        if title:
            lines.append(f"# {title}")
            lines.append("")
        lines.append(text)
        lines.append("")
        (docs_root / f"{corpus_id}.md").write_text("\n".join(lines), encoding="utf-8")


def _load_scifact() -> tuple[Any, Any, Any, Any]:
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - convenience path.
        raise SystemExit(
            "Missing dependency: install `datasets` first, for example "
            "`pip install datasets`."
        ) from exc

    corpus = load_dataset("mteb/scifact", "corpus", split="corpus")
    queries = load_dataset("mteb/scifact", "queries", split="queries")
    qrels_train = load_dataset("mteb/scifact", "default", split="train")
    qrels_test = load_dataset("mteb/scifact", "default", split="test")
    return corpus, queries, qrels_train, qrels_test


def _import_sample(max_corpus: int, max_queries: int, split: str) -> None:
    corpus, queries, qrels_train, qrels_test = _load_scifact()
    qrels = qrels_train if split == "train" else qrels_test

    sampled_qrels = list(qrels.select(range(min(max_queries, len(qrels)))))
    query_ids = []
    corpus_ids = []
    for row in sampled_qrels:
        query_id = str(row["query-id"])
        corpus_id = str(row["corpus-id"])
        if query_id not in query_ids:
            query_ids.append(query_id)
        if corpus_id not in corpus_ids:
            corpus_ids.append(corpus_id)

    corpus_by_id = {str(row["_id"]): dict(row) for row in corpus}
    queries_by_id = {str(row["_id"]): dict(row) for row in queries}

    sampled_queries = [
        queries_by_id[query_id]
        for query_id in query_ids
        if query_id in queries_by_id
    ][:max_queries]
    sampled_corpus = [
        corpus_by_id[corpus_id]
        for corpus_id in corpus_ids
        if corpus_id in corpus_by_id
    ]

    remaining_corpus_budget = max(0, max_corpus - len(sampled_corpus))
    if remaining_corpus_budget:
        for row in corpus:
            row_id = str(row["_id"])
            if row_id in corpus_ids:
                continue
            sampled_corpus.append(dict(row))
            if len(sampled_corpus) >= max_corpus:
                break

    _write_json(SAMPLE_ROOT / "corpus.json", sampled_corpus[:max_corpus])
    _write_json(SAMPLE_ROOT / "queries.json", sampled_queries)
    _write_json(SAMPLE_ROOT / "qrels.json", sampled_qrels)
    _write_sample_docs(sampled_corpus[:max_corpus])

    eval_cases = [
        {
            "question": queries_by_id[query_id]["text"],
            "expected_document_ids": [_sample_doc_id(corpus_id)],
            "expected_snippets": [],
            "reference_answer": "",
            "expected_to_abstain": False,
            "metadata": {
                "query_id": query_id,
                "corpus_id": corpus_id,
                "relative_path": _sample_doc_relative_path(corpus_id),
            },
        }
        for row in sampled_qrels
        for query_id, corpus_id in [
            (str(row["query-id"]), str(row["corpus-id"]))
        ]
        if query_id in queries_by_id
    ]
    _write_json(SAMPLE_ROOT / "eval_cases.json", eval_cases)

    summary = {
        "dataset": "mteb/scifact",
        "split": split,
        "corpus_documents": len(sampled_corpus[:max_corpus]),
        "queries": len(sampled_queries),
        "qrels": len(sampled_qrels),
        "eval_cases": len(eval_cases),
    }
    (SAMPLE_ROOT / "README.md").write_text(
        "\n".join(
            [
                "# SciFact sample",
                "",
                "This directory contains a compact sample extracted from "
                "`mteb/scifact`.",
                "",
                "Files:",
                "- `corpus.json`: sampled corpus abstracts",
                "- `docs/`: markdown files materialized for `build_index.py`",
                "- `queries.json`: sampled claims/questions",
                "- `qrels.json`: relevance pairs used for retrieval evaluation",
                "- `eval_cases.json`: EasyRAG-ready retrieval eval cases",
                "",
                "Quick preview:",
                "- `python scripts/import_scifact_sample.py show`",
                "",
                "Import again:",
                "- `python scripts/import_scifact_sample.py import --split train`",
                "",
                "Build an index from the sample docs:",
                f"- `EASYRAG_REPO_ROOT={SAMPLE_ROOT} python scripts/build_index.py --action rebuild`",
                "",
                f"Current sample summary: `{json.dumps(summary, ensure_ascii=False)}`",
                "",
                "Source: https://huggingface.co/datasets/mteb/scifact",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _write_full_docs(root: Path, corpus: Any) -> int:
    docs_root = root / "docs"
    docs_root.mkdir(parents=True, exist_ok=True)
    count = 0
    for row in corpus:
        doc_id = str(row["_id"]).strip()
        title = str(row.get("title", "")).strip()
        text = str(row.get("text", "")).strip()
        lines = []
        if title:
            lines.append(f"# {title}")
            lines.append("")
        lines.append(text)
        lines.append("")
        (docs_root / f"{doc_id}.md").write_text("\n".join(lines), encoding="utf-8")
        count += 1
    return count


def _import_full(root: Path) -> None:
    corpus, queries, qrels_train, qrels_test = _load_scifact()
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    corpus_count = _write_full_docs(root, corpus)
    _write_json(root / "queries.json", [dict(row) for row in queries])
    _write_json(root / "qrels_train.json", [dict(row) for row in qrels_train])
    _write_json(root / "qrels_test.json", [dict(row) for row in qrels_test])

    summary = {
        "dataset": "mteb/scifact",
        "export_root": str(root),
        "docs_dir": str(root / "docs"),
        "corpus_documents": corpus_count,
        "queries": len(queries),
        "qrels_train": len(qrels_train),
        "qrels_test": len(qrels_test),
    }
    (root / "README.md").write_text(
        "\n".join(
            [
                "# SciFact full export",
                "",
                "This directory contains a full repository-local export of "
                "`mteb/scifact`.",
                "",
                "Files:",
                "- `docs/`: one markdown file per corpus document",
                "- `queries.json`: all query rows",
                "- `qrels_train.json`: all train relevance pairs",
                "- `qrels_test.json`: all test relevance pairs",
                "",
                "Index only the full SciFact corpus docs:",
                f"- `EASYRAG_REPO_ROOT={root} python scripts/build_index.py --action rebuild`",
                "",
                "Preview the export:",
                f"- `python scripts/import_scifact_sample.py show-full --full-root {root}`",
                "",
                f"Current export summary: `{json.dumps(summary, ensure_ascii=False)}`",
                "",
                "Source: https://huggingface.co/datasets/mteb/scifact",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _show_sample() -> None:
    corpus = _load_json(SAMPLE_ROOT / "corpus.json")
    queries = _load_json(SAMPLE_ROOT / "queries.json")
    qrels = _load_json(SAMPLE_ROOT / "qrels.json")
    eval_cases = _load_json(SAMPLE_ROOT / "eval_cases.json")
    doc_paths = sorted((SAMPLE_ROOT / "docs").glob("*.md"))

    if not corpus and not queries and not qrels and not eval_cases and not doc_paths:
        raise SystemExit(
            "No imported SciFact sample found. Run "
            "`python scripts/import_scifact_sample.py import` first."
        )

    print(f"sample_root={SAMPLE_ROOT}")
    print(f"corpus_documents={len(corpus)}")
    print(f"materialized_docs={len(doc_paths)}")
    print(f"queries={len(queries)}")
    print(f"qrels={len(qrels)}")
    print(f"eval_cases={len(eval_cases)}")

    if corpus:
        first = corpus[0]
        print("\n[corpus preview]")
        print(f"_id={first.get('_id', '')}")
        print(f"title={str(first.get('title', '')).strip()}")
        print(f"text={str(first.get('text', '')).strip()[:280]}")

    if doc_paths:
        first_path = doc_paths[0]
        print("\n[materialized doc preview]")
        print(f"path={first_path}")
        print(first_path.read_text(encoding="utf-8")[:280].strip())

    if queries:
        first = queries[0]
        print("\n[query preview]")
        print(f"_id={first.get('_id', '')}")
        print(f"text={str(first.get('text', '')).strip()}")

    if qrels:
        first = qrels[0]
        print("\n[qrels preview]")
        print(
            "query-id={query_id} corpus-id={corpus_id} score={score}".format(
                query_id=first.get("query-id", ""),
                corpus_id=first.get("corpus-id", ""),
                score=first.get("score", ""),
            )
        )

    if eval_cases:
        first = eval_cases[0]
        print("\n[eval case preview]")
        print(f"question={first.get('question', '')}")
        print(f"expected_document_ids={first.get('expected_document_ids', [])}")
        print(f"metadata={first.get('metadata', {})}")


def _show_full(root: Path) -> None:
    root = root.resolve()
    docs_root = root / "docs"
    queries = _load_json(root / "queries.json")
    qrels_train = _load_json(root / "qrels_train.json")
    qrels_test = _load_json(root / "qrels_test.json")
    doc_paths = sorted(docs_root.glob("*.md")) if docs_root.exists() else []

    if not doc_paths and not queries and not qrels_train and not qrels_test:
        raise SystemExit(
            "No full SciFact export found. Run "
            "`python scripts/import_scifact_sample.py import-full` first."
        )

    print(f"full_root={root}")
    print(f"docs_dir={docs_root}")
    print(f"corpus_documents={len(doc_paths)}")
    print(f"queries={len(queries)}")
    print(f"qrels_train={len(qrels_train)}")
    print(f"qrels_test={len(qrels_test)}")

    if doc_paths:
        first_path = doc_paths[0]
        preview = first_path.read_text(encoding="utf-8")[:280].strip()
        print("\n[doc preview]")
        print(f"path={first_path}")
        print(preview)

    if queries:
        first = queries[0]
        print("\n[query preview]")
        print(f"_id={first.get('_id', '')}")
        print(f"text={str(first.get('text', '')).strip()}")

    if qrels_train:
        first = qrels_train[0]
        print("\n[qrels train preview]")
        print(
            "query-id={query_id} corpus-id={corpus_id} score={score}".format(
                query_id=first.get("query-id", ""),
                corpus_id=first.get("corpus-id", ""),
                score=first.get("score", ""),
            )
        )


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.command == "show":
        _show_sample()
        return
    if args.command == "show-full":
        _show_full(args.full_root)
        return
    if args.command == "import-full":
        _import_full(args.full_root)
        return
    _import_sample(
        max_corpus=max(1, args.max_corpus),
        max_queries=max(1, args.max_queries),
        split=args.split,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
