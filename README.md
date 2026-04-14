# EasyRAG

![logo](./new_logo.png)

EasyRAG is a lightweight RAG project built for both learning and hands-on engineering. It breaks a small RAG system into visible stages: data loading, indexing, retrieval, generation, evaluation, optimization, and system architecture. Those stages are unpacked step by step through `docs/`, Jupyter notebooks, and a compact, readable codebase.

If you want to learn more than "how to call a black-box RAG API" and actually see the intermediate objects, tradeoffs, and implementation points, this repository was made for that.

## What makes this project useful

- Teaching first: the content follows the pipeline in order, so it is easy to build a full mental model of RAG from scratch.
- Observable artifacts: `Document`, chunks, summaries, vectors, graph state, citations, and `QueryResult` objects are kept as inspectable as possible.
- Docs and experiments mirror each other: `docs/` explains the concepts and stage-level mental models, while `notebooks/` covers the same topics through runnable or partially scaffolded experiments.
- Small and readable code: the main entry points are concentrated around a few objects such as `EasyRAG`, `QueryParam`, `ChunkingConfig`, and `QueryResult`.
- Local-first, but still extensible: the default setup is simple enough for teaching, while still leaving room for swappable backends, provider hooks, and knowledge graph curation.
- You can start without API keys: some notebooks include deterministic stubs or fallback paths so you can learn the structure first and plug in real models later.

## Who this is for

- Learners who want a systematic understanding of the core RAG pipeline
- Developers who want a RAG codebase that is easier to read than a large all-in-one framework
- Educators who want course material, experiments, and implementation to live in one repository
- Anyone who wants to teach or study chunking, hybrid retrieval, reranking, grounding, and evaluation in a more focused way

## What you will learn

- How raw source material becomes a canonical `Document`
- How chunking, embeddings, vector indexing, and graph curation fit together in the indexing stage
- How query normalization, rewriting, multi-query retrieval, fusion, reranking, and hydration fit into retrieval
- How retrieval results flow into answer generation, prompting, and guardrails
- Why evaluation should sit on the main path, not as an afterthought
- How local backends, production backends, observability, and fallback belong in the same system-level mental model

## What this project is not

- It is not a one-click production RAG platform
- It is not a giant abstraction layer that hides the important details inside a framework
- It is not a course repo that gives you notebooks without showing where the engineering code lives

EasyRAG is closer to a small RAG reference project that you can teach from, take apart, and extend.

## Current status

- The main `docs/` structure is stable and ready for sequential reading
- The numbering and narrative flow in `notebooks/` are stable, though completion levels still vary across notebooks
- `scripts/build_index.py` is already usable as a real indexing entry point
- `examples/` is still mostly placeholder material, so notebooks remain the main practice path for now
- `01-rag-basics` and `07-optimization-overview` are currently docs-only sections

In practice, that means the repository is already a good fit for guided study and code reading, while deeper experiment coverage is still being filled in.

## Quick start

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For development dependencies:

```bash
pip install -e ".[dev]"
```

Optional backend dependencies:

```bash
pip install -e ".[hnsw]"
pip install -e ".[postgres]"
```

The project currently requires Python `>=3.11`.

### 2. Best first entry point

If you want to run the smallest complete loop first, this is the path I recommend:

1. Read [docs/00-overview.md](docs/00-overview.md)
2. Run [notebooks/00_overview/00_01_quickstart_end_to_end.ipynb](notebooks/00_overview/00_01_quickstart_end_to_end.ipynb)
3. Then read [notebooks/00_overview/00_02_observing_rag_artifacts.ipynb](notebooks/00_overview/00_02_observing_rag_artifacts.ipynb)

The point of this path is not to squeeze out the strongest answer quality on day one. It is to make one full lifecycle visible:

`initialize -> insert -> query -> inspect -> finalize`

### 3. Build a local index

The repository already includes a real index maintenance script:

```bash
python scripts/build_index.py --action rebuild
```

Rebuild only one document:

```bash
python scripts/build_index.py --action rebuild --doc-id <doc_id>
```

Delete the indexed artifacts for one document:

```bash
python scripts/build_index.py --action delete --doc-id <doc_id>
```

### 4. Plug in real models

Many notebooks start with deterministic stubs or fallback backends so you can build the right mental model first. When you are ready to connect real providers, just configure OpenAI-compatible environment variables. The project already exposes provider hooks for querying, embeddings, reranking, and KG extraction.

