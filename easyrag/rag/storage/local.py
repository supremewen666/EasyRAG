"""Built-in single-node storage backends for EasyRAG's EasyRAG subsystem."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np

from easyrag.rag.knowledge.extraction import summarize_entity_descriptions
from easyrag.rag.storage.base import BaseDocStatusStorage, BaseGraphStorage, BaseKVStorage, BaseVectorStorage
from easyrag.rag.utils import dedupe_strings

try:
    import hnswlib
except ImportError:  # pragma: no cover - optional dependency.
    hnswlib = None

try:
    import networkx as nx
except ImportError:  # pragma: no cover - optional dependency.
    nx = None

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    """Return lowercase lexical tokens for deterministic retrieval."""

    return _TOKEN_PATTERN.findall(text.lower())


def _read_json(path: Path, default: Any) -> Any:
    """Read JSON data if the file exists, otherwise return a default value."""

    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload: Any) -> None:
    """Persist JSON using UTF-8 and stable pretty printing."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _merge_owner_maps(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge per-document entity ownership metadata."""

    merged = deepcopy(existing)
    for doc_id, payload in incoming.items():
        current = merged.setdefault(str(doc_id), {"count": 0, "types": [], "descriptions": []})
        current["count"] = int(current.get("count", 0)) + int(payload.get("count", 0))
        current["types"] = sorted(set(list(current.get("types", [])) + list(payload.get("types", []))))
        current["descriptions"] = dedupe_strings(
            [str(value).strip() for value in list(current.get("descriptions", [])) + list(payload.get("descriptions", [])) if str(value).strip()]
        )
    return merged


def _refresh_entity_node(node: dict[str, Any]) -> dict[str, Any]:
    """Refresh aggregate fields derived from entity ownership metadata."""

    owners = {
        str(doc_id): payload
        for doc_id, payload in dict(node.get("owners", {})).items()
        if int(payload.get("count", 0)) > 0
    }
    node["owners"] = owners
    node["doc_ids"] = sorted(owners)
    base_entity_types = [str(entity_type).strip() for entity_type in list(node.get("manual_entity_types", [])) if str(entity_type).strip()]
    if not base_entity_types:
        base_entity_types = [str(entity_type).strip() for entity_type in list(node.get("entity_types", [])) if str(entity_type).strip()]
    node["entity_types"] = sorted(
        {
            str(entity_type)
            for entity_type in base_entity_types
            if str(entity_type).strip()
        }
        | {
            str(entity_type)
            for payload in owners.values()
            for entity_type in payload.get("types", [])
            if str(entity_type).strip()
        }
    )
    manual_description = str(node.get("manual_description", "")).strip()
    if not manual_description and not owners:
        manual_description = str(node.get("description", "")).strip()
    node["manual_description"] = manual_description
    node["description"] = summarize_entity_descriptions(
        ([manual_description] if manual_description else [])
        + [
            str(description)
            for payload in owners.values()
            for description in payload.get("descriptions", [])
            if str(description).strip()
        ]
    )
    node["owner_count"] = sum(int(payload.get("count", 0)) for payload in owners.values())
    return node


