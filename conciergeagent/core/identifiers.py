"""Stable, reproducible identifier generation.

The engine previously derived session and ticket IDs from the builtin ``hash()``.
CPython seeds string hashing randomly per process (PYTHONHASHSEED) as a defence
against hash-flooding, so identical inputs produced different IDs on every
restart -- making tickets impossible to reproduce, replay, or assert on.

BLAKE2b gives a fast, stable, collision-resistant digest instead.
"""
from __future__ import annotations

import hashlib

_DIGEST_BYTES = 5  # 10 hex chars -- ample spread for demo-scale volumes


def stable_digest(*parts: str, length: int = 8) -> str:
    """Return an uppercase hex digest that is identical for identical inputs.

    Args:
        parts: Components hashed together. ``None`` values are rejected by the
            join, so callers must pass strings explicitly.
        length: Number of hex characters to return (1-10).
    """
    if not 1 <= length <= _DIGEST_BYTES * 2:
        raise ValueError(f"length must be between 1 and {_DIGEST_BYTES * 2}")
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.blake2b(payload, digest_size=_DIGEST_BYTES).hexdigest()[:length].upper()


def session_id(query: str, customer_id: str, intent: str = "") -> str:
    """Deterministic session identifier for one customer interaction.

    Intent participates in the digest: the same question asked of the advisory
    lane and the support lane are distinct interactions and must not collide.
    """
    return f"SES-{stable_digest(customer_id, intent, query, length=8)}"


def ticket_id(query: str, customer_id: str) -> str:
    """Deterministic support ticket identifier."""
    return f"TCK-{stable_digest('ticket', customer_id, query, length=8)}"
