from __future__ import annotations

import json
import re
from typing import Any

from app.db import fetch_all


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _searchable(row: dict[str, Any]) -> str:
    payload = row.get("payload") or {}
    return " ".join(
        (
            str(row.get("title", "")),
            str(row.get("content", "")),
            json.dumps(payload, default=str),
        )
    )


def search(query: str, limit: int = 6) -> list[dict[str, Any]]:
    if limit < 1:
        return []

    rows = fetch_all(
        """
        select source_id, source_kind, title, content, payload
        from assistant_sources
        order by source_id
        """
    )
    wanted = _tokens(query)
    scored = [(len(wanted & _tokens(_searchable(row))), row) for row in rows]
    matching = [item for item in scored if item[0] > 0]
    matching.sort(key=lambda item: (-item[0], str(item[1]["source_id"])))

    if not matching:
        matching = scored[:limit]
    return [row for _, row in matching[:limit]]


def build_index() -> int:
    rows = fetch_all("select source_id from assistant_sources")
    for row in rows:
        _tokens(str(row["source_id"]))
    return len(rows)
