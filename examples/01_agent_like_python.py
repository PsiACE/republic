from __future__ import annotations

import os

from pydantic import BaseModel

from republic import LLM, tool_from_model
from republic.tools import ToolExecutor


class Reminder(BaseModel):
    task: str
    time: str


class MissingEnvVarError(RuntimeError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Set {name} before running this example.")


def create_reminder(payload: Reminder) -> dict[str, str]:
    return {"status": "scheduled", "task": payload.task, "time": payload.time}


api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise MissingEnvVarError("LLM_API_KEY")
llm = LLM(model=os.getenv("REPUBLIC_TOOL_MODEL", "openrouter:openai/gpt-4o-mini"), api_key=api_key)
message = "Remind me to water the plants tomorrow at 9."
if not llm.if_(message, "Is this a reminder request?").value:
    raise SystemExit("decision=no_action")
tool = tool_from_model(Reminder, create_reminder)
calls = llm.chat.tool_calls(f"Extract a reminder: {message}", tools=[tool], max_tokens=96)
result = ToolExecutor().execute(calls.value, tools=[tool])
print("result=", result.tool_results, "error=", result.error)
