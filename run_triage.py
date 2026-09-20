"""Interactive CLI Runner & Stress-Test Suite for Customer Support Triage Agent.

Features:
- Interactive Mode: Enter custom tickets live, observe routing and step through HITL approvals.
- Batch Mode: Stress-tests the graph across all 6 real-world messy support tickets.
- Diagram Mode: Inspect the LangGraph architecture and export Mermaid diagrams.
"""

import argparse
import sys
import uuid
from typing import Any, Dict

# Fix Windows console UTF-8 / charmap encoding issues
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from src.config import settings
from src.graph import create_support_graph, get_mermaid_diagram
from src.state import TriageState
from tests.test_tickets import SAMPLE_TICKETS

# Initialize rich console with safe fallback
console = Console(force_terminal=True, legacy_windows=False)


def print_banner():
    """Prints welcome banner with course context."""
    banner_text = Text()
    banner_text.append("LangGraph Multi-Agent Systems: Project 2\n", style="bold cyan")
    banner_text.append("Customer Support Triage Agent (Supervisor Pattern + Human-in-the-Loop)\n", style="bold green")
    banner_text.append(f"Model: {settings.MODEL_NAME} | Provider: {settings.LLM_PROVIDER.upper()}\n", style="dim white")
    banner_text.append("Business Rules: Refunds > $50 & Critical/Angry Sentiment require Human Review", style="italic yellow")
    console.print(Panel(banner_text, border_style="cyan"))


