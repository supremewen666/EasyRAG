# Graph Curation Pipeline

## What Problem This Page Answers

This page answers how graph-specific artifacts are extracted, cleaned, and synchronized after or alongside indexing. It should help readers see graph curation as a separate runtime concern rather than as a side note inside chunk indexing.

## Core Idea Or Mechanism

Graph curation owns entity and relation extraction, merge logic, and synchronization into graph storage. Its role is to transform document-derived signals into a stable relational layer that retrieval can later exploit.

## Tradeoffs / Failure Modes

Graph curation often fails through noisy extraction, poor deduplication, or inconsistent sync across vector and graph stores. If these responsibilities are hidden inside indexing, graph quality becomes difficult to inspect or improve independently.

## Where To Go Next

- Read [../../easyrag/rag/knowledge/extraction.py](../../easyrag/rag/knowledge/extraction.py), [../../easyrag/rag/knowledge/curation.py](../../easyrag/rag/knowledge/curation.py), and [../../easyrag/rag/knowledge/sync.py](../../easyrag/rag/knowledge/sync.py).
- Then inspect [../../easyrag/rag/storage/graph/networkx_graph.py](../../easyrag/rag/storage/graph/networkx_graph.py) and [../../easyrag/rag/storage/graph/postgres_graph.py](../../easyrag/rag/storage/graph/postgres_graph.py).
- Pair this with [../../docs/04-retrieval-overview.md](../04-retrieval-overview.md) when tracing graph-assisted retrieval behavior.
