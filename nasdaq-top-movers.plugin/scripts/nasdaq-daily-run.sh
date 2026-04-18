#!/usr/bin/env bash
# StockHive daily runner — invoked by the OpenClaw scheduler at 17:00 ET Mon–Fri.
# Loads env, then runs the orchestrator agent as a one-shot `claude -p` call
# with the nasdaq-top-movers plugin active.

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PLUGIN_DIR"

# 1. Load env
if [[ -f "config/.env" ]]; then
  set -a; source config/.env; set +a
elif [[ -f "config/.env.example" ]]; then
  echo "[warn] No config/.env found; copy config/.env.example and fill in secrets." >&2
fi

RUN_DATE="$(TZ=America/New_York date +%Y-%m-%d)"
LOG_DIR="${PLUGIN_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/run-${RUN_DATE}.log"

echo "[stockhive] run=${RUN_DATE} plugin=${PLUGIN_DIR}" | tee -a "$LOG_FILE"

PROMPT='Pick the top 10 Nasdaq 100 gainers over the last 4 weeks, run technical + fundamental + sentiment analysis via ephemeral subagents in parallel, decide BULLISH or BEARISH, then push the top 5 buy candidates to Telegram.'

# 2. Invoke Claude Code with the plugin in headless mode.
claude -p "$PROMPT" \
  --plugin nasdaq-top-movers \
  --agent nasdaq-analyst-orchestrator \
  --max-turns 40 \
  2>&1 | tee -a "$LOG_FILE"

echo "[stockhive] done run=${RUN_DATE}" | tee -a "$LOG_FILE"
