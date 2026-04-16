"""Tests for the repository-backed test_rag.py QA demo."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_rag


class TestRAGScriptTestCase(unittest.TestCase):
    """Verify the root-level QA demo stays runnable."""

    def _create_demo_repo(self, root: Path) -> Path:
        docs_dir = root / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "architecture.md").write_text(
            "# Architecture\n"
            "EasyRAG organizes retrieval around hybrid chunk evidence and graph-aware signals.\n"
            "Hybrid retrieval keeps citations inspectable.\n",
            encoding="utf-8",
        )
        (docs_dir / "retrieval.md").write_text(
            "# Retrieval\n"
            "EasyRAG supports naive, local, global, hybrid, and mix retrieval modes.\n"
            "Query rewrite and rerank steps improve evidence selection.\n",
            encoding="utf-8",
        )
        return docs_dir

    def test_main_builds_repo_index_then_prints_retrieval_and_answer_sections(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            docs_dir = self._create_demo_repo(repo_root)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                test_rag.main(
                    [
                        "--repo-root",
                        str(repo_root),
                        "--working-dir",
                        str(repo_root / ".easyrag" / "rag_storage"),
                        "--workspace",
                        "qa-demo",
                    ]
                )

        output = stdout.getvalue()
        self.assertIn("=== EasyRAG QA Demo ===", output)
        self.assertIn("Build:", output)
        self.assertIn("Retrieval:", output)
        self.assertIn("Answer:", output)
        self.assertIn("workspace=qa-demo", output)
        self.assertIn(
            f"location={(docs_dir / 'retrieval.md').resolve()}",
            output,
        )
        self.assertIn("query=How does EasyRAG handle retrieval?", output)
        self.assertIn("answer_model_used=True", output)
        self.assertIn("fallback_used=False", output)
        self.assertNotIn("vector_backend=fallback_token", output)
        self.assertNotIn("sample_data", output)

    def test_main_supports_naive_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            self._create_demo_repo(repo_root)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                test_rag.main(
                    [
                        "--repo-root",
                        str(repo_root),
                        "--workspace",
                        "qa-naive",
                        "--mode",
                        "naive",
                        "--query",
                        "What retrieval modes does EasyRAG support?",
                    ]
                )

        output = stdout.getvalue()
        self.assertIn("mode=naive", output)
        self.assertIn("query=What retrieval modes does EasyRAG support?", output)
        self.assertIn("Citations:", output)
        self.assertIn("Selected citations:", output)
        self.assertIn("vector_backend=", output)


if __name__ == "__main__":
    unittest.main()
