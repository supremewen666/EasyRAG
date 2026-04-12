# Generation Overview

This chapter explains what happens after retrieval has already produced grounded evidence. In a full RAG system, generation is the stage that turns citations, surfaced entities, relation hints, and retrieval metadata into an answer that a human can actually read.

In EasyRAG, that boundary is especially important to keep visible. Today, `EasyRAG.aquery()` returns a structured `QueryResult`. That means the repository already teaches the evidence side of the problem very clearly, while the final answer-synthesis layer is still something you compose downstream.

That is not a limitation for learning. It is a useful separation. It lets you study generation as a second problem built on top of grounded retrieval rather than blending both phases together too early.

## Retrieval Output Is Not Yet An Answer

After retrieval, you already have valuable material:

- citation-ready snippets
- surfaced entities
- surfaced relations
- debugging metadata about rewrite, MQE, and backend choice

But none of those artifacts are automatically the final answer.

They still need to be turned into something that:

- answers the user's actual question
- stays faithful to retrieved evidence
- fits within a prompt budget
- makes citation boundaries easy to inspect

This is why generation should be treated as a distinct stage. Good retrieval improves generation, but it does not replace it.

## The Current Handoff Object Is `QueryResult`

In the current EasyRAG design, `QueryResult` is the handoff object between retrieval and any downstream answer layer.

The most important fields are:

- `citations`: the main evidence payload for answer construction
- `entities`: extra graph-aware context that may help answer framing
- `relations`: relation-level hints that can help explain connections
- `metadata`: diagnostics such as `rewritten_query`, `expanded_queries`, `retrieval_queries`, and `vector_backend`

This means the practical generation question becomes:

> given one `QueryResult`, how should we choose evidence, pack context, prompt a model, and present a grounded answer?

That is the question this chapter introduces.

## Candidate Selection Comes Before Answer Synthesis

One of the most common beginner mistakes in RAG is to pass every retrieved hit directly into the final prompt.

That usually works poorly because:

- some hits are redundant
- some hits are only loosely relevant
- long prompts waste context budget
- too much evidence can blur the main answer path

EasyRAG already performs retrieval-time trimming through fields such as `top_k` and `chunk_top_k`. That helps decide which records survive retrieval.

But generation usually needs a second selection step:

- which citations are strong enough to include
- whether to keep broad context or only the most direct evidence
- whether entities or relations should be shown explicitly
- how much of each snippet to keep

In other words, retrieval chooses candidates for inspection, while generation chooses evidence for answering.

## Context Assembly Is More Than Concatenation

Once you have a smaller evidence set, you still have to assemble context.

That usually includes decisions such as:

- ordering chunks by importance or chronology
- grouping evidence from the same source
- preserving titles and logical paths for traceability
- trimming snippets to fit the prompt budget
- separating evidence from instructions

This is why generation is not just "append top-k chunks into one string."

The arrangement matters because prompt order influences what the answer model notices first. A well-packed context makes the answer easier to ground. A sloppy context makes the model work harder and often increases unsupported claims.

## Prompting And Answer Synthesis

After context assembly, the next step is prompt construction.

A grounded generation prompt usually contains four ingredients:

1. the task instruction
2. the user question
3. the retrieved evidence block
4. the expected answer style

Different answer styles lead to different prompts:

- extractive answers stay very close to citation wording
- abstractive answers summarize across several citations
- citation-aware answers explicitly point back to evidence items

For teaching, citation-aware answers are often the best first step because they keep the evidence boundary visible.

In EasyRAG today, this prompt-building and answer-synthesis layer is something you compose outside the core `aquery()` API. That is exactly what the fundamentals generation notebook demonstrates.

## Good Retrieval Can Still Lead To Bad Generation

Even when retrieval succeeds, generation can still fail.

Common failure modes include:

- overpacking the prompt with too many weak citations
- dropping the most important evidence during trimming
- mixing evidence and instructions so the model ignores source boundaries
- writing claims that are broader than the retrieved snippets justify
- preserving a fluent answer style while losing citation discipline

This is why generation needs its own guardrails. Retrieval quality is necessary, but it is not sufficient.

## What EasyRAG Supports Today

Today, EasyRAG already gives you the main ingredients needed for grounded answer composition:

- document ingestion and chunking
- retrieval over chunks, summaries, and graph signals
- surfaced citations, entities, relations, and metadata
- zero-key teaching paths and provider-backed retrieval paths

What it does not yet present as a stable built-in public layer is:

- a final `AnswerParam` API
- a canonical `AnswerResult` object
- a built-in context packer
- a built-in prompt builder
- a built-in answer synthesizer

That distinction matters. This chapter is about where generation fits in the learning path, not about claiming that EasyRAG already ships a full answer-generation subsystem.

## Why This Separation Is Still Useful

The current boundary is actually a helpful teaching choice.

It lets you study the flow in two clean stages:

1. retrieval: produce grounded evidence
2. generation: turn grounded evidence into a user-facing answer

That separation makes it easier to debug:

- if the evidence is wrong, the problem is mostly retrieval
- if the evidence is good but the answer is weak, the problem is mostly generation

This is one of the clearest lessons carried over from `rag-from-scratch`: you learn faster when evidence selection and answer synthesis stay inspectable instead of being hidden inside one opaque call.

## How This Chapter Connects To The Notebook

The most direct companion to this overview is:

- [fundamentals/05_generation_basics.ipynb](../notebooks/fundamentals/05_generation_basics.ipynb)

That notebook keeps the current EasyRAG boundary honest. It starts from a real `QueryResult`, then shows how to:

- inspect the grounded evidence
- select a smaller answer-ready citation set
- pack those citations into a context block
- build a simple prompt
- synthesize a citation-aware answer with a deterministic teaching helper

The point is not to present the perfect answer stack. The point is to make the handoff from retrieval to generation concrete.

## Where To Go Next

After this overview, the best next steps are:

- run [fundamentals/05_generation_basics.ipynb](../notebooks/fundamentals/05_generation_basics.ipynb) to see retrieval outputs turned into a simple grounded answer
- read [principles/18-generation-foundations.md](principles/18-generation-foundations.md) for the conceptual boundary between evidence and answers
- read [principles/19-top-k-and-candidate-selection.md](principles/19-top-k-and-candidate-selection.md) for evidence selection strategy
- read [principles/20-context-assembly-and-packing.md](principles/20-context-assembly-and-packing.md) for context-budget thinking
- read [principles/21-prompting-and-answer-synthesis.md](principles/21-prompting-and-answer-synthesis.md) for prompt-structure ideas
- read [principles/22-generation-failures-and-guardrails.md](principles/22-generation-failures-and-guardrails.md) for failure analysis
- read [engineering/26-generation-pipeline.md](engineering/26-generation-pipeline.md) for how a future built-in generation layer could extend the current retrieval core

If `04-retrieval-overview.md` explained how a question becomes grounded evidence, this chapter should explain how grounded evidence becomes the input to answer generation.
