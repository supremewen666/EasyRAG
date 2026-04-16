"""End-to-end retrieval execution pipeline."""

from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING, Any

from easyrag.rag.retrieval.fusion import combine_mode_results, trim_records
from easyrag.rag.retrieval.hydration import (
    build_citations,
    chunks_to_documents,
    detect_vector_backend,
    hydrate_records,
)
from easyrag.rag.retrieval.provenance import (
    collect_vector_backends,
    query_used_token_fallback,
    select_primary_vector_backend,
)
from easyrag.rag.retrieval.query_modes import run_variant_queries
from easyrag.rag.types import QueryParam, QueryResult

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG


def _duration_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000.0, 3)


def _matches_metadata_filters(
    record: dict[str, object], metadata_filters: dict[str, Any] | None
) -> bool:
    if not metadata_filters:
        return True
    metadata = record.get("metadata", {})
    if not isinstance(metadata, dict):
        return False
    for key, expected in metadata_filters.items():
        actual = metadata.get(key)
        if isinstance(actual, (list, tuple, set)):
            actual_values = {str(value) for value in actual}
            if isinstance(expected, (list, tuple, set)):
                if not {str(value) for value in expected}.issubset(actual_values):
                    return False
            elif str(expected) not in actual_values:
                return False
            continue
        if isinstance(expected, (list, tuple, set)):
            if str(actual) not in {str(value) for value in expected}:
                return False
            continue
        if actual != expected:
            return False
    return True


def _apply_record_filters(
    records: list[dict[str, object]], param: QueryParam
) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    for record in records:
        if param.min_score is not None and float(record.get("score", 0.0)) < float(
            param.min_score
        ):
            continue
        if not _matches_metadata_filters(record, param.metadata_filters):
            continue
        filtered.append(record)
    return filtered


async def execute_query(rag: "EasyRAG", query: str, param: QueryParam) -> QueryResult:
    """Execute one multi-mode query over the active RAG workspace."""

    total_started = perf_counter()
    mode = param.mode.lower().strip()
    prepare_started = perf_counter()
    prepared = rag.query_preprocessor.prepare(query, param)
    prepare_ms = _duration_ms(prepare_started)

    candidate_started = perf_counter()
    (
        naive_hits,
        local_hits,
        global_hits,
        local_entities,
        relation_hits,
        backend_groups,
    ) = await run_variant_queries(
        rag,
        prepared.retrieval_queries,
        param,
    )
    candidate_ms = _duration_ms(candidate_started)

    if mode == "naive":
        selected = naive_hits
    elif mode == "local":
        selected = local_hits
    elif mode == "global":
        selected = global_hits
    elif mode == "hybrid":
        selected = combine_mode_results(param, (1.0, local_hits), (1.0, global_hits))
    elif mode == "mix":
        selected = combine_mode_results(
            param, (1.0, local_hits), (1.0, global_hits), (0.85, naive_hits)
        )
    else:
        raise ValueError(f"Unsupported query mode: {param.mode}")

    pre_filter_count = len(selected)
    filter_started = perf_counter()
    filtered_selected = _apply_record_filters(selected, param)
    filtered_relation_hits = _apply_record_filters(
        relation_hits, QueryParam(min_score=param.min_score)
    )
    filter_ms = _duration_ms(filter_started)

    hydration_started = perf_counter()
    hydrated = await hydrate_records(
        rag, trim_records(filtered_selected, param.chunk_top_k * 3)
    )
    hydration_ms = _duration_ms(hydration_started)
    rerank_applied = False
    rerank_started = perf_counter()
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
    rerank_ms = _duration_ms(rerank_started)

    assemble_started = perf_counter()
    hydrated = trim_records(hydrated, param.chunk_top_k)
    chunks = await chunks_to_documents(hydrated)
    citations = build_citations(chunks)
    observed_vector_backends = collect_vector_backends(
        *backend_groups["chunk"],
        *backend_groups["summary"],
        *backend_groups["entity"],
        *backend_groups["relation"],
    )
    query_vector_backend = select_primary_vector_backend(
        observed_vector_backends,
        default=rag.vector_storage.get_backend_name(),
    )
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
                "source_entity_id": str(
                    item.get("metadata", {}).get("source_entity_id", "")
                ),
                "target_entity_id": str(
                    item.get("metadata", {}).get("target_entity_id", "")
                ),
            }
            for item in trim_records(filtered_relation_hits, param.top_k)
        ],
        metadata={
            "original_query": prepared.original_query,
            "normalized_query": prepared.normalized_query,
            "rewritten_query": prepared.rewritten_query,
            "expanded_queries": prepared.expanded_queries,
            "retrieval_queries": prepared.retrieval_queries,
            "rerank_applied": rerank_applied,
            "chunk_strategies": hit_chunk_strategies,
            "vector_backend": query_vector_backend,
            "vector_backends": sorted(observed_vector_backends),
            "fallback_used": query_used_token_fallback(observed_vector_backends),
            "hydrated_vector_backend": detect_vector_backend(hydrated),
            "filters_applied": {
                "metadata_filters": dict(param.metadata_filters or {}),
                "min_score": param.min_score,
            },
            "candidate_counts": {
                "naive": len(naive_hits),
                "local": len(local_hits),
                "global": len(global_hits),
                "selected_pre_filter": pre_filter_count,
                "selected_post_filter": len(filtered_selected),
                "filtered_out": max(pre_filter_count - len(filtered_selected), 0),
                "hydrated": len(hydrated),
                "relations": len(filtered_relation_hits),
                "final_chunks": len(chunks),
            },
            "stage_timings_ms": {
                "prepare": prepare_ms,
                "candidate_generation": candidate_ms,
                "filtering": filter_ms,
                "hydration": hydration_ms,
                "rerank": rerank_ms,
                "result_assembly": _duration_ms(assemble_started),
                "total": _duration_ms(total_started),
            },
        },
    )
