"""Tests for generation, evaluation, filtering, and document-quality flows."""

from __future__ import annotations

import asyncio
import tempfile
import unittest

from easyrag.rag import AnswerParam, EasyRAG, EvalCase, QueryParam
from easyrag.rag.evaluation import evaluate_answers, evaluate_retrieval

_KEYWORDS = [
    "architecture",
    "easyrag",
    "embedding",
    "grounded",
    "retrieval",
    "query",
    "rewrite",
    "storage",
]


def _run(awaitable: object) -> object:
    return asyncio.run(awaitable)


def _stub_embedding(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for text in texts:
        lowered = text.lower()
        vector = [float(lowered.count(keyword)) for keyword in _KEYWORDS]
        vector.append(float(len(lowered.split())))
        vectors.append(vector)
    return vectors


def _stub_query_model(prompt: str, *, task: str, count: int = 1) -> str | list[str]:
    cleaned = prompt.split(":", 1)[-1].strip()
    if task == "rewrite":
        return f"{cleaned} grounded retrieval"
    if task == "mqe":
        return [f"{cleaned} variant {index}" for index in range(1, count + 1)]
    raise ValueError(task)


class GenerationPipelineTestCase(unittest.TestCase):
    def test_aanswer_uses_deterministic_fallback_and_budgets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="generation",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        [
                            "# Retrieval\nEasyRAG uses grounded retrieval and query rewrite to keep answers traceable.\n",
                            "# Storage\nRetrieved evidence is packed before answer synthesis and storage review.\n",
                        ],
                        ids=["doc::retrieval", "doc::storage"],
                        file_paths=["docs/retrieval.md", "docs/storage.md"],
                    )
                )
                answer = _run(
                    rag.aanswer(
                        "How does EasyRAG keep answers grounded?",
                        QueryParam(
                            mode="naive",
                            rewrite_enabled=False,
                            mqe_enabled=False,
                            chunk_top_k=3,
                        ),
                        AnswerParam(max_citations=2, max_context_chars=140),
                    )
                )
            finally:
                _run(rag.finalize_storages())

        self.assertTrue(answer.answer)
        self.assertLessEqual(len(answer.selected_citations), 2)
        self.assertIn("[1]", answer.answer)
        self.assertTrue(answer.context_block)
        self.assertTrue(answer.metadata["fallback_used"])
        self.assertEqual(
            answer.metadata["selected_citation_count"], len(answer.selected_citations)
        )

    def test_aanswer_abstains_when_no_evidence_is_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="abstain",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        "# Retrieval\nEasyRAG answers retrieval questions.\n",
                        ids=["doc::retrieval"],
                        file_paths=["docs/retrieval.md"],
                    )
                )
                answer = _run(
                    rag.aanswer(
                        "What is the company holiday calendar?",
                        QueryParam(
                            mode="naive", rewrite_enabled=False, mqe_enabled=False
                        ),
                        AnswerParam(),
                    )
                )
            finally:
                _run(rag.finalize_storages())

        self.assertIn("cannot answer", answer.answer.lower())
        self.assertTrue(answer.metadata["abstained"])
        self.assertTrue(answer.metadata["insufficient_evidence"])

    def test_explicit_answer_model_func_is_used(self) -> None:
        def _answer_model(prompt: str, **_: object) -> str:
            self.assertIn("Retrieved evidence:", prompt)
            return "Structured grounded answer [1]"

        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="generation-model",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
                answer_model_func=_answer_model,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        "# Retrieval\nEasyRAG uses grounded retrieval and rewrite.\n",
                        ids=["doc::retrieval"],
                        file_paths=["docs/retrieval.md"],
                    )
                )
                answer = _run(
                    rag.aanswer(
                        "How does EasyRAG use rewrite?",
                        QueryParam(
                            mode="naive", rewrite_enabled=False, mqe_enabled=False
                        ),
                        AnswerParam(),
                    )
                )
            finally:
                _run(rag.finalize_storages())

        self.assertEqual(answer.answer, "Structured grounded answer [1]")
        self.assertTrue(answer.metadata["answer_model_used"])
        self.assertFalse(answer.metadata["fallback_used"])


