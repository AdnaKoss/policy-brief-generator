from __future__ import annotations

from fastapi.testclient import TestClient

from api import main as api_main
from generation.generator import BriefGenerationError
from generation.schemas import PolicyBrief
from ingestion.web import FetchError

client = TestClient(api_main.app)


def _make_brief() -> PolicyBrief:
    return PolicyBrief(
        title="Brief title",
        executive_summary="Summary.",
        background="Background.",
        key_findings=["Finding one."],
        policy_implications="Implications.",
        recommendations=["Do X."],
        sources=["pasted text"],
        limitations=[],
        date="2026-08-02",
    )


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_with_text_returns_brief(monkeypatch):
    captured = {}

    def fake_generate_brief(source, topic_hint=None):
        captured["source"] = source
        captured["topic_hint"] = topic_hint
        return _make_brief()

    monkeypatch.setattr(api_main, "generate_brief", fake_generate_brief)

    response = client.post(
        "/generate",
        data={"text": "x" * 250, "topic_hint": "AI governance"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Brief title"
    assert captured["topic_hint"] == "AI governance"
    assert captured["source"].source_type == "text"


def test_generate_requires_exactly_one_source():
    response = client.post("/generate", data={})

    assert response.status_code == 400


def test_generate_rejects_multiple_sources():
    response = client.post(
        "/generate",
        data={"url": "https://example.org/report", "text": "x" * 250},
    )

    assert response.status_code == 400


def test_generate_wraps_ingestion_fetch_error(monkeypatch):
    def fake_extract_from_url(url):
        raise FetchError(f"Could not extract article text from {url}")

    monkeypatch.setattr(api_main, "extract_from_url", fake_extract_from_url)

    response = client.post("/generate", data={"url": "https://example.org/dead-link"})

    assert response.status_code == 422


def test_generate_wraps_brief_generation_error(monkeypatch):
    def fake_generate_brief(source, topic_hint=None):
        raise BriefGenerationError("Gemini generation failed: quota exceeded")

    monkeypatch.setattr(api_main, "generate_brief", fake_generate_brief)

    response = client.post("/generate", data={"text": "x" * 250})

    assert response.status_code == 502
