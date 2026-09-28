"""Enterprise CRM Customer Store, Invoicing Ledger, and System Telemetry.

Provides access to 602 enterprise customer accounts, 2,207 historical invoices,
real-time system health telemetry, diagnostic logs, and support knowledge base articles.
Loads data directly from CSV datasets in data/ with robust in-memory fallbacks.
"""

import csv
import os
from typing import Any, Dict, List, Optional

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CUSTOMERS_CSV = os.path.join(_BASE_DIR, "data", "customers.csv")
_INVOICES_CSV = os.path.join(_BASE_DIR, "data", "invoices.csv")


# ==============================================================================
# 1. CRM Customer Profiles (CSV Loader with Seed Fallback)
# ==============================================================================

_SEED_CUSTOMERS: Dict[str, Dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Alice Smith",
        "email": "alice@acme-corp.com",
        "company": "Acme Corp Global",
        "tier": "pro",
        "industry": "Cloud Infrastructure & DevOps",
        "monthly_spend": 49.0,
        "annual_contract_value": 588.0,
        "account_manager": "Growth Account Desk (US-East)",
        "sla_level": "Priority Business (4h Business Hours SLA)",
        "joined_date": "2023-04-12",
        "renewal_date": "2025-04-12",
        "status": "active",
        "account_status": "active",
        "billing_country": "US",
        "billing_city": "San Francisco, CA",
        "phone": "+1-415-555-0192",
        "payment_method": "Visa ending 4242",
        "credit_balance": 0.0,
        "active_licenses": 10,
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Bob Miller",
        "email": "bmiller@globalenterprise.io",
        "company": "GlobalEnterprise Holdings",
        "tier": "enterprise",
        "industry": "Fintech & Payments",
        "monthly_spend": 499.0,
        "annual_contract_value": 5988.0,
        "account_manager": "Sarah Jenkins (VIP Lead)",
        "sla_level": "Enterprise Critical (15min 24/7 SLA • 99.99% Uptime Guarantee)",
        "joined_date": "2022-01-15",
        "renewal_date": "2025-01-15",
        "status": "active",
        "account_status": "active",
        "billing_country": "US",
        "billing_city": "New York, NY",
        "phone": "+1-212-555-0833",
        "payment_method": "ACH Direct Corporate Transfer (JPMorgan Chase)",
        "credit_balance": 500.0,
        "active_licenses": 250,
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Charlie Davis",
        "email": "charlie.d@gmail.com",
        "company": "Davis Independent Tech",
        "tier": "free",
        "industry": "Data Analytics & AI",
        "monthly_spend": 0.0,
        "annual_contract_value": 0.0,
        "account_manager": "Community Tier Automated Bot",
        "sla_level": "Standard Community (48h SLA)",
        "joined_date": "2024-02-20",
        "renewal_date": "2025-02-20",
        "status": "active",
        "account_status": "active",
        "billing_country": "US",
        "billing_city": "Austin, TX",
        "phone": "+1-512-555-0341",
        "payment_method": "None (Free Tier)",
        "credit_balance": 0.0,
        "active_licenses": 1,
    },
    "CUST-004": {
        "customer_id": "CUST-004",
        "name": "Diana Prince",
        "email": "diana@themyscira-logistics.com",
        "company": "Themyscira Logistics Global",
        "tier": "pro",
        "industry": "Enterprise Logistics & Supply Chain",
        "monthly_spend": 250.0,
        "annual_contract_value": 3000.0,
        "account_manager": "Elena Rostova (Strategic Accounts)",
        "sla_level": "Priority Business (4h Business Hours SLA)",
        "joined_date": "2023-09-01",
        "renewal_date": "2024-09-01",
        "status": "active",
        "account_status": "active",
        "billing_country": "US",
        "billing_city": "Seattle, WA",
        "phone": "+1-206-555-0774",
        "payment_method": "Mastercard ending 9182",
        "credit_balance": 50.0,
        "active_licenses": 35,
    },
}


