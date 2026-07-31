"""Text cleaning shared by all ingestion paths (URL, PDF, pasted text): strips
blank lines and common web boilerplate that survives extraction (cookie
banners, nav labels, share prompts), collapses whitespace, and enforces a
minimum length so obviously-failed extractions (paywalls, JS-only pages) are
rejected before ever reaching the LLM."""

from __future__ import annotations

import re

MIN_TEXT_LENGTH = 200

_BOILERPLATE_LINE_PATTERNS = [
    re.compile(r"^(cookies?|subscribe|sign up|share this|advertisement)\b.*$", re.IGNORECASE),
    re.compile(r"^(home|about( us)?|contact( us)?|privacy policy|terms of (service|use))$", re.IGNORECASE),
    re.compile(r"^(read more|related articles?|you might also like)$", re.IGNORECASE),
]


class InsufficientTextError(ValueError):
    """Raised when cleaned text is too short to be a usable source."""


def clean_text(raw: str) -> str:
    if not raw or not raw.strip():
        raise InsufficientTextError("Source text is empty.")

    kept_lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(pattern.match(stripped) for pattern in _BOILERPLATE_LINE_PATTERNS):
            continue
        kept_lines.append(stripped)

    text = "\n".join(kept_lines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if len(text) < MIN_TEXT_LENGTH:
        raise InsufficientTextError(
            f"Cleaned text is only {len(text)} characters (minimum {MIN_TEXT_LENGTH}); "
            "the source may be paywalled, JavaScript-rendered, or not a real article."
        )
    return text
