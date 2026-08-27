from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time

class WealthTier(str, Enum):
    RETAIL = "RETAIL"
    PREMIER = "PREMIER"
    PRIVATE_CLIENT = "PRIVATE_CLIENT"
    ULTRA_HNW = "ULTRA_HNW"

class ServiceDomain(str, Enum):
    BANKING = "BANKING"
    INSURANCE = "INSURANCE"
    LUXURY_RETAIL = "LUXURY_RETAIL"

class SentimentGrade(str, Enum):
    DELIGHTED = "DELIGHTED"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    FRUSTRATED = "FRUSTRATED"
    CRITICAL_DISTRESS = "CRITICAL_DISTRESS"

class CustomerProfile(BaseModel):
    customer_id: str = "CUST-9082"
    name: str = "Alexander Wright"
    wealth_tier: WealthTier = WealthTier.PRIVATE_CLIENT
    primary_domain: ServiceDomain = ServiceDomain.BANKING
    assets_under_management_usd: float = 2500000.0
    lifetime_value_score: float = 94.5
    loyalty_points: int = 145000
    preferred_tone: str = "Concierge Formal & Proactive"
    relationship_tenure_years: int = 6

class ServiceInteraction(BaseModel):
    interaction_id: str = "INT-1002"
    customer_profile: CustomerProfile
    user_query: str
    intent_category: str = "ADVISORY" # ADVISORY | SUPPORT | LOYALTY
    raw_sentiment_score: float = 0.85 # -1.0 to 1.0

class AdvisoryRecommendation(BaseModel):
    portfolio_allocation: Dict[str, float]
    yield_enhancement_strategy: str
    tax_efficiency_notes: str
    bespoke_opportunity: str
    advisor_signature: str

class SupportResolution(BaseModel):
    ticket_id: str
    resolution_status: str # RESOLVED | CLAIM_EXPEDITED | DISPUTE_CREDITED | ESCALATED
    immediate_action_taken: str
    policy_reference: str
    sla_turnaround_time: str

class ExperienceReview(BaseModel):
    sentiment_grade: SentimentGrade
    hospitality_rating: int # 1 to 5 stars
    empathetic_opening: str
    loyalty_perk_awarded: Optional[str] = None
    executive_escalation_required: bool = False
    closing_courtesy: str

class ConciergeSessionResponse(BaseModel):
    session_id: str
    customer_id: str
    customer_name: str
    wealth_tier: WealthTier
    concierge_response_text: str
    advisory_recommendation: Optional[AdvisoryRecommendation] = None
    support_resolution: Optional[SupportResolution] = None
    experience_review: ExperienceReview
    csat_predicted_score: float
    execution_time_ms: float
