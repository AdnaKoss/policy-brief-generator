from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IngestedSource:
    """Normalized representation of a source after extraction and cleaning,
    regardless of whether it came from a URL, pasted text, or a PDF upload."""

    source_type: str  # "url" | "text" | "pdf"
    source_ref: str | None  # URL, filename, or None for pasted text
    title: str | None
    text: str
    retrieved_at: str

    @property
    def word_count(self) -> int:
        return len(self.text.split())
