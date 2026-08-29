"""ExperienceAgent: hospitality auditing, tone modulation, and entitlement."""
from __future__ import annotations

from conciergeagent.core.loyalty_policy import determine_perk
from conciergeagent.core.models import (
    CustomerProfile,
    ExperienceReview,
    SentimentGrade,
)
from conciergeagent.core.personalization_engine import PersonalizationEngine

# Hospitality rating delivered per sentiment grade (1-5 stars).
_HOSPITALITY_RATING: dict[SentimentGrade, int] = {
    SentimentGrade.DELIGHTED: 5,
    SentimentGrade.POSITIVE: 5,
    SentimentGrade.NEUTRAL: 5,
    SentimentGrade.FRUSTRATED: 3,
    SentimentGrade.CRITICAL_DISTRESS: 1,
}

# Per SPEC.md section 4, only critical distress triggers a human handover.
# Frustration is remediated in-channel with an apology and a recovery credit.
_ESCALATION_GRADES = frozenset({SentimentGrade.CRITICAL_DISTRESS})


class ExperienceAgent:
    """Audits interaction hospitality, crafts empathetic phrasing, awards
    entitlements, and triggers executive handover when a case warrants it.
    """

    def __init__(self) -> None:
        self.name = "ExperienceAgent"
        self.version = "2.0.0"

    @staticmethod
    def _compose_opening(profile: CustomerProfile, grade: SentimentGrade) -> str:
        """Greet in the register the sentiment calls for.

        The neutral greeting names the dedicated officer from the SPEC tier
        matrix rather than the tier itself: "valued Private Client client"
        reads as a mistake, while "Your Senior Private Banker" is both
        correct and warmer.
        """
        officer = PersonalizationEngine.get_tier_sla(profile.wealth_tier)["dedicated_officer"]
        tier_label = profile.wealth_tier.display_name

        if grade is SentimentGrade.CRITICAL_DISTRESS:
            return (
                f"Dear {profile.name}, please accept our immediate and sincere apologies. "
                f"Your {officer} is taking personal ownership of your case right now."
            )
        if grade is SentimentGrade.FRUSTRATED:
            return (
                f"Dear {profile.name}, I am sorry this has fallen short of the standard "
                f"you expect from us. Your {officer} will put it right straight away."
            )
        if grade is SentimentGrade.DELIGHTED:
            return (
                f"{profile.name}, thank you. It is a genuine privilege to look after you, "
                f"and our {tier_label} desk is delighted to hear this."
            )
        return (
            f"A very warm welcome, {profile.name}. Your {officer} is delighted to "
            "assist you today."
        )

    def audit_experience(
        self, profile: CustomerProfile, query: str, raw_sentiment: float
    ) -> ExperienceReview:
        grade, _score = PersonalizationEngine.classify_sentiment(query, raw_sentiment)
        award = determine_perk(profile.wealth_tier, grade)
        escalate = grade in _ESCALATION_GRADES

        closing = (
            "Your executive handover ticket is open and you will hear from us "
            "within your SLA."
            if escalate
            else "Your dedicated concierge team remains on standby, 24/7/365."
        )

        return ExperienceReview(
            sentiment_grade=grade,
            hospitality_rating=_HOSPITALITY_RATING[grade],
            empathetic_opening=self._compose_opening(profile, grade),
            loyalty_perk_awarded=award.description if award else None,
            executive_escalation_required=escalate,
            closing_courtesy=closing,
        )
