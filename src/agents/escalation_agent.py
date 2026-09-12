"""Escalation Specialist Agent Node.

Specializes in high-stakes customer interactions:
- VIP / Enterprise account tier grievances
- Legal threats or churn risk
- Unresolvable cross-functional incidents

Prepares an Executive Dossier and routes into the Human-in-the-Loop checkpoint
so an Account Executive or Support Director can intervene.
"""

from typing import Any, Dict, List
from langchain_core.messages import AIMessage, HumanMessage
from src.mock_data import CUSTOMERS_DB
from src.state import TriageState
from src.tools.billing_tools import lookup_customer_profile


def escalation_agent_node(state: TriageState) -> Dict[str, Any]:
    """Specialist node handling high-priority escalations and executive briefings.

    Args:
        state: Current TriageState.

    Returns:
        State dictionary updates with executive dossier and human approval flag set to True.
    """
    customer_id = state.get("customer_id", "CUST-002")
    actions: List[str] = list(state.get("actions_taken", []))

    # 1. Step 1: Look up VIP profile and account manager
    profile_res = lookup_customer_profile.invoke({"identifier": customer_id})
    actions.append(f"lookup_customer_profile({customer_id})")

    customer_info = profile_res.get("customer", {})
    account_mgr = customer_info.get("account_manager", "Senior Support Manager")
    tier = customer_info.get("tier", state.get("customer_tier", "enterprise"))

    # 2. Extract grievance from messages
    user_msgs = [m.content for m in state["messages"] if isinstance(m, HumanMessage) or m.type == "human"]
    complaint_summary = " ".join(user_msgs)

    # 3. Create Executive Briefing Dossier
    executive_dossier = (
        f"🚨 EXECUTIVE ESCALATION BRIEFING\n"
        f"---------------------------------------------------\n"
        f"Ticket ID:         {state['ticket_id']}\n"
        f"Customer:          {customer_info.get('name', 'Valued Customer')} ({customer_id})\n"
        f"Account Tier:      {tier.upper()}\n"
        f"Monthly Spend:     ${customer_info.get('monthly_spend', 0.0):.2f}/mo\n"
        f"Assigned Lead:     {account_mgr}\n"
        f"Assessed Sentiment:{state.get('sentiment', 'ANGRY')}\n"
        f"Priority:          {state.get('priority', 'CRITICAL')}\n"
        f"Churn Risk:        {state.get('churn_risk', True)}\n"
        f"Customer Issue:    {complaint_summary}\n"
        f"---------------------------------------------------\n"
        f"Recommended Action: Immediate personal outreach by {account_mgr} "
        f"with incident report or executive credit."
    )

    # 4. Draft professional de-escalation response for human review
    draft_response = (
        f"Dear {customer_info.get('name', 'Customer')},\n\n"
        f"Thank you for contacting our leadership team. We understand the urgency of your situation "
        f"and sincerely apologize for the frustration this has caused.\n\n"
        f"Your ticket has been escalated directly to our Senior Account Lead, {account_mgr}. "
        f"We are conducting a priority review of your account and will follow up with you directly "
        f"with a comprehensive resolution.\n\n"
        f"Sincerely,\n"
        f"Customer Support Executive Escalations Team"
    )

    actions.append("generated_executive_dossier()")
    actions.append(f"paged_account_manager({account_mgr})")

    agent_message = AIMessage(
        content=(
            f"🚨 [Escalation Specialist Dossier Prepared]\n"
            f"{executive_dossier}\n\n"
            f"Draft Customer Message:\n{draft_response}"
        )
    )

    return {
        "messages": [agent_message],
        "draft_response": draft_response,
        "actions_taken": actions,
        "requires_human_approval": True,
        "approval_reason": (
            f"Escalation ticket for {customer_id} ({tier.upper()} tier). "
            f"Requires Human Manager review and authorization."
        ),
        "status": "pending_human_review",
    }
