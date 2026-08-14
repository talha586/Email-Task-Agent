"""LLM provider abstraction for the email-to-task agent."""

from __future__ import annotations

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
    """Groq-backed model client."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        import groq

        self._client = groq.Groq(api_key=api_key)
        self._model = model

    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        return ModelResponse(content=content, model=self._model, provider="groq")
