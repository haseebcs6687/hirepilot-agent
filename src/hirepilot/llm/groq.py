"""Groq LLM provider implementation."""

from __future__ import annotations

from typing import Any, Optional
import httpx

from hirepilot.llm.base import LLMMessage, LLMProvider, LLMResponse
from hirepilot.llm.exceptions import (
    AuthenticationError,
    LLMError,
    ProviderUnavailableError,
    RateLimitError,
)
from hirepilot.llm.rate_limiter import SlidingWindowRateLimiter
from hirepilot.logger import get_logger

logger = get_logger("llm.groq")


class GroqProvider(LLMProvider):
    """Groq API provider (OpenAI-compatible schema with ultra-fast inference)."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        rpm_limit: int = 30,
        timeout_seconds: float = 30.0,
        rate_limiter: Optional[SlidingWindowRateLimiter] = None,
    ) -> None:
        limiter = rate_limiter or SlidingWindowRateLimiter(max_requests=rpm_limit)
        super().__init__(name="groq", model=model, rate_limiter=limiter)
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def _prepare_payload(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        try:
            choices = data.get("choices", [])
            if not choices:
                raise LLMError("Groq returned empty choices list", provider=self.name)

            message = choices[0].get("message", {})
            text = message.get("content", "")

            raw_usage = data.get("usage", {})
            usage = {
                "prompt_tokens": raw_usage.get("prompt_tokens", 0),
                "completion_tokens": raw_usage.get("completion_tokens", 0),
                "total_tokens": raw_usage.get("total_tokens", 0),
            }

            return LLMResponse(
                content=text,
                model=self.model,
                provider=self.name,
                usage=usage,
                raw=data,
            )
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            raise LLMError(f"Failed to parse Groq response: {e}", provider=self.name) from e

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> None:
        status = exc.response.status_code
        error_text = exc.response.text
        logger.warning("Groq HTTP error %d: %s", status, error_text)
        if status == 429:
            raise RateLimitError("Groq rate limit exceeded (429)", provider=self.name)
        if status in (401, 403):
            raise AuthenticationError("Invalid or missing Groq API key", provider=self.name)
        if status >= 500:
            raise ProviderUnavailableError(f"Groq server error ({status})", provider=self.name)
        raise LLMError(f"Groq API returned error {status}: {error_text}", provider=self.name, status_code=status)

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise AuthenticationError("Groq API key is not configured.", provider=self.name)
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def complete(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        headers = self._get_headers()
        if not self.rate_limiter.acquire_sync(timeout=self.timeout_seconds):
            raise RateLimitError("Rate limit wait timed out for Groq", provider=self.name)

        msg_list = self._normalize_messages(messages)
        payload = self._prepare_payload(msg_list, temperature, max_tokens)

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(self.BASE_URL, headers=headers, json=payload)
                res.raise_for_status()
                return self._parse_response(res.json())
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderUnavailableError(f"Groq network/timeout error: {exc}", provider=self.name) from exc
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"Unexpected error calling Groq: {exc}", provider=self.name) from exc

    async def complete_async(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        headers = self._get_headers()
        if not await self.rate_limiter.acquire_async(timeout=self.timeout_seconds):
            raise RateLimitError("Rate limit wait timed out for Groq", provider=self.name)

        msg_list = self._normalize_messages(messages)
        payload = self._prepare_payload(msg_list, temperature, max_tokens)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(self.BASE_URL, headers=headers, json=payload)
                res.raise_for_status()
                return self._parse_response(res.json())
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderUnavailableError(f"Groq network/timeout error: {exc}", provider=self.name) from exc
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"Unexpected error calling Groq: {exc}", provider=self.name) from exc
