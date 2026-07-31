"""Wraps user-pasted text into the same normalized shape the URL and PDF
ingestion paths produce, so downstream code never needs to care where a
source came from."""

from __future__ import annotations

from datetime import datetime, timezone

from ingestion.cleaning import clean_text
from ingestion.models import IngestedSource


def from_text(text: str, title: str | None = None, source_ref: str | None = None) -> IngestedSource:
    cleaned = clean_text(text)
    return IngestedSource(
        source_type="text",
        source_ref=source_ref,
        title=title,
        text=cleaned,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )
