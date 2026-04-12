# Retrieval Overview

This chapter explains what happens after the index already exists. In EasyRAG, retrieval is the phase that turns a user question into grounded, inspectable outputs such as citations, surfaced entities, relation hits, and diagnostics metadata.

The key point is that retrieval is not just "run vector search." It is a pipeline with several stages, and each stage changes what evidence the system ultimately returns.

## Retrieval Starts With A Question, Not With A Chunk

The retrieval phase begins when a user asks a question, but the system does not send that raw string directly to one search function and stop there.

In EasyRAG, the pipeline can include:

- query normalization
- optional rewriting
- optional multi-query expansion (MQE)
- mode-specific retrieval
- rank fusion
- hydration
- citation assembly

This means the retrieval story is about transformation as much as it is about search.

## Query Preprocessing

Before retrieval runs, EasyRAG creates a prepared query representation.

The preprocessing layer can:

- normalize whitespace and punctuation noise
- rewrite the question into a retrieval-oriented form
- generate multiple query variants
- collect the final list of retrieval queries that will actually be used

This is important because retrieval often improves when the question asked by the user is converted into a form that better matches the indexed corpus.

The result of this stage is visible through retrieval metadata such as:

- `normalized_query`
- `rewritten_query`
- `expanded_queries`
- `retrieval_queries`

That metadata is one of the easiest ways to debug retrieval behavior.

## The Five Retrieval Modes

EasyRAG exposes five named retrieval modes through `QueryParam.mode`.

### `naive`

`naive` retrieval searches chunk vectors directly. This is the simplest mode and the easiest one to understand first.

Use it when you want the most direct chunk-similarity baseline.

### `local`

`local` retrieval focuses on query-time entities and their nearby chunk neighborhoods. It combines entity-oriented graph context with dense chunk backfill.

Use it when entity-centric locality matters more than broad document coverage.

### `global`

`global` retrieval emphasizes broader context. It can use summaries, central entities, and graph neighborhoods to retrieve a wider view of the indexed knowledge.

Use it when the question is broad, architectural, or likely to benefit from document-level context.

### `hybrid`

`hybrid` combines local and global retrieval signals. This is often a good default when you want more than one retrieval perspective without adding every possible signal.

### `mix`

`mix` extends the combination by including naive chunk retrieval alongside the local and global channels. It is the broadest built-in retrieval combination.

This mode can optionally benefit from reranking when a reranker is configured.

## Why Multiple Modes Exist

The five modes are not five brand-new products. They are different ways of looking at the same indexed workspace.

The intuition is:

- chunk similarity alone is sometimes enough
- entity neighborhoods sometimes help recover missing context
- summary-level or central-node context sometimes helps broad questions
- combining channels can reduce brittleness

This is why retrieval in EasyRAG is framed as a composition problem rather than a single search primitive.

## Fusion And Selection

When more than one retrieval channel is used, EasyRAG needs a way to combine ranked records.

At a high level, the system supports:

- reciprocal-rank-style fusion
- weighted score accumulation
- trimming to a final set of hydrated records

The important teaching lesson is not the exact formula. It is the idea that multiple ranked lists can be merged into one more robust candidate set before final selection.

This is also why small corpora can make several modes converge: if the corpus is tiny and the strongest evidence is obvious, different retrieval channels often surface the same records. That is expected behavior, not a sign that the mode comparison failed.

## Hydration And Citations

Retrieval candidates are not immediately returned as user-facing outputs. First, EasyRAG hydrates the ranked records back into richer data structures.

Hydration is responsible for turning ranked IDs into records with:

- text
- title
- path
- metadata
- score
- backend information

After hydration, EasyRAG builds citation payloads. Those citations are the clearest proof that retrieval is grounded:

- each citation has a source type
- a title
- a location
- a text snippet

This is why the notebooks emphasize citations rather than only raw scores. Citations are what a human reader can actually inspect.

## What `QueryResult` Carries

The final retrieval package is `QueryResult`.

For learning purposes, the most important fields are:

- `citations`: grounded snippets ready for inspection
- `entities`: entity labels surfaced during retrieval
- `relations`: relation hits with scores and endpoints
- `metadata`: diagnostics about preprocessing, chunk strategies, rerank status, and vector backend

One useful boundary to keep in mind: EasyRAG currently teaches the grounded retrieval core. `QueryResult` is a structured retrieval output, not a final answer-generation wrapper.

## Why Retrieval Is More Than Vector Search

Vector search is an important part of modern retrieval, but EasyRAG deliberately teaches retrieval as a larger system:

- preprocessing changes the search inputs
- retrieval modes choose which indexed views to emphasize
- fusion combines ranked evidence
- hydration turns records into inspectable outputs
- graph signals can add another layer of context

If you only look at the vector backend, you will miss most of the teaching value of the retrieval pipeline.

## Rerank And Backend Notes

At a high level, reranking is an optional later-stage refinement step. When configured, it can reorder already retrieved candidates rather than replace the retrieval process itself.

Backend choice matters too:

- in richer provider setups, retrieval may use dense embedding backends
- in zero-key teaching setups, retrieval may fall back to token-based behavior

The mental model should stay the same in both cases. The scoring details change, but the retrieval pipeline structure does not.

## How This Chapter Connects To The Notebooks

This overview connects most directly to:

- [fundamentals/02_query_modes.ipynb](../notebooks/fundamentals/02_query_modes.ipynb), which compares the five retrieval modes on one small corpus
- [fundamentals/04_knowledge_graph.ipynb](../notebooks/fundamentals/04_knowledge_graph.ipynb), which shows how automatically extracted graph signals influence graph-aware retrieval

Those notebooks exist to make this chapter concrete:

- the query-modes notebook compares outputs side by side
- the knowledge-graph notebook shows where entities and relations appear in practice

## Where To Go Next

After this overview, choose your next layer of depth:

- run [fundamentals/02_query_modes.ipynb](../notebooks/fundamentals/02_query_modes.ipynb) for a practical mode comparison
- run [fundamentals/04_knowledge_graph.ipynb](../notebooks/fundamentals/04_knowledge_graph.ipynb) for graph-assisted retrieval
- read [principles/10-query-preprocessing.md](principles/10-query-preprocessing.md) for the preprocessing layer
- read [principles/13-hybrid-retrieval-and-fusion.md](principles/13-hybrid-retrieval-and-fusion.md) for the theory behind retrieval composition
- read [engineering/22-retrieval-pipeline.md](engineering/22-retrieval-pipeline.md) for a code-oriented view of the retrieval implementation

If `03-indexing-overview.md` explained how knowledge gets prepared, this chapter should explain how that prepared knowledge gets turned back into grounded evidence for a question.
