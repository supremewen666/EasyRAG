# Indexing Pipeline

## What Problem This Page Answers

This page answers how source material becomes persisted retrieval artifacts. It should help readers follow the indexing path from ingestion through chunking, embedding, and storage writes.

## Core Idea Or Mechanism

The indexing pipeline stages document preparation, chunk creation, artifact derivation, and backend writes in a fixed runtime order. Each stage should make its inputs and outputs explicit so readers can tell where summaries, vectors, and graph-side artifacts are created.

## Tradeoffs / Failure Modes

Indexing pipelines fail when stage boundaries are blurry, retries are inconsistent, or side effects across stores are not coordinated. Overloading indexing with too much hidden logic also makes downstream retrieval bugs hard to trace.

## Where To Go Next

- Read [../../easyrag/rag/indexing/pipeline.py](../../easyrag/rag/indexing/pipeline.py) first.
- Then inspect [../../easyrag/rag/indexing/prepare.py](../../easyrag/rag/indexing/prepare.py), [../../easyrag/rag/indexing/chunking.py](../../easyrag/rag/indexing/chunking.py), and [../../easyrag/rag/indexing/loaders.py](../../easyrag/rag/indexing/loaders.py).
- For a runnable path, open [../../scripts/build_index.py](../../scripts/build_index.py).
