# StockHive 🐝📈

> **OpenClaw-native agent system — Nasdaq 100 Top 5 Weekly Buys, delivered daily to Telegram.**
>
> Platform: **Claude Cowork + OpenClaw**

StockHive is an **agent system** — the runtime composition of an orchestrator,
four ephemeral subagents, five skills, a scheduled task, and five MCP
connections — that every trading day at **17:00 ET (post-close)**:

1. Ranks the **top 10 Nasdaq-100 gainers** over a rolling 4-week window.
2. Spawns **ephemeral subagents in parallel** — technical, fundamental, sentiment — plus a data fetcher up front.
3. Aggregates their reports, runs `decision_engine.py`, and labels the market **BULLISH** or **BEARISH**.
4. Posts the **Top 5 Buy Candidates** — with rationale and exclusions — to a Telegram channel.

> An **agent system** is the runtime composition — orchestrator, subagents,
> skills, scheduled tasks — that actually does the work end-to-end. StockHive
> is not a distributable plugin package; it is a ready-to-register OpenClaw
> agent system whose composition is described by [`agent-system.json`](./agent-system.json)
> and whose artifacts live in [`agent-system/`](./agent-system).

---

## Architecture at a glance

| Stage | Actor | Persistence | Skill | MCPs |
|------:|-------|-------------|-------|------|
| 1. Cron | `nasdaq-daily-schedule.json` | — | — | — |
| 2. Orchestrate | `nasdaq-analyst-orchestrator` | **persistent** | — | all |
| 3a. Fetch & rank | `data-fetcher` | ephemeral | `stock-data-fetcher` | yfinance, nasdaq-data-link |
| 3b. Technicals | `technical-analyst` | ephemeral | `technical-indicators` | alpha-vantage, yfinance |
| 3c. Fundamentals | `fundamental-analyst` | ephemeral | `fundamental-snapshot` | yfinance |
| 3d. Sentiment | `sentiment-analyst` | ephemeral | `sentiment-analyzer` | news-api |
| 4. Decide | orchestrator → `decision_engine.py` | — | — | — |
| 5. Publish | `telegram-publisher` | ephemeral | `telegram-formatter` | telegram-bot |

**4** ephemeral subagents · **5** skills · **5** MCP servers · **17:00 ET** cron.

---

## Repository layout

```
stockHive/
├── README.md                          ← you are here (run guide)
├── agent-system.json                  ← agent system composition manifest
└── agent-system/                      ← the runtime composition itself
    ├── agents/                        ← orchestrator + 5 subagent specs
    ├── skills/                        ← 5 reusable SKILL.md capabilities
    ├── scheduled-tasks/               ← daily cron spec
    ├── scripts/                       ← runner + pick_top10 + decision_engine
    ├── mcps/                          ← MCP server connection config
    └── config/                        ← Nasdaq-100 tickers + .env.example
```

---

## 🏁 Running it in OpenClaw Chat

Walk through StockHive in **OpenClaw Chat** by pasting these commands **in
this order**. Each one is a real message you type in the OpenClaw chat UI.

### Prerequisites
- Claude Cowork with OpenClaw enabled.
- API keys: Alpha Vantage, Nasdaq Data Link, NewsAPI.
- A Telegram bot token + channel chat id (create via `@BotFather`).

### 0 · Clone the repo inside OpenClaw Chat

```
/bash git clone https://github.com/girisheduru/stockHive && cd stockHive
```

### 1 · Register the agent system

```
/agents register ./agent-system.json
```

OpenClaw reads the composition manifest and registers, in one step:
- the **orchestrator** (`nasdaq-analyst-orchestrator`, persistent)
- the **5 ephemeral subagents** (`data-fetcher`, `technical-analyst`, `fundamental-analyst`, `sentiment-analyst`, `telegram-publisher`)
- the **5 skills** under `agent-system/skills/`
- the **scheduled task** `nasdaq-daily-top5-buys`
- the **MCP connections** under `agent-system/mcps/mcp-config.json`

Verify:

```
/agents list
/skills list
/tasks list
```

### 2 · Configure secrets

```
/bash cp agent-system/config/.env.example agent-system/config/.env && $EDITOR agent-system/config/.env
```

