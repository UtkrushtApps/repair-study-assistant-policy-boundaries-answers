from __future__ import annotations

import re
from typing import Any

from app.db import fetch_all

REDACTION = "[REDACTED]"

SENSITIVE_KEYS = {
    "participant_id",
    "participant_number",
    "name",
    "first_name",
    "last_name",
    "initials",
    "date_of_birth",
    "birth_date",
    "dob",
    "email",
    "email_address",
    "phone",
    "phone_number",
    "medical_record_number",
    "mrn",
}

_GENERIC_PATTERNS = (
    re.compile(r"\bP-\d{3,}\b", re.IGNORECASE),
    re.compile(r"\bMRN[-\s:]?[A-Z0-9-]{4,}\b", re.IGNORECASE),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?<!\w)\+?1?[\s.-]?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\w)"),
)


def _known_sensitive_values() -> list[str]:
    """Read sensitive values without retaining them in module or session state."""
    try:
        rows = fetch_all("select payload from case_records")
    except Exception:
        # Generic patterns remain an important fail-safe when the store is unavailable.
        return []

    values: list[str] = []
    for row in rows:
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if key.lower() in SENSITIVE_KEYS and value not in (None, ""):
                values.append(str(value))
    return sorted(set(values), key=len, reverse=True)


def redact_text(value: str) -> str:
    """Remove both known case identifiers and common identifier formats."""
    result = str(value)
    for sensitive_value in _known_sensitive_values():
        result = re.sub(
            rf"(?<!\w){re.escape(sensitive_value)}(?!\w)",
            REDACTION,
            result,
            flags=re.IGNORECASE,
        )
    for pattern in _GENERIC_PATTERNS:
        result = pattern.sub(REDACTION, result)
    return result


def sanitize_payload(value: Any) -> Any:
    """Recursively remove sensitive fields and redact strings in structured data."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, child in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                continue
            cleaned[str(key)] = sanitize_payload(child)
        return cleaned
    if isinstance(value, list):
        return [sanitize_payload(child) for child in value]
    if isinstance(value, tuple):
        return [sanitize_payload(child) for child in value]
    if isinstance(value, str):
        return redact_text(value)
    return value
