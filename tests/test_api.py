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


def test_api_dataset_stats():
    """Verify enterprise dataset stats endpoint aggregates 1,000 tickets."""
    response = client.get("/api/dataset/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_tickets"] >= 1000
    assert "categories" in stats
    assert "technical" in stats["categories"]
    assert "billing" in stats["categories"]
    assert "escalation" in stats["categories"]
    assert stats["human_review_required_count"] > 0
    assert stats["total_disputed_amount_sum"] > 0


def test_api_dataset_tickets_pagination_and_filtering():
    """Verify enterprise dataset listing with pagination and category/tier filters."""
    # Test pagination
    response = client.get("/api/dataset/tickets?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["tickets"]) == 10

    # Test filtering by category
    resp_billing = client.get("/api/dataset/tickets?category=billing&limit=5")
    assert resp_billing.status_code == 200
    billing_data = resp_billing.json()
    assert len(billing_data["tickets"]) == 5
    for t in billing_data["tickets"]:
        assert t["expected_category"] == "billing"


def test_api_dataset_single_ticket():
    """Verify single ticket retrieval by ID from enterprise dataset."""
    response = client.get("/api/dataset/tickets/TIK-1001")
    assert response.status_code == 200
    ticket = response.json()
    assert ticket["ticket_id"] == "TIK-1001"
    assert "customer_id" in ticket
    assert "message" in ticket


def test_api_customers_list_and_profile():
    """Verify customer CRM directory and Customer 360 profile endpoints."""
    # Test list customers
    res = client.get("/api/customers?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total_matched"] == 10
    assert "crm_summary" in data
    assert data["crm_summary"]["total_customers"] >= 600

    # Test single customer 360 profile
    res_c = client.get("/api/customers/CUST-141")
    assert res_c.status_code == 200
    cdata = res_c.json()
    assert cdata["customer"]["customer_id"] == "CUST-141"
    assert cdata["customer"]["company"] == "Horizon Retail Network"
    assert cdata["customer"]["tier"] == "enterprise"
    assert cdata["total_invoices"] >= 1


def test_api_submit_ticket_for_customer():
    """Verify submitting a ticket directly on a customer's account."""
    payload = {
        "message": "We are experiencing network timeouts connecting to your API. Can you investigate?",
        "subject": "Urgent API Timeout Issue",
    }
    res = client.post("/api/customers/CUST-141/ticket", json=payload)
    assert res.status_code == 200
    tdata = res.json()
    assert tdata["status"] in ["resolved", "pending_human_review"]
    assert tdata["category"] in ["technical", "escalation"]
    assert tdata["final_response"] is not None or tdata["draft_response"] is not None


