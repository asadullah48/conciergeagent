"""Perk entitlement policy across the full tier x sentiment matrix."""
from __future__ import annotations

import pytest

from conciergeagent.core.loyalty_policy import (
    GIFT_ELIGIBLE_TIERS,
    PerkCategory,
    determine_perk,
)
from conciergeagent.core.models import SentimentGrade, WealthTier

RECOVERY_GRADES = (SentimentGrade.FRUSTRATED, SentimentGrade.CRITICAL_DISTRESS)


@pytest.mark.parametrize("tier", list(WealthTier))
def test_neutral_never_earns_a_perk(tier):
    """SPEC.md section 4: neutral sentiment receives hospitality only."""
    assert determine_perk(tier, SentimentGrade.NEUTRAL) is None


@pytest.mark.parametrize("tier", list(WealthTier))
@pytest.mark.parametrize("grade", RECOVERY_GRADES)
def test_service_failure_always_triggers_recovery_regardless_of_tier(tier, grade):
    award = determine_perk(tier, grade)
    assert award is not None
    assert award.category is PerkCategory.SERVICE_RECOVERY
    assert award.goodwill_credit_usd > 0


@pytest.mark.parametrize("tier", list(WealthTier))
def test_delight_always_earns_a_loyalty_reward(tier):
    award = determine_perk(tier, SentimentGrade.DELIGHTED)
    assert award is not None
    assert award.category is PerkCategory.LOYALTY_REWARD
    assert award.goodwill_credit_usd == 0.0


@pytest.mark.parametrize("tier", sorted(GIFT_ELIGIBLE_TIERS, key=lambda t: t.value))
def test_positive_sentiment_rewards_gift_eligible_tiers(tier):
    award = determine_perk(tier, SentimentGrade.POSITIVE)
    assert award is not None
    assert award.category is PerkCategory.LOYALTY_REWARD


@pytest.mark.parametrize(
    "tier", [t for t in WealthTier if t not in GIFT_ELIGIBLE_TIERS]
)
def test_positive_sentiment_does_not_reward_ineligible_tiers(tier):
    assert determine_perk(tier, SentimentGrade.POSITIVE) is None


@pytest.mark.parametrize("tier", list(WealthTier))
def test_critical_credit_is_double_the_frustrated_credit(tier):
    critical = determine_perk(tier, SentimentGrade.CRITICAL_DISTRESS)
    frustrated = determine_perk(tier, SentimentGrade.FRUSTRATED)
    assert critical.goodwill_credit_usd == pytest.approx(frustrated.goodwill_credit_usd * 2)


def test_recovery_credit_increases_with_tier():
    credits = [
        determine_perk(tier, SentimentGrade.CRITICAL_DISTRESS).goodwill_credit_usd
        for tier in (
            WealthTier.RETAIL,
            WealthTier.PREMIER,
            WealthTier.PRIVATE_CLIENT,
            WealthTier.ULTRA_HNW,
        )
    ]
    assert credits == sorted(credits)
    assert len(set(credits)) == len(credits)


def test_recovery_and_reward_are_distinct_categories():
    """Regression guard for the perverse incentive: distress and delight must
    not be payable from the same instrument."""
    distress = determine_perk(WealthTier.RETAIL, SentimentGrade.CRITICAL_DISTRESS)
    delight = determine_perk(WealthTier.RETAIL, SentimentGrade.DELIGHTED)
    assert distress.category is not delight.category


@pytest.mark.parametrize("tier", list(WealthTier))
def test_delight_reward_is_never_a_cash_credit(tier):
    """Rewards are marketing spend, not remediation cash."""
    assert determine_perk(tier, SentimentGrade.DELIGHTED).goodwill_credit_usd == 0.0


@pytest.mark.parametrize("tier", list(WealthTier))
@pytest.mark.parametrize("grade", list(SentimentGrade))
def test_every_matrix_cell_is_defined(tier, grade):
    """No tier/grade combination may raise -- the matrix must be total."""
    award = determine_perk(tier, grade)
    assert award is None or award.description


def test_gift_eligible_tiers_match_the_spec_privilege_matrix():
    assert {WealthTier.ULTRA_HNW, WealthTier.PRIVATE_CLIENT} == GIFT_ELIGIBLE_TIERS


def test_recovery_description_states_the_credit_amount():
    award = determine_perk(WealthTier.ULTRA_HNW, SentimentGrade.CRITICAL_DISTRESS)
    assert f"{award.goodwill_credit_usd:,.2f}" in award.description
