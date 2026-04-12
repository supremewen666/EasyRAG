# Retrieval Overview

This chapter explains what happens after the index already exists. In EasyRAG, retrieval turns a user question into grounded, inspectable outputs such as citations, surfaced entities, relation hits, and diagnostics metadata.

## The learning question

How does one question get transformed into ranked evidence instead of being sent straight to a single vector search call?

## The retrieval flow

```text
user question
  -> normalization / rewrite / MQE
  -> mode-specific retrieval
  -> fusion and rerank
  -> hydration
  -> citations, entities, relations, metadata
```

That sequence is the reason retrieval is more than "run search and sort by score."

## Query preprocessing comes first

EasyRAG can normalize, rewrite, and expand the incoming query before retrieval runs. The output of that stage is visible through metadata fields such as:

- `normalized_query`
- `rewritten_query`
- `expanded_queries`
- `retrieval_queries`

That visibility matters. It lets you inspect what the system actually searched for instead of guessing from the final citation list alone.

## Retrieval modes search different views of the workspace

EasyRAG exposes five built-in retrieval modes:

- `naive`
- `local`
- `global`
- `hybrid`
- `mix`

The exact implementation details differ, but the teaching idea is stable: different modes emphasize different indexed views of the same workspace. Some lean harder on chunk-level retrieval. Others give summaries or graph neighborhoods more influence.

## Fusion, rerank, and hydration happen after recall

Later retrieval stages refine what earlier stages surfaced:

- fusion merges several ranked candidate lists
- rerank reorders the already recalled candidates
- hydration turns ranked IDs into citation-ready records with text, title, path, and metadata

This is why retrieval quality is not one number and not one function call. Each stage can rescue or degrade the final grounded output.

## `QueryResult` is the handoff object

The final retrieval package is `QueryResult`. For learning purposes, the most useful fields are:

- `citations`
- `entities`
- `relations`
- `metadata`

That is the evidence bundle that later generation and evaluation stages build on.

## Notebook handoff

The most direct notebook companions to this chapter are:

- [04_01_query_modes.ipynb](../notebooks/04_retrieval/04_01_query_modes.ipynb), which compares the five retrieval modes on one small corpus
- [04_02_knowledge_graph.ipynb](../notebooks/04_retrieval/04_02_knowledge_graph.ipynb), which shows graph-aware retrieval after KG extraction
- [04_03_query_preprocessing_lab.ipynb](../notebooks/04_retrieval/04_03_query_preprocessing_lab.ipynb), [04_04_vector_retrieval_lab.ipynb](../notebooks/04_retrieval/04_04_vector_retrieval_lab.ipynb), [04_05_hybrid_fusion_lab.ipynb](../notebooks/04_retrieval/04_05_hybrid_fusion_lab.ipynb), and [04_06_rerank_lab.ipynb](../notebooks/04_retrieval/04_06_rerank_lab.ipynb) for stage-specific comparisons

## Where to go next

- Continue with [05-generation-overview.md](05-generation-overview.md) to see how grounded retrieval outputs become answer-ready evidence.
- Jump to [06-evaluation-overview.md](06-evaluation-overview.md) if you want to measure retrieval quality directly before adding answer synthesis.
- Read [engineering/22-retrieval-pipeline.md](engineering/22-retrieval-pipeline.md) for the code-oriented version of the same flow.
