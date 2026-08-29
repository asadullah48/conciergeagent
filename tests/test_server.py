"""HTTP surface: probes, metrics, validation, CORS, and the interact endpoint."""
from __future__ import annotations

import copy

import pytest

from conciergeagent import __version__
from conciergeagent.core.config import DEFAULT_ALLOWED_ORIGINS

BASE_PAYLOAD = {
    "interaction_id": "INT-API-001",
    "customer_profile": {
        "customer_id": "CUST-API-1",
        "name": "Lady Victoria",
        "wealth_tier": "ULTRA_HNW",
        "primary_domain": "BANKING",
        "assets_under_management_usd": 15_000_000.0,
        "lifetime_value_score": 98.0,
        "loyalty_points": 500_000,
        "preferred_tone": "Formal",
        "relationship_tenure_years": 10,
    },
    "user_query": "I would like to explore private equity co-investments.",
    "intent_category": "ADVISORY",
    "raw_sentiment_score": 0.95,
}


def payload(**overrides):
    body = copy.deepcopy(BASE_PAYLOAD)
    body.update(overrides)
    return body


class TestProbes:
    def test_healthz_reports_healthy(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_healthz_reports_the_package_version(self, client):
        assert client.get("/healthz").json()["version"] == __version__

    def test_readyz_reports_three_active_agents(self, client):
        body = client.get("/readyz").json()
        assert body["status"] == "ready"
        assert body["concierge_agents_active"] == 3

    def test_readyz_names_each_agent(self, client):
        agents = client.get("/readyz").json()["agents"]
        assert set(agents) == {"AdvisorAgent", "SupportAgent", "ExperienceAgent"}

    def test_root_serves_the_dashboard(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "ConciergeAgent" in response.text

    def test_openapi_schema_is_served(self, client):
        schema = client.get("/openapi.json").json()
        assert schema["info"]["version"] == __version__
        assert "/api/v1/concierge/interact" in schema["paths"]

    def test_openapi_declares_the_licence(self, client):
        assert "Apache" in client.get("/openapi.json").json()["info"]["license"]["name"]


class TestMetricsEndpoint:
    def test_metrics_are_served_as_prometheus_text(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")

    def test_metrics_include_the_latency_histogram(self, client):
        assert "concierge_interaction_latency_ms_count" in client.get("/metrics").text

    def test_interactions_are_counted_in_metrics(self, client):
        client.post("/api/v1/concierge/interact", json=payload())
        body = client.get("/metrics").text
        assert "concierge_interactions_total" in body
        assert 'tier="ULTRA_HNW"' in body


class TestInteractEndpoint:
    def test_advisory_request_succeeds(self, client):
        response = client.post("/api/v1/concierge/interact", json=payload())
        assert response.status_code == 200
        body = response.json()
        assert body["customer_name"] == "Lady Victoria"
        assert body["advisory_recommendation"] is not None
        allocation = body["advisory_recommendation"]["portfolio_allocation"]
        assert "Global Private Equity & VC" in allocation

    def test_support_request_returns_a_resolution(self, client):
        body = client.post(
            "/api/v1/concierge/interact",
            json=payload(intent_category="SUPPORT", user_query="There is a disputed charge."),
        ).json()
        assert body["support_resolution"]["resolution_status"] == "DISPUTE_CREDITED"
        assert body["advisory_recommendation"] is None

    def test_loyalty_request_returns_neither_specialist_payload(self, client):
        body = client.post(
            "/api/v1/concierge/interact",
            json=payload(intent_category="LOYALTY", user_query="What are my rewards?"),
        ).json()
        assert body["support_resolution"] is None
        assert body["advisory_recommendation"] is None
        assert body["intent_routed"] == "LOYALTY"

    def test_response_reports_the_routed_intent(self, client):
        body = client.post("/api/v1/concierge/interact", json=payload()).json()
        assert body["intent_routed"] == "ADVISORY"

    def test_response_is_reproducible_for_identical_input(self, client):
        first = client.post("/api/v1/concierge/interact", json=payload()).json()
        second = client.post("/api/v1/concierge/interact", json=payload()).json()
        assert first["session_id"] == second["session_id"]

    def test_experience_review_is_always_present(self, client):
        body = client.post("/api/v1/concierge/interact", json=payload()).json()
        assert body["experience_review"]["sentiment_grade"]
        assert 1 <= body["experience_review"]["hospitality_rating"] <= 5


class TestValidation:
    @pytest.mark.parametrize("score", [-1.5, 1.5, 100])
    def test_out_of_range_sentiment_is_rejected(self, client, score):
        response = client.post(
            "/api/v1/concierge/interact", json=payload(raw_sentiment_score=score)
        )
        assert response.status_code == 422

    def test_unknown_intent_is_rejected(self, client):
        response = client.post(
            "/api/v1/concierge/interact", json=payload(intent_category="TELEPORT")
        )
        assert response.status_code == 422

    def test_empty_query_is_rejected(self, client):
        response = client.post("/api/v1/concierge/interact", json=payload(user_query=""))
        assert response.status_code == 422

    def test_missing_query_is_rejected(self, client):
        body = payload()
        del body["user_query"]
        assert client.post("/api/v1/concierge/interact", json=body).status_code == 422

    def test_unknown_wealth_tier_is_rejected(self, client):
        body = payload()
        body["customer_profile"]["wealth_tier"] = "BILLIONAIRE"
        assert client.post("/api/v1/concierge/interact", json=body).status_code == 422

    def test_negative_aum_is_rejected(self, client):
        body = payload()
        body["customer_profile"]["assets_under_management_usd"] = -1
        assert client.post("/api/v1/concierge/interact", json=body).status_code == 422

    def test_validation_error_names_the_offending_field(self, client):
        detail = client.post(
            "/api/v1/concierge/interact", json=payload(raw_sentiment_score=9)
        ).json()["detail"]
        assert any("raw_sentiment_score" in str(item["loc"]) for item in detail)


class TestCors:
    def test_allowed_origin_is_echoed(self, client):
        origin = DEFAULT_ALLOWED_ORIGINS[0]
        response = client.get("/healthz", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin

    def test_unlisted_origin_is_not_granted_access(self, client):
        response = client.get("/healthz", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in response.headers

    def test_wildcard_origin_is_never_returned(self, client):
        response = client.get("/healthz", headers={"Origin": DEFAULT_ALLOWED_ORIGINS[0]})
        assert response.headers.get("access-control-allow-origin") != "*"

    def test_preflight_from_an_allowed_origin_succeeds(self, client):
        response = client.options(
            "/api/v1/concierge/interact",
            headers={
                "Origin": DEFAULT_ALLOWED_ORIGINS[0],
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
