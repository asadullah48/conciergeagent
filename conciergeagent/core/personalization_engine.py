from typing import Dict, Any, Tuple
from conciergeagent.core.models import (
    CustomerProfile, WealthTier, SentimentGrade
)

class PersonalizationEngine:
    """
    Calculates customer sentiment affinity, dynamically generates bespoke persona framing,
    and assigns VIP concierge privileges.
    """
    @staticmethod
    def classify_sentiment(text: str, raw_score: float = 0.5) -> Tuple[SentimentGrade, float]:
        text_lower = text.lower()
        
        # Distress cues
        if any(w in text_lower for w in ["unacceptable", "terrible", "fraud", "stolen", "lawyer", "angry", "furious"]):
            return SentimentGrade.CRITICAL_DISTRESS, -0.90
        elif any(w in text_lower for w in ["disappointed", "delayed", "wrong", "issue", "error", "confused", "problem"]):
            return SentimentGrade.FRUSTRATED, -0.40
        elif any(w in text_lower for w in ["excellent", "wonderful", "love", "amazing", "delighted", "superb", "brilliant"]):
            return SentimentGrade.DELIGHTED, 0.95
        elif any(w in text_lower for w in ["good", "thanks", "helpful", "great", "appreciate"]):
            return SentimentGrade.POSITIVE, 0.70
        else:
            return SentimentGrade.NEUTRAL, max(-0.2, min(0.3, raw_score))

    @staticmethod
    def get_tier_sla(tier: WealthTier) -> Dict[str, Any]:
        if tier == WealthTier.ULTRA_HNW:
            return {
                "sla_seconds": 30,
                "dedicated_officer": "Executive Family Office Lead",
                "max_dispute_auto_credit": 50000.0,
                "concierge_gift_eligible": True
            }
        elif tier == WealthTier.PRIVATE_CLIENT:
            return {
                "sla_seconds": 60,
                "dedicated_officer": "Senior Private Banker",
                "max_dispute_auto_credit": 10000.0,
                "concierge_gift_eligible": True
            }
        elif tier == WealthTier.PREMIER:
            return {
                "sla_seconds": 120,
                "dedicated_officer": "Premier Relationship Manager",
                "max_dispute_auto_credit": 2500.0,
                "concierge_gift_eligible": False
            }
        else:
            return {
                "sla_seconds": 300,
                "dedicated_officer": "Digital Concierge Assistant",
                "max_dispute_auto_credit": 500.0,
                "concierge_gift_eligible": False
            }
