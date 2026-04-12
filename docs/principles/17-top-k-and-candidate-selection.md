# Top-K And Candidate Selection

## What Problem This Page Answers

This page answers how many retrieved items should survive into answer preparation. It treats candidate selection as a bridge between retrieval quality and generation quality.

## Core Idea Or Mechanism

Top-k and candidate selection convert a ranked list into a bounded working set using fixed limits, score thresholds, or token-budget-aware rules. The goal is to preserve enough evidence for grounding without overwhelming the answer stage.

## Tradeoffs / Failure Modes

Small candidate sets improve efficiency but risk missing necessary support. Large sets improve recall but increase noise, duplication, and the chance that later packing or prompting buries the most useful evidence.

## Where To Go Next

- Return to [overview](../00-overview.md) for the stage sequence.
- Pair this page with [generation overview](../05-generation-overview.md).
- Continue in the notebook [05_02_evidence_selection_and_topk_for_answering.ipynb](../../notebooks/05_generation/05_02_evidence_selection_and_topk_for_answering.ipynb).
