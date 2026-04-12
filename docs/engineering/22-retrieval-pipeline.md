# Retrieval Pipeline

## What Problem This Page Answers

This page answers how one query moves through preprocessing, candidate retrieval, fusion, hydration, and final result shaping. It is the code-oriented companion to the retrieval overview.

## Core Idea Or Mechanism

The retrieval pipeline composes several narrower modules rather than one monolithic search function. Query preparation, mode execution, fusion, reranking, and hydration should each leave behind inspectable intermediate artifacts.

## Tradeoffs / Failure Modes

Retrieval code gets hard to reason about when candidate generation, score combination, and result shaping are mixed together. Hidden fallback behavior can also make the system appear robust while quietly masking weak first-stage retrieval.

## Where To Go Next

- Read [../../easyrag/rag/retrieval/pipeline.py](../../easyrag/rag/retrieval/pipeline.py) first.
- Then inspect [../../easyrag/rag/retrieval/preprocess.py](../../easyrag/rag/retrieval/preprocess.py), [../../easyrag/rag/retrieval/query_modes.py](../../easyrag/rag/retrieval/query_modes.py), [../../easyrag/rag/retrieval/fusion.py](../../easyrag/rag/retrieval/fusion.py), and [../../easyrag/rag/retrieval/hydration.py](../../easyrag/rag/retrieval/hydration.py).
- For a runnable entrypoint, open [../../examples/query_demo.py](../../examples/query_demo.py).
