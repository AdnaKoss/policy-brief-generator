"""Google Gemini backend — the default, free-tier LLM provider."""

from __future__ import annotations

import json
import os
from typing import Type, TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from generation.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class GeminiProviderError(RuntimeError):
    """Raised when Gemini fails to produce a usable structured response."""


class GeminiProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        self._client = genai.Client()
        self._model = model or DEFAULT_GEMINI_MODEL

    def generate_structured(self, system_prompt: str, user_content: str, schema: Type[T]) -> T:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_json_schema=schema.model_json_schema(),
                ),
            )
        except errors.APIError as exc:
            raise GeminiProviderError(f"Gemini generation failed: {exc.message}") from exc

        if not response.text:
            raise GeminiProviderError("Gemini did not return any content.")

        try:
            data = json.loads(response.text)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValueError) as exc:
            raise GeminiProviderError(f"Gemini returned unparsable JSON: {exc}") from exc
