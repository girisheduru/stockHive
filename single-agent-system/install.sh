#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SINGLE_ENV="$ROOT_DIR/single-agent-system/.env"
BASE_ENV="$ROOT_DIR/agent-system/config/.env"
BASE_ENV_EXAMPLE="$ROOT_DIR/agent-system/config/.env.example"

mkdir -p "$ROOT_DIR/single-agent-system"
mkdir -p "$ROOT_DIR/agent-system/config"

if [[ ! -f "$BASE_ENV" && -f "$BASE_ENV_EXAMPLE" ]]; then
  cp "$BASE_ENV_EXAMPLE" "$BASE_ENV"
fi

printf "\nStockHive Single-Agent Telegram Installer\n"
printf "This will associate one bot token + chat id for replies.\n\n"

# Non-interactive convenience:
# - If single-agent-system/.env already exists, reuse it.
# - Otherwise, prompt for values (token input is hidden).
if [[ -f "$SINGLE_ENV" ]]; then
  # shellcheck disable=SC1090
  source "$SINGLE_ENV" || true
fi

if [[ -z "${SINGLE_TELEGRAM_BOT_TOKEN:-}" ]]; then
  read -r -s -p "Telegram Bot Token: " SINGLE_TELEGRAM_BOT_TOKEN
  printf "\n"
fi

if [[ -z "${SINGLE_TELEGRAM_CHAT_ID:-}" ]]; then
  read -r -p "Telegram Chat ID (target chat/user/channel): " SINGLE_TELEGRAM_CHAT_ID
fi

if [[ -z "$SINGLE_TELEGRAM_BOT_TOKEN" || -z "$SINGLE_TELEGRAM_CHAT_ID" ]]; then
  echo "Both SINGLE_TELEGRAM_BOT_TOKEN and SINGLE_TELEGRAM_CHAT_ID are required."
  exit 1
fi

cat > "$SINGLE_ENV" <<ENV
SINGLE_TELEGRAM_BOT_TOKEN="$SINGLE_TELEGRAM_BOT_TOKEN"
SINGLE_TELEGRAM_CHAT_ID="$SINGLE_TELEGRAM_CHAT_ID"
ENV

printf "\nWrote: %s\n" "$SINGLE_ENV"
printf "Base system env left unchanged: %s\n" "$BASE_ENV"
printf "\nLoad env vars before connecting MCP:\n"
printf "  set -a; source agent-system/config/.env; source single-agent-system/.env; set +a\n\n"
printf "Persistent agent behavior: keep OpenClaw daemon running; this orchestrator stays idle and waits for inbound events.\n"
