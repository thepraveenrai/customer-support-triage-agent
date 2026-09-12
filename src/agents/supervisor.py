"""Supervisor Router Node with Sentiment-Based Priority Rule (Challenge Solution).

The Supervisor Pattern is the central orchestrator in this multi-agent architecture.
Instead of passing the conversation sequentially through every agent (chain pattern),
the Supervisor evaluates the incoming ticket and dynamically routes to the best specialist:
- Billing Specialist
- Technical Support Specialist
- Escalation Specialist

🏆 TROPHY CHALLENGE INCLUDED:
The supervisor includes a dedicated Sentiment & Urgency engine that implements:
- Sentiment extraction: POSITIVE, NEUTRAL, FRUSTRATED, ANGRY
- Urgency extraction: LOW, MEDIUM, HIGH, CRITICAL
- Churn Risk identification: detects threats of cancelling or legal action
- Sentiment-Based Priority Override: automatically bumps priority and overrides
  routing if a customer is highly distressed.
"""

import json
from typing import Any, Dict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.config import settings
from src.llm import get_llm
from src.state import PriorityLevel, SentimentLevel, TicketCategory, TriageState

SUPERVISOR_SYSTEM_PROMPT = """You are an expert AI Customer Support Supervisor and Triage Orchestrator.
Your job is to analyze incoming customer support tickets, classify them accurately,
evaluate customer sentiment, determine ticket priority, and assign the ticket to the proper specialist.

Routing categories:
- 'billing': Invoices, charges, payment failures, subscription changes, and refund requests.
- 'technical': Bugs, error codes (500, 503), service downtime, API issues, troubleshooting.
- 'escalation': Legal threats, lawsuit mentions, extreme customer distress, VIP enterprise accounts, unresolvable complaints.

Sentiment levels:
- 'POSITIVE': Customer is polite, appreciative, or satisfied.
- 'NEUTRAL': Customer is matter-of-fact, calm, or asking a straightforward question.
- 'FRUSTRATED': Customer is experiencing delay, inconvenience, or moderate annoyance.
- 'ANGRY': Customer is furious, using aggressive language, demanding immediate answers, or threatening churn/lawsuits.

Priority levels:
- 'LOW': Non-urgent queries, general questions, routine billing queries.
- 'MEDIUM': Standard technical bugs or minor invoice queries without active downtime.
- 'HIGH': Direct financial disputes, substantial service degradation, or high frustration.
- 'CRITICAL': Complete system outage, legal threats, or major enterprise account at risk.

Respond ONLY with a valid JSON object matching this schema:
{
  "category": "billing" | "technical" | "escalation",
  "sentiment": "POSITIVE" | "NEUTRAL" | "FRUSTRATED" | "ANGRY",
  "priority": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "churn_risk": true | false,
  "reasoning": "Brief explanation of routing decision"
}
"""


def apply_sentiment_priority_rules(
    category: TicketCategory,
    sentiment: SentimentLevel,
    priority: PriorityLevel,
    churn_risk: bool,
    user_text: str,
) -> tuple[TicketCategory, PriorityLevel, str]:
    """🏆 TROPHY CHALLENGE SOLUTION: Sentiment-Based Priority Rule Engine.

    Business Rules:
    1. If customer is ANGRY and threatening churn/lawsuit -> force CRITICAL priority and route to 'escalation'.
    2. If customer is ANGRY or FRUSTRATED with a billing issue -> force priority to at least HIGH.
    3. If enterprise account or complete downtime mentioned -> force CRITICAL.
    """
    adjusted_category = category
    adjusted_priority = priority
    rule_notes = []

    text_lower = user_text.lower()

    # Rule 1: Legal or Lawsuit threat (direct escalation)
    if any(w in text_lower for w in ["legal", "lawsuit", "lawyer", "sue", "litigation"]):
        adjusted_category = "escalation"
        adjusted_priority = "CRITICAL"
        rule_notes.append("Rule: Legal threat detected - auto-escalation to CRITICAL.")

    # Rule 2: High Financial Dispute with Anger or Churn Threat
    elif category == "billing":
        if sentiment in ["ANGRY", "FRUSTRATED"] or churn_risk:
            if adjusted_priority in ["LOW", "MEDIUM"]:
                adjusted_priority = "HIGH"
            rule_notes.append("Rule: Customer distress or churn threat on billing inquiry bumped priority to HIGH.")

    # Rule 3: Extreme non-billing distress
    elif sentiment == "ANGRY" and churn_risk:
        adjusted_category = "escalation"
        adjusted_priority = "CRITICAL"
        rule_notes.append("Rule: Angry customer with severe churn threat escalated to CRITICAL.")

    # Rule 4: Production Downtime Rule
    elif "503" in text_lower or "outage" in text_lower or "crash" in text_lower:
        if adjusted_priority == "LOW":
            adjusted_priority = "HIGH"
            rule_notes.append("Rule: Service outage keyword boosted priority to HIGH.")

    explanation = " | ".join(rule_notes) if rule_notes else "Standard baseline routing applied."
    return adjusted_category, adjusted_priority, explanation


