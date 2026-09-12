"""Tests for OpenRouter model integration in src/llm.py."""

from unittest.mock import patch
from langchain_openai import ChatOpenAI

from src.config import Settings
from src.llm import MockChatSupportModel, get_llm


def test_openrouter_llm_instantiation():
    """Verify get_llm instantiates ChatOpenAI with OpenRouter base URL and headers."""
    mock_settings = Settings()
    mock_settings.LLM_PROVIDER = "openrouter"
    mock_settings.OPENROUTER_API_KEY = "sk-or-v1-testkey123"
    mock_settings.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    mock_settings.OPENROUTER_APP_NAME = "Customer Support Triage Agent"
    mock_settings.OPENROUTER_HTTP_REFERER = "https://localhost"
    mock_settings.MODEL_NAME = "openai/gpt-4o-mini"
    mock_settings.MODEL_TEMPERATURE = 0.0

    with patch("src.llm.settings", mock_settings):
        llm = get_llm()
        assert isinstance(llm, ChatOpenAI)
        assert str(llm.openai_api_base).rstrip("/") == "https://openrouter.ai/api/v1"
        assert llm.model_name == "openai/gpt-4o-mini"
        assert llm.default_headers.get("HTTP-Referer") == "https://localhost"
        assert llm.default_headers.get("X-Title") == "Customer Support Triage Agent"


def test_openrouter_fallback_on_missing_key():
    """Verify get_llm gracefully falls back to MockChatSupportModel when key is empty."""
    mock_settings = Settings()
    mock_settings.LLM_PROVIDER = "openrouter"
    mock_settings.OPENROUTER_API_KEY = ""

    with patch("src.llm.settings", mock_settings):
        llm = get_llm()
        assert isinstance(llm, MockChatSupportModel)
