"""Compatibility tests for graph storage payload loading."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from easyrag.rag.storage.local import NetworkXGraphStorage


def _run(awaitable: object) -> object:
    """Run one async helper inside unittest."""

    return asyncio.run(awaitable)


class _FakeGraph:
    """Small graph stub for serialization compatibility tests."""

    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, object]] = {}
        self._edges: dict[tuple[str, str], dict[str, object]] = {}
        self.nodes = _FakeNodeView(self)

    def add_node(self, node_id: str, **data: object) -> None:
        self._nodes[str(node_id)] = dict(data)

    def add_edge(self, u_of_edge: str, v_of_edge: str, **data: object) -> None:
        normalized_source = str(u_of_edge)
        normalized_target = str(v_of_edge)
        self._nodes.setdefault(normalized_source, {"id": normalized_source})
        self._nodes.setdefault(normalized_target, {"id": normalized_target})
        self._edges[tuple(sorted((normalized_source, normalized_target)))] = dict(data)

    def edges(self, data: bool = False) -> list[object]:
        if not data:
            return list(self._edges)
        return [
            (source, target, dict(edge))
            for (source, target), edge in self._edges.items()
        ]

    def has_edge(self, source: str, target: str) -> bool:
        return tuple(sorted((str(source), str(target)))) in self._edges

    def __contains__(self, node_id: object) -> bool:
        return str(node_id) in self._nodes

    def __getitem__(self, source: str) -> dict[str, dict[str, object]]:
        normalized_source = str(source)
        neighbors: dict[str, dict[str, object]] = {}
        for (left, right), edge in self._edges.items():
            if left == normalized_source:
                neighbors[right] = dict(edge)
            elif right == normalized_source:
                neighbors[left] = dict(edge)
        return neighbors


class _FakeNodeView:
    """Minimal callable/subscriptable node view."""

    def __init__(self, graph: _FakeGraph) -> None:
        self._graph = graph

    def __call__(self, data: bool = False) -> list[object]:
        if not data:
            return list(self._graph._nodes)
        return [
            (node_id, dict(node))
            for node_id, node in self._graph._nodes.items()
        ]

    def __getitem__(self, node_id: str) -> dict[str, object]:
        return dict(self._graph._nodes[str(node_id)])


class _FakeNetworkXModule:
    """Minimal networkx-compatible module shape for graph storage tests."""

    Graph = _FakeGraph


class GraphStorageCompatibilityTestCase(unittest.TestCase):
    """Verify graph payload compatibility across backend availability changes."""

    def test_legacy_dict_payload_loads_when_networkx_is_available(self) -> None:
        legacy_payload = {
            "nodes": {
                "entity::alpha": {
                    "id": "entity::alpha",
                    "kind": "entity",
                    "label": "Alpha",
                },
                "entity::beta": {
                    "id": "entity::beta",
                    "kind": "entity",
                    "label": "Beta",
                },
            },
            "edges": {
                "entity::alpha|entity::beta": {
                    "source": "entity::alpha",
                    "target": "entity::beta",
                    "kind": "semantic_relation",
                    "weight": 1.0,
                }
            },
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_dir = Path(tmp_dir) / "compat"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            (workspace_dir / "graph.json").write_text(
                json.dumps(legacy_payload), encoding="utf-8"
            )
            (workspace_dir / "graph_relations.json").write_text(
                json.dumps({}), encoding="utf-8"
            )

            with mock.patch("easyrag.rag.storage.local.nx", _FakeNetworkXModule()):
                storage = NetworkXGraphStorage(tmp_dir, "compat")
                _run(storage.initialize())
                try:
                    node_ids = sorted(node_id for node_id, _ in storage._iter_nodes())
                    edge_pairs = sorted(
                        (source, target)
                        for source, target, _ in storage._iter_edges()
                    )
                finally:
                    _run(storage.finalize())

        self.assertEqual(node_ids, ["entity::alpha", "entity::beta"])
        self.assertEqual(edge_pairs, [("entity::alpha", "entity::beta")])

    def test_node_link_payload_loads_without_networkx_and_rewrites_stable_format(self) -> None:
        node_link_payload = {
            "directed": False,
            "multigraph": False,
            "graph": {},
            "nodes": [
                {"id": "entity::alpha", "kind": "entity", "label": "Alpha"},
                {"id": "entity::beta", "kind": "entity", "label": "Beta"},
            ],
            "edges": [
                {
                    "source": "entity::alpha",
                    "target": "entity::beta",
                    "kind": "semantic_relation",
                    "weight": 1.0,
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_dir = Path(tmp_dir) / "compat"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            graph_path = workspace_dir / "graph.json"
            graph_path.write_text(json.dumps(node_link_payload), encoding="utf-8")
            (workspace_dir / "graph_relations.json").write_text(
                json.dumps({}), encoding="utf-8"
            )

            with mock.patch("easyrag.rag.storage.local.nx", None):
                storage = NetworkXGraphStorage(tmp_dir, "compat")
                _run(storage.initialize())
                try:
                    node_ids = sorted(node_id for node_id, _ in storage._iter_nodes())
                    edge_pairs = sorted(
                        (source, target)
                        for source, target, _ in storage._iter_edges()
                    )
                finally:
                    _run(storage.finalize())

            rewritten_payload = json.loads(graph_path.read_text(encoding="utf-8"))

        self.assertEqual(node_ids, ["entity::alpha", "entity::beta"])
        self.assertEqual(edge_pairs, [("entity::alpha", "entity::beta")])
        self.assertIsInstance(rewritten_payload["nodes"], dict)
        self.assertIsInstance(rewritten_payload["edges"], dict)

    def test_networkx_backend_writes_stable_graph_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch("easyrag.rag.storage.local.nx", _FakeNetworkXModule()):
                storage = NetworkXGraphStorage(tmp_dir, "compat")
                _run(storage.initialize())
                try:
                    _run(
                        storage.upsert_nodes(
                            [
                                {
                                    "id": "entity::alpha",
                                    "kind": "entity",
                                    "label": "Alpha",
                                },
                                {
                                    "id": "entity::beta",
                                    "kind": "entity",
                                    "label": "Beta",
                                },
                            ]
                        )
                    )
                    _run(
                        storage.upsert_edges(
                            [
                                {
                                    "source": "entity::alpha",
                                    "target": "entity::beta",
                                    "kind": "semantic_relation",
                                    "weight": 1.0,
                                }
                            ]
                        )
                    )
                finally:
                    _run(storage.finalize())

            graph_path = Path(tmp_dir) / "compat" / "graph.json"
            payload = json.loads(graph_path.read_text(encoding="utf-8"))

        self.assertIsInstance(payload["nodes"], dict)
        self.assertIsInstance(payload["edges"], dict)
        self.assertIn("entity::alpha", payload["nodes"])
        self.assertIn("entity::alpha|entity::beta", payload["edges"])


if __name__ == "__main__":
    unittest.main()
