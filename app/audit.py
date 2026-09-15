from __future__ import annotations

import json
from typing import Any

from app.db import execute
from app.privacy import sanitize_payload


class AuditStore:
    """Writes privacy-sanitized review events to the durable audit store."""

    def write(self, event_type: str, session_id: str, details: dict[str, Any]) -> None:
        safe_details = sanitize_payload(details)
        execute(
            "insert into audit_events(event_type, session_id, details) values (%s, %s, %s::jsonb)",
            (
                str(event_type)[:100],
                str(session_id)[:100],
                json.dumps(safe_details, ensure_ascii=True, default=str),
            ),
        )
