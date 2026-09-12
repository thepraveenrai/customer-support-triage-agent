"""Billing Specialist Agent Node.

Specializes in financial inquiries, invoice lookups, subscription adjustments,
and refund requests.

Enforces business policy:
- Automated refunds allowed up to $50.00.
- Any refund > $50.00 or cancellation halts for Human-in-the-Loop approval.
"""

import re
from typing import Any, Dict, List
from langchain_core.messages import AIMessage, HumanMessage
from src.config import settings
from src.state import TriageState
from src.tools.billing_tools import (
    get_invoice_history,
    lookup_customer_profile,
    process_refund,
)


def billing_agent_node(state: TriageState) -> Dict[str, Any]:
    """Specialist node handling billing, subscriptions, invoices, and refunds.

    Args:
        state: The current TriageState.

    Returns:
        State dictionary updates including draft_response, actions_taken,
        and human approval requirements.
    """
    customer_id = state.get("customer_id", "CUST-001")
    actions: List[str] = list(state.get("actions_taken", []))

    # 1. Step 1: Look up customer profile
    profile_res = lookup_customer_profile.invoke({"identifier": customer_id})
    actions.append(f"lookup_customer_profile({customer_id})")

    # 2. Step 2: Retrieve customer's billing invoices
    invoices_res = get_invoice_history.invoke({"customer_id": customer_id})
    actions.append(f"get_invoice_history({customer_id})")

    # 3. Analyze customer inquiry for refund or cancellation intents
    user_msgs = [m.content for m in state["messages"] if isinstance(m, HumanMessage) or m.type == "human"]
    inquiry_text = " ".join(user_msgs).lower()

    requires_human = False
    approval_reason = None
    draft_response = ""

    # Look for dollar amounts mentioned in the text (e.g. $250, $49, 250 dollars)
    amount_match = re.search(r"\$\s*(\d+(?:\.\d{2})?)", inquiry_text)
    if not amount_match:
        amount_match = re.search(r"(\d+(?:\.\d{2})?)\s*(?:dollars|usd)", inquiry_text)

    requested_amount = float(amount_match.group(1)) if amount_match else None

    # Check if a refund or cancellation is being requested
    if "refund" in inquiry_text or "cancel" in inquiry_text or "dispute" in inquiry_text:
        # Determine target invoice
        invoices = invoices_res.get("invoices", [])
        target_inv = invoices[-1] if invoices else None

        refund_target_amount = requested_amount or (target_inv["amount"] if target_inv else 49.0)
        target_inv_id = target_inv["invoice_id"] if target_inv else "INV-2024-UNKNOWN"

        # Check threshold rule (> $50 requires human manager approval)
        if refund_target_amount > settings.REFUND_APPROVAL_THRESHOLD_USD:
            requires_human = True
            approval_reason = (
                f"Requested refund of ${refund_target_amount:.2f} on {target_inv_id} "
                f"exceeds automated threshold of ${settings.REFUND_APPROVAL_THRESHOLD_USD:.2f}. "
                "Compliance policy requires Supervisor sign-off."
            )
            actions.append(f"flagged_for_human_approval(amount=${refund_target_amount:.2f})")

            draft_response = (
                f"Hello,\n\n"
                f"Thank you for contacting billing support. We have verified your account ({customer_id}) "
                f"and located your invoice {target_inv_id} for ${refund_target_amount:.2f}.\n\n"
                f"Because this refund request exceeds our standard automated threshold, "
                f"it has been forwarded to our billing manager for expedited review and release. "
                f"Once authorized, your funds will be returned to your original payment method in 3-5 business days."
            )
        else:
            # Automated refund execution
            refund_res = process_refund.invoke({
                "customer_id": customer_id,
                "invoice_id": target_inv_id,
                "amount": refund_target_amount,
                "reason": "Customer support ticket resolution",
            })
            actions.append(f"process_refund({target_inv_id}, amount=${refund_target_amount:.2f})")

            draft_response = (
                f"Hello,\n\n"
                f"We have verified your account and processed a full refund of ${refund_target_amount:.2f} "
                f"for invoice {target_inv_id}.\n\n"
                f"You should see the credit reflected on your bank statement within 3 to 5 business days. "
                f"Please let us know if you need anything else!"
            )
    else:
        # Standard invoice query / billing question
        inv_count = invoices_res.get("total_invoices", 0)
        draft_response = (
            f"Hello,\n\n"
            f"Thank you for reaching out to billing support. We reviewed your account profile ({customer_id}). "
            f"You currently have {inv_count} recorded invoices. Your subscription is active and up to date.\n\n"
            f"Please let us know if you would like a copy of a specific invoice statement or have any questions!"
        )

    # If the sentiment was marked ANGRY or CRITICAL priority, enforce human review
    if settings.ENFORCE_SENTIMENT_HUMAN_GATE and (state.get("sentiment") == "ANGRY" or state.get("priority") == "CRITICAL"):
        requires_human = True
        approval_reason = approval_reason or "Customer sentiment is ANGRY. Manager review required before sending."

    agent_message = AIMessage(
        content=(
            f"💳 [Billing Specialist Response Drafted]\n"
            f"Actions Taken: {', '.join(actions)}\n"
            f"Requires Human Approval: {requires_human}\n"
            f"Draft:\n{draft_response}"
        )
    )

    return {
        "messages": [agent_message],
        "draft_response": draft_response,
        "actions_taken": actions,
        "requires_human_approval": requires_human,
        "approval_reason": approval_reason,
        "status": "pending_human_review" if requires_human else "resolved",
    }
