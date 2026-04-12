# System Architecture

This chapter is the system-level map for EasyRAG. The goal is not to re-explain every detail from the earlier chapters. The goal is to show how the major subsystems fit together so that later indexing, retrieval, and knowledge-graph notebooks feel like parts of one coherent pipeline.

The guiding question for this page is simple: when a source document becomes a grounded retrieval result, which modules are responsible for each transformation?

## What The System Is Optimizing For

EasyRAG is optimized for clarity before scale. It is intentionally small enough that a learner can trace the whole flow from document ingestion to grounded citations without going through a large framework.

That teaching-first design leads to a few architectural choices:

- the public API is compact and explicit
- indexing and retrieval are separate phases
- local-first storage is the default mental model
- knowledge graph signals are visible, but not forced into every explanation
- most important transformations have a named module boundary

This means the architecture is not trying to hide complexity. It is trying to place it where you can study it.

## One End-to-End Flow

At a high level, one EasyRAG workflow looks like this:

```text
source files or raw texts
  -> Document objects
  -> chunking and summaries
  -> storage records, vectors, and graph state
  -> query preprocessing
  -> retrieval modes and fusion
  -> hydrated records
  -> grounded citations + metadata
```

The user-facing loop usually looks like:

1. create an `EasyRAG` instance
2. initialize storages
3. insert or rebuild indexed knowledge
4. query with `QueryParam`
5. inspect `QueryResult`
6. finalize storages

That is the whole system in miniature. The rest of the repository exists to make those six steps explicit and inspectable.

## The Main Subsystems

### Orchestrator

The orchestrator lives in `easyrag/rag/orchestrator.py` and exposes the high-level `EasyRAG` API. It coordinates ingestion, retrieval, graph operations, and storage lifecycle.

This is the main place where a learner can answer questions such as:

- how does initialization happen?
- which helpers are considered public entry points?
- what does `aquery()` return?
- where do manual graph operations fit?

If you only read one implementation file to understand the top-level flow, start there.

### Indexing

The indexing subsystem turns raw source material into searchable knowledge artifacts.

Its core responsibilities include:

- discovering or preparing documents
- choosing chunking strategies
- creating chunk and summary records
- writing vectors and graph artifacts
- maintaining a workspace on disk

The most important modules are:

- `easyrag/rag/indexing/loaders.py`
- `easyrag/rag/indexing/prepare.py`
- `easyrag/rag/indexing/chunking.py`
- `easyrag/rag/indexing/pipeline.py`
- `easyrag/rag/indexing/maintenance.py`

This is the subsystem you should have in mind when reading [03-indexing-overview.md](03-indexing-overview.md) or running [fundamentals/01_build_index.ipynb](../notebooks/fundamentals/01_build_index.ipynb).

### Retrieval

The retrieval subsystem turns one question into a set of grounded results.

Its responsibilities include:

- query normalization
- optional rewrite and MQE expansion
- executing one or more retrieval modes
- fusing and trimming ranked records
- hydrating records into citation-ready documents
- packaging everything into `QueryResult`

The most important modules are:

- `easyrag/rag/retrieval/preprocess.py`
- `easyrag/rag/retrieval/query_modes.py`
- `easyrag/rag/retrieval/fusion.py`
- `easyrag/rag/retrieval/hydration.py`
- `easyrag/rag/retrieval/pipeline.py`

This subsystem is the conceptual bridge between [04-retrieval-overview.md](04-retrieval-overview.md) and [fundamentals/02_query_modes.ipynb](../notebooks/fundamentals/02_query_modes.ipynb).

### Knowledge

EasyRAG uses a lightweight knowledge layer rather than a separate knowledge platform. During ingestion, entities and relations can be extracted from content and synchronized into graph-aware retrieval state.

That layer matters because it lets retrieval reason over more than chunk similarity alone. Local and global retrieval paths can use entities, relations, and neighborhoods to widen or re-center the evidence search.