## Three suggested learning paths

### Path A: learning RAG systematically for the first time

Read the main line in order:

1. [docs/00-overview.md](docs/00-overview.md)
2. [docs/01-rag-basics.md](docs/01-rag-basics.md)
3. [docs/02-data-loading-overview.md](docs/02-data-loading-overview.md)
4. [docs/03-indexing-overview.md](docs/03-indexing-overview.md)
5. [docs/04-retrieval-overview.md](docs/04-retrieval-overview.md)
6. [docs/05-generation-overview.md](docs/05-generation-overview.md)
7. [docs/06-evaluation-overview.md](docs/06-evaluation-overview.md)
8. [docs/07-optimization-overview.md](docs/07-optimization-overview.md)
9. [docs/08-system-architecture-overview.md](docs/08-system-architecture-overview.md)

### Path B: learning mainly through notebooks

These notebooks make a good starting set:

- [00_01_quickstart_end_to_end.ipynb](notebooks/00_overview/00_01_quickstart_end_to_end.ipynb): run the smallest end-to-end loop
- [03_07_build_index_pipeline.ipynb](notebooks/03_indexing/03_07_build_index_pipeline.ipynb): see exactly what the indexing pipeline writes out
- [04_04_hybrid_metadata_filter_and_modes.ipynb](notebooks/04_retrieval/04_04_hybrid_metadata_filter_and_modes.ipynb): move into practical retrieval mode combinations
- [04_05_fusion_rerank_and_topk.ipynb](notebooks/04_retrieval/04_05_fusion_rerank_and_topk.ipynb): understand how the candidate set changes
- [06_05_eval_driven_debugging.ipynb](notebooks/06_evaluation/06_05_eval_driven_debugging.ipynb): turn evaluation signals into debugging actions

### Path C: understanding the system mainly through code

I recommend reading the code in this order:

1. [easyrag/rag/orchestrator.py](easyrag/rag/orchestrator.py)
2. [easyrag/rag/indexing/](easyrag/rag/indexing)
3. [easyrag/rag/retrieval/](easyrag/rag/retrieval)
4. [easyrag/rag/knowledge/](easyrag/rag/knowledge)
5. [easyrag/rag/storage/](easyrag/rag/storage)

Supporting docs:

- [docs/engineering/20-code-map.md](docs/engineering/20-code-map.md)
- [docs/engineering/21-indexing-pipeline.md](docs/engineering/21-indexing-pipeline.md)
- [docs/engineering/22-retrieval-pipeline.md](docs/engineering/22-retrieval-pipeline.md)
- [docs/engineering/23-generation-pipeline.md](docs/engineering/23-generation-pipeline.md)
- [docs/engineering/24-graph-curation-pipeline.md](docs/engineering/24-graph-curation-pipeline.md)
- [docs/engineering/25-local-vs-production-backends.md](docs/engineering/25-local-vs-production-backends.md)
- [docs/engineering/26-extension-guide.md](docs/engineering/26-extension-guide.md)

## Content map

| Module | What you will find | Best time to open it |
| --- | --- | --- |
| [docs/README.md](docs/README.md) | Master index for all documentation | When you want to follow the course-style main path |
| [notebooks/README.md](notebooks/README.md) | Stage-based navigation for all notebooks | When you want to run experiments directly |
| [docs/principles/](docs/principles) | Topic-focused method notes such as chunking, hybrid retrieval, packing, and evaluation | When you want to go deep on one subject |
| [docs/engineering/](docs/engineering) | Code structure, runtime flow, and extension points | When you want to move from teaching material into implementation details |
| [scripts/build_index.py](scripts/build_index.py) | Index build and maintenance script | When you want to move from demo mode to a real repo-level workflow |
| [sample_data/](sample_data) | Small sample corpora | When you want to inspect artifacts on a tiny dataset |
| [examples/README.md](examples/README.md) | Example script directory | When you want to see where future script-based entry points may go |

## Main course map

