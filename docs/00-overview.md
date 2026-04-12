# Overview

This page is the front door to EasyRAG as a teaching repository. The goal is not to show every feature at once. The goal is to give you a stable mental model, show where the main code lives, and point you to the first runnable walkthrough in [00_quickstart.ipynb](../notebooks/00_overview/00_quickstart.ipynb).

## The learning question

What are the stages of a small RAG system, and how does EasyRAG make those stages visible instead of hiding them behind one opaque API call?

## The end-to-end flow

At a high level, EasyRAG follows one simple loop:

```text
source files or raw texts
  -> canonical Document objects
  -> chunks, summaries, vectors, and graph state
  -> query preprocessing
  -> retrieval modes and ranking
  -> grounded citations and diagnostics
  -> downstream answer generation
  -> evaluation and optimization
```

That order matters. Retrieval quality depends on what was loaded and indexed earlier. Answer quality depends on what retrieval returned. Evaluation only becomes useful once you can inspect each stage separately.

## What EasyRAG is

EasyRAG is a lightweight, teaching-first RAG core library for repository and local-document workflows. It keeps the scope intentionally narrow:

- load and normalize documents
- chunk them into retrievable units
- store searchable artifacts in local or production-style backends
- retrieve chunks through multiple query modes
- attach lightweight graph signals when helpful
- hand back grounded results that are easy to inspect

That makes the repository useful in two ways. You can learn the shape of a RAG system from it, and you can also use it as a compact reference implementation when you need to extend or debug one.

## What EasyRAG does not hide

EasyRAG is easiest to learn when you keep these boundaries visible:

- data loading happens before indexing
- indexing happens before retrieval
- retrieval returns evidence, not a polished final answer
- evaluation is not a separate afterthought; it is how you tell which layer is weak
- optimization only makes sense once evaluation has localized the problem

This is close to the step-by-step teaching rhythm used in [pguso/rag-from-scratch](https://github.com/pguso/rag-from-scratch): move through the pipeline in order, inspect each artifact, and only then stack on the next concept.

## How the mainline is organized

The documentation now follows the pipeline directly:

1. [01-rag-basics.md](01-rag-basics.md)
2. [02-data-loading-overview.md](02-data-loading-overview.md)
3. [03-indexing-overview.md](03-indexing-overview.md)
4. [04-retrieval-overview.md](04-retrieval-overview.md)
5. [05-generation-overview.md](05-generation-overview.md)
6. [06-evaluation-overview.md](06-evaluation-overview.md)
7. [07-optimization-overview.md](07-optimization-overview.md)
8. [08-system-architecture-overview.md](08-system-architecture-overview.md)

The notebook tree mirrors the same stages, so the docs and runnable walkthroughs tell the same story instead of drifting apart.

## Start with the quickstart

The first runnable walkthrough lives in [00_quickstart.ipynb](../notebooks/00_overview/00_quickstart.ipynb). It is intentionally small:

- Path A runs with deterministic stubs and no API keys
- Path B keeps the same lifecycle but shows where real providers plug in
- the notebook stays close to the public `EasyRAG` API, not to private helper internals

If you are new to the repo, run the stub path first. It gives you the orchestration shape before any provider configuration noise shows up.

## Where to go next

- Read [01-rag-basics.md](01-rag-basics.md) for the minimal vocabulary: `Document`, chunks, citations, and `QueryResult`.
- Continue with [02-data-loading-overview.md](02-data-loading-overview.md) when you want to see how raw inputs become canonical records.
- Keep [notebooks/README.md](../notebooks/README.md) open if you prefer to move stage by stage through runnable material.
