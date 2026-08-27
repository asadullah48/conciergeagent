import pytest
from conciergeagent.agents.support_agent import SupportAgent
from conciergeagent.core.models import CustomerProfile, WealthTier

def test_support_dispute_resolution():
    agent = SupportAgent()
    prof = CustomerProfile(wealth_tier=WealthTier.PRIVATE_CLIENT)
    res = agent.resolve_inquiry(prof, "I have an unrecognized charge on my platinum card.")
    
    assert res.resolution_status == "DISPUTE_CREDITED"
    assert "$10,000.00" in res.immediate_action_taken
    assert "Zero-Liability" in res.policy_reference

def test_support_claim_resolution():
    agent = SupportAgent()
    prof = CustomerProfile(wealth_tier=WealthTier.PREMIER)
    res = agent.resolve_inquiry(prof, "I need to file an insurance damage claim.")
    
    assert res.resolution_status == "CLAIM_EXPEDITED"
    assert "VIP claim processing" in res.immediate_action_taken