Fill in `ALPHA_VANTAGE_API_KEY`, `NASDAQ_DATA_LINK_API_KEY`, `NEWS_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

### 3 · Connect the MCP servers

```
/mcp connect ./agent-system/mcps/mcp-config.json
```

OpenClaw spawns the five MCP servers: `yfinance-mcp`, `alpha-vantage-mcp`, `nasdaq-data-link-mcp`, `news-api-mcp`, `telegram-bot-mcp`.

Verify:

```
/mcp list
```

### 4 · Smoke-test each subagent (one-at-a-time — shows off ephemeral spawn/teardown)

```
/agent run data-fetcher --input "Use config/nasdaq100-tickers.json and return the top 10 by 4-week return."
/agent run technical-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
/agent run fundamental-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
/agent run sentiment-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```

Each spawns, runs, replies with strict JSON, and tears down — a great live demo of ephemeral-subagent lifecycle.

### 5 · Full agent system on demand (manual trigger of the cron task)

```
/task run nasdaq-daily-top5-buys
```

In this workspace, the scheduled path now uses the Yahoo-based live runner via:
- `agent-system/scripts/nasdaq-daily-run.sh`
- `openclawMVP/scripts/run_live_option_b.py`

It loads `agent-system/config/.env`, fetches live market/news data, runs the current decision engine, and publishes to Telegram unless `STOCKHIVE_PUBLISH_MODE=dry-run` is set.

### 6 · Inspect the Telegram output

Open your Telegram channel — you'll see the canonical StockHive alert:

```
** Nasdaq 100 — Daily Top 5 Buys **
Date: 18 Apr 2026  |  Close + 1h

Market view:  [ BULLISH ]
Breadth 8/10 up, RSI avg 62, sentiment +0.42

Top 5 Buy Candidates
--------------------
1. AVGO  +18.1%  RSI 66  PE 42
   Tech: MACD>0, above SMA50. Fund: strong.
...
--
OpenClaw  |  Daily 17:00 ET
```

### 7 · (Optional) Enable the recurring schedule

```
/schedule enable nasdaq-daily-top5-buys
```

From then on OpenClaw fires the agent system every weekday at **17:00 America/New_York**.

Pause with:

```
/schedule disable nasdaq-daily-top5-buys
```

---

## Local MVP mode

For this workspace, the local runnable MVP is isolated under `openclawMVP/` so it stays separate from the main OpenClaw agent-system definition.

### Run the local MVP

```bash
cd stockHive
python3 openclawMVP/scripts/run_local_mvp.py
```

This produces deterministic artifacts under `openclawMVP/output/`:
- `top10.json`
- `technical.json`
- `fundamental.json`
- `sentiment.json`
- `merged.json`
- `decision.json`
- `telegram_message.md`
- `orchestrator_result.json`

### Run tests

```bash
cd stockHive
python3 openclawMVP/tests/run_tests.py
```

If `pytest` is available in your environment, you can also run:

```bash
python3 -m pytest openclawMVP/tests/test_agent_system.py
```

The local MVP preserves the same pipeline shape as the intended OpenClaw setup:
- top-10 selection
- parallel analyst stages
- deterministic decision engine
- formatted publish output

## Design notes

- **Agent system, not a plugin.** StockHive is the *runtime composition* — orchestrator + subagents + skills + scheduled task — registered directly with OpenClaw. One manifest ([`agent-system.json`](./agent-system.json)) wires every piece.
- **Ephemeral subagents, by design.** Each analyst spins up for one run with its own context, does its job, and is torn down on reply — cheap, isolated, and audit-friendly.
- **Parallel fan-out.** The orchestrator dispatches technical / fundamental / sentiment in a single turn, so the whole fan-out round-trips in a few seconds of wall time.
- **Composable skills.** Every skill (`stock-data-fetcher`, `technical-indicators`, …) is independently triggerable outside the pipeline — reusable across other OpenClaw agent systems.
- **Deterministic decision layer.** `decision_engine.py` is plain Python — no LLM in the critical scoring path, so the BULLISH/BEARISH call is reproducible and unit-testable.
- **One-command register, one-command run.** `/agents register` then `/task run` — nothing else.

---

## Troubleshooting quick-ref

| Symptom | Fix |
|---|---|
| `agent: not found` | Re-run `/agents register ./agent-system.json`. |
| `mcp: server not found` | Re-run `/mcp connect ./agent-system/mcps/mcp-config.json`. |
| Orchestrator stalls at stage 1 | Check `ALPHA_VANTAGE_API_KEY` / `NASDAQ_DATA_LINK_API_KEY`. |
| No Telegram message | Verify `TELEGRAM_CHAT_ID` is a channel (`-100…` prefix) and the bot is an admin. |
| Top 5 looks thin | Many tickers excluded for RSI>70 — that's the overbought guardrail firing. |

---

## License

MIT © 2026 Girish Eduru.
