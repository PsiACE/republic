# Error Handling

Errors are raised as `RepublicError` with a stable `ErrorKind`.

You can override the default classification via `error_classifier`:

```python
from republic import LLM
from republic.core import ErrorKind

def classify(exc: Exception):
    if isinstance(exc, TimeoutError):
        return ErrorKind.TEMPORARY
    return None

llm = LLM(model="openai:gpt-4o-mini", error_classifier=classify)
```