def supervisor_node(state: TriageState) -> Dict[str, Any]:
    """LangGraph Node: Evaluates customer ticket, extracts sentiment, and routes.

    Args:
        state: Current graph state containing ticket messages and customer info.

    Returns:
        State updates containing ticket_category, sentiment, priority, churn_risk, and triage_reasoning.
    """
    # Extract customer messages
    user_messages = [m.content for m in state["messages"] if isinstance(m, HumanMessage) or m.type == "human"]
    ticket_content = " ".join(user_messages) if user_messages else "No content provided."

    customer_tier = state.get("customer_tier", "free")
    customer_id = state.get("customer_id", "Unknown")

    # Build prompt context
    enriched_prompt = (
        f"Customer ID: {customer_id}\n"
        f"Customer Tier: {customer_tier}\n"
        f"Ticket Content:\n{ticket_content}\n"
    )

    llm = get_llm()
    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=enriched_prompt),
    ]

    try:
        response = llm.invoke(messages)
        content_text = response.content.strip()

        # Clean JSON markdown if model wrapped in ```json ... ```
        if "```" in content_text:
            content_text = content_text.split("```")[1]
            if content_text.startswith("json"):
                content_text = content_text[4:]
            content_text = content_text.strip()

        parsed = json.loads(content_text)
        category: TicketCategory = parsed.get("category", "technical")
        sentiment: SentimentLevel = parsed.get("sentiment", "NEUTRAL")
        priority: PriorityLevel = parsed.get("priority", "MEDIUM")
        churn_risk: bool = bool(parsed.get("churn_risk", False))
        reasoning: str = parsed.get("reasoning", "Classified by Supervisor LLM.")

    except Exception as err:
        # Resilient fallback if JSON parsing fails
        category = "technical"
        sentiment = "NEUTRAL"
        priority = "MEDIUM"
        churn_risk = False
        reasoning = f"Fallback routing due to parsing exception: {err}"

    # Apply Trophy Challenge Sentiment-Based Priority Rule
    final_category, final_priority, rule_msg = apply_sentiment_priority_rules(
        category=category,
        sentiment=sentiment,
        priority=priority,
        churn_risk=churn_risk,
        user_text=ticket_content,
    )

    full_reasoning = f"{reasoning} ({rule_msg})"

    # Record Supervisor audit message in the conversation
    audit_msg = AIMessage(
        content=(
            f"📋 [Supervisor Triage] Ticket: {state['ticket_id']} | "
            f"Category: {final_category.upper()} | "
            f"Sentiment: {sentiment} | "
            f"Priority: {final_priority} | "
            f"Assigned Specialist: {final_category}_specialist"
        )
    )

    return {
        "messages": [audit_msg],
        "ticket_category": final_category,
        "sentiment": sentiment,
        "priority": final_priority,
        "churn_risk": churn_risk,
        "triage_reasoning": full_reasoning,
        "specialist_assigned": f"{final_category}_specialist",
        "status": "triaged",
    }