def execute_ticket(ticket: Dict[str, Any], interactive_hitl: bool = True) -> Dict[str, Any]:
    """Executes a single ticket through the support graph.

    If the ticket requires human approval, pauses at the checkpoint and either
    prompts the user (interactive) or applies auto-approval (batch).

    Args:
        ticket: Ticket dictionary with customer info and message.
        interactive_hitl: Whether to prompt for human approval or auto-approve in tests.

    Returns:
        Final graph state after completion.
    """
    thread_id = f"thread-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    graph = create_support_graph(interrupt_on_human_review=True)

    initial_state: TriageState = {
        "messages": [HumanMessage(content=ticket["message"])],
        "ticket_id": ticket.get("id", f"TIK-{uuid.uuid4().hex[:4].upper()}"),
        "customer_id": ticket.get("customer_id", "CUST-001"),
        "customer_email": ticket.get("customer_email", "customer@example.com"),
        "customer_tier": ticket.get("customer_tier", "pro"),
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

    console.print(f"\n[bold blue]📥 Ingesting Ticket {initial_state['ticket_id']}:[/bold blue] {ticket.get('name', 'Custom Ticket')}")
    console.print(f"[dim]Customer:[/dim] {initial_state['customer_id']} ({initial_state['customer_tier'].upper()} Tier)")
    console.print(f"[dim]Query:[/dim] \"{ticket['message']}\"\n")

    # Step 1: Run graph until completion or checkpoint interrupt
    with console.status("[cyan]Running Supervisor & Specialist Graph...", spinner="dots"):
        graph.invoke(initial_state, config=config)

    # Step 2: Check if graph halted before human_review
    state_snapshot = graph.get_state(config)

    if state_snapshot.next == ("human_review",):
        curr_state = state_snapshot.values
        console.print(Panel(
            f"[bold red]⚠️  HUMAN-IN-THE-LOOP CHECKPOINT TRIGGERED[/bold red]\n\n"
            f"[bold]Reason:[/bold] {curr_state.get('approval_reason')}\n"
            f"[bold]Category:[/bold] {curr_state.get('ticket_category', '').upper()} | "
            f"[bold]Sentiment:[/bold] {curr_state.get('sentiment')} | "
            f"[bold]Priority:[/bold] {curr_state.get('priority')}\n"
            f"[bold]Assigned Specialist:[/bold] {curr_state.get('specialist_assigned')}\n"
            f"[bold]Actions Taken:[/bold] {', '.join(curr_state.get('actions_taken', []))}\n\n"
            f"[bold cyan]Draft Response Prepared by Agent:[/bold cyan]\n"
            f"{curr_state.get('draft_response')}",
            title=f"🚨 Review Required for {initial_state['ticket_id']}",
            border_style="red",
        ))

        decision = "approve"
        feedback = None

        if interactive_hitl:
            console.print("\n[bold yellow]Manager Action Required:[/bold yellow]")
            choice = Prompt.ask(
                "Choose human decision",
                choices=["1", "2", "3"],
                default="1",
                show_choices=False,
                show_default=True,
            )
            console.print("[dim]Options: [1] Approve as-is | [2] Edit response | [3] Reject with feedback[/dim]")

            if choice == "1":
                decision = "approve"
                feedback = "Approved by Support Lead."
            elif choice == "2":
                decision = "edit"
                feedback = Prompt.ask("[bold]Enter replacement response message[/bold]")
            elif choice == "3":
                decision = "reject"
                feedback = Prompt.ask("[bold]Enter rejection reason for customer[/bold]", default="Policy compliance")
        else:
            # Automated mode for batch run
            decision = "approve"
            feedback = "Automated batch review approval."

        # Update checkpointed state with human input
        graph.update_state(
            config,
            {
                "human_decision": decision,
                "human_feedback": feedback,
            },
            as_node=curr_state.get("specialist_assigned", "billing_specialist"),
        )

        console.print(f"[green]Resuming graph execution with decision: '{decision.upper()}'...[/green]")
        # Resume execution by passing None
        resumed_state = graph.invoke(None, config=config)
        return resumed_state

    # Auto-resolved without human interruption
    final_values = state_snapshot.values
    return final_values


def run_batch_mode():
    """Runs all 6 real-world messy support tickets and prints formatted results table."""
    console.print("\n[bold cyan]🧪 RUNNING BATCH STRESS-TEST SUITE (6 Real-World Messy Tickets)[/bold cyan]")

    results = []
    for idx, ticket in enumerate(SAMPLE_TICKETS, start=1):
        console.rule(f"Stress-Test {idx}/6: {ticket['name']}")
        res = execute_ticket(ticket, interactive_hitl=False)
        results.append((ticket, res))

    # Print summary table
    table = Table(title="Support Triage Stress-Test Summary", border_style="cyan", show_header=True)
    table.add_column("Ticket ID", style="bold white")
    table.add_column("Scenario", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Sentiment", style="yellow")
    table.add_column("Priority", style="red")
    table.add_column("HITL Review?", style="bold")
    table.add_column("Status", style="green")

    for ticket, res in results:
        hitl_str = "[bold red]YES (Paused)[/bold red]" if res.get("requires_human_approval") else "[green]Auto-Resolved[/green]"
        table.add_row(
            res.get("ticket_id", "N/A"),
            ticket["name"],
            str(res.get("ticket_category", "")).upper(),
            str(res.get("sentiment", "")),
            str(res.get("priority", "")),
            hitl_str,
            str(res.get("status", "")).upper(),
        )

    console.print("\n")
    console.print(table)
    console.print("\n[bold green]✅ All 6 stress-test tickets evaluated successfully![/bold green]")


def run_interactive_mode():
    """Allows user to enter a custom support ticket and step through execution."""
    console.print("\n[bold green]💬 INTERACTIVE TICKET TRIAGE CONSOLE[/bold green]")
    console.print("Type your support ticket message below to observe routing, tools, and HITL in action.\n")

    while True:
        customer_id = Prompt.ask("[bold cyan]Customer ID[/bold cyan] (e.g. CUST-001, CUST-002, CUST-004)", default="CUST-001")
        customer_tier = Prompt.ask("[bold cyan]Customer Tier[/bold cyan] (free, pro, enterprise)", default="pro")
        message = Prompt.ask("[bold cyan]Support Ticket Message[/bold cyan]")

        if not message.strip():
            console.print("[red]Ticket message cannot be empty![/red]")
            continue

        ticket = {
            "id": f"TIK-{uuid.uuid4().hex[:4].upper()}",
            "name": "Live Interactive Ticket",
            "customer_id": customer_id,
            "customer_email": f"{customer_id.lower()}@customer.com",
            "customer_tier": customer_tier,
            "message": message,
        }

        final_state = execute_ticket(ticket, interactive_hitl=True)

        console.print(Panel(
            f"[bold green]Resolution Status:[/bold green] {final_state.get('status', '').upper()}\n"
            f"[bold green]Specialist:[/bold green] {final_state.get('specialist_assigned')}\n"
            f"[bold green]Tools Invoked:[/bold green] {', '.join(final_state.get('actions_taken', []))}\n\n"
            f"[bold white]Final Response Sent to Customer:[/bold white]\n"
            f"{final_state.get('final_response')}",
            title="📬 Final Delivered Customer Resolution",
            border_style="green",
        ))

        again = Prompt.ask("\nSubmit another ticket?", choices=["y", "n"], default="y")
        if again.lower() != "y":
            console.print("\n[cyan]Goodbye! Keep building multi-agent systems with LangGraph.[/cyan]")
            break


def run_diagram_mode():
    """Prints Mermaid graph and ASCII diagram."""
    console.print("\n[bold cyan]🗺️  LANGGRAPH ARCHITECTURE DIAGRAM[/bold cyan]")
    mermaid_code = get_mermaid_diagram()
    console.print(Panel(mermaid_code, title="Mermaid Flowchart", border_style="magenta"))

    ascii_art = """
   +-------------------------------------------------------------+
   |                  CUSTOMER TICKET INGESTION                  |
   +-------------------------------------------------------------+
                                 |
                                 v
   +-------------------------------------------------------------+
   |             SUPERVISOR & SENTIMENT ANALYZER                 |
   |   - Predicts category (Billing, Technical, Escalation)      |
   |   - Analyzes Sentiment (Positive, Neutral, Angry)           |
   |   - Evaluates Priority & Churn Risk                         |
   |   - Applies Sentiment-Based Priority Rule (Challenge)       |
   +-------------------------------------------------------------+
          /                      |                      \\
         / (billing)             | (technical)           \\ (escalation)
        v                        v                        v
+------------------+   +--------------------+   +-------------------+
| BILLING SPECIALIST|  | TECH SPECIALIST    |   | ESCALATION AGENT  |
| - Check invoices |   | - Check telemetry  |   | - VIP accounts    |
| - Execute refund |   | - Query KB & logs  |   | - Lawsuit threats |
+------------------+   +--------------------+   +-------------------+
        \\                        |                        /
         \\ (if refund > $50)     | (if enterprise outage)| (always)
          +----------------------+-----------------------+
                                 |
                                 v
   +-------------------------------------------------------------+
   |               HUMAN-IN-THE-LOOP CHECKPOINT                  |
   |   - Execution paused before human_review node               |
   |   - Thread state saved in MemorySaver checkpointer          |
   |   - Human Manager: [Approve] | [Edit] | [Reject]            |
   +-------------------------------------------------------------+
                                 |
                                 v
   +-------------------------------------------------------------+
   |                  FINAL RESPONSE DELIVERED                   |
   +-------------------------------------------------------------+
    """
    console.print(ascii_art)


def run_stats_mode(csv_path: str = None):
    """Displays rich analytics dashboard for the 1,000-ticket dataset."""
    from src.data_loader import get_dataset_analytics, DEFAULT_CSV_PATH

    path = csv_path or DEFAULT_CSV_PATH
    stats = get_dataset_analytics(path)

    console.print("\n[bold cyan]📊 1,000 ENTERPRISE TICKET DATASET ANALYTICS[/bold cyan]")
    console.print(f"[dim]Dataset Path: {path}[/dim]\n")

    # Overview Table
    overview_table = Table(title="Dataset Key Metrics", border_style="cyan")
    overview_table.add_column("Metric", style="bold white")
    overview_table.add_column("Value", style="bold green")

    overview_table.add_row("Total Ingested Tickets", str(stats["total_tickets"]))
    overview_table.add_row("Human Review Checkpoints Needed", f"{stats['human_review_required_count']} ({stats['human_review_pct']}%)")
    overview_table.add_row("Customer Churn Risks Flagged", f"{stats['churn_risk_count']} ({stats['churn_risk_pct']}%)")
    overview_table.add_row("Total Disputed Amount", f"${stats['total_disputed_amount_sum']:,.2f}")
    overview_table.add_row("Average Dispute Amount", f"${stats['average_disputed_amount']:,.2f}")
    console.print(overview_table)

    # Breakdown Tables Grid
    grid_table = Table.grid(padding=1)
    grid_table.add_column()
    grid_table.add_column()

    cat_table = Table(title="Category Distribution", border_style="blue")
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Count", justify="right")
    for cat, count in stats["categories"].items():
        cat_table.add_row(cat.capitalize(), str(count))

    sent_table = Table(title="Sentiment Breakdown", border_style="magenta")
    sent_table.add_column("Sentiment", style="magenta")
    sent_table.add_column("Count", justify="right")
    for sent, count in stats["sentiments"].items():
        sent_table.add_row(sent, str(count))

    tier_table = Table(title="Customer Tiers", border_style="green")
    tier_table.add_column("Tier", style="green")
    tier_table.add_column("Count", justify="right")
    for tier, count in stats["tiers"].items():
        tier_table.add_row(tier.upper(), str(count))

    prio_table = Table(title="Priority Levels", border_style="yellow")
    prio_table.add_column("Priority", style="yellow")
    prio_table.add_column("Count", justify="right")
    for prio, count in stats["priorities"].items():
        prio_table.add_row(prio, str(count))

    console.print("\n")
    console.print(cat_table)
    console.print(sent_table)
    console.print(tier_table)
    console.print(prio_table)


def run_dataset_mode(csv_path: str = None, limit: int = 5, ticket_id: str = None):
    """Executes tickets loaded from the 1,000 enterprise dataset."""
    from src.data_loader import load_tickets_csv, get_ticket_by_id, DEFAULT_CSV_PATH

    path = csv_path or DEFAULT_CSV_PATH

    if ticket_id:
        target = get_ticket_by_id(ticket_id, csv_path=path)
        if not target:
            console.print(f"[bold red]Ticket ID '{ticket_id}' not found in dataset: {path}[/bold red]")
            return
        tickets_to_run = [target]
    else:
        tickets_to_run = load_tickets_csv(csv_path=path, limit=limit)

    console.print(f"\n[bold cyan]🚀 EXECUTING {len(tickets_to_run)} TICKETS FROM ENTERPRISE DATASET[/bold cyan]")
    console.print(f"[dim]Source: {path}[/dim]\n")

    summary_table = Table(
        title="Execution Results Summary",
        border_style="cyan",
        header_style="bold cyan",
    )
    summary_table.add_column("Ticket ID", style="bold white")
    summary_table.add_column("Customer", style="dim white")
    summary_table.add_column("Category", style="blue")
    summary_table.add_column("Sentiment", style="yellow")
    summary_table.add_column("Priority", style="red")
    summary_table.add_column("HITL?", justify="center")
    summary_table.add_column("Status", style="green")

    for i, t in enumerate(tickets_to_run, 1):
        console.print(f"\n[bold yellow]─── Running Ticket {i}/{len(tickets_to_run)}: {t['id']} ───[/bold yellow]")
        final_state = execute_ticket(t, interactive_hitl=False)

        hitl_marker = "[bold red]YES[/bold red]" if final_state.get("requires_human_approval") else "[green]NO[/green]"
        summary_table.add_row(
            t["id"],
            f"{t['customer_id']} ({t['customer_tier'].upper()})",
            final_state.get("ticket_category", "N/A"),
            final_state.get("sentiment", "N/A"),
            final_state.get("priority", "N/A"),
            hitl_marker,
            final_state.get("status", "N/A").upper(),
        )

    console.print("\n")
    console.print(summary_table)


def main():
    parser = argparse.ArgumentParser(description="Customer Support Triage Multi-Agent System CLI")
    parser.add_argument(
        "--mode",
        choices=["batch", "interactive", "diagram", "dataset", "stats"],
        default="batch",
        help="Run mode: 'batch' (stress-test 6 tickets), 'dataset' (run from 1000 CSV), 'stats' (dataset analytics), 'interactive' (live tickets), 'diagram' (view graph flow)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of tickets to execute when in 'dataset' mode (default: 5)",
    )
    parser.add_argument(
        "--ticket",
        type=str,
        default=None,
        help="Specific ticket ID to execute from dataset (e.g. 'TIK-1042')",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Custom path to tickets CSV dataset",
    )
    args = parser.parse_args()

    print_banner()

    if args.mode == "batch":
        run_batch_mode()
    elif args.mode == "interactive":
        run_interactive_mode()
    elif args.mode == "diagram":
        run_diagram_mode()
    elif args.mode == "stats":
        run_stats_mode(csv_path=args.csv)
    elif args.mode == "dataset":
        run_dataset_mode(csv_path=args.csv, limit=args.limit, ticket_id=args.ticket)


if __name__ == "__main__":
    main()

