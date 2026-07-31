# Policy Brief Generator

A tool that turns raw sources (public reports, articles, pasted text, PDFs) on a
digital / AI / data governance topic into a structured, professional policy
brief in the UN/UNDP style — with a review-and-edit step before export.

*(Full documentation, architecture diagram, and demo brief will be added once
the pipeline is complete.)*

## Project layout

```
ingestion/    Source intake (URL scraping, pasted text, PDF) + text cleaning
generation/   LLM-backed structured brief generation
api/          FastAPI application (REST endpoints)
templates/    Word export template / prompt templates
frontend/     Streamlit UI
examples/     Sample generated briefs
tests/        pytest test suite
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # add your Anthropic API key
```
