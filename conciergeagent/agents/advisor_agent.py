"""AdvisorAgent: tier-appropriate portfolio construction and tax framing."""
from __future__ import annotations

from conciergeagent.core.models import (
    AdvisoryRecommendation,
    CustomerProfile,
    WealthTier,
)

PRIVATE_MARKET_TIERS = frozenset({WealthTier.ULTRA_HNW, WealthTier.PRIVATE_CLIENT})

_PRIVATE_MARKET_ALLOCATION = {
    "Global Private Equity & VC": 0.30,
    "Hedging & Real Assets": 0.20,
    "Tax-Exempt Fixed Income": 0.25,
    "Global Equities": 0.20,
    "Liquidity / Yield Reserve": 0.05,
}
_PREMIER_ALLOCATION = {
    "Diversified Core Equities (ETF)": 0.50,
    "Investment Grade Corporate Debt": 0.30,
    "High-Yield Treasury Notes": 0.15,
    "Cash Buffer": 0.05,
}
_RETAIL_ALLOCATION = {
    "Broad Market Index Funds": 0.70,
    "Short-Term Government Bonds": 0.25,
    "Emergency Savings": 0.05,
}


class AdvisorAgent:
    """Formulates personalized investment strategy for the client wealth tier."""

    def __init__(self) -> None:
        self.name = "AdvisorAgent"
        self.version = "2.0.0"

    def generate_advisory(
        self, profile: CustomerProfile, query: str
    ) -> AdvisoryRecommendation:
        if profile.wealth_tier in PRIVATE_MARKET_TIERS:
            allocation = _PRIVATE_MARKET_ALLOCATION
            strategy = (
                "Direct indexing paired with quantitative tax-loss harvesting and a "
                "private credit liquidity pool yielding 8.2% APY."
            )
            tax_notes = (
                "Structured via a Delaware Statutory Trust / offshore family office "
                "vehicle with 0% state capital gains friction."
            )
            opportunity = (
                "Exclusive pre-IPO secondary co-investment allocation "
                "($500k minimum ticket)."
            )
        elif profile.wealth_tier is WealthTier.PREMIER:
            allocation = _PREMIER_ALLOCATION
            strategy = (
                "Multi-asset automated rebalancing with a 5.4% blended portfolio yield."
            )
            tax_notes = (
                "Annual tax-loss harvesting applied automatically across "
                "non-registered accounts."
            )
            opportunity = (
                "Premier preferred deposit interest rate bonus "
                "(+0.65% over benchmark)."
            )
        else:
            allocation = _RETAIL_ALLOCATION
            strategy = (
                "Dollar-cost averaging into low-cost diversified index funds "
                "yielding 4.8% APY."
            )
            tax_notes = "Maximized Roth IRA / 401(k) retirement contributions."
            opportunity = "Round-up micro-investing and zero-commission trading."

        return AdvisoryRecommendation(
            portfolio_allocation=dict(allocation),
            yield_enhancement_strategy=strategy,
            tax_efficiency_notes=tax_notes,
            bespoke_opportunity=opportunity,
            advisor_signature="Certified Private Wealth Lead - ConciergeAgent Desk",
        )