class RetrievalFilterAndQualityTestCase(unittest.TestCase):
    def test_query_filters_and_observability_metadata_are_exposed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="filters",
                query_model_func=_stub_query_model,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        [
                            "# Architecture\nretrieval retrieval retrieval keeps architecture grounded.\n",
                            "# Guide\nretrieval keeps guides readable.\n",
                        ],
                        ids=["doc::architecture", "doc::guide"],
                        file_paths=["docs/architecture.md", "docs/guide.md"],
                    )
                )
                min_score_result = _run(
                    rag.aquery(
                        "retrieval retrieval",
                        QueryParam(
                            mode="naive",
                            rewrite_enabled=False,
                            mqe_enabled=False,
                            min_score=130.0,
                        ),
                    )
                )
                metadata_result = _run(
                    rag.aquery(
                        "retrieval",
                        QueryParam(
                            mode="naive",
                            rewrite_enabled=False,
                            mqe_enabled=False,
                            metadata_filters={"doc_id": "doc::guide"},
                        ),
                    )
                )
            finally:
                _run(rag.finalize_storages())

        self.assertEqual(
            [citation["location"] for citation in min_score_result.citations],
            ["docs/architecture.md"],
        )
        self.assertEqual(
            [citation["location"] for citation in metadata_result.citations],
            ["docs/guide.md"],
        )
        self.assertIn("candidate_counts", metadata_result.metadata)
        self.assertIn("stage_timings_ms", metadata_result.metadata)
        self.assertIn("fallback_used", metadata_result.metadata)
        self.assertEqual(
            metadata_result.metadata["filters_applied"]["metadata_filters"],
            {"doc_id": "doc::guide"},
        )

    def test_quality_flags_and_skipped_documents_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="quality",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
            )
            _run(rag.initialize_storages())
            try:
                stats = _run(
                    rag.ainsert(
                        ["\x00 \n\n", "tiny doc", "tiny doc"],
                        ids=["doc::empty", "doc::one", "doc::two"],
                        file_paths=["docs/empty.md", "docs/one.md", "docs/two.md"],
                    )
                )
                first_status = _run(rag.doc_status_storage.get_status("doc::one"))
            finally:
                _run(rag.finalize_storages())

        self.assertEqual(stats["documents"], 2)
        self.assertEqual(stats["skipped_documents"], 1)
        self.assertEqual(stats["quality_issue_counts"]["empty_after_normalization"], 1)
        self.assertEqual(stats["quality_issue_counts"]["duplicate_content_in_batch"], 2)
        self.assertIn("very_short", first_status["metadata"]["quality_flags"])
        self.assertIn(
            "duplicate_content_in_batch", first_status["metadata"]["quality_flags"]
        )


class EvaluationRunnerTestCase(unittest.TestCase):
    def test_evaluate_retrieval_reports_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="eval-retrieval",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        "# Architecture\nEasyRAG uses query rewrite for grounded retrieval.\n",
                        ids=["doc::architecture"],
                        file_paths=["docs/architecture.md"],
                    )
                )
                report = _run(
                    evaluate_retrieval(
                        rag,
                        [
                            EvalCase(
                                question="What uses query rewrite?",
                                expected_document_ids=("doc::architecture",),
                            )
                        ],
                        QueryParam(
                            mode="naive", rewrite_enabled=False, mqe_enabled=False
                        ),
                    )
                )
            finally:
                _run(rag.finalize_storages())

        self.assertEqual(report["metrics"]["hit_rate"], 1.0)
        self.assertEqual(report["metrics"]["recall_at_k"], 1.0)
        self.assertEqual(report["metrics"]["precision_at_k"], 1.0)
        self.assertEqual(report["metrics"]["mrr_at_k"], 1.0)

    def test_evaluate_answers_reports_grounding_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = EasyRAG(
                working_dir=tmp_dir,
                workspace="eval-answer",
                embedding_func=_stub_embedding,
                query_model_func=_stub_query_model,
            )
            _run(rag.initialize_storages())
            try:
                _run(
                    rag.ainsert(
                        "# Retrieval\nEasyRAG uses grounded retrieval and query rewrite.\n",
                        ids=["doc::retrieval"],
                        file_paths=["docs/retrieval.md"],
                    )
                )
                report = _run(
                    evaluate_answers(
                        rag,
                        [
                            EvalCase(
                                question="How does EasyRAG use query rewrite?",
                                expected_to_abstain=False,
                            ),
                            EvalCase(
                                question="When is the company retreat?",
                                expected_to_abstain=True,
                            ),
                        ],
                        QueryParam(
                            mode="naive", rewrite_enabled=False, mqe_enabled=False
                        ),
                        AnswerParam(),
                    )
                )
            finally:
                _run(rag.finalize_storages())

        self.assertGreaterEqual(report["metrics"]["citation_presence"], 0.5)
        self.assertGreaterEqual(report["metrics"]["support_ratio"], 0.5)
        self.assertEqual(report["metrics"]["abstain_accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
