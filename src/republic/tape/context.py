"""Context building for tape entries."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, TypeAlias

from republic.tape.entries import TapeEntry
from republic.tape.query import TapeQuery


class _LastAnchor:
    def __repr__(self) -> str:
        return "LAST_ANCHOR"


LAST_ANCHOR = _LastAnchor()
AnchorSelector: TypeAlias = str | None | _LastAnchor


@dataclass(frozen=True)
class TapeContext:
    """Rules for selecting tape entries into a prompt context.

    anchor: LAST_ANCHOR for the most recent anchor, None for the full tape, or an anchor name.
    select: Optional selector called after anchor slicing that returns messages.
    """

    anchor: AnchorSelector = LAST_ANCHOR
    select: Callable[[Iterable[TapeEntry]], list[dict[str, Any]]] | None = None

    def build_query(self, query: TapeQuery) -> TapeQuery:
        if self.anchor is None:
            return query
        if isinstance(self.anchor, _LastAnchor):
            return query.last_anchor()
        return query.after_anchor(self.anchor)


def build_messages(entries: Iterable[TapeEntry], context: TapeContext) -> list[dict[str, Any]]:
    if context.select is not None:
        return context.select(entries)
    return _default_messages(entries)


def _default_messages(entries: Iterable[TapeEntry]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for entry in entries:
        if entry.kind != "message":
            continue
        payload = entry.payload
        if not isinstance(payload, dict):
            continue
        messages.append(dict(payload))
    return messages
