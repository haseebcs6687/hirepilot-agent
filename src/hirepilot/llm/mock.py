"""Mock LLM provider for unit testing and offline development."""

from __future__ import annotations

from typing import Any, Callable, Optional

from hirepilot.llm.base import LLMMessage, LLMProvider, LLMResponse
from hirepilot.llm.rate_limiter import SlidingWindowRateLimiter


class MockLLMProvider(LLMProvider):
    """Mock LLM provider returning predetermined or dynamic responses."""

    def __init__(
        self,
        name: str = "mock",
        model: str = "mock-model-v1",
        default_response: str = "Mock generated content",
        response_handler: Optional[Callable[[list[LLMMessage]], str]] = None,
        should_fail: bool = False,
        failure_exception: Optional[Exception] = None,
        rpm_limit: int = 100,
    ) -> None:
        super().__init__(name=name, model=model, rate_limiter=SlidingWindowRateLimiter(max_requests=rpm_limit))
        self.default_response = default_response
        self.response_handler = response_handler
        self.should_fail = should_fail
        self.failure_exception = failure_exception
        self.call_history: list[dict[str, Any]] = []

    def _generate_response(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        self.call_history.append({"messages": messages, "kwargs": kwargs})

        if self.should_fail:
            if self.failure_exception:
                raise self.failure_exception
            raise RuntimeError(f"Simulated failure from {self.name}")

        if self.response_handler:
            content = self.response_handler(messages)
        else:
            content = self.default_response

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.name,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            raw={"status": "mock_success"},
        )

    def complete(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        msg_list = self._normalize_messages(messages)
        return self._generate_response(msg_list, temperature=temperature, max_tokens=max_tokens, **kwargs)

    async def complete_async(
        self,
        messages: list[LLMMessage] | str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        msg_list = self._normalize_messages(messages)
        return self._generate_response(msg_list, temperature=temperature, max_tokens=max_tokens, **kwargs)
