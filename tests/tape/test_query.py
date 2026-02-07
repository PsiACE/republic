from __future__ import annotations

from republic import TapeEntry
from republic.tape import InMemoryTapeStore, TapeQuery


class TestTapeQuery:
    def test_between_anchors_selects_range(self):
        store = InMemoryTapeStore()
        store.append("tape", TapeEntry.message({"role": "user", "content": "a"}))
        store.append("tape", TapeEntry.anchor("start"))
        store.append("tape", TapeEntry.message({"role": "user", "content": "b"}))
        store.append("tape", TapeEntry.anchor("end"))
        store.append("tape", TapeEntry.message({"role": "user", "content": "c"}))

        query = TapeQuery("tape", store).between_anchors("start", "end").kinds("message")
        results = query.all()
        assert [entry.payload["content"] for entry in results] == ["b"]

    def test_between_anchors_uses_nearest_start(self):
        store = InMemoryTapeStore()
        store.append("tape", TapeEntry.anchor("start"))
        store.append("tape", TapeEntry.message({"role": "user", "content": "old"}))
        store.append("tape", TapeEntry.anchor("start"))
        store.append("tape", TapeEntry.message({"role": "user", "content": "new"}))
        store.append("tape", TapeEntry.anchor("end"))

        query = TapeQuery("tape", store).between_anchors("start", "end").kinds("message")
        results = query.all()
        assert [entry.payload["content"] for entry in results] == ["new"]

    def test_between_anchors_is_noop_when_end_missing(self):
        store = InMemoryTapeStore()
        store.append("tape", TapeEntry.message({"role": "user", "content": "a"}))
        store.append("tape", TapeEntry.anchor("start"))
        store.append("tape", TapeEntry.message({"role": "user", "content": "b"}))

        query = TapeQuery("tape", store).between_anchors("start", "end").kinds("message")
        results = query.all()
        assert [entry.payload["content"] for entry in results] == ["a", "b"]

    def test_last_anchor_selects_after_most_recent_anchor(self):
        store = InMemoryTapeStore()
        store.append("tape", TapeEntry.message({"role": "user", "content": "a"}))
        store.append("tape", TapeEntry.anchor("start"))
        store.append("tape", TapeEntry.message({"role": "user", "content": "b"}))
        store.append("tape", TapeEntry.anchor("end"))
        store.append("tape", TapeEntry.message({"role": "user", "content": "c"}))

        query = TapeQuery("tape", store).last_anchor().kinds("message")
        results = query.all()
        assert [entry.payload["content"] for entry in results] == ["c"]
