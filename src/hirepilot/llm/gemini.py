"""Google Gemini LLM provider implementation."""

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

logger = get_logger("llm.gemini")


class GeminiProvider(LLMProvider):
    """Google Gemini provider via Google AI Studio API."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        rpm_limit: int = 15,
        timeout_seconds: float = 30.0,
        rate_limiter: Optional[SlidingWindowRateLimiter] = None,
    ) -> None:
        limiter = rate_limiter or SlidingWindowRateLimiter(max_requests=rpm_limit)
        super().__init__(name="gemini", model=model, rate_limiter=limiter)
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def _prepare_payload(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Map generic LLMMessages to Gemini REST payload."""
        contents = []
        system_instructions = []

        for msg in messages:
            if msg.role == "system":
                system_instructions.append({"text": msg.content})
            elif msg.role in ("user", "human"):
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role in ("assistant", "model"):
                contents.append({"role": "model", "parts": [{"text": msg.content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": f"[{msg.role}]: {msg.content}"}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instructions:
            payload["systemInstruction"] = {"parts": system_instructions}
        return payload

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise LLMError("Gemini returned empty candidate list", provider=self.name)

            content_parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in content_parts)

            usage_metadata = data.get("usageMetadata", {})
            usage = {
                "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                "total_tokens": usage_metadata.get("totalTokenCount", 0),
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
            raise LLMError(f"Failed to parse Gemini response: {e}", provider=self.name) from e

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> None:
        status = exc.response.status_code
        error_text = exc.response.text
        logger.warning("Gemini HTTP error %d: %s", status, error_text)
        if status == 429:
            raise RateLimitError("Gemini rate limit exceeded (429)", provider=self.name)
        if status in (401, 403):
            raise AuthenticationError("Invalid or missing Gemini API key", provider=self.name)
        if status >= 500:
            raise ProviderUnavailableError(f"Gemini server error ({status})", provider=self.name)
        raise LLMError(f"Gemini API returned error {status}: {error_text}", provider=self.name, status_code=status)

    def complete(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        if not self.api_key:
            raise AuthenticationError("Gemini API key is not configured.", provider=self.name)

        if not self.rate_limiter.acquire_sync(timeout=self.timeout_seconds):
            raise RateLimitError("Rate limit wait timed out for Gemini", provider=self.name)

        msg_list = self._normalize_messages(messages)
        payload = self._prepare_payload(msg_list, temperature, max_tokens)
        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                return self._parse_response(res.json())
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderUnavailableError(f"Gemini network/timeout error: {exc}", provider=self.name) from exc
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"Unexpected error calling Gemini: {exc}", provider=self.name) from exc

    async def complete_async(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        if not self.api_key:
            raise AuthenticationError("Gemini API key is not configured.", provider=self.name)

        if not await self.rate_limiter.acquire_async(timeout=self.timeout_seconds):
            raise RateLimitError("Rate limit wait timed out for Gemini", provider=self.name)

        msg_list = self._normalize_messages(messages)
        payload = self._prepare_payload(msg_list, temperature, max_tokens)
        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                return self._parse_response(res.json())
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderUnavailableError(f"Gemini network/timeout error: {exc}", provider=self.name) from exc
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"Unexpected error calling Gemini: {exc}", provider=self.name) from exc
