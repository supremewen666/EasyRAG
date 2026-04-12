# Indexing Overview

This chapter explains what happens after documents have already been loaded and normalized. In EasyRAG, indexing is the phase that turns canonical `Document` objects into searchable workspace state.

## The learning question

How do loaded documents become chunks, summaries, vectors, graph signals, and on-disk artifacts that retrieval can actually use later?

## The indexing flow

```text
Document objects
  -> chunk selection and chunk generation
  -> summary generation
  -> vector payloads
  -> graph entities and relations
  -> storage writes
  -> reusable workspace state
```

This stage is what makes the corpus retrievable. Without it, retrieval has nothing structured to search over.

## What indexing adds on top of loading

The loading stage made the inputs clean and canonical. Indexing adds the derived artifacts that support later retrieval:

- chunks for focused evidence retrieval
- summaries for broader document-level access
- vector records for dense or fallback search
- graph signals for local and global retrieval paths
- document and status records for persistent workspace management

That is why "build the index" is not a housekeeping step. It is where raw documents become retrievable knowledge.

## Chunking is the first real indexing decision

EasyRAG makes chunking explicit through `chunk_documents()` and `ChunkingConfig`. The main strategies are:

- structured chunking for heading-rich material
- semantic chunking for long continuous text when embeddings are available
- sliding-window chunking as a robust fallback

Chunking quality shapes everything that comes later. If the chunks are too broad, retrieval drags in noise. If the chunks are too thin, retrieval returns fragments with weak context.

## Why summaries and graph signals appear here

Indexing does more than preserve the original text.

### Summaries

Summaries give retrieval a higher-level view of a document. That matters when a single chunk is too narrow but the document still clearly belongs in the candidate set.

### Graph signals

Entities and relations create another view of the corpus. They let graph-aware retrieval modes reason over neighborhoods and relations instead of relying only on chunk similarity.

The useful mental model is that indexing creates several retrievable views of the same source material.

## What gets written to the workspace

In local mode, a finished build usually leaves behind artifacts for:

- documents and chunks
- summaries
- vector state
- graph state
- document status tracking
- compatibility snapshots

That is why a finished workspace feels larger than a single vector table. EasyRAG builds a bundle of coordinated retrieval structures.

## Notebook handoff

The direct notebook companions to this chapter are:

- [03_01_build_index.ipynb](../notebooks/03_indexing/03_01_build_index.ipynb), which rebuilds a small workspace and verifies it with one query
- [03_02_chunking_strategy_lab.ipynb](../notebooks/03_indexing/03_02_chunking_strategy_lab.ipynb), which compares chunking behavior more directly

The first notebook answers "what does index building do?" The second answers "which chunking choice changed what?"

## Where to go next

- Continue with [04-retrieval-overview.md](04-retrieval-overview.md) once you want to inspect how the workspace is searched.
- Read [engineering/21-indexing-pipeline.md](engineering/21-indexing-pipeline.md) if you want the code-oriented version of this stage.
