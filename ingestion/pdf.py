"""Extracts text from an uploaded PDF report (World Bank / UN reports are
routinely PDF-only)."""

from __future__ import annotations

import io
from datetime import datetime, timezone

import pdfplumber

from ingestion.cleaning import clean_text
from ingestion.models import IngestedSource


class PdfExtractionError(RuntimeError):
    """Raised when no extractable text is found in the PDF."""


def extract_from_pdf(file_bytes: bytes, filename: str | None = None) -> IngestedSource:
    pages_text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text:
                pages_text.append(page_text)

    raw_text = "\n\n".join(pages_text)
    if not raw_text.strip():
        raise PdfExtractionError(
            f"No extractable text found in {filename or 'the uploaded PDF'} "
            "(it may be a scanned image without OCR)."
        )

    cleaned = clean_text(raw_text)
    return IngestedSource(
        source_type="pdf",
        source_ref=filename,
        title=None,
        text=cleaned,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )
