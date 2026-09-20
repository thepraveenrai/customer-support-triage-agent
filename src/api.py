"""Production FastAPI REST API for Customer Support Triage Agent.

Exposes endpoints to:
1. Submit support tickets for automated multi-agent triage
2. Inspect checkpointed thread state for pending Human-in-the-Loop reviews
3. Submit human decisions (approve / edit / reject) to resume execution
4. Fetch architecture topology & Mermaid diagrams
"""

import uuid
from typing import Any, Dict, List, Literal, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.config import settings
from src.data_loader import get_dataset_analytics, get_ticket_by_id, load_tickets_csv
from src.graph import create_support_graph, get_mermaid_diagram
from src.state import PriorityLevel, SentimentLevel, TicketCategory, TriageState

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-grade Multi-Agent Customer Support Triage API powered by LangGraph. "
        "Demonstrates the Supervisor Pattern, specialist agents, and Human-in-the-Loop checkpointing."
    ),
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton compiled graph with in-memory checkpointer
support_graph = create_support_graph(interrupt_on_human_review=True)


# ==============================================================================
# Request & Response Schemas
# ==============================================================================

class TicketSubmissionRequest(BaseModel):
    """Payload to submit a new customer support ticket."""
    message: str = Field(..., description="Customer support message content or problem description.")
    customer_id: str = Field(default="CUST-001", description="Customer ID (e.g. CUST-001, CUST-002, CUST-004).")
    customer_email: Optional[str] = Field(default="customer@example.com", description="Customer contact email.")
    customer_tier: Literal["free", "pro", "enterprise"] = Field(default="pro", description="Customer subscription tier.")
    thread_id: Optional[str] = Field(default=None, description="Optional custom thread ID for checkpointing.")


class HumanReviewRequest(BaseModel):
    """Payload for Human-in-the-Loop manager decisions."""
    decision: Literal["approve", "reject", "edit"] = Field(
        ...,
        description="Human manager action: 'approve' draft as-is, 'edit' draft, or 'reject' action."
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Optional feedback or replacement response text when editing or rejecting."
    )


class TicketResponse(BaseModel):
    """Complete ticket status response."""
    thread_id: str
    ticket_id: str
    status: str
    category: Optional[TicketCategory] = None
    sentiment: Optional[SentimentLevel] = None
    priority: Optional[PriorityLevel] = None
    churn_risk: Optional[bool] = None
    specialist_assigned: Optional[str] = None
    requires_human_approval: bool
    approval_reason: Optional[str] = None
    draft_response: Optional[str] = None
    final_response: Optional[str] = None
    actions_taken: List[str] = []


class DatasetTicketResponse(BaseModel):
    """Schema for a ticket in the 1,000 enterprise dataset."""
    ticket_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    customer_company: str
    customer_tier: str
    channel: str
    subject: str
    message: str
    disputed_amount: Optional[float] = None
    expected_category: str
    expected_sentiment: str
    expected_priority: str
    churn_risk: bool
    expected_human_approval: bool
    timestamp: str


class DatasetListResponse(BaseModel):
    """Paginated list of dataset tickets."""
    total_in_batch: int
    offset: int
    limit: int
    tickets: List[DatasetTicketResponse]


# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/", tags=["System"])
def root():
    """System health check and metadata."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "model_name": settings.MODEL_NAME,
        "docs_url": "/docs",
        "status": "healthy",
    }


# ------------------------------------------------------------------------------
# 1,000 Enterprise Dataset Endpoints
# ------------------------------------------------------------------------------

@app.get("/api/dataset/stats", tags=["Enterprise Dataset"])
def get_dataset_stats():
    """Returns comprehensive statistical distribution of the 1,000 enterprise tickets."""
    try:
        return get_dataset_analytics()
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute dataset analytics: {err}",
        )


@app.get("/api/dataset/tickets", response_model=DatasetListResponse, tags=["Enterprise Dataset"])
def list_dataset_tickets(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    priority: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
):
    """Queries and filters tickets from the 1,000 enterprise dataset."""
    try:
        tickets = load_tickets_csv(
            limit=limit,
            offset=offset,
            category=category,
            sentiment=sentiment,
            priority=priority,
            tier=tier,
            search=search,
        )
        return DatasetListResponse(
            total_in_batch=len(tickets),
            offset=offset,
            limit=limit,
            tickets=[DatasetTicketResponse(**t) for t in tickets],
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query dataset: {err}",
        )


@app.get("/api/dataset/tickets/{ticket_id}", response_model=DatasetTicketResponse, tags=["Enterprise Dataset"])
def get_dataset_ticket(ticket_id: str):
    """Retrieves a single ticket by its ID (e.g. 'TIK-1042') from the 1,000 dataset."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found in the enterprise dataset.",
        )
    return DatasetTicketResponse(**ticket)


