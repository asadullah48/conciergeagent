"""ExperienceAgent hospitality audit, escalation, and entitlement wiring."""
from __future__ import annotations

import pytest

from conciergeagent.agents.experience_agent import ExperienceAgent
from conciergeagent.core.models import SentimentGrade, WealthTier
from tests.conftest import (
    CRITICAL_QUERY,
    DELIGHTED_QUERY,
    FRUSTRATED_QUERY,
    NEUTRAL_QUERY,
    POSITIVE_QUERY,
)

QUERY_FOR_GRADE = {
    SentimentGrade.DELIGHTED: DELIGHTED_QUERY,
    SentimentGrade.POSITIVE: POSITIVE_QUERY,
    SentimentGrade.NEUTRAL: NEUTRAL_QUERY,
    SentimentGrade.FRUSTRATED: FRUSTRATED_QUERY,
    SentimentGrade.CRITICAL_DISTRESS: CRITICAL_QUERY,
}


@pytest.fixture
def agent() -> ExperienceAgent:
    return ExperienceAgent()


@pytest.mark.parametrize("grade", list(SentimentGrade))
def test_each_query_reaches_its_intended_grade(agent, profile_factory, grade):
    review = agent.audit_experience(profile_factory(), QUERY_FOR_GRADE[grade], 0.5)
    assert review.sentiment_grade is grade


@pytest.mark.parametrize(
    "grade,rating",
    [
        (SentimentGrade.DELIGHTED, 5),
        (SentimentGrade.POSITIVE, 5),
        (SentimentGrade.NEUTRAL, 5),
        (SentimentGrade.FRUSTRATED, 3),
        (SentimentGrade.CRITICAL_DISTRESS, 1),
    ],
)
def test_hospitality_rating_per_grade(agent, profile_factory, grade, rating):
    review = agent.audit_experience(profile_factory(), QUERY_FOR_GRADE[grade], 0.5)
    assert review.hospitality_rating == rating


def test_only_critical_distress_escalates(agent, profile_factory):
    """SPEC.md section 4: frustration is remediated in-channel, not handed over."""
    escalating = {
        grade
        for grade in SentimentGrade
        if agent.audit_experience(
            profile_factory(), QUERY_FOR_GRADE[grade], 0.5
        ).executive_escalation_required
    }
    assert escalating == {SentimentGrade.CRITICAL_DISTRESS}


@pytest.mark.parametrize("tier", list(WealthTier))
def test_neutral_interaction_awards_no_perk(agent, profile_factory, tier):
    review = agent.audit_experience(profile_factory(tier), NEUTRAL_QUERY, 0.0)
    assert review.loyalty_perk_awarded is None


def test_ultra_hnw_delight_unlocks_the_flagship_reward(agent, profile_factory):
    review = agent.audit_experience(
        profile_factory(WealthTier.ULTRA_HNW), DELIGHTED_QUERY, 0.9
    )
    assert "Private Jet" in review.loyalty_perk_awarded


def test_distress_awards_a_recovery_credit_not_a_luxury_gift(agent, profile_factory):
    review = agent.audit_experience(profile_factory(WealthTier.PREMIER), CRITICAL_QUERY, -0.8)
    assert "Service Recovery Credit" in review.loyalty_perk_awarded
    assert "Private Jet" not in review.loyalty_perk_awarded


@pytest.mark.parametrize("grade", list(SentimentGrade))
def test_opening_always_addresses_the_customer_by_name(agent, profile_factory, grade):
    profile = profile_factory(name="Lady Victoria")
    review = agent.audit_experience(profile, QUERY_FOR_GRADE[grade], 0.5)
    assert "Lady Victoria" in review.empathetic_opening


@pytest.mark.parametrize(
    "grade", [SentimentGrade.CRITICAL_DISTRESS, SentimentGrade.FRUSTRATED]
)
def test_negative_openings_apologise(agent, profile_factory, grade):
    review = agent.audit_experience(profile_factory(), QUERY_FOR_GRADE[grade], -0.5)
    assert any(word in review.empathetic_opening.lower() for word in ("apolog", "sorry"))


@pytest.mark.parametrize(
    "grade", [SentimentGrade.DELIGHTED, SentimentGrade.POSITIVE, SentimentGrade.NEUTRAL]
)
def test_non_negative_openings_do_not_apologise(agent, profile_factory, grade):
    review = agent.audit_experience(profile_factory(), QUERY_FOR_GRADE[grade], 0.8)
    assert "apolog" not in review.empathetic_opening.lower()


def test_escalated_closing_references_the_handover(agent, profile_factory):
    review = agent.audit_experience(profile_factory(), CRITICAL_QUERY, -0.9)
    assert "handover" in review.closing_courtesy.lower()


def test_standard_closing_references_standby_cover(agent, profile_factory):
    review = agent.audit_experience(profile_factory(), NEUTRAL_QUERY, 0.0)
    assert "standby" in review.closing_courtesy.lower()


@pytest.mark.parametrize("tier", list(WealthTier))
@pytest.mark.parametrize("grade", list(SentimentGrade))
def test_audit_never_raises_across_the_matrix(agent, profile_factory, tier, grade):
    review = agent.audit_experience(profile_factory(tier), QUERY_FOR_GRADE[grade], 0.0)
    assert review.empathetic_opening and review.closing_courtesy


def test_tier_label_is_humanised_in_the_greeting(agent, profile_factory):
    review = agent.audit_experience(profile_factory(WealthTier.PRIVATE_CLIENT), NEUTRAL_QUERY, 0.0)
    assert "Private Client" in review.empathetic_opening
    assert "PRIVATE_CLIENT" not in review.empathetic_opening


def test_agent_reports_its_identity(agent):
    assert agent.name == "ExperienceAgent"
    assert agent.version
