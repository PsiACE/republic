"""Tape session helpers for Republic."""

from __future__ import annotations

from typing import Any

from republic.core.results import ErrorPayload
from republic.tape.context import ContextSelection, TapeContext, build_messages
from republic.tape.entries import TapeEntry
from republic.tape.query import TapeQuery
from republic.tape.store import InMemoryTapeStore, TapeStore


class TapeManager:
    """Global tape manager that owns storage and default context."""

    def __init__(
        self,
        *,
        store: TapeStore | None = None,
        default_context: TapeContext | None = None,
    ) -> None:
        self._tape_store = store or InMemoryTapeStore()
        self._global_context = default_context or TapeContext()

    @property
    def default_context(self) -> TapeContext:
        return self._global_context

    @default_context.setter
    def default_context(self, value: TapeContext) -> None:
        self._global_context = value

    def tape(self, name: str, *, context: TapeContext | None = None) -> Tape:
        return Tape(name, self, context=context)

    def list_tapes(self) -> list[str]:
        return self._tape_store.list_tapes()

    def read_entries(self, tape: str) -> list[TapeEntry]:
        return self._tape_store.read(tape) or []

    def read_messages(self, tape: str, *, context: TapeContext | None = None) -> ContextSelection:
        active_context = context or self._global_context
        return build_messages(self.read_entries(tape), active_context)

    def append_entry(self, tape: str, entry: TapeEntry) -> None:
        self._tape_store.append(tape, entry)

    def query_tape(self, tape: str) -> TapeQuery:
        return TapeQuery(tape=tape, store=self._tape_store)

    def reset_tape(self, tape: str) -> None:
        self._tape_store.reset(tape)

    def handoff(
        self,
        tape: str,
        name: str,
        *,
        state: dict[str, Any] | None = None,
        **meta: Any,
    ) -> list[TapeEntry]:
        entry = TapeEntry.anchor(name, state=state, **meta)
        event = TapeEntry.event("handoff", {"name": name, "state": state or {}}, **meta)
        self._tape_store.append(tape, entry)
        self._tape_store.append(tape, event)
        return [entry, event]

    def record_chat(  # noqa: C901
        self,
        *,
        tape: str,
        run_id: str,
        system_prompt: str | None,
        context_error: ErrorPayload | None,
        new_messages: list[dict[str, Any]],
        response_text: str | None,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_results: list[Any] | None = None,
        error: ErrorPayload | None = None,
        response: Any | None = None,
        provider: str | None = None,
        model: str | None = None,
        usage: dict[str, Any] | None = None,
    ) -> None:
        meta = {"run_id": run_id}
        if system_prompt:
            self._tape_store.append(tape, TapeEntry.system(system_prompt, **meta))
        if context_error is not None:
            self._tape_store.append(tape, TapeEntry.error(context_error, **meta))

        for message in new_messages:
            self._tape_store.append(tape, TapeEntry.message(message, **meta))

        if tool_calls:
            self._tape_store.append(tape, TapeEntry.tool_call(tool_calls, **meta))
        if tool_results is not None:
            self._tape_store.append(tape, TapeEntry.tool_result(tool_results, **meta))

        if error is not None:
            self._tape_store.append(tape, TapeEntry.error(error, **meta))

        if response_text is not None:
            self._tape_store.append(
                tape,
                TapeEntry.message({"role": "assistant", "content": response_text}, **meta),
            )

        data: dict[str, Any] = {"status": "error" if error is not None else "ok"}
        resolved_usage = usage or self._extract_usage(response)
        if resolved_usage is not None:
            data["usage"] = resolved_usage
        if provider:
            data["provider"] = provider
        if model:
            data["model"] = model
        self._tape_store.append(tape, TapeEntry.event("run", data, **meta))

    @staticmethod
    def _extract_usage(response: Any) -> dict[str, Any] | None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return None
        if isinstance(usage, dict):
            return usage
        if hasattr(usage, "model_dump"):
            return usage.model_dump(exclude_none=True)
        if hasattr(usage, "dict"):
            return usage.dict(exclude_none=True)
        return dict(getattr(usage, "__dict__", {}) or {}) or None


class Tape:
    """Named tape view."""

    def __init__(self, name: str, manager: TapeManager, *, context: TapeContext | None = None) -> None:
        self._name = name
        self._manager = manager
        self._local_context = context

    def __repr__(self) -> str:
        return f"<Tape name={self._name}>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def context(self) -> TapeContext:
        return self._local_context or self._manager.default_context

    @context.setter
    def context(self, value: TapeContext | None) -> None:
        self._local_context = value

    def read_entries(self) -> list[TapeEntry]:
        return self._manager.read_entries(self._name)

    def read_messages(self, *, context: TapeContext | None = None) -> ContextSelection:
        active_context = context or self.context
        return self._manager.read_messages(self._name, context=active_context)

    def append(self, entry: TapeEntry) -> None:
        self._manager.append_entry(self._name, entry)

    def query(self) -> TapeQuery:
        return self._manager.query_tape(self._name)

    def reset(self) -> None:
        self._manager.reset_tape(self._name)

    def handoff(self, name: str, *, state: dict[str, Any] | None = None, **meta: Any) -> list[TapeEntry]:
        return self._manager.handoff(self._name, name, state=state, **meta)
