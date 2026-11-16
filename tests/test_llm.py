"""Unit tests for HirePilot LLM abstraction, rate limiter, and fallback."""

import pytest
from hirepilot.llm.base import LLMMessage
from hirepilot.llm.exceptions import LLMError, RateLimitError
from hirepilot.llm.fallback import FallbackLLMProvider
from hirepilot.llm.mock import MockLLMProvider
from hirepilot.llm.rate_limiter import SlidingWindowRateLimiter


def test_rate_limiter_sync():
    """Verify rate limiter allows up to max_requests and respects windows."""
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=1.0)
    assert limiter.acquire_sync(timeout=0.1) is True
    assert limiter.acquire_sync(timeout=0.1) is True
    assert limiter.acquire_sync(timeout=0.1) is True
    # 4th request within 1s should fail timeout
    assert limiter.acquire_sync(timeout=0.05) is False


@pytest.mark.asyncio
async def test_rate_limiter_async():
    """Verify async rate limiter handles requests."""
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=1.0)
    assert await limiter.acquire_async(timeout=0.1) is True
    assert await limiter.acquire_async(timeout=0.1) is True
    assert await limiter.acquire_async(timeout=0.05) is False


def test_mock_provider_complete():
    """Verify MockLLMProvider returns expected response and tracks calls."""
    provider = MockLLMProvider(default_response="Personalized outreach line")
    response = provider.complete("Write an email hook")

    assert response.content == "Personalized outreach line"
    assert response.provider == "mock"
    assert len(provider.call_history) == 1
    assert provider.call_history[0]["messages"][0].content == "Write an email hook"


@pytest.mark.asyncio
async def test_mock_provider_async():
    """Verify MockLLMProvider async completion."""
    provider = MockLLMProvider(default_response="Async email response")
    response = await provider.complete_async([LLMMessage(role="user", content="Hello")])
    assert response.content == "Async email response"


def test_fallback_success_on_primary():
    """Verify FallbackLLMProvider returns primary response when primary succeeds."""
    primary = MockLLMProvider(name="gemini-mock", default_response="Primary response")
    fallback = MockLLMProvider(name="groq-mock", default_response="Fallback response")

    orchestrator = FallbackLLMProvider(primary=primary, fallback=fallback)
    response = orchestrator.complete("Draft prompt")

    assert response.content == "Primary response"
    assert response.provider == "gemini-mock"
    assert len(primary.call_history) == 1
    assert len(fallback.call_history) == 0


def test_fallback_triggers_when_primary_rate_limited():
    """Verify FallbackLLMProvider gracefully falls back to secondary when primary fails."""
    primary = MockLLMProvider(
        name="gemini-mock",
        should_fail=True,
        failure_exception=RateLimitError("Gemini 429 quota exhausted", provider="gemini-mock"),
    )
    fallback = MockLLMProvider(name="groq-mock", default_response="Groq fallback output")

    orchestrator = FallbackLLMProvider(
        primary=primary,
        fallback=fallback,
        max_retries=1,
    )
    response = orchestrator.complete("Draft prompt")

    assert response.content == "Groq fallback output"
    assert response.provider == "groq-mock"
    assert len(primary.call_history) == 1
    assert len(fallback.call_history) == 1


@pytest.mark.asyncio
async def test_fallback_async_triggers():
    """Verify async failover behavior."""
    primary = MockLLMProvider(
        name="gemini-mock",
        should_fail=True,
        failure_exception=RateLimitError("Rate limited", provider="gemini-mock"),
    )
    fallback = MockLLMProvider(name="groq-mock", default_response="Async fallback")

    orchestrator = FallbackLLMProvider(primary=primary, fallback=fallback, max_retries=1)
    response = await orchestrator.complete_async("Draft prompt")

    assert response.content == "Async fallback"
    assert response.provider == "groq-mock"


def test_fallback_raises_when_all_fail():
    """Verify LLMError is raised when both providers fail."""
    primary = MockLLMProvider(
        name="gemini-mock",
        should_fail=True,
        failure_exception=RateLimitError("Primary quota", provider="gemini-mock"),
    )
    fallback = MockLLMProvider(
        name="groq-mock",
        should_fail=True,
        failure_exception=LLMError("Groq service outage", provider="groq-mock"),
    )

    orchestrator = FallbackLLMProvider(primary=primary, fallback=fallback, max_retries=1)
    with pytest.raises(LLMError) as exc_info:
        orchestrator.complete("Draft prompt")

    assert "Both primary" in str(exc_info.value)
