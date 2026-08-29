"""Shared fixtures for the ConciergeAgent test suite."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from conciergeagent.core.models import CustomerProfile, ServiceDomain, WealthTier
from conciergeagent.core.observability import METRICS
from conciergeagent.server import app

# Representative query text per sentiment grade, reused across the suite.
DELIGHTED_QUERY = "The private banking service has been absolutely wonderful."
POSITIVE_QUERY = "Thanks, that was helpful."
NEUTRAL_QUERY = "Please confirm my next statement date."
FRUSTRATED_QUERY = "My international wire transfer is delayed again."
CRITICAL_QUERY = "This is unacceptable, there is fraud on my account."


@pytest.fixture(autouse=True)
def _isolate_metrics():
    """Each test sees a clean metrics registry (the registry is process-global)."""
    METRICS.reset()
    yield
    METRICS.reset()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def profile_factory():
    def _make(tier: WealthTier = WealthTier.PRIVATE_CLIENT, **overrides) -> CustomerProfile:
        defaults = {
            "customer_id": f"CUST-{tier.value}",
            "name": "Test Client",
            "wealth_tier": tier,
            "primary_domain": ServiceDomain.BANKING,
        }
        defaults.update(overrides)
        return CustomerProfile(**defaults)

    return _make
