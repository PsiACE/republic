"""Error definitions for Republic."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class ErrorKind(str, Enum):
    """Stable error kinds for caller decisions."""

    INVALID_INPUT = "invalid_input"
    CONFIG = "config"
    PROVIDER = "provider"
    TOOL = "tool"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


@dataclass
class RepublicError(Exception):
    """Public error type for Republic.

    Attributes:
        kind: Stable, actionable error kind.
        message: Human-readable description.
        cause: Original exception for debugging.
    """

    kind: ErrorKind
    message: str
    cause: Exception | None = None

    def __str__(self) -> str:
        return f"[{self.kind.value}] {self.message}"

    def with_cause(self, cause: Exception) -> RepublicError:
        return replace(self, cause=cause)
