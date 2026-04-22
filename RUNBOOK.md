# StockHive — OpenClaw Chat Runbook

Step-by-step sequence to bring up the StockHive agent system from a fresh
clone. Paste each block into **OpenClaw Chat** in the order shown. Do not
skip ahead — each step assumes the previous one succeeded.

---

## Prerequisites

You can collect these in advance, or let the orchestrator walk you through
them interactively in **Step 3** — whichever you prefer.

Before step 1, have (or be ready to obtain) these:

| Item | How to get it |
|---|---|
| Claude Cowork with OpenClaw enabled | OpenClaw onboarding |
| `ALPHA_VANTAGE_API_KEY` | https://www.alphavantage.co/support/#api-key |
| `NASDAQ_DATA_LINK_API_KEY` | https://data.nasdaq.com/account/api |
| `NEWS_API_KEY` | https://newsapi.org/register |
| `TELEGRAM_BOT_TOKEN` | Chat with `@BotFather` → `/newbot` |
| `TELEGRAM_CHAT_ID` | Add the bot to your channel as admin; resolve the `-100…` chat id |

---

## Step 1 — Clone the repo

```
/bash git clone https://github.com/girisheduru/stockHive && cd stockHive
```

Expected: `stockHive/` with `agent-system.json` at the root and an `agent-system/` directory alongside it.

---

## Step 2 — Register the agent system

```
/agents register ./agent-system.json
```

OpenClaw reads the composition manifest and registers, in one step:

- **Orchestrator** — `nasdaq-analyst-orchestrator` (persistent)
- **Ephemeral subagents** — `data-fetcher`, `technical-analyst`, `fundamental-analyst`, `sentiment-analyst`, `telegram-publisher`
- **Skills** — `stock-data-fetcher`, `technical-indicators`, `fundamental-snapshot`, `sentiment-analyzer`, `telegram-formatter`
- **Scheduled task** — `nasdaq-daily-top5-buys`
- **MCP connections** — declared under `agent-system/mcps/mcp-config.json`

Verify:

```
/agents list
/skills list
/tasks list
```

You should see the orchestrator plus 5 subagents, 5 skills, and 1 scheduled task.

---

## Step 3 — Configure secrets (interactive)

StockHive needs five secrets before it can run. Kick off the interactive
prompt — OpenClaw Chat will ask you for each value one at a time,
validate it, and write it into `agent-system/config/.env`.

```
/bash cp agent-system/config/.env.example agent-system/config/.env
```

Then paste this **one** message into the chat:

```
Read agent-system/config/.env.example and for every blank key, ask me
for the value one at a time. For each key:
  1. Show the key name and a one-line description of what it is / where
     to obtain it (use the table in RUNBOOK.md "Prerequisites" as the
     reference).
  2. Wait for my reply.
  3. Validate it (non-empty; TELEGRAM_CHAT_ID must start with "-100";
     TELEGRAM_BOT_TOKEN must match "<digits>:<alphanum>"; API keys must
     be at least 16 chars).
  4. Write the key=value into agent-system/config/.env, preserving any
     comments and the existing key order. Never echo previously entered
     secrets back to me.
  5. Move on to the next blank key.
When all keys are filled, run:
    /bash grep -c '=.\+' agent-system/config/.env
and confirm the count matches the number of required keys.
```

The orchestrator will prompt you in order for:

| Key | What it is |
|---|---|
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage RSI/MACD data — https://www.alphavantage.co/support/#api-key |
| `NASDAQ_DATA_LINK_API_KEY` | Nasdaq Data Link EOD fallback — https://data.nasdaq.com/account/api |
| `NEWS_API_KEY` | NewsAPI headlines for sentiment — https://newsapi.org/register |
| `TELEGRAM_BOT_TOKEN` | From `@BotFather` → `/newbot` |
| `TELEGRAM_CHAT_ID` | Your channel's `-100…` chat id; the bot must be a channel admin |

Ground rules for you while answering:

