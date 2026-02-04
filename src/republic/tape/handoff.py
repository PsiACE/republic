"""Handoff helpers for tape."""

from __future__ import annotations

import builtins
from typing import Any, Protocol

from .entries import TapeEntry


class HandoffHandler(Protocol):
    """Build handoff entries for a tape."""

    def build_entries(
        self,
        tape: str,
        name: str,
        state: dict[str, Any] | None,
        meta: dict[str, Any],
    ) -> builtins.list[TapeEntry]: ...


class HandoffPolicy(Protocol):
    """Decide whether a handoff should be recorded."""

    def allow(
        self,
        *,
        tape: str,
        name: str,
        state: dict[str, Any] | None,
        meta: dict[str, Any],
    ) -> bool: ...
