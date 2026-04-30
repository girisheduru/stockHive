# Single Agent System Setup (Telegram Single-Ticker)

This setup follows the same registration style as `stockhive-openclaw-setup-fixed.md`.

## 1. Prerequisites

Make sure the base StockHive system is already present and configured:
- `agent-system/` exists
- MCP config exists at `agent-system/mcps/mcp-config.json`
- env vars are configured (Alpha Vantage, Nasdaq Data Link, News API, Telegram)

## 2. Confirm files

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

## 3. Register orchestrator (same pattern)

From repo root:

```bash
openclaw agents add stockhive-telegram-trigger-orchestrator \
  --workspace "$PWD" \
  --non-interactive
```

## 4. Register system manifest

```bash
/agents register ./single-agent-system/agent-system.json
```

Verify:

```bash
/agents list
```

## 5. Wire inbound Telegram event trigger (no schedule)

When a Telegram message arrives, trigger `stockhive-telegram-trigger-orchestrator` immediately with event payload:
- `chat_id`
- `message_id`
- `from_user_id`
- `message_text`

This flow is event-driven and replies to the same chat/person context. It does not use polling or cron.

## 6. Manual test

Send a message in Telegram like:
- `Analyze NVDA`
- `AAPL`
- `check msft`

Then trigger:

```bash
/agent run stockhive-telegram-trigger-orchestrator --input '{"trigger":"telegram_webhook_event","event_payload":{"chat_id":"-1001234567890","message_id":"12345","from_user_id":"777777","message_text":"Analyze NVDA"}}'
```

## 7. Runtime compatibility note

If your OpenClaw version does not fully apply markdown identity on `agents add`, prefix the run prompt with:

```text
Read and follow single-agent-system/agents/stockhive-telegram-trigger-orchestrator.md.
```

This is the same compatibility fallback used in `stockhive-openclaw-setup-fixed.md`.
