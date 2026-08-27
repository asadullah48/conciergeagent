import time
from typing import Optional
from conciergeagent.core.models import (
    CustomerProfile, ServiceInteraction, ConciergeSessionResponse, WealthTier
)
from conciergeagent.agents.advisor_agent import AdvisorAgent
from conciergeagent.agents.support_agent import SupportAgent
from conciergeagent.agents.experience_agent import ExperienceAgent

class ConciergeEngine:
    """
    ConciergeEngine: Orchestrates AdvisorAgent, SupportAgent, and ExperienceAgent
    to produce bespoke, 5-star customer experiences.
    """
    def __init__(self):
        self.advisor_agent = AdvisorAgent()
        self.support_agent = SupportAgent()
        self.experience_agent = ExperienceAgent()

    def process_interaction(self, interaction: ServiceInteraction) -> ConciergeSessionResponse:
        t0 = time.time()
        prof = interaction.customer_profile
        query = interaction.user_query
        intent = interaction.intent_category.upper()

        # Step 1: Experience & Sentiment Audit
        exp_review = self.experience_agent.audit_experience(prof, query, interaction.raw_sentiment_score)

        advisory_rec = None
        support_res = None
        body_parts = [exp_review.empathetic_opening]

        # Step 2: Route by Intent
        if intent == "ADVISORY" or any(w in query.lower() for w in ["invest", "portfolio", "yield", "wealth", "tax", "allocation"]):
            advisory_rec = self.advisor_agent.generate_advisory(prof, query)
            body_parts.append(f"\n\n📊 **Bespoke Wealth Advisory Strategy:**\n{advisory_rec.yield_enhancement_strategy}\n\n• **Tax Optimizations:** {advisory_rec.tax_efficiency_notes}\n• **Private Allocation:** {advisory_rec.bespoke_opportunity}")
        else:
            support_res = self.support_agent.resolve_inquiry(prof, query)
            body_parts.append(f"\n\n🛡️ **Concierge Resolution Action [{support_res.ticket_id}]:**\n{support_res.immediate_action_taken}\n\n• **Policy Framework:** {support_res.policy_reference}\n• **Guaranteed SLA:** {support_res.sla_turnaround_time}")

        if exp_review.loyalty_perk_awarded:
            body_parts.append(f"\n\n🎁 **VIP Concierge Privilege Unlocked:** {exp_review.loyalty_perk_awarded}")

        body_parts.append(f"\n\n{exp_review.closing_courtesy}")

        full_text = "".join(body_parts)
        exec_ms = round((time.time() - t0) * 1000.0, 2)
        csat = 4.95 if not exp_review.executive_escalation_required else 4.70

        return ConciergeSessionResponse(
            session_id=f"SES-{abs(hash(query)) % 1000000}",
            customer_id=prof.customer_id,
            customer_name=prof.name,
            wealth_tier=prof.wealth_tier,
            concierge_response_text=full_text,
            advisory_recommendation=advisory_rec,
            support_resolution=support_res,
            experience_review=exp_review,
            csat_predicted_score=csat,
            execution_time_ms=exec_ms
        )
