# Conversation Storage

```python
from republic import InMemoryConversationStore, LLM

store = InMemoryConversationStore()
llm = LLM(model="openai:gpt-4o-mini", conversation_store=store)
```

Custom stores should implement `list`, `reset`, `get`, and `append`. `get` returns a snapshot of messages, and
`append` persists new messages. The default store is in-memory and not thread-safe.
