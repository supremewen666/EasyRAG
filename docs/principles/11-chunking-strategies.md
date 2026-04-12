# Chunking Strategies

## What Problem This Page Answers

This page answers how raw documents should be cut into retrievable units before indexing. It treats chunking as a core modeling choice, not as a preprocessing detail.

## Core Idea Or Mechanism

Chunking decides the semantic granularity of retrieval. Different strategies such as fixed windows, structure-aware segmentation, and overlap-based slicing each change what can be recalled and what context must later be reconstructed.

## Tradeoffs / Failure Modes

Chunks that are too small lose context; chunks that are too large reduce precision and waste token budget. Overlap can improve recall but increases index size, redundancy, and downstream rerank or packing costs.

## Where To Go Next

- Return to [overview](../00-overview.md) for the phase map.
- Pair this page with [indexing overview](../03-indexing-overview.md).
- Continue in the notebook [03_01_chunking_principles.ipynb](../../notebooks/03_indexing/03_01_chunking_principles.ipynb).
