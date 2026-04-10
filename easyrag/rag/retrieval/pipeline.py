"""End-to-end retrieval execution pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from easyrag.rag.retrieval.fusion import combine_mode_results, trim_records
from easyrag.rag.retrieval.hydration import build_citations, chunks_to_documents, detect_vector_backend, hydrate_records
from easyrag.rag.retrieval.query_modes import run_variant_queries
from easyrag.rag.types import QueryParam, QueryResult

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG


async def execute_query(rag: "EasyRAG", query: str, param: QueryParam) -> QueryResult:
    """Execute one multi-mode query over the active RAG workspace."""

    mode = param.mode.lower().strip()
    prepared = rag.query_preprocessor.prepare(query, param)
    naive_hits, local_hits, global_hits, local_entities, relation_hits = await run_variant_queries(
        rag,
        prepared.retrieval_queries,
        param,
    )

    if mode == "naive":
        selected = naive_hits
    elif mode == "local":
        selected = local_hits
    elif mode == "global":
        selected = global_hits
    elif mode == "hybrid":
        selected = combine_mode_results(param, (1.0, local_hits), (1.0, global_hits))
    elif mode == "mix":
        selected = combine_mode_results(param, (1.0, local_hits), (1.0, global_hits), (0.85, naive_hits))
    else:
        raise ValueError(f"Unsupported query mode: {param.mode}")

    hydrated = await hydrate_records(rag, trim_records(selected, param.chunk_top_k * 3))
    rerank_applied = False
    if mode == "mix" and rag.reranker_func is not None:
        try:
            hydrated = list(rag.reranker_func(prepared.rewritten_query, hydrated))
            rerank_applied = True
        except Exception:
            rerank_applied = False
    elif mode == "hybrid" and param.enable_rerank and rag.reranker_func is not None:
        try:
            hydrated = list(rag.reranker_func(prepared.rewritten_query, hydrated))
            rerank_applied = True
        except Exception:
            rerank_applied = False

    hydrated = trim_records(hydrated, param.chunk_top_k)
    chunks = await chunks_to_documents(hydrated)
    citations = build_citations(chunks)
    hit_chunk_strategies = sorted(
        {
            str(document.metadata.get("chunk_strategy", "unknown"))
            for document in chunks
            if document.metadata.get("chunk_strategy")
        }
    )

    return QueryResult(
        mode=mode,
        chunks=chunks,
        citations=citations,
        entities=local_entities[: param.top_k],
        relations=[
            {
                "id": str(item["id"]),
                "snippet": str(item.get("text", ""))[:200],
                "score": float(item.get("score", 0.0)),
                "relation": str(item.get("metadata", {}).get("relation", "")),
                "source_entity_id": str(item.get("metadata", {}).get("source_entity_id", "")),
                "target_entity_id": str(item.get("metadata", {}).get("target_entity_id", "")),
            }
            for item in trim_records(relation_hits, param.top_k)
        ],
        metadata={
            "original_query": prepared.original_query,
            "normalized_query": prepared.normalized_query,
            "rewritten_query": prepared.rewritten_query,
            "expanded_queries": prepared.expanded_queries,
            "retrieval_queries": prepared.retrieval_queries,
            "rerank_applied": rerank_applied,
            "chunk_strategies": hit_chunk_strategies,
            "vector_backend": detect_vector_backend(hydrated),
        },
    )
