"""Minimal client for any OpenAI-compatible chat completions endpoint.

No provider SDK: the request shape is identical across Groq, Cerebras,
OpenRouter, Together and the Gemini compatibility endpoint, so a single
httpx call covers all of them - and httpx is already a runtime dependency.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from conciergeagent.core.config import Settings
from conciergeagent.core.observability import METRICS

logger = logging.getLogger(__name__)


class LLMUnavailable(RuntimeError):
    """The model could not be reached, or returned something unusable.

    Deliberately one exception type: from the caller point of view a timeout,
    a rate limit and a malformed body all mean the same thing - narration is
    not available for this request, serve the deterministic text.
    """


class LLMClient:
    """Single-shot chat completion. No retries by design.

    A concierge reply is on a tier SLA measured in seconds; burning that
    budget on retrying a rate-limited free-tier endpoint serves the customer
    worse than answering immediately from the rule engine.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def model(self) -> str:
        return self._settings.llm_model

    def complete(self, system_prompt: str, user_prompt: str, *, max_tokens: int = 600) -> str:
        settings = self._settings
        if not settings.llm_active:
            raise LLMUnavailable("no API key configured")

        payload: dict[str, Any] = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
            "max_tokens": max_tokens,
        }

        try:
            response = httpx.post(
                f"{settings.llm_base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                timeout=settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except httpx.TimeoutException as exc:
            METRICS.increment("concierge_llm_failures_total", {"reason": "timeout"})
            raise LLMUnavailable("model timed out") from exc
        except httpx.HTTPStatusError as exc:
            reason = "rate_limited" if exc.response.status_code == 429 else "http_error"
            METRICS.increment("concierge_llm_failures_total", {"reason": reason})
            raise LLMUnavailable(f"model returned {exc.response.status_code}") from exc
        except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError) as exc:
            METRICS.increment("concierge_llm_failures_total", {"reason": "malformed"})
            raise LLMUnavailable("model response was unusable") from exc

        if not isinstance(content, str) or not content.strip():
            METRICS.increment("concierge_llm_failures_total", {"reason": "empty"})
            raise LLMUnavailable("model returned empty content")

        METRICS.increment("concierge_llm_calls_total", {"model": settings.llm_model})
        return content.strip()
