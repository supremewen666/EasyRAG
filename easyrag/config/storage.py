"""Storage and persistence configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path

from easyrag.config.runtime import get_data_dir


def get_rag_index_path() -> Path:
    """Return the on-disk location for the lightweight document index."""

    return Path(
        os.getenv("EASYRAG_INDEX_PATH", get_data_dir() / "rag_index.json")
    ).resolve()


def get_rag_working_dir() -> Path:
    """Return the default EasyRAG-style storage root directory."""

    return Path(
        os.getenv("EASYRAG_WORKING_DIR", get_data_dir() / "rag_storage")
    ).resolve()


def get_rag_workspace() -> str:
    """Return the active workspace name for the repository knowledge store."""

    return os.getenv("EASYRAG_WORKSPACE", "default").strip() or "default"


def get_rag_storage_backend() -> str:
    """Return the configured storage backend bundle for EasyRAG."""

    return os.getenv("EASYRAG_STORAGE_BACKEND", "local").strip() or "local"


def get_postgres_dsn() -> str:
    """Return the configured PostgreSQL DSN for production RAG storage."""

    return os.getenv("EASYRAG_POSTGRES_DSN", "").strip()


def get_qdrant_url() -> str:
    """Return the configured Qdrant base URL for production vector storage."""

    return os.getenv("EASYRAG_QDRANT_URL", "").strip()


def get_qdrant_api_key() -> str:
    """Return the configured Qdrant API key."""

    return os.getenv("EASYRAG_QDRANT_API_KEY", "").strip()


def get_qdrant_collection_prefix() -> str:
    """Return the collection prefix used for Qdrant namespaces."""

    return os.getenv("EASYRAG_QDRANT_COLLECTION_PREFIX", "easyrag").strip() or "easyrag"
