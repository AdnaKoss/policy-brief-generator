"""Fetches and extracts the main article/report text from a public URL.

Uses trafilatura first (handles boilerplate removal and metadata extraction
out of the box); falls back to a plain requests + BeautifulSoup paragraph
scrape for the rare page trafilatura can't parse.
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests
import trafilatura
from bs4 import BeautifulSoup

from ingestion.cleaning import clean_text
from ingestion.models import IngestedSource

USER_AGENT = (
    "Mozilla/5.0 (compatible; PolicyBriefGenerator/1.0; "
    "+https://github.com/AdnaKoss/policy-brief-generator)"
)
REQUEST_TIMEOUT = 15


class FetchError(RuntimeError):
    """Raised when a URL cannot be fetched or no extractable content is found."""


def extract_from_url(url: str) -> IngestedSource:
    downloaded = trafilatura.fetch_url(url)
    text = None
    title = None

    if downloaded:
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
        metadata = trafilatura.extract_metadata(downloaded)
        if metadata:
            title = metadata.title

    if not text:
        text, title = _fallback_extract(url, title)

    if not text:
        raise FetchError(f"Could not extract article text from {url}")

    cleaned = clean_text(text)
    return IngestedSource(
        source_type="url",
        source_ref=url,
        title=title,
        text=cleaned,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )


def _fallback_extract(url: str, title: str | None) -> tuple[str | None, str | None]:
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Request to {url} failed: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    if not title and soup.title:
        title = soup.title.get_text(strip=True)

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    text = "\n".join(p for p in paragraphs if p)
    return (text or None), title
