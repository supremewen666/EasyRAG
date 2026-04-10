"""Runtime and repository path configuration."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional at import time.
    load_dotenv = None


def _discover_project_root() -> Path:
    """Best-effort project root discovery used before env vars are loaded."""

    return Path(__file__).resolve().parent.parent.parent


def load_environment() -> Path:
    """Load the project's `.env` file once and return the effective project root."""

    project_root = _discover_project_root()
    env_path = project_root / ".env"
    if load_dotenv is not None and env_path.exists():
        load_dotenv(env_path, override=False)
    return project_root


PROJECT_ROOT = load_environment()


def get_repo_root() -> Path:
    """Return the repository root used for document discovery and local storage."""

    return Path(os.getenv("EASYRAG_REPO_ROOT", PROJECT_ROOT)).resolve()


def get_data_dir() -> Path:
    """Return the writable local data directory for indexes and fallback memory."""

    return Path(os.getenv("EASYRAG_DATA_DIR", get_repo_root() / ".easyrag")).resolve()
