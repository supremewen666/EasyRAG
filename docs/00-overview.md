# Overview

This page is the front door to EasyRAG as a teaching repository. It is meant to give you one stable map before you dive into individual modules, notebooks, or helper functions. The repository is easier to learn when each stage stays visible and the artifacts from that stage stay inspectable.

## The learning question

What are the stages of a small RAG system, and how does EasyRAG make each stage visible instead of collapsing everything into one opaque API call?

## The end-to-end flow

```text
source files or raw texts
  -> canonical Document objects
  -> chunks, summaries, vectors, and graph state
  -> query normalization and retrieval planning
  -> ranked evidence and hydrated citations
  -> downstream answer generation
  -> evaluation
  -> optimization
```

That order is the teaching backbone of the repo. Retrieval quality depends on what was loaded and indexed earlier. Generation quality depends on the evidence retrieval returned. Optimization only becomes useful after evaluation tells you which stage is weak.

## What you will learn here

- how the main docs and notebooks line up with the same pipeline
- which objects are worth inspecting at each stage
- where the current material is already runnable and where it is still a scaffold
- how to move through the repo without treating it like a black box

## Key concepts

### Stage boundaries matter

EasyRAG is easier to reason about when you keep a few boundaries fixed:

- loading happens before indexing
- indexing happens before retrieval
- retrieval returns evidence, not a polished final answer
- evaluation is a first-class stage, not a late add-on
- optimization starts after measurement, not before it

### The public teaching objects are small on purpose

If you keep only a few names in your head at first, keep these:

- `Document`
- `ChunkingConfig`
- `QueryParam`
- `QueryResult`

They connect the docs, notebooks, and codebase better than a long directory listing ever could.

### Docs and notebooks tell the same story

The docs explain the stage. The notebooks show the same stage in a runnable or scaffolded form. That mirror is deliberate. It keeps the repository close to the step-by-step teaching rhythm used in [pguso/rag-from-scratch](https://github.com/pguso/rag-from-scratch): move through the pipeline in order, inspect intermediate artifacts, and only then add another layer.

## What is complete and what is still lightweight

The repo now has one stable curriculum shape, but not every notebook is equally deep yet.

- `01-rag-basics.md` is a docs-only vocabulary chapter
- `07-optimization-overview.md` is a docs-only roadmap chapter for now
- several stage notebooks are full walkthroughs
- several newer notebooks are intentionally scaffolded so the directory tree is stable before every lab is fully built out

That is not accidental. The structure is final first, then the deeper stage labs can grow inside it.

## Notebook handoff

Start here if you want the smallest runnable loop:

- [00_01_quickstart_end_to_end.ipynb](../notebooks/00_overview/00_01_quickstart_end_to_end.ipynb) for the compact end-to-end path
- [00_02_observing_rag_artifacts.ipynb](../notebooks/00_overview/00_02_observing_rag_artifacts.ipynb) for the artifact-level companion

Then move through the mainline docs in order:

1. [01-rag-basics.md](01-rag-basics.md)
2. [02-data-loading-overview.md](02-data-loading-overview.md)
3. [03-indexing-overview.md](03-indexing-overview.md)
4. [04-retrieval-overview.md](04-retrieval-overview.md)
5. [05-generation-overview.md](05-generation-overview.md)
6. [06-evaluation-overview.md](06-evaluation-overview.md)
7. [07-optimization-overview.md](07-optimization-overview.md)
8. [08-system-architecture-overview.md](08-system-architecture-overview.md)

## Where to go next

- Read [01-rag-basics.md](01-rag-basics.md) if you want the smallest vocabulary first.
- Continue with [02-data-loading-overview.md](02-data-loading-overview.md) if you want to see how raw inputs become canonical records.
- Keep [notebooks/README.md](../notebooks/README.md) open if you prefer to move through the curriculum stage by stage.
