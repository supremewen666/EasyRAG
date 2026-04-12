# Hybrid Retrieval And Fusion

## What Problem This Page Answers

This page answers why one retrieval channel is often not enough for production-quality RAG. It covers the logic of combining multiple candidate sources before answer preparation.

## Core Idea Or Mechanism

Hybrid retrieval mixes signals such as dense similarity, keyword constraints, metadata filtering, graph neighborhoods, or summary-level recall. Fusion then combines partial rankings into a stronger candidate pool instead of trusting a single scorer.

## Tradeoffs / Failure Modes

Hybrid setups usually improve robustness, but they also create more knobs, more score calibration problems, and more chances to accumulate redundant or low-signal candidates if fusion is too naive.

## Where To Go Next

- Return to [overview](../00-overview.md) for the stage map.
- Pair this page with [retrieval overview](../04-retrieval-overview.md).
- Continue in the notebook [04_04_hybrid_metadata_filter_and_modes.ipynb](../../notebooks/04_retrieval/04_04_hybrid_metadata_filter_and_modes.ipynb).
