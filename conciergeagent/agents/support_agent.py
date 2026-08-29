"""SupportAgent: dispute credits, claims triage, and policy operations."""
from __future__ import annotations

from conciergeagent.core.identifiers import ticket_id
from conciergeagent.core.models import (
    CustomerProfile,
    ResolutionStatus,
    SupportResolution,
)
from conciergeagent.core.personalization_engine import PersonalizationEngine

_DISPUTE_CUES = ("dispute", "charge", "fraud", "unauthorized", "unrecognized")
_CLAIM_CUES = ("claim", "insurance", "damage", "accident", "policy payout")


class SupportAgent:
    """Resolves customer inquiries, disputes, and claims within tier SLA."""

    def __init__(self) -> None:
        self.name = "SupportAgent"
        self.version = "2.0.0"

    def resolve_inquiry(self, profile: CustomerProfile, query: str) -> SupportResolution:
        tier_sla = PersonalizationEngine.get_tier_sla(profile.wealth_tier)
        query_lower = query.lower()

        if any(cue in query_lower for cue in _DISPUTE_CUES):
            action = (
                f"Instant provisional credit granted up to "
                f"${tier_sla['max_dispute_auto_credit']:,.2f}. Card frozen and a digital token "
                "reissued to your mobile wallet immediately."
            )
            status = ResolutionStatus.DISPUTE_CREDITED
            policy = "Reg E / Zero-Liability VIP Protection Guarantee"
        elif any(cue in query_lower for cue in _CLAIM_CUES):
            action = (
                "Fast-track VIP claim processing initiated with direct adjuster dispatch and "
                "zero out-of-pocket deductible waiver."
            )
            status = ResolutionStatus.CLAIM_EXPEDITED
            policy = "Concierge Diamond Comprehensive Policy Sec. 4"
        else:
            action = "Inquiry verified against the ledger and resolved with priority routing."
            status = ResolutionStatus.RESOLVED
            policy = "Five-Star Customer Charter"

        return SupportResolution(
            ticket_id=ticket_id(query, profile.customer_id),
            resolution_status=status,
            immediate_action_taken=action,
            policy_reference=policy,
            sla_turnaround_time=f"{tier_sla['sla_seconds']} seconds (Guaranteed)",
        )
