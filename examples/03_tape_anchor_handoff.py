from __future__ import annotations

import json
import os
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field

from republic import LLM, tool_from_model
from republic.tape import TapeContext
from republic.tape.entries import TapeEntry
from republic.tools import ToolExecutor


def select_task_messages(entries: Sequence[TapeEntry], _: TapeContext) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for entry in entries:
        if entry.kind == "anchor":
            break
        if entry.kind == "message" and isinstance(entry.payload, dict):
            messages.append(dict(entry.payload))
    return messages


class IntentDecision(BaseModel):
    changed: bool = Field(..., description="True if the user intent changed.")
    anchor: str | None = Field(None, description="Short anchor name for the new task.")


class HandoffState(BaseModel):
    task: str
    facts: list[str] = Field(default_factory=list)
    next_action: str


def decide_intent(payload: IntentDecision) -> dict[str, Any]:
    return payload.model_dump()


def emit_state(payload: HandoffState) -> dict[str, Any]:
    return payload.model_dump()


class MissingEnvVarError(RuntimeError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Set {name} before running this example.")


api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise MissingEnvVarError("LLM_API_KEY")
llm = LLM(model=os.getenv("REPUBLIC_HANDOFF_MODEL", "openrouter:openai/gpt-4o-mini"), api_key=api_key)

tape = llm.tape("handoff-demo")
current_anchor: str | None = None
used_anchors: list[str] = []
decision_tool = tool_from_model(IntentDecision, decide_intent)
state_tool = tool_from_model(HandoffState, emit_state)

turns = [
    "Can you move my lunch meeting?",
    "Please move it to 12:30.",
    "I need groceries.",
    "Please add milk to the list.",
    "Actually, move the lunch meeting to 1:00.",
]

for text in turns:
    if current_anchor is None:
        history = "none"
    else:
        tape.context = TapeContext(anchor=current_anchor, select=select_task_messages)
        history_messages = [m.get("content") for m in tape.messages().messages if m.get("role") == "user"]
        history = "\n".join(history_messages[-2:]) if history_messages else "none"
    prompt = (
        "You are routing user messages into tasks. "
        f"Current task: {current_anchor or 'none'}.\n"
        f"Existing anchors: {', '.join(used_anchors) if used_anchors else 'none'}\n"
        f"Current task user history: {history}\n"
        f"User: {text}\n"
        "If the message continues the current task or adds details, call the tool with changed=false. "
        "If the user intent changed, call the tool with changed=true and propose a short anchor name. "
        "If the user returns to an existing task, reuse its anchor name. "
        "Use 1-3 lowercase words joined by underscores."
    )
    decision_calls = llm.chat.tool_calls(prompt, tools=[decision_tool], max_tokens=64)
    decision_exec = ToolExecutor().execute(decision_calls.value, tools=[decision_tool])
    decision = decision_exec.tool_results[0] if decision_exec.tool_results else {}
    changed = bool(decision.get("changed"))
    proposed = decision.get("anchor") if isinstance(decision.get("anchor"), str) else None

    if current_anchor is None:
        changed = True

    if not proposed:
        proposed = "task"

    if changed:
        if current_anchor is not None:
            tape.context = TapeContext(anchor=current_anchor, select=select_task_messages)
            task_messages = [m for m in tape.messages().messages if m.get("role") == "user"]
            state_messages = [
                *task_messages,
                {
                    "role": "system",
                    "content": (
                        "Build a minimal handoff evidence pack for the next agent. "
                        f"Task name: {current_anchor}. "
                        "You must call the tool to return: task, facts, next_action. "
                        "Facts must be explicitly stated by the user. Use at most 3 facts. "
                        "Be brief and do not add assumptions."
                    ),
                },
            ]
            state_calls = llm.chat.tool_calls(messages=state_messages, tools=[state_tool], max_tokens=96)
            state_exec = ToolExecutor().execute(state_calls.value, tools=[state_tool])
            state = state_exec.tool_results[0] if state_exec.tool_results else {}
            if state:
                payload = json.dumps(state, sort_keys=True)
                tape.append(TapeEntry.message({"role": "system", "content": f"Handoff state: {payload}"}))
            print("handoff_state=", state, "error=", state_exec.error)

        tape.handoff(proposed, state={"owner": "assistant-bot"})
        current_anchor = proposed
        if proposed not in used_anchors:
            used_anchors.append(proposed)

    tape.context = TapeContext(anchor=current_anchor, select=select_task_messages)
    reply = tape.create(text, system_prompt="Reply in one short sentence.", max_tokens=32)
    print("user=", text)
    print(
        "selected_anchor=",
        current_anchor,
        "intent_change=",
        changed,
        "decision_error=",
        decision_exec.error,
    )
    print("reply=", reply.value, "error=", reply.error)

for anchor in used_anchors:
    tape.context = TapeContext(anchor=anchor, select=select_task_messages)
    context_messages = [message.get("content") for message in tape.messages().messages]
    print(f"context_{anchor}=", context_messages)
