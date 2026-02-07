# Tape

Tape is the core state model in Republic. It is an append-only log of entries. State is derived, not rewritten.

`llm.tape(name)` returns a stateful handle to a named tape.

## Quick Start

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini")
tape = llm.tape("notes")

tape("Remember this.")
print(tape.messages())
```

`messages()` returns the context-selected messages, not the raw entries.

## Entries vs Messages

Entries are facts. Messages are what gets fed back to the model.

```python
from republic import LLM, TapeEntry

llm = LLM(model="openai:gpt-4o-mini")
tape = llm.tape("notes")

tape.append(TapeEntry.message({"role": "user", "content": "Hello"}))
print(tape.entries())
print(tape.messages())
```

## Anchors and Handoff

Use anchors to mark phases and control context boundaries.

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini")
llm.tape("notes").handoff("handoff:v1", state={"phase": "summary"})
```

## Stores

Implement `list_tapes`, `read`, `append`, and `reset`.
`read` should return a snapshot, and `append` must only add new entries.
Use `reset` for local or test cleanup, not for rewriting history.

```python
from republic import LLM
from republic.tape import InMemoryTapeStore

store = InMemoryTapeStore()
llm = LLM(model="openai:gpt-4o-mini", tape_store=store)
```

```python
llm.tapes()
```

## Query

Use `TapeQuery` for lightweight, chainable selection.

```python
from republic import TapeEntry
from republic.tape import InMemoryTapeStore, TapeQuery

store = InMemoryTapeStore()
store.append("notes", TapeEntry.message({"role": "user", "content": "a"}))
store.append("notes", TapeEntry.anchor("start"))
store.append("notes", TapeEntry.message({"role": "user", "content": "b"}))
store.append("notes", TapeEntry.anchor("end"))

entries = TapeQuery("notes", store).between_anchors("start", "end").kinds("message").all()
```

Between-anchors selection excludes the anchor entries themselves.
After-anchor selection starts after the most recent matching anchor name.

With a tape handle:

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini")
tape = llm.tape("notes")
entries = tape.query().after_anchor("handoff:v1").kinds("message").all()
entries = tape.query().last_anchor().kinds("message").all()
```

For context assembly, see [Context](context.md).
