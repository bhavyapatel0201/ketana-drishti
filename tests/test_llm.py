from types import SimpleNamespace

import pytest

from ketana_drishti import llm
from ketana_drishti.llm import ClaudeClient, FakeClient, LLMError, LLMResponse


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    # Never read the developer's real .env during tests.
    monkeypatch.setattr(llm, "load_dotenv", lambda *a, **k: None)


def test_missing_key_gives_clear_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        ClaudeClient()


def test_model_default_and_env_override(monkeypatch):
    monkeypatch.delenv("KETANA_MODEL", raising=False)
    assert ClaudeClient(api_key="k").model == llm.DEFAULT_MODEL
    monkeypatch.setenv("KETANA_MODEL", "claude-opus-5-5")
    assert ClaudeClient(api_key="k").model == "claude-opus-5-5"
    assert ClaudeClient(api_key="k", model="x").model == "x"


class _Stub:
    def __init__(self, content=None, boom=False):
        self.kwargs = None
        self._content, self._boom = content, boom
        self.messages = self

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self._boom:
            raise RuntimeError("secret-key-123 leaked in message")
        return SimpleNamespace(content=self._content)


def test_complete_forces_tool_and_parses_input():
    c = ClaudeClient(api_key="k")
    c._client = _Stub([SimpleNamespace(type="tool_use", input={"statements": []})])
    tool = {"name": "give_reading", "description": "d", "input_schema": {"type": "object"}}
    r = c.complete("sys", "usr", tool=tool)
    assert r.tool_input == {"statements": []}
    assert c._client.kwargs["tool_choice"] == {"type": "tool", "name": "give_reading"}
    assert c._client.kwargs["system"] == "sys"


def test_complete_plain_text():
    c = ClaudeClient(api_key="k")
    c._client = _Stub([SimpleNamespace(type="text", text="hello")])
    r = c.complete("s", "u")
    assert r.text == "hello" and r.tool_input is None
    assert "tools" not in c._client.kwargs


def test_errors_never_leak_the_underlying_message():
    c = ClaudeClient(api_key="k")
    c._client = _Stub(boom=True)
    with pytest.raises(LLMError) as e:
        c.complete("s", "u")
    assert "secret-key-123" not in str(e.value)


def test_fake_client_scripts_and_records():
    f = FakeClient(["hi", {"a": 1}, LLMResponse(text="x")])
    assert f.complete("s", "u").text == "hi"
    assert f.complete("s", "u").tool_input == {"a": 1}
    assert f.complete("s", "u").text == "x"
    assert len(f.calls) == 3
    with pytest.raises(LLMError):
        f.complete("s", "u")


def test_api_error_shows_server_message_only():
    class Boom(Exception):
        status_code = 400
        body = {"error": {"message": "credit balance is too low"}}

    c = ClaudeClient(api_key="k")

    class S:
        messages = None

        def create(self, **kw):
            raise Boom("raw text with sk-ant-secret")

    s = S()
    s.messages = s
    c._client = s
    with pytest.raises(LLMError) as e:
        c.complete("s", "u")
    assert "credit balance is too low" in str(e.value)
    assert "sk-ant-secret" not in str(e.value)
