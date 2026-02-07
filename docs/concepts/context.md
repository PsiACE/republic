# Context

Context defines how tape entries become prompt messages. Republic keeps the default path simple, while letting you override selection when needed.

The flow is always: anchor slicing → selection.

`tape.messages()` uses the tape's current context.

## Default Context

The default context includes `message` entries after the most recent anchor.

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini")
tape = llm.tape("notes")
```

`llm.context` sets the default context used by tapes created from the client.

## Anchor Control

Use `TapeContext.anchor` to control where context starts. The anchor name must be explicit.
Context starts after the most recent matching anchor name.
`TapeContext()` defaults to the most recent anchor; use `anchor=None` for full context.

```python
from republic import LLM, TapeContext

llm = LLM(model="openai:gpt-4o-mini")
tape = llm.tape("notes", context=TapeContext(anchor="handoff:v1"))
```

Set `anchor=None` to include the full tape.

## Missing Anchors

If an anchor is missing, Republic leaves the context unchanged. Anchors are best-effort hints, not hard requirements.

## Selection

Use `TapeContext.select` for custom selection logic (keyword search, semantic retrieval, recency windows).
The selector receives entries after anchor slicing and should return message dictionaries.
Keep selection deterministic and preserve order when possible.

```python
from republic import LLM, TapeContext, TapeEntry

def keyword_select(entries: list[TapeEntry], context: TapeContext) -> list[dict[str, str]]:
    query = "deploy"
    results: list[TapeEntry] = []
    for entry in entries:
        if entry.kind != "message":
            continue
        content = str(entry.payload.get("content", "")).lower()
        if query in content:
            results.append(entry)
    return [entry.payload for entry in results[-5:]]

context = TapeContext(anchor=None, select=keyword_select)
llm = LLM(model="openai:gpt-4o-mini")
tape = llm.tape("notes", context=context)
```

Swap `keyword_select` with your embedding search to enable semantic selection.

## Anchor-Based Strategies

Complex strategies stay simple when they are explicit and deterministic. Use anchors to define phases, then select
only what the model should see.

```python
from republic import LLM, TapeContext, TapeEntry

def anchored_context(entries: list[TapeEntry], context: TapeContext) -> list[dict[str, str]]:
    def last_anchor_index(prefix: str) -> int | None:
        for idx in range(len(entries) - 1, -1, -1):
            entry = entries[idx]
            if entry.kind == "anchor" and str(entry.payload.get("name", "")).startswith(prefix):
                return idx
        return None

    start = last_anchor_index("phase:exec")
    end = last_anchor_index("handoff:summary")

    if start is None:
        start = 0
    else:
        start += 1

    if end is None:
        end = len(entries)

    segment = entries[start:end]
    messages = [entry.payload for entry in segment if entry.kind == "message"]

    summary_index = last_anchor_index("handoff:summary")
    if summary_index is not None:
        summary = entries[summary_index].payload.get("state", {}).get("text")
        if summary:
            messages.insert(0, {"role": "system", "content": summary})

    return messages[-30:]

context = TapeContext(anchor=None, select=anchored_context)
llm = LLM(model="openai:gpt-4o-mini")
tape = llm.tape("notes", context=context)
```

## Runtime Updates

You can update the context on an existing client.

```python
from republic import LLM, TapeContext

llm = LLM(model="openai:gpt-4o-mini")
llm.context = TapeContext(anchor=None)
```

You can also override per tape:

```python
tape = llm.tape("notes")
tape.context = TapeContext(anchor="handoff:v1")
```