- Paste the raw value exactly (no quotes, no leading/trailing spaces).
- If you don't have a key yet, reply `skip` — that key will stay blank and
  StockHive will run in degraded mode (the subagent that needs it will
  return `confidence:"low"` and the orchestrator will exclude the ticker).
- To abort at any point, reply `stop` and no further writes are made.

### Alternative — fill the file manually

If you prefer not to go interactive, just open the file and fill all five
values by hand:

```
/bash $EDITOR agent-system/config/.env
/bash grep -c '=.\+' agent-system/config/.env   # sanity-check: 5+ matches
```

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

All five should report `status: running`.

---

## Step 5 — Smoke-test the ephemeral subagents (one at a time)

These calls exercise spawn-run-teardown for each analyst in isolation. Each returns strict JSON and exits.

**5a — Data fetcher**
```
/agent run data-fetcher --input "Use config/nasdaq100-tickers.json and return the top 10 by 4-week return."
```

**5b — Technical analyst**
```
/agent run technical-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```

**5c — Fundamental analyst**
```
/agent run fundamental-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```

**5d — Sentiment analyst**
```
/agent run sentiment-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```

Expected: each reply is a JSON array matching the output shape documented in the corresponding `agent-system/skills/<skill>/SKILL.md`.

---

## Step 6 — Run the full agent system on demand

This is exactly what the scheduler fires daily at 17:00 ET.

```
/task run nasdaq-daily-top5-buys
```

What you'll see in the log stream:

1. `[STAGE 1/6]` orchestrator selects the top 10 gainers.
2. `[STAGE 2/6]` three ephemeral subagents dispatched **in parallel**.
3. `[STAGE 3/6]` aggregated report.
4. `[STAGE 4/6]` `decision_engine.py` returns `market_view` + `top5`.
5. `[STAGE 5/6]` `telegram-publisher` formats and sends the alert.
6. `[STAGE 6/6]` Telegram message id echoed back.

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

From here on OpenClaw fires the agent system every weekday at **17:00 America/New_York**.

Pause any time with:

```
/schedule disable nasdaq-daily-top5-buys
```

---

## Step 9 — Tail logs (optional)

```
/bash tail -n 100 -f agent-system/logs/run-$(TZ=America/New_York date +%Y-%m-%d).log
```

---

## Teardown

To unregister the agent system and stop all MCP servers:

```
/schedule disable nasdaq-daily-top5-buys
/mcp disconnect --all-from ./agent-system/mcps/mcp-config.json
/agents unregister ./agent-system.json
```

---

## Command reference

| Command | Purpose |
|---|---|
| `/agents register <manifest>` | Load the composition manifest, register every agent/skill/task/mcp it declares |
| `/agents list` / `/skills list` / `/tasks list` | Inspect what's currently registered |
| `/mcp connect <config>` | Spawn MCP servers from a config file |
| `/mcp list` | Show MCP server status |
| `/agent run <name> --input <json>` | One-shot invoke of an ephemeral subagent |
| `/task run <task_id>` | Fire a scheduled task manually (off-schedule) |
| `/schedule enable <task_id>` / `/schedule disable <task_id>` | Control the cron for a scheduled task |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `agent: not found` | Manifest not registered in this session | Re-run step 2 |
| `mcp: server not found` | MCP server didn't start | Re-run step 4; `/mcp logs <server>` |
| Orchestrator stalls at stage 1 | Missing market-data keys | Check `ALPHA_VANTAGE_API_KEY` / `NASDAQ_DATA_LINK_API_KEY` in `.env` |
| No Telegram message | Bad chat id or bot perms | `TELEGRAM_CHAT_ID` must be the `-100…` channel id and the bot must be a channel admin |
| Top 5 looks thin / empty | RSI>70 or PE>80 exclusions fired on many tickers | Expected — these are the overbought / stretched guardrails |
| `permission denied` running `nasdaq-daily-run.sh` | File not executable | `/bash chmod +x agent-system/scripts/*.sh agent-system/scripts/*.py` |
