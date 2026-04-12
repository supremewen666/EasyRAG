# Storage Design And Backend Tradeoffs

## What Problem This Page Answers

This page answers how to think about storage as a system design decision in RAG, not just as a deployment detail. It focuses on why different data shapes often need different persistence strategies.

## Core Idea Or Mechanism

RAG systems usually separate concerns across KV, vector, graph, and status stores because their access patterns, consistency needs, and scaling pressures differ. Backend choice is therefore part of retrieval and indexing design, not a purely operational afterthought.

## Tradeoffs / Failure Modes

Collapsing everything into one store simplifies setup but usually hurts one workload. Splitting stores improves specialization, but raises coordination cost, synchronization risk, and observability complexity when pipelines fail halfway.

## Where To Go Next

- Return to [overview](../00-overview.md) for the full stage path.
- Pair this page with [system architecture overview](../08-system-architecture-overview.md).
- Continue in the notebook [03_08_storage_and_workspace_artifacts.ipynb](../../notebooks/03_indexing/03_08_storage_and_workspace_artifacts.ipynb).
