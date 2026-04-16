"""Repository-backed QA demo for EasyRAG."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from easyrag.rag import AnswerParam, EasyRAG, QueryParam  # noqa: E402
from easyrag.support.async_utils import run_sync  # noqa: E402
from scripts.build_index import build_repository_index  # noqa: E402

_KEYWORDS = [
    "architecture",
    "answer",
    "chunk",
    "citation",
    "document",
    "easyrag",
    "embedding",
    "evaluation",
    "generation",
    "graph",
    "hybrid",
    "index",
    "query",
    "rerank",
    "retrieval",
    "rewrite",
    "storage",
]


def _run_async(awaitable: object) -> object:
    """Run async EasyRAG operations from this CLI."""

    return run_sync(awaitable)


def _stub_embedding(texts: list[str]) -> list[list[float]]:
    """Return deterministic dense embeddings for repo-scale demo flows."""

    vectors: list[list[float]] = []
    for text in texts:
        lowered = text.lower()
        vector = [float(lowered.count(keyword)) for keyword in _KEYWORDS]
        vector.append(float(len(lowered.split())))
        vectors.append(vector)
    return vectors


def _stub_query_model(prompt: str, *, task: str, count: int = 1) -> str | list[str]:
    """Return deterministic rewrite and MQE expansions for the QA demo."""

    cleaned = prompt.split(":", 1)[-1].strip()
    if task == "rewrite":
        return f"{cleaned} hybrid retrieval architecture"
    if task == "mqe":
        return [f"{cleaned} evidence variant {index}" for index in range(1, count + 1)]
    raise ValueError(task)


def _stub_reranker(
    query: str, items: list[dict[str, object]]
) -> list[dict[str, object]]:
    """Prefer candidates whose text overlaps most with the rewritten query."""

    lowered_query = query.lower()
    ranked: list[dict[str, object]] = []
    for item in items:
        text = str(item.get("text", "")).lower()
        score = sum(text.count(keyword) for keyword in lowered_query.split())
        candidate = dict(item)
        candidate["rerank_score"] = float(score)
        ranked.append(candidate)
    ranked.sort(key=lambda item: float(item.get("rerank_score", 0.0)), reverse=True)
    return ranked


def _stub_answer_model(
    prompt: str,
    *,
    question: str,
    citations: list[dict[str, str]],
    style: str,
) -> str:
    """Return a short grounded answer from the top citation."""

    del prompt, question, style
    if not citations:
        return ""
    snippet = " ".join(str(citations[0].get("snippet", "")).split())
    sentence = snippet.split(". ", 1)[0].strip()
    if not sentence:
        sentence = snippet[:180].strip()
    if sentence and sentence[-1] not in ".!?":
        sentence = f"{sentence}."
    return f"{sentence} [1]"


class DemoEasyRAG(EasyRAG):
    """EasyRAG subclass wired to deterministic local demo providers."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        kwargs.setdefault("embedding_func", _stub_embedding)
        kwargs.setdefault("query_model_func", _stub_query_model)
        kwargs.setdefault("reranker_func", _stub_reranker)
        kwargs.setdefault("answer_model_func", _stub_answer_model)
        super().__init__(*args, **kwargs)


