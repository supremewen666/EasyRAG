"""Tests for the EasyRAG-style repository knowledge subsystem."""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from easyrag.support.optional_deps import Document
from easyrag.rag import EasyRAG, KGExtractionConfig, QueryParam
from easyrag.rag.indexing import ChunkingConfig, build_vector_index, chunk_documents, load_repo_documents, rebuild_document_index
from easyrag.tools import create_search_docs_tool, search_docs_tool
from scripts import build_index

_KEYWORDS = [
    "architecture",
    "easyrag",
    "embedding",
    "rerank",
    "retrieval",
    "query",
    "rewrite",
    "index",
    "pdf",
    "semantic",
]


def _run(awaitable: object) -> object:
    """Run an async helper inside unittest."""

    return asyncio.run(awaitable)


def _stub_embedding(texts: list[str]) -> list[list[float]]:
    """Return deterministic dense embeddings for tests."""

    vectors: list[list[float]] = []
    for text in texts:
        lowered = text.lower()
        vector = [float(lowered.count(keyword)) for keyword in _KEYWORDS]
        vector.append(float(len(lowered.split())))
        vectors.append(vector)
    return vectors


def _stub_query_model(prompt: str, *, task: str, count: int = 1) -> str | list[str]:
    """Return deterministic query rewrites and MQE variants."""

    cleaned = prompt.split(":", 1)[-1].strip()
    if task == "rewrite":
        return f"{cleaned} repository architecture"
    if task == "mqe":
        return [f"{cleaned} variant {index}" for index in range(1, count + 1)]
    raise ValueError(task)


def _stub_reranker(query: str, items: list[dict[str, object]]) -> list[dict[str, object]]:
    """Rerank candidates by keyword overlap with the query."""

    lowered_query = query.lower()
    scored = []
    for item in items:
        text = str(item.get("text", "")).lower()
        score = sum(text.count(keyword) for keyword in lowered_query.split())
        candidate = dict(item)
        candidate["rerank_score"] = score
        scored.append(candidate)
    scored.sort(key=lambda item: float(item.get("rerank_score", 0.0)), reverse=True)
    return scored


def _stub_kg_model_func(
    text: str,
    *,
    entity_types: list[str],
    max_entities: int,
    max_relations: int,
    metadata: dict[str, object] | None = None,
) -> dict[str, list[dict[str, str]]]:
    """Return deterministic architecture-oriented KG extraction results."""

    del metadata
    allowed = set(entity_types)

    def pick(*candidates: str) -> str:
        for candidate in candidates:
            if candidate in allowed:
                return candidate
        return entity_types[0] if entity_types else "concept"

    entities: list[dict[str, str]] = [
        {"name": "EasyRAG", "type": pick("component", "module"), "description": "Repository knowledge system root."},
    ]
    relations: list[dict[str, str]] = []
    lowered = text.lower()

    if "workflow" in lowered or "retrieval" in lowered:
        entities.append({"name": "Retrieval Workflow", "type": pick("workflow", "concept"), "description": "Retrieval flow for repository answers."})
        relations.append({"source": "EasyRAG", "target": "Retrieval Workflow", "relation": "orchestrates", "description": "EasyRAG orchestrates the retrieval workflow."})
    if "rewrite" in lowered or "query" in lowered:
        entities.append({"name": "Query Rewriter", "type": pick("tool", "component"), "description": "Query preprocessing helper."})
        relations.append({"source": "EasyRAG", "target": "Query Rewriter", "relation": "uses", "description": "EasyRAG uses query rewriting during retrieval."})
    if "embedding" in lowered or "rerank" in lowered:
        entities.append({"name": "Embedding Layer", "type": pick("dependency", "tool"), "description": "Dense retrieval support layer."})
        relations.append({"source": "EasyRAG", "target": "Embedding Layer", "relation": "depends_on", "description": "EasyRAG depends on embeddings and reranking for dense retrieval."})

    deduped_entities: list[dict[str, str]] = []
    seen_entities: set[str] = set()
    for entity in entities:
        key = entity["name"].lower()
        if key in seen_entities:
            continue
        seen_entities.add(key)
        deduped_entities.append(entity)

    deduped_relations: list[dict[str, str]] = []
    seen_relations: set[tuple[str, str, str]] = set()
    for relation in relations:
        key = (relation["source"].lower(), relation["target"].lower(), relation["relation"])
        if key in seen_relations:
            continue
        seen_relations.add(key)
        deduped_relations.append(relation)

    return {
        "entities": deduped_entities[:max_entities],
        "relations": deduped_relations[:max_relations],
    }


