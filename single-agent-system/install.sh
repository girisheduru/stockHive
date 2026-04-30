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

read -r -p "Telegram Bot Token: " TELEGRAM_BOT_TOKEN
read -r -p "Telegram Chat ID (target chat/user/channel): " TELEGRAM_CHAT_ID

if [[ -z "$TELEGRAM_BOT_TOKEN" || -z "$TELEGRAM_CHAT_ID" ]]; then
  echo "Both TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required."
  exit 1
fi

cat > "$SINGLE_ENV" <<ENV
TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
ENV

if [[ -f "$BASE_ENV" ]]; then
  if grep -q '^TELEGRAM_BOT_TOKEN=' "$BASE_ENV"; then
    sed -i.bak "s#^TELEGRAM_BOT_TOKEN=.*#TELEGRAM_BOT_TOKEN=\"$TELEGRAM_BOT_TOKEN\"#" "$BASE_ENV"
  else
    printf '\nTELEGRAM_BOT_TOKEN="%s"\n' "$TELEGRAM_BOT_TOKEN" >> "$BASE_ENV"
  fi

  if grep -q '^TELEGRAM_CHAT_ID=' "$BASE_ENV"; then
    sed -i.bak "s#^TELEGRAM_CHAT_ID=.*#TELEGRAM_CHAT_ID=\"$TELEGRAM_CHAT_ID\"#" "$BASE_ENV"
  else
    printf 'TELEGRAM_CHAT_ID="%s"\n' "$TELEGRAM_CHAT_ID" >> "$BASE_ENV"
  fi
fi

printf "\nWrote: %s\n" "$SINGLE_ENV"
printf "Updated: %s (Telegram association)\n" "$BASE_ENV"
printf "\nLoad env vars before connecting MCP:\n"
printf "  set -a; source agent-system/config/.env; source single-agent-system/.env; set +a\n\n"
printf "Persistent agent behavior: keep OpenClaw daemon running; this orchestrator stays idle and waits for inbound events.\n"
