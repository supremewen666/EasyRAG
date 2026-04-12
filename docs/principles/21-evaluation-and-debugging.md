# Evaluation And Debugging

## What Problem This Page Answers

This page answers how to tell whether a RAG system is getting better or just changing behavior. It closes the loop by turning observed failures into measurable debugging work.

## Core Idea Or Mechanism

Evaluation breaks the pipeline into inspectable stages and asks whether failures come from query prep, retrieval, ranking, context packing, or answer synthesis. Good debugging relies on stable artifacts, observable metadata, and a small repeatable test set.

## Tradeoffs / Failure Modes

If evaluation mixes too many variables at once, teams may optimize the wrong stage. Weak observability also creates false confidence because a final answer can look plausible even when the retrieved evidence is poor.

## Where To Go Next

- Return to [overview](../00-overview.md) for the main curriculum path.
- Pair this page with [evaluation overview](../06-evaluation-overview.md).
- Continue in the notebook [06_05_eval_driven_debugging.ipynb](../../notebooks/06_evaluation/06_05_eval_driven_debugging.ipynb).
