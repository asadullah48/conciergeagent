"""Perk entitlement policy: who receives what, and why.

Two economically distinct instruments were previously conflated into a single
"perk" string, which produced a perverse incentive -- a frustrated customer
earned a richer payout than a delighted one:

  * SERVICE RECOVERY -- goodwill issued *after a service failure*. It is a cost
    of remediation, is expensed against the support budget, and is owed
    regardless of tier because the failure was ours.
  * LOYALTY REWARD -- recognition of relationship value. It is a marketing
    spend, is gated on wealth tier per the SPEC privilege matrix, and is never
    owed -- it is discretionary.

Keeping them separate means "being angry" and "being delighted" draw on
different budgets and can no longer be compared as if they were the same prize.
"""
from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from conciergeagent.core.models import SentimentGrade, WealthTier

GIFT_ELIGIBLE_TIERS = frozenset({WealthTier.ULTRA_HNW, WealthTier.PRIVATE_CLIENT})


class PerkCategory(str, Enum):
    SERVICE_RECOVERY = "SERVICE_RECOVERY"
    LOYALTY_REWARD = "LOYALTY_REWARD"


class PerkAward(NamedTuple):
    """A single entitlement decision, with the reason it was made."""

    category: PerkCategory
    description: str
    goodwill_credit_usd: float = 0.0


# Tier -> service recovery credit issued after a *critical* failure.
_CRITICAL_RECOVERY_CREDIT = {
    WealthTier.ULTRA_HNW: 2_500.0,
    WealthTier.PRIVATE_CLIENT: 1_000.0,
    WealthTier.PREMIER: 500.0,
    WealthTier.RETAIL: 250.0,
}

# Tier -> loyalty reward granted to a genuinely delighted client.
_DELIGHTED_REWARD = {
    WealthTier.ULTRA_HNW: "10,000 Bonus Loyalty Points + Private Jet & Dining Concierge Access",
    WealthTier.PRIVATE_CLIENT: "5,000 Bonus Loyalty Points + Luxury Lounge Access",
    WealthTier.PREMIER: "2,500 Bonus Loyalty Points + Preferred Deposit Rate Bonus (+0.65%)",
    WealthTier.RETAIL: "1,000 Loyalty Reward Points",
}


def determine_perk(tier: WealthTier, grade: SentimentGrade) -> PerkAward | None:
    """Decide the entitlement for one interaction, or ``None`` for no award.

    Baseline policy, reconciling SPEC.md sections 3 (tier privilege matrix) and
    4 (sentiment escalation tree):

    ============================  ========================================
    Sentiment grade               Award
    ============================  ========================================
    CRITICAL_DISTRESS             Service recovery, tier-scaled credit
    FRUSTRATED                    Service recovery, half the critical credit
    DELIGHTED                     Loyalty reward, tier-gated
    POSITIVE                      Loyalty reward only for gift-eligible tiers
    NEUTRAL                       None -- standard hospitality only
    ============================  ========================================
    """
    if grade is SentimentGrade.CRITICAL_DISTRESS:
        credit = _CRITICAL_RECOVERY_CREDIT[tier]
        return PerkAward(
            PerkCategory.SERVICE_RECOVERY,
            f"Priority Service Recovery Credit (${credit:,.2f}) with executive case ownership",
            credit,
        )

    if grade is SentimentGrade.FRUSTRATED:
        credit = _CRITICAL_RECOVERY_CREDIT[tier] / 2
        return PerkAward(
            PerkCategory.SERVICE_RECOVERY,
            f"Service Recovery Credit (${credit:,.2f}) applied to your account",
            credit,
        )

    if grade is SentimentGrade.DELIGHTED:
        return PerkAward(PerkCategory.LOYALTY_REWARD, _DELIGHTED_REWARD[tier])

    if grade is SentimentGrade.POSITIVE and tier in GIFT_ELIGIBLE_TIERS:
        return PerkAward(
            PerkCategory.LOYALTY_REWARD, "2,500 Bonus Loyalty Points + Luxury Lounge Access"
        )

    # NEUTRAL, and POSITIVE below the gifting threshold: hospitality only.
    return None
