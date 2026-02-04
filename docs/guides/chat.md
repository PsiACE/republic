# Chat

Chat gives you stateless requests. Tape gives you state.

## Basic Chat

Use `llm.chat` for stateless requests.

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
print(llm.chat.create("Tell me a story."))
```

## Streaming Chat

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")

for chunk in llm.chat.stream("Write a haiku about light."):
    print(chunk, end="")
```

## Message Lists

```python
messages = [
    {"role": "system", "content": "You are concise."},
    {"role": "user", "content": "Summarize this."},
]
print(llm.chat.create(messages=messages))
```

## Raw Responses

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
raw = llm.chat.raw("Give me JSON.")
print(raw)
```

## Tape History

Use `llm.tape(name)` for stateful chat.

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
tape = llm.tape("notes")
tape("Remember this.")
print(tape.messages())
```

Streaming with tape works the same way:

```python
for chunk in tape.stream("Write a 5-word line about light."):
    print(chunk, end="")
```

For tape semantics and context selection, see [Tape](../concepts/tape.md) and [Context](../concepts/context.md).
