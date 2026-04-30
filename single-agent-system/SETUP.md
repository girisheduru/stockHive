# Single Agent System Setup (Telegram Single-Ticker)

This setup follows the same registration style as `stockhive-openclaw-setup-fixed.md`.

## 1. Prerequisites

Make sure the base StockHive system is already present and configured:
- `agent-system/` exists
- MCP config exists at `agent-system/mcps/mcp-config.json`
- env vars are configured (Alpha Vantage, Nasdaq Data Link, News API, Telegram)
- OpenClaw daemon is running (persistent agent stays alive and waits for inbound events)

## 2. Install and Associate Telegram Credentials

From repo root run:

```bash
bash single-agent-system/install.sh
```

This installer asks for:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

and associates them by writing:
- `single-agent-system/.env`
- `agent-system/config/.env` (Telegram fields)

## 3. Confirm files

```bash
ls single-agent-system
ls single-agent-system/agents
ls single-agent-system/runtime
ls single-agent-system/scripts
```

Expected key files:
- `single-agent-system/agent-system.json`
- `single-agent-system/agents/stockhive-telegram-trigger-orchestrator.md`
- `single-agent-system/runtime/telegram-single-run-input.json`
- `single-agent-system/scripts/extract_ticker.py`
- `single-agent-system/install.sh`

## 4. Load Env

```bash
set -a
source agent-system/config/.env
source single-agent-system/.env
set +a
```

## 5. Register Components Individually (No `/agents register`)

From repo root, add each required agent explicitly:

```bash
openclaw agents add stockhive-telegram-trigger-orchestrator \
  --workspace "$PWD" \
  --non-interactive
```

```bash
openclaw agents add technical-analyst \
  --workspace "$PWD" \
  --non-interactive
```

```bash
openclaw agents add fundamental-analyst \
  --workspace "$PWD" \
  --non-interactive
```

```bash
openclaw agents add sentiment-analyst \
  --workspace "$PWD" \
  --non-interactive
```

```bash
openclaw agents add telegram-publisher \
  --workspace "$PWD" \
  --non-interactive
```

Connect MCPs (uses existing repo MCP config):

```bash
/mcp connect ./agent-system/mcps/mcp-config.json
```

Verify:

```bash
/agents list
/mcp list
```

## 6. Runtime behavior (always-on, no schedule)

When a Telegram message arrives, trigger `stockhive-telegram-trigger-orchestrator` immediately with event payload:
- `chat_id`
- `message_id`
- `from_user_id`
- `message_text`

This flow is event-driven and replies to the same chat/person context. It does not use polling or cron.

## 7. Manual test

Send a message in Telegram like:
- `Analyze NVDA`
- `AAPL`
- `check msft`

Then trigger:

```bash
/agent run stockhive-telegram-trigger-orchestrator --input '{"trigger":"telegram_webhook_event","event_payload":{"chat_id":"-1001234567890","message_id":"12345","from_user_id":"777777","message_text":"Analyze NVDA"}}'
```

## 8. Runtime compatibility note

If your OpenClaw version does not fully apply markdown identity on `agents add`, prefix the run prompt with:

```text
Read and follow single-agent-system/agents/stockhive-telegram-trigger-orchestrator.md.
```

This is the same compatibility fallback used in `stockhive-openclaw-setup-fixed.md`.

Do the same for specialists if needed:

```text
Read and follow agent-system/agents/technical-analyst.md.
Read and follow agent-system/agents/fundamental-analyst.md.
Read and follow agent-system/agents/sentiment-analyst.md.
Read and follow agent-system/agents/telegram-publisher.md.
```
