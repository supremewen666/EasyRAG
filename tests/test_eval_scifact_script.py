"""Tests for the SciFact retrieval evaluation script."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path("/Users/supremewen/EasyRAG/scripts/eval_scifact.py")


def _load_script_module():
    os.environ["EASYRAG_SKIP_VENV_REEXEC"] = "1"
    spec = importlib.util.spec_from_file_location("eval_scifact_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load eval_scifact.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvalSciFactScriptTestCase(unittest.TestCase):
    """Verify the repository-local SciFact eval script stays runnable."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_script_module()

    def _write_benchmark_root(self, root: Path) -> tuple[Path, Path]:
        repo_root = root / "sample_data"
        eval_root = repo_root / "scifact"
        docs_root = eval_root / "docs"
        docs_root.mkdir(parents=True)
        (docs_root / "101.md").write_text(
            "# Study 101\nBiomaterials can be inductive.\n",
            encoding="utf-8",
        )
        (docs_root / "202.md").write_text(
            "# Study 202\nZero-dimensional materials can influence scaffolds.\n",
            encoding="utf-8",
        )
        (eval_root / "queries.json").write_text(
            json.dumps(
                [
                    {
                        "_id": "q1",
                        "text": "0-dimensional biomaterials lack inductive properties.",
                    }
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (eval_root / "qrels.json").write_text(
            json.dumps(
                [
                    {"query-id": "q1", "corpus-id": "101", "score": 1},
                    {"query-id": "q1", "corpus-id": "202", "score": 1},
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return repo_root, eval_root

    def test_load_eval_cases_groups_qrels_and_uses_repo_relative_doc_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root, eval_root = self._write_benchmark_root(Path(tmp_dir))
            cases, source_name = self.module.load_eval_cases(
                eval_root,
                repo_root,
                split="train",
                limit=None,
            )

        self.assertEqual(source_name, "qrels.json")
        self.assertEqual(len(cases), 1)
        self.assertEqual(
            cases[0].expected_document_ids,
            (
                "doc::scifact-docs-101-md",
                "doc::scifact-docs-202-md",
            ),
        )
        self.assertEqual(cases[0].metadata["corpus_ids"], ["101", "202"])

    def test_summarize_alignment_flags_missing_expected_document_ids(self) -> None:
        alignment = self.module.summarize_alignment(
            [
                self.module.EvalCase(
                    question="question",
                    expected_document_ids=("doc::scifact-docs-101-md",),
                )
            ],
            {"doc::other-root-docs-101-md"},
        )

        self.assertFalse(alignment["has_overlap"])
        self.assertEqual(alignment["matched_expected_documents"], 0)
        self.assertEqual(alignment["missing_expected_documents"], 1)
        self.assertEqual(
            alignment["missing_doc_ids_preview"],
            ["doc::scifact-docs-101-md"],
        )

    def test_main_prints_metrics_and_case_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root, eval_root = self._write_benchmark_root(Path(tmp_dir))
            stdout = io.StringIO()
            default_working_dir = Path(tmp_dir) / "storage"

            class _FakeDocStatusStorage:
                async def list_statuses(self) -> list[dict[str, str]]:
                    return [{"document_id": "doc::scifact-docs-101-md"}]

            class _FakeRAG:
                def __init__(self, *, working_dir: Path, workspace: str) -> None:
                    self.working_dir = working_dir
                    self.workspace = workspace
                    self.doc_status_storage = _FakeDocStatusStorage()

                async def initialize_storages(self) -> None:
                    return None

                async def finalize_storages(self) -> None:
                    return None

                async def get_stats(self) -> dict[str, object]:
                    return {
                        "documents": 1,
                        "chunks": 2,
                        "chunk_vectors": 2,
                        "summary_vectors": 1,
                        "vector_backend": "dense_embedding",
                    }

            async def _fake_evaluate_retrieval(
                rag: object,
                cases: list[object],
                query_param: object,
            ) -> dict[str, object]:
                del rag, query_param
                return {
                    "cases": [
                        {
                            "question": cases[0].question,
                            "expected_document_ids": list(cases[0].expected_document_ids),
                            "retrieved_document_ids": ["doc::scifact-docs-101-md"],
                            "metrics": {
                                "hit_rate": 1.0,
                                "recall_at_k": 0.5,
                                "precision_at_k": 1.0,
                                "mrr_at_k": 1.0,
                            },
                        }
                    ],
                    "metrics": {
                        "hit_rate": 1.0,
                        "recall_at_k": 0.5,
                        "precision_at_k": 1.0,
                        "mrr_at_k": 1.0,
                    },
                    "metadata": {"case_count": len(cases), "mode": "naive"},
                }

            with (
                patch.object(self.module, "EasyRAG", _FakeRAG),
                patch.object(
                    self.module,
                    "get_rag_working_dir",
                    lambda: default_working_dir,
                ),
                patch.object(
                    self.module,
                    "evaluate_retrieval",
                    _fake_evaluate_retrieval,
                ),
                contextlib.redirect_stdout(stdout),
            ):
                self.module.main(
                    [
                        "--eval-root",
                        str(eval_root),
                        "--repo-root",
                        str(repo_root),
                        "--workspace",
                        "scifact-eval",
                        "--preview-cases",
                        "1",
                    ]
                )

        output = stdout.getvalue()
        self.assertIn("=== EasyRAG SciFact Eval ===", output)
        self.assertIn("case_source=qrels.json", output)
        self.assertIn("vector_backend=dense_embedding", output)
        self.assertIn("matched_expected_documents=1", output)
        self.assertIn('"hit_rate": 1.0', output)
        self.assertIn("[1] question=0-dimensional biomaterials lack inductive properties.", output)


if __name__ == "__main__":
    unittest.main()
