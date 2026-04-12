# Optimization Overview

This chapter is a roadmap chapter. It explains what comes after evaluation, but it is intentionally docs-only in the current repository. The goal is to give the learning path a clear next step without pretending that all optimization material is already built out.

## The learning question

Once evaluation has shown where the system is weak, which levers can you actually change, and how should you choose them without falling into random trial-and-error tuning?

## The optimization flow

```text
evaluation result
  -> identify the weak stage
  -> choose one controlled lever
  -> rerun the relevant eval
  -> compare quality, latency, and cost
  -> keep or discard the change
```

The key habit is simple: optimize after measurement, not before it.

## Where optimization can happen

EasyRAG exposes several distinct layers where tuning decisions can matter:

- data quality and metadata discipline
- chunking strategy
- embedding model choice
- vector backend or indexing parameters
- retrieval mode selection
- fusion and rerank policy
- evidence selection for generation
- context packing and prompting policy

Each layer changes a different part of the pipeline, so each layer needs the matching evaluation loop.

## Common optimization goals

In practice, you are usually trading between a few clear goals:

- better recall
- better precision
- stronger grounding
- lower latency
- lower cost
- more stable behavior

Those goals do not always move together. A heavier reranker might improve ranking while making latency worse. Larger evidence sets might improve recall while hurting grounding.

## What this chapter is and is not

This chapter is a roadmap, not a finished lab pack.

It is here to make one point explicit: evaluation is not the end of the story. Once you know what is weak, you need a controlled way to improve it.

It is not here to pretend the repository already contains a complete optimization curriculum. That material should grow out of the evaluation notebooks instead of being added as isolated tuning tricks.

## Where to go next

- Use [06-evaluation-overview.md](06-evaluation-overview.md) as the operational prerequisite for this chapter.
- Read [08-system-architecture-overview.md](08-system-architecture-overview.md) if you want to see where those optimization levers sit in the larger system.
