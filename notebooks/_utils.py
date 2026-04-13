from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterator

from easyrag.rag import EasyRAG
from easyrag.rag.providers import can_use_openai_compatible_models
from easyrag.support.async_utils import run_sync

NOTEBOOK_KEYWORDS = [
    "architecture",
    "easyrag",
    "embedding",
    "grounded",
    "retrieval",
    "query",
    "rewrite",
    "storage",
    "rerank",
    "policy",
    "citation",
    "prompt",
]


def ensure_repo_root_on_path() -> Path:
    import sys

    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "easyrag").exists():
            root = candidate.resolve()
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            return root
    raise RuntimeError("Could not locate the EasyRAG repository root from the current working directory.")


def stub_embedding(texts: list[str], *, keywords: list[str] | None = None) -> list[list[float]]:
    active_keywords = keywords or NOTEBOOK_KEYWORDS
    vectors: list[list[float]] = []
    for text in texts:
        lowered = str(text).lower()
        vector = [float(lowered.count(keyword)) for keyword in active_keywords]
        vector.append(float(len(lowered.split())))
        vectors.append(vector)
    return vectors


def stub_query_model(prompt: str, *, task: str, count: int = 1) -> str | list[str]:
    cleaned = prompt.split(":", 1)[-1].strip()
    if task == "rewrite":
        return f"{cleaned} grounded retrieval"
    if task == "mqe":
        return [f"{cleaned} variant {index}" for index in range(1, count + 1)]
    raise ValueError(task)


def stub_reranker(query: str, items: list[dict[str, object]]) -> list[dict[str, object]]:
    lowered_query = query.lower()
    scored: list[dict[str, object]] = []
    for item in items:
        text = str(item.get("text", "")).lower()
        score = sum(text.count(keyword) for keyword in lowered_query.split())
        candidate = dict(item)
        candidate["rerank_score"] = score
        scored.append(candidate)
    scored.sort(key=lambda item: float(item.get("rerank_score", 0.0)), reverse=True)
    return scored


def print_json(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def provider_ready() -> bool:
    return can_use_openai_compatible_models()


def production_backends_ready() -> bool:
    return bool(os.environ.get("EASYRAG_POSTGRES_DSN")) and bool(os.environ.get("EASYRAG_QDRANT_URL"))


def list_workspace_files(workspace_root: str | Path) -> list[str]:
    root = Path(workspace_root)
    return [str(path.relative_to(root)) for path in sorted(root.rglob("*")) if path.is_file()]


@contextmanager
def managed_demo_rag(
    workspace: str,
    *,
    working_dir: str | None = None,
    embedding_func=stub_embedding,
    query_model_func=stub_query_model,
    answer_model_func=None,
    **kwargs: Any,
) -> Iterator[tuple[EasyRAG, Path, Path]]:
    tmp_dir: TemporaryDirectory[str] | None = None
    if working_dir is None:
        tmp_dir = TemporaryDirectory()
        working_dir = tmp_dir.name
    root = Path(working_dir)
    rag = EasyRAG(
        working_dir=str(root),
        workspace=workspace,
        embedding_func=embedding_func,
        query_model_func=query_model_func,
        answer_model_func=answer_model_func,
        **kwargs,
    )
    run_sync(rag.initialize_storages())
    try:
        yield rag, root, root / workspace
    finally:
        try:
            run_sync(rag.finalize_storages())
        finally:
            if tmp_dir is not None:
                tmp_dir.cleanup()


def skip_message(kind: str) -> str:
    if kind == "provider":
        return "Skipping provider-backed path because OPENAI-compatible config is not set."
    if kind == "production":
        return "Skipping production-backed path because PostgreSQL/Qdrant configuration is not set."
    return "Skipping optional path because configuration is not set."
