"""Thin wrapper around the Claude API, plus an offline fake for tests.

Rules this module keeps:
- The API key is read from the environment (or .env) and is never printed,
  logged or put into an error message.
- The model name comes from KETANA_MODEL, so it can change without code edits.
- Tests use FakeClient, so they never call the network or cost money.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

DEFAULT_MODEL = "claude-sonnet-5-5"
DEFAULT_MAX_TOKENS = 1500


class LLMError(Exception):
    """Anything that goes wrong talking to the model (message is safe to show)."""


@dataclass
class LLMResponse:
    text: str = ""
    tool_input: dict | None = None
    model: str = ""


class ClaudeClient:
    def __init__(self, api_key: str | None = None, model: str | None = None,
                 max_tokens: int = DEFAULT_MAX_TOKENS):
        load_dotenv()
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise LLMError(
                "ANTHROPIC_API_KEY is not set. Put it in the .env file in the "
                "project root (one line: ANTHROPIC_API_KEY=...)."
            )
        from anthropic import Anthropic

        self._client = Anthropic(api_key=key)
        self.model = model or os.environ.get("KETANA_MODEL") or DEFAULT_MODEL
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str, tool: dict | None = None) -> LLMResponse:
        """Send one request. If `tool` is given, the model is forced to call it."""
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if tool is not None:
            kwargs["tools"] = [tool]
            kwargs["tool_choice"] = {"type": "tool", "name": tool["name"]}
        try:
            msg = self._client.messages.create(**kwargs)
        except Exception as exc:
            # Only the server's own message is shown (status + text from Anthropic);
            # never str(exc) for other errors, to keep secrets out of messages.
            detail = ""
            status = getattr(exc, "status_code", None)
            body = getattr(exc, "body", None)
            if status and isinstance(body, dict):
                inner = body.get("error") if isinstance(body.get("error"), dict) else {}
                detail = f" [{status}] {inner.get('message', '')}".rstrip()
            raise LLMError(f"Claude request failed ({type(exc).__name__}).{detail}") from exc

        text, tool_input = "", None
        for block in msg.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_input = dict(block.input)
        return LLMResponse(text=text, tool_input=tool_input, model=self.model)


@dataclass
class FakeClient:
    """Offline stand-in. `responses` are returned in order, one per call."""

    responses: list = field(default_factory=list)
    calls: list = field(default_factory=list)
    model: str = "fake-model"

    def complete(self, system: str, user: str, tool: dict | None = None) -> LLMResponse:
        self.calls.append({"system": system, "user": user, "tool": tool})
        if not self.responses:
            raise LLMError("FakeClient has no more scripted responses.")
        item = self.responses.pop(0)
        if isinstance(item, LLMResponse):
            return item
        if isinstance(item, dict):
            return LLMResponse(tool_input=item, model=self.model)
        return LLMResponse(text=str(item), model=self.model)
