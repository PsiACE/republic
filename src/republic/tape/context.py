"""Context building for tape entries."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from .entries import TapeEntry


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
    select: Callable[[Sequence[TapeEntry], TapeContext], list[dict[str, Any]]] | None = None


def build_messages(entries: Sequence[TapeEntry], context: TapeContext) -> list[dict[str, Any]]:
    selected_entries = _slice_after_anchor(entries, context.anchor)
    if context.select is not None:
        return context.select(selected_entries, context)
    return _default_messages(selected_entries)


def _default_messages(entries: Sequence[TapeEntry]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for entry in entries:
        if entry.kind != "message":
            continue
        payload = entry.payload
        if not isinstance(payload, dict):
            continue
        messages.append(dict(payload))
    return messages


def _slice_after_anchor(entries: Sequence[TapeEntry], anchor: AnchorSelector) -> Sequence[TapeEntry]:
    if anchor is None:
        return entries

    anchor_name = None if anchor is LAST_ANCHOR else anchor
    start_index = 0
    for idx in range(len(entries) - 1, -1, -1):
        entry = entries[idx]
        if entry.kind != "anchor":
            continue
        if anchor_name is not None and entry.payload.get("name") != anchor_name:
            continue
        start_index = idx + 1
        break
    else:
        return entries

    return entries[start_index:]
