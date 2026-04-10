"""Storage backend bundle resolution for canonical RAG storage packages."""

from __future__ import annotations

from easyrag.config import get_rag_storage_backend
from easyrag.rag.storage.base import BaseDocStatusStorage, BaseGraphStorage, BaseKVStorage, BaseVectorStorage
from easyrag.rag.storage.graph.networkx_graph import NetworkXGraphStorage
from easyrag.rag.storage.graph.postgres_graph import PostgresGraphStorage
from easyrag.rag.storage.kv.json_kv import JSONKVStorage
from easyrag.rag.storage.kv.postgres_kv import PostgresKVStorage
from easyrag.rag.storage.status.json_doc_status import JSONDocStatusStorage
from easyrag.rag.storage.status.postgres_doc_status import PostgresDocStatusStorage
from easyrag.rag.storage.vector.embedding_vector import EmbeddingVectorStorage
from easyrag.rag.storage.vector.qdrant_vector import QdrantVectorStorage

StorageBundle = tuple[type[BaseKVStorage], type[BaseVectorStorage], type[BaseGraphStorage], type[BaseDocStatusStorage]]


def resolve_storage_bundle(backend_name: str | None = None) -> StorageBundle:
    """Resolve the configured EasyRAG storage backend bundle."""

    normalized = (backend_name or get_rag_storage_backend()).strip().lower()
    if normalized == "local":
        return JSONKVStorage, EmbeddingVectorStorage, NetworkXGraphStorage, JSONDocStatusStorage
    if normalized == "postgres_qdrant":
        return PostgresKVStorage, QdrantVectorStorage, PostgresGraphStorage, PostgresDocStatusStorage
    raise ValueError(f"Unsupported RAG storage backend: {backend_name}")
