"""Messy real-world support tickets used to stress-test the triage agent.

These 6 scenarios mirror production environments, testing edge cases like
unauthorized charges, angry churn threats, cryptic stack traces, VIP SLAs,
ambiguous multi-intents, and routine queries.
"""

from typing import Any, Dict, List

SAMPLE_TICKETS: List[Dict[str, Any]] = [
    {
        "id": "TIK-101",
        "name": "Calm Billing Inquiry",
        "customer_id": "CUST-001",
        "customer_email": "alice@acme-corp.com",
        "customer_tier": "pro",
        "message": (
            "Hi support team! I noticed charge INV-2024-001 for $49 on my card today. "
            "Can you confirm whether this covers my Pro subscription for this month? "
            "Thanks for your help!"
        ),
        "expected_category": "billing",
        "expected_sentiment": "NEUTRAL",
        "expected_human_approval": False,
    },
    {
        "id": "TIK-102",
        "name": "Furious Customer Demanding $250 Refund",
        "customer_id": "CUST-004",
        "customer_email": "diana@themyscira-logistics.com",
        "customer_tier": "pro",
        "message": (
            "THIS IS COMPLETELY UNACCEPTABLE! You charged my card $250 for invoice INV-2024-099 "
            "without my authorization! I DEMAND AN IMMEDIATE $250 REFUND or I will report "
            "this fraud to my bank, cancel my subscription, and never use your product again!"
        ),
        "expected_category": "billing",
        "expected_sentiment": "ANGRY",
        "expected_human_approval": True,  # Refund > $50 + ANGRY sentiment triggers human review
    },
    {
        "id": "TIK-103",
        "name": "Cryptic Technical Stack Trace & 503 Outage",
        "customer_id": "CUST-001",
        "customer_email": "alice@acme-corp.com",
        "customer_tier": "pro",
        "message": (
            "Our automated ingestion pipeline broke 15 minutes ago. Error output:\n"
            "HTTP 503 Service Unavailable: upstream worker pool exhausted on partition sync\n"
            "Is the data sync pipeline down? We are blocked on processing our client data."
        ),
        "expected_category": "technical",
        "expected_sentiment": "FRUSTRATED",
        "expected_human_approval": False,
    },
    {
        "id": "TIK-104",
        "name": "VIP Enterprise Escalation & Lawsuit Threat",
        "customer_id": "CUST-002",
        "customer_email": "bmiller@globalenterprise.io",
        "customer_tier": "enterprise",
        "message": (
            "This is Bob Miller, CTO of GlobalEnterprise (CUST-002). Your catastrophic server "
            "outage today breached our enterprise 99.99% SLA. I need an emergency call with our "
            "dedicated account lead Sarah and senior management within 30 minutes, or our corporate "
            "lawyer will commence litigation for contract damages."
        ),
        "expected_category": "escalation",
        "expected_sentiment": "ANGRY",
        "expected_human_approval": True,  # Escalation + Legal threat requires executive review
    },
    {
        "id": "TIK-105",
        "name": "Ambiguous Multi-Intent Inquiry",
        "customer_id": "CUST-003",
        "customer_email": "charlie.d@gmail.com",
        "customer_tier": "free",
        "message": (
            "Hey, your website crashed with a bug when I was trying to look at the billing page, "
            "and I also wanted to ask how to reset my API key and what the rate limits are."
        ),
        "expected_category": "technical",
        "expected_sentiment": "NEUTRAL",
        "expected_human_approval": False,
    },
    {
        "id": "TIK-106",
        "name": "Routine API Documentation Question",
        "customer_id": "CUST-003",
        "customer_email": "charlie.d@gmail.com",
        "customer_tier": "free",
        "message": (
            "Hello! I am building an integration and need to know the API rate limits "
            "and how to generate an API key. Could you point me to the documentation?"
        ),
        "expected_category": "technical",
        "expected_sentiment": "NEUTRAL",
        "expected_human_approval": False,
    },
]


def test_sample_ticket_batch_execution():
    """Verify all 6 sample tickets can be executed through the triage pipeline."""
    from run_triage import execute_ticket

    for ticket in SAMPLE_TICKETS:
        res = execute_ticket(ticket, interactive_hitl=False)
        assert res["status"] == "resolved"
        assert res["final_response"] is not None
        assert res["requires_human_approval"] == ticket["expected_human_approval"]

