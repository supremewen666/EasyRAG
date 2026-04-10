"""Optional dependency fallbacks used across EasyRAG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


try:
    from pydantic import BaseModel as PydanticBaseModel
    from pydantic import Field
except ImportError:  # pragma: no cover - exercised only without optional deps.
    def Field(default: Any = None, default_factory: Callable[[], Any] | None = None, **_: Any) -> Any:
        """Return a default value compatible with a subset of Pydantic's Field API."""

        if default_factory is not None:
            return default_factory()
        return default

    class PydanticBaseModel:
        """Small fallback that supports the subset of BaseModel used in this project."""

        def __init__(self, **kwargs: Any) -> None:
            annotations = {}
            for cls in reversed(self.__class__.__mro__):
                annotations.update(getattr(cls, "__annotations__", {}))
            for name in annotations:
                default = getattr(self.__class__, name, None)
                value = kwargs[name] if name in kwargs else default
                setattr(self, name, value)

        def model_dump(self) -> dict[str, Any]:
            """Serialize public fields into plain Python data."""

            annotations = {}
            for cls in reversed(self.__class__.__mro__):
                annotations.update(getattr(cls, "__annotations__", {}))
            return {name: _dump_value(getattr(self, name)) for name in annotations}

        @classmethod
        def model_validate(cls, value: Any) -> "PydanticBaseModel":
            """Normalize dicts and already-typed instances into the target model."""

            if isinstance(value, cls):
                return value
            if isinstance(value, dict):
                return cls(**value)
            raise TypeError(f"Cannot validate {type(value)!r} as {cls.__name__}")

        def __repr__(self) -> str:
            items = ", ".join(f"{key}={value!r}" for key, value in self.model_dump().items())
            return f"{self.__class__.__name__}({items})"


def _dump_value(value: Any) -> Any:
    """Serialize nested compatibility objects into primitive Python values."""

    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_dump_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump_value(item) for key, item in value.items()}
    return value


BaseModel = PydanticBaseModel


try:
    from langchain_core.documents import Document
except ImportError:  # pragma: no cover - exercised only without optional deps.
    @dataclass
    class Document:
        """Minimal stand-in for LangChain Document."""

        page_content: str
        metadata: dict[str, Any]


try:
    from langchain_core.tools import BaseTool, tool
except ImportError:  # pragma: no cover - exercised only without optional deps.
    class BaseTool:
        """Minimal read-only tool wrapper compatible with the project's needs."""

        def __init__(self, name: str, description: str, func: Callable[..., Any]) -> None:
            self.name = name
            self.description = description
            self._func = func

        def invoke(self, input_data: Any) -> Any:
            """Invoke the wrapped callable with either a dict or scalar argument."""

            if isinstance(input_data, dict):
                return self._func(**input_data)
            return self._func(input_data)

    def tool(func: Callable[..., Any] | None = None, *, description: str | None = None) -> Callable[..., Any]:
        """Fallback decorator that wraps a function into a simple tool object."""

        def decorator(inner: Callable[..., Any]) -> BaseTool:
            return BaseTool(
                name=inner.__name__,
                description=description or (inner.__doc__ or "").strip(),
                func=inner,
            )

        if func is None:
            return decorator
        return decorator(func)


Runnable = Any
