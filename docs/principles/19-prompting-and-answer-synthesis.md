# Prompting And Answer Synthesis

## What Problem This Page Answers

This page answers how a packed evidence set becomes a grounded answer. It focuses on prompt structure and synthesis behavior rather than on model-provider specifics.

## Core Idea Or Mechanism

Answer synthesis combines the user question, answer instructions, and retrieved evidence into a prompt that encourages grounded generation. Prompt structure shapes whether the model behaves extractively, abstractively, or in a citation-aware style.

## Tradeoffs / Failure Modes

Prompting can improve clarity and grounding, but it cannot fully compensate for weak evidence. Loose instructions may invite hallucination, while overly rigid prompting can produce brittle or under-informative answers.

## Where To Go Next

- Return to [overview](../00-overview.md) for the phase-level map.
- Pair this page with [generation overview](../05-generation-overview.md).
- Continue in the notebook [05_04_prompting_and_answer_style.ipynb](../../notebooks/05_generation/05_04_prompting_and_answer_style.ipynb).
