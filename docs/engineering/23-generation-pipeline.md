# Generation Pipeline

## What Problem This Page Answers

This page answers where answer generation would attach to the current retrieval-oriented public surface. It should clarify the planned handoff from `QueryResult` into context assembly, prompting, and answer synthesis.

## Core Idea Or Mechanism

The generation pipeline should sit immediately after retrieval because it consumes selected evidence rather than raw documents. Even before full implementation lands, readers need a clear extension seam for context builders, prompt builders, and answer synthesizers.

## Tradeoffs / Failure Modes

If generation is described too early as a standalone subsystem, it looks disconnected from retrieval quality. If it is described too late, readers miss the fact that answer quality depends on a concrete post-retrieval pipeline rather than on a single model call.

## Where To Go Next

- Start from [../../easyrag/rag/types.py](../../easyrag/rag/types.py) and [../../easyrag/rag/orchestrator.py](../../easyrag/rag/orchestrator.py) to see the current public handoff.
- Pair it with [05-generation-overview.md](../05-generation-overview.md) for the conceptual stage view.
- Use [../../notebooks/05_generation/05_01_query_result_to_answer.ipynb](../../notebooks/05_generation/05_01_query_result_to_answer.ipynb) as the current learning bridge.
