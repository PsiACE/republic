"""Observability helpers for Republic."""

from __future__ import annotations

from contextlib import nullcontext
from typing import Any

try:  # pragma: no cover - optional dependency
    import logfire  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    logfire = None

from republic.core.errors import ErrorKind, RepublicError

_INSTRUMENTED = False


def span(name: str, **attributes: Any):
    if not _INSTRUMENTED or logfire is None:
        return nullcontext()
    return logfire.span(name, **attributes)


def instrument_republic() -> None:
    """Enable Republic's Logfire spans after users configure Logfire themselves."""
    if logfire is None:
        raise RepublicError(
            ErrorKind.CONFIG,
            "Logfire is not installed. Install with 'republic[observability]' to enable tracing.",
        )
    global _INSTRUMENTED
    _INSTRUMENTED = True
