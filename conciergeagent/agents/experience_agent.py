from typing import Optional
from conciergeagent.core.models import (
    CustomerProfile, WealthTier, SentimentGrade, ExperienceReview
)
from conciergeagent.core.personalization_engine import PersonalizationEngine

class ExperienceAgent:
    """
    ExperienceAgent: Audits interaction hospitality, crafts empathetic phrasing,
    awards VIP loyalty perks, and triggers executive human handover when needed.
    """
    def __init__(self):
        self.name = "ExperienceAgent"
        self.version = "1.0.0"

    def audit_experience(self, profile: CustomerProfile, query: str, raw_sentiment: float) -> ExperienceReview:
        grade, score = PersonalizationEngine.classify_sentiment(query, raw_sentiment)
        
        # Opening greeting
        if grade in [SentimentGrade.CRITICAL_DISTRESS, SentimentGrade.FRUSTRATED]:
            opening = f"Dear {profile.name}, please accept our immediate and sincere apologies for any distress this has caused. We are taking personal ownership of your case right now."
            rating = 3 if grade == SentimentGrade.FRUSTRATED else 1
            escalate = True
            perk = "Priority Service Credit ($250) + Complimentary Luxury Lounge Pass"
        else:
            opening = f"A very warm welcome, {profile.name}. It is our absolute pleasure to assist our valued {profile.wealth_tier.value.replace('_', ' ')} client today."
            rating = 5
            escalate = False
            if profile.wealth_tier in [WealthTier.ULTRA_HNW, WealthTier.PRIVATE_CLIENT]:
                perk = "Exclusive 5,000 Bonus Loyalty Points + Private Jet & Dining Concierge Access"
            else:
                perk = "Complimentary 1,000 Loyalty Reward Points"

        closing = f"At your service 24/7/365. Your dedicated concierge team remains on standby."

        return ExperienceReview(
            sentiment_grade=grade,
            hospitality_rating=rating,
            empathetic_opening=opening,
            loyalty_perk_awarded=perk,
            executive_escalation_required=escalate,
            closing_courtesy=closing
        )
