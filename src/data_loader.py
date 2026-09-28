"""Enterprise Customer Support Dataset Loader & Analytics Engine.

Provides high-performance streaming, filtering, search, and statistical aggregation
for the 1,000+ customer support ticket dataset (data/customer_support_tickets_1000.csv).
"""

import csv
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

DEFAULT_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "customer_support_tickets_1000.csv",
)


def _cast_ticket_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Casts raw CSV string values into typed Python objects."""
    disputed_amt = None
    if row.get("disputed_amount") and row["disputed_amount"].strip():
        try:
            disputed_amt = float(row["disputed_amount"].strip())
        except ValueError:
            disputed_amt = None

    return {
        "id": row.get("ticket_id", ""),
        "ticket_id": row.get("ticket_id", ""),
        "customer_id": row.get("customer_id", ""),
        "customer_name": row.get("customer_name", ""),
        "customer_email": row.get("customer_email", ""),
        "customer_company": row.get("customer_company", ""),
        "customer_tier": row.get("customer_tier", "free"),
        "channel": row.get("channel", "email"),
        "subject": row.get("subject", ""),
        "message": row.get("message", ""),
        "disputed_amount": disputed_amt,
        "expected_category": row.get("expected_category", "technical"),
        "category": row.get("expected_category", "technical"),
        "expected_sentiment": row.get("expected_sentiment", "NEUTRAL"),
        "sentiment": row.get("expected_sentiment", "NEUTRAL"),
        "expected_priority": row.get("expected_priority", "LOW"),
        "priority": row.get("expected_priority", "LOW"),
        "churn_risk": str(row.get("churn_risk", "")).strip().lower() == "true",
        "expected_human_approval": str(row.get("expected_human_approval", "")).strip().lower() == "true",
        "requires_human": str(row.get("expected_human_approval", "")).strip().lower() == "true",
        "timestamp": row.get("timestamp", ""),
    }


def load_tickets_csv(
    csv_path: str = DEFAULT_CSV_PATH,
    limit: Optional[int] = None,
    offset: int = 0,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    priority: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Loads and filters tickets from the enterprise CSV dataset.

    Args:
        csv_path: Absolute or relative path to the CSV file.
        limit: Maximum number of tickets to return.
        offset: Number of matched tickets to skip before collecting.
        category: Filter by ticket category ('billing', 'technical', 'escalation').
        sentiment: Filter by sentiment ('POSITIVE', 'NEUTRAL', 'FRUSTRATED', 'ANGRY').
        priority: Filter by priority ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL').
        tier: Filter by customer tier ('free', 'pro', 'enterprise').
        search: Substring search across ticket_id, subject, message, customer name/company.

    Returns:
        List of typed ticket dictionaries.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Customer support dataset not found at: {csv_path}")

    results = []
    search_lower = search.lower().strip() if search else None
    matched_idx = 0

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            ticket = _cast_ticket_row(raw_row)

            # Category filter
            if category and ticket["expected_category"].lower() != category.lower():
                continue

            # Sentiment filter
            if sentiment and ticket["expected_sentiment"].upper() != sentiment.upper():
                continue

            # Priority filter
            if priority and ticket["expected_priority"].upper() != priority.upper():
                continue

            # Tier filter
            if tier and ticket["customer_tier"].lower() != tier.lower():
                continue

            # Full text search filter
            if search_lower:
                text_corpus = (
                    f"{ticket['ticket_id']} {ticket['subject']} {ticket['message']} "
                    f"{ticket['customer_name']} {ticket['customer_company']} {ticket['customer_email']}"
                ).lower()
                if search_lower not in text_corpus:
                    continue

            # Handle pagination offset
            if matched_idx < offset:
                matched_idx += 1
                continue

            results.append(ticket)
            matched_idx += 1

            if limit and len(results) >= limit:
                break

    return results


def get_ticket_by_id(
    ticket_id: str,
    csv_path: str = DEFAULT_CSV_PATH,
) -> Optional[Dict[str, Any]]:
    """Fetches a single ticket by its ticket_id (e.g. 'TIK-1042')."""
    target_id = ticket_id.strip().upper()
    if not os.path.exists(csv_path):
        return None

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            if raw_row.get("ticket_id", "").strip().upper() == target_id:
                return _cast_ticket_row(raw_row)

    return None


@lru_cache(maxsize=1)
def get_dataset_analytics(csv_path: str = DEFAULT_CSV_PATH) -> Dict[str, Any]:
    """Computes statistical metrics and distribution breakdowns across the dataset."""
    tickets = load_tickets_csv(csv_path=csv_path)
    total = len(tickets)

    categories: Dict[str, int] = {}
    sentiments: Dict[str, int] = {}
    priorities: Dict[str, int] = {}
    tiers: Dict[str, int] = {}
    channels: Dict[str, int] = {}

    hitl_count = 0
    churn_risk_count = 0
    disputed_amounts: List[float] = []

    for t in tickets:
        cat = t["expected_category"]
        categories[cat] = categories.get(cat, 0) + 1

        sent = t["expected_sentiment"]
        sentiments[sent] = sentiments.get(sent, 0) + 1

        prio = t["expected_priority"]
        priorities[prio] = priorities.get(prio, 0) + 1

        tier = t["customer_tier"]
        tiers[tier] = tiers.get(tier, 0) + 1

        ch = t["channel"]
        channels[ch] = channels.get(ch, 0) + 1

        if t["expected_human_approval"]:
            hitl_count += 1
        if t["churn_risk"]:
            churn_risk_count += 1
        if t["disputed_amount"] is not None:
            disputed_amounts.append(t["disputed_amount"])

    avg_dispute = sum(disputed_amounts) / len(disputed_amounts) if disputed_amounts else 0.0

    return {
        "total_tickets": total,
        "categories": categories,
        "sentiments": sentiments,
        "priorities": priorities,
        "tiers": tiers,
        "channels": channels,
        "human_review_required_count": hitl_count,
        "human_review_pct": round((hitl_count / total * 100) if total else 0.0, 1),
        "churn_risk_count": churn_risk_count,
        "churn_risk_pct": round((churn_risk_count / total * 100) if total else 0.0, 1),
        "total_disputed_amount_sum": round(sum(disputed_amounts), 2),
        "average_disputed_amount": round(avg_dispute, 2),
    }


# ==============================================================================
# Customer Dataset Loader & Analytics
# ==============================================================================

DEFAULT_CUSTOMERS_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "customers.csv",
)

DEFAULT_INVOICES_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "invoices.csv",
)


def load_customers_csv(
    csv_path: str = DEFAULT_CUSTOMERS_CSV,
    limit: Optional[int] = None,
    offset: int = 0,
    tier: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Loads and filters customers from the enterprise CRM CSV dataset.

    Args:
        csv_path: Path to the customers CSV.
        limit: Max number of customers to return.
        offset: Offset for pagination.
        tier: Filter by 'free', 'pro', or 'enterprise'.
        industry: Filter by industry.
        status: Filter by 'active', 'churn_risk', etc.
        country: Filter by 2-letter country code (e.g. 'US', 'DE').
        search: Substring search across customer_id, name, company, email.

    Returns:
        List of typed customer dictionaries.
    """
    if not os.path.exists(csv_path):
        return []

    results = []
    search_lower = search.lower().strip() if search else None
    matched_idx = 0

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            cid = raw.get("customer_id", "").strip().upper()
            c_tier = raw.get("tier", "free").lower()
            c_status = raw.get("account_status", "active").lower()
            c_ind = raw.get("industry", "")
            c_country = raw.get("billing_country", "").upper()

            if tier and c_tier != tier.lower():
                continue
            if status and c_status != status.lower():
                continue
            if industry and industry.lower() not in c_ind.lower():
                continue
            if country and c_country != country.upper():
                continue

            if search_lower:
                corpus = f"{cid} {raw.get('name', '')} {raw.get('company', '')} {raw.get('email', '')}".lower()
                if search_lower not in corpus:
                    continue

            if matched_idx < offset:
                matched_idx += 1
                continue

            try:
                monthly = float(raw.get("monthly_spend", 0.0))
            except ValueError:
                monthly = 0.0
            try:
                acv = float(raw.get("annual_contract_value", 0.0))
            except ValueError:
                acv = 0.0
            try:
                credit = float(raw.get("credit_balance", 0.0))
            except ValueError:
                credit = 0.0

            results.append({
                "customer_id": cid,
                "name": raw.get("name", ""),
                "email": raw.get("email", ""),
                "company": raw.get("company", ""),
                "tier": c_tier,
                "industry": c_ind,
                "monthly_spend": monthly,
                "annual_contract_value": acv,
                "account_manager": raw.get("account_manager", "Unassigned"),
                "sla_level": raw.get("sla_level", "Standard"),
                "joined_date": raw.get("joined_date", ""),
                "renewal_date": raw.get("renewal_date", ""),
                "status": c_status,
                "billing_country": c_country,
                "billing_city": raw.get("billing_city", ""),
                "phone": raw.get("phone", ""),
                "payment_method": raw.get("payment_method", ""),
                "credit_balance": credit,
                "active_licenses": int(raw.get("active_licenses", 1)),
            })

            matched_idx += 1
            if limit and len(results) >= limit:
                break

    return results


