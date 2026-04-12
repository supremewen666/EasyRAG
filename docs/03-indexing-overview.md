# Indexing Overview

This chapter explains what happens before retrieval can work at all. In EasyRAG, indexing is the phase that turns source material into searchable workspace state. If you skip this phase conceptually, retrieval looks like magic. If you understand it, retrieval becomes much easier to reason about.

The core question for this page is: how do raw documents become chunks, summaries, vectors, and graph signals that later support grounded results?

## Why Indexing Exists Before Retrieval

Retrieval does not start from nothing. Before a question can be answered with grounded citations, the system needs prepared knowledge artifacts:

- documents with stable metadata
- chunk boundaries
- summary records
- vector entries or fallback searchable records
- optional graph entities and relations
- persistent workspace files

That is what indexing creates. It is the preparation phase that transforms source content into retrievable structure.

This is why "build the index" is not a housekeeping step. It is the moment where the corpus becomes searchable knowledge.

## The Indexing Pipeline In One Flow

At a high level, indexing in EasyRAG looks like this:

```text
source files or manual texts
  -> Document objects
  -> chunk selection and chunk generation
  -> summary generation
  -> vector payloads
  -> graph entities and relations
  -> storage writes
  -> reusable workspace state
```

That flow is implemented in small, separate modules so that each transformation stays visible.

## Loading And Preparing Documents

EasyRAG supports two main entry paths into indexing:

### Repository loading

`load_repo_documents()` discovers indexable repository files, reads them, and returns canonical `Document` objects with metadata such as:

- `title`
- `path`
- `relative_path`
- `doc_id`
- `source_type`

For repository-shaped knowledge, this is usually the cleanest entry point because the metadata is derived automatically from the file system.

### Manual preparation

`prepare_documents_for_insert()` and `EasyRAG.prepare_documents()` let you turn raw text plus explicit `ids` and `file_paths` into the same `Document` shape.

This path matters when the corpus does not live as repository files yet. It is also the easiest way to teach custom document ingestion in a notebook.

The key insight is that both paths converge on the same `Document` abstraction. Indexing does not care whether the text came from `docs/architecture.md` or a hand-constructed in-memory example once it has canonical metadata.

## From Documents To Chunks

Chunking is one of the most important decisions in the entire system. Retrieval usually works over chunks rather than over whole documents because smaller units make it easier to return focused evidence.

EasyRAG makes this explicit through `chunk_documents()` and `ChunkingConfig`.

The main strategies are:

- structured chunking for heading-rich documents
- semantic chunking for continuous text when embeddings are available
- sliding-window chunking as a robust fallback

In practice, this means the same repository can contain multiple chunking behaviors:

- Markdown architecture notes often become structured chunks
- simple text notes may fall back to sliding windows
- longer continuous inputs can use semantic boundaries when embeddings are present

This is why indexing quality shapes retrieval quality. A weak chunking decision makes later ranking and fusion harder than it needs to be.

## What The Ingestion Pipeline Creates

Once documents are chunked, the indexing pipeline creates several derived artifacts:

- document records
- chunk records
- summary records
- vector payloads for chunks and summaries
- graph nodes and edges
- semantic relation records
- document status records

The important thing to remember is that indexing is not just "store embeddings." EasyRAG builds a richer workspace than a single vector table. That richer structure is what enables multiple retrieval modes later.

## Why Summaries And Graph Signals Appear During Indexing

Indexing does more than preserve the original text. It also creates higher-level retrieval aids.

### Summaries

Document summaries give retrieval a compact, document-level representation. This becomes especially useful for broader retrieval paths that want more than one isolated chunk match.

### Graph signals

Entities and relations can be extracted during ingestion and synchronized into graph-aware retrieval state. This is what allows local and global retrieval paths to use neighborhoods and relation-aware context instead of relying only on chunk similarity.

For a learner, the main lesson is that indexing can create multiple views of the same corpus:

- chunk-level
- summary-level
- entity-level
- relation-level

Later retrieval modes decide which of those views to emphasize.

## Who Does What In The Code

The indexing responsibilities are split across a few clear interfaces:

- `load_repo_documents()`: discover and read repository content
- `prepare_documents_for_insert()`: normalize raw manual texts into canonical documents
- `chunk_documents()`: choose and execute chunking strategies
- `build_insert_payloads()`: create the records that will be written into storage
- `ingest_documents()`: persist the indexed artifacts into the active workspace
- `rebuild_document_index()`: rebuild a whole repo-root workspace in one call

This is a good example of EasyRAG's teaching style: each stage is small enough to inspect directly.

## What The On-Disk Workspace Contains

When you rebuild a workspace with local storage, EasyRAG writes a set of persistent files that together represent the indexed state.

At a high level, you should expect artifacts for:

- document and chunk storage
- summaries
- vector state
- graph state
- document status tracking
- a compatibility snapshot for quick inspection

That is why a finished build feels larger than a single vector index. The workspace is a bundle of coordinated retrieval structures, not just one numeric matrix.

## Zero-Key Indexing And Fallback Behavior

One important property of the teaching setup is that indexing can still run without a real API key. In those cases, EasyRAG can still build local workspace structure and later retrieve through fallback search behavior.

This matters for notebooks because it means learners can still understand:

- loading
- chunking
- workspace persistence
- retrieval verification

without needing a live provider before they understand the architecture.

In other words, zero-key indexing is not feature-complete production retrieval. It is a practical way to keep the learning loop runnable.

## How This Chapter Connects To The Notebooks

This page explains the objects and transitions. The notebooks show them happening in sequence.

- [fundamentals/01_build_index.ipynb](../notebooks/fundamentals/01_build_index.ipynb) shows a repo-shaped corpus becoming a workspace
- [fundamentals/03_custom_documents.ipynb](../notebooks/fundamentals/03_custom_documents.ipynb) shows the manual-document path

The connection between them is important:

- the build-index notebook emphasizes repository loading and workspace artifacts
- the custom-documents notebook emphasizes metadata control and manual ingestion

Together, they show the two main ways knowledge can enter EasyRAG.

## Where To Go Next

After this overview, choose the next layer depending on what you want to understand:

- run [fundamentals/01_build_index.ipynb](../notebooks/fundamentals/01_build_index.ipynb) for the repository build walkthrough
- run [fundamentals/03_custom_documents.ipynb](../notebooks/fundamentals/03_custom_documents.ipynb) for the manual-ingestion path
- read [principles/11-chunking-strategies.md](principles/11-chunking-strategies.md) for chunking tradeoffs
- read [engineering/21-indexing-pipeline.md](engineering/21-indexing-pipeline.md) for a more code-oriented pipeline explanation

If `02-system-architecture.md` gave you the whole map, this chapter should tell you exactly what the indexing half of that map is responsible for.
