# Evaluation Overview

This chapter turns evaluation into a first-class stage instead of leaving it scattered across debugging notes. A RAG system can produce fluent answers for the wrong reasons, so "the answer looks fine" is not enough.

## The learning question

What exactly should you measure in a RAG pipeline, and how do you use those measurements to locate the weak layer instead of only scoring the final answer?

## The evaluation flow

```text
loaded corpus and query set
  -> tiny eval set with gold evidence or expected behavior
  -> retrieval metrics
  -> grounding and faithfulness checks
  -> answer usefulness checks
  -> eval-driven debugging
```

The key idea is that evaluation is not one metric and not one stage at the very end.

## Why RAG evaluation needs layers

Different problems show up in different places:

- bad source loading leads to missing or noisy inputs
- bad chunking leads to weak evidence boundaries
- bad retrieval leads to low recall or poor ranking
- bad answer synthesis leads to unsupported claims even when the right citations were found

If you only score the final answer, those failure modes collapse into one blurry signal.

## What can be evaluated in EasyRAG

EasyRAG already exposes several artifacts that make evaluation practical:

- canonical documents
- chunks
- citations
- retrieval metadata
- `QueryResult`

Those objects give you a way to inspect what the system saw, what it searched, what it returned, and what a downstream answer layer used later.

## A small eval set is a good teaching tool

The first useful evaluation set is usually small and explicit:

- one query
- one or more gold evidence records
- an expected answer shape or a grounded claim list

That is enough to teach the habit of checking whether retrieval found the right evidence before you start tuning prompts or providers.

## The main metric families

### Retrieval quality

These metrics ask whether the system found the right evidence:

- hit rate
- recall@k
- precision@k
- MRR or other ranking-aware metrics
- candidate coverage across retrieval modes

### Grounding and faithfulness

These checks ask whether the answer stayed tied to the evidence:

- is each claim supported by a citation?
- does the answer drift beyond the retrieved snippets?
- did the answer stay useful without inventing unsupported detail?

### Operational behavior

For real systems, evaluation also includes:

- latency
- cost
- stability across runs or provider settings

Those do not replace retrieval or grounding metrics, but they matter once the core behavior is acceptable.

## Evaluation and debugging belong together

Evaluation is not just a scorecard for a report. It is a way to localize problems:

- low recall might point back to chunking or query rewriting
- weak ranking might point to fusion or rerank policy
- good retrieval plus weak answers often points to context packing or prompting

That is why the evaluation stage sits before optimization in the mainline.

## Notebook handoff

The evaluation notebooks now form a small sequence:

- [06_01_eval_basics.ipynb](../notebooks/06_evaluation/06_01_eval_basics.ipynb)
- [06_02_build_tiny_eval_set.ipynb](../notebooks/06_evaluation/06_02_build_tiny_eval_set.ipynb)
- [06_03_retrieval_metrics.ipynb](../notebooks/06_evaluation/06_03_retrieval_metrics.ipynb)
- [06_04_grounding_and_faithfulness.ipynb](../notebooks/06_evaluation/06_04_grounding_and_faithfulness.ipynb)
- [06_05_eval_driven_debugging.ipynb](../notebooks/06_evaluation/06_05_eval_driven_debugging.ipynb)

They are intentionally compact, but together they complete the loop from retrieval and generation into measurement and diagnosis.

## Where to go next

- Continue with [07-optimization-overview.md](07-optimization-overview.md) once you want to turn evaluation findings into concrete tuning choices.
- Revisit [04-retrieval-overview.md](04-retrieval-overview.md) or [05-generation-overview.md](05-generation-overview.md) if an evaluation result tells you which stage to inspect next.