def get_customer_by_id(identifier: str, csv_path: str = DEFAULT_CUSTOMERS_CSV) -> Optional[Dict[str, Any]]:
    """Fetches a specific customer by ID (e.g. 'CUST-141') or email address."""
    clean_id = identifier.strip().lower()
    customers = load_customers_csv(csv_path=csv_path)
    for c in customers:
        if c["customer_id"].lower() == clean_id or c["email"].lower() == clean_id:
            return c
    return None


def load_invoices_csv(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    csv_path: str = DEFAULT_INVOICES_CSV,
) -> List[Dict[str, Any]]:
    """Loads invoices from the enterprise invoices dataset."""
    if not os.path.exists(csv_path):
        return []

    results = []
    clean_cid = customer_id.strip().upper() if customer_id else None

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            cid = raw.get("customer_id", "").strip().upper()
            inv_status = raw.get("status", "paid").lower()

            if clean_cid and cid != clean_cid:
                continue
            if status and inv_status != status.lower():
                continue

            try:
                amt = float(raw.get("amount", 0.0))
            except ValueError:
                amt = 0.0

            results.append({
                "invoice_id": raw.get("invoice_id", ""),
                "customer_id": cid,
                "customer_name": raw.get("customer_name", ""),
                "customer_company": raw.get("customer_company", ""),
                "amount": amt,
                "currency": raw.get("currency", "USD"),
                "date": raw.get("date", ""),
                "due_date": raw.get("due_date", ""),
                "status": inv_status,
                "description": raw.get("description", ""),
                "payment_method": raw.get("payment_method", ""),
            })

            if limit and len(results) >= limit:
                break

    return results


