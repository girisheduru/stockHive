#!/usr/bin/env bash
# StockHive primary orchestrator runtime launcher.
# Prepares a dated runtime payload and run-manifest for the agent-native path.

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
RUN_TS="$(TZ="$RUN_TZ" date +%Y-%m-%dT%H:%M:%S%z)"
LOG_DIR="${SYSTEM_DIR}/logs"
RUNTIME_DIR="${SYSTEM_DIR}/runtime/generated"
mkdir -p "$LOG_DIR" "$RUNTIME_DIR"
LOG_FILE="${LOG_DIR}/orchestrator-runtime-${RUN_DATE}.log"
RUNTIME_FILE="${RUNTIME_DIR}/orchestrator-run-${RUN_DATE}.json"
MANIFEST_FILE="${RUNTIME_DIR}/orchestrator-manifest-${RUN_DATE}.json"
RESULT_FILE="${RUNTIME_DIR}/orchestrator-result-${RUN_DATE}.json"

python3 - <<'PY' "$RUNTIME_FILE" "$MANIFEST_FILE" "$RESULT_FILE" "$RUN_DATE" "$RUN_TS"
import json
import sys
from pathlib import Path

runtime_file = Path(sys.argv[1])
manifest_file = Path(sys.argv[2])
result_file = Path(sys.argv[3])
run_date = sys.argv[4]
run_ts = sys.argv[5]
repo = Path.cwd()
template_path = repo / "agent-system" / "runtime" / "orchestrator-run-input.json"
payload = json.loads(template_path.read_text())
payload["run_date"] = run_date
runtime_file.write_text(json.dumps(payload, indent=2) + "\n")
manifest = {
    "run_date": run_date,
    "generated_at": run_ts,
    "runtime_payload": str(runtime_file),
    "result_file": str(result_file),
    "mode": "primary_orchestrator_runtime",
    "status": "prepared",
    "fallback": payload.get("fallback", {}),
}
manifest_file.write_text(json.dumps(manifest, indent=2) + "\n")
result = {
    "run_date": run_date,
    "generated_at": run_ts,
    "mode": "primary_orchestrator_runtime",
    "status": "prepared",
    "message": "Primary runtime payload prepared; execute through orchestrator session/tooling.",
    "runtime_payload": str(runtime_file),
    "manifest_file": str(manifest_file),
}
result_file.write_text(json.dumps(result, indent=2) + "\n")
PY

echo "[stockhive-orchestrator] run=${RUN_DATE} repo=${REPO_DIR}" | tee -a "$LOG_FILE"
echo "[stockhive-orchestrator] runtime_payload=${RUNTIME_FILE}" | tee -a "$LOG_FILE"
echo "[stockhive-orchestrator] manifest_file=${MANIFEST_FILE}" | tee -a "$LOG_FILE"
echo "[stockhive-orchestrator] result_file=${RESULT_FILE}" | tee -a "$LOG_FILE"
echo "[stockhive-orchestrator] primary runtime launcher prepared payload and manifest; execute via orchestrator session/tooling." | tee -a "$LOG_FILE"

echo "$RESULT_FILE"
