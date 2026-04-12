# Extension Guide

## What Problem This Page Answers

This page answers where new features should attach without breaking the teaching shape of the repo. It is the final engineering page because it depends on readers already understanding the major runtime seams.

## Core Idea Or Mechanism

Extensions should land at stable module boundaries: chunking, providers, retrieval modes, storage adapters, and future generation hooks. The point is not just to add behavior, but to preserve inspectable flow and avoid scattering customization across the codebase.

## Tradeoffs / Failure Modes

Extension guides fail when they encourage direct patching of orchestration code for every new idea. Without clear seams, the project becomes harder to teach, test, and evolve because each feature modifies multiple unrelated modules.

## Where To Go Next

- Start from [../../easyrag/rag/indexing/chunking_core.py](../../easyrag/rag/indexing/chunking_core.py), [../../easyrag/rag/providers.py](../../easyrag/rag/providers.py), and [../../easyrag/rag/storage/base.py](../../easyrag/rag/storage/base.py).
- Then inspect [../../easyrag/rag/retrieval/query_modes.py](../../easyrag/rag/retrieval/query_modes.py) for retrieval-side extension points.
- Use [../../tests/test_rag_retriever.py](../../tests/test_rag_retriever.py) and [../../tests/test_rag_graph_ops.py](../../tests/test_rag_graph_ops.py) as behavior anchors when adding new capabilities.
