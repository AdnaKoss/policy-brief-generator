"""LLM-backed generation of a structured UN/UNDP-style policy brief from a
single ingested source. Provider-agnostic: pick the backend with the
LLM_PROVIDER env var — "gemini" (default, free tier) or "anthropic" (Claude,
requires a funded API key)."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from generation.prompts import SYSTEM_PROMPT
from generation.providers import AnthropicProvider, GeminiProvider, LLMProvider
from generation.providers.anthropic_provider import AnthropicProviderError
from generation.providers.gemini_provider import GeminiProviderError
from generation.schemas import GeneratedBrief, PolicyBrief
from ingestion.models import IngestedSource

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()


class BriefGenerationError(RuntimeError):
    """Raised when the configured LLM provider fails to produce a usable brief."""


def _get_provider() -> LLMProvider:
    if LLM_PROVIDER == "anthropic":
        return AnthropicProvider()
    if LLM_PROVIDER == "gemini":
        return GeminiProvider()
    raise BriefGenerationError(
        f"Unknown LLM_PROVIDER '{LLM_PROVIDER}' — expected 'gemini' or 'anthropic'."
    )


def generate_brief(source: IngestedSource, topic_hint: str | None = None) -> PolicyBrief:
    provider = _get_provider()
    user_content = _build_user_message(source, topic_hint)

    try:
        generated = provider.generate_structured(SYSTEM_PROMPT, user_content, GeneratedBrief)
    except (AnthropicProviderError, GeminiProviderError) as exc:
        raise BriefGenerationError(str(exc)) from exc

    return PolicyBrief(
        **generated.model_dump(),
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )


def _build_user_message(source: IngestedSource, topic_hint: str | None) -> str:
    header = f"Topic focus: {topic_hint}\n\n" if topic_hint else ""
    source_label = source.source_ref or "pasted text"
    return (
        f"{header}"
        f"Source ({source.source_type}, retrieved {source.retrieved_at}): {source_label}\n\n"
        f"--- SOURCE TEXT START ---\n{source.text}\n--- SOURCE TEXT END ---"
    )
