"""Base contracts and data models for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field

from hirepilot.llm.rate_limiter import SlidingWindowRateLimiter


class LLMMessage(BaseModel):
    """Represents a chat message."""
    role: str = Field(description="Role of the author: system, user, assistant")
    content: str = Field(description="Textual content of the message")


class LLMResponse(BaseModel):
    """Unified response from any LLM provider."""
    content: str = Field(description="Generated text content")
    model: str = Field(description="Model identifier that produced the response")
    provider: str = Field(description="Provider name (gemini, groq, mock, etc.)")
    usage: dict[str, int] = Field(default_factory=dict, description="Token usage statistics if available")
    raw: dict[str, Any] = Field(default_factory=dict, description="Raw provider response payload")


class LLMProvider(ABC):
    """Abstract base class for LLM providers with built-in rate limiting."""

    def __init__(
        self,
        name: str,
        model: str,
        rate_limiter: Optional[SlidingWindowRateLimiter] = None,
    ) -> None:
        self.name = name
        self.model = model
        self.rate_limiter = rate_limiter or SlidingWindowRateLimiter(max_requests=60)

    @abstractmethod
    async def complete_async(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        """Asynchronously generate a completion."""
        pass

    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        """Synchronously generate a completion."""
        pass

    def _normalize_messages(self, messages: list[LLMMessage] | str) -> list[LLMMessage]:
        """Convert string prompt or message list into standard LLMMessage list."""
        if isinstance(messages, str):
            return [LLMMessage(role="user", content=messages)]
        return messages
