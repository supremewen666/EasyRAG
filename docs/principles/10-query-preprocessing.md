# Query Preprocessing

## What Problem This Page Answers

This page answers what should happen between a user's raw question and the retrieval system's actual search input. It frames query preprocessing as a quality control layer rather than as a small optimization.

## Core Idea Or Mechanism

The core mechanism is to turn one unstable natural-language question into a more retrieval-friendly representation through normalization, rewrite, decomposition, or expansion. The goal is to improve recall without losing the user's original intent.

## Tradeoffs / Failure Modes

Preprocessing can help under-specified or noisy queries, but it can also drift the query away from the user's wording, introduce over-expansion, or make later debugging harder if the transformed query is not observable.

## Where To Go Next

- Return to [overview](../00-overview.md) for the stage-level path.
- Pair this page with [retrieval overview](../04-retrieval-overview.md).
- Continue in the notebook [04_01_query_normalization_and_preprocessing.ipynb](../../notebooks/04_retrieval/04_01_query_normalization_and_preprocessing.ipynb).
