"""Pytest test suite for LangGraph Customer Support Triage System.

Verifies:
1. Supervisor routing accuracy across categories
2. Trophy Challenge: Sentiment-Based Priority Rule engine
3. Specialist agent tool execution (CRM, invoices, telemetry)
4. Human-in-the-Loop checkpointing with MemorySaver
5. State resumption with manager approval, rejection, and edits
"""

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from src.agents.supervisor import apply_sentiment_priority_rules
from src.graph import create_support_graph
from src.state import TriageState
from tests.test_tickets import SAMPLE_TICKETS


def test_supervisor_sentiment_priority_challenge_rule():
    """Verify Trophy Challenge: Sentiment-based Priority Rule logic."""
    # Case 1: Angry customer threatening lawsuit
    cat, prio, note = apply_sentiment_priority_rules(
        category="billing",
        sentiment="ANGRY",
        priority="HIGH",
        churn_risk=True,
        user_text="I am going to sue you with my lawyer",
    )
    assert cat == "escalation", "Angry lawsuit threat should auto-escalate"
    assert prio == "CRITICAL", "Angry lawsuit threat should be CRITICAL priority"
    assert "auto-escalation" in note

    # Case 2: Frustrated billing inquiry
    cat2, prio2, note2 = apply_sentiment_priority_rules(
        category="billing",
        sentiment="FRUSTRATED",
        priority="LOW",
        churn_risk=False,
        user_text="My bill had an extra charge and I am frustrated",
    )
    assert cat2 == "billing"
    assert prio2 == "HIGH", "Billing dispute with frustration should be bumped to HIGH"

    # Case 3: Calm standard inquiry
    cat3, prio3, _ = apply_sentiment_priority_rules(
        category="technical",
        sentiment="NEUTRAL",
        priority="LOW",
        churn_risk=False,
        user_text="How do I get an API key?",
    )
    assert cat3 == "technical"
    assert prio3 == "LOW"


def test_calm_billing_auto_resolve_flow():
    """Verify Ticket 1: Calm billing query routes to billing and auto-resolves without human halt."""
    ticket = SAMPLE_TICKETS[0]
    graph = create_support_graph(interrupt_on_human_review=True)

    initial_state: TriageState = {
        "messages": [HumanMessage(content=ticket["message"])],
        "ticket_id": ticket["id"],
        "customer_id": ticket["customer_id"],
        "customer_email": ticket["customer_email"],
        "customer_tier": ticket["customer_tier"],
        "ticket_category": None,
        "sentiment": None,
        "priority": None,
        "churn_risk": None,
        "triage_reasoning": None,
        "specialist_assigned": None,
        "draft_response": None,
        "actions_taken": [],
        "requires_human_approval": False,
        "approval_reason": None,
        "human_decision": None,
        "human_feedback": None,
        "final_response": None,
        "status": "open",
    }

    config = {"configurable": {"thread_id": "test-thread-001"}}
    final_state = graph.invoke(initial_state, config=config)

    assert final_state["ticket_category"] == "billing"
    assert final_state["sentiment"] in ("NEUTRAL", "POSITIVE")
    assert final_state["status"] == "resolved"
    assert final_state["requires_human_approval"] is False
    assert final_state["final_response"] is not None
    assert len(final_state["actions_taken"]) >= 2


def test_high_refund_triggers_hitl_checkpoint_and_resumes():
    """Verify Ticket 2: $250 refund halts at human_review, persists checkpoint, and resumes."""
    ticket = SAMPLE_TICKETS[1]  # Furious customer requesting $250 refund
    saver = MemorySaver()
    graph = create_support_graph(checkpointer=saver, interrupt_on_human_review=True)

    initial_state: TriageState = {
        "messages": [HumanMessage(content=ticket["message"])],
        "ticket_id": ticket["id"],
        "customer_id": ticket["customer_id"],
        "customer_email": ticket["customer_email"],
        "customer_tier": ticket["customer_tier"],
        "ticket_category": None,
        "sentiment": None,
        "priority": None,
        "churn_risk": None,
        "triage_reasoning": None,
        "specialist_assigned": None,
        "draft_response": None,
        "actions_taken": [],
        "requires_human_approval": False,
        "approval_reason": None,
        "human_decision": None,
        "human_feedback": None,
        "final_response": None,
        "status": "open",
    }

    thread_id = "test-thread-hitl-002"
    config = {"configurable": {"thread_id": thread_id}}

    # 1. Run graph - it should pause at human_review checkpoint
    paused_state = graph.invoke(initial_state, config=config)

    # Inspect paused state at the boundary
    current_snapshot = graph.get_state(config)
    assert current_snapshot.next == ("human_review",), (
        f"Graph should be paused right before human_review! Found next: {current_snapshot.next}"
    )

    state_values = current_snapshot.values
    assert state_values["requires_human_approval"] is True
    assert state_values["status"] == "pending_human_review"
    assert "exceeds" in state_values["approval_reason"].lower() or "angry" in state_values["approval_reason"].lower()

    # 2. Simulate Human Manager reviewing and approving the request
    graph.update_state(
        config,
        {
            "human_decision": "approve",
            "human_feedback": "Authorized by Finance Director Dave.",
        },
        as_node="billing_specialist",
    )

    # 3. Resume the graph from the checkpoint
    resumed_state = graph.invoke(None, config=config)

    assert resumed_state["status"] == "resolved"
    assert resumed_state["human_decision"] == "approve"
    assert resumed_state["final_response"] is not None
    assert "refund" in resumed_state["final_response"].lower()


