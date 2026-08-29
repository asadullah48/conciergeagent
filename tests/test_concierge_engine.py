"""ConciergeEngine routing, response assembly, CSAT, and metrics emission."""
from __future__ import annotations

import pytest

from conciergeagent.core.models import (
    IntentCategory,
    SentimentGrade,
    ServiceInteraction,
    WealthTier,
)
from conciergeagent.core.observability import METRICS
from conciergeagent.orchestration.concierge_engine import ConciergeEngine
from tests.conftest import CRITICAL_QUERY, DELIGHTED_QUERY, NEUTRAL_QUERY


@pytest.fixture
def engine() -> ConciergeEngine:
    return ConciergeEngine()


def _interact(engine, profile, query=NEUTRAL_QUERY, intent=IntentCategory.ADVISORY, sentiment=0.5):
    return engine.process_interaction(
        ServiceInteraction(
            customer_profile=profile,
            user_query=query,
            intent_category=intent,
            raw_sentiment_score=sentiment,
        )
    )


class TestRouting:
    def test_advisory_intent_produces_only_an_advisory(self, engine, profile_factory):
        result = _interact(engine, profile_factory(), intent=IntentCategory.ADVISORY)
        assert result.advisory_recommendation is not None
        assert result.support_resolution is None

    def test_support_intent_produces_only_a_resolution(self, engine, profile_factory):
        result = _interact(engine, profile_factory(), intent=IntentCategory.SUPPORT)
        assert result.support_resolution is not None
        assert result.advisory_recommendation is None

    def test_loyalty_intent_produces_neither_payload(self, engine, profile_factory):
        result = _interact(engine, profile_factory(), intent=IntentCategory.LOYALTY)
        assert result.support_resolution is None
        assert result.advisory_recommendation is None

    @pytest.mark.parametrize("intent", list(IntentCategory))
    def test_routed_intent_is_reported_back(self, engine, profile_factory, intent):
        assert _interact(engine, profile_factory(), intent=intent).intent_routed is intent

    def test_declared_intent_is_not_overridden_by_query_keywords(self, engine, profile_factory):
        """Regression guard: a SUPPORT request containing the word tax used to be
        re-routed to the advisor, silently discarding the declared intent.
        """
        result = _interact(
            engine,
            profile_factory(),
            query="There is a disputed charge on my tax payment",
            intent=IntentCategory.SUPPORT,
        )
        assert result.support_resolution is not None
        assert result.advisory_recommendation is None

    def test_loyalty_lane_reports_the_points_balance(self, engine, profile_factory):
        profile = profile_factory(loyalty_points=145_000)
        result = _interact(engine, profile, intent=IntentCategory.LOYALTY)
        assert "145,000" in result.concierge_response_text


class TestResponseAssembly:
    def test_response_opens_with_the_empathetic_greeting(self, engine, profile_factory):
        result = _interact(engine, profile_factory())
        assert result.concierge_response_text.startswith(
            result.experience_review.empathetic_opening
        )

    def test_response_closes_with_the_courtesy(self, engine, profile_factory):
        result = _interact(engine, profile_factory())
        assert result.concierge_response_text.rstrip().endswith(
            result.experience_review.closing_courtesy
        )

    def test_awarded_perk_appears_in_the_response(self, engine, profile_factory):
        result = _interact(engine, profile_factory(WealthTier.ULTRA_HNW), DELIGHTED_QUERY)
        assert result.experience_review.loyalty_perk_awarded in result.concierge_response_text

    def test_no_perk_section_when_nothing_is_awarded(self, engine, profile_factory):
        result = _interact(engine, profile_factory(WealthTier.RETAIL), NEUTRAL_QUERY)
        assert result.experience_review.loyalty_perk_awarded is None
        assert "Concierge Privilege Applied" not in result.concierge_response_text

    def test_ticket_id_is_surfaced_in_a_support_response(self, engine, profile_factory):
        result = _interact(engine, profile_factory(), intent=IntentCategory.SUPPORT)
        assert result.support_resolution.ticket_id in result.concierge_response_text

    def test_profile_fields_are_echoed_back(self, engine, profile_factory):
        profile = profile_factory(WealthTier.PREMIER, name="Julian Ross", customer_id="CUST-77")
        result = _interact(engine, profile)
        assert result.customer_name == "Julian Ross"
        assert result.customer_id == "CUST-77"
        assert result.wealth_tier is WealthTier.PREMIER


