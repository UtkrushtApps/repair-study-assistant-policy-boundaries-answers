#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
pip install -q -r requirements.txt
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
docker compose up -d
for attempt in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U study -d study_assistant >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" == "30" ]]; then
    echo "PostgreSQL did not become healthy" >&2
    exit 1
  fi
  sleep 1
done
test -s init_database.sql
test -s data/requests.jsonl
docker compose exec -T postgres psql -U study -d study_assistant -tAc "select count(*) > 0 from sources" | grep -q t
docker compose exec -T postgres psql -U study -d study_assistant -tAc "select count(*) > 0 from case_records" | grep -q t
python -m app.readiness
if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  python -m app.ping
fi
if [[ -f .api.pid ]] && kill -0 "$(cat .api.pid)" 2>/dev/null; then
  kill "$(cat .api.pid)"
fi
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 >api.log 2>&1 &
echo $! > .api.pid
echo "ready"
