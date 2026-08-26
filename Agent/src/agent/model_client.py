"""LLM provider abstraction for the email-to-task agent."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModelResponse:
    content: str
    model: str
    provider: str


class ModelClient(ABC):
    """Abstract interface for text-completion LLM providers."""

    @abstractmethod
    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        """Return a single text completion for the given prompt."""


class GroqModelClient(ModelClient):
    """Groq-backed model client.

    Retries transient failures (network blips, rate limits, timeouts) with
    a short backoff before giving up — a single flaky call no longer fails
    the whole request outright.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-120b",
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        import groq

        self._client = groq.Groq(api_key=api_key)
        self._model = model
        self._max_retries = max(1, max_retries)
        self._retry_backoff_seconds = retry_backoff_seconds

    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=0.2,
                )
                content = response.choices[0].message.content or ""
                return ModelResponse(content=content, model=self._model, provider="groq")
            except Exception as exc:  # noqa: BLE001 — genuinely want to retry any failure
                last_exc = exc
                if attempt < self._max_retries:
                    time.sleep(self._retry_backoff_seconds * attempt)

        assert last_exc is not None  # loop always sets this before exhausting
        raise last_exc