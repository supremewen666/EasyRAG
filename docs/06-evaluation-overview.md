# Evaluation Overview

This chapter turns evaluation into a first-class stage instead of leaving it scattered across debugging notes. A RAG system can produce fluent answers for the wrong reasons, so "the answer looks fine" is not enough.

## The learning question

What exactly should you measure in a RAG pipeline, and how do you use those measurements to locate the weak layer instead of only scoring the final answer?

## The evaluation flow

```text
loaded corpus and query set
  -> evaluation set construction
  -> retrieval metrics
  -> grounding and usefulness checks
  -> latency, cost, and regression checks
  -> eval-driven debugging
```

The key idea is that evaluation is not one metric and not one stage at the very end.

## What you will learn

- why RAG evaluation has to be layered
- which artifacts EasyRAG already exposes for inspection
- how offline and online evaluation answer different questions
- why optimization should start from evaluation findings, not intuition alone

## Layered evaluation

Different problems show up in different places:

- bad source loading leads to missing or noisy inputs
- bad chunking leads to weak evidence boundaries
- bad retrieval leads to low recall or poor ranking
- bad answer synthesis leads to unsupported claims even when the right citations were found

If you only score the final answer, those failure modes collapse into one blurry signal.

EasyRAG already exposes several artifacts that make layered evaluation practical:

- canonical documents
- chunks
- citations
- retrieval metadata
- `QueryResult`

Those objects let you inspect what the system saw, what it searched, what it returned, and what the downstream answer layer did later.

## Metric families

### Retrieval metrics

These metrics ask whether the system found the right evidence:

- hit rate
- recall@k
- precision@k
- MRR or NDCG
- candidate coverage across retrieval modes

### Grounding and answer checks

These checks ask whether the answer stayed tied to the evidence:

- is each claim supported by a citation?
- does the answer drift beyond the retrieved snippets?
- did the answer stay useful without inventing unsupported detail?
- does the answer follow the expected abstention policy when evidence is weak?

### Operational checks

Real systems also need:

- latency
- throughput
- cost per query
- stability across runs
- regression checks before and after a change

These do not replace retrieval or grounding metrics, but they matter once the core behavior is acceptable.

## Industrial evaluation methods

Industrial RAG evaluation usually combines several methods:

- a small golden set with explicit evidence expectations
- synthetic or bootstrapped evaluation items when coverage is thin
- pairwise answer comparison
- citation verification
- human review for edge cases
- latency and throughput SLO tracking
- cost tracking by stage or by query
- regression suites that run before and after retrieval or prompting changes

That is why evaluation sits before optimization in the mainline. It tells you which layer deserves the next tuning pass.

## Offline and online evaluation

Offline evaluation is the fastest place to compare retrieval policies, ranking policies, or prompt variants against a known set of examples. Online evaluation matters once you care about real traffic, user tolerance, and operational behavior.

You usually need both:

- offline evaluation for fast iteration
- online or shadow evaluation for behavior under realistic conditions

## Evaluation and debugging belong together

Evaluation is not just a scorecard. It is a localization tool:

- low recall can point back to chunking or query rewrite
- weak ranking can point to fusion or rerank policy
- good retrieval plus weak answers often points to context packing or prompting
- unstable latency can point to provider, caching, or orchestration issues

That is the bridge into the next chapter.

## Notebook handoff

The evaluation notebooks now form a fuller sequence:

- [06_01_evaluation_basics.ipynb](../notebooks/06_evaluation/06_01_evaluation_basics.ipynb)
- [06_02_building_a_tiny_eval_set.ipynb](../notebooks/06_evaluation/06_02_building_a_tiny_eval_set.ipynb)
- [06_03_retrieval_metrics.ipynb](../notebooks/06_evaluation/06_03_retrieval_metrics.ipynb)
- [06_04_answer_grounding_and_faithfulness.ipynb](../notebooks/06_evaluation/06_04_answer_grounding_and_faithfulness.ipynb)
- [06_05_eval_driven_debugging.ipynb](../notebooks/06_evaluation/06_05_eval_driven_debugging.ipynb)
- [06_06_latency_cost_and_regression_checks.ipynb](../notebooks/06_evaluation/06_06_latency_cost_and_regression_checks.ipynb)

Some of these are still lightweight scaffolds, but together they complete the loop from measurement to diagnosis.

## Where to go next

- Continue with [07-optimization-overview.md](07-optimization-overview.md) once you want to turn evaluation findings into concrete tuning choices.
- Revisit [04-retrieval-overview.md](04-retrieval-overview.md) or [05-generation-overview.md](05-generation-overview.md) if an evaluation result tells you which stage to inspect next.
