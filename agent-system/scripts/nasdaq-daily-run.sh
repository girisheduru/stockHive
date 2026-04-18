#!/usr/bin/env bash
# StockHive daily runner — entrypoint for the scheduled task.
# Loads env and invokes the orchestrator agent in headless one-shot mode.
# The orchestrator spawns the ephemeral subagents that complete the agent system.

set -euo pipefail

SYSTEM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SYSTEM_DIR"

# 1. Load env
if [[ -f "config/.env" ]]; then
  set -a; source config/.env; set +a
elif [[ -f "config/.env.example" ]]; then
  echo "[warn] No config/.env found; copy config/.env.example and fill in secrets." >&2
fi

RUN_DATE="$(TZ=America/New_York date +%Y-%m-%d)"
LOG_DIR="${SYSTEM_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/run-${RUN_DATE}.log"

echo "[stockhive] run=${RUN_DATE} system=${SYSTEM_DIR}" | tee -a "$LOG_FILE"

PROMPT='Pick the top 10 Nasdaq 100 gainers over the last 4 weeks, run technical + fundamental + sentiment analysis via ephemeral subagents in parallel, decide BULLISH or BEARISH, then push the top 5 buy candidates to Telegram.'

# 2. Invoke Claude Code with the orchestrator agent. The agent system is
#    registered with OpenClaw via `/agents register`, so subagents, skills,
#    and MCPs resolve automatically from agent-system.json.
claude -p "$PROMPT" \
  --agent nasdaq-analyst-orchestrator \
  --max-turns 40 \
  2>&1 | tee -a "$LOG_FILE"

echo "[stockhive] done run=${RUN_DATE}" | tee -a "$LOG_FILE"
