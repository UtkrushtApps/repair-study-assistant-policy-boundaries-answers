from __future__ import annotations

import json
from pathlib import Path

from app import context, policy
from app.db import fetch_all
from app.retrieval import build_index, search


def main() -> None:
    request_path = Path("data/requests.jsonl")
    requests = [
        json.loads(line)
        for line in request_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    source_rows = fetch_all("select source_id from assistant_sources")
    record_rows = fetch_all("select record_id from case_records")
    if not requests or not source_rows or not record_rows:
        raise RuntimeError("Seed data is unavailable")
    if build_index() != len(source_rows):
        raise RuntimeError("Source index is incomplete")
    search(str(requests[0]["request"]))
    if context.ContextBundle is None or policy.Policy is None:
        raise RuntimeError("Assistant modules are unavailable")
    print(
        f"readiness ok: {len(source_rows)} sources, "
        f"{len(record_rows)} records, {len(requests)} requests"
    )


if __name__ == "__main__":
    main()
