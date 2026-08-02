from __future__ import annotations

import pytest

from generation import generator
from generation.providers.anthropic_provider import AnthropicProviderError
from generation.providers.gemini_provider import GeminiProviderError
from generation.schemas import GeneratedBrief
from ingestion.models import IngestedSource


def _make_source(text: str | None = None, source_ref: str | None = None) -> IngestedSource:
    return IngestedSource(
        source_type="text",
        source_ref=source_ref,
        title="Test title",
        text=text or "x" * 250,
        retrieved_at="2026-08-02T00:00:00+00:00",
    )


def _make_generated() -> GeneratedBrief:
    return GeneratedBrief(
        title="Brief title",
        executive_summary="Summary.",
        background="Background.",
        key_findings=["Finding one."],
        policy_implications="Implications.",
        recommendations=["Do X."],
        sources=["pasted text"],
        limitations=[],
    )


class DummyProvider:
    def __init__(self, generated=None, error=None):
        self.generated = generated
        self.error = error
        self.calls = []

    def generate_structured(self, system_prompt, user_content, schema):
        self.calls.append((system_prompt, user_content, schema))
        if self.error:
            raise self.error
        return self.generated


def test_generate_brief_uses_gemini_by_default(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    dummy = DummyProvider(generated=_make_generated())
    monkeypatch.setattr(generator, "GeminiProvider", lambda: dummy)

    brief = generator.generate_brief(_make_source())

    assert brief.title == "Brief title"
    assert brief.date
    assert len(dummy.calls) == 1


def test_generate_brief_uses_anthropic_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    dummy = DummyProvider(generated=_make_generated())
    monkeypatch.setattr(generator, "AnthropicProvider", lambda: dummy)

    brief = generator.generate_brief(_make_source())

    assert brief.title == "Brief title"
    assert len(dummy.calls) == 1


def test_generate_brief_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "not-a-real-provider")

    with pytest.raises(generator.BriefGenerationError, match="Unknown LLM_PROVIDER"):
        generator.generate_brief(_make_source())


def test_generate_brief_wraps_gemini_errors(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    dummy = DummyProvider(error=GeminiProviderError("boom"))
    monkeypatch.setattr(generator, "GeminiProvider", lambda: dummy)

    with pytest.raises(generator.BriefGenerationError, match="boom"):
        generator.generate_brief(_make_source())


def test_generate_brief_wraps_anthropic_errors(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    dummy = DummyProvider(error=AnthropicProviderError("nope"))
    monkeypatch.setattr(generator, "AnthropicProvider", lambda: dummy)

    with pytest.raises(generator.BriefGenerationError, match="nope"):
        generator.generate_brief(_make_source())


def test_build_user_message_includes_topic_hint_and_source():
    source = _make_source(source_ref="https://example.org/report")
    message = generator._build_user_message(source, topic_hint="AI governance")

    assert "Topic focus: AI governance" in message
    assert "https://example.org/report" in message
    assert source.text in message


def test_build_user_message_omits_topic_hint_when_absent():
    source = _make_source()
    message = generator._build_user_message(source, topic_hint=None)

    assert "Topic focus" not in message
    assert "pasted text" in message
