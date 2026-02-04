# Observability

Republic integrates with Logfire when installed and configured.

Note: Install the optional dependency `republic[observability]` to use Logfire.

```python
from republic.core import instrument_republic

instrument_republic()
```

You can also use `span` for manual tracing.
