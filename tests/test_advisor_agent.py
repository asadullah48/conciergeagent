import pytest
from conciergeagent.agents.advisor_agent import AdvisorAgent
from conciergeagent.core.models import CustomerProfile, WealthTier

def test_advisor_private_client_allocation():
    agent = AdvisorAgent()
    prof = CustomerProfile(
        name="Eleanor Vance",
        wealth_tier=WealthTier.PRIVATE_CLIENT,
        assets_under_management_usd=5000000.0
    )
    rec = agent.generate_advisory(prof, "How should I rebalance my wealth portfolio?")
    
    assert "Global Private Equity & VC" in rec.portfolio_allocation
    assert rec.portfolio_allocation["Global Private Equity & VC"] == 0.30
    assert "tax-loss harvesting" in rec.yield_enhancement_strategy
    assert "pre-IPO" in rec.bespoke_opportunity

def test_advisor_retail_allocation():
    agent = AdvisorAgent()
    prof = CustomerProfile(name="John Doe", wealth_tier=WealthTier.RETAIL)
    rec = agent.generate_advisory(prof, "Help me invest my savings.")
    
    assert "Broad Market Index Funds" in rec.portfolio_allocation
    assert rec.portfolio_allocation["Broad Market Index Funds"] == 0.70
