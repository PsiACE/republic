from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from republic import LLM, TapeContext, TapeEntry, ToolSet, schema_from_model, tool, tool_from_model
from republic.core import ErrorKind, span
from republic.tape import InMemoryTapeStore, TapeQuery

DEFAULT_MODEL = "openrouter:openrouter/free"
DEFAULT_HEADERS = {
    "HTTP-Referer": "https://getrepublic.org",
    "X-Title": "republic docs",
}


class CheckFailure(Exception):
    pass


class MissingEnvError(CheckFailure):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(key)

    def __str__(self) -> str:
        return f"{self.key} is missing from the environment"


class ToolCallsMissing(CheckFailure):
    def __str__(self) -> str:
        return "no tool calls returned"


class ToolResultMissing(CheckFailure):
    def __str__(self) -> str:
        return "tool result missing"


class ToolsAutoMissing(CheckFailure):
    def __str__(self) -> str:
        return "auto tools returned no result"


class TapeToolsMissing(CheckFailure):
    def __str__(self) -> str:
        return "tape tools returned no result"


class ResponsesStreamEmpty(CheckFailure):
    def __str__(self) -> str:
        return "responses.stream returned no events"


def require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise MissingEnvError(key)
    return value


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def log(name: str, status: str, detail: str = "") -> None:
    line = f"[{status}] {name}"
    if detail:
        line = f"{line} -> {detail}"
    print(line)


def run_check(name: str, fn: Callable[[], Any], failures: list[tuple[str, Exception]]) -> None:
    try:
        result = fn()
    except Exception as exc:
        failures.append((name, exc))
        log(name, "fail", f"{type(exc).__name__}: {exc}")
    else:
        detail = "ok" if result is None else str(result)
        log(name, "ok", detail)


def build_llm(
    api_key: str,
    model: str,
    headers: dict[str, str],
    *,
    tape_store: InMemoryTapeStore | None = None,
    error_classifier: Callable[[Exception], ErrorKind | None] | None = None,
) -> LLM:
    return LLM(
        model=model,
        api_key=api_key,
        client_args={"default_headers": headers},
        tape_store=tape_store,
        error_classifier=error_classifier,
    )


def check_basic_chat(llm: LLM) -> str:
    response = llm.chat.create("Reply with the word OK.")
    assert_true("OK" in response, "basic chat did not include OK")
    return response


def check_stream_chat(llm: LLM) -> str:
    text = "".join(llm.chat.stream("Reply with the word OK."))
    assert_true("OK" in text, "stream chat did not include OK")
    return text


def check_message_list(llm: LLM) -> str:
    messages = [
        {"role": "system", "content": "You are concise."},
        {"role": "user", "content": "Reply with OK."},
    ]
    response = llm.chat.create(messages=messages)
    assert_true("OK" in response, "message list did not include OK")
    return response


def check_raw_response(llm: LLM) -> str:
    raw = llm.chat.raw("Return JSON with key ok and value true.")
    assert_true(raw is not None, "raw response is empty")
    return raw.model


def check_tape_basics(llm: LLM) -> str:
    tape = llm.tape("docs-notes")
    reply = tape("Remember this for later.")
    messages = tape.messages()
    assert_true(messages[-1]["role"] == "assistant", "last tape message should be assistant")
    assert_true(any(msg["role"] == "user" for msg in messages), "tape messages missing user")
    return reply


def check_tape_stream(llm: LLM) -> str:
    tape = llm.tape("docs-stream")
    text = "".join(tape.stream("Reply with OK."))
    assert_true("OK" in text, "tape stream did not include OK")
    return text


def check_context_selection(api_key: str, model: str, headers: dict[str, str]) -> str:
    store = InMemoryTapeStore()
    store.append("ctx", TapeEntry.message({"role": "user", "content": "old"}))
    store.append("ctx", TapeEntry.anchor("handoff"))
    store.append("ctx", TapeEntry.message({"role": "user", "content": "new"}))

    llm_ctx = build_llm(api_key, model, headers, tape_store=store)
    tape = llm_ctx.tape("ctx", context=TapeContext(anchor="last"))
    messages = tape.messages()
    assert_true({"role": "user", "content": "old"} not in messages, "context anchor did not slice")
    assert_true({"role": "user", "content": "new"} in messages, "context missing latest message")
    return "anchor ok"


def check_tape_query() -> str:
    store = InMemoryTapeStore()
    store.append("q", TapeEntry.message({"role": "user", "content": "a"}))
    store.append("q", TapeEntry.anchor("start"))
    store.append("q", TapeEntry.message({"role": "user", "content": "b"}))
    store.append("q", TapeEntry.anchor("end"))
    query = TapeQuery("q", store).between_anchors("start", "end").kinds("message")
    entries = query.all()
    assert_true(len(entries) == 1 and entries[0].payload.get("content") == "b", "TapeQuery returned unexpected entries")
    return "query ok"


def check_tools_schema_only() -> str:
    class WeatherSchema(BaseModel):
        """Weather request."""

        location: str

    tool_schema = schema_from_model(WeatherSchema, name="weather_schema")

    def handle_weather(payload: WeatherSchema) -> str:
        return f"Weather in {payload.location} is sunny"

    typed_tool = tool_from_model(WeatherSchema, handle_weather, name="weather_tool")
    toolset = ToolSet.from_tools([tool_schema, typed_tool])
    assert_true(toolset.payload is not None, "toolset payload missing")
    return "typed tools ok"


