"""Human-in-the-Loop (HITL) Review Node.

This node is the checkpoint boundary where human operators review, approve,
edit, or reject agent decisions.

In LangGraph, HITL is implemented using Checkpointers (e.g. MemorySaver).
When the graph pauses before or inside this node, the execution thread state
is persisted. A human manager can inspect the state, supply approval data,
and resume execution.
"""

from typing import Any, Dict
from langchain_core.messages import AIMessage
from src.state import TriageState


def human_review_node(state: TriageState) -> Dict[str, Any]:
    """Processes human managerial review on flagged tickets.

    Evaluates the human_decision field ('approve', 'reject', 'edit') and updates
    the final response and ticket status accordingly.

    Args:
        state: The current TriageState.

    Returns:
        State dictionary updates with final_response, status, and audit message.
    """
    decision = state.get("human_decision", "approve")
    feedback = state.get("human_feedback")
    draft = state.get("draft_response", "")

    if decision == "approve":
        final_text = draft
        audit_note = "✅ Human Manager APPROVED the agent draft without modification."
        ticket_status = "resolved"

    elif decision == "edit":
        # Use human manager's customized response text
        final_text = feedback if feedback else draft
        audit_note = "✏️ Human Manager EDITED the response before sending to the customer."
        ticket_status = "resolved"

    elif decision == "reject":
        reason = feedback if feedback else "Action not authorized under standard service terms."
        final_text = (
            f"Hello,\n\n"
            f"Your request has been reviewed by our Customer Support Operations Team. "
            f"At this time, we are unable to approve the requested action. "
            f"Details: {reason}\n\n"
            f"If you have additional documentation or questions, please reply to this thread."
        )
        audit_note = f"❌ Human Manager REJECTED the agent draft. Reason: {reason}"
        ticket_status = "resolved"

    else:
        # Fallback / pending
        final_text = draft
        audit_note = "⏳ Pending Human Review."
        ticket_status = "pending_human_review"

    review_msg = AIMessage(
        content=(
            f"👤 [Human-in-the-Loop Review Executed]\n"
            f"Decision: {decision.upper()}\n"
            f"Audit: {audit_note}\n\n"
            f"Final Message to Customer:\n{final_text}"
        )
    )

    return {
        "messages": [review_msg],
        "final_response": final_text,
        "status": ticket_status,
        "human_decision": decision,
    }