class EasyRAGLifecycleTestCase(unittest.TestCase):
    """Verify lifecycle, persistence, and query modes."""

    def test_requires_initialize_before_use(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(working_dir=tmp_dir, workspace="lifecycle", embedding_func=_stub_embedding, query_model_func=_stub_query_model)
            with self.assertRaises(RuntimeError):
                _run(rag.aquery("architecture", QueryParam(mode="naive")))
            with self.assertRaises(RuntimeError):
                _run(rag.ainsert("Architecture notes"))

    def test_insert_and_query_modes_with_preprocessing_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="repo",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
                reranker_func=_stub_reranker,
            )
            _run(rag.initialize_storages())
            try:
                stats = _run(
                    rag.ainsert(
                        [
                            "# Architecture\nEasyRAG uses query rewriting and retrieval workflows for repository guidance.\n## Retrieval\nHybrid retrieval uses semantic chunks.\n",
                            "# Setup\nUse embeddings and rerank models to answer documentation questions.\n",
                        ],
                        ids=["doc::architecture", "doc::setup"],
                        file_paths=["docs/architecture.md", "docs/setup.md"],
                    )
                )
                self.assertEqual(stats["documents"], 2)

                for mode in ("naive", "local", "global", "hybrid", "mix"):
                    result = _run(
                        rag.aquery(
                            "How does query rewriting help repository guidance?",
                            QueryParam(mode=mode, chunk_top_k=3, enable_rerank=(mode in {"hybrid", "mix"})),
                        )
                    )
                    self.assertTrue(result.citations, mode)
                    self.assertEqual(result.mode, mode)
                    self.assertIn("rewritten_query", result.metadata)
                    self.assertIn("expanded_queries", result.metadata)
                    self.assertIn("retrieval_queries", result.metadata)

                aggregate = _run(rag.get_stats())
                self.assertGreaterEqual(aggregate["graph_nodes"], 4)
                self.assertGreaterEqual(aggregate["entity_vectors"], 1)
                self.assertIn(aggregate["vector_backend"], {"hnsw_embedding", "dense_embedding"})
            finally:
                _run(rag.finalize_storages())

    def test_hnsw_backend_is_preferred_when_available(self) -> None:
        class FakeHNSWIndex:
            def __init__(self, space: str, dim: int) -> None:
                self.space = space
                self.dim = dim
                self._embeddings = np.zeros((0, dim), dtype=np.float32)
                self._labels = np.zeros((0,), dtype=np.int32)

            def init_index(self, max_elements: int, ef_construction: int, M: int) -> None:
                del max_elements, ef_construction, M

            def add_items(self, embeddings: np.ndarray, labels: np.ndarray) -> None:
                self._embeddings = np.array(embeddings, dtype=np.float32)
                self._labels = np.array(labels, dtype=np.int32)

            def set_ef(self, ef: int) -> None:
                del ef

            def knn_query(self, query_embedding: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
                normalized_records = self._embeddings / np.maximum(np.linalg.norm(self._embeddings, axis=1, keepdims=True), 1e-12)
                normalized_query = query_embedding / np.maximum(np.linalg.norm(query_embedding, axis=1, keepdims=True), 1e-12)
                scores = normalized_records @ normalized_query[0]
                ranked = np.argsort(scores)[::-1][:k]
                distances = 1.0 - scores[ranked]
                return self._labels[ranked][None, :], distances[None, :]

        fake_hnswlib = mock.Mock(Index=FakeHNSWIndex)
        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch("easyrag.rag.storage.local.hnswlib", fake_hnswlib):
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="hnsw",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        [
                            "# Architecture\nEasyRAG uses retrieval orchestration.\n",
                            "# Setup\nEasyRAG uses embeddings for dense search.\n",
                        ],
                        ids=["doc::architecture", "doc::setup"],
                        file_paths=["docs/architecture.md", "docs/setup.md"],
                    )
                )
                result = _run(rag.aquery("How does EasyRAG retrieval work?", QueryParam(mode="naive", rewrite_enabled=False, mqe_enabled=False)))
                aggregate = _run(rag.get_stats())
            finally:
                _run(rag.finalize_storages())

        self.assertTrue(result.citations)
        self.assertIn("EasyRAG", result.citations[0]["snippet"])
        self.assertEqual(result.metadata["vector_backend"], "hnsw_embedding")
        self.assertEqual(aggregate["vector_backend"], "hnsw_embedding")

    def test_workspace_isolation_and_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag_alpha = EasyRAG(working_dir=tmp_dir, workspace="alpha", embedding_func=_stub_embedding, query_model_func=_stub_query_model)
            rag_beta = EasyRAG(working_dir=tmp_dir, workspace="beta", embedding_func=_stub_embedding, query_model_func=_stub_query_model)

            _run(rag_alpha.initialize_storages())
            _run(rag_beta.initialize_storages())
            try:
                _run(rag_alpha.ainsert("Alpha design uses embeddings.", ids=["doc::alpha"], file_paths=["docs/alpha.md"]))
                _run(rag_beta.ainsert("Beta design uses retrieval workflows.", ids=["doc::beta"], file_paths=["docs/beta.md"]))
            finally:
                _run(rag_alpha.finalize_storages())
                _run(rag_beta.finalize_storages())

            reopened_alpha = EasyRAG(working_dir=tmp_dir, workspace="alpha", embedding_func=_stub_embedding, query_model_func=_stub_query_model)
            reopened_beta = EasyRAG(working_dir=tmp_dir, workspace="beta", embedding_func=_stub_embedding, query_model_func=_stub_query_model)
            _run(reopened_alpha.initialize_storages())
            _run(reopened_beta.initialize_storages())
            try:
                alpha_result = _run(reopened_alpha.aquery("What uses embeddings?", QueryParam(mode="naive", rewrite_enabled=False, mqe_enabled=False)))
                beta_result = _run(reopened_beta.aquery("What uses retrieval workflows?", QueryParam(mode="naive", rewrite_enabled=False, mqe_enabled=False)))
                self.assertTrue(alpha_result.citations)
                self.assertTrue(beta_result.citations)
                self.assertIn("embeddings", alpha_result.citations[0]["snippet"])
                self.assertIn("retrieval workflows", beta_result.citations[0]["snippet"])
            finally:
                _run(reopened_alpha.finalize_storages())
                _run(reopened_beta.finalize_storages())

            self.assertTrue((Path(tmp_dir) / "alpha" / "kv" / "documents.json").exists())
            self.assertTrue((Path(tmp_dir) / "beta" / "vector" / "chunk.npy").exists())

    def test_dense_failure_falls_back_to_token_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            def failing_embedding(_: list[str]) -> list[list[float]]:
                raise RuntimeError("embedding failure")

            rag = EasyRAG(working_dir=tmp_dir, workspace="fallback", embedding_func=failing_embedding, query_model_func=_stub_query_model)
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        ["# Architecture\nEasyRAG uses query rewriting for retrieval orchestration.\n"],
                        ids=["doc::architecture"],
                        file_paths=["docs/architecture.md"],
                    )
                )
                result = _run(rag.aquery("retrieval orchestration", QueryParam(mode="naive", rewrite_enabled=False, mqe_enabled=False)))
            finally:
                _run(rag.finalize_storages())

            self.assertTrue(result.citations)
            self.assertEqual(result.metadata["vector_backend"], "fallback_token")

    def test_delete_documents_removes_all_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="delete",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
                llm_model_func=_stub_kg_model_func,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        ["# Architecture\nEasyRAG uses query rewriting and retrieval workflows.\n"],
                        ids=["doc::architecture"],
                        file_paths=["docs/architecture.md"],
                    )
                )
                deleted = _run(rag.adelete_documents(["doc::architecture"]))
                result = _run(rag.aquery("query rewriting", QueryParam(mode="naive", rewrite_enabled=False, mqe_enabled=False)))
                aggregate = _run(rag.get_stats())
            finally:
                _run(rag.finalize_storages())

            self.assertEqual(deleted["documents"], 1)
            self.assertFalse(result.citations)
            self.assertEqual(aggregate["documents"], 0)
            self.assertEqual(aggregate["chunks"], 0)
            self.assertEqual(aggregate["entity_vectors"], 0)
            self.assertEqual(aggregate["relation_vectors"], 0)
            self.assertEqual(aggregate["status_records"], 0)

    def test_upsert_replaces_existing_doc_id_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="update",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
                llm_model_func=_stub_kg_model_func,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        ["# Architecture\nEasyRAG uses query rewriting for retrieval.\n"],
                        ids=["doc::architecture"],
                        file_paths=["docs/architecture.md"],
                    )
                )
                _run(
                    rag.ainsert(
                        ["# Architecture\nEasyRAG uses embeddings for dense retrieval.\n"],
                        ids=["doc::architecture"],
                        file_paths=["docs/architecture.md"],
                    )
                )
                stored_chunk = _run(rag.kv_storage.get_chunk("doc::architecture::chunk::0"))
                old_result = _run(rag.aquery("query rewriting", QueryParam(mode="naive", rewrite_enabled=False, mqe_enabled=False)))
                new_result = _run(rag.aquery("embeddings", QueryParam(mode="naive", rewrite_enabled=False, mqe_enabled=False)))
            finally:
                _run(rag.finalize_storages())

            self.assertNotIn("query rewriting", stored_chunk["text"])
            self.assertTrue(old_result.citations)
            self.assertNotIn("query rewriting", old_result.citations[0]["snippet"])
            self.assertTrue(new_result.citations)
            self.assertIn("embeddings", new_result.citations[0]["snippet"])

    def test_shared_entity_survives_single_document_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="shared",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
                llm_model_func=_stub_kg_model_func,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        [
                            "# Alpha\nEasyRAG uses retrieval workflows.\n",
                            "# Beta\nEasyRAG uses embeddings for dense search.\n",
                        ],
                        ids=["doc::alpha", "doc::beta"],
                        file_paths=["docs/alpha.md", "docs/beta.md"],
                    )
                )
                shared_before = _run(rag.graph_storage.get_node("entity::easyrag"))
                _run(rag.adelete_documents(["doc::alpha"]))
                shared_after = _run(rag.graph_storage.get_node("entity::easyrag"))
                beta_result = _run(rag.aquery("embeddings", QueryParam(mode="naive", rewrite_enabled=False, mqe_enabled=False)))
            finally:
                _run(rag.finalize_storages())

            self.assertEqual(sorted(shared_before["doc_ids"]), ["doc::alpha", "doc::beta"])
            self.assertEqual(shared_after["doc_ids"], ["doc::beta"])
            self.assertTrue(beta_result.citations)
            self.assertIn("embeddings", beta_result.citations[0]["snippet"])

    def test_llm_kg_extraction_populates_typed_entity_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="kg",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
                llm_model_func=_stub_kg_model_func,
                kg_extraction_config=KGExtractionConfig(entity_types=("component", "workflow", "tool", "dependency")),
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        ["# Architecture\nEasyRAG uses query rewriting, embeddings, and a retrieval workflow.\n"],
                        ids=["doc::architecture"],
                        file_paths=["docs/architecture.md"],
                    )
                )
                easyrag_entity = _run(rag.graph_storage.get_node("entity::easyrag"))
                aggregate = _run(rag.get_stats())
            finally:
                _run(rag.finalize_storages())

            self.assertIn("component", easyrag_entity["entity_types"])
            self.assertTrue(easyrag_entity["description"])
            self.assertGreaterEqual(aggregate["relation_vectors"], 1)

    def test_easyrag_uses_env_kg_entity_types_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch.dict(
            os.environ,
            {"EASYRAG_KG_ENTITY_TYPES": "workflow,tool"},
            clear=False,
        ):
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="kg-env",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
                llm_model_func=_stub_kg_model_func,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        ["# Architecture\nEasyRAG uses query rewriting and a retrieval workflow.\n"],
                        ids=["doc::architecture"],
                        file_paths=["docs/architecture.md"],
                    )
                )
                workflow_entity = _run(rag.graph_storage.get_node("entity::retrieval-workflow"))
            finally:
                _run(rag.finalize_storages())

            self.assertEqual(rag.kg_extraction_config.entity_types, ("workflow", "tool"))
            self.assertEqual(workflow_entity["entity_types"], ["workflow"])


