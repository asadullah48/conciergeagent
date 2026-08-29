"""Sentiment classification and the wealth-tier privilege matrix."""
from __future__ import annotations

from typing import Any

from conciergeagent.core.models import SentimentGrade, WealthTier

# Lexical cues, evaluated in order of severity: a complaint wrapped in
# politeness is still a complaint, so distress outranks praise.
DISTRESS_CUES = (
    "unacceptable",
    "terrible",
    "fraud",
    "stolen",
    "lawyer",
    "angry",
    "furious",
)
FRICTION_CUES = (
    "disappointed",
    "delayed",
    "wrong",
    "issue",
    "error",
    "confused",
    "problem",
)
DELIGHT_CUES = (
    "excellent",
    "wonderful",
    "love",
    "amazing",
    "delighted",
    "superb",
    "brilliant",
)
PRAISE_CUES = ("good", "thanks", "helpful", "great", "appreciate")

NEUTRAL_SCORE_FLOOR = -0.2
NEUTRAL_SCORE_CEILING = 0.3

_TIER_SLA: dict[WealthTier, dict[str, Any]] = {
    WealthTier.ULTRA_HNW: {
        "sla_seconds": 30,
        "dedicated_officer": "Executive Family Office Lead",
        "max_dispute_auto_credit": 50_000.0,
        "concierge_gift_eligible": True,
    },
    WealthTier.PRIVATE_CLIENT: {
        "sla_seconds": 60,
        "dedicated_officer": "Senior Private Banker",
        "max_dispute_auto_credit": 10_000.0,
        "concierge_gift_eligible": True,
    },
    WealthTier.PREMIER: {
        "sla_seconds": 120,
        "dedicated_officer": "Premier Relationship Manager",
        "max_dispute_auto_credit": 2_500.0,
        "concierge_gift_eligible": False,
    },
    WealthTier.RETAIL: {
        "sla_seconds": 300,
        "dedicated_officer": "Digital Concierge Assistant",
        "max_dispute_auto_credit": 500.0,
        "concierge_gift_eligible": False,
    },
}


class PersonalizationEngine:
    """Grades customer sentiment and resolves tier-based service privileges."""

    @staticmethod
    def classify_sentiment(text: str, raw_score: float = 0.5) -> tuple[SentimentGrade, float]:
        """Map free text to a sentiment grade and a normalised score."""
        lowered = text.lower()

        if any(cue in lowered for cue in DISTRESS_CUES):
            return SentimentGrade.CRITICAL_DISTRESS, -0.90
        if any(cue in lowered for cue in FRICTION_CUES):
            return SentimentGrade.FRUSTRATED, -0.40
        if any(cue in lowered for cue in DELIGHT_CUES):
            return SentimentGrade.DELIGHTED, 0.95
        if any(cue in lowered for cue in PRAISE_CUES):
            return SentimentGrade.POSITIVE, 0.70

        clamped = max(NEUTRAL_SCORE_FLOOR, min(NEUTRAL_SCORE_CEILING, raw_score))
        return SentimentGrade.NEUTRAL, clamped

    @staticmethod
    def get_tier_sla(tier: WealthTier) -> dict[str, Any]:
        """Return the SLA, officer, and auto-credit limit for a wealth tier."""
        return dict(_TIER_SLA[tier])
