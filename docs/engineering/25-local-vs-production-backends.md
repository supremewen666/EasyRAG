# Local Vs Production Backends

## What Problem This Page Answers

This page answers how the repository's local teaching setup relates to its more production-oriented backend bundle. It is an implementation page about concrete module boundaries, not a general storage-principles page.

## Core Idea Or Mechanism

The engineering distinction is between a simple local stack that optimizes for inspectability and a production-oriented stack that optimizes for scale, concurrency, and operational correctness. The important question is which abstractions stay stable when backend implementations change.

## Tradeoffs / Failure Modes

Local backends are easy to reason about but can hide production concerns such as concurrency, persistence guarantees, and multi-process coordination. Production backends solve those problems, but can make learning harder if the abstraction boundary is not explicit.

## Where To Go Next

- Read [../../easyrag/rag/storage/local.py](../../easyrag/rag/storage/local.py) and [../../easyrag/rag/storage/production.py](../../easyrag/rag/storage/production.py) first.
- Then inspect [../../easyrag/rag/storage/bundles.py](../../easyrag/rag/storage/bundles.py) and [../../easyrag/config/storage.py](../../easyrag/config/storage.py).
- For backend implementations, follow the `kv`, `vector`, `graph`, and `status` modules under [../../easyrag/rag/storage](../../easyrag/rag/storage).
