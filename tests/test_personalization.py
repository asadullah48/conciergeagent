"""Sentiment classification and the tier SLA privilege matrix."""
from __future__ import annotations

import pytest

from conciergeagent.core.models import SentimentGrade, WealthTier
from conciergeagent.core.personalization_engine import PersonalizationEngine

classify = PersonalizationEngine.classify_sentiment
tier_sla = PersonalizationEngine.get_tier_sla


@pytest.mark.parametrize(
    "text",
    [
        "This is completely unacceptable fraud on my account!",
        "My card was stolen and nobody helped",
        "I am furious about this",
        "I will be contacting my lawyer",
        "Your service is terrible",
    ],
)
def test_distress_cues_classify_as_critical(text):
    grade, score = classify(text)
    assert grade is SentimentGrade.CRITICAL_DISTRESS
    assert score < -0.5


@pytest.mark.parametrize(
    "text",
    [
        "I am disappointed with the delay",
        "My transfer is delayed again",
        "The statement has the wrong figure",
        "There is an error on my account",
        "I am confused by this problem",
    ],
)
def test_friction_cues_classify_as_frustrated(text):
    grade, score = classify(text)
    assert grade is SentimentGrade.FRUSTRATED
    assert -0.5 < score < 0


@pytest.mark.parametrize(
    "text",
    [
        "This is brilliant and wonderful service!",
        "I love the private banking desk",
        "An amazing experience",
        "Superb, truly excellent work",
        "I am delighted",
    ],
)
def test_praise_cues_classify_as_delighted(text):
    grade, score = classify(text)
    assert grade is SentimentGrade.DELIGHTED
    assert score > 0.8


@pytest.mark.parametrize(
    "text", ["Thanks, that was helpful", "Good, I appreciate it", "That is great"]
)
def test_mild_praise_classifies_as_positive(text):
    grade, score = classify(text)
    assert grade is SentimentGrade.POSITIVE
    assert 0.5 < score < 0.8


@pytest.mark.parametrize(
    "text",
    [
        "Please confirm my next statement date",
        "What is the routing number",
        "I would like to update my address",
    ],
)
def test_factual_queries_classify_as_neutral(text):
    grade, _ = classify(text)
    assert grade is SentimentGrade.NEUTRAL


def test_classification_is_case_insensitive():
    assert classify("UNACCEPTABLE FRAUD")[0] is SentimentGrade.CRITICAL_DISTRESS


def test_distress_outranks_praise_when_both_cues_appear():
    """Safety-relevant ordering: a complaint wrapped in politeness is still a complaint."""
    grade, _ = classify("Your service is normally wonderful but this is fraud")
    assert grade is SentimentGrade.CRITICAL_DISTRESS


@pytest.mark.parametrize("raw,expected", [(-5.0, -0.2), (5.0, 0.3), (0.1, 0.1)])
def test_neutral_score_is_clamped_to_the_neutral_band(raw, expected):
    _, score = classify("What is the routing number", raw)
    assert score == pytest.approx(expected)


def test_empty_text_is_neutral():
    assert classify("", 0.0)[0] is SentimentGrade.NEUTRAL


@pytest.mark.parametrize(
    "tier,seconds,credit,gift",
    [
        (WealthTier.ULTRA_HNW, 30, 50_000.0, True),
        (WealthTier.PRIVATE_CLIENT, 60, 10_000.0, True),
        (WealthTier.PREMIER, 120, 2_500.0, False),
        (WealthTier.RETAIL, 300, 500.0, False),
    ],
)
def test_tier_sla_matrix_matches_the_spec(tier, seconds, credit, gift):
    sla = tier_sla(tier)
    assert sla["sla_seconds"] == seconds
    assert sla["max_dispute_auto_credit"] == credit
    assert sla["concierge_gift_eligible"] is gift


def test_sla_tightens_as_tier_rises():
    order = [WealthTier.RETAIL, WealthTier.PREMIER, WealthTier.PRIVATE_CLIENT, WealthTier.ULTRA_HNW]
    seconds = [tier_sla(t)["sla_seconds"] for t in order]
    assert seconds == sorted(seconds, reverse=True)


def test_dispute_limit_rises_with_tier():
    order = [WealthTier.RETAIL, WealthTier.PREMIER, WealthTier.PRIVATE_CLIENT, WealthTier.ULTRA_HNW]
    limits = [tier_sla(t)["max_dispute_auto_credit"] for t in order]
    assert limits == sorted(limits)


@pytest.mark.parametrize("tier", list(WealthTier))
def test_every_tier_has_a_named_officer(tier):
    assert tier_sla(tier)["dedicated_officer"].strip()
