import pytest
from conciergeagent.orchestration.concierge_engine import ConciergeEngine
from conciergeagent.core.models import CustomerProfile, ServiceInteraction, WealthTier

def test_concierge_engine_advisory_flow():
    engine = ConciergeEngine()
    prof = CustomerProfile(name="Julian Ross", wealth_tier=WealthTier.PRIVATE_CLIENT)
    interaction = ServiceInteraction(
        customer_profile=prof,
        user_query="Please propose a tax-advantaged private asset allocation for my family trust.",
        intent_category="ADVISORY"
    )
    res = engine.process_interaction(interaction)
    
    assert res.customer_name == "Julian Ross"
    assert res.advisory_recommendation is not None
    assert res.csat_predicted_score >= 4.7
    assert res.experience_review.hospitality_rating == 5
