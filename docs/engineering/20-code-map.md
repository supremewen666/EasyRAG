# Code Map

## What Problem This Page Answers

This page answers where a new reader should enter the codebase after finishing the overview docs. It is the anchor page for the engineering section and should make the rest of the repository navigable.

## Core Idea Or Mechanism

The codebase is easiest to read through runtime flow: public entrypoints first, then orchestration, then stage-specific modules for indexing, retrieval, knowledge curation, and storage. The key is to map user-facing actions such as build, query, and inspect back to the modules that own them.

## Tradeoffs / Failure Modes

Code maps become stale quickly if they list every file instead of the stable module seams. If this page is vague, architecture overview links become dead ends and readers lose the engineering thread before they reach the real implementation.

## Where To Go Next

- Start from [../../easyrag/rag/orchestrator.py](../../easyrag/rag/orchestrator.py) and [../../easyrag/rag/types.py](../../easyrag/rag/types.py).
- Then read [../../easyrag/rag/indexing/pipeline.py](../../easyrag/rag/indexing/pipeline.py) and [../../easyrag/rag/retrieval/pipeline.py](../../easyrag/rag/retrieval/pipeline.py).
- Use [../../examples/build_index_demo.py](../../examples/build_index_demo.py) and [../../examples/query_demo.py](../../examples/query_demo.py) as runnable entrypoints.
