"""Evaluation runners for retrieval and grounded answering."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from easyrag.rag.evaluation.grounding import answer_abstained, answer_has_citations, sentence_support_ratio
from easyrag.rag.evaluation.metrics import hit_rate_at_k, mrr_at_k, precision_at_k, recall_at_k
from easyrag.rag.types import AnswerParam, EvalCase, QueryParam

if TYPE_CHECKING:
    from easyrag.rag.orchestrator import EasyRAG


def _match_relevance(
    *,
    document_id: str,
    snippet: str,
    expected_document_ids: tuple[str, ...],
    expected_snippets: tuple[str, ...],
) -> bool:
    if expected_document_ids and document_id in expected_document_ids:
        return True
    lowered_snippet = snippet.lower()
    return any(expected.lower() in lowered_snippet for expected in expected_snippets if expected.strip())


def _aggregate(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


async def evaluate_retrieval(
    rag: "EasyRAG",
    cases: list[EvalCase],
    query_param: QueryParam,
) -> dict[str, Any]:
    """Evaluate retrieval quality over a deterministic case set."""

    case_reports: list[dict[str, Any]] = []
    hit_rates: list[float] = []
    recalls: list[float] = []
    precisions: list[float] = []
    mrrs: list[float] = []

    for case in cases:
        result = await rag.aquery(case.question, query_param)
        relevances = [
            _match_relevance(
                document_id=str(chunk.metadata.get("doc_id", "")),
                snippet=str(citation.get("snippet", "")),
                expected_document_ids=case.expected_document_ids,
                expected_snippets=case.expected_snippets,
            )
            for chunk, citation in zip(result.chunks, result.citations, strict=False)
        ]
        expected_total = len(case.expected_document_ids or case.expected_snippets)
        hit_rate = hit_rate_at_k(relevances)
        recall = recall_at_k(relevances, expected_total=expected_total)
        precision = precision_at_k(relevances)
        mrr = mrr_at_k(relevances)
        hit_rates.append(hit_rate)
        recalls.append(recall)
        precisions.append(precision)
        mrrs.append(mrr)
        case_reports.append(
            {
                "question": case.question,
                "expected_document_ids": list(case.expected_document_ids),
                "expected_snippets": list(case.expected_snippets),
                "retrieved_document_ids": [str(chunk.metadata.get("doc_id", "")) for chunk in result.chunks],
                "retrieved_citations": list(result.citations),
                "metrics": {
                    "hit_rate": hit_rate,
                    "recall_at_k": recall,
                    "precision_at_k": precision,
                    "mrr_at_k": mrr,
                },
                "metadata": dict(case.metadata),
            }
        )

    return {
        "cases": case_reports,
        "metrics": {
            "hit_rate": _aggregate(hit_rates),
            "recall_at_k": _aggregate(recalls),
            "precision_at_k": _aggregate(precisions),
            "mrr_at_k": _aggregate(mrrs),
        },
        "metadata": {
            "case_count": len(cases),
            "mode": query_param.mode,
        },
    }


async def evaluate_answers(
    rag: "EasyRAG",
    cases: list[EvalCase],
    query_param: QueryParam,
    answer_param: AnswerParam,
) -> dict[str, Any]:
    """Evaluate grounded answering over a deterministic case set."""

    case_reports: list[dict[str, Any]] = []
    citation_presence_scores: list[float] = []
    support_ratios: list[float] = []
    abstain_scores: list[float] = []

    for case in cases:
        result = await rag.aanswer(case.question, query_param, answer_param)
        answer = result.answer
        has_citations = answer_has_citations(answer)
        support_ratio = sentence_support_ratio(answer, [citation.get("snippet", "") for citation in result.selected_citations])
        abstained = answer_abstained(answer)
        abstain_correct = abstained == case.expected_to_abstain
        citation_presence_scores.append(1.0 if has_citations else 0.0)
        support_ratios.append(support_ratio)
        abstain_scores.append(1.0 if abstain_correct else 0.0)
        case_reports.append(
            {
                "question": case.question,
                "reference_answer": case.reference_answer,
                "answer": answer,
                "selected_citations": list(result.selected_citations),
                "checks": {
                    "citation_presence": has_citations,
                    "support_ratio": support_ratio,
                    "abstained": abstained,
                    "abstain_correct": abstain_correct,
                },
                "metadata": dict(case.metadata),
            }
        )

    return {
        "cases": case_reports,
        "metrics": {
            "citation_presence": _aggregate(citation_presence_scores),
            "support_ratio": _aggregate(support_ratios),
            "abstain_accuracy": _aggregate(abstain_scores),
        },
        "metadata": {
            "case_count": len(cases),
            "mode": query_param.mode,
            "answer_style": answer_param.style,
        },
    }
