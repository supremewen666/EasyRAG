"""Query-mode candidate generation for retrieval."""

from __future__ import annotations

from typing import TYPE_CHECKING

from easyrag.rag.retrieval.fusion import merge_ranked_records, rrf_fuse
from easyrag.rag.types import QueryParam
from easyrag.rag.utils import dedupe_strings, extract_entity_candidates

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG


async def naive_query(
    rag: "EasyRAG", query: str, param: QueryParam
) -> list[dict[str, object]]:
    """Retrieve chunks directly from the chunk vector namespace."""

    return await rag.vector_storage.similarity_search("chunk", query, param.chunk_top_k)


async def local_query(
    rag: "EasyRAG", query: str, param: QueryParam
) -> tuple[list[dict[str, object]], list[str], dict[str, list[dict[str, object]]]]:
    """Retrieve chunks related to query-time entities plus dense backfill."""

    extracted_entities = extract_entity_candidates(query, {"title": query, "path": ""})
    entity_hits = await rag.vector_storage.similarity_search(
        "entity", query, param.top_k
    )
    resolved_entities = await rag.graph_storage.resolve_entity_ids(
        extracted_entities, limit=param.top_k
    )
    entity_ids = [str(item["id"]) for item in resolved_entities]
    entity_ids.extend(
        str(item["id"]) for item in entity_hits if str(item["id"]) not in entity_ids
    )
    entities = dedupe_strings(
        [
            str(item.get("label", ""))
            for item in resolved_entities
            if str(item.get("label", "")).strip()
        ]
        + extracted_entities
        + [
            str(item.get("metadata", {}).get("label", item.get("text", "")))
            for item in entity_hits
        ]
    )
    neighbors = await rag.graph_storage.get_neighbors(
        entity_ids, kind_filter="chunk", limit=param.chunk_top_k
    )
    dense_backfill = await rag.vector_storage.similarity_search(
        "chunk", query, param.chunk_top_k
    )
    selected = merge_ranked_records([(1.0, neighbors), (0.6, dense_backfill)])
    return selected, entities, {"entity": entity_hits, "chunk": dense_backfill}


async def global_query(
    rag: "EasyRAG", query: str, param: QueryParam
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, list[dict[str, object]]],
]:
    """Retrieve broad context from summaries, central entities, and dense backfill."""

    summary_hits = await rag.vector_storage.similarity_search(
        "summary", query, param.top_k
    )
    central_entities = await rag.graph_storage.top_nodes(
        kind="entity", limit=param.top_k
    )
    central_neighbors = await rag.graph_storage.get_neighbors(
        [str(item["id"]) for item in central_entities],
        kind_filter="chunk",
        limit=param.chunk_top_k,
    )
    dense_backfill = await rag.vector_storage.similarity_search(
        "chunk", query, param.chunk_top_k
    )
    merged = merge_ranked_records(
        [(1.0, summary_hits), (0.7, central_neighbors), (0.4, dense_backfill)]
    )
    return merged, central_entities, {
        "summary": summary_hits,
        "chunk": dense_backfill,
    }


async def run_variant_queries(
    rag: "EasyRAG",
    retrieval_queries: list[str],
    param: QueryParam,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[str],
    list[dict[str, object]],
    dict[str, list[list[dict[str, object]]]],
]:
    """Run naive/local/global retrieval for each prepared query variant."""

    naive_groups: list[list[dict[str, object]]] = []
    local_groups: list[list[dict[str, object]]] = []
    global_groups: list[list[dict[str, object]]] = []
    relation_groups: list[list[dict[str, object]]] = []
    backend_groups: dict[str, list[list[dict[str, object]]]] = {
        "chunk": [],
        "summary": [],
        "entity": [],
        "relation": [],
    }
    entities: list[str] = []
    central_entities: list[dict[str, object]] = []

    for retrieval_query in retrieval_queries:
        naive_hits = await naive_query(rag, retrieval_query, param)
        naive_groups.append(naive_hits)
        backend_groups["chunk"].append(naive_hits)
        local_hits, local_entities, local_backend_groups = await local_query(
            rag, retrieval_query, param
        )
        global_hits, global_central, global_backend_groups = await global_query(
            rag, retrieval_query, param
        )
        local_groups.append(local_hits)
        global_groups.append(global_hits)
        relation_hits = await rag.vector_storage.similarity_search(
            "relation", retrieval_query, param.top_k
        )
        relation_groups.append(relation_hits)
        backend_groups["relation"].append(relation_hits)
        backend_groups["entity"].append(local_backend_groups["entity"])
        backend_groups["chunk"].append(local_backend_groups["chunk"])
        backend_groups["summary"].append(global_backend_groups["summary"])
        backend_groups["chunk"].append(global_backend_groups["chunk"])
        entities.extend(local_entities)
        if not central_entities:
            central_entities = global_central

    return (
        rrf_fuse(naive_groups),
        rrf_fuse(local_groups),
        rrf_fuse(global_groups),
        dedupe_strings(entities),
        rrf_fuse(relation_groups),
        backend_groups,
    )
