"""LLM provider and model factory for Customer Support Triage.

Provides seamless support for:
1. Live OpenAI models (via ChatOpenAI)
2. Resilient Mock Fallback Model for local testing and zero-cost demonstrations
   (ideal for students before they set up their API keys).
"""

import json
import re
from typing import Any, List, Optional
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
from src.config import settings


class MockChatSupportModel(BaseChatModel):
    """Deterministic, zero-dependency mock LLM for educational tests & demos.

    Simulates realistic LLM responses based on ticket keywords, enabling students
    to run the multi-agent graph offline without spending API credits or encountering
    auth errors.
    """

    model_name: str = "mock-support-v1"

    @property
    def _llm_type(self) -> str:
        return "mock-support"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Extract the latest user text
        user_texts = [m.content for m in messages if isinstance(m, HumanMessage) or m.type == "human"]
        full_text = " ".join(user_texts).lower() if user_texts else ""
        sys_texts = [m.content for m in messages if isinstance(m, SystemMessage) or m.type == "system"]
        prompt_context = " ".join(sys_texts).lower()

        # Check if Supervisor Router prompt is asking for JSON triage classification
        if "supervisor" in prompt_context or "triage" in prompt_context or "json" in prompt_context:
            result_json = self._simulate_supervisor_triage(full_text)
            generation = ChatGeneration(message=AIMessage(content=result_json))
            return ChatResult(generations=[generation])

        # Specialist agent responses
        response_text = self._simulate_specialist_response(prompt_context, full_text)
        generation = ChatGeneration(message=AIMessage(content=response_text))
        return ChatResult(generations=[generation])

    def _simulate_supervisor_triage(self, text: str) -> str:
        """Simulate Supervisor triage classification JSON."""
        # 1. Escalation conditions: VIP legal action, lawsuits, litigation, SLA breaches
        if any(w in text for w in ["lawyer", "lawsuit", "litigation", "sue", "breached our enterprise", "sla breach"]):
            sentiment = "ANGRY"
            priority = "CRITICAL"
            category = "escalation"
            churn_risk = True
            reasoning = "Customer threatened legal action / VIP escalation with extreme frustration."

        # 2. Billing conditions: refund, charge, invoice, subscription, cost, bill, cancel
        elif any(w in text for w in ["refund", "invoice", "charge", "charged", "billing", "bill", "subscription", "cancel"]):
            category = "billing"
            churn_risk = "cancel" in text or "leaving" in text
            if any(w in text for w in ["furious", "unacceptable", "steal", "scam", "fraud", "immediately"]):
                sentiment = "ANGRY"
                priority = "HIGH"
                reasoning = "Customer expressing strong dissatisfaction with billing or requesting immediate refund."
            elif "frustrated" in text or "annoyed" in text:
                sentiment = "FRUSTRATED"
                priority = "MEDIUM"
                reasoning = "Customer experienced billing discrepancy."
            else:
                sentiment = "NEUTRAL"
                priority = "LOW"
                reasoning = "Standard billing or invoice status inquiry."

        # 3. Technical conditions: error, 503, bug, crash, timeout, api, sync, fail
        elif any(w in text for w in ["503", "error", "bug", "crash", "down", "latency", "timeout", "sync", "api"]):
            category = "technical"
            churn_risk = False
            if "outage" in text or "production" in text or "503" in text:
                sentiment = "FRUSTRATED"
                priority = "HIGH"
                reasoning = "Customer experiencing critical service interruption or 503 API error."
            else:
                sentiment = "NEUTRAL"
                priority = "MEDIUM"
                reasoning = "Customer seeking technical troubleshooting assistance."

        # 4. Default fallback
        else:
            category = "technical"
            sentiment = "NEUTRAL"
            priority = "LOW"
            churn_risk = False
            reasoning = "General support inquiry routed to technical specialist for initial review."

        payload = {
            "category": category,
            "sentiment": sentiment,
            "priority": priority,
            "churn_risk": churn_risk,
            "reasoning": reasoning,
        }
        return json.dumps(payload, indent=2)

    def _simulate_specialist_response(self, prompt_context: str, user_text: str) -> str:
        """Simulate specialist response generation."""
        if "billing" in prompt_context:
            return (
                "I have thoroughly reviewed your account and invoice history. "
                "Regarding your request, our billing team has investigated the charge. "
                "If eligible for a refund, our automated policy processes claims within 3-5 business days."
            )
        elif "technical" in prompt_context:
            return (
                "Our diagnostic systems detected an active incident (INC-8821) on the data sync pipeline "
                "causing intermittent 503 Service Unavailable responses. SRE is deploying a hotfix. "
                "Please retry with exponential backoff, or consult Knowledge Base article KB-202."
            )
        elif "escalation" in prompt_context:
            return (
                "We recognize the critical severity of this issue and apologize for the disruption to your operations. "
                "Your account has been escalated directly to Senior Management and your Dedicated Account Lead. "
                "A human specialist is actively reviewing this ticket."
            )
        return "Thank you for reaching out. We are processing your request."


def get_llm():
    """Factory returning configured LLM instance.

    Supports:
    1. OpenRouter (OpenRouter API key with base_url https://openrouter.ai/api/v1)
    2. Direct OpenAI (OpenAI API key)
    3. MockChatSupportModel (zero-cost offline fallback for testing & demos)
    """
    # 1. OpenRouter Provider
    if settings.LLM_PROVIDER == "openrouter" and settings.OPENROUTER_API_KEY:
        try:
            from langchain_openai import ChatOpenAI

            headers = {
                "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER,
                "X-Title": settings.OPENROUTER_APP_NAME,
            }
            return ChatOpenAI(
                model=settings.MODEL_NAME,
                temperature=settings.MODEL_TEMPERATURE,
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
                default_headers=headers,
            )
        except Exception as err:
            print(f"[Warning] Failed to initialize OpenRouter ChatOpenAI ({err}). Falling back to MockChatSupportModel.")
            return MockChatSupportModel()

    # 2. Direct OpenAI Provider
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=settings.MODEL_NAME,
                temperature=settings.MODEL_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
            )
        except Exception as err:
            print(f"[Warning] Failed to initialize OpenAI ChatOpenAI ({err}). Falling back to MockChatSupportModel.")
            return MockChatSupportModel()

    # 3. Default Mock Fallback
    return MockChatSupportModel()
