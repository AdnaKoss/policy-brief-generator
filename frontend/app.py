"""Streamlit UI for the Policy Brief Generator: collect a source (URL, pasted
text, or PDF), call the API to generate a brief, then let the user review and
lightly edit it before exporting."""

from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Policy Brief Generator", page_icon=":page_facing_up:", layout="wide")


def _reset_brief() -> None:
    st.session_state.pop("brief", None)


def _lines(value: str) -> list[str]:
    return [line for line in value.splitlines() if line.strip()]


def _call_generate(*, url, text, uploaded_file, topic_hint) -> dict:
    data = {}
    if topic_hint:
        data["topic_hint"] = topic_hint
    files = None
    if url:
        data["url"] = url
    elif text:
        data["text"] = text
    elif uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}

    response = requests.post(f"{API_BASE_URL}/generate", data=data, files=files, timeout=120)
    if response.status_code != 200:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(detail)
    return response.json()


def _brief_to_markdown(brief: dict) -> str:
    lines = [f"# {brief['title']}", "", f"*{brief['date']}*", ""]
    lines += ["## Executive Summary", brief["executive_summary"], ""]
    lines += ["## Background", brief["background"], ""]
    lines += ["## Key Findings"] + [f"- {item}" for item in brief["key_findings"]]
    lines += ["", "## Policy Implications", brief["policy_implications"], ""]
    lines += ["## Recommendations"] + [f"- {item}" for item in brief["recommendations"]]
    lines += ["", "## Sources"] + [f"- {item}" for item in brief["sources"]]
    if brief["limitations"]:
        lines += ["", "## Limitations"] + [f"- {item}" for item in brief["limitations"]]
    return "\n".join(lines)


st.title("Policy Brief Generator")
st.caption(
    "Turn a report, article, or pasted text on digital / AI / data governance "
    "into a structured UN/UNDP-style policy brief."
)

with st.sidebar:
    st.header("Source")
    source_mode = st.radio("Input type", ["URL", "Paste text", "Upload PDF"])
    url = text = None
    uploaded_file = None
    if source_mode == "URL":
        url = st.text_input("Source URL")
    elif source_mode == "Paste text":
        text = st.text_area("Pasted text", height=200)
    else:
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    topic_hint = st.text_input("Topic focus (optional)")
    generate_clicked = st.button("Generate brief", type="primary", on_click=_reset_brief)

if generate_clicked:
    with st.spinner("Generating brief..."):
        try:
            st.session_state["brief"] = _call_generate(
                url=url, text=text, uploaded_file=uploaded_file, topic_hint=topic_hint
            )
        except (requests.RequestException, RuntimeError) as exc:
            st.error(f"Could not generate brief: {exc}")

brief = st.session_state.get("brief")
if brief:
    st.subheader("Review & edit")
    brief["title"] = st.text_input("Title", brief["title"])
    brief["executive_summary"] = st.text_area(
        "Executive Summary", brief["executive_summary"], height=100
    )
    brief["background"] = st.text_area("Background", brief["background"], height=150)
    brief["key_findings"] = _lines(
        st.text_area("Key Findings (one per line)", "\n".join(brief["key_findings"]), height=120)
    )
    brief["policy_implications"] = st.text_area(
        "Policy Implications", brief["policy_implications"], height=120
    )
    brief["recommendations"] = _lines(
        st.text_area(
            "Recommendations (one per line)", "\n".join(brief["recommendations"]), height=100
        )
    )
    brief["sources"] = _lines(
        st.text_area("Sources (one per line)", "\n".join(brief["sources"]), height=80)
    )
    brief["limitations"] = _lines(
        st.text_area("Limitations (one per line)", "\n".join(brief["limitations"]), height=80)
    )

    st.download_button(
        "Download as Markdown",
        data=_brief_to_markdown(brief),
        file_name="policy_brief.md",
        mime="text/markdown",
    )
else:
    st.info("Fill in a source in the sidebar and click **Generate brief** to start.")
