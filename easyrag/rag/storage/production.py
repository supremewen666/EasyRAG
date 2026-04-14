"""Production-oriented RAG storage backends backed by PostgreSQL and Qdrant."""

from __future__ import annotations

import json
import re
from typing import Any

import numpy as np

from easyrag.config import (
    get_postgres_dsn,
    get_qdrant_api_key,
    get_qdrant_collection_prefix,
    get_qdrant_url,
)
from easyrag.rag.storage.base import BaseTaskStatusStorage, BaseVectorStorage
from easyrag.rag.storage.local import (
    JSONDocStatusStorage,
    JSONKVStorage,
    NetworkXGraphStorage,
    TokenVectorStorage,
)

try:
    import httpx
except ImportError:  # pragma: no cover - optional dependency.
    httpx = None

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency.
    psycopg = None

_SAFE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9_]+")


def _json_dump(value: Any) -> str:
    """Serialize one JSON-compatible value for database persistence."""

    return json.dumps(value, ensure_ascii=False)


def _json_load(value: Any, default: Any) -> Any:
    """Deserialize one JSON payload with a permissive fallback."""

    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return default


def _require_postgres() -> str:
    """Return the configured PostgreSQL DSN or raise a helpful error."""

    dsn = get_postgres_dsn()
    if psycopg is None:
        raise RuntimeError(
            "PostgreSQL backend requires `psycopg`. Install the `postgres` extra."
        )
    if not dsn:
        raise RuntimeError("PostgreSQL backend requires `EASYRAG_POSTGRES_DSN`.")
    return dsn


def _ensure_postgres_schema(conn: Any) -> None:
    """Create the minimal PostgreSQL schema used by production RAG backends."""

    statements = [
        """
        CREATE TABLE IF NOT EXISTS documents (
            workspace TEXT NOT NULL,
            id TEXT NOT NULL,
            payload TEXT NOT NULL,
            PRIMARY KEY (workspace, id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS chunks (
            workspace TEXT NOT NULL,
            id TEXT NOT NULL,
            document_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            PRIMARY KEY (workspace, id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS summaries (
            workspace TEXT NOT NULL,
            id TEXT NOT NULL,
            document_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            PRIMARY KEY (workspace, id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS cache (
            workspace TEXT NOT NULL,
            namespace TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (workspace, namespace, key)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS graph_nodes (
            workspace TEXT NOT NULL,
            id TEXT NOT NULL,
            payload TEXT NOT NULL,
            PRIMARY KEY (workspace, id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS graph_edges (
            workspace TEXT NOT NULL,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            payload TEXT NOT NULL,
            PRIMARY KEY (workspace, source, target)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS entities (
            workspace TEXT NOT NULL,
            id TEXT NOT NULL,
            label TEXT NOT NULL,
            description TEXT NOT NULL,
            manual_description TEXT NOT NULL,
            entity_types TEXT NOT NULL,
            manual_entity_types TEXT NOT NULL,
            owners TEXT NOT NULL,
            metadata TEXT NOT NULL,
            provenance TEXT NOT NULL,
            doc_ids TEXT NOT NULL,
            owner_count INTEGER NOT NULL,
            PRIMARY KEY (workspace, id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS entity_aliases (
            workspace TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            alias TEXT NOT NULL,
            PRIMARY KEY (workspace, entity_id, alias)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS relations (
            workspace TEXT NOT NULL,
            id TEXT NOT NULL,
            source_entity_id TEXT NOT NULL,
            target_entity_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            description TEXT NOT NULL,
            weight DOUBLE PRECISION NOT NULL,
            metadata TEXT NOT NULL,
            provenance TEXT NOT NULL,
            PRIMARY KEY (workspace, id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS doc_status (
            workspace TEXT NOT NULL,
            document_id TEXT NOT NULL,
            status TEXT NOT NULL,
            metadata TEXT NOT NULL,
            PRIMARY KEY (workspace, document_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS task_status (
            workspace TEXT NOT NULL,
            task_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            PRIMARY KEY (workspace, task_id)
        )
        """,
    ]
    with conn.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
    conn.commit()


def _safe_collection_name(*parts: str) -> str:
    """Return a Qdrant-safe collection identifier."""

    return "_".join(
        _SAFE_NAME_PATTERN.sub("_", part.strip()).strip("_").lower() or "default"
        for part in parts
    )


