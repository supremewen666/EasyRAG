"""Default provider adapters for EasyRAG EasyRAG."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from easyrag.config import (
    get_embedding_base_url,
    get_embedding_model_name,
    get_kg_base_url,
    get_kg_model_name,
    get_openai_api_key,
    get_query_base_url,
    get_query_model_name,
    get_rerank_base_url,
    get_rerank_model_name,
    has_openai_compatible_config,
)

try:
    import httpx
except ImportError:  # pragma: no cover - optional dependency path.
    httpx = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency path.
    OpenAI = None


def _retryable_exception_types() -> tuple[type[BaseException], ...]:
    """Return a conservative set of transient exception types."""

    types: list[type[BaseException]] = [TimeoutError, ConnectionError, OSError]
    if httpx is not None:
        for name in ("TimeoutException", "TransportError", "NetworkError", "ReadTimeout", "ConnectTimeout"):
            value = getattr(httpx, name, None)
            if isinstance(value, type) and issubclass(value, BaseException):
                types.append(value)
    return tuple(dict.fromkeys(types))


def _is_retryable_error(exc: Exception) -> bool:
    """Return whether an exception looks transient enough to retry once or twice."""

    if isinstance(exc, _retryable_exception_types()):
        return True
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "timeout",
            "temporarily unavailable",
            "connection reset",
            "connection aborted",
            "try again",
            "too many requests",
            "rate limit",
        )
    )


def _call_with_retry(operation: Any, *, attempts: int = 3) -> Any:
    """Retry a transient provider call a small number of times."""

    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt >= attempts - 1 or not _is_retryable_error(exc):
                raise
    if last_error is not None:
        raise last_error
    raise RuntimeError("Provider call failed before execution.")


def can_use_openai_compatible_models() -> bool:
    """Return whether the environment has enough configuration for model calls."""

    return bool(has_openai_compatible_config())


def _require_client(base_url: str | None) -> Any:
    """Build an OpenAI-compatible client or raise a helpful error."""

    if OpenAI is None:
        raise RuntimeError("openai package is not installed.")
    api_key = get_openai_api_key().strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=api_key, base_url=base_url)


def _require_httpx() -> Any:
    """Return the httpx module or raise a helpful error."""

    if httpx is None:
        raise RuntimeError("httpx is not installed.")
    return httpx


def _get_origin(base_url: str) -> str:
    """Return the scheme://netloc portion of a URL."""

    parsed = urlsplit(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(f"Invalid base URL: {base_url}")
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def _is_dashscope_url(base_url: str | None) -> bool:
    """Return whether a base URL points at a DashScope host."""

    if not base_url:
        return False
    host = urlsplit(base_url).netloc.lower()
    return host in {"dashscope.aliyuncs.com", "dashscope-intl.aliyuncs.com"}


def _looks_like_vl_embedding_model(model_name: str) -> bool:
    """Return whether the model name targets DashScope's multimodal embedding API."""

    return model_name.strip().lower().startswith("qwen3-vl-embedding")


def _looks_like_vl_rerank_model(model_name: str) -> bool:
    """Return whether the model name targets DashScope's multimodal rerank API."""

    return model_name.strip().lower().startswith("qwen3-vl-rerank")


def _looks_like_dashscope_text_rerank_model(model_name: str) -> bool:
    """Return whether the model name is served by DashScope's rerank APIs."""

    normalized = model_name.strip().lower()
    return normalized.startswith("qwen3-rerank") or normalized.startswith("gte-rerank-v2")


def _path_to_data_url(path: str) -> str | None:
    """Convert a local image path into a base64 data URL."""

    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    return f"data:{mime_type};base64,{base64.b64encode(file_path.read_bytes()).decode('ascii')}"


def _build_multimodal_content(item: Any) -> dict[str, str]:
    """Normalize one text or text+image payload for DashScope VL APIs."""

    if isinstance(item, str):
        return {"text": item}

    if isinstance(item, dict):
        content: dict[str, str] = {}
        text = str(item.get("text", "")).strip()
        if text:
            content["text"] = text
        image_paths = item.get("image_paths", []) or []
        for image_path in image_paths:
            data_url = _path_to_data_url(str(image_path))
            if data_url:
                content["image"] = data_url
                break
        if content:
            return content
    return {"text": str(item)}


def _build_multimodal_rerank_document(item: dict[str, Any]) -> dict[str, str]:
    """Build one rerank document payload from hydrated retrieval data."""

    metadata = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
    return _build_multimodal_content(
        {
            "text": str(item.get("text") or item.get("snippet") or ""),
            "image_paths": metadata.get("image_paths", []) or item.get("image_paths", []) or [],
        }
    )


def _get_dashscope_multimodal_embedding_url(base_url: str | None) -> str:
    """Return the official DashScope endpoint for multimodal embeddings."""

    if not base_url:
        raise RuntimeError("No embedding base URL is configured.")
    return f"{_get_origin(base_url)}/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"


def _get_dashscope_rerank_url(base_url: str | None, model_name: str) -> str:
    """Return the best DashScope rerank endpoint for the given model."""

    if not base_url:
        raise RuntimeError("No rerank base URL is configured.")
    origin = _get_origin(base_url)
    host = urlsplit(base_url).netloc.lower()
    if host == "dashscope-intl.aliyuncs.com" and model_name.strip().lower().startswith("qwen3-rerank"):
        return f"{origin}/compatible-api/v1/reranks"
    return f"{origin}/api/v1/services/rerank/text-rerank/text-rerank"


def _extract_text_from_chat_response(response: Any) -> str:
    """Normalize common OpenAI-compatible chat response shapes into text."""

    try:
        message = response.choices[0].message
        content = getattr(message, "content", "")
        if isinstance(content, list):
            return "".join(
                str(part.get("text", "")) if isinstance(part, dict) else str(getattr(part, "text", ""))
                for part in content
            ).strip()
        return str(content or "").strip()
    except Exception as exc:  # pragma: no cover - defensive normalization.
        raise RuntimeError(f"Could not parse chat response: {exc}") from exc


def _parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from raw model output with light cleanup."""

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if "\n" in cleaned:
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    candidate = cleaned[start : end + 1] if start >= 0 and end >= start else cleaned
    payload = json.loads(candidate)
    if not isinstance(payload, dict):
        raise RuntimeError("Model output is not a JSON object.")
    return payload


def default_query_model_func(
    prompt: str,
    *,
    task: str,
    count: int = 1,
) -> str | list[str]:
    """Run query rewrite or MQE generation through an OpenAI-compatible chat model."""

    client = _require_client(get_query_base_url())
    if task == "rewrite":
        system_prompt = (
            "You rewrite repository-search queries for retrieval. "
            "Return exactly one concise rewritten query and nothing else."
        )
    elif task == "mqe":
        system_prompt = (
            "You generate diverse repository-search query variants for retrieval. "
            f"Return exactly {count} variants as a JSON array of strings."
        )
    else:
        raise ValueError(f"Unsupported query model task: {task}")

    response = _call_with_retry(
        lambda: client.chat.completions.create(
            model=get_query_model_name(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
    )
    text = _extract_text_from_chat_response(response)
    if task == "rewrite":
        return text

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass
    lines = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
    return lines[:count]


def default_embedding_func(texts: list[Any]) -> list[list[float]]:
    """Generate dense embeddings through OpenAI-compatible or DashScope APIs."""

    model_name = get_embedding_model_name()
    base_url = get_embedding_base_url()
    if _looks_like_vl_embedding_model(model_name):
        if not _is_dashscope_url(base_url):
            raise RuntimeError("Qwen3-VL-Embedding requires a DashScope embedding base URL.")
        client = _require_httpx()
        response = _call_with_retry(
            lambda: client.post(
                _get_dashscope_multimodal_embedding_url(base_url),
                json={
                    "model": model_name,
                    "input": {"contents": [_build_multimodal_content(text) for text in texts]},
                },
                headers={"Authorization": f"Bearer {get_openai_api_key().strip()}", "Content-Type": "application/json"},
                timeout=30.0,
            )
        )
        response.raise_for_status()
        body = response.json()
        embeddings = body.get("output", {}).get("embeddings") or []
        values = [list(item.get("embedding") or []) for item in embeddings]
        if len(values) != len(texts) or any(not value for value in values):
            raise RuntimeError("Embedding endpoint returned no usable vectors.")
        return values

    client = _require_client(base_url)
    response = _call_with_retry(lambda: client.embeddings.create(model=model_name, input=texts))
    return [list(item.embedding) for item in response.data]


def default_kg_model_func(
    text: str,
    *,
    entity_types: list[str] | tuple[str, ...],
    max_entities: int,
    max_relations: int,
    metadata: dict[str, Any] | None = None,
) -> dict[str, list[dict[str, str]]]:
    """Extract entities and relations as structured JSON through a chat model."""

    client = _require_client(get_kg_base_url())
    allowed_types = ", ".join(entity_types)
    page_context = ""
    if metadata:
        title = str(metadata.get("title", "")).strip()
        path = str(metadata.get("relative_path") or metadata.get("path") or "").strip()
        page_context = f"Title: {title}\nPath: {path}\n" if title or path else ""
    system_prompt = (
        "You extract repository-architecture knowledge graph data from technical documentation. "
        "Return only JSON with shape "
        '{"entities":[{"name":"","type":"","description":""}],"relations":[{"source":"","target":"","relation":"","description":""}]}. '
        f"Allowed entity types: {allowed_types}. "
        "Prefer architecture-level concepts such as modules, services, components, tools, workflows, configs, and dependencies. "
        f"Return at most {max_entities} entities and {max_relations} relations. "
        "Relation names must be concise lowercase snake_case. "
        "Only include entities and relations grounded in the provided text."
    )
    response = _call_with_retry(
        lambda: client.chat.completions.create(
            model=get_kg_model_name(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{page_context}Content:\n{text}"},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
    )
    parsed = _parse_json_object(_extract_text_from_chat_response(response))
    entities = parsed.get("entities", [])
    relations = parsed.get("relations", [])
    if not isinstance(entities, list) or not isinstance(relations, list):
        raise RuntimeError("KG extraction response is missing entities or relations arrays.")
    return {
        "entities": [item for item in entities if isinstance(item, dict)],
        "relations": [item for item in relations if isinstance(item, dict)],
    }


def default_reranker_func(query: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rerank retrieval candidates through OpenAI-compatible or DashScope APIs."""

    client = _require_httpx()
    api_key = get_openai_api_key().strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    base_url = get_rerank_base_url()
    if not base_url:
        raise RuntimeError("No rerank base URL is configured.")
    model_name = get_rerank_model_name()

    documents = [str(item.get("text") or item.get("snippet") or "") for item in items]
    if _is_dashscope_url(base_url) and (
        _looks_like_vl_rerank_model(model_name) or _looks_like_dashscope_text_rerank_model(model_name)
    ):
        if _looks_like_vl_rerank_model(model_name):
            payload = {
                "model": model_name,
                "input": {
                    "query": {"text": query},
                    "documents": [_build_multimodal_rerank_document(item) for item in items],
                },
                "parameters": {
                    "top_n": len(documents),
                    "return_documents": True,
                },
            }
        else:
            payload = {
                "model": model_name,
                "query": query,
                "documents": documents,
                "top_n": len(documents),
            }
        response = _call_with_retry(
            lambda: client.post(
                _get_dashscope_rerank_url(base_url, model_name),
                json=payload,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=30.0,
            )
        )
    else:
        response = _call_with_retry(
            lambda: client.post(
                f"{base_url.rstrip('/')}/rerank",
                json={
                    "model": model_name,
                    "query": query,
                    "documents": documents,
                    "top_n": len(documents),
                },
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=30.0,
            )
        )
    response.raise_for_status()
    body = response.json()
    raw_results = body.get("output", {}).get("results") or body.get("results") or body.get("data") or []
    ranked = []
    for item in raw_results:
        index = int(item.get("index", 0))
        score = float(item.get("relevance_score", item.get("score", 0.0)))
        if 0 <= index < len(items):
            candidate = dict(items[index])
            candidate["rerank_score"] = score
            ranked.append(candidate)
    if not ranked:
        raise RuntimeError("Rerank endpoint returned no usable results.")
    ranked.sort(key=lambda item: float(item.get("rerank_score", 0.0)), reverse=True)
    return ranked
