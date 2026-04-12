# RAG Basics

This chapter introduces the smallest set of ideas you need before building an index or reading the retrieval pipeline. It follows the same teaching move used by from-scratch RAG tutorials: start with the vocabulary, define the two main phases, and only then move into implementation details.

In EasyRAG, the most important shift is this: we do not ask the model to answer from memory alone. We first turn a corpus into searchable artifacts, then use those artifacts to ground retrieval results.

## RAG In One Sentence

Retrieval-Augmented Generation (RAG) is a pattern where a system searches an external knowledge source for relevant evidence before producing an answer or a grounded result.

That sentence hides two different jobs:

- indexing: transform source material into searchable records
- retrieval: use those records to answer a question with evidence

If you keep those two jobs separate in your head, the rest of the repository becomes much easier to follow.

## The Core Objects

EasyRAG is easiest to understand if you know what gets created at each stage.

| Object | What it means | Where it comes from | Why it matters |
| --- | --- | --- | --- |
| Document | A raw source item such as a Markdown file, text file, or PDF page | `load_repo_documents()` or `prepare_documents_for_insert()` | It is the starting unit of knowledge ingestion. |
| Chunk | A smaller retrieval unit cut from a document | `chunk_documents()` | Retrieval usually works better over chunks than over full documents. |
| Summary | A compact document-level record | indexing pipeline | It gives retrieval a higher-level entry point than raw chunks alone. |
| Vector record | A searchable representation of a chunk, summary, entity, or relation | vector storage | It powers dense or fallback search over indexed content. |
| Entity / relation | Lightweight knowledge graph nodes and edges derived from content | KG extraction and sync | They let retrieval use more than plain chunk similarity. |
| Citation | A user-facing grounded reference containing title, location, and snippet | retrieval hydration | It is the clearest evidence that retrieval worked. |
| Query result | The structured output of `EasyRAG.aquery()` | retrieval pipeline | It bundles citations, entities, relations, and metadata for downstream use. |

One important boundary in this repository: EasyRAG currently teaches the grounded retrieval core. `aquery()` returns a structured retrieval result, not a final natural-language answer generator. That is intentional. It keeps the educational focus on retrieval mechanics.

## The Two Main Phases

### 1. Indexing

Indexing is the offline or preparation phase. The system takes source documents and turns them into artifacts that can be searched later.

In EasyRAG, indexing usually includes:

1. load documents from a repository or from in-memory text
2. choose a chunking strategy
3. create chunk and summary records
4. write storage entries for documents, chunks, and summaries
5. synchronize vector records
6. optionally extract lightweight entities and relations

The important insight is that retrieval speed and quality depend heavily on what happened during indexing. A poor index produces poor retrieval even if the query side is well designed.

### 2. Retrieval

Retrieval is the online phase. A user asks a question, and the system turns that question into a set of grounded results.

In EasyRAG, retrieval usually includes:

1. normalize the incoming question
2. optionally rewrite the query and generate MQE variants
3. search the indexed records through one or more retrieval modes
4. hydrate the retrieved records back into document-like objects
5. return citations, entities, relations, and diagnostics metadata

This means retrieval is not just "vector search." It is a pipeline that starts with query preprocessing and ends with structured evidence.

## Why Chunking Matters

Chunking is one of the most important ideas in practical RAG.

If chunks are too large:

- retrieval can return more irrelevant text than needed
- later stages have to process noisy context
- section-level intent gets blurred together

If chunks are too small:

- key context gets split apart
- retrieval may return fragments without enough meaning
- document structure becomes harder to preserve

EasyRAG keeps chunking explicit because different source types benefit from different strategies:

- structured chunking works well for Markdown and heading-based docs
- semantic chunking is better for long continuous text when embeddings are available
- sliding-window chunking is the fallback when structure or semantic boundaries are weak

This is why the indexing notebook focuses on chunk inspection before it focuses on querying.

## Why An Index Exists Before A Query

New readers often think a RAG system starts when the user asks a question. In practice, most of the work happened earlier.

Before retrieval can be useful, the system needs:

- known document IDs and metadata
- chunk boundaries
- storage records
- searchable vectors or fallback token structures
- optional graph signals

That is what "build the index" really means. It is not a cosmetic preprocessing step. It is the moment where raw source material becomes retrievable knowledge.

## What Retrieval Returns In EasyRAG

When you call `EasyRAG.aquery()`, you receive a `QueryResult` object. The most useful fields for a beginner are:

- `citations`: grounded snippets with source locations
- `entities`: entity labels surfaced during retrieval
- `relations`: lightweight relation hits
- `metadata`: diagnostics such as rewritten queries, expanded queries, chunk strategies, and vector backend

That metadata is especially valuable when you are learning. It lets you inspect what the system actually searched for instead of treating retrieval as a black box.

## A Minimal Mental Model

The whole system can be summarized like this:

```text
source files
  -> documents
  -> chunks + summaries
  -> storage + vectors + graph signals
  -> query preprocessing
  -> retrieval modes
  -> citations and diagnostics
```

If you can explain that flow in your own words, you already understand the foundation of this repository.

## How EasyRAG Maps These Basics To Code

The core concepts above map directly onto the repository:

- `easyrag/rag/indexing/loaders.py`: document discovery and PDF page loading
- `easyrag/rag/indexing/chunking.py`: chunk strategy selection and execution
- `easyrag/rag/indexing/pipeline.py`: document-to-storage ingestion
- `easyrag/rag/indexing/maintenance.py`: index rebuild helpers and compatibility snapshot writing
- `easyrag/rag/retrieval/preprocess.py`: query normalization, rewriting, and MQE
- `easyrag/rag/retrieval/pipeline.py`: retrieval execution and `QueryResult` assembly
- `easyrag/rag/orchestrator.py`: the high-level `EasyRAG` API that ties it together

This is the main teaching pattern of the project: a small number of concepts, each tied to a visible module.

## What To Read Or Run Next

The best next step after this chapter is to watch indexing happen on a small repository-shaped corpus:

- run [notebooks/fundamentals/01_build_index.ipynb](../notebooks/fundamentals/01_build_index.ipynb) to load docs, inspect chunks, and build an index
- then read [03-indexing-overview.md](03-indexing-overview.md) for a deeper look at ingestion details
- come back to [00-overview.md](00-overview.md) if you want the higher-level map again

If `00-overview.md` told you what the project is, this chapter should tell you what the main objects are. The next notebook will show how those objects get created in practice.