def _demo_rag_factory(working_dir: Path, workspace: str) -> DemoEasyRAG:
    """Build one deterministic EasyRAG instance for indexing or QA."""

    return DemoEasyRAG(working_dir=working_dir, workspace=workspace)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the QA demo."""

    parser = argparse.ArgumentParser(
        description="Build a repository index, then run retrieval and QA demos."
    )
    parser.add_argument(
        "--query",
        default="How does EasyRAG handle retrieval?",
        help="Question to run against the indexed repository documents.",
    )
    parser.add_argument(
        "--mode",
        choices=("naive", "local", "global", "hybrid", "mix"),
        default="hybrid",
        help="Retrieval mode to use before answer generation.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Maximum number of chunks and citations to retain.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(PROJECT_ROOT),
        help="Repository root whose docs should be indexed before querying.",
    )
    parser.add_argument(
        "--workspace",
        default="test_rag",
        help="Workspace name used for the QA demo index.",
    )
    parser.add_argument(
        "--working-dir",
        default=None,
        help="Optional EasyRAG storage root. Defaults to <repo_root>/.easyrag/rag_storage.",
    )
    parser.add_argument(
        "--index-path",
        default=None,
        help="Optional legacy snapshot path. Defaults to <repo_root>/.easyrag/rag_index.json.",
    )
    return parser.parse_args([] if argv is None else argv)


def _truncate(text: str, *, limit: int = 180) -> str:
    """Return a compact single-line preview."""

    normalized = " ".join(str(text).split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3]}..."


def _resolve_storage_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    """Resolve repo-local storage paths for the demo run."""

    repo_root = Path(args.repo_root).resolve()
    data_dir = repo_root / ".easyrag"
    working_dir = (
        Path(args.working_dir).resolve()
        if args.working_dir is not None
        else data_dir / "rag_storage"
    )
    index_path = (
        Path(args.index_path).resolve()
        if args.index_path is not None
        else data_dir / "rag_index.json"
    )
    return repo_root, working_dir, index_path


def _print_build_section(
    *,
    repo_root: Path,
    workspace: str,
    working_dir: Path,
    index_path: Path,
    summary: dict[str, object],
) -> None:
    """Print the build step summary produced before querying."""

    stats = dict(summary.get("stats", {}) or {})
    aggregate = dict(summary.get("aggregate", {}) or {})
    print("=== EasyRAG QA Demo ===")
    print("Build:")
    print(f"repo_root={repo_root}")
    print(f"workspace={workspace}")
    print(f"working_dir={working_dir / workspace}")
    print(f"index_path={index_path}")
    print(f"action={summary.get('action', 'rebuild')}")
    print(f"targeted_doc_ids={summary.get('targeted_doc_ids', [])}")
    print(f"documents={stats.get('documents', 0)}")
    print(f"pdf_documents={stats.get('pdf_documents', 0)}")
    print(f"chunks={stats.get('chunks', 0)}")
    print(f"vector_backend={aggregate.get('vector_backend', 'unknown')}")
    print(f"chunk_strategy_counts={aggregate.get('chunk_strategy_counts', {})}")
    print()


def _print_retrieval_section(
    *,
    query: str,
    mode: str,
    top_k: int,
    result: object,
) -> None:
    """Print retrieval output before answer synthesis."""

    print("Retrieval:")
    print(f"query={query}")
    print(f"mode={mode}")
    print(f"top_k={top_k}")
    print("Citations:")
    citations = list(getattr(result, "citations", []))
    if not citations:
        print("- none")
    for index, citation in enumerate(citations, start=1):
        print(
            f"- [{index}] title={citation.get('title', 'Document')} "
            f"location={citation.get('location', '')}"
        )
        print(f"  snippet={_truncate(str(citation.get('snippet', '')))}")
    print("Chunks:")
    chunks = list(getattr(result, "chunks", []))
    if not chunks:
        print("- none")
    for index, chunk in enumerate(chunks[:top_k], start=1):
        metadata = getattr(chunk, "metadata", {}) or {}
        print(
            f"- [{index}] doc_id={metadata.get('doc_id', '')} "
            f"chunk_id={metadata.get('chunk_id', '')} "
            f"path={metadata.get('path', '')}"
        )
        print(f"  text={_truncate(getattr(chunk, 'page_content', ''))}")
    print("Metadata:")
    metadata = dict(getattr(result, "metadata", {}) or {})
    for key in (
        "original_query",
        "normalized_query",
        "rewritten_query",
        "expanded_queries",
        "retrieval_queries",
        "vector_backend",
        "fallback_used",
        "candidate_counts",
        "stage_timings_ms",
    ):
        if key in metadata:
            print(f"- {key}={metadata[key]}")
    print()


def _print_answer_section(*, answer: object) -> None:
    """Print grounded answer output for the QA step."""

    metadata = dict(getattr(answer, "metadata", {}) or {})
    print("Answer:")
    print(f"text={getattr(answer, 'answer', '')}")
    if metadata.get("additional_context"):
        print(
            "additional_context="
            f"{_truncate(str(metadata.get('additional_context', '')))}"
        )
    print("Selected citations:")
    selected = list(getattr(answer, "selected_citations", []))
    if not selected:
        print("- none")
    for index, citation in enumerate(selected, start=1):
        print(
            f"- [{index}] title={citation.get('title', 'Document')} "
            f"location={citation.get('location', '')}"
        )
        print(f"  snippet={_truncate(str(citation.get('snippet', '')))}")
    print("Metadata:")
    for key in (
        "retrieval_mode",
        "raw_citation_count",
        "selected_citation_count",
        "context_chars",
        "evidence_support",
        "prior_knowledge_used",
        "additional_context_present",
        "answer_model_used",
        "fallback_used",
        "abstained",
    ):
        if key in metadata:
            print(f"- {key}={metadata[key]}")


def main(argv: list[str] | None = None) -> None:
    """Build a repo index, then run retrieval and answer generation demos."""

    args = _parse_args(argv)
    repo_root, working_dir, index_path = _resolve_storage_paths(args)
    summary = build_repository_index(
        action="rebuild",
        repo_root=repo_root,
        working_dir=working_dir,
        workspace=args.workspace,
        index_path=index_path,
        rag_factory=_demo_rag_factory,
    )
    rag = DemoEasyRAG(working_dir=working_dir, workspace=args.workspace)
    _run_async(rag.initialize_storages())
    try:
        retrieval_result = _run_async(
            rag.aquery(
                args.query,
                QueryParam(
                    mode=args.mode,
                    top_k=args.top_k,
                    chunk_top_k=args.top_k,
                    enable_rerank=args.mode in {"hybrid", "mix"},
                ),
            )
        )
        answer_result = _run_async(
            rag.aanswer(
                args.query,
                QueryParam(
                    mode=args.mode,
                    top_k=args.top_k,
                    chunk_top_k=args.top_k,
                    enable_rerank=args.mode in {"hybrid", "mix"},
                ),
                AnswerParam(
                    max_citations=max(1, min(args.top_k, 3)),
                    max_context_chars=420,
                ),
            )
        )
    finally:
        _run_async(rag.finalize_storages())

    _print_build_section(
        repo_root=repo_root,
        workspace=args.workspace,
        working_dir=working_dir,
        index_path=index_path,
        summary=summary,
    )
    _print_retrieval_section(
        query=args.query,
        mode=args.mode,
        top_k=args.top_k,
        result=retrieval_result,
    )
    _print_answer_section(answer=answer_result)


if __name__ == "__main__":
    main(sys.argv[1:])
