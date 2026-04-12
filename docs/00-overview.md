# Overview

This page is the front door to EasyRAG as a teaching repository. The goal is not to show every feature at once. The goal is to give you a stable mental model, show where the main code lives, and point you to the first runnable walkthrough in [00_quickstart.ipynb](../notebooks/fundamentals/00_quickstart.ipynb).

## Why RAG

Large Language Models are strong pattern matchers, but they still have several limits that matter in real applications:

- their knowledge can be stale
- they can hallucinate unsupported claims
- they do not know your private repository or documentation by default
- they often answer without a clear evidence trail

Retrieval-Augmented Generation (RAG) addresses this by adding an explicit retrieval step before generation. Instead of asking the model to answer from parameters alone, we first retrieve relevant chunks from an external knowledge base and then use those grounded artifacts to support the response.

That shift matters because it turns the system from "guess from pretrained memory" into "search, gather evidence, then answer."

## What EasyRAG Is

EasyRAG is a lightweight, teaching-first RAG core library for repository and local-document workflows. It keeps the scope intentionally narrow:

- load and normalize documents
- chunk them into retrievable units
- store searchable artifacts in local or production-style backends
- retrieve chunks through multiple query modes
- attach lightweight knowledge graph signals when helpful

This repository is small on purpose. You can read the orchestrator, the indexing pipeline, the retrieval pipeline, and the storage layer without stepping through a large framework. That makes it useful for both learners and engineers who want a compact reference implementation.

## How This Repo Maps to RAG From Scratch

The teaching flow is inspired by the "build it step by step" style from [pguso/rag-from-scratch](https://github.com/pguso/rag-from-scratch). EasyRAG follows the same broad story, but the code is organized as a Python library with pluggable backends and a repository-oriented workflow.

| Tutorial idea | EasyRAG location | What it does in this repo |
| --- | --- | --- |
| Load source documents | `easyrag/rag/indexing/loaders.py` | Discovers indexable docs and PDFs and turns them into `Document` objects. |
| Normalize manual inserts | `easyrag/rag/indexing/prepare.py` | Converts raw strings into canonical `Document` records with metadata. |
| Chunk documents | `easyrag/rag/indexing/chunking.py` | Splits documents into chunks for retrieval and downstream enrichment. |
| Build searchable artifacts | `easyrag/rag/indexing/pipeline.py` | Creates document, chunk, summary, vector, and graph payloads during ingestion. |
| Configure model providers | `easyrag/rag/providers.py` | Adapts OpenAI-compatible embedding, query rewrite, rerank, and KG extraction calls. |
| Rewrite and expand queries | `easyrag/rag/retrieval/preprocess.py` | Normalizes the query, optionally rewrites it, and generates MQE variants. |
| Run retrieval modes | `easyrag/rag/retrieval/query_modes.py` | Implements naive, local, global, hybrid, and mix retrieval behavior. |
| Coordinate the full flow | `easyrag/rag/orchestrator.py` | Exposes `EasyRAG` as the high-level API for insert, query, and maintenance. |
| Swap storage backends | `easyrag/rag/storage/` | Separates local-first storage from production-oriented bundles. |
| Rebuild a repo index | `scripts/build_index.py` | Provides a small CLI for repository indexing and maintenance. |

The useful takeaway is that the same RAG story still applies: collect documents, transform them into searchable units, retrieve evidence, and return grounded results. EasyRAG just makes each stage explicit in library form.

## The Smallest End-to-End Flow

At the highest level, EasyRAG revolves around one simple loop:

1. Create an `EasyRAG` instance
2. Initialize storages
3. Insert documents
4. Query with `QueryParam`
5. Finalize storages

The smallest example looks like this:

```python
from easyrag import EasyRAG, QueryParam
from easyrag.support.async_utils import run_sync

rag = EasyRAG()
run_sync(rag.initialize_storages())

run_sync(
    rag.ainsert(
        "EasyRAG uses retrieval before generation.",
        ids=["doc::demo"],
        file_paths=["notes/demo.md"],
    )
)

result = run_sync(
    rag.aquery(
        "How does EasyRAG answer grounded questions?",
        QueryParam(mode="hybrid"),
    )
)

print(result.citations)
run_sync(rag.finalize_storages())
```

That is the whole mental model in miniature: ingestion creates indexed knowledge, and retrieval turns a question into grounded citations.

## How To Use The Quickstart Notebook

The first runnable walkthrough lives in [00_quickstart.ipynb](../notebooks/fundamentals/00_quickstart.ipynb). It is structured as a teaching notebook rather than a benchmark notebook:

- each important code cell is introduced by a Markdown explanation
- each important code cell is followed by a short note on what you should observe
- Path A uses deterministic stub functions so the notebook can run without API keys
- Path B shows the same lifecycle with real OpenAI-compatible providers after configuration

This is deliberate. The notebook is meant to be readable by both humans and future coding agents: the explanation stays next to the code, the execution path is obvious, and the expected results are named where they appear.

If you are new to the repo, start with the stub path first. It teaches the orchestration shape without introducing provider configuration noise. Then move to the real-provider path once the lifecycle makes sense.

## Where To Go Next

After the quickstart, continue in this order:

- [01-rag-basics.md](01-rag-basics.md) for the conceptual building blocks
- [02-system-architecture.md](02-system-architecture.md) for the system-level map
- [03-indexing-overview.md](03-indexing-overview.md) for document preparation and indexing
- [04-retrieval-overview.md](04-retrieval-overview.md) for query preprocessing and retrieval modes
- [notebooks/README.md](../notebooks/README.md) for the notebook roadmap

When you want to move from a tiny in-memory example to repository-scale indexing, inspect `EasyRAG.load_repo_documents()` and then read `scripts/build_index.py`. Those two entry points bridge the gap between a teaching example and the real repository workflow.
