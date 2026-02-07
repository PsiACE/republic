# Embeddings

Embeddings are exposed through the same LLM facade and follow the `provider:model` format. The example uses OpenRouter with an OpenAI embedding model. You can override the model via `REPUBLIC_EMBEDDING_MODEL`.

Example prerequisite: set `LLM_API_KEY` in your environment.

```python
from __future__ import annotations

import os

from republic import LLM

api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise RuntimeError("Set LLM_API_KEY before running this example.")

embedding_model = os.getenv("REPUBLIC_EMBEDDING_MODEL", "openrouter:openai/text-embedding-3-small")
llm = LLM(model=embedding_model, api_key=api_key)
result = llm.embed(["hello", "world"])
print(result.value)
print(result.error)
```

## Notes

- Not all providers support embeddings.
- If you pass a chat model by mistake, you will receive a structured error.
