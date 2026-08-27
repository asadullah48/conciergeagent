from typing import Dict, Any
from conciergeagent.core.models import (
    CustomerProfile, WealthTier, SupportResolution
)
from conciergeagent.core.personalization_engine import PersonalizationEngine

class SupportAgent:
    """
    SupportAgent: Resolves customer inquiries, dispute claims, and policy changes
    with white-glove turnaround times.
    """
    def __init__(self):
        self.name = "SupportAgent"
        self.version = "1.0.0"

    def resolve_inquiry(self, profile: CustomerProfile, query: str) -> SupportResolution:
        tier_sla = PersonalizationEngine.get_tier_sla(profile.wealth_tier)
        query_lower = query.lower()

        if "dispute" in query_lower or "charge" in query_lower or "fraud" in query_lower:
            action = f"Instant provisional credit granted up to ${tier_sla['max_dispute_auto_credit']:,.2f}. Card frozen and digital token reissued to Apple/Google Wallet immediately."
            status = "DISPUTE_CREDITED"
            policy = "Reg E / Zero-Liability VIP Protection Guarantee"
        elif "claim" in query_lower or "insurance" in query_lower or "damage" in query_lower:
            action = "Fast-track VIP claim processing initiated with direct adjuster dispatch and zero out-of-pocket deductible waiver."
            status = "CLAIM_EXPEDITED"
            policy = "Concierge Diamond Comprehensive Policy Sec. 4"
        else:
            action = "Inquiry verified against ledger and resolved with customized priority routing."
            status = "RESOLVED"
            policy = "Five-Star Customer Charter"

        return SupportResolution(
            ticket_id=f"TCK-{abs(hash(query + profile.customer_id)) % 100000}",
            resolution_status=status,
            immediate_action_taken=action,
            policy_reference=policy,
            sla_turnaround_time=f"{tier_sla['sla_seconds']} seconds (Guaranteed)"
        )
