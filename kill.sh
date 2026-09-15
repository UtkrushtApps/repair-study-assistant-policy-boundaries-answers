#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -f .api.pid ]]; then
  kill "$(cat .api.pid)" 2>/dev/null || true
  rm -f .api.pid
fi
docker compose down
