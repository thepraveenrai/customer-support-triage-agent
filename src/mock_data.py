"""Realistic in-memory mock database and knowledge base for testing and demos.

This eliminates external database dependencies so students and instructors can
run the entire triage system immediately without configuring SQL databases or CRMs.
"""

from typing import Any, Dict, List, Optional


# ==============================================================================
# 1. Mock CRM Customer Profiles
# ==============================================================================

CUSTOMERS_DB: Dict[str, Dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Alice Smith",
        "email": "alice@acme-corp.com",
        "tier": "pro",
        "monthly_spend": 49.0,
        "joined_date": "2023-04-12",
        "status": "active",
        "account_manager": "Unassigned (Self-serve)",
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Bob Miller",
        "email": "bmiller@globalenterprise.io",
        "tier": "enterprise",
        "monthly_spend": 499.0,
        "joined_date": "2022-01-15",
        "status": "active",
        "account_manager": "Sarah Jenkins (VIP Lead)",
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Charlie Davis",
        "email": "charlie.d@gmail.com",
        "tier": "free",
        "monthly_spend": 0.0,
        "joined_date": "2024-02-20",
        "status": "active",
        "account_manager": "None (Community Tier)",
    },
    "CUST-004": {
        "customer_id": "CUST-004",
        "name": "Diana Prince",
        "email": "diana@themyscira-logistics.com",
        "tier": "pro",
        "monthly_spend": 99.0,
        "joined_date": "2023-09-01",
        "status": "active",
        "account_manager": "Unassigned",
    },
}

# Lookup index by email
CUSTOMER_BY_EMAIL: Dict[str, str] = {
    c["email"].lower(): c["customer_id"] for c in CUSTOMERS_DB.values()
}


# ==============================================================================
# 2. Mock Invoices
# ==============================================================================

INVOICES_DB: List[Dict[str, Any]] = [
    {
        "invoice_id": "INV-2024-001",
        "customer_id": "CUST-001",
        "amount": 49.00,
        "currency": "USD",
        "date": "2024-05-01",
        "status": "paid",
        "description": "Pro Tier Monthly Subscription - May 2024",
    },
    {
        "invoice_id": "INV-2024-002",
        "customer_id": "CUST-001",
        "amount": 49.00,
        "currency": "USD",
        "date": "2024-06-01",
        "status": "paid",
        "description": "Pro Tier Monthly Subscription - June 2024",
    },
    {
        "invoice_id": "INV-2024-099",
        "customer_id": "CUST-004",
        "amount": 250.00,
        "currency": "USD",
        "date": "2024-06-05",
        "status": "paid",
        "description": "Enterprise Add-on & Extra Compute Seats",
    },
    {
        "invoice_id": "INV-2024-501",
        "customer_id": "CUST-002",
        "amount": 499.00,
        "currency": "USD",
        "date": "2024-06-01",
        "status": "paid",
        "description": "Enterprise Dedicated Cluster - June 2024",
    },
]


# ==============================================================================
# 3. Mock System Health & Service Telemetry
# ==============================================================================

SYSTEM_STATUS_DB: Dict[str, Dict[str, Any]] = {
    "api-gateway": {
        "status": "operational",
        "latency_ms": 42,
        "error_rate_pct": 0.01,
        "last_incident": "None in last 30 days",
    },
    "auth-service": {
        "status": "operational",
        "latency_ms": 58,
        "error_rate_pct": 0.0,
        "last_incident": "Scheduled maintenance 14 days ago",
    },
    "data-sync-pipeline": {
        "status": "degraded",
        "latency_ms": 6240,
        "error_rate_pct": 14.8,
        "last_incident": "Active: Spike in 503 errors on /v2/sync worker pool. SRE investigating incident INC-8821.",
    },
    "billing-service": {
        "status": "operational",
        "latency_ms": 110,
        "error_rate_pct": 0.0,
        "last_incident": "None",
    },
}


# ==============================================================================
# 4. Mock Diagnostic Logs
# ==============================================================================

MOCK_SYSTEM_LOGS: List[Dict[str, str]] = [
    {
        "timestamp": "2024-06-12T10:14:22Z",
        "level": "ERROR",
        "service": "data-sync-pipeline",
        "message": "HTTP 503 Service Unavailable: upstream worker pool exhausted on partition sync",
    },
    {
        "timestamp": "2024-06-12T10:15:01Z",
        "level": "WARN",
        "service": "api-gateway",
        "message": "Timeout waiting for data-sync-pipeline response after 5000ms",
    },
    {
        "timestamp": "2024-06-12T10:20:00Z",
        "level": "INFO",
        "service": "billing-service",
        "message": "Webhook charge.succeeded processed for customer CUST-004 ($250.00)",
    },
]


# ==============================================================================
# 5. Mock Knowledge Base Articles
# ==============================================================================

KNOWLEDGE_BASE: List[Dict[str, str]] = [
    {
        "article_id": "KB-101",
        "title": "Refund and Cancellation Policy",
        "category": "billing",
        "content": (
            "We offer a 14-day no-questions-asked refund policy for subscription renewals. "
            "Refund requests under $50 can be automatically processed by support agents. "
            "Refund requests exceeding $50 or account terminations require Human Supervisor "
            "approval per compliance policy SEC-09. Funds appear in 3-5 business days."
        ),
    },
    {
        "article_id": "KB-202",
        "title": "Troubleshooting 503 Service Unavailable & Sync Delays",
        "category": "technical",
        "content": (
            "If encountering HTTP 503 on data sync pipelines: 1) Verify data-sync-pipeline "
            "status on status.platform.io. 2) Check if your client is passing excessive payload "
            "chunks (>10MB). 3) If incident INC-8821 is active, engineering is auto-scaling "
            "worker nodes; retry with exponential backoff (initial delay 5s)."
        ),
    },
    {
        "article_id": "KB-303",
        "title": "API Key Generation and Rate Limits",
        "category": "technical",
        "content": (
            "API keys can be generated in Dashboard > Settings > API Keys. "
            "Free tier is rate limited to 60 requests/min. Pro tier gets 600 req/min. "
            "Enterprise tier gets unlimited burst capacity."
        ),
    },
    {
        "article_id": "KB-404",
        "title": "Enterprise Dedicated Support & Escalation SLAs",
        "category": "escalation",
        "content": (
            "Enterprise customers receive 15-minute response SLA for Critical issues. "
            "Dedicated Account Managers are paged immediately when an Enterprise ticket is logged. "
            "For urgent outages, enterprise accounts can request war room video bridge."
        ),
    },
]
