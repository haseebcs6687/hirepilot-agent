"""Factory to instantiate LLM providers based on configuration."""

from __future__ import annotations

from typing import Optional

from hirepilot.config import Settings, get_settings
from hirepilot.llm.base import LLMProvider
from hirepilot.llm.fallback import FallbackLLMProvider
from hirepilot.llm.gemini import GeminiProvider
from hirepilot.llm.groq import GroqProvider
from hirepilot.llm.mock import MockLLMProvider


def get_llm_provider(settings: Optional[Settings] = None, use_mock: bool = False) -> LLMProvider:
    """Construct configured LLM provider hierarchy (Gemini primary -> Groq fallback)."""
    if use_mock:
        return MockLLMProvider()

    cfg = settings or get_settings()

    gemini = GeminiProvider(
        api_key=cfg.gemini_api_key,
        model=cfg.gemini_model,
        rpm_limit=cfg.gemini_rpm_limit,
    )

    groq = GroqProvider(
        api_key=cfg.groq_api_key,
        model=cfg.groq_model,
        rpm_limit=cfg.groq_rpm_limit,
    )

    # Primary Gemini with automatic fallback to Groq
    return FallbackLLMProvider(
        primary=gemini,
        fallback=groq,
        max_retries=2,
    )
