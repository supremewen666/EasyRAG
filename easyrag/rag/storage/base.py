"""Storage abstractions for the RAG subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable


class BaseStorage(ABC):
    """Shared lifecycle methods for storage backends."""

    def __init__(self, working_dir: str, workspace: str) -> None:
        self.working_dir = working_dir
        self.workspace = workspace

    @abstractmethod
    async def initialize(self) -> None:
        """Load or create the backing store."""

    @abstractmethod
    async def finalize(self) -> None:
        """Persist in-memory state to disk."""


class BaseKVStorage(BaseStorage):
    """Store documents, chunks, summaries, and optional cache entries."""

    @abstractmethod
    async def upsert_documents(self, items: list[dict[str, Any]]) -> None:
        """Insert or update document records."""

    @abstractmethod
    async def upsert_chunks(self, items: list[dict[str, Any]]) -> None:
        """Insert or update chunk records."""

    @abstractmethod
    async def upsert_summaries(self, items: list[dict[str, Any]]) -> None:
        """Insert or update document summary records."""

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> dict[str, int]:
        """Delete document, chunk, and summary records owned by one document."""

    @abstractmethod
    async def upsert_cache(self, namespace: str, key: str, value: Any) -> None:
        """Persist a cache entry."""

    @abstractmethod
    async def get_document(self, document_id: str) -> dict[str, Any] | None:
        """Return one document record if it exists."""

    @abstractmethod
    async def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        """Return one chunk record if it exists."""

    @abstractmethod
    async def get_chunks(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        """Return chunk records in caller-requested order where possible."""

    @abstractmethod
    async def get_summary(self, summary_id: str) -> dict[str, Any] | None:
        """Return one summary record if it exists."""

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Return storage-specific counts."""


class BaseVectorStorage(BaseStorage):
    """Store chunk, entity, relation, and summary retrieval items."""

    @abstractmethod
    async def upsert(self, namespace: str, items: list[dict[str, Any]]) -> None:
        """Insert or update vector-like records in a namespace."""

    @abstractmethod
    async def delete(self, namespace: str, ids: list[str]) -> int:
        """Delete records by identifier in one namespace."""

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> dict[str, int]:
        """Delete records owned by one document across namespaces."""

    @abstractmethod
    async def similarity_search(
        self, namespace: str, query: str, top_k: int
    ) -> list[dict[str, Any]]:
        """Search one namespace and return ranked records."""

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Return namespace counts."""

    def set_embedding_func(
        self, embedding_func: Callable[[list[str]], list[list[float]]] | None
    ) -> None:
        """Inject an embedding function into the storage backend."""

        del embedding_func

    def get_backend_name(self) -> str:
        """Return the active retrieval backend name."""

        return self.__class__.__name__


class BaseGraphStorage(BaseStorage):
    """Store graph nodes and edges for entity-aware retrieval."""

    @abstractmethod
    async def upsert_nodes(self, nodes: list[dict[str, Any]]) -> None:
        """Insert or update graph nodes."""

    @abstractmethod
    async def upsert_edges(self, edges: list[dict[str, Any]]) -> None:
        """Insert or update graph edges."""

    @abstractmethod
    async def upsert_relation_records(
        self, relations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Insert or update first-class semantic relation records."""

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> dict[str, Any]:
        """Delete graph data owned by one document and report affected entities."""

    @abstractmethod
    async def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Return one graph node if it exists."""

    @abstractmethod
    async def get_relation(self, relation_id: str) -> dict[str, Any] | None:
        """Return one semantic relation record if it exists."""

    @abstractmethod
    async def list_relations(
        self, *, entity_id: str | None = None
    ) -> list[dict[str, Any]]:
        """List semantic relation records, optionally filtered by entity."""

    @abstractmethod
    async def resolve_entity_ids(
        self, names: list[str], *, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Resolve query-time entity names against labels and aliases."""

    @abstractmethod
    async def delete_entity(self, entity_id: str) -> dict[str, Any]:
        """Delete one entity node and cascade its dependent graph artifacts."""

    @abstractmethod
    async def delete_relation(self, relation_id: str) -> dict[str, Any]:
        """Delete one semantic relation record and refresh derived graph state."""

    @abstractmethod
    async def merge_entities(
        self, source_entity_id: str, target_entity_id: str
    ) -> dict[str, Any]:
        """Merge one entity into another and rewrite graph references."""

    @abstractmethod
    async def merge_relations(
        self, source_relation_id: str, target_relation_id: str
    ) -> dict[str, Any]:
        """Merge one relation into another and preserve the target identifier."""

    @abstractmethod
    async def get_neighbors(
        self,
        node_ids: list[str],
        *,
        kind_filter: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return ranked neighbor nodes."""

    @abstractmethod
    async def top_nodes(
        self, *, kind: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Return graph nodes ranked by centrality."""

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Return node and edge counts."""


class BaseDocStatusStorage(BaseStorage):
    """Track document insertion lifecycle and errors."""

    @abstractmethod
    async def mark_status(
        self,
        document_id: str,
        status: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update document status."""

    @abstractmethod
    async def get_status(self, document_id: str) -> dict[str, Any] | None:
        """Return one document status if it exists."""

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> int:
        """Delete one document status if it exists."""

    @abstractmethod
    async def list_statuses(self) -> list[dict[str, Any]]:
        """Return all document statuses."""

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Return status counts."""


class BaseTaskStatusStorage(BaseStorage):
    """Persist long-running index task status for optional background workflows."""

    @abstractmethod
    async def upsert_task(self, task: dict[str, Any]) -> None:
        """Insert or update one task record."""

    @abstractmethod
    async def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Return one task record if it exists."""

    @abstractmethod
    async def list_tasks(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """List recent task records."""
