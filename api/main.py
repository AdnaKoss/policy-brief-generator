"""FastAPI application exposing the ingestion -> generation pipeline as a
single /generate endpoint: accepts a URL, pasted text, or an uploaded PDF,
and returns a structured PolicyBrief."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from generation.generator import BriefGenerationError, generate_brief
from generation.schemas import PolicyBrief
from ingestion.cleaning import InsufficientTextError
from ingestion.models import IngestedSource
from ingestion.pdf import PdfExtractionError, extract_from_pdf
from ingestion.text_input import from_text
from ingestion.web import FetchError, extract_from_url

app = FastAPI(title="Policy Brief Generator", version="0.1.0")


class HealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/generate", response_model=PolicyBrief)
async def generate(
    url: Optional[str] = Form(default=None),
    text: Optional[str] = Form(default=None),
    topic_hint: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
) -> PolicyBrief:
    source = await _ingest(url=url, text=text, file=file)
    try:
        return generate_brief(source, topic_hint=topic_hint)
    except BriefGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _ingest(
    *, url: Optional[str], text: Optional[str], file: Optional[UploadFile]
) -> IngestedSource:
    provided = [value for value in (url, text, file) if value]
    if len(provided) != 1:
        raise HTTPException(
            status_code=400, detail="Provide exactly one of: url, text, or file."
        )

    try:
        if url:
            return extract_from_url(url)
        if text:
            return from_text(text)
        return extract_from_pdf(await file.read(), filename=file.filename)
    except (FetchError, PdfExtractionError, InsufficientTextError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