The most important modules are:

- `easyrag/rag/knowledge/extraction.py`
- `easyrag/rag/knowledge/sync.py`
- `easyrag/rag/knowledge/curation.py`

For learners, the main idea is not "EasyRAG is a graph database." The main idea is "graph signals are another retrieval aid that can sit beside chunks and summaries."

### Storage

The storage subsystem hides the difference between local-first persistence and production-oriented bundles.

At the architectural level, this means the rest of the pipeline can think in terms of documents, chunks, vectors, and graph records without caring whether the backing implementation is JSON + local vector state or PostgreSQL + Qdrant.

The important abstraction boundary is:

- the mental model stays stable
- the storage implementation can vary

This is why local-first and production-style backends belong under one architecture picture rather than two separate products.

## Stable Teaching Interfaces

If you are learning the system, there are four interfaces worth keeping in your head at all times:

- `EasyRAG`: the orchestrator API
- `QueryParam`: the query-time control surface
- `ChunkingConfig`: the indexing-time chunking control surface
- `QueryResult.metadata`: the easiest window into what retrieval actually did

Those interfaces are stable teaching anchors because they connect directly to both docs and notebooks.

For example:

- `EasyRAG.load_repo_documents()` shows how repository content enters the system
- `ChunkingConfig` explains why chunk boundaries change
- `QueryParam(mode="hybrid")` changes how retrieval is assembled
- `QueryResult.metadata` tells you which query variants and chunk strategies were involved

## How The Data Flow Maps To Code

The easiest way to read the architecture is to follow the data:

1. source material becomes `Document` objects
   via `load_repo_documents()` or `prepare_documents_for_insert()`
2. documents become chunks, summaries, vectors, and graph records
   via the indexing pipeline
3. a user query becomes normalized, rewritten, and expanded search inputs
   via query preprocessing
4. retrieval modes search different views of the indexed workspace
   via `naive`, `local`, `global`, `hybrid`, and `mix`
5. ranked records become hydrated documents and citations
   via the hydration helpers
6. the final package becomes a `QueryResult`
   with citations, entities, relations, and diagnostics metadata

That is the architecture in operational form.

## Local-First And Production-Style Backends

EasyRAG teaches a local-first architecture because that is the easiest environment for understanding the moving parts. In local mode, learners can inspect files on disk and see workspace contents directly.

Production-style backends change persistence details, but they do not change the main pipeline:

- documents are still ingested
- chunks and summaries are still built
- vectors are still searched
- graph signals can still enrich retrieval
- `QueryResult` still carries grounded outputs

This is an important architectural promise: backend swaps should not require a new mental model.

## What The System Does Not Claim

To keep the architecture honest, it helps to name what this repository is not trying to be.

EasyRAG is not presented here as:

- a complete chat product
- a frontend framework
- a hosted retrieval platform
- a general-purpose agent runtime

Most importantly, `EasyRAG.aquery()` returns a grounded retrieval result, not a final prose answer generator. That boundary is intentional and should stay visible throughout the teaching material.

## Where To Go Next

Use this page as a map, then dive into the phase you want to understand next:

- [03-indexing-overview.md](03-indexing-overview.md) for how raw source material becomes indexed knowledge
- [04-retrieval-overview.md](04-retrieval-overview.md) for how one question becomes grounded results
- [fundamentals/01_build_index.ipynb](../notebooks/fundamentals/01_build_index.ipynb) for a runnable indexing walkthrough
- [fundamentals/02_query_modes.ipynb](../notebooks/fundamentals/02_query_modes.ipynb) for mode-by-mode retrieval comparison
- [fundamentals/04_knowledge_graph.ipynb](../notebooks/fundamentals/04_knowledge_graph.ipynb) for automatic graph-assisted retrieval on a small corpus

If `01-rag-basics.md` explained the objects, this chapter should explain the boundaries between the subsystems that create and use those objects.
