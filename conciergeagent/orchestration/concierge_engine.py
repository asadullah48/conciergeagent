"""ConciergeEngine: orchestrates the three specialist agents into one response."""
from __future__ import annotations

import logging
import time

from conciergeagent.agents.advisor_agent import AdvisorAgent
from conciergeagent.agents.experience_agent import ExperienceAgent
from conciergeagent.agents.support_agent import SupportAgent
from conciergeagent.core.identifiers import session_id
from conciergeagent.core.models import (
    ConciergeSessionResponse,
    ExperienceReview,
    IntentCategory,
    ServiceInteraction,
)
from conciergeagent.core.observability import METRICS

logger = logging.getLogger(__name__)

# Predicted CSAT by hospitality rating, before escalation adjustment.
_CSAT_BY_RATING = {5: 4.95, 4: 4.70, 3: 4.20, 2: 3.60, 1: 3.10}
_ESCALATION_CSAT_PENALTY = 0.25


class ConciergeEngine:
    """Runs the experience audit, routes to a specialist lane, and assembles
    the customer-facing response.

    Routing is driven by ``ServiceInteraction.intent_category`` alone. Earlier
    revisions also sniffed the query text for keywords, which meant a caller's
    explicitly declared intent could be silently overridden -- surprising for
    API consumers and effectively untestable.
    """

    def __init__(self) -> None:
        self.advisor_agent = AdvisorAgent()
        self.support_agent = SupportAgent()
        self.experience_agent = ExperienceAgent()

    @staticmethod
    def _predict_csat(review: ExperienceReview) -> float:
        base = _CSAT_BY_RATING.get(review.hospitality_rating, 4.0)
        if review.executive_escalation_required:
            base -= _ESCALATION_CSAT_PENALTY
        return round(max(0.0, min(5.0, base)), 2)

    def process_interaction(self, interaction: ServiceInteraction) -> ConciergeSessionResponse:
        started = time.perf_counter()
        profile = interaction.customer_profile
        query = interaction.user_query
        intent = interaction.intent_category

        review = self.experience_agent.audit_experience(
            profile, query, interaction.raw_sentiment_score
        )

        advisory = None
        resolution = None
        sections = [review.empathetic_opening]

        if intent is IntentCategory.ADVISORY:
            advisory = self.advisor_agent.generate_advisory(profile, query)
            sections.append(
                f"\n\n📊 **Bespoke Wealth Advisory Strategy:**\n"
                f"{advisory.yield_enhancement_strategy}\n\n"
                f"• **Tax Optimisations:** {advisory.tax_efficiency_notes}\n"
                f"• **Private Allocation:** {advisory.bespoke_opportunity}"
            )
        elif intent is IntentCategory.SUPPORT:
            resolution = self.support_agent.resolve_inquiry(profile, query)
            sections.append(
                f"\n\n🛡️ **Concierge Resolution Action [{resolution.ticket_id}]:**\n"
                f"{resolution.immediate_action_taken}\n\n"
                f"• **Policy Framework:** {resolution.policy_reference}\n"
                f"• **Guaranteed SLA:** {resolution.sla_turnaround_time}"
            )
        else:  # IntentCategory.LOYALTY -- handled entirely by the ExperienceAgent.
            sections.append(
                "\n\n🎖️ **Loyalty & Recognition Review:** Your relationship "
                "standing has been reviewed by your dedicated "
                f"{profile.wealth_tier.display_name} desk against a balance of "
                f"{profile.loyalty_points:,} points."
            )

        if review.loyalty_perk_awarded:
            sections.append(
                f"\n\n🎁 **Concierge Privilege Applied:** {review.loyalty_perk_awarded}"
            )
        sections.append(f"\n\n{review.closing_courtesy}")

        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
        METRICS.increment(
            "concierge_interactions_total",
            {"tier": profile.wealth_tier.value, "intent": intent.value},
        )
        METRICS.increment(
            "concierge_sentiment_total", {"grade": review.sentiment_grade.value}
        )
        if review.executive_escalation_required:
            METRICS.increment("concierge_escalations_total", {"tier": profile.wealth_tier.value})
        METRICS.observe_latency_ms(elapsed_ms)

        logger.info(
            "interaction processed",
            extra={
                "customer_id": profile.customer_id,
                "wealth_tier": profile.wealth_tier.value,
                "intent": intent.value,
                "sentiment_grade": review.sentiment_grade.value,
                "escalated": review.executive_escalation_required,
                "duration_ms": elapsed_ms,
            },
        )

        return ConciergeSessionResponse(
            session_id=session_id(query, profile.customer_id, intent.value),
            customer_id=profile.customer_id,
            customer_name=profile.name,
            wealth_tier=profile.wealth_tier,
            intent_routed=intent,
            concierge_response_text="".join(sections),
            advisory_recommendation=advisory,
            support_resolution=resolution,
            experience_review=review,
            csat_predicted_score=self._predict_csat(review),
            execution_time_ms=elapsed_ms,
        )
