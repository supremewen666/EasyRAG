# Retrieval Overview

This chapter explains what happens after the index already exists. In EasyRAG, retrieval turns a user question into grounded, inspectable outputs such as citations, surfaced entities, and diagnostics metadata.

## The learning question

How does one question get transformed into ranked evidence instead of being sent straight to one search call and one score sort?

## The retrieval flow

```text
user question
  -> query normalization
  -> rewrite or multi-query expansion
  -> retrieval over one or more indexed views
  -> fusion, rerank, and thresholding
  -> hydration
  -> citations and retrieval metadata
```

That sequence is the reason retrieval is more than "run search and sort by score."

## What you will learn

- why preprocessing belongs to retrieval, not only to loading
- how recall, fusion, rerank, and hydration are different stages
- which industrial retrieval patterns matter in practice
- how `QueryResult` becomes the handoff object for generation and evaluation

## Key concepts

### Query normalization

Normalization is the first retrieval habit, and it deserves its own slot in the stage.

Typical query-side normalization includes:

- whitespace cleanup
- punctuation cleanup
- term and abbreviation normalization
- number, unit, and date normalization
- light typo handling when the corpus and domain justify it

The point is not to rewrite every question aggressively. The point is to make the actual retrieval query easier to match against indexed text.

### Rewrite and multi-query expansion

Some questions need one search form. Others benefit from several:

- a normalized base query
- a rewritten query that states the intent more clearly
- a small set of expanded retrieval queries that widen coverage

EasyRAG exposes these intermediate forms through metadata so you can inspect what the system actually searched for.

### Recall, fusion, rerank, and hydration are separate

Retrieval quality is not one number and not one function call:

- recall finds candidate evidence
- fusion combines several candidate lists
- rerank improves ordering after recall
- thresholding decides how weak evidence should be handled
- hydration turns anonymous IDs into citation-ready records

That stage separation is what makes later debugging possible.

## Industrial retrieval patterns

Industrial retrieval systems usually combine several techniques rather than betting on one mode:

- hybrid retrieval across lexical and dense signals
- metadata filtering before or beside recall
- field-aware retrieval across title, summary, and body
- rerank after recall instead of replacing recall
- thresholding and adaptive top-k
- fallback paths when one retrieval mode returns weak coverage
- cached retrieval for repeated questions

The important habit is to think in combinations: preprocess, recall, fuse, rerank, hydrate, and fall back when needed.

## `QueryResult` is the handoff object

The final retrieval package is `QueryResult`. For learning purposes, the most useful fields are:

- `citations`
- `entities`
- `relations`
- `metadata`

That is the evidence bundle that later generation and evaluation stages build on.

## Notebook handoff

The retrieval notebooks now follow the retrieval pipeline more directly:

- [04_01_query_normalization_and_preprocessing.ipynb](../notebooks/04_retrieval/04_01_query_normalization_and_preprocessing.ipynb)
- [04_02_query_rewrite_and_multi_query.ipynb](../notebooks/04_retrieval/04_02_query_rewrite_and_multi_query.ipynb)
- [04_03_naive_retrieval_basics.ipynb](../notebooks/04_retrieval/04_03_naive_retrieval_basics.ipynb)
- [04_04_hybrid_metadata_filter_and_modes.ipynb](../notebooks/04_retrieval/04_04_hybrid_metadata_filter_and_modes.ipynb)
- [04_05_fusion_rerank_and_topk.ipynb](../notebooks/04_retrieval/04_05_fusion_rerank_and_topk.ipynb)
- [04_06_hydration_and_citations.ipynb](../notebooks/04_retrieval/04_06_hydration_and_citations.ipynb)
- [04_07_retrieval_failure_cases_and_debugging.ipynb](../notebooks/04_retrieval/04_07_retrieval_failure_cases_and_debugging.ipynb)

Some of these are full comparisons today and some are scaffolds, but together they cover query preparation, recall, ranking, and evidence packaging in order.

## Where to go next

- Continue with [05-generation-overview.md](05-generation-overview.md) to see how grounded retrieval outputs become answer-ready evidence.
- Jump to [06-evaluation-overview.md](06-evaluation-overview.md) if you want to measure retrieval quality before you add more answer logic.
- Read [engineering/22-retrieval-pipeline.md](engineering/22-retrieval-pipeline.md) for the code-oriented version of the same flow.
