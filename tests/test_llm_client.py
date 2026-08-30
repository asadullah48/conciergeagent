"""LLMClient must translate every failure mode into one exception type.

No network is touched: ``httpx.post`` is monkeypatched to return real
``httpx.Response`` objects (or raise a real ``httpx.TimeoutException``), so
the client's own status/JSON handling runs unmodified against realistic
inputs.
"""
from __future__ import annotations

import httpx
import pytest

from conciergeagent.core.config import get_settings
from conciergeagent.core.observability import METRICS
from conciergeagent.llm.client import LLMClient, LLMUnavailable

FAKE_URL = "https://fake-llm.example/v1"
_LLM_KEYS = ("LLM_ENABLED", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", "LLM_TIMEOUT_SECONDS")


@pytest.fixture
def active_settings(monkeypatch):
    """An LLM-active Settings snapshot pointed at a fake, unreachable host."""
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", FAKE_URL)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "5")
    return get_settings()


def _fake_response(status_code: int, **kwargs) -> httpx.Response:
    request = httpx.Request("POST", f"{FAKE_URL}/chat/completions")
    return httpx.Response(status_code, request=request, **kwargs)


class TestInactiveClient:
    def test_no_api_key_raises_unavailable(self, monkeypatch):
        for key in _LLM_KEYS:
            monkeypatch.delenv(key, raising=False)
        client = LLMClient(get_settings())
        with pytest.raises(LLMUnavailable):
            client.complete("system", "user")

    def test_disabled_with_a_key_still_raises_unavailable(self, monkeypatch, active_settings):
        monkeypatch.setenv("LLM_ENABLED", "false")
        client = LLMClient(get_settings())
        with pytest.raises(LLMUnavailable):
            client.complete("system", "user")

    def test_model_property_reflects_settings(self, active_settings):
        assert LLMClient(active_settings).model == "test-model"


class TestSuccessfulCompletion:
    def test_returns_stripped_content(self, monkeypatch, active_settings):
        monkeypatch.setattr(
            httpx,
            "post",
            lambda *a, **k: _fake_response(
                200, json={"choices": [{"message": {"content": "  Hello, client.  "}}]}
            ),
        )
        assert LLMClient(active_settings).complete("system", "user") == "Hello, client."

    def test_successful_call_is_counted(self, monkeypatch, active_settings):
        monkeypatch.setattr(
            httpx,
            "post",
            lambda *a, **k: _fake_response(
                200, json={"choices": [{"message": {"content": "ok"}}]}
            ),
        )
        LLMClient(active_settings).complete("system", "user")
        counters = METRICS.snapshot()["counters"]
        assert any("concierge_llm_calls_total" in key for key in counters)

    def test_request_carries_model_and_prompts(self, monkeypatch, active_settings):
        captured = {}

        def fake_post(url, *, json, headers, timeout):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return _fake_response(200, json={"choices": [{"message": {"content": "ok"}}]})

        monkeypatch.setattr(httpx, "post", fake_post)
        LLMClient(active_settings).complete("sys-prompt", "user-prompt", max_tokens=42)

        assert captured["url"] == f"{FAKE_URL}/chat/completions"
        assert captured["json"]["model"] == "test-model"
        assert captured["json"]["max_tokens"] == 42
        assert captured["json"]["messages"] == [
            {"role": "system", "content": "sys-prompt"},
            {"role": "user", "content": "user-prompt"},
        ]
        assert captured["headers"]["Authorization"] == "Bearer test-key"


class TestFailureModes:
    def test_timeout_raises_unavailable(self, monkeypatch, active_settings):
        monkeypatch.setattr(
            httpx, "post", lambda *a, **k: (_ for _ in ()).throw(httpx.TimeoutException("slow"))
        )
        with pytest.raises(LLMUnavailable):
            LLMClient(active_settings).complete("system", "user")

    def test_timeout_is_counted_with_reason(self, monkeypatch, active_settings):
        monkeypatch.setattr(
            httpx, "post", lambda *a, **k: (_ for _ in ()).throw(httpx.TimeoutException("slow"))
        )
        with pytest.raises(LLMUnavailable):
            LLMClient(active_settings).complete("system", "user")
        counters = METRICS.snapshot()["counters"]
        assert any("timeout" in key for key in counters)

    def test_rate_limited_status_raises_unavailable(self, monkeypatch, active_settings):
        monkeypatch.setattr(httpx, "post", lambda *a, **k: _fake_response(429, json={}))
        with pytest.raises(LLMUnavailable):
            LLMClient(active_settings).complete("system", "user")
        counters = METRICS.snapshot()["counters"]
        assert any("rate_limited" in key for key in counters)

    def test_other_http_error_status_raises_unavailable(self, monkeypatch, active_settings):
        monkeypatch.setattr(httpx, "post", lambda *a, **k: _fake_response(500, json={}))
        with pytest.raises(LLMUnavailable):
            LLMClient(active_settings).complete("system", "user")
        counters = METRICS.snapshot()["counters"]
        assert any("http_error" in key for key in counters)

    def test_malformed_body_raises_unavailable(self, monkeypatch, active_settings):
        monkeypatch.setattr(
            httpx, "post", lambda *a, **k: _fake_response(200, content=b"not json")
        )
        with pytest.raises(LLMUnavailable):
            LLMClient(active_settings).complete("system", "user")
        counters = METRICS.snapshot()["counters"]
        assert any("malformed" in key for key in counters)

    def test_missing_choices_key_raises_unavailable(self, monkeypatch, active_settings):
        monkeypatch.setattr(httpx, "post", lambda *a, **k: _fake_response(200, json={}))
        with pytest.raises(LLMUnavailable):
            LLMClient(active_settings).complete("system", "user")

    def test_empty_content_raises_unavailable(self, monkeypatch, active_settings):
        monkeypatch.setattr(
            httpx,
            "post",
            lambda *a, **k: _fake_response(
                200, json={"choices": [{"message": {"content": "   "}}]}
            ),
        )
        with pytest.raises(LLMUnavailable):
            LLMClient(active_settings).complete("system", "user")
        counters = METRICS.snapshot()["counters"]
        assert any("empty" in key for key in counters)
