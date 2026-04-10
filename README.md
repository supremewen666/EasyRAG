# EasyRAG

EasyRAG is a standalone repository knowledge library for local document indexing, hybrid retrieval, and lightweight knowledge graph curation.

This repository contains only the EasyRAG core:

- repository document loading, including text-first PDF support
- chunking, indexing, retrieval, and reranking hooks
- local JSON / NumPy / NetworkX storage backends
- optional PostgreSQL + Qdrant production storage backends
- a small CLI for building and maintaining the local index
- a lightweight tool wrapper for agent-style search integrations

It does not include the old Streamlit UI, FastAPI service surface, GitHub MCP integration, or memory layer.

## Install

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the core package:

```bash
pip install -e .
```

Install test dependencies:

```bash
pip install -e ".[dev]"
```

Optional extras:

```bash
pip install -e ".[hnsw]"
pip install -e ".[postgres]"
```

## Configuration

Copy the example environment file if you want local defaults:

```bash
cp .env.example .env
```

Important variables:

- `EASYRAG_REPO_ROOT`: repository root used for document discovery
- `EASYRAG_DATA_DIR`: local data directory, defaults to `<repo>/.easyrag`
- `EASYRAG_INDEX_PATH`: compatibility JSON snapshot path
- `EASYRAG_WORKING_DIR`: storage root for workspace data
- `EASYRAG_WORKSPACE`: active workspace name
- `EASYRAG_STORAGE_BACKEND`: `local` or `postgres_qdrant`
- `OPENAI_API_KEY`: enables query rewriting, embeddings, reranking, and KG extraction through OpenAI-compatible APIs
- `EASYRAG_QUERY_MODEL_NAME`, `EASYRAG_EMBEDDING_MODEL_NAME`, `EASYRAG_RERANK_MODEL_NAME`, `EASYRAG_KG_MODEL_NAME`: role-specific model overrides
- `EASYRAG_QUERY_BASE_URL`, `EASYRAG_EMBEDDING_BASE_URL`, `EASYRAG_RERANK_BASE_URL`, `EASYRAG_KG_BASE_URL`: optional role-specific base URLs

Production backend variables:

- `EASYRAG_POSTGRES_DSN`
- `EASYRAG_QDRANT_URL`
- `EASYRAG_QDRANT_API_KEY`
- `EASYRAG_QDRANT_COLLECTION_PREFIX`

## Build The Index

Build or refresh the local workspace:

```bash
python scripts/build_index.py
```

Target specific documents:

```bash
python scripts/build_index.py --action rebuild --doc-id doc::docs-architecture-md
python scripts/build_index.py --action delete --doc-id doc::docs-architecture-md
```

The CLI writes storage files under `.easyrag/rag_storage/<workspace>/` by default and also emits a compatibility snapshot at `.easyrag/rag_index.json`.

## Python Usage

```python
import asyncio

from easyrag import EasyRAG, QueryParam


async def main() -> None:
    rag = EasyRAG()
    await rag.initialize_storages()
    try:
        await rag.ainsert(
            "# Architecture\nEasyRAG uses semantic retrieval and query rewriting.\n",
            ids=["doc::architecture"],
            file_paths=["docs/architecture.md"],
        )
        result = await rag.aquery(
            "How does retrieval work?",
            QueryParam(mode="hybrid", top_k=8, chunk_top_k=5),
        )
        print(result.citations)
    finally:
        await rag.finalize_storages()


asyncio.run(main())
```

Top-level exports:

- `easyrag.EasyRAG`
- `easyrag.QueryParam`
- `easyrag.QueryResult`
- `easyrag.KGExtractionConfig`
- `easyrag.tools.create_search_docs_tool`
- `easyrag.tools.search_docs_tool`

## Project Layout

- `easyrag/rag/`: core orchestrator, indexing, retrieval, knowledge, and storage
- `easyrag/config/`: environment-backed configuration helpers
- `easyrag/support/`: optional dependency fallbacks
- `easyrag/tools.py`: simple search-tool wrappers
- `scripts/build_index.py`: local indexing CLI
- `tests/`: focused coverage for config, providers, retrieval, graph ops, and backend bundle resolution

## Tests

Run the focused standalone suite:

```bash
python -m pytest -q tests/test_config.py tests/test_rag_providers.py tests/test_rag_retriever.py tests/test_rag_graph_ops.py tests/test_rag_backends.py
```
