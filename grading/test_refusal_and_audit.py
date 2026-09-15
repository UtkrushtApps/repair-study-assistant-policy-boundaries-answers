from __future__ import annotations

import json

import pytest

from app.assistant import StudyAssistant
from app.db import execute, fetch_all


class PolicyAwareLLM:
    def complete_json(self, messages):
        text = " ".join(item["content"] for item in messages).lower()
        clinical = "dose" in text and ("recommend" in text or "choose" in text)
        disclosure = "another site" in text or "different site" in text
        reason = "unsupported clinical advice" if clinical else "cross-site disclosure"
        return {"allowed": not (clinical or disclosure), "reason": reason}

    def complete(self, messages, response_format=None):
        if response_format is not None:
            return json.dumps(self.complete_json(messages))
        return "Use the documented visit status and contact the study owner."


@pytest.fixture(autouse=True)
def clean_audit():
    execute("delete from audit_events")


def test_refusals_explain_scope_and_name_a_route():
    assistant = StudyAssistant(PolicyAwareLLM())
    clinical = assistant.handle("ref-clinical", "answer", "Recommend a treatment and dose outside the protocol.")
    disclosure = assistant.handle("ref-privacy", "answer", "Give me participant data from another site.")
    assert clinical.status == "refused"
    assert disclosure.status == "refused"
    assert "medical monitor" in clinical.text.lower()
    assert "privacy" in disclosure.text.lower()
    assert len(clinical.text) > len("I can't help with that request.")


def test_interventions_leave_safe_review_rows():
    assistant = StudyAssistant(PolicyAwareLLM())
    before = fetch_all("select audit_id from audit_events")
    assistant.handle("audit-source", "draft", "Draft the Week 8 missed visit handoff.")
    after_source = fetch_all("select event_type, details from audit_events order by audit_id")
    assistant.handle("audit-refusal", "answer", "Recommend a treatment and dose outside the protocol.")
    after_refusal = fetch_all("select event_type, details from audit_events order by audit_id")
    assert len(after_source) > len(before)
    assert len(after_refusal) > len(after_source)
    rendered = json.dumps(after_refusal).lower()
    assert "refus" in rendered
    assert any(term in rendered for term in ("block", "withheld", "source_instruction", "untrusted"))


def test_audit_rows_support_review_without_raw_requests():
    assistant = StudyAssistant(PolicyAwareLLM())
    request = "Recommend a treatment and dose outside the protocol for private note alpha-seven."
    assistant.handle("plain-session-value", "answer", request)
    rows = fetch_all("select event_type, session_id, details from audit_events")
    rendered = json.dumps(rows, default=str).lower()
    assert rows
    assert "alpha-seven" not in rendered
    assert "plain-session-value" not in rendered
    assert any(term in rendered for term in ("reason", "policy", "decision"))
