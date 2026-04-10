"""Query-mode candidate generation for retrieval."""

from __future__ import annotations

from typing import TYPE_CHECKING

from easyrag.rag.retrieval.fusion import merge_ranked_records, rrf_fuse
from easyrag.rag.types import QueryParam
from easyrag.rag.utils import dedupe_strings, extract_entity_candidates

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG


async def naive_query(rag: "EasyRAG", query: str, param: QueryParam) -> list[dict[str, object]]:
    """Retrieve chunks directly from the chunk vector namespace."""

    return await rag.vector_storage.similarity_search("chunk", query, param.chunk_top_k)


async def local_query(rag: "EasyRAG", query: str, param: QueryParam) -> tuple[list[dict[str, object]], list[str]]:
    """Retrieve chunks related to query-time entities plus dense backfill."""

    extracted_entities = extract_entity_candidates(query, {"title": query, "path": ""})
    entity_hits = await rag.vector_storage.similarity_search("entity", query, param.top_k)
    resolved_entities = await rag.graph_storage.resolve_entity_ids(extracted_entities, limit=param.top_k)
    entity_ids = [str(item["id"]) for item in resolved_entities]
    entity_ids.extend(str(item["id"]) for item in entity_hits if str(item["id"]) not in entity_ids)
    entities = dedupe_strings(
        [str(item.get("label", "")) for item in resolved_entities if str(item.get("label", "")).strip()]
        + extracted_entities
        + [str(item.get("metadata", {}).get("label", item.get("text", ""))) for item in entity_hits]
    )
    neighbors = await rag.graph_storage.get_neighbors(entity_ids, kind_filter="chunk", limit=param.chunk_top_k)
    dense_backfill = await rag.vector_storage.similarity_search("chunk", query, param.chunk_top_k)
    selected = merge_ranked_records([(1.0, neighbors), (0.6, dense_backfill)])
    return selected, entities


async def global_query(rag: "EasyRAG", query: str, param: QueryParam) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Retrieve broad context from summaries, central entities, and dense backfill."""

    summary_hits = await rag.vector_storage.similarity_search("summary", query, param.top_k)
    central_entities = await rag.graph_storage.top_nodes(kind="entity", limit=param.top_k)
    central_neighbors = await rag.graph_storage.get_neighbors(
        [str(item["id"]) for item in central_entities],
        kind_filter="chunk",
        limit=param.chunk_top_k,
    )
    dense_backfill = await rag.vector_storage.similarity_search("chunk", query, param.chunk_top_k)
    merged = merge_ranked_records([(1.0, summary_hits), (0.7, central_neighbors), (0.4, dense_backfill)])
    return merged, central_entities


async def run_variant_queries(
    rag: "EasyRAG",
    retrieval_queries: list[str],
    param: QueryParam,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[str], list[dict[str, object]]]:
    """Run naive/local/global retrieval for each prepared query variant."""

    naive_groups: list[list[dict[str, object]]] = []
    local_groups: list[list[dict[str, object]]] = []
    global_groups: list[list[dict[str, object]]] = []
    relation_groups: list[list[dict[str, object]]] = []
    entities: list[str] = []
    central_entities: list[dict[str, object]] = []

    for retrieval_query in retrieval_queries:
        naive_groups.append(await naive_query(rag, retrieval_query, param))
        local_hits, local_entities = await local_query(rag, retrieval_query, param)
        global_hits, global_central = await global_query(rag, retrieval_query, param)
        local_groups.append(local_hits)
        global_groups.append(global_hits)
        relation_groups.append(await rag.vector_storage.similarity_search("relation", retrieval_query, param.top_k))
        entities.extend(local_entities)
        if not central_entities:
            central_entities = global_central

    return (
        rrf_fuse(naive_groups),
        rrf_fuse(local_groups),
        rrf_fuse(global_groups),
        dedupe_strings(entities),
        rrf_fuse(relation_groups),
    )
