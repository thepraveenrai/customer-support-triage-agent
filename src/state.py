"""State definitions for the Customer Support Triage Multi-Agent System.

In LangGraph, 'State' is the single source of truth passed between nodes.
Every node receives the current state, performs logic/tool calls, and returns
a dictionary of keys to update in the state.
"""

from typing import Annotated, Any, Dict, List, Literal, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# Allowed triage categories routed by the Supervisor
TicketCategory = Literal["billing", "technical", "escalation", "general"]

# Customer sentiment classification
SentimentLevel = Literal["POSITIVE", "NEUTRAL", "FRUSTRATED", "ANGRY"]

# Ticket urgency/priority classification
PriorityLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Human-in-the-loop decision status
HumanDecision = Literal["pending", "approve", "reject", "edit"]

# Overall ticket resolution lifecycle status
TicketStatus = Literal[
    "open",
    "triaged",
    "in_progress",
    "pending_human_review",
    "resolved",
    "escalated",
]


class TriageState(TypedDict):
    """The complete shared state schema for the customer support graph.

    Attributes:
        messages: Conversation history between the customer and agents.
                  The `add_messages` reducer automatically appends new messages
                  rather than overwriting previous ones.
        ticket_id: Unique support ticket identifier (e.g. TIK-1042).
        customer_id: Identifier of the customer submitting the ticket.
        customer_email: Customer contact email.
        customer_tier: Subscription tier ('free', 'pro', 'enterprise').
        ticket_category: Category assigned by the Supervisor router.
        sentiment: Sentiment extracted from the user's inquiry.
        priority: Computed urgency priority level.
        churn_risk: Flag if customer is threatening to leave or cancel.
        triage_reasoning: Rationale provided by the Supervisor for routing.
        specialist_assigned: Which specialist agent processed the ticket.
        draft_response: The response or resolution drafted by the specialist.
        actions_taken: History of diagnostic or financial tools invoked.
        requires_human_approval: Boolean flag triggering the HITL checkpoint.
        approval_reason: Clear justification of why human review is required.
        human_decision: Human manager's decision ('approve', 'reject', 'edit').
        human_feedback: Human manager's notes or edited response text.
        final_response: The final message delivered to the customer.
        status: The current workflow status of the ticket.
    """

    # 1. Message history with LangGraph's standard `add_messages` reducer
    messages: Annotated[List[BaseMessage], add_messages]

    # 2. Ticket & Customer Metadata
    ticket_id: str
    customer_id: str
    customer_email: str
    customer_tier: str

    # 3. Supervisor Triage & Sentiment Analysis (Trophy Challenge)
    ticket_category: Optional[TicketCategory]
    sentiment: Optional[SentimentLevel]
    priority: Optional[PriorityLevel]
    churn_risk: Optional[bool]
    triage_reasoning: Optional[str]

    # 4. Specialist Execution & Tool Outcomes
    specialist_assigned: Optional[str]
    draft_response: Optional[str]
    actions_taken: List[str]

    # 5. Human-in-the-Loop (HITL) Checkpoint State
    requires_human_approval: bool
    approval_reason: Optional[str]
    human_decision: Optional[HumanDecision]
    human_feedback: Optional[str]

    # 6. Final Delivery
    final_response: Optional[str]
    status: TicketStatus
