"""Technical and diagnostic tools for the Technical Support Specialist Agent.

Provides capabilities to check service status, inspect live error logs,
and search technical troubleshooting documentation.
"""

from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from src.crm_store import KNOWLEDGE_BASE, MOCK_SYSTEM_LOGS, SYSTEM_STATUS_DB


@tool
def check_system_service_status(service_name: Optional[str] = None) -> Dict[str, Any]:
    """Check the health, operational status, latency, and active incidents of platform services.

    Args:
        service_name: Optional name of the service (e.g. 'api-gateway', 'data-sync-pipeline',
                      'auth-service', 'billing-service'). If None, checks all services.

    Returns:
        Status report indicating whether services are operational, degraded, or down.
    """
    if service_name:
        clean_name = service_name.strip().lower()
        if clean_name in SYSTEM_STATUS_DB:
            return {
                "service": clean_name,
                "health": SYSTEM_STATUS_DB[clean_name],
            }
        return {
            "error": f"Unknown service '{service_name}'. Available: {list(SYSTEM_STATUS_DB.keys())}"
        }

    return {
        "overall_status": "degraded" if any(s["status"] != "operational" for s in SYSTEM_STATUS_DB.values()) else "operational",
        "services": SYSTEM_STATUS_DB,
    }


@tool
def fetch_system_logs(service: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
    """Fetch recent diagnostic logs and error traces from system services.

    Args:
        service: Optional filter by service name (e.g. 'data-sync-pipeline').
        limit: Maximum number of log lines to retrieve (default 5).

    Returns:
        Recent log entries containing timestamps, severity levels, and error details.
    """
    logs = MOCK_SYSTEM_LOGS
    if service:
        clean_srv = service.strip().lower()
        logs = [log for log in logs if clean_srv in log["service"].lower()]

    return {
        "count": min(len(logs), limit),
        "logs": logs[:limit],
    }


@tool
def search_knowledge_base(query: str) -> Dict[str, Any]:
    """Search internal customer support and technical knowledge base for solutions.

    Args:
        query: Search keywords or problem description (e.g. '503 error', 'refund policy', 'API key').

    Returns:
        Matching knowledge base articles with step-by-step guides.
    """
    query_tokens = [tok.lower() for tok in query.split()]

    matches = []
    for article in KNOWLEDGE_BASE:
        text_corpus = f"{article['title']} {article['content']} {article['category']}".lower()
        # Simple relevance scoring based on token overlap
        match_score = sum(1 for tok in query_tokens if tok in text_corpus)
        if match_score > 0:
            matches.append((match_score, article))

    # Sort by relevance
    matches.sort(key=lambda x: x[0], reverse=True)

    results = [item[1] for item in matches[:3]]
    return {
        "query": query,
        "results_found": len(results),
        "articles": results,
    }
