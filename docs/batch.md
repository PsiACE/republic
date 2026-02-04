# Batch

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
job = llm.batch.create(
    input_file_path="/tmp/requests.jsonl",
    endpoint="/v1/chat/completions",
)
print(job)
```
