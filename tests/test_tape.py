from __future__ import annotations

from republic.core.errors import ErrorKind
from republic.tape.context import LAST_ANCHOR, TapeContext, build_messages
from republic.tape.entries import TapeEntry
from republic.tape.query import TapeQuery
from republic.tape.store import InMemoryTapeStore


def _entries() -> list[TapeEntry]:
    return [
        TapeEntry.message({"role": "user", "content": "first"}),
        TapeEntry.anchor("a1"),
        TapeEntry.message({"role": "user", "content": "second"}),
        TapeEntry.anchor("a2"),
        TapeEntry.message({"role": "assistant", "content": "third"}),
    ]


def test_build_messages_after_last_anchor() -> None:
    entries = _entries()
    selection = build_messages(entries, TapeContext(anchor=LAST_ANCHOR))
    assert [message["content"] for message in selection.messages] == ["third"]
    assert selection.error is None


def test_build_messages_missing_anchor() -> None:
    entries = _entries()
    selection = build_messages(entries, TapeContext(anchor="missing"))
    assert selection.messages == []
    assert selection.error is not None
    assert selection.error.kind == ErrorKind.NOT_FOUND


def test_tape_query_between_anchors() -> None:
    store = InMemoryTapeStore()
    tape = "t1"
    for entry in _entries():
        store.append(tape, entry)

    query = TapeQuery(tape=tape, store=store).between_anchors("a1", "a2")
    result = query.all()
    assert result.error is None
    assert [entry.kind for entry in result.entries] == ["message"]
    assert result.entries[0].payload["content"] == "second"
