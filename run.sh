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
  if docker compose exec -T postgres psql -U study -d study_assistant -tAc "select 1 from sources limit 1" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" == "30" ]]; then
    echo "PostgreSQL did not finish seeding" >&2
    exit 1
  fi
  sleep 2
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
  kill -- "-$(cat .api.pid)" 2>/dev/null || kill "$(cat .api.pid)"
fi
nohup setsid python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app >api.log 2>&1 &
echo $! > .api.pid
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "API is running on port 8000 (log: api.log)"
    break
  fi
  if [[ "$attempt" == "30" ]]; then
    echo "API did not start" >&2
    tail -20 api.log >&2 || true
    exit 1
  fi
  sleep 1
done
echo "ready"
