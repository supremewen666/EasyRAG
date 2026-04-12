# Optimization Overview

This chapter is a roadmap chapter. It explains what comes after evaluation, but it is intentionally docs-only in the current repository. The goal is to make the next step concrete without pretending that every optimization lab already exists.

## The learning question

Once evaluation has shown where the system is weak, which levers can you actually change, and how do you choose them without drifting into random trial-and-error tuning?

## The optimization flow

```text
evaluation result
  -> identify the weak stage
  -> choose one controlled lever
  -> rerun the relevant evaluation slice
  -> compare quality, latency, and cost
  -> keep or discard the change
```

The key habit is simple: optimize after measurement, not before it.

## What you will learn

- which layers of the EasyRAG pipeline are realistic tuning targets
- how to separate quality tuning from latency and cost tuning
- why each tuning pass should have a matching evaluation loop
- what later optimization notebooks should eventually expand into

## Optimization layers

### 1. Data normalization and cleaning

Sometimes the best optimization is earlier than retrieval:

- better normalization
- better boilerplate removal
- cleaner metadata
- more stable document IDs

If the inputs improve, later retrieval often improves without any retrieval-specific change.

### 2. Chunking

Chunk tuning changes the retrieval unit itself:

- chunk size
- overlap
- heading awareness
- parent-child strategies
- semantic versus structural chunking

This is often the first place to revisit when recall feels noisy.

### 3. Embedding and index tuning

Once chunking is stable, you can tune:

- embedding model choice
- embedding cache policy
- vector index parameters
- incremental versus full rebuild behavior
- namespace and metadata indexing choices

### 4. Retrieval tuning

This is where many industrial systems spend most of their time:

- query normalization policy
- rewrite or multi-query policy
- hybrid retrieval balance
- metadata filtering
- rerank depth
- thresholding and fallback behavior

### 5. Prompt and answer tuning

If retrieval is already healthy, the next gains may come from:

- evidence selection
- context packing
- prompt format
- abstention rules
- structured output policy

### 6. Latency and cost tuning

Not every improvement is about answer quality:

- cache hit rate
- expensive provider calls
- rerank depth versus latency
- adaptive top-k
- batching and concurrency

Those changes still need evaluation. They just optimize a different objective.

## Industrial optimization patterns

Common optimization patterns in production systems include:

- normalization tuning before indexing
- chunk-strategy tuning from retrieval failures
- score calibration and threshold tuning
- metadata-filter refinement
- rerank depth tuning
- adaptive top-k
- cache strategy tuning
- multi-stage retrieval with graceful fallback
- regression checks before rollout

The main discipline is to change one lever at a time and rerun the relevant evaluation slice.

## What this chapter is and is not

This chapter is a roadmap, not a finished notebook set.

It is here to make one point explicit: evaluation is not the end of the story. Once you know what is weak, you need a controlled way to improve it. The future notebook work should grow out of the six layers above rather than appear as isolated tuning tricks.

## Where to go next

- Use [06-evaluation-overview.md](06-evaluation-overview.md) as the prerequisite for this chapter.
- Read [08-system-architecture-overview.md](08-system-architecture-overview.md) if you want to see where those optimization levers sit in the larger system.
