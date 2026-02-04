# Batch

Batch is for offline or large-volume requests. It depends on provider support.

OpenRouter does not support batch operations. Use a provider that exposes batch endpoints (for example, OpenAI).

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
job = llm.batch.create(
    input_file_path="/tmp/requests.jsonl",
    endpoint="/v1/chat/completions",
)
print(job)
```
