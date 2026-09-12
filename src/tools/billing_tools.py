"""Billing and financial tools for the Billing Specialist Agent.

In LangGraph multi-agent systems, agents are equipped with specialized tools
to query databases, verify customer records, and perform actions safely.
"""

from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from src.mock_data import CUSTOMERS_DB, CUSTOMER_BY_EMAIL, INVOICES_DB


@tool
def lookup_customer_profile(identifier: str) -> Dict[str, Any]:
    """Look up a customer account by their Customer ID (e.g. 'CUST-001') or email address.

    Args:
        identifier: Customer ID (e.g. CUST-001) or email address (e.g. alice@acme-corp.com).

    Returns:
        Customer profile dictionary with tier, status, monthly spend, and account manager.
    """
    clean_id = identifier.strip()
    # Check direct ID match
    if clean_id.upper() in CUSTOMERS_DB:
        return {"found": True, "customer": CUSTOMERS_DB[clean_id.upper()]}

    # Check email index
    cust_id = CUSTOMER_BY_EMAIL.get(clean_id.lower())
    if cust_id and cust_id in CUSTOMERS_DB:
        return {"found": True, "customer": CUSTOMERS_DB[cust_id]}

    return {
        "found": False,
        "error": f"No customer found with identifier '{identifier}'",
    }


@tool
def get_invoice_history(customer_id: str) -> Dict[str, Any]:
    """Retrieve billing history and previous invoices for a customer.

    Args:
        customer_id: The unique customer identifier (e.g. 'CUST-001').

    Returns:
        List of past invoices with amounts, dates, and payment statuses.
    """
    clean_id = customer_id.strip().upper()
    invoices = [inv for inv in INVOICES_DB if inv["customer_id"] == clean_id]

    if not invoices:
        return {
            "found": False,
            "customer_id": clean_id,
            "invoices": [],
            "message": f"No invoices found for customer {clean_id}",
        }

    return {
        "found": True,
        "customer_id": clean_id,
        "total_invoices": len(invoices),
        "invoices": invoices,
    }


@tool
def process_refund(customer_id: str, invoice_id: str, amount: float, reason: str) -> Dict[str, Any]:
    """Execute or prepare a refund for a customer's specific invoice.

    Args:
        customer_id: The customer ID requesting the refund (e.g. 'CUST-001').
        invoice_id: The specific invoice ID to refund (e.g. 'INV-2024-001').
        amount: The monetary amount in USD to refund.
        reason: Justification provided for the refund.

    Returns:
        Refund processing result detailing whether it succeeded or requires approval.
    """
    clean_cid = customer_id.strip().upper()
    clean_iid = invoice_id.strip().upper()

    # Locate invoice
    matching = [
        inv
        for inv in INVOICES_DB
        if inv["invoice_id"] == clean_iid and inv["customer_id"] == clean_cid
    ]

    if not matching:
        return {
            "status": "failed",
            "error": f"Invoice {clean_iid} does not exist for customer {clean_cid}.",
        }

    target_inv = matching[0]

    # Validate amount
    if amount > target_inv["amount"]:
        return {
            "status": "failed",
            "error": f"Requested refund (${amount}) exceeds invoice total (${target_inv['amount']}).",
        }

    # If amount exceeds $50, company policy requires human approval
    if amount > 50.0:
        return {
            "status": "approval_required",
            "invoice_id": clean_iid,
            "amount": amount,
            "reason": reason,
            "message": (
                f"Refund amount ${amount:.2f} exceeds the automated limit of $50.00. "
                "Per compliance rule SEC-09, managerial Human Approval is required."
            ),
        }

    return {
        "status": "completed",
        "invoice_id": clean_iid,
        "refunded_amount": amount,
        "currency": "USD",
        "message": f"Successfully refunded ${amount:.2f} to original payment method.",
    }
