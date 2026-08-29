"""AdvisorAgent produces a valid, tier-appropriate allocation for every tier."""
from __future__ import annotations

import pytest

from conciergeagent.agents.advisor_agent import AdvisorAgent
from conciergeagent.core.models import WealthTier

QUERY = "How should I rebalance my portfolio?"


@pytest.fixture
def agent() -> AdvisorAgent:
    return AdvisorAgent()


@pytest.mark.parametrize("tier", list(WealthTier))
def test_allocation_sums_to_one_for_every_tier(agent, profile_factory, tier):
    """The model validator enforces this; the test proves no branch violates it."""
    rec = agent.generate_advisory(profile_factory(tier), QUERY)
    assert sum(rec.portfolio_allocation.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("tier", list(WealthTier))
def test_every_tier_receives_a_complete_recommendation(agent, profile_factory, tier):
    rec = agent.generate_advisory(profile_factory(tier), QUERY)
    assert rec.portfolio_allocation
    assert rec.yield_enhancement_strategy.strip()
    assert rec.tax_efficiency_notes.strip()
    assert rec.bespoke_opportunity.strip()
    assert rec.advisor_signature.strip()


@pytest.mark.parametrize("tier", [WealthTier.PRIVATE_CLIENT, WealthTier.ULTRA_HNW])
def test_upper_tiers_receive_private_market_access(agent, profile_factory, tier):
    rec = agent.generate_advisory(profile_factory(tier), QUERY)
    assert "Global Private Equity & VC" in rec.portfolio_allocation
    assert rec.portfolio_allocation["Global Private Equity & VC"] == 0.30
    assert "pre-IPO" in rec.bespoke_opportunity


@pytest.mark.parametrize("tier", [WealthTier.RETAIL, WealthTier.PREMIER])
def test_lower_tiers_receive_no_private_market_access(agent, profile_factory, tier):
    rec = agent.generate_advisory(profile_factory(tier), QUERY)
    assert "Global Private Equity & VC" not in rec.portfolio_allocation


def test_premier_receives_a_balanced_core_allocation(agent, profile_factory):
    rec = agent.generate_advisory(profile_factory(WealthTier.PREMIER), QUERY)
    assert rec.portfolio_allocation["Diversified Core Equities (ETF)"] == 0.50
    assert "tax-loss harvesting" in rec.tax_efficiency_notes


def test_retail_receives_an_index_led_allocation(agent, profile_factory):
    rec = agent.generate_advisory(profile_factory(WealthTier.RETAIL), QUERY)
    assert rec.portfolio_allocation["Broad Market Index Funds"] == 0.70
    assert "Roth IRA" in rec.tax_efficiency_notes


@pytest.mark.parametrize("tier", list(WealthTier))
def test_no_allocation_weight_is_negative(agent, profile_factory, tier):
    rec = agent.generate_advisory(profile_factory(tier), QUERY)
    assert all(weight >= 0 for weight in rec.portfolio_allocation.values())


@pytest.mark.parametrize("tier", list(WealthTier))
def test_every_tier_holds_a_liquidity_reserve(agent, profile_factory, tier):
    """No tier should be fully illiquid -- some cash-like sleeve must exist."""
    rec = agent.generate_advisory(profile_factory(tier), QUERY)
    liquid_terms = ("liquidity", "cash", "savings", "reserve", "buffer")
    assert any(term in name.lower() for name in rec.portfolio_allocation for term in liquid_terms)


def test_advisory_is_deterministic_for_identical_input(agent, profile_factory):
    profile = profile_factory(WealthTier.ULTRA_HNW)
    assert agent.generate_advisory(profile, QUERY) == agent.generate_advisory(profile, QUERY)


def test_agent_reports_its_identity(agent):
    assert agent.name == "AdvisorAgent"
    assert agent.version
