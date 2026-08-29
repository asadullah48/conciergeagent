"""SupportAgent routing, tier-scaled credits, and deterministic tickets."""
from __future__ import annotations

import pytest

from conciergeagent.agents.support_agent import SupportAgent
from conciergeagent.core.models import ResolutionStatus, WealthTier

DISPUTE_QUERY = "I have an unrecognized charge on my platinum card."
CLAIM_QUERY = "I need to file an insurance damage claim."
GENERAL_QUERY = "Please confirm my next statement date."


@pytest.fixture
def agent() -> SupportAgent:
    return SupportAgent()


@pytest.mark.parametrize(
    "query",
    [
        "I want to dispute this",
        "There is a strange charge",
        "This looks like fraud",
        "An unauthorized transaction appeared",
        "I see an unrecognized payment",
    ],
)
def test_dispute_cues_route_to_dispute_credit(agent, profile_factory, query):
    assert agent.resolve_inquiry(profile_factory(), query).resolution_status is (
        ResolutionStatus.DISPUTE_CREDITED
    )


@pytest.mark.parametrize(
    "query",
    [
        "I need to file a claim",
        "My insurance needs updating",
        "There is storm damage to the property",
        "I was in an accident",
    ],
)
def test_claim_cues_route_to_expedited_claim(agent, profile_factory, query):
    assert agent.resolve_inquiry(profile_factory(), query).resolution_status is (
        ResolutionStatus.CLAIM_EXPEDITED
    )


def test_unmatched_query_falls_back_to_resolved(agent, profile_factory):
    assert agent.resolve_inquiry(profile_factory(), GENERAL_QUERY).resolution_status is (
        ResolutionStatus.RESOLVED
    )


def test_dispute_takes_precedence_over_claim_when_both_cues_appear(agent, profile_factory):
    result = agent.resolve_inquiry(profile_factory(), "I dispute this insurance charge")
    assert result.resolution_status is ResolutionStatus.DISPUTE_CREDITED


@pytest.mark.parametrize(
    "tier,expected",
    [
        (WealthTier.ULTRA_HNW, "$50,000.00"),
        (WealthTier.PRIVATE_CLIENT, "$10,000.00"),
        (WealthTier.PREMIER, "$2,500.00"),
        (WealthTier.RETAIL, "$500.00"),
    ],
)
def test_dispute_credit_is_tier_scaled(agent, profile_factory, tier, expected):
    result = agent.resolve_inquiry(profile_factory(tier), DISPUTE_QUERY)
    assert expected in result.immediate_action_taken


@pytest.mark.parametrize(
    "tier,seconds",
    [
        (WealthTier.ULTRA_HNW, 30),
        (WealthTier.PRIVATE_CLIENT, 60),
        (WealthTier.PREMIER, 120),
        (WealthTier.RETAIL, 300),
    ],
)
def test_sla_is_tier_scaled(agent, profile_factory, tier, seconds):
    result = agent.resolve_inquiry(profile_factory(tier), GENERAL_QUERY)
    assert f"{seconds} seconds" in result.sla_turnaround_time


def test_dispute_cites_zero_liability_policy(agent, profile_factory):
    result = agent.resolve_inquiry(profile_factory(), DISPUTE_QUERY)
    assert "Zero-Liability" in result.policy_reference


def test_claim_cites_the_comprehensive_policy(agent, profile_factory):
    assert "Diamond" in agent.resolve_inquiry(profile_factory(), CLAIM_QUERY).policy_reference


@pytest.mark.parametrize("tier", list(WealthTier))
def test_every_tier_receives_a_ticket(agent, profile_factory, tier):
    assert agent.resolve_inquiry(profile_factory(tier), GENERAL_QUERY).ticket_id.startswith("TCK-")


def test_ticket_id_is_stable_for_identical_input(agent, profile_factory):
    profile = profile_factory()
    first = agent.resolve_inquiry(profile, DISPUTE_QUERY).ticket_id
    second = agent.resolve_inquiry(profile, DISPUTE_QUERY).ticket_id
    assert first == second


def test_ticket_id_differs_per_customer(agent, profile_factory):
    one = agent.resolve_inquiry(profile_factory(customer_id="CUST-A"), DISPUTE_QUERY).ticket_id
    two = agent.resolve_inquiry(profile_factory(customer_id="CUST-B"), DISPUTE_QUERY).ticket_id
    assert one != two


def test_ticket_id_differs_per_query(agent, profile_factory):
    profile = profile_factory()
    assert (
        agent.resolve_inquiry(profile, DISPUTE_QUERY).ticket_id
        != agent.resolve_inquiry(profile, CLAIM_QUERY).ticket_id
    )


def test_routing_is_case_insensitive(agent, profile_factory):
    assert agent.resolve_inquiry(profile_factory(), "THERE IS FRAUD HERE").resolution_status is (
        ResolutionStatus.DISPUTE_CREDITED
    )


def test_agent_reports_its_identity(agent):
    assert agent.name == "SupportAgent"
    assert agent.version