class ChunkingAndLoadingTestCase(unittest.TestCase):
    """Verify loading and chunk strategy selection."""

    def test_chunk_documents_chooses_structured_and_semantic_strategies(self) -> None:
        documents = [
            Document(
                page_content="# Architecture\nIntro.\n## Retrieval\nSemantic chunks help retrieval.\n",
                metadata={"doc_id": "doc::md", "path": "docs/architecture.md", "relative_path": "docs/architecture.md", "title": "architecture", "source_type": "doc"},
            ),
            Document(
                page_content="Sentence one about semantic retrieval. Sentence two about Qwen. Sentence three about overlap.",
                metadata={"doc_id": "doc::txt", "path": "docs/notes.txt", "relative_path": "docs/notes.txt", "title": "notes", "source_type": "doc"},
            ),
        ]
        rag = EasyRAG(working_dir="/tmp", workspace="unused", embedding_func=_stub_embedding, query_model_func=_stub_query_model)
        chunks = chunk_documents(documents, config=ChunkingConfig(), rag=rag)
        strategies = {str(chunk.metadata.get("chunk_strategy")) for chunk in chunks}

        self.assertIn("structured", strategies)
        self.assertIn("semantic", strategies)
        self.assertTrue(all(chunk.metadata.get("overlap_policy") for chunk in chunks))

    def test_load_repo_documents_includes_pdf_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "design.md").write_text("# Design\nGraph retrieval.\n", encoding="utf-8")
            pdf_path = docs_dir / "manual.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 fake")

            fake_pages = [
                mock.Mock(extract_text=mock.Mock(return_value="Page one architecture notes")),
                mock.Mock(extract_text=mock.Mock(return_value="")),
                mock.Mock(extract_text=mock.Mock(return_value="Page three setup details")),
            ]
            fake_reader = mock.Mock(pages=fake_pages)
            with mock.patch("easyrag.rag.indexing.loaders.PdfReader", return_value=fake_reader):
                documents = load_repo_documents(root)

            pdf_documents = [document for document in documents if document.metadata["source_type"] == "pdf"]
            self.assertEqual(len(pdf_documents), 2)
            self.assertEqual(pdf_documents[0].metadata["page_number"], 1)
            self.assertEqual(pdf_documents[1].metadata["page_number"], 3)

    def test_load_repo_documents_keeps_image_only_pdf_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            pdf_path = docs_dir / "visual-manual.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 fake")

            fake_image = mock.Mock(name="diagram.png", data=b"\x89PNG\r\n\x1a\n")
            fake_pages = [
                mock.Mock(extract_text=mock.Mock(return_value=""), images=[fake_image]),
            ]
            fake_reader = mock.Mock(pages=fake_pages)
            with mock.patch("easyrag.rag.indexing.loaders.PdfReader", return_value=fake_reader):
                documents = load_repo_documents(root)

            self.assertEqual(len(documents), 1)
            self.assertIn("Scanned PDF page 1", documents[0].page_content)
            self.assertTrue(documents[0].metadata["has_visual_content"])
            image_paths = documents[0].metadata["image_paths"]
            self.assertEqual(len(image_paths), 1)
            self.assertTrue(Path(image_paths[0]).exists())


