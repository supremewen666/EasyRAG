"""Tests for storage backend bundle resolution."""

from __future__ import annotations

import unittest

from easyrag.rag.storage.bundles import resolve_storage_bundle


class StorageBackendResolutionTestCase(unittest.TestCase):
    """Verify backend bundle selection for local and production modes."""

    def test_local_backend_bundle_is_default(self) -> None:
        kv_cls, vector_cls, graph_cls, status_cls = resolve_storage_bundle("local")
        self.assertEqual(kv_cls.__name__, "JSONKVStorage")
        self.assertEqual(vector_cls.__name__, "EmbeddingVectorStorage")
        self.assertEqual(graph_cls.__name__, "NetworkXGraphStorage")
        self.assertEqual(status_cls.__name__, "JSONDocStatusStorage")

    def test_postgres_qdrant_backend_bundle_resolves(self) -> None:
        kv_cls, vector_cls, graph_cls, status_cls = resolve_storage_bundle(
            "postgres_qdrant"
        )
        self.assertEqual(kv_cls.__name__, "PostgresKVStorage")
        self.assertEqual(vector_cls.__name__, "QdrantVectorStorage")
        self.assertEqual(graph_cls.__name__, "PostgresGraphStorage")
        self.assertEqual(status_cls.__name__, "PostgresDocStatusStorage")