class PostgresKVStorage(JSONKVStorage):
    """Persist KV records in PostgreSQL while reusing JSONKVStorage behavior."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        self._dsn = get_postgres_dsn()

    async def initialize(self) -> None:
        self._documents = {}
        self._chunks = {}
        self._summaries = {}
        self._cache = {}
        dsn = _require_postgres()
        with psycopg.connect(dsn) as conn:
            _ensure_postgres_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, payload FROM documents WHERE workspace = %s",
                    (self.workspace,),
                )
                self._documents = {
                    str(item_id): dict(_json_load(payload, {}))
                    for item_id, payload in cursor.fetchall()
                }

                cursor.execute(
                    "SELECT id, payload FROM chunks WHERE workspace = %s",
                    (self.workspace,),
                )
                self._chunks = {
                    str(item_id): dict(_json_load(payload, {}))
                    for item_id, payload in cursor.fetchall()
                }

                cursor.execute(
                    "SELECT id, payload FROM summaries WHERE workspace = %s",
                    (self.workspace,),
                )
                self._summaries = {
                    str(item_id): dict(_json_load(payload, {}))
                    for item_id, payload in cursor.fetchall()
                }

                cursor.execute(
                    "SELECT namespace, key, value FROM cache WHERE workspace = %s",
                    (self.workspace,),
                )
                for namespace, key, value in cursor.fetchall():
                    self._cache.setdefault(str(namespace), {})[str(key)] = _json_load(
                        value, None
                    )

    async def finalize(self) -> None:
        dsn = _require_postgres()
        with psycopg.connect(dsn) as conn:
            _ensure_postgres_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM documents WHERE workspace = %s", (self.workspace,)
                )
                cursor.executemany(
                    "INSERT INTO documents (workspace, id, payload) VALUES (%s, %s, %s)",
                    [
                        (self.workspace, item_id, _json_dump(payload))
                        for item_id, payload in self._documents.items()
                    ],
                )

                cursor.execute(
                    "DELETE FROM chunks WHERE workspace = %s", (self.workspace,)
                )
                cursor.executemany(
                    "INSERT INTO chunks (workspace, id, document_id, payload) VALUES (%s, %s, %s, %s)",
                    [
                        (
                            self.workspace,
                            item_id,
                            str(payload.get("document_id", "")),
                            _json_dump(payload),
                        )
                        for item_id, payload in self._chunks.items()
                    ],
                )

                cursor.execute(
                    "DELETE FROM summaries WHERE workspace = %s", (self.workspace,)
                )
                cursor.executemany(
                    "INSERT INTO summaries (workspace, id, document_id, payload) VALUES (%s, %s, %s, %s)",
                    [
                        (
                            self.workspace,
                            item_id,
                            str(
                                payload.get("document_id", "")
                                or payload.get("metadata", {}).get("doc_id", "")
                            ),
                            _json_dump(payload),
                        )
                        for item_id, payload in self._summaries.items()
                    ],
                )

                cursor.execute(
                    "DELETE FROM cache WHERE workspace = %s", (self.workspace,)
                )
                cache_rows = [
                    (self.workspace, namespace, key, _json_dump(value))
                    for namespace, bucket in self._cache.items()
                    for key, value in bucket.items()
                ]
                if cache_rows:
                    cursor.executemany(
                        "INSERT INTO cache (workspace, namespace, key, value) VALUES (%s, %s, %s, %s)",
                        cache_rows,
                    )
            conn.commit()


class PostgresGraphStorage(NetworkXGraphStorage):
    """Persist graph nodes, edges, and relation records in PostgreSQL."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        self._dsn = get_postgres_dsn()

    async def initialize(self) -> None:
        self._graph = (
            self._graph.__class__()
            if hasattr(self._graph, "__class__") and hasattr(self._graph, "add_node")
            else {"nodes": {}, "edges": {}}
        )
        self._relations = {}
        dsn = _require_postgres()
        with psycopg.connect(dsn) as conn:
            _ensure_postgres_schema(conn)
            alias_map: dict[str, list[str]] = {}
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT entity_id, alias FROM entity_aliases WHERE workspace = %s",
                    (self.workspace,),
                )
                for entity_id, alias in cursor.fetchall():
                    alias_map.setdefault(str(entity_id), []).append(str(alias))

                cursor.execute(
                    """
                    SELECT id, label, description, manual_description, entity_types, manual_entity_types,
                           owners, metadata, provenance, doc_ids, owner_count
                    FROM entities
                    WHERE workspace = %s
                    """,
                    (self.workspace,),
                )
                for row in cursor.fetchall():
                    entity_id = str(row[0])
                    self._set_node_data(
                        entity_id,
                        {
                            "id": entity_id,
                            "kind": "entity",
                            "label": str(row[1]),
                            "description": str(row[2]),
                            "manual_description": str(row[3]),
                            "entity_types": list(_json_load(row[4], [])),
                            "manual_entity_types": list(_json_load(row[5], [])),
                            "owners": dict(_json_load(row[6], {})),
                            "metadata": dict(_json_load(row[7], {})),
                            "provenance": list(_json_load(row[8], [])),
                            "doc_ids": list(_json_load(row[9], [])),
                            "owner_count": int(row[10] or 0),
                            "aliases": list(alias_map.get(entity_id, [])),
                        },
                    )

                cursor.execute(
                    "SELECT id, payload FROM graph_nodes WHERE workspace = %s",
                    (self.workspace,),
                )
                for node_id, payload in cursor.fetchall():
                    self._set_node_data(str(node_id), dict(_json_load(payload, {})))

                cursor.execute(
                    "SELECT source, target, payload FROM graph_edges WHERE workspace = %s",
                    (self.workspace,),
                )
                for source, target, payload in cursor.fetchall():
                    self._set_edge_data(
                        str(source), str(target), dict(_json_load(payload, {}))
                    )

                cursor.execute(
                    """
                    SELECT id, source_entity_id, target_entity_id, relation, description, weight, metadata, provenance
                    FROM relations
                    WHERE workspace = %s
                    """,
                    (self.workspace,),
                )
                for row in cursor.fetchall():
                    relation_id = str(row[0])
                    self._relations[relation_id] = {
                        "id": relation_id,
                        "source_entity_id": str(row[1]),
                        "target_entity_id": str(row[2]),
                        "relation": str(row[3]),
                        "description": str(row[4]),
                        "weight": float(row[5]),
                        "metadata": dict(_json_load(row[6], {})),
                        "provenance": list(_json_load(row[7], [])),
                    }
        for source_entity_id, target_entity_id in {
            tuple(sorted((record["source_entity_id"], record["target_entity_id"])))
            for record in self._relations.values()
        }:
            self._refresh_relation_edge(source_entity_id, target_entity_id)

    async def finalize(self) -> None:
        dsn = _require_postgres()
        with psycopg.connect(dsn) as conn:
            _ensure_postgres_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM entity_aliases WHERE workspace = %s", (self.workspace,)
                )
                cursor.execute(
                    "DELETE FROM entities WHERE workspace = %s", (self.workspace,)
                )
                cursor.execute(
                    "DELETE FROM graph_nodes WHERE workspace = %s", (self.workspace,)
                )
                cursor.execute(
                    "DELETE FROM graph_edges WHERE workspace = %s", (self.workspace,)
                )
                cursor.execute(
                    "DELETE FROM relations WHERE workspace = %s", (self.workspace,)
                )

                entity_rows: list[tuple[Any, ...]] = []
                alias_rows: list[tuple[Any, ...]] = []
                node_rows: list[tuple[Any, ...]] = []
                for node_id, node in self._iter_nodes():
                    if str(node.get("kind", "")) == "entity":
                        entity_rows.append(
                            (
                                self.workspace,
                                node_id,
                                str(node.get("label", "")),
                                str(node.get("description", "")),
                                str(node.get("manual_description", "")),
                                _json_dump(list(node.get("entity_types", []) or [])),
                                _json_dump(
                                    list(node.get("manual_entity_types", []) or [])
                                ),
                                _json_dump(dict(node.get("owners", {}))),
                                _json_dump(dict(node.get("metadata", {}))),
                                _json_dump(list(node.get("provenance", []) or [])),
                                _json_dump(list(node.get("doc_ids", []) or [])),
                                int(node.get("owner_count", 0) or 0),
                            )
                        )
                        alias_rows.extend(
                            (self.workspace, node_id, str(alias))
                            for alias in list(node.get("aliases", []) or [])
                            if str(alias).strip()
                        )
                        continue
                    node_rows.append((self.workspace, node_id, _json_dump(node)))

                if entity_rows:
                    cursor.executemany(
                        """
                        INSERT INTO entities (
                            workspace, id, label, description, manual_description, entity_types,
                            manual_entity_types, owners, metadata, provenance, doc_ids, owner_count
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        entity_rows,
                    )
                if alias_rows:
                    cursor.executemany(
                        "INSERT INTO entity_aliases (workspace, entity_id, alias) VALUES (%s, %s, %s)",
                        alias_rows,
                    )
                if node_rows:
                    cursor.executemany(
                        "INSERT INTO graph_nodes (workspace, id, payload) VALUES (%s, %s, %s)",
                        node_rows,
                    )

                edge_rows = [
                    (self.workspace, source, target, _json_dump(edge))
                    for source, target, edge in self._iter_edges()
                    if str(edge.get("kind", "")) != "semantic_relation"
                ]
                if edge_rows:
                    cursor.executemany(
                        "INSERT INTO graph_edges (workspace, source, target, payload) VALUES (%s, %s, %s, %s)",
                        edge_rows,
                    )

                relation_rows = [
                    (
                        self.workspace,
                        str(relation["id"]),
                        str(relation["source_entity_id"]),
                        str(relation["target_entity_id"]),
                        str(relation.get("relation", "related_to")),
                        str(relation.get("description", "")),
                        float(relation.get("weight", 1.0)),
                        _json_dump(dict(relation.get("metadata", {}))),
                        _json_dump(list(relation.get("provenance", []) or [])),
                    )
                    for relation in self._relations.values()
                ]
                if relation_rows:
                    cursor.executemany(
                        """
                        INSERT INTO relations (
                            workspace, id, source_entity_id, target_entity_id, relation, description, weight, metadata, provenance
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        relation_rows,
                    )
            conn.commit()


class PostgresDocStatusStorage(JSONDocStatusStorage):
    """Persist document indexing status in PostgreSQL."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        self._dsn = get_postgres_dsn()

    async def initialize(self) -> None:
        self._statuses = {}
        dsn = _require_postgres()
        with psycopg.connect(dsn) as conn:
            _ensure_postgres_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT document_id, status, metadata FROM doc_status WHERE workspace = %s",
                    (self.workspace,),
                )
                self._statuses = {
                    str(document_id): {
                        "document_id": str(document_id),
                        "status": str(status),
                        "metadata": dict(_json_load(metadata, {})),
                    }
                    for document_id, status, metadata in cursor.fetchall()
                }

    async def finalize(self) -> None:
        dsn = _require_postgres()
        with psycopg.connect(dsn) as conn:
            _ensure_postgres_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM doc_status WHERE workspace = %s", (self.workspace,)
                )
                rows = [
                    (
                        self.workspace,
                        document_id,
                        str(payload.get("status", "")),
                        _json_dump(dict(payload.get("metadata", {}))),
                    )
                    for document_id, payload in self._statuses.items()
                ]
                if rows:
                    cursor.executemany(
                        "INSERT INTO doc_status (workspace, document_id, status, metadata) VALUES (%s, %s, %s, %s)",
                        rows,
                    )
            conn.commit()


class PostgresTaskStatusStorage(BaseTaskStatusStorage):
    """Persist index task status in PostgreSQL."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        self._dsn = get_postgres_dsn()
        self._tasks: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        self._tasks = {}
        dsn = _require_postgres()
        with psycopg.connect(dsn) as conn:
            _ensure_postgres_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT task_id, payload FROM task_status WHERE workspace = %s",
                    (self.workspace,),
                )
                self._tasks = {
                    str(task_id): dict(_json_load(payload, {}))
                    for task_id, payload in cursor.fetchall()
                }

    async def finalize(self) -> None:
        dsn = _require_postgres()
        with psycopg.connect(dsn) as conn:
            _ensure_postgres_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM task_status WHERE workspace = %s", (self.workspace,)
                )
                rows = [
                    (self.workspace, task_id, _json_dump(payload))
                    for task_id, payload in self._tasks.items()
                ]
                if rows:
                    cursor.executemany(
                        "INSERT INTO task_status (workspace, task_id, payload) VALUES (%s, %s, %s)",
                        rows,
                    )
            conn.commit()

    async def upsert_task(self, task: dict[str, Any]) -> None:
        task_id = str(task["task_id"])
        payload = dict(task)
        self._tasks[task_id] = payload
        dsn = _require_postgres()
        with psycopg.connect(dsn) as conn:
            _ensure_postgres_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO task_status (workspace, task_id, payload)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (workspace, task_id)
                    DO UPDATE SET payload = EXCLUDED.payload
                    """,
                    (self.workspace, task_id, _json_dump(payload)),
                )
            conn.commit()

    async def get_task(self, task_id: str) -> dict[str, Any] | None:
        task = self._tasks.get(task_id)
        return dict(task) if task is not None else None

    async def list_tasks(self, *, limit: int = 100) -> list[dict[str, Any]]:
        tasks = sorted(
            (dict(task) for task in self._tasks.values()),
            key=lambda item: str(item.get("requested_at", "")),
            reverse=True,
        )
        return tasks[: max(limit, 0)]


class QdrantVectorStorage(BaseVectorStorage):
    """Qdrant-backed dense retrieval with a token-overlap fallback path."""

    _namespaces = ("chunk", "entity", "relation", "summary")

    def __init__(self, working_dir: str, workspace: str) -> None:
        super().__init__(working_dir, workspace)
        self._url = get_qdrant_url().rstrip("/")
        self._api_key = get_qdrant_api_key()
        self._collection_prefix = get_qdrant_collection_prefix()
        self._embedding_func = None
        self._token_fallback = TokenVectorStorage(working_dir, workspace)
        self._known_dimensions: dict[str, int] = {}

    def set_embedding_func(self, embedding_func):
        self._embedding_func = embedding_func

    async def initialize(self) -> None:
        await self._token_fallback.initialize()
        if httpx is None:
            raise RuntimeError("Qdrant backend requires `httpx`.")
        if not self._url:
            raise RuntimeError("Qdrant backend requires `EASYRAG_QDRANT_URL`.")

    async def finalize(self) -> None:
        await self._token_fallback.finalize()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["api-key"] = self._api_key
        return headers

    def _collection_name(self, namespace: str) -> str:
        return _safe_collection_name(self._collection_prefix, self.workspace, namespace)

    def _request(
        self, method: str, path: str, *, json_payload: Any | None = None
    ) -> dict[str, Any]:
        if httpx is None:
            raise RuntimeError("Qdrant backend requires `httpx`.")
        response = httpx.request(
            method,
            f"{self._url}{path}",
            headers=self._headers(),
            json=json_payload,
            timeout=20.0,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Qdrant request failed: {response.status_code} {response.text}"
            )
        if not response.content:
            return {}
        return dict(response.json())

    async def _embed_items(self, items: list[dict[str, Any]]) -> np.ndarray:
        if not items or self._embedding_func is None:
            return np.zeros((0, 0), dtype=np.float32)
        try:
            inputs = [
                item.get("embedding_input", str(item.get("text", ""))) for item in items
            ]
            values = self._embedding_func(inputs)
            embeddings = np.array(values, dtype=np.float32)
            if embeddings.ndim != 2 or embeddings.shape[0] != len(items):
                return np.zeros((0, 0), dtype=np.float32)
            return embeddings
        except Exception:
            return np.zeros((0, 0), dtype=np.float32)

    async def _ensure_collection(self, namespace: str, dimension: int) -> None:
        if dimension <= 0:
            return
        collection = self._collection_name(namespace)
        if self._known_dimensions.get(namespace) == dimension:
            return
        try:
            self._request("GET", f"/collections/{collection}")
            self._known_dimensions[namespace] = dimension
            return
        except Exception:
            pass
        self._request(
            "PUT",
            f"/collections/{collection}",
            json_payload={"vectors": {"size": dimension, "distance": "Cosine"}},
        )
        self._known_dimensions[namespace] = dimension

    async def upsert(self, namespace: str, items: list[dict[str, Any]]) -> None:
        await self._token_fallback.upsert(namespace, items)
        embeddings = await self._embed_items(items)
        if not len(items) or embeddings.size == 0:
            return
        await self._ensure_collection(namespace, int(embeddings.shape[1]))
        collection = self._collection_name(namespace)
        points = [
            {
                "id": str(item["id"]),
                "vector": embeddings[index].tolist(),
                "payload": {
                    "id": str(item["id"]),
                    "text": str(item.get("text", "")),
                    "metadata": dict(item.get("metadata", {})),
                    "workspace": self.workspace,
                    "namespace": namespace,
                },
            }
            for index, item in enumerate(items)
        ]
        self._request(
            "PUT", f"/collections/{collection}/points", json_payload={"points": points}
        )

    async def delete(self, namespace: str, ids: list[str]) -> int:
        normalized_ids = [str(item_id) for item_id in ids if str(item_id).strip()]
        await self._token_fallback.delete(namespace, normalized_ids)
        if not normalized_ids:
            return 0
        try:
            self._request(
                "POST",
                f"/collections/{self._collection_name(namespace)}/points/delete",
                json_payload={"points": normalized_ids},
            )
        except Exception:
            return 0
        return len(normalized_ids)

    async def _list_ids_by_document(
        self, namespace: str, document_id: str
    ) -> list[str]:
        try:
            payload = self._request(
                "POST",
                f"/collections/{self._collection_name(namespace)}/points/scroll",
                json_payload={
                    "limit": 256,
                    "with_payload": True,
                    "with_vector": False,
                    "filter": {
                        "must": [
                            {"key": "metadata.doc_id", "match": {"value": document_id}},
                        ]
                    },
                },
            )
        except Exception:
            return []
        return [
            str(item.get("id", ""))
            for item in list(payload.get("result", {}).get("points", []))
            if str(item.get("id", "")).strip()
        ]

    async def delete_by_document(self, document_id: str) -> dict[str, int]:
        deleted: dict[str, int] = {}
        for namespace in self._namespaces:
            if namespace == "entity":
                deleted[namespace] = 0
                continue
            ids = await self._list_ids_by_document(namespace, document_id)
            deleted[namespace] = await self.delete(namespace, ids)
        return deleted

    async def similarity_search(
        self, namespace: str, query: str, top_k: int
    ) -> list[dict[str, Any]]:
        if self._embedding_func is None or top_k <= 0:
            return await self._token_fallback.similarity_search(namespace, query, top_k)
        try:
            query_embedding = np.array(self._embedding_func([query]), dtype=np.float32)
            if query_embedding.ndim != 2 or query_embedding.shape[0] != 1:
                return await self._token_fallback.similarity_search(
                    namespace, query, top_k
                )
            payload = self._request(
                "POST",
                f"/collections/{self._collection_name(namespace)}/points/search",
                json_payload={
                    "vector": query_embedding[0].tolist(),
                    "limit": top_k,
                    "with_payload": True,
                    "with_vector": False,
                },
            )
        except Exception:
            return await self._token_fallback.similarity_search(namespace, query, top_k)

        results: list[dict[str, Any]] = []
        for item in list(payload.get("result", [])):
            point_payload = dict(item.get("payload", {}))
            candidate = {
                "id": str(point_payload.get("id", item.get("id", ""))),
                "text": str(point_payload.get("text", "")),
                "metadata": dict(point_payload.get("metadata", {})),
                "score": float(item.get("score", 0.0)),
                "vector_backend": "qdrant",
            }
            results.append(candidate)
        if results:
            return results
        return await self._token_fallback.similarity_search(namespace, query, top_k)

    async def get_stats(self) -> dict[str, Any]:
        stats: dict[str, Any] = {}
        for namespace in self._namespaces:
            try:
                payload = self._request(
                    "GET", f"/collections/{self._collection_name(namespace)}"
                )
                stats[namespace] = int(payload.get("result", {}).get("points_count", 0))
            except Exception:
                stats[namespace] = 0
        stats["vector_backend"] = self.get_backend_name()
        return stats

    def get_backend_name(self) -> str:
        return "qdrant"


__all__ = [
    "PostgresDocStatusStorage",
    "PostgresGraphStorage",
    "PostgresKVStorage",
    "PostgresTaskStatusStorage",
    "QdrantVectorStorage",
]
