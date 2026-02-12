from __future__ import annotations

import pytest

from republic.core.errors import ErrorKind
from republic.core.results import ErrorPayload
from republic.tape.context import LAST_ANCHOR, TapeContext, build_messages
from republic.tape.entries import TapeEntry
from republic.tape.query import TapeQuery
from republic.tape.store import InMemoryTapeStore


def _seed_entries() -> list[TapeEntry]:
    return [
        TapeEntry.message({"role": "user", "content": "before"}),
        TapeEntry.anchor("a1"),
        TapeEntry.message({"role": "user", "content": "task 1"}),
        TapeEntry.message({"role": "assistant", "content": "answer 1"}),
        TapeEntry.anchor("a2"),
        TapeEntry.message({"role": "user", "content": "task 2"}),
    ]


def test_build_messages_uses_last_anchor_slice() -> None:
    messages = build_messages(_seed_entries(), TapeContext(anchor=LAST_ANCHOR))
    assert [message["content"] for message in messages] == ["task 2"]


def test_build_messages_reports_missing_anchor() -> None:
    with pytest.raises(ErrorPayload) as exc_info:
        build_messages(_seed_entries(), TapeContext(anchor="missing"))
    assert exc_info.value.kind == ErrorKind.NOT_FOUND


def test_query_between_anchors_and_limit() -> None:
    store = InMemoryTapeStore()
    tape = "session"

    for entry in _seed_entries():
        store.append(tape, entry)

    entries = TapeQuery(tape=tape, store=store).between_anchors("a1", "a2").kinds("message").limit(1).all()
    assert len(entries) == 1
    assert entries[0].payload["content"] == "task 1"
