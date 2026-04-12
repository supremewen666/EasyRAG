"""Async helpers shared by synchronous wrappers."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Coroutine
from typing import Any, TypeVar, cast

_T = TypeVar("_T")


def run_sync(awaitable: Awaitable[_T]) -> _T:
    """Run an awaitable from sync code, including inside an active event loop."""

    coroutine = cast(Coroutine[Any, Any, _T], awaitable)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    state: dict[str, object] = {}

    def runner() -> None:
        try:
            state["result"] = asyncio.run(coroutine)
        except BaseException as exc:
            state["error"] = exc

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()

    error = state.get("error")
    if error is not None:
        raise cast(BaseException, error)
    return cast(_T, state.get("result"))


__all__ = ["run_sync"]