def _merge_node_payload(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge one graph node payload into an existing node."""

    merged = {**existing, **incoming}
    if merged.get("kind") == "entity":
        manual_entity_types = dedupe_strings(
            [
                str(value).strip()
                for value in list(existing.get("manual_entity_types", []))
                + list(incoming.get("manual_entity_types", []))
                + list(incoming.get("entity_types", []))
                if str(value).strip()
            ]
        )
        merged["manual_entity_types"] = manual_entity_types
        incoming_manual_description = str(incoming.get("manual_description", "")).strip() or str(incoming.get("description", "")).strip()
        existing_manual_description = str(existing.get("manual_description", "")).strip()
        merged["manual_description"] = incoming_manual_description or existing_manual_description
        merged["aliases"] = dedupe_strings(
            [str(value).strip() for value in list(existing.get("aliases", [])) + list(incoming.get("aliases", [])) if str(value).strip()]
        )
        merged["provenance"] = dedupe_strings(
            [str(value).strip() for value in list(existing.get("provenance", [])) + list(incoming.get("provenance", [])) if str(value).strip()]
        )
        merged["metadata"] = {**dict(existing.get("metadata", {})), **dict(incoming.get("metadata", {}))}
        merged["owners"] = _merge_owner_maps(
            dict(existing.get("owners", {})),
            dict(incoming.get("owners", {})),
        )
        return _refresh_entity_node(merged)
    return merged


def _merge_contributions(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge per-document relation contribution metadata."""

    merged = deepcopy(existing)
    for doc_id, payload in incoming.items():
        current = merged.setdefault(str(doc_id), {"weight": 0.0, "relations": [], "descriptions": [], "chunk_ids": []})
        current["weight"] = float(current.get("weight", 0.0)) + float(payload.get("weight", 0.0))
        current["relations"] = sorted(set(list(current.get("relations", [])) + list(payload.get("relations", []))))
        current["descriptions"] = dedupe_strings(
            [str(value).strip() for value in list(current.get("descriptions", [])) + list(payload.get("descriptions", [])) if str(value).strip()]
        )
        current["chunk_ids"] = sorted(set(list(current.get("chunk_ids", [])) + list(payload.get("chunk_ids", []))))
    return merged


def _refresh_contributed_edge(edge: dict[str, Any]) -> dict[str, Any]:
    """Refresh aggregate edge fields from contribution metadata."""

    contributions = {
        str(doc_id): payload
        for doc_id, payload in dict(edge.get("contributions", {})).items()
        if float(payload.get("weight", 0.0)) > 0
    }
    edge["contributions"] = contributions
    edge["weight"] = sum(float(payload.get("weight", 0.0)) for payload in contributions.values())
    edge["relations"] = sorted(
        {
            str(relation)
            for payload in contributions.values()
            for relation in payload.get("relations", [])
            if str(relation).strip()
        }
    )
    edge["doc_ids"] = sorted(contributions)
    edge["description"] = summarize_entity_descriptions(
        [
            str(description)
            for payload in contributions.values()
            for description in payload.get("descriptions", [])
            if str(description).strip()
        ]
    )
    return edge


def _merge_edge_payload(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge one graph edge payload into an existing edge."""

    if incoming.get("contributions") or existing.get("contributions"):
        merged = {**existing, **incoming}
        merged["contributions"] = _merge_contributions(
            dict(existing.get("contributions", {})),
            dict(incoming.get("contributions", {})),
        )
        return _refresh_contributed_edge(merged)

    merged = {**existing, **incoming}
    merged["weight"] = float(existing.get("weight", 0.0)) + float(incoming.get("weight", 0.0))
    merged["relations"] = sorted(
        set(list(existing.get("relations", [])) + list(incoming.get("relations", [])) + [str(incoming.get("relation", "")).strip()])
        - {""}
    )
    return merged


def _is_document_owned_node(node_id: str, node: dict[str, Any], document_id: str) -> bool:
    """Return whether a graph node is owned by one document."""

    if node_id == document_id or node_id == f"summary::{document_id}" or node_id.startswith(f"{document_id}::chunk::"):
        return True
    if str(node.get("document_id", "")) == document_id:
        return True
    if str(node.get("doc_id", "")) == document_id and node.get("kind") in {"document", "summary", "chunk"}:
        return True
    return False


def _normalize_relation_record(relation: dict[str, Any]) -> dict[str, Any]:
    """Normalize one first-class semantic relation record."""

    metadata = dict(relation.get("metadata", {}))
    provenance = dedupe_strings(
        [str(value).strip() for value in list(relation.get("provenance", [])) if str(value).strip()]
    )
    if not provenance and str(metadata.get("doc_id", "")).strip():
        provenance.append(str(metadata["doc_id"]).strip())
    return {
        "id": str(relation["id"]),
        "source_entity_id": str(relation["source_entity_id"]),
        "target_entity_id": str(relation["target_entity_id"]),
        "relation": str(relation.get("relation", "related_to")).strip() or "related_to",
        "description": str(relation.get("description", "")).strip(),
        "weight": float(relation.get("weight", 1.0)),
        "metadata": metadata,
        "provenance": provenance,
    }


class JSONKVStorage(BaseKVStorage):
    """Persist documents, chunks, summaries, and cache entries in JSON files."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        root = Path(working_dir) / workspace / "kv"
        self._root = root
        self._documents_path = root / "documents.json"
        self._chunks_path = root / "chunks.json"
        self._summaries_path = root / "summaries.json"
        self._cache_path = root / "cache.json"
        self._documents: dict[str, dict[str, Any]] = {}
        self._chunks: dict[str, dict[str, Any]] = {}
        self._summaries: dict[str, dict[str, Any]] = {}
        self._cache: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        self._documents = _read_json(self._documents_path, {})
        self._chunks = _read_json(self._chunks_path, {})
        self._summaries = _read_json(self._summaries_path, {})
        self._cache = _read_json(self._cache_path, {})

    async def finalize(self) -> None:
        _write_json(self._documents_path, self._documents)
        _write_json(self._chunks_path, self._chunks)
        _write_json(self._summaries_path, self._summaries)
        _write_json(self._cache_path, self._cache)

    async def upsert_documents(self, items: list[dict[str, Any]]) -> None:
        for item in items:
            self._documents[str(item["id"])] = item

    async def upsert_chunks(self, items: list[dict[str, Any]]) -> None:
        for item in items:
            self._chunks[str(item["id"])] = item

    async def upsert_summaries(self, items: list[dict[str, Any]]) -> None:
        for item in items:
            self._summaries[str(item["id"])] = item

    async def delete_by_document(self, document_id: str) -> dict[str, int]:
        deleted_documents = 0
        deleted_chunks = 0
        deleted_summaries = 0
        if document_id in self._documents:
            self._documents.pop(document_id, None)
            deleted_documents += 1

        for chunk_id in [chunk_id for chunk_id, chunk in self._chunks.items() if str(chunk.get("document_id", "")) == document_id]:
            self._chunks.pop(chunk_id, None)
            deleted_chunks += 1

        for summary_id in [
            summary_id
            for summary_id, summary in self._summaries.items()
            if str(summary.get("document_id", "")) == document_id or str(summary.get("metadata", {}).get("doc_id", "")) == document_id
        ]:
            self._summaries.pop(summary_id, None)
            deleted_summaries += 1

        summary_key = f"summary::{document_id}"
        if summary_key in self._summaries:
            self._summaries.pop(summary_key, None)
            deleted_summaries += 1

        return {
            "documents": deleted_documents,
            "chunks": deleted_chunks,
            "summaries": deleted_summaries,
        }

    async def upsert_cache(self, namespace: str, key: str, value: Any) -> None:
        bucket = self._cache.setdefault(namespace, {})
        bucket[key] = value

    async def get_document(self, document_id: str) -> dict[str, Any] | None:
        return self._documents.get(document_id)

    async def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        return self._chunks.get(chunk_id)

    async def get_chunks(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        return [self._chunks[chunk_id] for chunk_id in chunk_ids if chunk_id in self._chunks]

    async def get_summary(self, summary_id: str) -> dict[str, Any] | None:
        return self._summaries.get(summary_id)

    async def get_stats(self) -> dict[str, Any]:
        chunk_strategy_counts: dict[str, int] = {}
        for chunk in self._chunks.values():
            strategy = str(chunk.get("metadata", {}).get("chunk_strategy", "unknown"))
            chunk_strategy_counts[strategy] = chunk_strategy_counts.get(strategy, 0) + 1
        pdf_documents = sum(1 for item in self._documents.values() if item.get("metadata", {}).get("source_type") == "pdf")
        return {
            "documents": len(self._documents),
            "chunks": len(self._chunks),
            "summaries": len(self._summaries),
            "cache_entries": sum(len(bucket) for bucket in self._cache.values()),
            "pdf_documents": pdf_documents,
            "chunk_strategy_counts": chunk_strategy_counts,
        }


class TokenVectorStorage(BaseVectorStorage):
    """Sparse token-overlap retrieval backend with namespace isolation."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        self._path = Path(working_dir) / workspace / "token_vector_store.json"
        self._store: dict[str, dict[str, dict[str, Any]]] = {}

    async def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        raw_store = _read_json(self._path, {})
        self._store = {
            str(namespace): {str(item_id): dict(payload) for item_id, payload in dict(bucket).items()}
            for namespace, bucket in dict(raw_store).items()
        }

    async def finalize(self) -> None:
        _write_json(self._path, self._store)

    async def upsert(self, namespace: str, items: list[dict[str, Any]]) -> None:
        bucket = self._store.setdefault(namespace, {})
        for item in items:
            payload = dict(item)
            text = str(payload.get("text", ""))
            payload["tokens"] = payload.get("tokens") or _tokenize(text)
            bucket[str(payload["id"])] = payload

    async def delete(self, namespace: str, ids: list[str]) -> int:
        bucket = self._store.get(namespace, {})
        deleted = 0
        for item_id in ids:
            if bucket.pop(str(item_id), None) is not None:
                deleted += 1
        return deleted

    async def delete_by_document(self, document_id: str) -> dict[str, int]:
        deleted: dict[str, int] = {}
        for namespace, bucket in self._store.items():
            if namespace == "entity":
                deleted[namespace] = 0
                continue
            removable_ids = [
                item_id
                for item_id, payload in bucket.items()
                if str(payload.get("metadata", {}).get("doc_id", "")) == document_id
            ]
            deleted[namespace] = await self.delete(namespace, removable_ids)
        return deleted

    async def similarity_search(self, namespace: str, query: str, top_k: int) -> list[dict[str, Any]]:
        bucket = self._store.get(namespace, {})
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        query_token_set = set(query_tokens)
        ranked: list[tuple[tuple[int, int, int], dict[str, Any]]] = []
        for item in bucket.values():
            tokens = list(item.get("tokens", []))
            token_set = set(tokens)
            overlap = len(query_token_set & token_set)
            frequency = sum(tokens.count(token) for token in query_tokens)
            phrase_bonus = 1 if query.lower() in str(item.get("text", "")).lower() else 0
            if overlap == 0 and frequency == 0 and phrase_bonus == 0:
                continue
            ranked.append(((overlap, frequency, phrase_bonus), item))

        ranked.sort(key=lambda item: item[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, payload in ranked[:top_k]:
            item = dict(payload)
            item["score"] = score[0] * 100 + score[1] * 10 + score[2]
            item["vector_backend"] = "fallback_token"
            results.append(item)
        return results

    async def get_stats(self) -> dict[str, Any]:
        return {namespace: len(bucket) for namespace, bucket in self._store.items()}

    def get_backend_name(self) -> str:
        return "fallback_token"


class EmbeddingVectorStorage(BaseVectorStorage):
    """HNSW retrieval with dense and token-overlap fallbacks."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        self._root = Path(working_dir) / workspace / "vector"
        self._records: dict[str, dict[str, dict[str, Any]]] = {}
        self._embeddings: dict[str, dict[str, np.ndarray]] = {}
        self._hnsw_indexes: dict[str, Any] = {}
        self._hnsw_labels: dict[str, list[str]] = {}
        self._embedding_func = None
        self._token_fallback = TokenVectorStorage(working_dir, workspace)

    def set_embedding_func(self, embedding_func):
        self._embedding_func = embedding_func

    async def initialize(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        await self._token_fallback.initialize()
        for json_path in self._root.glob("*.json"):
            namespace = json_path.stem
            raw_records = _read_json(json_path, [])
            if isinstance(raw_records, dict):
                ordered_records = [dict(payload) for payload in raw_records.values()]
            else:
                ordered_records = [dict(payload) for payload in raw_records]
            self._records[namespace] = {str(record["id"]): record for record in ordered_records}
            embedding_bucket: dict[str, np.ndarray] = {}
            npy_path = self._root / f"{namespace}.npy"
            if npy_path.exists():
                try:
                    matrix = np.load(npy_path)
                except Exception:
                    matrix = np.zeros((0, 0), dtype=np.float32)
                if matrix.ndim == 2 and len(ordered_records) == matrix.shape[0]:
                    for index, record in enumerate(ordered_records):
                        embedding_bucket[str(record["id"])] = np.array(matrix[index], dtype=np.float32)
            self._embeddings[namespace] = embedding_bucket
            self._rebuild_hnsw_index(namespace)

    async def finalize(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        for namespace, bucket in self._records.items():
            records = list(bucket.values())
            _write_json(self._root / f"{namespace}.json", records)
            embedding_bucket = self._embeddings.get(namespace, {})
            if records and embedding_bucket:
                dimension = next((int(vector.shape[0]) for vector in embedding_bucket.values() if vector.ndim == 1), 0)
                if dimension > 0:
                    matrix = np.stack(
                        [
                            np.array(embedding_bucket.get(str(record["id"]), np.zeros(dimension, dtype=np.float32)), dtype=np.float32)
                            for record in records
                        ]
                    )
                else:
                    matrix = np.zeros((0, 0), dtype=np.float32)
            else:
                matrix = np.zeros((0, 0), dtype=np.float32)
            np.save(self._root / f"{namespace}.npy", matrix)
        await self._token_fallback.finalize()

    async def upsert(self, namespace: str, items: list[dict[str, Any]]) -> None:
        bucket = self._records.setdefault(namespace, {})
        embedding_bucket = self._embeddings.setdefault(namespace, {})
        changed_ids: list[str] = []
        changed_payloads: list[dict[str, Any]] = []
        for item in items:
            payload = dict(item)
            payload["tokens"] = payload.get("tokens") or _tokenize(str(payload.get("text", "")))
            item_id = str(payload["id"])
            if bucket.get(item_id) != payload:
                changed_ids.append(item_id)
                changed_payloads.append(payload)
            bucket[item_id] = payload

        await self._token_fallback.upsert(namespace, list(bucket.values()))
        if not changed_ids:
            return

        embeddings = await self._embed_records(changed_payloads)
        if embeddings.size and embeddings.shape[0] == len(changed_payloads):
            for index, payload in enumerate(changed_payloads):
                embedding_bucket[str(payload["id"])] = np.array(embeddings[index], dtype=np.float32)
            self._rebuild_hnsw_index(namespace)
            return

        dimension = next((int(vector.shape[0]) for vector in embedding_bucket.values() if vector.ndim == 1), 0)
        if dimension > 0:
            for payload in changed_payloads:
                embedding_bucket[str(payload["id"])] = np.zeros(dimension, dtype=np.float32)
        else:
            for payload in changed_payloads:
                embedding_bucket.pop(str(payload["id"]), None)
        self._rebuild_hnsw_index(namespace)

    async def delete(self, namespace: str, ids: list[str]) -> int:
        bucket = self._records.get(namespace, {})
        embedding_bucket = self._embeddings.get(namespace, {})
        deleted = 0
        for item_id in ids:
            normalized = str(item_id)
            if bucket.pop(normalized, None) is not None:
                deleted += 1
            embedding_bucket.pop(normalized, None)
        await self._token_fallback.delete(namespace, ids)
        self._rebuild_hnsw_index(namespace)
        return deleted

    async def delete_by_document(self, document_id: str) -> dict[str, int]:
        deleted: dict[str, int] = {}
        for namespace, bucket in self._records.items():
            if namespace == "entity":
                deleted[namespace] = 0
                continue
            removable_ids = [
                item_id
                for item_id, payload in bucket.items()
                if str(payload.get("metadata", {}).get("doc_id", "")) == document_id
            ]
            deleted[namespace] = await self.delete(namespace, removable_ids)
        return deleted

    async def _embed_records(self, records: list[dict[str, Any]]) -> np.ndarray:
        if not records or self._embedding_func is None:
            return np.zeros((0, 0), dtype=np.float32)
        try:
            inputs = [record.get("embedding_input", str(record.get("text", ""))) for record in records]
            values = self._embedding_func(inputs)
            embeddings = np.array(values, dtype=np.float32)
            if embeddings.ndim != 2 or len(embeddings) != len(records):
                return np.zeros((0, 0), dtype=np.float32)
            return embeddings
        except Exception:
            return np.zeros((0, 0), dtype=np.float32)

    def _rebuild_hnsw_index(self, namespace: str) -> None:
        self._hnsw_indexes.pop(namespace, None)
        self._hnsw_labels.pop(namespace, None)
        if hnswlib is None:
            return

        bucket = self._records.get(namespace, {})
        embedding_bucket = self._embeddings.get(namespace, {})
        record_ids = [item_id for item_id in bucket if item_id in embedding_bucket]
        if not record_ids:
            return

        try:
            embeddings = np.stack([embedding_bucket[item_id] for item_id in record_ids]).astype(np.float32)
        except Exception:
            return
        if embeddings.ndim != 2 or embeddings.shape[0] == 0 or embeddings.shape[1] == 0:
            return

        try:
            index = hnswlib.Index(space="cosine", dim=int(embeddings.shape[1]))
            index.init_index(max_elements=len(record_ids), ef_construction=max(100, min(400, len(record_ids) * 4)), M=16)
            index.add_items(embeddings, np.arange(len(record_ids), dtype=np.int32))
            index.set_ef(max(50, min(200, len(record_ids))))
        except Exception:
            return

        self._hnsw_indexes[namespace] = index
        self._hnsw_labels[namespace] = record_ids

    async def _dense_similarity_search(self, namespace: str, query: str, top_k: int) -> list[dict[str, Any]]:
        bucket = self._records.get(namespace, {})
        embedding_bucket = self._embeddings.get(namespace, {})
        if self._embedding_func is None or not embedding_bucket:
            return []
        try:
            record_ids = [item_id for item_id in bucket if item_id in embedding_bucket]
            if not record_ids:
                return []
            embeddings = np.stack([embedding_bucket[item_id] for item_id in record_ids])
            query_embedding = np.array(self._embedding_func([query]), dtype=np.float32)
            if query_embedding.ndim != 2 or query_embedding.shape[0] != 1 or query_embedding.shape[1] != embeddings.shape[1]:
                return []
            normalized_records = embeddings / np.maximum(np.linalg.norm(embeddings, axis=1, keepdims=True), 1e-12)
            normalized_query = query_embedding / np.maximum(np.linalg.norm(query_embedding, axis=1, keepdims=True), 1e-12)
            scores = normalized_records @ normalized_query[0]
            ranked_indices = np.argsort(scores)[::-1][:top_k]
            results: list[dict[str, Any]] = []
            for index in ranked_indices:
                if float(scores[index]) <= 0:
                    continue
                item_id = record_ids[int(index)]
                item = dict(bucket[item_id])
                item["score"] = float(scores[index])
                item["vector_backend"] = "dense_embedding"
                results.append(item)
            return results
        except Exception:
            return []

    async def _hnsw_similarity_search(self, namespace: str, query: str, top_k: int) -> list[dict[str, Any]]:
        index = self._hnsw_indexes.get(namespace)
        record_ids = self._hnsw_labels.get(namespace, [])
        embedding_bucket = self._embeddings.get(namespace, {})
        bucket = self._records.get(namespace, {})
        if hnswlib is None or self._embedding_func is None or index is None or not record_ids:
            return []

        dimension = next((int(embedding_bucket[item_id].shape[0]) for item_id in record_ids if item_id in embedding_bucket), 0)
        if dimension <= 0:
            return []

        try:
            query_embedding = np.array(self._embedding_func([query]), dtype=np.float32)
            if query_embedding.ndim != 2 or query_embedding.shape != (1, dimension):
                return []
            index.set_ef(max(50, min(200, max(top_k * 4, top_k))))
            labels, distances = index.knn_query(query_embedding, k=min(top_k, len(record_ids)))
        except Exception:
            return []

        results: list[dict[str, Any]] = []
        for label, distance in zip(labels[0], distances[0], strict=False):
            if int(label) < 0 or int(label) >= len(record_ids):
                continue
            score = 1.0 - float(distance)
            if score <= 0:
                continue
            item_id = record_ids[int(label)]
            item = dict(bucket[item_id])
            item["score"] = score
            item["vector_backend"] = "hnsw_embedding"
            results.append(item)
        return results

    async def similarity_search(self, namespace: str, query: str, top_k: int) -> list[dict[str, Any]]:
        bucket = self._records.get(namespace, {})
        if not bucket:
            return []

        hnsw_results = await self._hnsw_similarity_search(namespace, query, top_k)
        if hnsw_results:
            return hnsw_results

        dense_results = await self._dense_similarity_search(namespace, query, top_k)
        if dense_results:
            return dense_results

        return await self._token_fallback.similarity_search(namespace, query, top_k)

    async def get_stats(self) -> dict[str, Any]:
        stats = {namespace: len(bucket) for namespace, bucket in self._records.items()}
        stats["vector_backend"] = self.get_backend_name()
        return stats

    def get_backend_name(self) -> str:
        for index in self._hnsw_indexes.values():
            if index is not None:
                return "hnsw_embedding"
        for embedding_bucket in self._embeddings.values():
            if embedding_bucket:
                return "dense_embedding"
        return "fallback_token"


class NetworkXGraphStorage(BaseGraphStorage):
    """Graph backend that prefers networkx but falls back to plain dictionaries."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        self._path = Path(working_dir) / workspace / "graph.json"
        self._relations_path = Path(working_dir) / workspace / "graph_relations.json"
        self._graph = nx.Graph() if nx is not None else {"nodes": {}, "edges": {}}
        self._relations: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = _read_json(self._path, None)
        if payload and nx is not None:
            self._graph = nx.node_link_graph(payload)
        elif payload:
            self._graph = payload
        raw_relations = _read_json(self._relations_path, {})
        self._relations = {str(relation_id): dict(record) for relation_id, record in dict(raw_relations).items()}
        for source_entity_id, target_entity_id in {
            tuple(sorted((record["source_entity_id"], record["target_entity_id"])))
            for record in self._relations.values()
        }:
            self._refresh_relation_edge(source_entity_id, target_entity_id)

    async def finalize(self) -> None:
        if nx is not None:
            payload = nx.node_link_data(self._graph)
        else:
            payload = self._graph
        _write_json(self._path, payload)
        _write_json(self._relations_path, self._relations)

    def _iter_nodes(self) -> list[tuple[str, dict[str, Any]]]:
        if nx is not None:
            return [(str(node_id), dict(data)) for node_id, data in self._graph.nodes(data=True)]
        return [(str(node_id), dict(data)) for node_id, data in self._graph.get("nodes", {}).items()]

    def _get_node_data(self, node_id: str) -> dict[str, Any] | None:
        if nx is not None:
            if node_id not in self._graph:
                return None
            return dict(self._graph.nodes[node_id])
        node = self._graph.get("nodes", {}).get(node_id)
        return dict(node) if node else None

    def _set_node_data(self, node_id: str, data: dict[str, Any]) -> None:
        if nx is not None:
            self._graph.add_node(node_id, **data)
            return
        self._graph.setdefault("nodes", {})[node_id] = dict(data)

    def _delete_node(self, node_id: str) -> None:
        if nx is not None:
            if node_id in self._graph:
                self._graph.remove_node(node_id)
            return
        graph_nodes = self._graph.setdefault("nodes", {})
        graph_edges = self._graph.setdefault("edges", {})
        graph_nodes.pop(node_id, None)
        for edge_key in [edge_key for edge_key, edge in graph_edges.items() if edge["source"] == node_id or edge["target"] == node_id]:
            graph_edges.pop(edge_key, None)

    def _iter_edges(self) -> list[tuple[str, str, dict[str, Any]]]:
        if nx is not None:
            return [(str(source), str(target), dict(data)) for source, target, data in self._graph.edges(data=True)]
        return [
            (str(edge["source"]), str(edge["target"]), dict(edge))
            for edge in self._graph.get("edges", {}).values()
        ]

    def _get_edge_data(self, source: str, target: str) -> dict[str, Any] | None:
        if nx is not None:
            if not self._graph.has_edge(source, target):
                return None
            return dict(self._graph[source][target])
        edge_key = "|".join(sorted((source, target)))
        edge = self._graph.get("edges", {}).get(edge_key)
        return dict(edge) if edge else None

    def _set_edge_data(self, source: str, target: str, data: dict[str, Any]) -> None:
        payload = dict(data)
        payload["source"] = source
        payload["target"] = target
        if nx is not None:
            self._graph.add_edge(source, target, **payload)
            return
        self._graph.setdefault("nodes", {}).setdefault(source, {"id": source})
        self._graph.setdefault("nodes", {}).setdefault(target, {"id": target})
        edge_key = "|".join(sorted((source, target)))
        self._graph.setdefault("edges", {})[edge_key] = payload

    def _delete_edge(self, source: str, target: str) -> None:
        if nx is not None:
            if self._graph.has_edge(source, target):
                self._graph.remove_edge(source, target)
            return
        edge_key = "|".join(sorted((source, target)))
        self._graph.setdefault("edges", {}).pop(edge_key, None)

    def _neighbors(self, node_id: str) -> list[str]:
        if nx is not None:
            if node_id not in self._graph:
                return []
            return [str(neighbor) for neighbor in self._graph.neighbors(node_id)]
        graph_edges = self._graph.get("edges", {})
        neighbors: list[str] = []
        for edge in graph_edges.values():
            if edge["source"] == node_id:
                neighbors.append(str(edge["target"]))
            elif edge["target"] == node_id:
                neighbors.append(str(edge["source"]))
        return neighbors

    def _relation_pair(self, source_entity_id: str, target_entity_id: str) -> tuple[str, str]:
        """Return a stable unordered pair key for semantic relations."""

        return tuple(sorted((source_entity_id, target_entity_id)))

    def _iter_relation_records(self) -> list[dict[str, Any]]:
        """Return semantic relation records as plain dicts."""

        return [dict(record) for record in self._relations.values()]

    def _relation_records_for_pair(self, source_entity_id: str, target_entity_id: str) -> list[dict[str, Any]]:
        """Return all semantic relation records between two entities."""

        pair = self._relation_pair(source_entity_id, target_entity_id)
        return [
            dict(record)
            for record in self._relations.values()
            if self._relation_pair(record["source_entity_id"], record["target_entity_id"]) == pair
        ]

    def _refresh_relation_edge(self, source_entity_id: str, target_entity_id: str) -> None:
        """Refresh one aggregated graph edge derived from relation records."""

        records = self._relation_records_for_pair(source_entity_id, target_entity_id)
        if not records:
            edge = self._get_edge_data(source_entity_id, target_entity_id)
            if edge is not None and str(edge.get("kind", "")) == "semantic_relation":
                self._delete_edge(source_entity_id, target_entity_id)
            return
        self._set_edge_data(
            source_entity_id,
            target_entity_id,
            {
                "source": source_entity_id,
                "target": target_entity_id,
                "kind": "semantic_relation",
                "relation_record_ids": sorted(record["id"] for record in records),
                "relations": sorted({str(record.get("relation", "")).strip() for record in records if str(record.get("relation", "")).strip()}),
                "weight": sum(float(record.get("weight", 1.0)) for record in records),
                "description": summarize_entity_descriptions(
                    [str(record.get("description", "")).strip() for record in records if str(record.get("description", "")).strip()]
                ),
                "provenance": dedupe_strings(
                    [
                        str(value).strip()
                        for record in records
                        for value in list(record.get("provenance", []))
                        if str(value).strip()
                    ]
                ),
            },
        )

    async def upsert_nodes(self, nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            node_id = str(node["id"])
            existing = self._get_node_data(node_id) or {"id": node_id}
            merged = _merge_node_payload(existing, dict(node))
            self._set_node_data(node_id, merged)

    async def upsert_edges(self, edges: list[dict[str, Any]]) -> None:
        for edge in edges:
            source = str(edge["source"])
            target = str(edge["target"])
            existing = self._get_edge_data(source, target) or {"source": source, "target": target, "weight": 0.0, "relations": []}
            merged = _merge_edge_payload(existing, dict(edge))
            self._set_edge_data(source, target, merged)

    async def upsert_relation_records(self, relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        affected_pairs: set[tuple[str, str]] = set()
        stored: list[dict[str, Any]] = []
        for relation in relations:
            normalized = _normalize_relation_record(relation)
            existing = self._relations.get(normalized["id"])
            if existing is not None:
                affected_pairs.add(self._relation_pair(existing["source_entity_id"], existing["target_entity_id"]))
            self._relations[normalized["id"]] = normalized
            affected_pairs.add(self._relation_pair(normalized["source_entity_id"], normalized["target_entity_id"]))
            stored.append(dict(normalized))
        for source_entity_id, target_entity_id in affected_pairs:
            self._refresh_relation_edge(source_entity_id, target_entity_id)
        return stored

    async def delete_by_document(self, document_id: str) -> dict[str, Any]:
        removed_relation_ids: list[str] = []
        affected_relation_pairs: set[tuple[str, str]] = set()
        for relation_id, relation in list(self._relations.items()):
            provenance = {str(value).strip() for value in list(relation.get("provenance", [])) if str(value).strip()}
            if document_id not in provenance and str(relation.get("metadata", {}).get("doc_id", "")).strip() != document_id:
                continue
            removed_relation_ids.append(relation_id)
            affected_relation_pairs.add(self._relation_pair(relation["source_entity_id"], relation["target_entity_id"]))
            self._relations.pop(relation_id, None)
        for source_entity_id, target_entity_id in affected_relation_pairs:
            self._refresh_relation_edge(source_entity_id, target_entity_id)

        nodes_to_remove = {
            node_id
            for node_id, node in self._iter_nodes()
            if _is_document_owned_node(node_id, node, document_id)
        }
        affected_entity_ids: set[str] = set()
        for node_id in nodes_to_remove:
            for neighbor_id in self._neighbors(node_id):
                neighbor = self._get_node_data(neighbor_id)
                if neighbor and neighbor.get("kind") == "entity":
                    affected_entity_ids.add(neighbor_id)

        for source, target, edge in self._iter_edges():
            contributions = dict(edge.get("contributions", {}))
            if document_id not in contributions:
                continue
            if (self._get_node_data(source) or {}).get("kind") == "entity":
                affected_entity_ids.add(source)
            if (self._get_node_data(target) or {}).get("kind") == "entity":
                affected_entity_ids.add(target)
            contributions.pop(document_id, None)
            if contributions:
                edge["contributions"] = contributions
                self._set_edge_data(source, target, _refresh_contributed_edge(edge))
            else:
                self._delete_edge(source, target)

        for node_id in nodes_to_remove:
            self._delete_node(node_id)

        updated_entity_ids: list[str] = []
        removed_entity_ids: list[str] = []
        for entity_id in sorted(affected_entity_ids):
            node = self._get_node_data(entity_id)
            if node is None:
                continue
            owners = dict(node.get("owners", {}))
            if document_id in owners:
                owners.pop(document_id, None)
                node["owners"] = owners
            refreshed = _refresh_entity_node(node)
            if owners or refreshed.get("provenance") or refreshed.get("aliases"):
                self._set_node_data(entity_id, refreshed)
                updated_entity_ids.append(entity_id)
            else:
                self._delete_node(entity_id)
                removed_entity_ids.append(entity_id)

        return {
            "removed_nodes": len(nodes_to_remove),
            "updated_entity_ids": updated_entity_ids,
            "removed_entity_ids": removed_entity_ids,
            "removed_relation_ids": removed_relation_ids,
        }

    async def get_node(self, node_id: str) -> dict[str, Any] | None:
        node = self._get_node_data(node_id)
        return {"id": node_id, **node} if node is not None else None

    async def get_relation(self, relation_id: str) -> dict[str, Any] | None:
        relation = self._relations.get(relation_id)
        return dict(relation) if relation is not None else None

    async def list_relations(self, *, entity_id: str | None = None) -> list[dict[str, Any]]:
        if entity_id is None:
            return self._iter_relation_records()
        return [
            dict(record)
            for record in self._relations.values()
            if record["source_entity_id"] == entity_id or record["target_entity_id"] == entity_id
        ]

    async def resolve_entity_ids(self, names: list[str], *, limit: int = 20) -> list[dict[str, Any]]:
        normalized_names = [str(name).strip().lower() for name in names if str(name).strip()]
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for node_id, node in self._iter_nodes():
            if str(node.get("kind", "")) != "entity":
                continue
            candidates = {str(node.get("label", "")).strip().lower()}
            candidates.update(str(alias).strip().lower() for alias in list(node.get("aliases", [])) if str(alias).strip())
            score = 0.0
            for name in normalized_names:
                if name in candidates:
                    score = max(score, 3.0)
                elif any(name in candidate or candidate in name for candidate in candidates if candidate):
                    score = max(score, 1.0)
            if score <= 0 or node_id in seen:
                continue
            results.append({"id": node_id, **node, "score": score})
            seen.add(node_id)
        results.sort(key=lambda item: (float(item.get("score", 0.0)), float(item.get("owner_count", 0.0))), reverse=True)
        return results[: max(limit, 0)]

    async def delete_entity(self, entity_id: str) -> dict[str, Any]:
        node = self._get_node_data(entity_id)
        if node is None:
            return {"deleted_entity": 0, "removed_relation_ids": []}
        removed_relation_ids: list[str] = []
        affected_pairs: set[tuple[str, str]] = set()
        for relation_id, relation in list(self._relations.items()):
            if relation["source_entity_id"] != entity_id and relation["target_entity_id"] != entity_id:
                continue
            removed_relation_ids.append(relation_id)
            affected_pairs.add(self._relation_pair(relation["source_entity_id"], relation["target_entity_id"]))
            self._relations.pop(relation_id, None)
        for source_entity_id, target_entity_id in affected_pairs:
            self._refresh_relation_edge(source_entity_id, target_entity_id)
        self._delete_node(entity_id)
        return {"deleted_entity": 1, "removed_relation_ids": removed_relation_ids}

    async def delete_relation(self, relation_id: str) -> dict[str, Any]:
        relation = self._relations.pop(relation_id, None)
        if relation is None:
            return {"deleted_relation": 0}
        self._refresh_relation_edge(relation["source_entity_id"], relation["target_entity_id"])
        return {"deleted_relation": 1, "relation": dict(relation)}

    async def merge_entities(self, source_entity_id: str, target_entity_id: str) -> dict[str, Any]:
        if source_entity_id == target_entity_id:
            return {"merged": 0, "removed_relation_ids": []}
        source = self._get_node_data(source_entity_id)
        target = self._get_node_data(target_entity_id)
        if source is None or target is None:
            return {"merged": 0, "removed_relation_ids": []}

        merged_target = _merge_node_payload(
            target,
            {
                **source,
                "id": target_entity_id,
                "label": str(target.get("label", "")).strip() or str(source.get("label", "")).strip(),
                "aliases": dedupe_strings(
                    [
                        str(source.get("label", "")).strip(),
                        *list(target.get("aliases", [])),
                        *list(source.get("aliases", [])),
                    ]
                ),
            },
        )
        self._set_node_data(target_entity_id, merged_target)

        for neighbor_id in self._neighbors(source_entity_id):
            neighbor = self._get_node_data(neighbor_id)
            edge = self._get_edge_data(source_entity_id, neighbor_id)
            if neighbor is None or edge is None:
                continue
            if str(neighbor.get("kind", "")) == "entity" and str(edge.get("kind", "")) == "semantic_relation":
                continue
            payload = dict(edge)
            payload["source"] = target_entity_id
            payload["target"] = neighbor_id
            existing = self._get_edge_data(target_entity_id, neighbor_id) or {
                "source": target_entity_id,
                "target": neighbor_id,
                "weight": 0.0,
                "relations": [],
            }
            self._set_edge_data(target_entity_id, neighbor_id, _merge_edge_payload(existing, payload))
            self._delete_edge(source_entity_id, neighbor_id)

        removed_relation_ids: list[str] = []
        affected_pairs: set[tuple[str, str]] = set()
        for relation_id, relation in list(self._relations.items()):
            changed = False
            affected_pairs.add(self._relation_pair(relation["source_entity_id"], relation["target_entity_id"]))
            if relation["source_entity_id"] == source_entity_id:
                relation["source_entity_id"] = target_entity_id
                changed = True
            if relation["target_entity_id"] == source_entity_id:
                relation["target_entity_id"] = target_entity_id
                changed = True
            if not changed:
                continue
            if relation["source_entity_id"] == relation["target_entity_id"]:
                removed_relation_ids.append(relation_id)
                self._relations.pop(relation_id, None)
                continue
            self._relations[relation_id] = relation
            affected_pairs.add(self._relation_pair(relation["source_entity_id"], relation["target_entity_id"]))

        for source_id, target_id in affected_pairs:
            self._refresh_relation_edge(source_id, target_id)

        self._delete_node(source_entity_id)
        return {"merged": 1, "target_entity_id": target_entity_id, "removed_relation_ids": removed_relation_ids}

    async def merge_relations(self, source_relation_id: str, target_relation_id: str) -> dict[str, Any]:
        if source_relation_id == target_relation_id:
            return {"merged": 0}
        source = self._relations.get(source_relation_id)
        target = self._relations.get(target_relation_id)
        if source is None or target is None:
            return {"merged": 0}
        merged = dict(target)
        merged["weight"] = float(target.get("weight", 1.0)) + float(source.get("weight", 1.0))
        merged["provenance"] = dedupe_strings(
            [str(value).strip() for value in list(target.get("provenance", [])) + list(source.get("provenance", [])) if str(value).strip()]
        )
        merged["description"] = summarize_entity_descriptions(
            [str(target.get("description", "")).strip(), str(source.get("description", "")).strip()]
        )
        merged["metadata"] = {**dict(source.get("metadata", {})), **dict(target.get("metadata", {}))}
        self._relations[target_relation_id] = merged
        self._relations.pop(source_relation_id, None)
        self._refresh_relation_edge(source["source_entity_id"], source["target_entity_id"])
        self._refresh_relation_edge(target["source_entity_id"], target["target_entity_id"])
        return {"merged": 1, "target_relation_id": target_relation_id}

    async def get_neighbors(
        self,
        node_ids: list[str],
        *,
        kind_filter: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        scores: dict[str, float] = {}
        source_ids = set(node_ids)
        for node_id in node_ids:
            for neighbor_id in self._neighbors(node_id):
                if neighbor_id in source_ids:
                    continue
                node = self._get_node_data(neighbor_id)
                if node is None:
                    continue
                if kind_filter and node.get("kind") != kind_filter:
                    continue
                edge = self._get_edge_data(node_id, neighbor_id) or {}
                scores[neighbor_id] = scores.get(neighbor_id, 0.0) + float(edge.get("weight", 1.0))
        ranked_ids = sorted(scores, key=lambda item: scores[item], reverse=True)[:limit]
        return [
            {"id": node_id, **(self._get_node_data(node_id) or {}), "score": scores[node_id]}
            for node_id in ranked_ids
        ]

    async def top_nodes(self, *, kind: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        degree_map: dict[str, int] = {node_id: 0 for node_id, _ in self._iter_nodes()}
        for source, target, _ in self._iter_edges():
            degree_map[source] = degree_map.get(source, 0) + 1
            degree_map[target] = degree_map.get(target, 0) + 1
        ranked: list[tuple[int, str]] = []
        for node_id, data in self._iter_nodes():
            if kind and data.get("kind") != kind:
                continue
            ranked.append((degree_map.get(node_id, 0), node_id))
        ranked.sort(reverse=True)
        return [
            {"id": node_id, **(self._get_node_data(node_id) or {}), "score": degree}
            for degree, node_id in ranked[:limit]
        ]

    async def get_stats(self) -> dict[str, Any]:
        return {
            "nodes": len(self._iter_nodes()),
            "edges": len(self._iter_edges()),
        }


class JSONDocStatusStorage(BaseDocStatusStorage):
    """Persist document processing status as JSON."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        self._path = Path(working_dir) / workspace / "doc_status.json"
        self._statuses: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._statuses = _read_json(self._path, {})

    async def finalize(self) -> None:
        _write_json(self._path, self._statuses)

    async def mark_status(
        self,
        document_id: str,
        status: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._statuses[document_id] = {
            "document_id": document_id,
            "status": status,
            "metadata": metadata or {},
        }

    async def get_status(self, document_id: str) -> dict[str, Any] | None:
        return self._statuses.get(document_id)

    async def delete_by_document(self, document_id: str) -> int:
        return 1 if self._statuses.pop(document_id, None) is not None else 0

    async def list_statuses(self) -> list[dict[str, Any]]:
        return list(self._statuses.values())

    async def get_stats(self) -> dict[str, Any]:
        return {"documents": len(self._statuses)}


__all__ = [
    "EmbeddingVectorStorage",
    "JSONDocStatusStorage",
    "JSONKVStorage",
    "NetworkXGraphStorage",
    "TokenVectorStorage",
]
