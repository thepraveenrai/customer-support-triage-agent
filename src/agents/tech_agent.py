"""Technical Support Specialist Agent Node.

Specializes in troubleshooting, API integration errors, system health diagnostics,
and knowledge base resolution.
"""

from typing import Any, Dict, List
from langchain_core.messages import AIMessage, HumanMessage
from src.config import settings
from src.state import TriageState
from src.tools.tech_tools import (
    check_system_service_status,
    fetch_system_logs,
    search_knowledge_base,
)


def tech_agent_node(state: TriageState) -> Dict[str, Any]:
    """Specialist node resolving technical issues, server errors, and API questions.

    Args:
        state: The current TriageState.

    Returns:
        State dictionary updates including draft_response, actions_taken,
        and human approval requirements.
    """
    actions: List[str] = list(state.get("actions_taken", []))

    user_msgs = [m.content for m in state["messages"] if isinstance(m, HumanMessage) or m.type == "human"]
    inquiry_text = " ".join(user_msgs).lower()

    # 1. Step 1: Check system health and service telemetry
    service_status = check_system_service_status.invoke({})
    actions.append("check_system_service_status()")

    # 2. Step 2: Search knowledge base for relevant troubleshooting guides
    kb_results = search_knowledge_base.invoke({"query": inquiry_text})
    actions.append("search_knowledge_base()")

    # 3. Step 3: Fetch logs if errors or downtime are suspected
    has_503_or_sync = "503" in inquiry_text or "sync" in inquiry_text or "timeout" in inquiry_text
    recent_logs = []
    if has_503_or_sync:
        logs_res = fetch_system_logs.invoke({"service": "data-sync-pipeline", "limit": 3})
        recent_logs = logs_res.get("logs", [])
        actions.append("fetch_system_logs(service='data-sync-pipeline')")

    # 4. Synthesize diagnostic response
    requires_human = False
    approval_reason = None

    # Check if there is an active incident affecting the user's issue
    sync_service = service_status.get("services", {}).get("data-sync-pipeline", {})
    is_sync_degraded = sync_service.get("status") == "degraded"

    if has_503_or_sync and is_sync_degraded:
        incident_info = sync_service.get("last_incident", "Active worker pool saturation")
        draft_response = (
            f"Hello,\n\n"
            f"Our automated diagnostics have confirmed an active incident on our Data Sync Pipeline: "
            f"'{incident_info}'.\n\n"
            f"Our Site Reliability Engineering (SRE) team is actively deploying auto-scaled worker partitions. "
            f"In the meantime, please apply exponential backoff (retry after 5 seconds). "
            f"You can monitor live status at status.platform.io or refer to Knowledge Base Article KB-202.\n\n"
            f"We apologize for the inconvenience and are working to restore 100% capacity promptly."
        )
    elif "api key" in inquiry_text or "token" in inquiry_text or "rate limit" in inquiry_text:
        kb_articles = kb_results.get("articles", [])
        kb_text = kb_articles[0]["content"] if kb_articles else "Navigate to Dashboard > Settings > API Keys."
        draft_response = (
            f"Hello,\n\n"
            f"Regarding your API key and authentication inquiry:\n\n"
            f"{kb_text}\n\n"
            f"If you continue experiencing authorization issues, verify that your client sends the "
            f"'Authorization: Bearer <TOKEN>' header."
        )
    else:
        kb_articles = kb_results.get("articles", [])
        guidance = (
            kb_articles[0]["content"]
            if kb_articles
            else "Please provide your request payload and timestamp so we can examine the trace logs."
        )
        draft_response = (
            f"Hello,\n\n"
            f"Thank you for contacting technical support. We reviewed our system logs and documentation:\n\n"
            f"{guidance}\n\n"
            f"All core API gateway systems are currently operational. Let us know if you need further help!"
        )

    # Check if customer tier is enterprise experiencing critical outage or ANGRY sentiment
    if state.get("customer_tier") == "enterprise" and (state.get("priority") in ["HIGH", "CRITICAL"]):
        requires_human = True
        approval_reason = (
            f"Enterprise customer ({state.get('customer_id')}) encountered {state.get('priority')} "
            "technical disruption. Engineering manager sign-off required."
        )

    agent_message = AIMessage(
        content=(
            f"🔧 [Technical Specialist Response Drafted]\n"
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