class TestCsatPrediction:
    def test_five_star_interaction_scores_highest(self, engine, profile_factory):
        assert _interact(engine, profile_factory(), NEUTRAL_QUERY).csat_predicted_score == 4.95

    def test_escalation_reduces_the_predicted_score(self, engine, profile_factory):
        happy = _interact(engine, profile_factory(), NEUTRAL_QUERY)
        distressed = _interact(engine, profile_factory(), CRITICAL_QUERY, sentiment=-0.9)
        assert distressed.csat_predicted_score < happy.csat_predicted_score

    @pytest.mark.parametrize("query", [NEUTRAL_QUERY, DELIGHTED_QUERY, CRITICAL_QUERY])
    def test_score_stays_within_the_valid_range(self, engine, profile_factory, query):
        assert 0.0 <= _interact(engine, profile_factory(), query).csat_predicted_score <= 5.0


class TestDeterminismAndTiming:
    def test_session_id_is_stable_for_identical_input(self, engine, profile_factory):
        profile = profile_factory()
        assert _interact(engine, profile).session_id == _interact(engine, profile).session_id

    def test_session_id_varies_with_intent(self, engine, profile_factory):
        profile = profile_factory()
        advisory = _interact(engine, profile, intent=IntentCategory.ADVISORY).session_id
        support = _interact(engine, profile, intent=IntentCategory.SUPPORT).session_id
        assert advisory != support

    def test_execution_time_is_recorded(self, engine, profile_factory):
        assert _interact(engine, profile_factory()).execution_time_ms >= 0.0


class TestMetrics:
    def test_interaction_counter_is_labelled_by_tier_and_intent(self, engine, profile_factory):
        _interact(engine, profile_factory(WealthTier.ULTRA_HNW), intent=IntentCategory.SUPPORT)
        counters = METRICS.snapshot()["counters"]
        assert any(
            "ULTRA_HNW" in key and "SUPPORT" in key
            for key in counters
            if key.startswith("concierge_interactions_total")
        )

    def test_sentiment_counter_is_recorded(self, engine, profile_factory):
        _interact(engine, profile_factory(), DELIGHTED_QUERY)
        assert any(
            SentimentGrade.DELIGHTED.value in key for key in METRICS.snapshot()["counters"]
        )

    def test_escalation_counter_only_fires_on_escalation(self, engine, profile_factory):
        _interact(engine, profile_factory(), NEUTRAL_QUERY)
        assert not any(
            key.startswith("concierge_escalations_total") for key in METRICS.snapshot()["counters"]
        )
        _interact(engine, profile_factory(), CRITICAL_QUERY, sentiment=-0.9)
        assert any(
            key.startswith("concierge_escalations_total") for key in METRICS.snapshot()["counters"]
        )

    def test_latency_is_observed_once_per_interaction(self, engine, profile_factory):
        _interact(engine, profile_factory())
        _interact(engine, profile_factory())
        assert METRICS.snapshot()["latency_count"] == 2


@pytest.mark.parametrize("tier", list(WealthTier))
@pytest.mark.parametrize("intent", list(IntentCategory))
def test_full_matrix_produces_a_valid_response(engine, profile_factory, tier, intent):
    result = _interact(engine, profile_factory(tier), intent=intent)
    assert result.concierge_response_text.strip()
    assert result.session_id.startswith("SES-")
