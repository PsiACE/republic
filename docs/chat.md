# Chat

## Basic Chat

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

## Raw Responses

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
raw = llm.chat.raw("Give me JSON.")
print(raw)
```

## Conversations

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
llm.chat.create("Remember this.", conversation="notes")
print(llm.chat.get_history("notes"))
```