| Stage | Docs | Notebook / format | Keywords |
| --- | --- | --- | --- |
| 00 Overview | [00-overview.md](docs/00-overview.md) | [00_01](notebooks/00_overview/00_01_quickstart_end_to_end.ipynb), [00_02](notebooks/00_overview/00_02_observing_rag_artifacts.ipynb) | minimum viable loop, artifact inspection |
| 01 RAG basics | [01-rag-basics.md](docs/01-rag-basics.md) | docs-only | `Document`, `QueryResult`, stage boundaries |
| 02 Data loading | [02-data-loading-overview.md](docs/02-data-loading-overview.md) | [02_01-02_05](notebooks/02_data_loading) | repo loading, manual docs, PDF, normalization |
| 03 Indexing | [03-indexing-overview.md](docs/03-indexing-overview.md) | [03_01-03_08](notebooks/03_indexing) | chunking, embeddings, vector index, workspace artifacts |
| 04 Retrieval | [04-retrieval-overview.md](docs/04-retrieval-overview.md) | [04_01-04_07](notebooks/04_retrieval) | preprocessing, rewrite, hybrid, fusion, rerank, hydration |
| 05 Generation | [05-generation-overview.md](docs/05-generation-overview.md) | [05_01-05_05](notebooks/05_generation) | evidence selection, packing, prompting, guardrails |
| 06 Evaluation | [06-evaluation-overview.md](docs/06-evaluation-overview.md) | [06_01-06_06](notebooks/06_evaluation) | tiny eval set, retrieval metrics, grounding, regression |
| 07 Optimization | [07-optimization-overview.md](docs/07-optimization-overview.md) | docs-only | tuning roadmap, working backward from evaluation |
| 08 Architecture | [08-system-architecture-overview.md](docs/08-system-architecture-overview.md) | [08_01-08_03](notebooks/08_system_architecture) | code map, backends, observability, fallback |

## Core teaching objects

If you only want to remember a few names at first, start with these:

- `EasyRAG`
- `QueryParam`
- `ChunkingConfig`
- `QueryResult`
- `KGExtractionConfig`

These objects form the shared backbone across the docs, notebooks, and implementation. `EasyRAG`, `QueryParam`, `QueryResult`, and `KGExtractionConfig` are the main user-facing interfaces. `ChunkingConfig` is especially important if you want to understand the indexing stage well.

## Repository structure

```text
EasyRAG/
├── easyrag/                # Core library implementation
│   ├── config/             # Environment, model, and storage config
│   └── rag/
│       ├── indexing/       # loading / prepare / chunking / ingest
│       ├── retrieval/      # preprocess / query modes / fusion / hydration
│       ├── knowledge/      # entity / relation extraction and sync
│       └── storage/        # local and production-style storage backends
├── docs/                   # Main docs, principles, and engineering notes
├── notebooks/              # Teaching experiments aligned with the docs
├── scripts/                # Repo-level index maintenance scripts
├── sample_data/            # Small sample corpora
├── examples/               # Reserved script examples
└── tests/                  # Tests focused on core behavior
```

## Development and tests

Run the current core test set:

```bash
python -m pytest -q tests/test_config.py tests/test_rag_providers.py tests/test_rag_retriever.py tests/test_rag_graph_ops.py tests/test_rag_backends.py
```

If you plan to keep adding material to this repository, this rule of thumb will help:

- Put new teaching explanations in `docs/`
- Put new experiments in `notebooks/`
- Put reusable implementation into `easyrag/`

That keeps the boundary between the teaching narrative and the engineering interface clear.

## Roadmap

- Add deeper experiment coverage for evaluation and optimization
- Turn more retrieval and generation notebooks from scaffolds into comparable, reproducible experiments
- Add more complete example scripts
- Expand the sample data, exercises, and teaching tasks
- Keep improving production concerns such as observability, fallback, and latency/cost tracking

## Related indexes

- [docs/README.md](docs/README.md)
- [notebooks/README.md](notebooks/README.md)
- [examples/README.md](examples/README.md)
- [sample_data/README.md](sample_data/README.md)

## Inspiration

The structure of this README borrows good ideas from several strong teaching repositories:

- [pguso/rag-from-scratch](https://github.com/pguso/rag-from-scratch): learning the pipeline in order and keeping intermediate artifacts visible
- [datawhalechina/hello-agents](https://github.com/datawhalechina/hello-agents): a low-friction introduction that makes it clear who the project is for, what you can learn, and how to start
- [datawhalechina/all-in-rag](https://github.com/datawhalechina/all-in-rag): content maps, stage-based decomposition, and a more systematic course perspective
