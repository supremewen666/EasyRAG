# Generation Overview

This chapter explains what happens after retrieval has already produced grounded evidence. In a full RAG system, generation is the stage that turns citations, surfaced entities, relation hints, and retrieval metadata into an answer that a human can actually read.

## The learning question

Once retrieval has already done its job, how should you select evidence, pack context, prompt a model, and keep the answer tied back to real citations?

## The generation flow

```text
QueryResult
  -> evidence selection
  -> context assembly
  -> prompt construction
  -> answer synthesis
  -> grounding checks
```

That flow is downstream of retrieval, not a replacement for it.

## The current handoff is `QueryResult`

In EasyRAG today, `EasyRAG.aquery()` returns a structured `QueryResult`. That means the repository already teaches the evidence side of the problem clearly, while the final answer layer is something you compose downstream.

That boundary is useful for learning because it keeps the evidence visible. You can inspect the citations before you decide how to answer.

## Candidate selection comes before prompt writing

One common beginner mistake is to pass every retrieved hit straight into the final prompt. That usually fails because:

- some hits are redundant
- some hits are only loosely relevant
- large evidence sets blur the answer path
- prompt budget gets spent on weak context

Retrieval chooses candidates for inspection. Generation still has to choose which evidence survives into the final prompt.

## Context assembly is a separate decision

Even after you choose the evidence set, you still need to decide how to present it:

- order by score or by source
- group related snippets together or not
- clip long snippets
- preserve titles and paths for traceability
- separate evidence from instructions clearly

Prompt quality depends on those assembly choices as much as on the raw citation set.

## Good retrieval can still lead to bad generation

Generation can fail even when retrieval looked reasonable:

- the best citation was trimmed away
- too many weak citations were packed together
- the prompt blurred source text and instruction text
- the answer sounded good but over-claimed beyond the evidence

That is why generation needs its own labs, and why evaluation has to look at grounding instead of only fluency.

## Notebook handoff

The direct notebook companions to this chapter are:

- [05_01_generation_basics.ipynb](../notebooks/05_generation/05_01_generation_basics.ipynb), which walks through retrieval-to-answer handoff on a tiny corpus
- [05_02_top_k_selection_lab.ipynb](../notebooks/05_generation/05_02_top_k_selection_lab.ipynb), [05_03_context_packing_lab.ipynb](../notebooks/05_generation/05_03_context_packing_lab.ipynb), [05_04_prompting_and_answer_style_lab.ipynb](../notebooks/05_generation/05_04_prompting_and_answer_style_lab.ipynb), and [05_05_generation_failure_cases.ipynb](../notebooks/05_generation/05_05_generation_failure_cases.ipynb) for narrower comparisons

## Where to go next

- Continue with [06-evaluation-overview.md](06-evaluation-overview.md) if you want to score retrieval quality, grounding, and answer usefulness in a more systematic way.
- Read [principles/20-context-assembly-and-packing.md](principles/20-context-assembly-and-packing.md) and [principles/21-prompting-and-answer-synthesis.md](principles/21-prompting-and-answer-synthesis.md) for more focused guidance.
