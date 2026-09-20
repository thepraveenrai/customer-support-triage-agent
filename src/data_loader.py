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
