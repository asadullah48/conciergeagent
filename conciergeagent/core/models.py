"""Domain models for the ConciergeAgent platform.

Constraints that were previously expressed as trailing comments are enforced
here as Pydantic field constraints, so invalid payloads are rejected at the API
boundary (HTTP 422) instead of flowing into the agents. FastAPI publishes every
constraint and description into the OpenAPI schema at /docs.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator

ALLOCATION_TOLERANCE = 0.001


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


class IntentCategory(str, Enum):
    """Routing target for an interaction.

    Previously a free-form string: any unrecognised value fell through to the
    SupportAgent silently. Now an unknown intent is rejected at the boundary.
    """

    ADVISORY = "ADVISORY"
    SUPPORT = "SUPPORT"
    LOYALTY = "LOYALTY"


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    CLAIM_EXPEDITED = "CLAIM_EXPEDITED"
    DISPUTE_CREDITED = "DISPUTE_CREDITED"
    ESCALATED = "ESCALATED"


class CustomerProfile(BaseModel):
    customer_id: str = Field(default="CUST-9082", min_length=1, max_length=64)
    name: str = Field(default="Alexander Wright", min_length=1, max_length=120)
    wealth_tier: WealthTier = WealthTier.PRIVATE_CLIENT
    primary_domain: ServiceDomain = ServiceDomain.BANKING
    assets_under_management_usd: float = Field(default=2_500_000.0, ge=0.0)
    lifetime_value_score: float = Field(default=94.5, ge=0.0, le=100.0)
    loyalty_points: int = Field(default=145_000, ge=0)
    preferred_tone: str = Field(default="Concierge Formal & Proactive", max_length=120)
    relationship_tenure_years: int = Field(default=6, ge=0, le=120)


class ServiceInteraction(BaseModel):
    interaction_id: str = Field(default="INT-1002", min_length=1, max_length=64)
    customer_profile: CustomerProfile
    user_query: str = Field(
        ..., min_length=1, max_length=4000, description="Verbatim customer message."
    )
    intent_category: IntentCategory = IntentCategory.ADVISORY
    raw_sentiment_score: float = Field(
        default=0.85,
        ge=-1.0,
        le=1.0,
        description="Upstream sentiment signal; -1.0 (hostile) to 1.0 (delighted).",
    )


class AdvisoryRecommendation(BaseModel):
    portfolio_allocation: dict[str, float] = Field(
        ..., min_length=1, description="Asset class to weight; weights must sum to 1.0."
    )
    yield_enhancement_strategy: str
    tax_efficiency_notes: str
    bespoke_opportunity: str
    advisor_signature: str

    @model_validator(mode="after")
    def _allocation_must_total_one(self) -> AdvisoryRecommendation:
        """A portfolio that does not allocate exactly 100% is not a portfolio."""
        total = sum(self.portfolio_allocation.values())
        if abs(total - 1.0) > ALLOCATION_TOLERANCE:
            raise ValueError(f"portfolio_allocation must sum to 1.0, got {total:.4f}")
        if any(weight < 0 for weight in self.portfolio_allocation.values()):
            raise ValueError("portfolio_allocation weights must be non-negative")
        return self


class SupportResolution(BaseModel):
    ticket_id: str
    resolution_status: ResolutionStatus
    immediate_action_taken: str
    policy_reference: str
    sla_turnaround_time: str


class ExperienceReview(BaseModel):
    sentiment_grade: SentimentGrade
    hospitality_rating: int = Field(..., ge=1, le=5)
    empathetic_opening: str
    loyalty_perk_awarded: str | None = None
    executive_escalation_required: bool = False
    closing_courtesy: str


class ConciergeSessionResponse(BaseModel):
    session_id: str
    customer_id: str
    customer_name: str
    wealth_tier: WealthTier
    intent_routed: IntentCategory = Field(
        ..., description="Agent lane that actually handled the interaction."
    )
    concierge_response_text: str
    advisory_recommendation: AdvisoryRecommendation | None = None
    support_resolution: SupportResolution | None = None
    experience_review: ExperienceReview
    csat_predicted_score: float = Field(..., ge=0.0, le=5.0)
    execution_time_ms: float = Field(..., ge=0.0)
