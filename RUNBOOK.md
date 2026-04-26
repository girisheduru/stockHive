# StockHive — OpenClaw Chat Runbook

Step-by-step walkthrough to bring up the StockHive agent system from a fresh clone. Paste each block into **OpenClaw Chat** in the order shown. Do not skip ahead — each step assumes the previous one succeeded.

---

## Prerequisites

Collect these before starting, or let the orchestrator walk you through them interactively in Step 3.

| Item | How to obtain |
|------|--------------|
| Claude Cowork with OpenClaw enabled | OpenClaw onboarding |
| `ALPHA_VANTAGE_API_KEY` | [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key) |
| `NASDAQ_DATA_LINK_API_KEY` | [data.nasdaq.com/account/api](https://data.nasdaq.com/account/api) |
| `NEWS_API_KEY` | [newsapi.org/register](https://newsapi.org/register) |
| `TELEGRAM_BOT_TOKEN` | Chat `@BotFather` → `/newbot` |
| `TELEGRAM_CHAT_ID` | Add the bot to your channel as admin; resolve the `-100…` chat id |

---

## Step 1 — Clone the repo

```
/bash git clone https://github.com/girisheduru/stockHive && cd stockHive
```

**Expected:** `stockHive/` directory with `agent-system.json` at the root and `agent-system/` alongside it. No other setup needed.

---

## Step 2 — Register the agent system

```
/agents register ./agent-system.json
```

OpenClaw reads the composition manifest and registers everything in one step:

- **Orchestrator** — `stockhive-orchestrator` (persistent)
- **Ephemeral subagents** — `data-fetcher`, `technical-analyst`, `fundamental-analyst`, `sentiment-analyst`, `telegram-publisher`
- **Skills** — `stock-data-fetcher`, `technical-indicators`, `fundamental-snapshot`, `sentiment-analyzer`, `telegram-formatter`
- **Scheduled task** — `nasdaq-daily-top5-buys`
- **MCP connection config** — `agent-system/mcps/mcp-config.json`

Verify everything registered correctly:

```
/agents list
/skills list
/tasks list
```

You should see: 1 persistent orchestrator, 5 subagents, 5 skills, 1 scheduled task.

---

## Step 3 — Configure secrets

```
/bash cp agent-system/config/.env.example agent-system/config/.env
```

### Option A — Interactive (recommended for a live demo)

Paste this message into OpenClaw Chat and the orchestrator will prompt you for each key one at a time, validate it, and write it into `.env`:

```
Read agent-system/config/.env.example and for every blank key, ask me
for the value one at a time. For each key:
  1. Show the key name and a one-line description of what it is and where
     to obtain it (use the Prerequisites table in RUNBOOK.md as the reference).
  2. Wait for my reply.
  3. Validate it (non-empty; TELEGRAM_CHAT_ID must start with "-100";
     TELEGRAM_BOT_TOKEN must match "<digits>:<alphanum>"; API keys must
     be at least 16 characters).
  4. Write the key=value into agent-system/config/.env, preserving any
     comments and the existing key order. Never echo previously entered
     secrets back to me.
  5. Move on to the next blank key.
When all keys are filled, run:
    /bash grep -c '=.\+' agent-system/config/.env
and confirm the count matches the number of required keys.
```

Reply rules while answering:
- Paste the raw value exactly (no quotes, no leading/trailing spaces).
- Reply `skip` if you don't have a key yet — that subagent will return `confidence:"low"` and its tickers will be excluded from the Top 5.
- Reply `stop` to abort at any point without further writes.

### Option B — Manual

```
/bash $EDITOR agent-system/config/.env
/bash grep -c '=.\+' agent-system/config/.env
```

The count should be 5.

---

## Step 4 — Connect the MCP servers

```
/mcp connect ./agent-system/mcps/mcp-config.json
```

OpenClaw spawns: `yfinance-mcp`, `alpha-vantage-mcp`, `nasdaq-data-link-mcp`, `news-api-mcp`, `telegram-bot-mcp`.

Verify:

```
/mcp list
```

All five should report `status: running`. If any are not running, check the relevant API key in `.env` and re-run the connect command.

---

## Step 5 — Smoke-test the ephemeral subagents

These calls exercise the full spawn → run → teardown lifecycle for each specialist in isolation. Each returns strict JSON and exits. This is the best part to demo live — you can see each subagent come up and disappear.

**5a — Data fetcher** (selects 10 tickers from the Nasdaq-100 universe)

```
/agent run data-fetcher --input '{"universe_file":"agent-system/config/nasdaq100-tickers.json","selection_mode":"deterministic_daily_random_sample","target_count":10,"must_return_exactly":true}'
```

Expected: JSON array of exactly 10 objects, each with `ticker`, `return_4w`, `last_close`.

**5b — Technical analyst**

```
/agent run technical-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```

Expected: JSON array with RSI, MACD histogram, SMA20/50, close, signal, note per ticker.

**5c — Fundamental analyst**

```
/agent run fundamental-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```

Expected: JSON array with PE, market cap, sector, earnings health, note per ticker.

**5d — Sentiment analyst**

```
/agent run sentiment-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```

Expected: JSON array with sentiment score, top theme, headline count per ticker.

Output shapes for each specialist are documented in the corresponding `agent-system/skills/<skill>/SKILL.md`.

---

## Step 6 — Run the full pipeline on demand

This triggers the exact same execution path the daily scheduler fires at 17:00 ET.

```
/task run nasdaq-daily-top5-buys
```

Watch the orchestrator-native pipeline stages stream through the run:

| Stage | What you see |
|-------|-------------|
| `[STAGE 1/6]` | Orchestrator spawns `data-fetcher`; gets back deterministic 10-ticker sample |
| `[STAGE 2/6]` | Three specialist subagents dispatched **in parallel** |
| `[STAGE 3/6]` | Orchestrator merges all three structured outputs by ticker |
| `[STAGE 4/6]` | `decision_engine.py` returns `market_view` + `top5` + `excluded` |
| `[STAGE 5/6]` | `telegram-publisher` formats and sends the Telegram alert |
| `[STAGE 6/6]` | Final JSON run summary echoed (includes Telegram message id) |

Total wall time should be well under 5 minutes.

---

## Step 7 — Verify the Telegram alert

Open your Telegram channel. The message should look like:

```
** Nasdaq 100 — Daily Top 5 Buys **
Date: 22 Apr 2026  |  Close + 1h

Market view:  [ BULLISH ]
Breadth 8/10 up, RSI avg 62, sentiment +0.42

Top 5 Buy Candidates
--------------------
1. AVGO  +18.1%  RSI 66  PE 42
   Tech: MACD>0, above SMA50. Fund: strong.
2. AMD   +17.3%  RSI 63  PE 31
   Tech: breakout. Fund: earnings beat.
...
--
OpenClaw  |  Daily 17:00 ET
```

---

## Step 8 — Enable the recurring schedule

```
/schedule enable nasdaq-daily-top5-buys
```

From here on OpenClaw fires the pipeline every weekday at **17:00 America/New_York** (post-market close).

Pause any time with:

```
/schedule disable nasdaq-daily-top5-buys
```

---

## Step 9 — Inspect runtime output (optional)

The cleaned OpenClaw-native version does not require a shell-runtime log file to function.

Use OpenClaw task and agent output directly to inspect runs.

---

## Teardown

To fully unregister the agent system and stop all MCP servers:

```
/schedule disable nasdaq-daily-top5-buys
/mcp disconnect --all-from ./agent-system/mcps/mcp-config.json
/agents unregister ./agent-system.json
```

---

## Command reference

| Command | What it does |
|---------|-------------|
| `/agents register <manifest>` | Load a composition manifest; register every agent, skill, task, and MCP it declares |
| `/agents list` / `/skills list` / `/tasks list` | Inspect currently registered components |
| `/mcp connect <config>` | Spawn MCP servers from a config file |
| `/mcp list` | Show MCP server status |
| `/mcp logs <server>` | Show logs for a specific MCP server |
| `/agent run <name> --input <json>` | One-shot invoke of an ephemeral subagent |
| `/task run <task_id>` | Fire a scheduled task manually, off-schedule |
| `/schedule enable <task_id>` | Activate the cron for a task |
| `/schedule disable <task_id>` | Pause the cron for a task |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `agent: not found` | Manifest not registered in this session | Re-run step 2 |
| `mcp: server not found` | MCP server didn't start | Re-run step 4; check `/mcp logs <server>` |
| Orchestrator stalls at stage 1 | Missing market-data API key | Check `ALPHA_VANTAGE_API_KEY` / `NASDAQ_DATA_LINK_API_KEY` in `.env` |
| No Telegram message | Bad chat id or bot not admin | `TELEGRAM_CHAT_ID` must be `-100…` and the bot must be a channel admin |
| Top 5 looks thin or empty | Overbought/overvalued guardrails fired | Expected — tickers with RSI > 70 or PE > 80 are excluded by `decision_engine.py` |
| `permission denied` on helper scripts | Script not executable | `/bash chmod +x agent-system/scripts/*.py` |
| All candidates excluded | Broad market overbought | State this explicitly — it is the correct guardrail behaviour, not a bug |