@lru_cache(maxsize=4)
def get_customer_dataset_analytics(csv_path: str = DEFAULT_CUSTOMERS_CSV) -> Dict[str, Any]:
    """Computes statistical metrics for the customer database."""
    customers = load_customers_csv(csv_path=csv_path)
    total = len(customers)

    tier_counts = {}
    status_counts = {}
    industry_counts = {}
    country_counts = {}
    total_mrr = 0.0
    total_acv = 0.0

    for c in customers:
        t = c["tier"]
        tier_counts[t] = tier_counts.get(t, 0) + 1

        st = c["status"]
        status_counts[st] = status_counts.get(st, 0) + 1

        ind = c["industry"]
        industry_counts[ind] = industry_counts.get(ind, 0) + 1

        ctry = c["billing_country"]
        country_counts[ctry] = country_counts.get(ctry, 0) + 1

        total_mrr += c["monthly_spend"]
        total_acv += c["annual_contract_value"]

    return {
        "total_customers": total,
        "tier_distribution": tier_counts,
        "status_distribution": status_counts,
        "industry_distribution": industry_counts,
        "country_distribution": country_counts,
        "total_monthly_recurring_revenue": round(total_mrr, 2),
        "total_annual_contract_value": round(total_acv, 2),
        "average_monthly_spend": round((total_mrr / total) if total else 0.0, 2),
    }

