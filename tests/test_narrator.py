"""Narration must never be able to alter a material value.

No network is touched: a stub stands in for the LLM client so the guardrail
itself is what gets tested, not a provider.
"""
from __future__ import annotations

import pytest

from conciergeagent.core.models import NarrationMode
from conciergeagent.core.observability import METRICS
from conciergeagent.llm.client import LLMUnavailable
from conciergeagent.llm.narrator import (
    NARRATION_SYSTEM_PROMPT,
    SUPPORTED_LANGUAGES,
    build_user_prompt,
    extract_protected_facts,
    missing_facts,
    narrate,
)

DETERMINISTIC = (
    "Dear Lord Sterling, please accept our apologies. "
    "Concierge Resolution Action [TCK-FF1882A9]: instant provisional credit granted "
    "up to $50,000.00. Guaranteed SLA: 30 seconds. Private credit yielding 8.2% APY."
)


class StubClient:
    """Minimal stand-in for LLMClient."""

    model = "stub-model"

    def __init__(self, reply=None, error=None):
        self._reply = reply
        self._error = error
        self.calls = []

    def complete(self, system_prompt, user_prompt, **kwargs):
        self.calls.append((system_prompt, user_prompt))
        if self._error is not None:
            raise self._error
        return self._reply


def faithful_reply() -> str:
    return (
        "Lord Sterling, we have applied an instant provisional credit of up to $50,000.00 "
        "under reference TCK-FF1882A9, guaranteed within 30 seconds, alongside private "
        "credit yielding 8.2% APY."
    )


class TestFactExtraction:
    @pytest.mark.parametrize("fact", ["$50,000.00", "TCK-FF1882A9", "8.2%", "30 seconds"])
    def test_every_material_value_is_protected(self, fact):
        assert fact in extract_protected_facts(DETERMINISTIC)

    def test_plain_prose_has_no_protected_facts(self):
        assert extract_protected_facts("A very warm welcome to your concierge desk.") == set()

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("credit of $500", "$500"),
            ("credit of $1,250.00", "$1,250.00"),
            ("yield of 4.8%", "4.8%"),
            ("within 120 seconds", "120 seconds"),
            ("ticket TCK-0A1B2C3D", "TCK-0A1B2C3D"),
        ],
    )
    def test_individual_patterns(self, text, expected):
        assert expected in extract_protected_facts(text)

    def test_lowercase_ticket_is_not_treated_as_a_ticket(self):
        assert extract_protected_facts("tck-ff1882a9") == set()


class TestFaithfulness:
    def test_faithful_restatement_drops_nothing(self):
        assert missing_facts(DETERMINISTIC, faithful_reply()) == set()

    def test_altered_amount_is_detected(self):
        tampered = faithful_reply().replace("$50,000.00", "$500,000.00")
        assert "$50,000.00" in missing_facts(DETERMINISTIC, tampered)

    def test_dropped_ticket_is_detected(self):
        tampered = faithful_reply().replace("TCK-FF1882A9", "your case")
        assert "TCK-FF1882A9" in missing_facts(DETERMINISTIC, tampered)

    def test_shortened_sla_is_detected(self):
        tampered = faithful_reply().replace("30 seconds", "half a minute")
        assert "30 seconds" in missing_facts(DETERMINISTIC, tampered)

    def test_empty_narration_loses_every_fact(self):
        assert missing_facts(DETERMINISTIC, "") == extract_protected_facts(DETERMINISTIC)


class TestPromptConstruction:
    def test_prompt_carries_the_approved_reply(self):
        assert DETERMINISTIC in build_user_prompt(DETERMINISTIC, "Ultra-HNW")

    def test_prompt_names_the_tier(self):
        assert "Ultra-HNW" in build_user_prompt(DETERMINISTIC, "Ultra-HNW")

    @pytest.mark.parametrize("code,name", sorted(SUPPORTED_LANGUAGES.items()))
    def test_prompt_requests_the_target_language(self, code, name):
        assert name in build_user_prompt(DETERMINISTIC, "Retail", code)

    def test_unknown_language_falls_back_to_english(self):
        assert "English" in build_user_prompt(DETERMINISTIC, "Retail", "klingon")

    def test_system_prompt_forbids_changing_numbers(self):
        assert "Never change" in NARRATION_SYSTEM_PROMPT


class TestNarrate:
    def test_no_client_means_deterministic(self):
        result = narrate(DETERMINISTIC, "Ultra-HNW", None)
        assert result.mode is NarrationMode.DETERMINISTIC
        assert result.text == DETERMINISTIC

    def test_faithful_narration_is_accepted(self):
        result = narrate(DETERMINISTIC, "Ultra-HNW", StubClient(reply=faithful_reply()))
        assert result.mode is NarrationMode.LLM_NARRATED
        assert result.text == faithful_reply()

    def test_unfaithful_narration_is_discarded(self):
        tampered = faithful_reply().replace("$50,000.00", "$500,000.00")
        result = narrate(DETERMINISTIC, "Ultra-HNW", StubClient(reply=tampered))
        assert result.mode is NarrationMode.LLM_FALLBACK_UNFAITHFUL
        assert result.text == DETERMINISTIC

    def test_a_tampered_amount_never_reaches_the_customer(self):
        tampered = faithful_reply().replace("$50,000.00", "$500,000.00")
        result = narrate(DETERMINISTIC, "Ultra-HNW", StubClient(reply=tampered))
        assert "$500,000.00" not in result.text

    def test_model_failure_falls_back(self):
        client = StubClient(error=LLMUnavailable("model timed out"))
        result = narrate(DETERMINISTIC, "Ultra-HNW", client)
        assert result.mode is NarrationMode.LLM_FALLBACK_UNAVAILABLE
        assert result.text == DETERMINISTIC

    def test_fallback_is_never_silent(self):
        """Every fallback stays distinguishable from a real narration."""
        client = StubClient(error=LLMUnavailable("boom"))
        assert narrate(DETERMINISTIC, "Ultra-HNW", client).mode is not NarrationMode.LLM_NARRATED

    def test_language_reaches_the_model(self):
        client = StubClient(reply=faithful_reply())
        narrate(DETERMINISTIC, "Ultra-HNW", client, language="ar")
        assert "Arabic" in client.calls[0][1]

    def test_system_prompt_is_sent(self):
        client = StubClient(reply=faithful_reply())
        narrate(DETERMINISTIC, "Ultra-HNW", client)
        assert client.calls[0][0] == NARRATION_SYSTEM_PROMPT

    def test_narration_without_protected_facts_is_accepted(self):
        plain = "A very warm welcome to your concierge desk."
        client = StubClient(reply="Welcome. Your desk is at your service.")
        assert narrate(plain, "Retail", client).mode is NarrationMode.LLM_NARRATED

    @pytest.mark.parametrize(
        "mode_label,client_factory",
        [
            ("narrated", lambda: StubClient(reply=faithful_reply())),
            ("fallback_unavailable", lambda: StubClient(error=LLMUnavailable("x"))),
            (
                "fallback_unfaithful",
                lambda: StubClient(reply=faithful_reply().replace("8.2%", "9.9%")),
            ),
        ],
    )
    def test_each_outcome_is_counted(self, mode_label, client_factory):
        METRICS.reset()
        narrate(DETERMINISTIC, "Ultra-HNW", client_factory())
        counters = METRICS.snapshot()["counters"]
        assert any(mode_label in key for key in counters)
