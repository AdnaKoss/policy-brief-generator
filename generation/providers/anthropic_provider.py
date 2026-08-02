"""Anthropic Claude backend — optional, requires a funded API key. Enable
with LLM_PROVIDER=anthropic."""

from __future__ import annotations

import os
from typing import Type, TypeVar

import anthropic
from pydantic import BaseModel

from generation.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)

DEFAULT_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")
MAX_TOKENS = 8000


class AnthropicProviderError(RuntimeError):
    """Raised when Claude fails to produce a usable structured response."""


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        self._client = anthropic.Anthropic()
        self._model = model or DEFAULT_ANTHROPIC_MODEL

    def generate_structured(self, system_prompt: str, user_content: str, schema: Type[T]) -> T:
        try:
            response = self._client.messages.parse(
                model=self._model,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
                output_format=schema,
            )
        except anthropic.APIStatusError as exc:
            raise AnthropicProviderError(f"Claude generation failed: {exc.message}") from exc

        if response.stop_reason == "refusal":
            raise AnthropicProviderError("Claude declined to generate a brief for this source.")

        parsed = response.parsed_output
        if parsed is None:
            raise AnthropicProviderError("Claude did not return a parsable brief.")
        return parsed
