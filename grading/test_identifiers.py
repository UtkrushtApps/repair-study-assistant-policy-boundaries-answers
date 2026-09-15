from __future__ import annotations

import json

import pytest

from app.assistant import StudyAssistant
from app.db import execute, fetch_all


class LeakingLLM:
    def __init__(self, identifiers):
        self.identifiers = identifiers

    def complete_json(self, messages):
        return {"allowed": True, "reason": "within scope"}

    def complete(self, messages, response_format=None):
        if response_format is not None:
            return json.dumps(self.complete_json(messages))
        prompt = " ".join(item["content"] for item in messages)
        found = [value for value in self.identifiers if value.lower() in prompt.lower()]
        return "Case details: " + " | ".join(found) if found else "Case status is available without direct identifiers."


def identifier_values():
    records = fetch_all("select payload from case_records")
    keys = {"participant_id", "initials", "date_of_birth", "email", "phone", "medical_record_number"}
    return {
        str(value)
        for row in records
        for key, value in row["payload"].items()
        if key in keys and value
    }


@pytest.fixture(autouse=True)
def clean_audit():
    execute("delete from audit_events")


def assert_contains_no_identifier(value, identifiers):
    lowered = value.lower()
    assert all(identifier.lower() not in lowered for identifier in identifiers)


def test_identifiers_do_not_leave_answer_draft_or_error():
    identifiers = identifier_values()
    assistant = StudyAssistant(LeakingLLM(identifiers))
    results = [
        assistant.handle("id-answer", "answer", "What is the Week 8 missed visit status?"),
        assistant.handle("id-draft", "draft", "Draft the Week 8 missed visit handoff."),
        assistant.handle("id-error", "answer", "Why did the screening consent sync fail?"),
    ]
    for result in results:
        assert_contains_no_identifier(result.text, identifiers)


def test_identifiers_do_not_enter_history_or_audit():
    identifiers = identifier_values()
    assistant = StudyAssistant(LeakingLLM(identifiers))
    assistant.handle("stored", "draft", "Draft the Week 8 missed visit handoff.")
    assistant.handle("stored-error", "answer", "Why did the screening consent sync fail?")
    assert_contains_no_identifier(json.dumps(assistant.history, default=str), identifiers)
    rows = fetch_all("select event_type, session_id, details from audit_events order by audit_id")
    assert rows
    assert_contains_no_identifier(json.dumps(rows, default=str), identifiers)