def _load_customers_db() -> Dict[str, Dict[str, Any]]:
    customers: Dict[str, Dict[str, Any]] = dict(_SEED_CUSTOMERS)
    if os.path.exists(_CUSTOMERS_CSV):
        try:
            with open(_CUSTOMERS_CSV, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cid = row["customer_id"].strip().upper()
                    try:
                        monthly = float(row.get("monthly_spend", 0.0))
                    except ValueError:
                        monthly = 0.0
                    try:
                        acv = float(row.get("annual_contract_value", 0.0))
                    except ValueError:
                        acv = 0.0
                    try:
                        credit = float(row.get("credit_balance", 0.0))
                    except ValueError:
                        credit = 0.0
                    try:
                        licenses = int(row.get("active_licenses", 1))
                    except ValueError:
                        licenses = 1

                    customers[cid] = {
                        "customer_id": cid,
                        "name": row.get("name", ""),
                        "email": row.get("email", ""),
                        "company": row.get("company", ""),
                        "tier": row.get("tier", "free").lower(),
                        "industry": row.get("industry", "Technology"),
                        "monthly_spend": monthly,
                        "annual_contract_value": acv,
                        "account_manager": row.get("account_manager", "Unassigned"),
                        "sla_level": row.get("sla_level", "Standard Community (48h SLA)"),
                        "joined_date": row.get("joined_date", ""),
                        "renewal_date": row.get("renewal_date", ""),
                        "status": row.get("account_status", "active"),
                        "account_status": row.get("account_status", "active"),
                        "billing_country": row.get("billing_country", "US"),
                        "billing_city": row.get("billing_city", ""),
                        "phone": row.get("phone", ""),
                        "payment_method": row.get("payment_method", ""),
                        "credit_balance": credit,
                        "active_licenses": licenses,
                    }
        except Exception as e:
            print(f"Warning: Could not load customers CSV: {e}")
    return customers


CUSTOMERS_DB: Dict[str, Dict[str, Any]] = _load_customers_db()

# Lookup index by email
CUSTOMER_BY_EMAIL: Dict[str, str] = {
    c["email"].lower(): c["customer_id"] for c in CUSTOMERS_DB.values() if c.get("email")
}


# ==============================================================================
# 2. Invoicing Ledger (CSV Loader with Seed Fallback)
# ==============================================================================

_SEED_INVOICES: List[Dict[str, Any]] = [
    {
        "invoice_id": "INV-2024-001",
        "customer_id": "CUST-001",
        "customer_name": "Alice Smith",
        "customer_company": "Acme Corp Global",
        "amount": 49.00,
        "currency": "USD",
        "date": "2024-05-01",
        "due_date": "2024-05-31",
        "status": "paid",
        "description": "Pro Tier Monthly Subscription - May 2024",
        "payment_method": "Visa ending 4242",
    },
    {
        "invoice_id": "INV-2024-002",
        "customer_id": "CUST-001",
        "customer_name": "Alice Smith",
        "customer_company": "Acme Corp Global",
        "amount": 49.00,
        "currency": "USD",
        "date": "2024-06-01",
        "due_date": "2024-06-30",
        "status": "paid",
        "description": "Pro Tier Monthly Subscription - June 2024",
        "payment_method": "Visa ending 4242",
    },
    {
        "invoice_id": "INV-2024-099",
        "customer_id": "CUST-004",
        "customer_name": "Diana Prince",
        "customer_company": "Themyscira Logistics Global",
        "amount": 250.00,
        "currency": "USD",
        "date": "2024-06-05",
        "due_date": "2024-07-05",
        "status": "disputed",
        "description": "Enterprise Add-on & Extra Compute Seats",
        "payment_method": "Mastercard ending 9182",
    },
    {
        "invoice_id": "INV-2024-501",
        "customer_id": "CUST-002",
        "customer_name": "Bob Miller",
        "customer_company": "GlobalEnterprise Holdings",
        "amount": 499.00,
        "currency": "USD",
        "date": "2024-06-01",
        "due_date": "2024-07-01",
        "status": "paid",
        "description": "Enterprise Dedicated Cluster - June 2024",
        "payment_method": "ACH Direct Corporate Transfer (JPMorgan Chase)",
    },
]


def _load_invoices_db() -> List[Dict[str, Any]]:
    invoices: List[Dict[str, Any]] = list(_SEED_INVOICES)
    seen_ids = {inv["invoice_id"] for inv in invoices}
    if os.path.exists(_INVOICES_CSV):
        try:
            with open(_INVOICES_CSV, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    inv_id = row["invoice_id"].strip()
                    if inv_id in seen_ids:
                        continue
                    seen_ids.add(inv_id)
                    try:
                        amt = float(row.get("amount", 0.0))
                    except ValueError:
                        amt = 0.0
                    invoices.append({
                        "invoice_id": inv_id,
                        "customer_id": row.get("customer_id", "").strip().upper(),
                        "customer_name": row.get("customer_name", ""),
                        "customer_company": row.get("customer_company", ""),
                        "amount": amt,
                        "currency": row.get("currency", "USD"),
                        "date": row.get("date", ""),
                        "due_date": row.get("due_date", ""),
                        "status": row.get("status", "paid"),
                        "description": row.get("description", "Subscription invoice"),
                        "payment_method": row.get("payment_method", "Visa ending 4242"),
                    })
        except Exception as e:
            print(f"Warning: Could not load invoices CSV: {e}")
    return invoices


INVOICES_DB: List[Dict[str, Any]] = _load_invoices_db()


# ==============================================================================
# 3. System Health & Service Telemetry
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
# 4. Diagnostic Logs
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
# 5. Knowledge Base Articles
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