@app.post("/api/dataset/triage/{ticket_id}", response_model=TicketResponse, tags=["Enterprise Dataset"])
def triage_dataset_ticket(ticket_id: str, thread_id: Optional[str] = None):
    """Triages a specific ticket from the 1,000 enterprise dataset through the LangGraph multi-agent pipeline."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found in the enterprise dataset.",
        )

    assigned_thread_id = thread_id or f"th-{ticket_id.lower()}-{uuid.uuid4().hex[:6]}"

    initial_state: TriageState = {
        "messages": [HumanMessage(content=ticket["message"])],
        "ticket_id": ticket["ticket_id"],
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

    config = {"configurable": {"thread_id": assigned_thread_id}}

    try:
        support_graph.invoke(initial_state, config=config)
        snapshot = support_graph.get_state(config)
        values = snapshot.values

        return TicketResponse(
            thread_id=assigned_thread_id,
            ticket_id=ticket["ticket_id"],
            status=values.get("status", "open"),
            category=values.get("ticket_category"),
            sentiment=values.get("sentiment"),
            priority=values.get("priority"),
            churn_risk=values.get("churn_risk"),
            specialist_assigned=values.get("specialist_assigned"),
            requires_human_approval=values.get("requires_human_approval", False),
            approval_reason=values.get("approval_reason"),
            draft_response=values.get("draft_response"),
            final_response=values.get("final_response"),
            actions_taken=values.get("actions_taken", []),
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph execution failed for ticket '{ticket_id}': {err}",
        )


# ------------------------------------------------------------------------------
# Core Graph Execution & Checkpoint Endpoints
# ------------------------------------------------------------------------------

@app.post("/api/tickets/triage", response_model=TicketResponse, tags=["Support Tickets"])
def triage_ticket(payload: TicketSubmissionRequest):
    """Submit a custom customer support ticket for automated triage."""
    thread_id = payload.thread_id or f"th-{uuid.uuid4().hex[:8]}"
    ticket_id = f"TIK-{uuid.uuid4().hex[:6].upper()}"

    initial_state: TriageState = {
        "messages": [HumanMessage(content=payload.message)],
        "ticket_id": ticket_id,
        "customer_id": payload.customer_id,
        "customer_email": payload.customer_email or "unknown@customer.com",
        "customer_tier": payload.customer_tier,
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

    config = {"configurable": {"thread_id": thread_id}}

    try:
        support_graph.invoke(initial_state, config=config)
        snapshot = support_graph.get_state(config)
        values = snapshot.values

        return TicketResponse(
            thread_id=thread_id,
            ticket_id=ticket_id,
            status=values.get("status", "open"),
            category=values.get("ticket_category"),
            sentiment=values.get("sentiment"),
            priority=values.get("priority"),
            churn_risk=values.get("churn_risk"),
            specialist_assigned=values.get("specialist_assigned"),
            requires_human_approval=values.get("requires_human_approval", False),
            approval_reason=values.get("approval_reason"),
            draft_response=values.get("draft_response"),
            final_response=values.get("final_response"),
            actions_taken=values.get("actions_taken", []),
        )

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph execution failed: {err}",
        )


@app.get("/api/tickets/{thread_id}/state", tags=["Support Tickets"])
def get_ticket_state(thread_id: str):
    """Retrieve checkpointed state for an existing thread.

    Useful for support dashboards to check if a ticket is waiting for human review.
    """
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = support_graph.get_state(config)

    if not snapshot or not snapshot.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No state found for thread ID '{thread_id}'",
        )

    values = snapshot.values
    is_paused = snapshot.next == ("human_review",)

    return {
        "thread_id": thread_id,
        "is_paused_for_human_review": is_paused,
        "next_nodes": list(snapshot.next),
        "state": {
            "ticket_id": values.get("ticket_id"),
            "customer_id": values.get("customer_id"),
            "status": values.get("status"),
            "category": values.get("ticket_category"),
            "sentiment": values.get("sentiment"),
            "priority": values.get("priority"),
            "draft_response": values.get("draft_response"),
            "approval_reason": values.get("approval_reason"),
            "actions_taken": values.get("actions_taken", []),
            "final_response": values.get("final_response"),
        },
    }


@app.post("/api/tickets/{thread_id}/resume", response_model=TicketResponse, tags=["Support Tickets"])
def resume_ticket(thread_id: str, payload: HumanReviewRequest):
    """Submit human review decision ('approve', 'reject', 'edit') to resume execution."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = support_graph.get_state(config)

    if not snapshot or not snapshot.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread '{thread_id}' not found.",
        )

    if snapshot.next != ("human_review",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Thread '{thread_id}' is not currently paused at a human review checkpoint (Status: {snapshot.values.get('status')}).",
        )

    try:
        # Update checkpointed state with human manager's review
        support_graph.update_state(
            config,
            {
                "human_decision": payload.decision,
                "human_feedback": payload.feedback,
            },
            as_node=snapshot.values.get("specialist_assigned", "billing_specialist"),
        )

        # Resume execution
        resumed = support_graph.invoke(None, config=config)

        return TicketResponse(
            thread_id=thread_id,
            ticket_id=resumed.get("ticket_id", "N/A"),
            status=resumed.get("status", "resolved"),
            category=resumed.get("ticket_category"),
            sentiment=resumed.get("sentiment"),
            priority=resumed.get("priority"),
            churn_risk=resumed.get("churn_risk"),
            specialist_assigned=resumed.get("specialist_assigned"),
            requires_human_approval=resumed.get("requires_human_approval", False),
            approval_reason=resumed.get("approval_reason"),
            draft_response=resumed.get("draft_response"),
            final_response=resumed.get("final_response"),
            actions_taken=resumed.get("actions_taken", []),
        )

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume ticket: {err}",
        )


@app.get("/api/graph/diagram", tags=["System"])
def get_graph_diagram():
    """Returns the Mermaid graph representation of the triage architecture."""
    return {"mermaid": get_mermaid_diagram()}
