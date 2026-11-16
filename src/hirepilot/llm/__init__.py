"""LLM abstraction layer supporting free tier Gemini (primary) and Groq (fallback)."""

from hirepilot.llm.base import LLMMessage, LLMProvider, LLMResponse
from hirepilot.llm.exceptions import (
    AuthenticationError,
    LLMError,
    ProviderUnavailableError,
    RateLimitError,
)
from hirepilot.llm.fallback import FallbackLLMProvider
from hirepilot.llm.factory import get_llm_provider
from hirepilot.llm.gemini import GeminiProvider
from hirepilot.llm.groq import GroqProvider
from hirepilot.llm.mock import MockLLMProvider
from hirepilot.llm.rate_limiter import SlidingWindowRateLimiter

__all__ = [
    "LLMMessage",
    "LLMResponse",
    "LLMProvider",
    "GeminiProvider",
    "GroqProvider",
    "FallbackLLMProvider",
    "MockLLMProvider",
    "SlidingWindowRateLimiter",
    "LLMError",
    "RateLimitError",
    "AuthenticationError",
    "ProviderUnavailableError",
    "get_llm_provider",
]
