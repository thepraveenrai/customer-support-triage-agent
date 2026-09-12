"""Configuration management for Project 2: Customer Support Triage Agent.

Loads settings from environment variables and provides sensible defaults.
Supports OpenAI API, LangSmith observability, and offline Mock LLM execution.
"""

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

# Load environment variables from .env file if present
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Application configuration settings."""

    # Project metadata
    PROJECT_NAME: str = "Customer Support Triage Multi-Agent System"
    VERSION: str = "1.0.0"

    # LLM Settings
    # Supported providers: "openrouter", "openai", "mock"
    _env_provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    _openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    _openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if _env_provider in ["openrouter", "openai", "mock"]:
        LLM_PROVIDER: Literal["openrouter", "openai", "mock"] = _env_provider  # type: ignore
    elif _openrouter_key and not _openrouter_key.startswith("your-"):
        LLM_PROVIDER = "openrouter"
    elif _openai_key and not _openai_key.startswith("your-"):
        LLM_PROVIDER = "openai"
    else:
        LLM_PROVIDER = "mock"

    # OpenRouter API settings
    OPENROUTER_API_KEY: str = _openrouter_key
    OPENROUTER_BASE_URL: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    OPENROUTER_HTTP_REFERER: str = os.getenv(
        "OPENROUTER_HTTP_REFERER", "https://localhost"
    )
    OPENROUTER_APP_NAME: str = os.getenv(
        "OPENROUTER_APP_NAME", "Customer Support Triage Agent"
    )

    # OpenAI API settings
    OPENAI_API_KEY: str = _openai_key

    # Model name defaults to openrouter model if openrouter is active
    default_model = (
        "openai/gpt-4o-mini"
        if LLM_PROVIDER == "openrouter"
        else "gpt-4o-mini"
    )
    MODEL_NAME: str = os.getenv("MODEL_NAME", default_model)
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.0"))

    # Human-in-the-Loop (HITL) Thresholds
    # Any refund request strictly greater than this amount halts for human approval
    REFUND_APPROVAL_THRESHOLD_USD: float = float(
        os.getenv("REFUND_APPROVAL_THRESHOLD_USD", "50.0")
    )

    # If True, tickets classified with 'CRITICAL' urgency or 'ANGRY' sentiment
    # will require human manager sign-off before sending final resolution.
    ENFORCE_SENTIMENT_HUMAN_GATE: bool = True

    # Server Settings
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))


settings = Settings()
