"""Tests for graph operations, manual KG insertion, and relation lifecycle."""

from __future__ import annotations

import asyncio
import tempfile
import unittest

from easyrag.rag import EasyRAG, QueryParam

_KEYWORDS = [
    "architecture",
    "service",
    "module",
    "workflow",
    "api",
    "data",
    "depends",
    "orchestrates",
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
        return cleaned
    if task == "mqe":
        return [f"{cleaned} variant {index}" for index in range(1, count + 1)]
    raise ValueError(task)


class GraphOpsTestCase(unittest.TestCase):
    """Verify manual entity/relation operations and custom KG insertion."""

    def test_entity_and_relation_crud_refresh_vectors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(working_dir=tmp_dir, workspace="graph", embedding_func=_stub_embedding, query_model_func=_stub_query_model)
            _run(rag.initialize_storages())
            try:
                service = _run(
                    rag.acreate_entity(
                        label="Service API",
                        entity_types=["component"],
                        description="Service boundary for the application layer.",
                    )
                )
                datastore = _run(
                    rag.acreate_entity(
                        label="Data Store",
                        entity_types=["dependency"],
                        description="Persistence dependency.",
                    )
                )
                relation = _run(
                    rag.acreate_relation(
                        source_entity_id=service["id"],
                        target_entity_id=datastore["id"],
                        relation="depends_on",
                        description="Service API depends on Data Store.",
                    )
                )
                updated = _run(rag.aupdate_entity(service["id"], label="API Layer", aliases=["Gateway"]))
                result = _run(rag.aquery("Service API", QueryParam(mode="local", rewrite_enabled=False, mqe_enabled=False)))
                deleted = _run(rag.adelete_relation(relation["id"]))
                aggregate = _run(rag.get_stats())
            finally:
                _run(rag.finalize_storages())

            self.assertIn("Service API", updated["aliases"])
            self.assertIn("API Layer", result.entities)
            self.assertEqual(deleted["deleted_relation"], 1)
            self.assertEqual(aggregate["entity_vectors"], 2)
            self.assertEqual(aggregate["relation_vectors"], 0)

    def test_insert_custom_kg_and_merge_entities_rewrite_relations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(working_dir=tmp_dir, workspace="manual", embedding_func=_stub_embedding, query_model_func=_stub_query_model)
            _run(rag.initialize_storages())
            try:
                inserted = _run(
                    rag.ainsert_custom_kg(
                        batch_id="manual-batch",
                        entities=[
                            {"id": "entity::core-module", "label": "Core Module", "entity_types": ["module"], "description": "Legacy module."},
                            {"id": "entity::platform-module", "label": "Platform Module", "entity_types": ["module"], "description": "Target module."},
                            {"id": "entity::workflow-engine", "label": "Workflow Engine", "entity_types": ["workflow"], "description": "Execution workflow."},
                        ],
                        relations=[
                            {
                                "id": "relation::core-workflow",
                                "source_entity_id": "entity::core-module",
                                "target_entity_id": "entity::workflow-engine",
                                "relation": "orchestrates",
                                "description": "Core Module orchestrates Workflow Engine.",
                            }
                        ],
                    )
                )
                before_merge = _run(rag.aquery("Core Module", QueryParam(mode="local", rewrite_enabled=False, mqe_enabled=False)))
                merged = _run(rag.amerge_entities("entity::core-module", "entity::platform-module"))
                target = _run(rag.graph_storage.get_node("entity::platform-module"))
                source = _run(rag.graph_storage.get_node("entity::core-module"))
                relations = _run(rag.graph_storage.list_relations(entity_id="entity::platform-module"))
                after_merge = _run(rag.aquery("Core Module", QueryParam(mode="local", rewrite_enabled=False, mqe_enabled=False)))
            finally:
                _run(rag.finalize_storages())

            self.assertEqual(inserted["relations"], 1)
            self.assertIn("Core Module", before_merge.entities)
            self.assertEqual(merged["merged"], 1)
            self.assertIsNone(source)
            self.assertIn("Core Module", target["aliases"])
            self.assertEqual(len(relations), 1)
            self.assertEqual(relations[0]["source_entity_id"], "entity::platform-module")
            self.assertIn("Platform Module", after_merge.entities)

    def test_merge_relations_preserves_target_relation_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(working_dir=tmp_dir, workspace="relations", embedding_func=_stub_embedding, query_model_func=_stub_query_model)
            _run(rag.initialize_storages())
            try:
                left = _run(rag.acreate_entity(label="Service Mesh", entity_types=["component"], description="Traffic component."))
                right = _run(rag.acreate_entity(label="Runtime Config", entity_types=["config"], description="Runtime settings."))
                _run(
                    rag.acreate_relation(
                        relation_id="relation::one",
                        source_entity_id=left["id"],
                        target_entity_id=right["id"],
                        relation="depends_on",
                        description="Service Mesh depends on Runtime Config.",
                        provenance=["manual:one"],
                    )
                )
                _run(
                    rag.acreate_relation(
                        relation_id="relation::two",
                        source_entity_id=left["id"],
                        target_entity_id=right["id"],
                        relation="depends_on",
                        description="Service Mesh uses Runtime Config.",
                        provenance=["manual:two"],
                    )
                )
                merged = _run(rag.amerge_relations("relation::one", "relation::two"))
                target_relation = _run(rag.graph_storage.get_relation("relation::two"))
                source_relation = _run(rag.graph_storage.get_relation("relation::one"))
                aggregate = _run(rag.get_stats())
            finally:
                _run(rag.finalize_storages())

            self.assertEqual(merged["target_relation_id"], "relation::two")
            self.assertIsNone(source_relation)
            self.assertIn("manual:one", target_relation["provenance"])
            self.assertIn("manual:two", target_relation["provenance"])
            self.assertEqual(aggregate["relation_vectors"], 1)