def check_tools_manual(llm: LLM) -> str:
    @tool
    def get_weather(location: str) -> str:
        """Get the weather for a location."""
        return f"Weather in {location} is sunny"

    tool_calls = llm.chat.tool_calls("What's the weather in Tokyo?", tools=[get_weather])
    if not tool_calls:
        raise ToolCallsMissing
    result = llm.tools.execute(tool_calls, tools=[get_weather])
    if result is None:
        raise ToolResultMissing
    assert_true("Tokyo" in result, "manual tool result missing location")
    return result


def check_tools_auto(llm: LLM) -> str:
    @tool
    def get_weather(location: str) -> str:
        """Get the weather for a location."""
        return f"Weather in {location} is sunny"

    result = llm.chat.tools_auto("What's the weather in Tokyo?", tools=[get_weather])
    if result is None:
        raise ToolsAutoMissing
    assert_true("Tokyo" in result, "auto tools did not use tool result")
    return result


def check_tape_tools_auto(llm: LLM) -> str:
    @tool
    def get_weather(location: str) -> str:
        """Get the weather for a location."""
        return f"Weather in {location} is sunny"

    tape = llm.tape("docs-tools")
    result = tape.tools_auto("What's the weather in Tokyo?", tools=[get_weather])
    if result is None:
        raise TapeToolsMissing
    assert_true("Tokyo" in result, "tape tools auto did not use tool result")
    return result


def check_responses(llm: LLM) -> str:
    response = llm.responses.create("Reply with OK.")
    assert_true(response is not None, "responses.create returned None")
    return "responses ok"


def check_responses_stream(llm: LLM) -> str:
    events = list(llm.responses.stream("Reply with OK."))
    if not events:
        raise ResponsesStreamEmpty
    return f"events={len(events)}"


def check_batch(llm: LLM) -> str:
    payload = {
        "custom_id": "req-1",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {"model": "openrouter/free", "messages": [{"role": "user", "content": "OK"}]},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as handle:
        path = pathlib.Path(handle.name)
        handle.write(json.dumps(payload) + "\n")
    try:
        job = llm.batch.create(input_file_path=str(path), endpoint="/v1/chat/completions")
        assert_true(job is not None, "batch.create returned None")
        return "batch ok"
    finally:
        path.unlink(missing_ok=True)


def check_error_types(api_key: str, model: str, headers: dict[str, str]) -> str:
    def classify(exc: Exception):
        if isinstance(exc, TimeoutError):
            return ErrorKind.TEMPORARY
        return None

    llm_err = build_llm(api_key, model, headers, error_classifier=classify)
    assert_true(llm_err is not None, "error classifier setup failed")
    return "error classifier ok"


def check_span() -> str:
    span_obj = span("republic.docs")
    assert_true(span_obj is not None, "span returned None")
    return "span ok"


def main() -> int:
    api_key = require_env("LLM_API_KEY")
    model = os.environ.get("LLM_MODEL", DEFAULT_MODEL)
    headers = DEFAULT_HEADERS.copy()
    llm = build_llm(api_key, model, headers)

    failures: list[tuple[str, Exception]] = []
    checks = [
        ("chat.create", lambda: check_basic_chat(llm)),
        ("chat.stream", lambda: check_stream_chat(llm)),
        ("chat.messages", lambda: check_message_list(llm)),
        ("chat.raw", lambda: check_raw_response(llm)),
        ("tape.basics", lambda: check_tape_basics(llm)),
        ("tape.stream", lambda: check_tape_stream(llm)),
        ("tape.context", lambda: check_context_selection(api_key, model, headers)),
        ("tape.query", check_tape_query),
        ("tools.schema", check_tools_schema_only),
        ("responses.create", lambda: check_responses(llm)),
        ("responses.stream", lambda: check_responses_stream(llm)),
        ("errors.classifier", lambda: check_error_types(api_key, model, headers)),
        ("observability.span", check_span),
    ]

    for name, fn in checks:
        run_check(name, fn, failures)

    if llm.provider == "openrouter":
        log("tools.manual", "skip", "openrouter/free may return models without tool-call support")
        log("tools.auto", "skip", "openrouter/free may return models without tool-call support")
        log("tools.tape", "skip", "openrouter/free may return models without tool-call support")
    else:
        run_check("tools.manual", lambda: check_tools_manual(llm), failures)
        run_check("tools.auto", lambda: check_tools_auto(llm), failures)
        run_check("tools.tape", lambda: check_tape_tools_auto(llm), failures)

    if llm.provider == "openrouter":
        log("batch.create", "skip", "openrouter does not support batch operations")
    else:
        run_check("batch.create", lambda: check_batch(llm), failures)

    if failures:
        log("summary", "fail", f"{len(failures)} checks failed")
        for name, exc in failures:
            log(name, "fail", f"{type(exc).__name__}: {exc}")
        return 1

    log("summary", "ok", f"{len(checks)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