class IndexingHelperTestCase(unittest.TestCase):
    """Verify canonical indexing helpers still support local smoke flows."""

    def test_build_vector_index_and_search_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            documents = [
                Document(
                    page_content="# Architecture\nEasyRAG uses query rewriting for workflow orchestration.\n",
                    metadata={
                        "source_type": "doc",
                        "path": "docs/architecture.md",
                        "relative_path": "docs/architecture.md",
                        "title": "architecture",
                        "doc_id": "doc::architecture",
                    },
                )
            ]
            with mock.patch.dict(
                os.environ,
                {
                    "EASYRAG_DATA_DIR": str(Path(tmp_dir) / ".easyrag"),
                    "EASYRAG_INDEX_PATH": str(Path(tmp_dir) / ".easyrag" / "rag_index.json"),
                    "EASYRAG_WORKING_DIR": tmp_dir,
                    "EASYRAG_WORKSPACE": "compat",
                    "OPENAI_API_KEY": "",
                },
                clear=False,
            ):
                build_vector_index(documents)
                rag = EasyRAG(
                    working_dir=tmp_dir,
                    workspace="compat",
                    embedding_func=_stub_embedding,
                    query_model_func=_stub_query_model,
                )
                _run(rag.initialize_storages())
                try:
                    results = _run(
                        rag.aquery(
                            "How does workflow orchestration work?",
                            QueryParam(mode="naive", top_k=3, chunk_top_k=3, rewrite_enabled=False, mqe_enabled=False),
                        )
                    )
                    tool = create_search_docs_tool(lambda: rag, default_mode="naive", rewrite_enabled=False, mqe_enabled=False)
                    tool_results = tool.invoke({"query": "What uses query rewriting?"})
                finally:
                    _run(rag.finalize_storages())

            self.assertTrue(results.citations)
            self.assertIn("query rewriting", results.citations[0]["snippet"])
            self.assertIn("architecture", tool_results)

    def test_search_tool_runs_inside_existing_event_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="tool-loop",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        "# Architecture\nEasyRAG uses query rewriting for workflow orchestration.\n",
                        ids=["doc::architecture"],
                        file_paths=["docs/architecture.md"],
                    )
                )
                tool = create_search_docs_tool(lambda: rag, default_mode="naive", rewrite_enabled=False, mqe_enabled=False)

                async def invoke_tool() -> str:
                    return tool.invoke({"query": "What uses query rewriting?"})

                tool_results = _run(invoke_tool())
            finally:
                _run(rag.finalize_storages())

        self.assertIn("query rewriting", tool_results)

    def test_search_docs_tool_propagates_query_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch.dict(
                os.environ,
                {
                    "EASYRAG_WORKING_DIR": tmp_dir,
                    "EASYRAG_WORKSPACE": "tool-errors",
                },
                clear=False,
            ):
                with mock.patch("easyrag.tools.EasyRAG.initialize_storages", new=mock.AsyncMock()):
                    with mock.patch("easyrag.tools.EasyRAG.finalize_storages", new=mock.AsyncMock()):
                        with mock.patch("easyrag.tools.EasyRAG.aquery", new=mock.AsyncMock(side_effect=RuntimeError("boom"))):
                            with self.assertRaisesRegex(RuntimeError, "boom"):
                                search_docs_tool.invoke({"query": "What uses query rewriting?"})


