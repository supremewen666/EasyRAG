# RAG Basics

This chapter introduces the smallest set of ideas you need before loading documents, building an index, or reading the retrieval pipeline. The point is not to be comprehensive. The point is to make the rest of the repository legible.

## The learning question

What are the core objects and stage boundaries in EasyRAG, and why do they matter more than any single backend or provider choice?

## One mental model

EasyRAG is easiest to understand if you keep one compact flow in mind:

```text
source material
  -> Document
  -> chunk / summary / vector / graph artifacts
  -> retrieval query preparation
  -> ranked evidence
  -> citations and diagnostics
  -> downstream answer generation
```

If that flow is clear, the codebase stops feeling like a list of modules and starts feeling like one pipeline.

## The core objects

| Object | What it means | Where it appears | Why it matters |
| --- | --- | --- | --- |
| `Document` | A canonical source record with text and metadata | loading and preparation | It is the unit that enters the system. |
| Chunk | A smaller retrieval unit cut from a document | indexing | Retrieval usually works over chunks rather than whole files. |
| Summary | A higher-level document representation | indexing | It gives retrieval a broader view than raw chunks alone. |
| Vector record | A searchable representation of content | storage and retrieval | It powers dense retrieval or fallback search behavior. |
| Entity / relation | Lightweight graph signals derived from content | indexing and retrieval | They help graph-aware retrieval modes widen or re-center the search. |
| Citation | A grounded snippet with title, path, and location | retrieval output | It is the clearest proof that retrieval found real evidence. |
| `QueryResult` | The structured output of `EasyRAG.aquery()` | retrieval output | It bundles citations, entities, relations, and metadata for downstream use. |

## The three visible stages

### 1. Data loading

Before anything can be retrieved, source material has to become canonical `Document` objects with stable metadata. In EasyRAG, that can happen through repository loading, manual preparation, or document-specific loaders such as PDF page ingestion.

### 2. Indexing

Indexing turns those documents into searchable artifacts:

- chunks
- summaries
- vector payloads
- graph signals
- on-disk workspace state

This is where raw material becomes retrievable knowledge.

### 3. Retrieval

Retrieval takes a question and returns inspectable evidence:

- normalized or rewritten queries
- ranked records
- hydrated citations
- surfaced entities and relations
- metadata that explains what the system actually searched

Generation, evaluation, and optimization sit downstream of that retrieval result. They matter, but they are easier to reason about once the evidence boundary is clear.

## Why chunking and citations matter so much

Two beginner mistakes cause a lot of confusion later:

- treating chunking as a small implementation detail
- treating retrieval as "just scores" instead of grounded citations

Chunking decides what the system can retrieve cleanly. Citations decide whether a human can inspect what the system actually found. If either one is weak, the later answer layer will be harder to trust.

## How these basics map to code

The core concepts above map directly onto visible modules:

- `easyrag/rag/indexing/loaders.py`: source discovery and document loading
- `easyrag/rag/indexing/prepare.py`: canonical document preparation
- `easyrag/rag/indexing/chunking.py`: chunk strategy selection and execution
- `easyrag/rag/indexing/pipeline.py`: document-to-workspace ingestion
- `easyrag/rag/retrieval/preprocess.py`: query normalization, rewrite, and MQE
- `easyrag/rag/retrieval/pipeline.py`: retrieval execution and `QueryResult` assembly
- `easyrag/rag/orchestrator.py`: the public `EasyRAG` lifecycle

## Where to go next

- Read [02-data-loading-overview.md](02-data-loading-overview.md) for the input side of the system.
- Run [02_01_repo_loading_basics.ipynb](../notebooks/02_data_loading/02_01_repo_loading_basics.ipynb) to see canonical documents and chunk previews on a tiny corpus.
- Return to [00-overview.md](00-overview.md) if you want the full learning path again.
