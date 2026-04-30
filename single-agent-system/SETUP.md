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
ls single-agent-system/scheduled-tasks
ls single-agent-system/scripts
```

Expected key files:
- `single-agent-system/agent-system.json`
- `single-agent-system/agents/stockhive-telegram-trigger-orchestrator.md`
- `single-agent-system/runtime/telegram-single-run-input.json`
- `single-agent-system/scheduled-tasks/telegram-single-ticker-poll.json`
- `single-agent-system/scripts/extract_ticker.py`

## 3. Register orchestrator (same pattern)

From repo root:

```bash
openclaw agents add stockhive-telegram-trigger-orchestrator \
  --workspace "$PWD" \
  --non-interactive
```

## 4. Register system manifest and task

```bash
/agents register ./single-agent-system/agent-system.json
```

Verify:

```bash
/agents list
/tasks list
```

## 5. Enable schedule alongside existing daily schedule

```bash
/schedule enable telegram-single-ticker-analysis
```

This runs every 5 minutes on weekdays and does not disable `nasdaq-daily-top5-buys`.

## 6. Manual test

Send a message in Telegram like:
- `Analyze NVDA`
- `AAPL`
- `check msft`

Then trigger:

```bash
/task run telegram-single-ticker-analysis
```

## 7. Runtime compatibility note

If your OpenClaw version does not fully apply markdown identity on `agents add`, prefix the run prompt with:

```text
Read and follow single-agent-system/agents/stockhive-telegram-trigger-orchestrator.md.
```

This is the same compatibility fallback used in `stockhive-openclaw-setup-fixed.md`.
