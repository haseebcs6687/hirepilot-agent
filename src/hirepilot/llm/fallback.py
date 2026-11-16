"""Fallback and retry orchestrator for LLM providers."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

from hirepilot.llm.base import LLMMessage, LLMProvider, LLMResponse
from hirepilot.llm.exceptions import (
    AuthenticationError,
    LLMError,
    ProviderUnavailableError,
    RateLimitError,
)
from hirepilot.logger import get_logger

logger = get_logger("llm.fallback")


class FallbackLLMProvider(LLMProvider):
    """Orchestrates primary and fallback LLM providers with automatic failover."""

    def __init__(
        self,
        primary: LLMProvider,
        fallback: Optional[LLMProvider] = None,
        max_retries: int = 2,
        retry_delay_seconds: float = 1.0,
    ) -> None:
        super().__init__(
            name=f"fallback({primary.name}->{fallback.name if fallback else 'none'})",
            model=primary.model,
            rate_limiter=primary.rate_limiter,
        )
        self.primary = primary
        self.fallback = fallback
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

    def complete(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        primary_errors: list[Exception] = []

        # Attempt primary with retries for transient errors
        for attempt in range(1, self.max_retries + 1):
            try:
                return self.primary.complete(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            except (RateLimitError, ProviderUnavailableError) as exc:
                primary_errors.append(exc)
                logger.warning(
                    "Primary provider [%s] failed attempt %d/%d: %s",
                    self.primary.name,
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay_seconds * (2 ** (attempt - 1)))
            except AuthenticationError as exc:
                primary_errors.append(exc)
                logger.error("Primary provider [%s] authentication failed: %s", self.primary.name, exc)
                break  # Don't retry auth errors, failover immediately
            except Exception as exc:
                primary_errors.append(exc)
                logger.warning("Primary provider [%s] unexpected error: %s", self.primary.name, exc)
                break

        # If primary failed and fallback exists, failover to fallback
        if self.fallback:
            logger.info(
                "Triggering fallback provider [%s] after primary [%s] failure.",
                self.fallback.name,
                self.primary.name,
            )
            try:
                return self.fallback.complete(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            except Exception as fallback_exc:
                logger.error("Fallback provider [%s] also failed: %s", self.fallback.name, fallback_exc)
                raise LLMError(
                    f"Both primary ({self.primary.name}) and fallback ({self.fallback.name}) failed. "
                    f"Primary: {primary_errors[-1] if primary_errors else 'unknown'}; Fallback: {fallback_exc}",
                    provider=self.name,
                ) from fallback_exc

        last_err = primary_errors[-1] if primary_errors else Exception("Unknown primary error")
        raise LLMError(f"Primary provider [{self.primary.name}] failed and no fallback available: {last_err}") from last_err

    async def complete_async(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        primary_errors: list[Exception] = []

        for attempt in range(1, self.max_retries + 1):
            try:
                return await self.primary.complete_async(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            except (RateLimitError, ProviderUnavailableError) as exc:
                primary_errors.append(exc)
                logger.warning(
                    "Primary provider [%s] failed async attempt %d/%d: %s",
                    self.primary.name,
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay_seconds * (2 ** (attempt - 1)))
            except AuthenticationError as exc:
                primary_errors.append(exc)
                logger.error("Primary provider [%s] authentication failed: %s", self.primary.name, exc)
                break
            except Exception as exc:
                primary_errors.append(exc)
                logger.warning("Primary provider [%s] unexpected error: %s", self.primary.name, exc)
                break

        if self.fallback:
            logger.info(
                "Triggering fallback provider [%s] async after primary [%s] failure.",
                self.fallback.name,
                self.primary.name,
            )
            try:
                return await self.fallback.complete_async(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            except Exception as fallback_exc:
                logger.error("Fallback provider [%s] also failed async: %s", self.fallback.name, fallback_exc)
                raise LLMError(
                    f"Both primary ({self.primary.name}) and fallback ({self.fallback.name}) failed. "
                    f"Primary: {primary_errors[-1] if primary_errors else 'unknown'}; Fallback: {fallback_exc}",
                    provider=self.name,
                ) from fallback_exc

        last_err = primary_errors[-1] if primary_errors else Exception("Unknown primary error")
        raise LLMError(f"Primary provider [{self.primary.name}] failed and no fallback available: {last_err}") from last_err
