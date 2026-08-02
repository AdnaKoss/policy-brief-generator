from __future__ import annotations

from pydantic import BaseModel


class GeneratedBrief(BaseModel):
    """The part of the brief the LLM produces. `date` is added afterwards by
    the caller rather than trusted from the model, since the model has no
    reliable notion of "today"."""

    title: str
    executive_summary: str
    background: str
    key_findings: list[str]
    policy_implications: str
    recommendations: list[str]
    sources: list[str]
    limitations: list[str]


class PolicyBrief(GeneratedBrief):
    date: str