class BuildIndexScriptTestCase(unittest.TestCase):
    """Verify the build script populates the EasyRAG workspace."""

    def test_build_index_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            docs_dir = repo_root / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "architecture.md").write_text(
                "# Architecture\nEasyRAG connects indexing, retrieval, and query rewriting.\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with mock.patch.dict(
                os.environ,
                {
                    "EASYRAG_REPO_ROOT": str(repo_root),
                    "EASYRAG_DATA_DIR": str(repo_root / ".easyrag"),
                    "EASYRAG_INDEX_PATH": str(repo_root / ".easyrag" / "rag_index.json"),
                    "EASYRAG_WORKING_DIR": str(repo_root / ".easyrag" / "rag_storage"),
                    "EASYRAG_WORKSPACE": "demo",
                    "OPENAI_API_KEY": "",
                },
                clear=False,
            ):
                with contextlib.redirect_stdout(stdout):
                    build_index.main()

            output = stdout.getvalue()
            self.assertIn("documents=1", output)
            self.assertIn("workspace=demo", output)
            self.assertIn("vector_backend=fallback_token", output)
            self.assertTrue((repo_root / ".easyrag" / "rag_storage" / "demo" / "kv" / "documents.json").exists())

    def test_build_index_script_runs_inside_existing_event_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            docs_dir = repo_root / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "architecture.md").write_text(
                "# Architecture\nEasyRAG connects indexing, retrieval, and query rewriting.\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with mock.patch.dict(
                os.environ,
                {
                    "EASYRAG_REPO_ROOT": str(repo_root),
                    "EASYRAG_DATA_DIR": str(repo_root / ".easyrag"),
                    "EASYRAG_INDEX_PATH": str(repo_root / ".easyrag" / "rag_index.json"),
                    "EASYRAG_WORKING_DIR": str(repo_root / ".easyrag" / "rag_storage"),
                    "EASYRAG_WORKSPACE": "loop",
                    "OPENAI_API_KEY": "",
                },
                clear=False,
            ):
                async def run_script() -> None:
                    with contextlib.redirect_stdout(stdout):
                        build_index.main([])

                _run(run_script())

            output = stdout.getvalue()
            self.assertIn("documents=1", output)
            self.assertIn("workspace=loop", output)

    def test_build_index_delete_refreshes_legacy_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            docs_dir = repo_root / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "architecture.md").write_text(
                "# Architecture\nEasyRAG connects indexing, retrieval, and query rewriting.\n",
                encoding="utf-8",
            )

            index_path = repo_root / ".easyrag" / "rag_index.json"
            with mock.patch.dict(
                os.environ,
                {
                    "EASYRAG_REPO_ROOT": str(repo_root),
                    "EASYRAG_DATA_DIR": str(repo_root / ".easyrag"),
                    "EASYRAG_INDEX_PATH": str(index_path),
                    "EASYRAG_WORKING_DIR": str(repo_root / ".easyrag" / "rag_storage"),
                    "EASYRAG_WORKSPACE": "demo",
                    "OPENAI_API_KEY": "",
                },
                clear=False,
            ):
                build_index.main([])
                before_delete = json.loads(index_path.read_text(encoding="utf-8"))
                build_index.main(["--action", "delete", "--doc-id", "doc::docs-architecture-md"])
                after_delete = json.loads(index_path.read_text(encoding="utf-8"))

            self.assertEqual(len(before_delete), 1)
            self.assertEqual(after_delete, [])

    def test_rebuild_document_index_full_sync_removes_stale_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            docs_dir = repo_root / "docs"
            docs_dir.mkdir(parents=True)
            architecture_path = docs_dir / "architecture.md"
            setup_path = docs_dir / "setup.md"
            architecture_path.write_text("# Architecture\nEasyRAG uses retrieval workflows.\n", encoding="utf-8")
            setup_path.write_text("# Setup\nEasyRAG uses embeddings.\n", encoding="utf-8")

            with mock.patch.dict(
                os.environ,
                {
                    "EASYRAG_REPO_ROOT": str(repo_root),
                    "EASYRAG_DATA_DIR": str(repo_root / ".easyrag"),
                    "EASYRAG_INDEX_PATH": str(repo_root / ".easyrag" / "rag_index.json"),
                    "EASYRAG_WORKING_DIR": str(repo_root / ".easyrag" / "rag_storage"),
                    "EASYRAG_WORKSPACE": "sync",
                    "OPENAI_API_KEY": "",
                },
                clear=False,
            ):
                initial_docs = load_repo_documents(repo_root)
                removed_doc_id = next(
                    str(document.metadata["doc_id"])
                    for document in initial_docs
                    if document.metadata["title"] == "setup"
                )
                rebuild_document_index(repo_root)
                setup_path.unlink()
                rebuild_document_index(repo_root)

                rag = EasyRAG(
                    working_dir=repo_root / ".easyrag" / "rag_storage",
                    workspace="sync",
                    embedding_func=_stub_embedding,
                    query_model_func=_stub_query_model,
                )
                _run(rag.initialize_storages())
                try:
                    aggregate = _run(rag.get_stats())
                    removed_status = _run(rag.doc_status_storage.get_status(removed_doc_id))
                    removed_result = _run(rag.aquery("embeddings", QueryParam(mode="naive", rewrite_enabled=False, mqe_enabled=False)))
                finally:
                    _run(rag.finalize_storages())

            self.assertEqual(aggregate["documents"], 1)
            self.assertIsNone(removed_status)
            self.assertFalse(removed_result.citations)


if __name__ == "__main__":
    unittest.main()
