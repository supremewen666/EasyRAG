# System Architecture Overview

This chapter is the late-stage map of EasyRAG. It comes after the loading, indexing, retrieval, generation, evaluation, and optimization overviews because it is easier to read once the stage boundaries already make sense.

## The learning question

When a source document becomes a grounded retrieval result, which modules own each transformation, and where do backend swaps change the implementation without changing the mental model?

## The system-level flow

```text
source files or raw texts
  -> loading and canonical Documents
  -> indexing artifacts and workspace state
  -> retrieval preprocessing and ranked evidence
  -> citations and diagnostics
  -> downstream answer generation
  -> evaluation and optimization loops
```

This page does not try to replace the stage overviews. It reconnects them.

## The main subsystems

### Orchestrator

The orchestrator lives in `easyrag/rag/orchestrator.py` and exposes the public `EasyRAG` lifecycle. It is the easiest place to answer questions such as:

- how does storage initialization happen?
- which helpers are public?
- what does `aquery()` return?

### Loading and indexing

The loading and indexing path spans:

- `easyrag/rag/indexing/loaders.py`
- `easyrag/rag/indexing/prepare.py`
- `easyrag/rag/indexing/chunking.py`
- `easyrag/rag/indexing/pipeline.py`
- `easyrag/rag/indexing/maintenance.py`

Those modules own the transition from raw source material to persistent workspace artifacts.

### Retrieval

The retrieval path spans:

- `easyrag/rag/retrieval/preprocess.py`
- `easyrag/rag/retrieval/query_modes.py`
- `easyrag/rag/retrieval/fusion.py`
- `easyrag/rag/retrieval/hydration.py`
- `easyrag/rag/retrieval/pipeline.py`

Those modules own the transition from user question to `QueryResult`.

### Knowledge and graph curation

Graph-aware behavior lives beside the retrieval core rather than replacing it:

- `easyrag/rag/knowledge/extraction.py`
- `easyrag/rag/knowledge/sync.py`
- `easyrag/rag/knowledge/curation.py`

The useful architectural idea is that graph signals are another retrieval aid, not a separate product.

### Storage

The storage layer hides the difference between local-first persistence and production-style bundles. The rest of the pipeline can keep thinking in documents, chunks, vectors, and graph records even when the backing implementation changes.

That stability is one of the main teaching goals of the repository.

## The stable teaching interfaces

If you keep only a few names in your head, keep these:

- `EasyRAG`
- `QueryParam`
- `ChunkingConfig`
- `QueryResult`

Those interfaces connect the docs, notebooks, and real code better than any directory tree diagram would.

## Notebook handoff

The architecture-side notebook companion is:

- [08_01_storage_backend_lab.ipynb](../notebooks/08_system_architecture/08_01_storage_backend_lab.ipynb)

For code-oriented reading, the best companions are:

- [engineering/20-code-map.md](engineering/20-code-map.md)
- [engineering/24-local-vs-production-backends.md](engineering/24-local-vs-production-backends.md)

## Where to go next

- Return to [00-overview.md](00-overview.md) if you want the stage-by-stage path again.
- Use the engineering pages when you want implementation detail instead of teaching-level structure.
