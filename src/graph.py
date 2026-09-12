"""Customer Support Triage Multi-Agent Graph Architecture.

This module constructs the LangGraph StateGraph, registers nodes, connects
conditional routing edges from the Supervisor, and sets up checkpointing
with Human-in-the-Loop interrupts.
"""

from typing import Any, Dict, Literal, Optional
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.billing_agent import billing_agent_node
from src.agents.escalation_agent import escalation_agent_node
from src.agents.human_review import human_review_node
from src.agents.supervisor import supervisor_node
from src.agents.tech_agent import tech_agent_node
from src.state import TriageState


# ==============================================================================
# 1. Finalizing Node for Auto-Resolved Tickets
# ==============================================================================

def auto_resolver_node(state: TriageState) -> Dict[str, Any]:
    """Finalizes tickets that do NOT require human review."""
    draft = state.get("draft_response", "Your inquiry has been processed.")
    return {
        "final_response": draft,
        "status": "resolved",
        "requires_human_approval": False,
    }


# ==============================================================================
# 2. Conditional Edge Routing Functions
# ==============================================================================

def route_from_supervisor(
    state: TriageState,
) -> Literal["billing_specialist", "technical_specialist", "escalation_specialist"]:
    """Conditional Edge: Inspects Supervisor's classification and routes to specialist.

    Args:
        state: The current TriageState populated by supervisor_node.

    Returns:
        The target node name.
    """
    category = state.get("ticket_category", "technical")

    if category == "billing":
        return "billing_specialist"
    elif category == "escalation":
        return "escalation_specialist"
    else:
        return "technical_specialist"


def route_from_specialist(
    state: TriageState,
) -> Literal["human_review", "auto_resolver"]:
    """Conditional Edge: Checks if human review checkpoint is required.

    Args:
        state: State populated by specialist agent.

    Returns:
        'human_review' if approval is flagged, otherwise 'auto_resolver'.
    """
    if state.get("requires_human_approval", False):
        return "human_review"
    return "auto_resolver"


# ==============================================================================
# 3. Graph Builder Factory
# ==============================================================================

def create_support_graph(
    checkpointer: Optional[Any] = None,
    interrupt_on_human_review: bool = True,
):
    """Builds and compiles the Customer Support Triage StateGraph.

    Args:
        checkpointer: LangGraph checkpoint saver (defaults to MemorySaver()).
                      Persists state across threads for Human-in-the-Loop resumption.
        interrupt_on_human_review: If True, pauses graph execution right before
                                   entering the 'human_review' node.

    Returns:
        Compiled LangGraph instance ready for invocation.
    """
    # 1. Initialize StateGraph with our typed state schema
    builder = StateGraph(TriageState)

    # 2. Register all agent and processing nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("billing_specialist", billing_agent_node)
    builder.add_node("technical_specialist", tech_agent_node)
    builder.add_node("escalation_specialist", escalation_agent_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("auto_resolver", auto_resolver_node)

    # 3. Define Graph Edges & Flow
    # Every ticket enters at the Supervisor
    builder.add_edge(START, "supervisor")

    # Supervisor conditionally routes to one of three specialists
    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "billing_specialist": "billing_specialist",
            "technical_specialist": "technical_specialist",
            "escalation_specialist": "escalation_specialist",
        },
    )

    # Specialists conditionally route to either human_review or auto_resolver
    for specialist in ["billing_specialist", "technical_specialist", "escalation_specialist"]:
        builder.add_conditional_edges(
            specialist,
            route_from_specialist,
            {
                "human_review": "human_review",
                "auto_resolver": "auto_resolver",
            },
        )

    # Both terminating branches route to END
    builder.add_edge("auto_resolver", END)
    builder.add_edge("human_review", END)

    # 4. Attach Checkpointer (MemorySaver) and Interrupt settings
    saver = checkpointer if checkpointer is not None else MemorySaver()
    interrupts = ["human_review"] if interrupt_on_human_review else []

    graph = builder.compile(
        checkpointer=saver,
        interrupt_before=interrupts,
    )

    return graph


def get_mermaid_diagram() -> str:
    """Returns Mermaid markdown string of the support graph for course documentation."""
    graph = create_support_graph(interrupt_on_human_review=False)
    try:
        return graph.get_graph().draw_mermaid()
    except Exception:
        return """
graph TD
    START --> supervisor
    supervisor -->|billing| billing_specialist
    supervisor -->|technical| technical_specialist
    supervisor -->|escalation| escalation_specialist
    billing_specialist -->|needs approval| human_review
    billing_specialist -->|resolved| auto_resolver
    technical_specialist -->|needs approval| human_review
    technical_specialist -->|resolved| auto_resolver
    escalation_specialist -->|needs approval| human_review
    auto_resolver --> END
    human_review --> END
"""
