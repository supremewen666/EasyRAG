# Generation Overview

This chapter explains what happens after retrieval has already produced grounded evidence. In a full RAG system, generation is the stage that turns citations and retrieval metadata into an answer a human can actually use.

## The learning question

Once retrieval has done its job, how should you choose evidence, pack context, prompt a model, and keep the answer tied back to real citations?

## The generation flow

```text
QueryResult
  -> evidence selection
  -> context assembly
  -> prompt construction
  -> answer synthesis
  -> grounding checks and output shaping
```

That flow is downstream of retrieval, not a replacement for it.

## What you will learn

- why `QueryResult` is the right boundary between retrieval and generation
- why evidence selection comes before prompt writing
- how industrial answering patterns differ from naive "paste all hits into one prompt"
- which failure modes belong to generation even when retrieval was reasonable

## Key concepts

### `QueryResult` keeps the evidence visible

In EasyRAG today, `EasyRAG.aquery()` returns a structured `QueryResult`. That means the repository already teaches the evidence side of the system clearly, while the final answer layer stays explicit and composable downstream.

That boundary is useful because you can inspect the citations before you decide how to answer.

### Candidate selection comes before prompting

One common beginner mistake is to pass every retrieved hit straight into the final prompt. That usually fails because:

- some hits are redundant
- some hits are only loosely relevant
- prompt budget gets spent on weak context
- too much context makes the answer path blurrier, not clearer

Retrieval chooses candidates for inspection. Generation still has to choose which evidence survives into the final answer context.

### Context assembly is a separate decision

Even after you choose the evidence set, you still need to decide how to present it:

- order by score or by source
- group related snippets together or keep them separate
- clip long snippets or preserve more context
- keep titles and paths visible for traceability
- separate evidence text from instructions clearly

Prompt quality depends on those packaging choices as much as on the raw citation set.

## Industrial answering patterns

Industrial answering systems usually add a few policies on top of plain prompt writing:

- citation-aware answers
- extractive-first synthesis before free-form abstraction
- abstention when the evidence is weak
- explicit insufficient-evidence handling
- structured outputs for downstream consumers
- lightweight post-generation grounding checks

These patterns matter because a fluent answer can still be wrong for retrieval-shaped reasons.

## Good retrieval can still lead to bad generation

Generation can fail even when retrieval looked reasonable:

- the best citation was trimmed away
- too many weak citations were packed together
- the prompt blurred instructions and source text
- the answer over-claimed beyond the retrieved evidence

That is why evaluation needs to score grounding and usefulness, not only fluency.

## Notebook handoff

The generation notebooks now follow the answering pipeline more directly:

- [05_01_query_result_to_answer.ipynb](../notebooks/05_generation/05_01_query_result_to_answer.ipynb)
- [05_02_evidence_selection_and_topk_for_answering.ipynb](../notebooks/05_generation/05_02_evidence_selection_and_topk_for_answering.ipynb)
- [05_03_context_assembly_and_packing.ipynb](../notebooks/05_generation/05_03_context_assembly_and_packing.ipynb)
- [05_04_prompting_and_answer_style.ipynb](../notebooks/05_generation/05_04_prompting_and_answer_style.ipynb)
- [05_05_generation_failures_and_guardrails.ipynb](../notebooks/05_generation/05_05_generation_failures_and_guardrails.ipynb)

Some of these are full walkthroughs today and some are scaffolds, but the stage order is fixed.

## Where to go next

- Continue with [06-evaluation-overview.md](06-evaluation-overview.md) if you want to score retrieval quality, grounding, usefulness, latency, and regression behavior more systematically.
- Read [principles/18-context-assembly-and-packing.md](principles/18-context-assembly-and-packing.md) and [principles/19-prompting-and-answer-synthesis.md](principles/19-prompting-and-answer-synthesis.md) for narrower guidance.
