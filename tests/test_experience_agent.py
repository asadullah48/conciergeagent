import pytest
from conciergeagent.agents.experience_agent import ExperienceAgent
from conciergeagent.core.models import CustomerProfile, WealthTier, SentimentGrade

def test_experience_vip_delight():
    agent = ExperienceAgent()
    prof = CustomerProfile(name="Lord Sterling", wealth_tier=WealthTier.ULTRA_HNW)
    review = agent.audit_experience(prof, "I love the exclusive private banking services!", 0.9)
    
    assert review.sentiment_grade == SentimentGrade.DELIGHTED
    assert review.hospitality_rating == 5
    assert review.executive_escalation_required is False
    assert "Private Jet" in review.loyalty_perk_awarded

def test_experience_distress_escalation():
    agent = ExperienceAgent()
    prof = CustomerProfile(name="Sir Arthur", wealth_tier=WealthTier.PREMIER)
    review = agent.audit_experience(prof, "Unacceptable error delayed my international wire transfer!", -0.8)
    
    assert review.sentiment_grade == SentimentGrade.CRITICAL_DISTRESS
    assert review.executive_escalation_required is True
    assert "Priority Service Credit" in review.loyalty_perk_awarded
