"""Model and provider configuration helpers."""

from __future__ import annotations

import os


def get_default_model() -> str:
    """Return the default chat model identifier for OpenAI-compatible calls."""

    return os.getenv("EASYRAG_MODEL", "openai:gpt-4.1-mini")


def get_model_name() -> str:
    """Return the raw model name sent to an OpenAI-compatible chat endpoint."""

    return os.getenv("EASYRAG_MODEL_NAME", get_default_model().split(":", 1)[-1])


def _get_role_model_name(env_name: str, default: str) -> str:
    """Return a role-specific model name with a fallback default."""

    return os.getenv(env_name, default).strip() or default


def get_query_model_name() -> str:
    """Return the model used for query rewriting and MQE generation."""

    return _get_role_model_name("EASYRAG_QUERY_MODEL_NAME", get_model_name())


def get_embedding_model_name() -> str:
    """Return the embedding model used by the EasyRAG dense vector layer."""

    return _get_role_model_name("EASYRAG_EMBEDDING_MODEL_NAME", "qwen3-embedding")


def get_rerank_model_name() -> str:
    """Return the reranker model used by the EasyRAG rerank stage."""

    return _get_role_model_name("EASYRAG_RERANK_MODEL_NAME", "qwen3-rerank")


def get_kg_model_name() -> str:
    """Return the model used by the KG extraction stage."""

    return _get_role_model_name("EASYRAG_KG_MODEL_NAME", get_query_model_name())


def get_openai_api_key() -> str:
    """Return the API key used by the OpenAI-compatible chat client."""

    return os.getenv("OPENAI_API_KEY", "").strip()


def _get_role_api_key(env_name: str, *, fallback_names: tuple[str, ...] = ()) -> str:
    """Return a role-specific API key with shared and vendor fallbacks."""

    value = os.getenv(env_name, "").strip()
    if value:
        return value
    for fallback_name in fallback_names:
        value = os.getenv(fallback_name, "").strip()
        if value:
            return value
    return get_openai_api_key()


def get_query_api_key() -> str:
    """Return the API key used for query rewriting and MQE generation."""

    return _get_role_api_key("EASYRAG_QUERY_API_KEY")


def get_embedding_api_key() -> str:
    """Return the API key used for embedding generation."""

    return _get_role_api_key(
        "EASYRAG_EMBEDDING_API_KEY",
        fallback_names=("DASHSCOPE_API_KEY",),
    )


def get_rerank_api_key() -> str:
    """Return the API key used for reranking."""

    return _get_role_api_key(
        "EASYRAG_RERANK_API_KEY",
        fallback_names=("DASHSCOPE_API_KEY",),
    )


def get_kg_api_key() -> str:
    """Return the API key used for KG extraction."""

    return _get_role_api_key("EASYRAG_KG_API_KEY")


def get_openai_base_url() -> str | None:
    """Return the optional OpenAI-compatible base URL."""

    value = os.getenv("OPENAI_BASE_URL", "").strip()
    return value or None


def _get_role_base_url(env_name: str) -> str | None:
    """Return a role-specific OpenAI-compatible base URL with a shared fallback."""

    value = os.getenv(env_name, "").strip()
    if value:
        return value
    return get_openai_base_url()


def get_query_base_url() -> str | None:
    """Return the base URL used for query rewriting and MQE generation."""

    return _get_role_base_url("EASYRAG_QUERY_BASE_URL")


def get_embedding_base_url() -> str | None:
    """Return the base URL used for embedding generation."""

    return _get_role_base_url("EASYRAG_EMBEDDING_BASE_URL")


def get_rerank_base_url() -> str | None:
    """Return the base URL used for reranking."""

    return _get_role_base_url("EASYRAG_RERANK_BASE_URL")


def get_kg_base_url() -> str | None:
    """Return the base URL used for KG extraction."""

    return _get_role_base_url("EASYRAG_KG_BASE_URL")


def get_kg_entity_types() -> tuple[str, ...]:
    """Return the configured KG entity type allowlist."""

    raw_value = os.getenv("EASYRAG_KG_ENTITY_TYPES", "").strip()
    if not raw_value:
        return ()
    return tuple(part.strip() for part in raw_value.split(",") if part.strip())


def _has_local_embedding_config() -> bool:
    """Return whether embeddings are configured to use the local hash backend."""

    return get_embedding_model_name().strip().lower().startswith("local-hash")


def has_query_model_config() -> bool:
    """Return whether query-model calls are configured."""

    return bool(get_query_api_key())


def has_embedding_model_config() -> bool:
    """Return whether embedding generation is configured."""

    return _has_local_embedding_config() or bool(get_embedding_api_key())


def has_rerank_model_config() -> bool:
    """Return whether reranking is configured."""

    return bool(get_rerank_api_key())


def has_kg_model_config() -> bool:
    """Return whether KG extraction model calls are configured."""

    explicit_key = bool(os.getenv("EASYRAG_KG_API_KEY", "").strip())
    explicit_model = bool(os.getenv("EASYRAG_KG_MODEL_NAME", "").strip())
    explicit_base_url = bool(os.getenv("EASYRAG_KG_BASE_URL", "").strip())
    if explicit_key:
        return True
    if explicit_model or explicit_base_url:
        return bool(get_kg_api_key())
    return False


def has_openai_compatible_config() -> bool:
    """Return whether any model-backed behavior is configured."""

    return any(
        (
            has_query_model_config(),
            has_embedding_model_config(),
            has_rerank_model_config(),
            has_kg_model_config(),
        )
    )
