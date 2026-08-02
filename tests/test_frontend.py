from __future__ import annotations

from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP_PATH = "frontend/app.py"
RUN_TIMEOUT = 15


def _make_brief_json() -> dict:
    return {
        "title": "Brief title",
        "executive_summary": "Summary.",
        "background": "Background.",
        "key_findings": ["Finding one."],
        "policy_implications": "Implications.",
        "recommendations": ["Do X."],
        "sources": ["pasted text"],
        "limitations": [],
        "date": "2026-08-02",
    }


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class FakeDocxResponse:
    status_code = 200
    content = b"PK\x03\x04fake-docx-bytes"

    def json(self):
        return {}


def _generate_pasted_brief(at: AppTest) -> AppTest:
    at.sidebar.radio[0].set_value("Paste text").run(timeout=RUN_TIMEOUT)
    at.sidebar.text_area[0].set_value("x" * 250).run(timeout=RUN_TIMEOUT)
    with patch("requests.post", return_value=FakeResponse(200, _make_brief_json())):
        at.button[0].click().run(timeout=RUN_TIMEOUT)
    return at


def test_initial_state_shows_prompt_and_no_brief():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=RUN_TIMEOUT)

    assert not at.exception
    assert "brief" not in at.session_state
    assert at.info[0].value.startswith("Fill in a source")


def test_generate_from_pasted_text_populates_review_form():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=RUN_TIMEOUT)
    at.sidebar.radio[0].set_value("Paste text").run(timeout=RUN_TIMEOUT)
    at.sidebar.text_area[0].set_value("x" * 250).run(timeout=RUN_TIMEOUT)

    with patch("requests.post", return_value=FakeResponse(200, _make_brief_json())):
        at.button[0].click().run(timeout=RUN_TIMEOUT)

    assert not at.exception
    assert at.session_state["brief"]["title"] == "Brief title"
    titles = [t.value for t in at.text_input if t.label == "Title"]
    assert titles == ["Brief title"]
    assert [d.label for d in at.download_button] == ["Download as Markdown"]


def test_generate_error_shows_message_without_setting_brief():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=RUN_TIMEOUT)
    at.sidebar.radio[0].set_value("Paste text").run(timeout=RUN_TIMEOUT)
    at.sidebar.text_area[0].set_value("x" * 250).run(timeout=RUN_TIMEOUT)

    with patch(
        "requests.post",
        return_value=FakeResponse(502, {"detail": "Gemini generation failed: quota exceeded"}),
    ):
        at.button[0].click().run(timeout=RUN_TIMEOUT)

    assert not at.exception
    assert "brief" not in at.session_state
    assert "quota exceeded" in at.error[0].value


def test_editing_key_findings_strips_blank_lines():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=RUN_TIMEOUT)
    at.sidebar.radio[0].set_value("Paste text").run(timeout=RUN_TIMEOUT)
    at.sidebar.text_area[0].set_value("x" * 250).run(timeout=RUN_TIMEOUT)

    with patch("requests.post", return_value=FakeResponse(200, _make_brief_json())):
        at.button[0].click().run(timeout=RUN_TIMEOUT)

    findings_area = next(t for t in at.text_area if t.label == "Key Findings (one per line)")
    findings_area.set_value("Finding one.\n\nFinding two.\n").run(timeout=RUN_TIMEOUT)

    assert at.session_state["brief"]["key_findings"] == ["Finding one.", "Finding two."]


def test_prepare_word_export_shows_download_button():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=RUN_TIMEOUT)
    at = _generate_pasted_brief(at)

    export_button = next(b for b in at.button if b.label == "Prepare Word export")
    with patch("requests.post", return_value=FakeDocxResponse()):
        export_button.click().run(timeout=RUN_TIMEOUT)

    assert not at.exception
    assert at.session_state["docx_bytes"] == FakeDocxResponse.content
    assert "Download as Word (.docx)" in [d.label for d in at.download_button]


def test_editing_brief_after_word_export_invalidates_docx():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=RUN_TIMEOUT)
    at = _generate_pasted_brief(at)

    export_button = next(b for b in at.button if b.label == "Prepare Word export")
    with patch("requests.post", return_value=FakeDocxResponse()):
        export_button.click().run(timeout=RUN_TIMEOUT)

    title_input = next(t for t in at.text_input if t.label == "Title")
    title_input.set_value("Edited title").run(timeout=RUN_TIMEOUT)

    assert "docx_bytes" not in at.session_state
    assert "Download as Word (.docx)" not in [d.label for d in at.download_button]
