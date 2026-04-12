# Indexing Overview

This chapter explains what happens after documents have already been loaded and normalized. In EasyRAG, indexing is the stage that turns canonical `Document` objects into searchable workspace state.

## The learning question

How does chunking turn loaded documents into retrievable units, then into embeddings, vector records, summaries, graph signals, and stored artifacts that retrieval can actually use later?

## The indexing flow

```text
Document objects
  -> chunking
  -> embedding generation
  -> vector indexing
  -> summaries and graph enrichment
  -> storage writes
  -> reusable workspace state
```

That order is important. Chunking decides the retrieval unit. Embeddings represent that unit numerically. Vector indexing makes those embeddings searchable. Storage turns the whole bundle into something retrieval can reuse.

## What you will learn

- why indexing is more than "build the vector store"
- why the stage order must stay `chunking -> embedding -> vector index`
- how summaries, graph signals, and workspace artifacts fit beside dense retrieval
- which industrial indexing patterns are worth making explicit

## Key concepts

### Chunking is the first real indexing decision

EasyRAG makes chunking explicit through `chunk_documents()` and `ChunkingConfig`. Common strategies include:

- structured chunking for heading-rich material
- semantic chunking for long continuous text when embeddings are available
- sliding-window chunking as a robust fallback

Chunking quality shapes everything that comes later. If the chunks are too broad, retrieval drags in noise. If the chunks are too thin, retrieval returns fragments with weak context.

### Embeddings are a separate stage, not a hidden side effect

Once chunks exist, they become embedding inputs. This boundary matters because embedding behavior depends on:

- the model you chose
- the text you passed in
- the normalization you applied before encoding
- batching, caching, and provider behavior

Keeping embeddings explicit makes later debugging much easier.

### Vector indexing makes embeddings usable

Embeddings are not retrievable by themselves. They still need:

- an index structure
- metadata-aware storage
- namespace design
- incremental rebuild rules

That is why vector indexing deserves its own place in the curriculum.

## Normalization Before Embedding

Normalization appears again here because chunk text often needs one more pass before it becomes an embedding input.

Typical indexing-side normalization includes:

- removing repeated boilerplate that survived loading
- stabilizing whitespace and punctuation
- preserving useful headings while cleaning noisy separators
- keeping chunk text consistent across rebuilds

This matters because embedding models are sensitive to input shape. Two chunks that look almost the same to a human can still become less consistent vectors if the text is noisy in predictable ways.

## Industry Patterns In Indexing

Industrial indexing systems usually do more than "chunk and embed":

- parent-child chunking
- heading-aware chunking
- semantic chunking when structure is weak
- summary indexing for document-level recall
- multi-representation indexing across title, summary, and body
- metadata-filter-ready indexing
- embedding caches
- incremental indexing instead of full rebuilds
- separate namespaces for chunk, summary, and graph-oriented records

The useful mental model is that indexing creates several retrievable views of the same source material.

## What gets written to the workspace

In local mode, a finished build usually leaves behind artifacts for:

- documents and chunks
- summaries
- vector state
- graph state
- status tracking
- compatibility or maintenance snapshots

That is why a finished workspace feels larger than a single vector table. EasyRAG builds a coordinated artifact bundle, not just one searchable list.

## Notebook handoff

The indexing notebooks now follow the stage order directly:

- [03_01_chunking_principles.ipynb](../notebooks/03_indexing/03_01_chunking_principles.ipynb)
- [03_02_chunking_quality_analysis.ipynb](../notebooks/03_indexing/03_02_chunking_quality_analysis.ipynb)
- [03_03_embeddings_basics.ipynb](../notebooks/03_indexing/03_03_embeddings_basics.ipynb)
- [03_04_normalization_before_embedding.ipynb](../notebooks/03_indexing/03_04_normalization_before_embedding.ipynb)
- [03_05_embedding_inputs_and_provider_behavior.ipynb](../notebooks/03_indexing/03_05_embedding_inputs_and_provider_behavior.ipynb)
- [03_06_vector_index_basics.ipynb](../notebooks/03_indexing/03_06_vector_index_basics.ipynb)
- [03_07_build_index_pipeline.ipynb](../notebooks/03_indexing/03_07_build_index_pipeline.ipynb)
- [03_08_storage_and_workspace_artifacts.ipynb](../notebooks/03_indexing/03_08_storage_and_workspace_artifacts.ipynb)

Some are full walkthroughs today and some are still scaffolds, but the order is final.

## Where to go next

- Continue with [04-retrieval-overview.md](04-retrieval-overview.md) once you want to inspect how the workspace is searched.
- Read [engineering/21-indexing-pipeline.md](engineering/21-indexing-pipeline.md) if you want the code-oriented version of the same stage.
