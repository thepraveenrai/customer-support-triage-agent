"""API test suite for FastAPI support triage endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)


def test_api_root_health():
    """Verify system health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Customer Support Triage" in data["service"]


def test_api_calm_ticket_auto_resolve():
    """Verify API auto-resolves routine billing ticket."""
    payload = {
        "message": "Hi, I have a quick question about my invoice INV-2024-001 for $49.",
        "customer_id": "CUST-001",
        "customer_email": "alice@acme-corp.com",
        "customer_tier": "pro",
    }
    response = client.post("/api/tickets/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "billing"
    assert data["status"] == "resolved"
    assert data["requires_human_approval"] is False
    assert data["final_response"] is not None


def test_api_hitl_ticket_pause_and_resume():
    """Verify API pauses angry high-value refund ticket and resumes on human approval."""
    payload = {
        "message": "I was charged $250 without my consent! Give me a full refund immediately or I cancel!",
        "customer_id": "CUST-004",
        "customer_email": "diana@themyscira-logistics.com",
        "customer_tier": "pro",
    }
    response = client.post("/api/tickets/triage", json=payload)
    assert response.status_code == 200
    data = response.json()

    thread_id = data["thread_id"]
    assert data["requires_human_approval"] is True
    assert data["status"] == "pending_human_review"

    # Check state endpoint
    state_res = client.get(f"/api/tickets/{thread_id}/state")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert state_data["is_paused_for_human_review"] is True

    # Resume with approval
    resume_payload = {
        "decision": "approve",
        "feedback": "Approved refund in exception review.",
    }
    resume_res = client.post(f"/api/tickets/{thread_id}/resume", json=resume_payload)
    assert resume_res.status_code == 200
    resumed_data = resume_res.json()
    assert resumed_data["status"] == "resolved"
    assert resumed_data["final_response"] is not None
