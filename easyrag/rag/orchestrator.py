"""Canonical RAG orchestrator for EasyRAG's teaching-first architecture."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Sequence
from uuid import uuid4

from easyrag.support.optional_deps import Document
from easyrag.config import (
    get_kg_entity_types,
    get_rag_working_dir,
    get_rag_workspace,
    has_embedding_model_config,
    has_kg_model_config,
    has_query_model_config,
    has_rerank_model_config,
)
from easyrag.rag.generation.pipeline import generate_answer
from easyrag.rag.indexing.chunking import ChunkingConfig, build_chunker_registry
from easyrag.rag.indexing.loaders import load_repo_documents
from easyrag.rag.indexing.pipeline import ingest_documents
from easyrag.rag.indexing.prepare import (
    prepare_documents_for_insert,
    prepare_documents_for_insert_with_report,
)
from easyrag.rag.knowledge.curation import build_entity_payload, build_relation_payload
from easyrag.rag.knowledge.sync import sync_entity_vectors, sync_relation_vectors
from easyrag.rag.retrieval.pipeline import execute_query
from easyrag.rag.retrieval.preprocess import QueryPreprocessor
from easyrag.rag.storage.base import (
    BaseDocStatusStorage,
    BaseGraphStorage,
    BaseKVStorage,
    BaseVectorStorage,
)
from easyrag.rag.storage.bundles import resolve_storage_bundle
from easyrag.rag.types import (
    AnswerModelFunc,
    AnswerParam,
    AnswerResult,
    DEFAULT_KG_ENTITY_TYPES,
    ChunkerFunc,
    EmbeddingFunc,
    KGExtractionConfig,
    LLMFunc,
    QueryModelFunc,
    QueryParam,
    QueryResult,
    RerankerFunc,
)
from easyrag.rag.providers import (
    can_use_openai_compatible_models,
    default_embedding_func,
    default_kg_model_func,
    default_query_model_func,
    default_reranker_func,
)
from easyrag.rag.utils import slugify


def _resolve_kg_extraction_config(
    config: KGExtractionConfig | None,
) -> KGExtractionConfig:
    """Resolve KG extraction config with env-backed defaults."""

    if config is not None:
        if config.entity_types:
            return config
        return KGExtractionConfig(
            entity_types=get_kg_entity_types() or DEFAULT_KG_ENTITY_TYPES,
            max_entities_per_chunk=config.max_entities_per_chunk,
            max_relations_per_chunk=config.max_relations_per_chunk,
            fallback_to_rules=config.fallback_to_rules,
        )
    return KGExtractionConfig(
        entity_types=get_kg_entity_types() or DEFAULT_KG_ENTITY_TYPES
    )


class EasyRAG:
    """Single-repository RAG orchestrator with pluggable storage backends."""

    def __init__(
        self,
        *,
        working_dir: str | Path | None = None,
        workspace: str | None = None,
        llm_model_func: LLMFunc | None = None,
        query_model_func: QueryModelFunc | None = None,
        embedding_func: EmbeddingFunc | None = None,
        reranker_func: RerankerFunc | None = None,
        answer_model_func: AnswerModelFunc | None = None,
        kg_extraction_config: KGExtractionConfig | None = None,
        storage_backend: str | None = None,
        kv_storage_cls: type[BaseKVStorage] | None = None,
        vector_storage_cls: type[BaseVectorStorage] | None = None,
        graph_storage_cls: type[BaseGraphStorage] | None = None,
        doc_status_storage_cls: type[BaseDocStatusStorage] | None = None,
        chunking_config: ChunkingConfig | None = None,
        chunker_registry: dict[str, ChunkerFunc] | None = None,
    ) -> None:
        resolved_bundle = resolve_storage_bundle(storage_backend)
        self.working_dir = Path(working_dir or get_rag_working_dir()).resolve()
        self.workspace = workspace or get_rag_workspace()
        self.workspace_dir = self.working_dir / self.workspace
        self.llm_model_func = llm_model_func or (
            default_kg_model_func if has_kg_model_config() else None
        )
        self.query_model_func = query_model_func or (
            default_query_model_func if has_query_model_config() else None
        )
        self.embedding_func = embedding_func or (
            default_embedding_func if has_embedding_model_config() else None
        )
        self.reranker_func = reranker_func or (
            default_reranker_func if has_rerank_model_config() else None
        )
        self.answer_model_func = answer_model_func
        self.kg_extraction_config = _resolve_kg_extraction_config(kg_extraction_config)
        self.chunking_config = chunking_config or ChunkingConfig()
        self.chunker_registry = chunker_registry or build_chunker_registry()
        self.query_preprocessor = QueryPreprocessor(self.query_model_func)
        self.kv_storage = (kv_storage_cls or resolved_bundle[0])(
            str(self.working_dir), self.workspace
        )
        self.vector_storage = (vector_storage_cls or resolved_bundle[1])(
            str(self.working_dir), self.workspace
        )
        self.graph_storage = (graph_storage_cls or resolved_bundle[2])(
            str(self.working_dir), self.workspace
        )
        self.doc_status_storage = (doc_status_storage_cls or resolved_bundle[3])(
            str(self.working_dir), self.workspace
        )
        self.vector_storage.set_embedding_func(self.embedding_func)
        self._initialized = False

    async def initialize_storages(self) -> None:
        """Load or create all configured storages."""

        if self._initialized:
            return
        await self.kv_storage.initialize()
        await self.vector_storage.initialize()
        await self.graph_storage.initialize()
        await self.doc_status_storage.initialize()
        self._initialized = True

    @staticmethod
    def load_repo_documents(repo_root: str | Path) -> list[Document]:
        """Expose repository document discovery through the canonical entry point."""

        return load_repo_documents(repo_root)

    @staticmethod
    def prepare_documents(
        texts: str | Sequence[str],
        *,
        ids: Sequence[str] | None = None,
        file_paths: Sequence[str] | None = None,
    ) -> list[Document]:
        """Expose document normalization through the canonical entry point."""

        return prepare_documents_for_insert(texts, ids=ids, file_paths=file_paths)

    async def finalize_storages(self) -> None:
        """Persist all configured storages."""

        if not self._initialized:
            return
        await self.kv_storage.finalize()
        await self.vector_storage.finalize()
        await self.graph_storage.finalize()
        await self.doc_status_storage.finalize()
        self._initialized = False

    async def ainsert(
        self,
        texts: str | Sequence[str],
        *,
        ids: Sequence[str] | None = None,
        file_paths: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Insert one or more documents into the configured workspace."""

        self._ensure_initialized()
        documents, preparation_report = prepare_documents_for_insert_with_report(
            texts, ids=ids, file_paths=file_paths
        )
        stats = await ingest_documents(self, documents)
        quality_counts = dict(stats.get("quality_issue_counts", {}))
        if preparation_report.get("empty_after_normalization", 0):
            quality_counts["empty_after_normalization"] = int(
                quality_counts.get("empty_after_normalization", 0)
            ) + int(preparation_report["empty_after_normalization"])
        stats["quality_issue_counts"] = quality_counts
        stats["skipped_documents"] = int(stats.get("skipped_documents", 0)) + int(
            preparation_report.get("empty_after_normalization", 0)
        )
        return stats

    async def ainsert_documents(self, documents: Sequence[Document]) -> dict[str, Any]:
        """Insert pre-built Document objects while preserving their metadata."""

        self._ensure_initialized()
        return await ingest_documents(self, list(documents))

    async def adelete_documents(self, doc_ids: Sequence[str]) -> dict[str, int]:
        """Delete one or more documents and all derived index artifacts."""

        self._ensure_initialized()
        deleted = {
            "documents": 0,
            "chunks": 0,
            "summaries": 0,
            "vectors": 0,
            "statuses": 0,
            "graph_entities": 0,
            "graph_relations": 0,
        }
        for doc_id in dict.fromkeys(
            str(value) for value in doc_ids if str(value).strip()
        ):
            kv_stats = await self.kv_storage.delete_by_document(doc_id)
            vector_stats = await self.vector_storage.delete_by_document(doc_id)
            graph_stats = await self.graph_storage.delete_by_document(doc_id)
            status_deleted = await self.doc_status_storage.delete_by_document(doc_id)
            removed_entity_ids = list(graph_stats.get("removed_entity_ids", []))
            updated_entity_ids = list(graph_stats.get("updated_entity_ids", []))
            entity_vector_stats = await sync_entity_vectors(
                self,
                updated_entity_ids,
                removed_entity_ids=removed_entity_ids,
            )
            deleted["documents"] += int(kv_stats.get("documents", 0))
            deleted["chunks"] += int(kv_stats.get("chunks", 0))
            deleted["summaries"] += int(kv_stats.get("summaries", 0))
            deleted["vectors"] += sum(int(value) for value in vector_stats.values())
            deleted["vectors"] += int(entity_vector_stats.get("deleted", 0))
            deleted["statuses"] += int(status_deleted)
            deleted["graph_entities"] += len(removed_entity_ids)
            deleted["graph_relations"] += len(
                graph_stats.get("removed_relation_ids", [])
            )
        return deleted

    async def aquery(self, query: str, param: QueryParam) -> QueryResult:
        """Run one multi-mode knowledge query against the active workspace."""

        self._ensure_initialized()
        return await execute_query(self, query, param)

    async def aanswer(
        self,
        query: str,
        query_param: QueryParam,
        answer_param: AnswerParam | None = None,
    ) -> AnswerResult:
        """Run retrieval and generation as one grounded answering flow."""

        self._ensure_initialized()
        retrieval_result = await self.aquery(query, query_param)
        return generate_answer(
            query,
            retrieval_result,
            answer_param=answer_param or AnswerParam(),
            answer_model_func=self.answer_model_func,
        )

    async def acreate_entity(
        self,
        *,
        label: str,
        entity_id: str | None = None,
        entity_types: Sequence[str] | None = None,
        description: str = "",
        aliases: Sequence[str] | None = None,
        metadata: dict[str, Any] | None = None,
        provenance: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Create one manually curated entity and synchronize retrieval state."""

        self._ensure_initialized()
        normalized_id = entity_id or f"entity::{slugify(label)}"
        payload = self._build_entity_payload(
            entity_id=normalized_id,
            label=label,
            entity_types=entity_types,
            description=description,
            aliases=aliases,
            metadata=metadata,
            provenance=provenance,
        )
        await self.graph_storage.upsert_nodes([payload])
        await sync_entity_vectors(self, [normalized_id])
        entity = await self.graph_storage.get_node(normalized_id)
        return entity or {"id": normalized_id, **payload}

    async def aupdate_entity(
        self,
        entity_id: str,
        *,
        label: str | None = None,
        entity_types: Sequence[str] | None = None,
        description: str | None = None,
        aliases: Sequence[str] | None = None,
        metadata: dict[str, Any] | None = None,
        provenance: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Update one entity and refresh dependent vectors."""

        self._ensure_initialized()
        existing = await self.graph_storage.get_node(entity_id)
        if existing is None:
            raise ValueError(f"Unknown entity: {entity_id}")
        merged_aliases = list(aliases or [])
        if (
            label
            and str(existing.get("label", "")).strip()
            and label != str(existing.get("label", "")).strip()
        ):
            merged_aliases.append(str(existing.get("label", "")).strip())
        payload = self._build_entity_payload(
            entity_id=entity_id,
            label=label or str(existing.get("label", "")),
            entity_types=entity_types
            if entity_types is not None
            else list(existing.get("entity_types", []) or []),
            description=str(
                existing.get("manual_description", existing.get("description", ""))
            )
            if description is None
            else description,
            aliases=list(existing.get("aliases", []) or []) + merged_aliases,
            metadata=metadata,
            provenance=provenance,
        )
        await self.graph_storage.upsert_nodes([payload])
        await sync_entity_vectors(self, [entity_id])
        relation_ids = [
            str(relation["id"])
            for relation in await self.graph_storage.list_relations(entity_id=entity_id)
        ]
        if relation_ids:
            await sync_relation_vectors(self, relation_ids)
        entity = await self.graph_storage.get_node(entity_id)
        return entity or {"id": entity_id}

    async def adelete_entity(self, entity_id: str) -> dict[str, Any]:
        """Delete one entity and cascade its semantic relations."""

        self._ensure_initialized()
        result = await self.graph_storage.delete_entity(entity_id)
        await self.vector_storage.delete("entity", [entity_id])
        removed_relation_ids = list(result.get("removed_relation_ids", []))
        if removed_relation_ids:
            await self.vector_storage.delete("relation", removed_relation_ids)
        return result

    async def amerge_entities(
        self, source_entity_id: str, target_entity_id: str
    ) -> dict[str, Any]:
        """Merge one entity into another and refresh vectors."""

        self._ensure_initialized()
        result = await self.graph_storage.merge_entities(
            source_entity_id, target_entity_id
        )
        if int(result.get("merged", 0)) <= 0:
            return result
        await self.vector_storage.delete("entity", [source_entity_id])
        await sync_entity_vectors(self, [target_entity_id])
        removed_relation_ids = list(result.get("removed_relation_ids", []))
        surviving_relation_ids = [
            str(relation["id"])
            for relation in await self.graph_storage.list_relations(
                entity_id=target_entity_id
            )
        ]
        await sync_relation_vectors(
            self, surviving_relation_ids, removed_relation_ids=removed_relation_ids
        )
        return result

    async def acreate_relation(
        self,
        *,
        source_entity_id: str,
        target_entity_id: str,
        relation: str,
        relation_id: str | None = None,
        description: str = "",
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
        provenance: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Create one first-class semantic relation."""

        self._ensure_initialized()
        payload = await self._build_relation_payload(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relation=relation,
            relation_id=relation_id or f"relation::{uuid4().hex}",
            description=description,
            weight=weight,
            metadata=metadata,
            provenance=provenance,
        )
        await self.graph_storage.upsert_relation_records([payload])
        await sync_relation_vectors(self, [str(payload["id"])])
        stored = await self.graph_storage.get_relation(str(payload["id"]))
        return stored or payload

    async def aupdate_relation(
        self,
        relation_id: str,
        *,
        source_entity_id: str | None = None,
        target_entity_id: str | None = None,
        relation: str | None = None,
        description: str | None = None,
        weight: float | None = None,
        metadata: dict[str, Any] | None = None,
        provenance: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Update one semantic relation and refresh retrieval state."""

        self._ensure_initialized()
        existing = await self.graph_storage.get_relation(relation_id)
        if existing is None:
            raise ValueError(f"Unknown relation: {relation_id}")
        payload = await self._build_relation_payload(
            source_entity_id=source_entity_id
            or str(existing.get("source_entity_id", "")),
            target_entity_id=target_entity_id
            or str(existing.get("target_entity_id", "")),
            relation=relation or str(existing.get("relation", "related_to")),
            relation_id=relation_id,
            description=str(existing.get("description", ""))
            if description is None
            else description,
            weight=float(existing.get("weight", 1.0)) if weight is None else weight,
            metadata={**dict(existing.get("metadata", {})), **dict(metadata or {})},
            provenance=provenance
            if provenance is not None
            else list(existing.get("provenance", []) or []),
        )
        await self.graph_storage.upsert_relation_records([payload])
        await sync_relation_vectors(self, [relation_id])
        stored = await self.graph_storage.get_relation(relation_id)
        return stored or payload

    async def adelete_relation(self, relation_id: str) -> dict[str, Any]:
        """Delete one semantic relation and remove its retrieval vector."""

        self._ensure_initialized()
        result = await self.graph_storage.delete_relation(relation_id)
        await self.vector_storage.delete("relation", [relation_id])
        return result

    async def amerge_relations(
        self, source_relation_id: str, target_relation_id: str
    ) -> dict[str, Any]:
        """Merge two semantic relations and preserve the target identifier."""

        self._ensure_initialized()
        result = await self.graph_storage.merge_relations(
            source_relation_id, target_relation_id
        )
        if int(result.get("merged", 0)) <= 0:
            return result
        await sync_relation_vectors(
            self, [target_relation_id], removed_relation_ids=[source_relation_id]
        )
        return result

    async def ainsert_custom_kg(
        self,
        *,
        entities: Sequence[dict[str, Any]],
        relations: Sequence[dict[str, Any]],
        source_label: str | None = None,
        batch_id: str | None = None,
    ) -> dict[str, int]:
        """Insert manually curated entities and relations into the active workspace."""

        self._ensure_initialized()
        normalized_batch_id = (
            batch_id or slugify(source_label or uuid4().hex) or uuid4().hex
        )
        provenance = [f"manual:{normalized_batch_id}"]
        entity_payloads: list[dict[str, Any]] = []
        entity_ids: list[str] = []
        for entity in entities:
            label = str(entity.get("label", "")).strip()
            if not label:
                continue
            entity_id = str(entity.get("id", "")).strip() or f"entity::{slugify(label)}"
            entity_payloads.append(
                self._build_entity_payload(
                    entity_id=entity_id,
                    label=label,
                    entity_types=list(entity.get("entity_types", []) or []),
                    description=str(entity.get("description", "")).strip(),
                    aliases=list(entity.get("aliases", []) or []),
                    metadata=dict(entity.get("metadata", {})),
                    provenance=provenance + list(entity.get("provenance", []) or []),
                )
            )
            entity_ids.append(entity_id)
        if entity_payloads:
            await self.graph_storage.upsert_nodes(entity_payloads)

        relation_payloads: list[dict[str, Any]] = []
        relation_ids: list[str] = []
        for relation in relations:
            source_entity_id = str(relation.get("source_entity_id", "")).strip()
            target_entity_id = str(relation.get("target_entity_id", "")).strip()
            relation_name = str(relation.get("relation", "")).strip()
            if not source_entity_id or not target_entity_id or not relation_name:
                continue
            relation_id = (
                str(relation.get("id", "")).strip() or f"relation::{uuid4().hex}"
            )
            relation_payloads.append(
                await self._build_relation_payload(
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity_id,
                    relation=relation_name,
                    relation_id=relation_id,
                    description=str(relation.get("description", "")).strip(),
                    weight=float(relation.get("weight", 1.0)),
                    metadata=dict(relation.get("metadata", {})),
                    provenance=provenance + list(relation.get("provenance", []) or []),
                )
            )
            relation_ids.append(relation_id)
        if relation_payloads:
            await self.graph_storage.upsert_relation_records(relation_payloads)

        entity_stats = await sync_entity_vectors(self, entity_ids)
        relation_stats = await sync_relation_vectors(self, relation_ids)
        return {
            "entities": entity_stats["upserted"],
            "relations": relation_stats["upserted"],
        }

    async def get_stats(self) -> dict[str, int]:
        """Return aggregated storage stats for diagnostics and build output."""

        self._ensure_initialized()
        stats = await self.kv_storage.get_stats()
        vector_stats = await self.vector_storage.get_stats()
        graph_stats = await self.graph_storage.get_stats()
        status_stats = await self.doc_status_storage.get_stats()
        return {
            **stats,
            "entity_vectors": int(vector_stats.get("entity", 0)),
            "relation_vectors": int(vector_stats.get("relation", 0)),
            "chunk_vectors": int(vector_stats.get("chunk", 0)),
            "summary_vectors": int(vector_stats.get("summary", 0)),
            "vector_backend": str(
                vector_stats.get(
                    "vector_backend", self.vector_storage.get_backend_name()
                )
            ),
            "graph_nodes": int(graph_stats.get("nodes", 0)),
            "graph_edges": int(graph_stats.get("edges", 0)),
            "status_records": int(status_stats.get("documents", 0)),
        }

    def can_rerank(self) -> bool:
        """Return whether a reranker is configured."""

        return self.reranker_func is not None and can_use_openai_compatible_models()

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                "EasyRAG storages are not initialized. Call await rag.initialize_storages() first."
            )

    def _build_entity_payload(
        self,
        *,
        entity_id: str,
        label: str,
        entity_types: Sequence[str] | None = None,
        description: str = "",
        aliases: Sequence[str] | None = None,
        metadata: dict[str, Any] | None = None,
        provenance: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Build one manual entity node payload."""

        return build_entity_payload(
            entity_id=entity_id,
            label=label,
            entity_types=entity_types,
            description=description,
            aliases=aliases,
            metadata=metadata,
            provenance=provenance,
        )

    async def _build_relation_payload(
        self,
        *,
        source_entity_id: str,
        target_entity_id: str,
        relation: str,
        relation_id: str,
        description: str = "",
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
        provenance: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Build one semantic relation record payload after validating endpoints."""

        return await build_relation_payload(
            self.graph_storage,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relation=relation,
            relation_id=relation_id,
            description=description,
            weight=weight,
            metadata=metadata,
            provenance=provenance,
        )
