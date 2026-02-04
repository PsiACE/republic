# Responses

Use Responses when you need provider-native output or events. Responses are stateless.

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
response = llm.responses.create("Write a haiku about light.")
print(response)
```

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
for event in llm.responses.stream("Write a haiku about light."):
    print(event)
```
