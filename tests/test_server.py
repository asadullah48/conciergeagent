from fastapi.testclient import TestClient
from conciergeagent.server import app

client = TestClient(app)

def test_server_dashboard_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "ConciergeAgent" in res.text

def test_server_healthz():
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_server_readyz():
    res = client.get("/readyz")
    assert res.status_code == 200
    assert res.json()["concierge_agents_active"] == 3

def test_server_interact_api():
    payload = {
        "interaction_id": "INT-API-001",
        "customer_profile": {
            "customer_id": "CUST-001",
            "name": "Lady Victoria",
            "wealth_tier": "ULTRA_HNW",
            "primary_domain": "BANKING",
            "assets_under_management_usd": 15000000.0,
            "lifetime_value_score": 98.0,
            "loyalty_points": 500000,
            "preferred_tone": "Formal",
            "relationship_tenure_years": 10
        },
        "user_query": "I would like to explore private equity co-investments.",
        "intent_category": "ADVISORY",
        "raw_sentiment_score": 0.95
    }
    res = client.post("/api/v1/concierge/interact", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["customer_name"] == "Lady Victoria"
    assert data["advisory_recommendation"] is not None
    assert "Global Private Equity & VC" in data["advisory_recommendation"]["portfolio_allocation"]
