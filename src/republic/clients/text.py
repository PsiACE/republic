"""Text helpers for Republic."""

from __future__ import annotations

from textwrap import dedent
from typing import Any, List, Protocol

from republic.core.errors import ErrorKind, RepublicError


class ChatCaller(Protocol):
    def create(self, prompt: str, **kwargs: Any) -> str:
        ...


class TextClient:
    """Lightweight text helpers built on chat completions."""

    def __init__(self, chat: ChatCaller) -> None:
        self._chat = chat

    def if_(self, input_text: str, question: str) -> bool:
        prompt = dedent(
            f"""
            Here is an input:
            <input>
            {input_text.strip()}
            </input>

            And a question:
            <question>
            {question.strip()}
            </question>

            Answer with only 'yes' or 'no'.
            """
        ).strip()

        response = self._chat.create(prompt)
        return "yes" in response.strip().lower()

    def classify(self, input_text: str, choices: List[str]) -> str:
        if not choices:
            raise RepublicError(ErrorKind.INVALID_INPUT, "choices must not be empty.")
        normalized_choices = [choice.strip().lower() for choice in choices]
        choices_str = ", ".join(normalized_choices)

        prompt = dedent(
            f"""
            You are given this input:
            <input>
            {input_text.strip()}
            </input>

            And the following choices:
            <choices>
            {choices_str}
            </choices>

            Answer with only one of the choices.
            """
        ).strip()

        response = self._chat.create(prompt).strip().lower()
        if response in normalized_choices:
            return response
        return normalized_choices[0]
