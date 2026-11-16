"""Custom exceptions for LLM providers."""

from __future__ import annotations


class LLMError(Exception):
    """Base exception for LLM provider errors."""

    def __init__(self, message: str, provider: str = "unknown", status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status_code = status_code


class RateLimitError(LLMError):
    """Raised when an LLM provider rate limit is exceeded."""

    def __init__(self, message: str, provider: str = "unknown", retry_after: float | None = None) -> None:
        super().__init__(message, provider=provider, status_code=429)
        self.retry_after = retry_after


class AuthenticationError(LLMError):
    """Raised when API key or credentials are invalid."""

    def __init__(self, message: str, provider: str = "unknown") -> None:
        super().__init__(message, provider=provider, status_code=401)


class ProviderUnavailableError(LLMError):
    """Raised when provider is down, experiencing outage, or times out."""
