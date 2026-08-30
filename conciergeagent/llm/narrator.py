"""Render deterministic decisions as natural language.

The model is a *renderer*, never a decision maker. Every material value --
the dispute credit, the allocation weights, the SLA, the escalation flag --
is computed by the rule engine before narration begins. The model is handed
that finished text and asked only to restate it.

That boundary is then enforced rather than trusted: the facts extracted from
the deterministic text must all survive into the narrated text, or the
narration is discarded. A model that quietly turns "$50,000.00" into
"$500,000.00" cannot reach a customer.
"""
from __future__ import annotations

import logging
import re
from typing import NamedTuple

from conciergeagent.core.models import NarrationMode
from conciergeagent.core.observability import METRICS
from conciergeagent.llm.client import LLMClient, LLMUnavailable

logger = logging.getLogger(__name__)

# Values that must survive narration untouched.
_PROTECTED_PATTERNS = (
    re.compile(r"\$[\d,]+(?:\.\d{2})?"),          # currency amounts
    re.compile(r"\bTCK-[0-9A-F]{8}\b"),           # support ticket identifiers
    re.compile(r"\b\d+(?:\.\d+)?%"),              # allocation and yield percentages
    re.compile(r"\b\d+\s+seconds\b"),             # SLA guarantees
)

SUPPORTED_LANGUAGES = {"en": "English", "ar": "Arabic"}

# The house voice. This is brand copy as much as it is a prompt.
NARRATION_SYSTEM_PROMPT = """You are the writing desk for a private banking concierge service.

You will be given a complete, already-approved reply to a client. Your only
job is to restate it in warm, precise, understated prose.

Rules you must not break:
- Never change, drop, round, or invent a number, currency amount, percentage,
  ticket reference, or time guarantee. Reproduce every one of them exactly.
- Never add a commitment, product, benefit, or apology that is not already in
  the text you were given.
- Never ask the client a question or request further information.
- Keep it under 180 words. No bullet points, no headings.
- Understated confidence, not salesmanship. No exclamation marks, no
  superlatives, no emoji."""


class Narration(NamedTuple):
    text: str
    mode: NarrationMode


def extract_protected_facts(text: str) -> set[str]:
    """Collect every value the model is forbidden from altering."""
    facts: set[str] = set()
    for pattern in _PROTECTED_PATTERNS:
        facts.update(match.group(0) for match in pattern.finditer(text))
    return facts


def missing_facts(deterministic: str, narrated: str) -> set[str]:
    """Return protected facts that did not survive into the narrated text."""
    return {fact for fact in extract_protected_facts(deterministic) if fact not in narrated}


def build_user_prompt(deterministic_text: str, tier_label: str, language: str = "en") -> str:
    """Frame the approved reply for restatement."""
    target = SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES["en"])
    return (
        f"Client tier: {tier_label}\n"
        f"Write the reply in {target}.\n\n"
        "Approved reply to restate:\n"
        f"{deterministic_text}"
    )


def narrate(
    deterministic_text: str,
    tier_label: str,
    client: LLMClient | None,
    *,
    language: str = "en",
) -> Narration:
    """Return the customer-facing text and how it was produced.

    Falls back to the deterministic text on any failure, and always reports
    which path was taken. A silent fallback would hide a broken model
    integration behind output that still looks perfectly correct.
    """
    if client is None:
        return Narration(deterministic_text, NarrationMode.DETERMINISTIC)

    try:
        candidate = client.complete(
            NARRATION_SYSTEM_PROMPT,
            build_user_prompt(deterministic_text, tier_label, language),
        )
    except LLMUnavailable as exc:
        logger.warning(
            "narration unavailable, serving deterministic reply", extra={"reason": str(exc)}
        )
        METRICS.increment("concierge_narration_total", {"mode": "fallback_unavailable"})
        return Narration(deterministic_text, NarrationMode.LLM_FALLBACK_UNAVAILABLE)

    dropped = missing_facts(deterministic_text, candidate)
    if dropped:
        logger.warning(
            "narration dropped protected facts, serving deterministic reply",
            extra={"dropped_fact_count": len(dropped)},
        )
        METRICS.increment("concierge_narration_total", {"mode": "fallback_unfaithful"})
        return Narration(deterministic_text, NarrationMode.LLM_FALLBACK_UNFAITHFUL)

    METRICS.increment("concierge_narration_total", {"mode": "narrated"})
    return Narration(candidate, NarrationMode.LLM_NARRATED)
