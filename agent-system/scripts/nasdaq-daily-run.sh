#!/usr/bin/env bash
# StockHive daily runner — entrypoint for the scheduled task.
# Loads env and executes the Yahoo-based live runner.

set -euo pipefail

SYSTEM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SYSTEM_DIR}/.." && pwd)"
cd "$REPO_DIR"

if [[ -f "agent-system/config/.env" ]]; then
  set -a; source agent-system/config/.env; set +a
elif [[ -f "agent-system/config/.env.example" ]]; then
  echo "[warn] No agent-system/config/.env found; copy .env.example and fill in secrets." >&2
fi

RUN_TZ="${TIMEZONE:-Europe/London}"
RUN_DATE="$(TZ="$RUN_TZ" date +%Y-%m-%d)"
LOG_DIR="${SYSTEM_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/run-${RUN_DATE}.log"

echo "[stockhive] run=${RUN_DATE} repo=${REPO_DIR}" | tee -a "$LOG_FILE"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "[error] Missing repo-local virtualenv at ${REPO_DIR}/.venv" | tee -a "$LOG_FILE"
  exit 1
fi

STOCKHIVE_PUBLISH_MODE="${STOCKHIVE_PUBLISH_MODE:-live}" \
  .venv/bin/python openclawMVP/scripts/run_live_option_b.py \
  2>&1 | tee -a "$LOG_FILE"

echo "[stockhive] done run=${RUN_DATE}" | tee -a "$LOG_FILE"
