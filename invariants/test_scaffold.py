import json
from pathlib import Path

from app import context, policy
from app.db import fetch_all
from app.retrieval import build_index, search


def test_seed_store_is_available() -> None:
    rows = fetch_all("select source_id from assistant_sources")
    assert len(rows) >= 2
    assert build_index()


def test_local_search_returns_context() -> None:
    requests = [
        json.loads(line)
        for line in Path("data/requests.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = search(requests[0]["request"])
    assert rows


def test_assessed_modules_load() -> None:
    assert context.ContextBundle is not None
    assert policy.Policy is not None