def test_hitl_manager_edit_flow():
    """Verify Human Manager can customize/edit the response before sending."""
    ticket = SAMPLE_TICKETS[3]  # VIP Escalation
    saver = MemorySaver()
    graph = create_support_graph(checkpointer=saver, interrupt_on_human_review=True)

    initial_state: TriageState = {
        "messages": [HumanMessage(content=ticket["message"])],
        "ticket_id": ticket["id"],
        "customer_id": ticket["customer_id"],
        "customer_email": ticket["customer_email"],
        "customer_tier": ticket["customer_tier"],
        "ticket_category": None,
        "sentiment": None,
        "priority": None,
        "churn_risk": None,
        "triage_reasoning": None,
        "specialist_assigned": None,
        "draft_response": None,
        "actions_taken": [],
        "requires_human_approval": False,
        "approval_reason": None,
        "human_decision": None,
        "human_feedback": None,
        "final_response": None,
        "status": "open",
    }

    thread_id = "test-thread-edit-003"
    config = {"configurable": {"thread_id": thread_id}}

    graph.invoke(initial_state, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.next == ("human_review",)

    # Manager provides a custom edited message
    custom_message = (
        "Dear Bob, this is VP of Engineering Mark. I am personally jumping on a call "
        "with you right now at 1-800-555-0199. Our team has already stabilized your cluster."
    )

    graph.update_state(
        config,
        {
            "human_decision": "edit",
            "human_feedback": custom_message,
        },
        as_node="escalation_specialist",
    )

    resumed_state = graph.invoke(None, config=config)
    assert resumed_state["status"] == "resolved"
    assert resumed_state["final_response"] == custom_message
    assert resumed_state["human_decision"] == "edit"


def test_hitl_manager_reject_flow():
    """Verify Human Manager can reject a draft and supply a reason."""
    ticket = SAMPLE_TICKETS[1]  # High refund dispute
    saver = MemorySaver()
    graph = create_support_graph(checkpointer=saver, interrupt_on_human_review=True)

    initial_state: TriageState = {
        "messages": [HumanMessage(content=ticket["message"])],
        "ticket_id": ticket["id"],
        "customer_id": ticket["customer_id"],
        "customer_email": ticket["customer_email"],
        "customer_tier": ticket["customer_tier"],
        "ticket_category": None,
        "sentiment": None,
        "priority": None,
        "churn_risk": None,
        "triage_reasoning": None,
        "specialist_assigned": None,
        "draft_response": None,
        "actions_taken": [],
        "requires_human_approval": False,
        "approval_reason": None,
        "human_decision": None,
        "human_feedback": None,
        "final_response": None,
        "status": "open",
    }

    thread_id = "test-thread-reject-005"
    config = {"configurable": {"thread_id": thread_id}}

    graph.invoke(initial_state, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.next == ("human_review",)

    graph.update_state(
        config,
        {
            "human_decision": "reject",
            "human_feedback": "Charge verified as legitimate compute usage. Refund rejected per terms.",
        },
        as_node="billing_specialist",
    )

    resumed_state = graph.invoke(None, config=config)
    assert resumed_state["status"] == "resolved"
    assert resumed_state["human_decision"] == "reject"
    assert "unable to approve" in resumed_state["final_response"].lower()
    assert "legitimate compute usage" in resumed_state["final_response"]


def test_technical_503_outage_diagnostic_flow():
    """Verify Ticket 3: 503 outage fetches diagnostic telemetry and provides incident steps."""
    ticket = SAMPLE_TICKETS[2]
    graph = create_support_graph(interrupt_on_human_review=False)

    initial_state: TriageState = {
        "messages": [HumanMessage(content=ticket["message"])],
        "ticket_id": ticket["id"],
        "customer_id": ticket["customer_id"],
        "customer_email": ticket["customer_email"],
        "customer_tier": ticket["customer_tier"],
        "ticket_category": None,
        "sentiment": None,
        "priority": None,
        "churn_risk": None,
        "triage_reasoning": None,
        "specialist_assigned": None,
        "draft_response": None,
        "actions_taken": [],
        "requires_human_approval": False,
        "approval_reason": None,
        "human_decision": None,
        "human_feedback": None,
        "final_response": None,
        "status": "open",
    }

    config = {"configurable": {"thread_id": "test-thread-tech-004"}}
    res = graph.invoke(initial_state, config=config)

    assert res["ticket_category"] == "technical"
    assert res["specialist_assigned"] == "technical_specialist"
    assert "check_system_service_status()" in res["actions_taken"]
    assert "fetch_system_logs(service='data-sync-pipeline')" in res["actions_taken"]
    assert "INC-8821" in res["final_response"] or "503" in res["final_response"]
