# StockHive 🐝📈

> **OpenClaw native agent — Nasdaq 100 Top 5 Weekly Buys, delivered daily to Telegram.**
>
> Hackathon submission · Platform: **Claude Cowork + OpenClaw Plugin**

StockHive is a fully automated, multi-agent pipeline that every trading day at **17:00 ET (post-close)**:

1. Ranks the **top 10 Nasdaq-100 gainers** over a rolling 4-week window.
2. Spawns **4 ephemeral subagents in parallel** — technical, fundamental, sentiment, plus the data fetcher.
3. Aggregates their reports, runs `decision_engine.py`, and labels the market **BULLISH** or **BEARISH**.
4. Posts the **Top 5 Buy Candidates** — with rationale and exclusions — to a Telegram channel.

The entire system ships as one OpenClaw plugin: [`nasdaq-top-movers.plugin/`](./nasdaq-top-movers.plugin).

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

See the source: [architecture PPT reference](./nasdaq-top-movers.plugin/README.md).

---

## Repository layout

```
stockHive/
├── README.md                       ← you are here (hackathon run guide)
└── nasdaq-top-movers.plugin/       ← the OpenClaw plugin
    ├── plugin.json                 ← manifest
    ├── agents/                     ← orchestrator + 5 subagent prompts
    ├── skills/                     ← 5 reusable SKILL.md capabilities
    ├── scheduled-tasks/            ← daily cron spec
    ├── scripts/                    ← runner + pick_top10 + decision_engine
    ├── mcps/                       ← MCP server connection config
    └── config/                     ← Nasdaq-100 tickers + .env.example
```

---

## 🏁 Running it in OpenClaw Chat — hackathon demo sequence

The judges (or you) can walk through StockHive in **OpenClaw Chat** with these steps, copy-pasted **in this order**. Every step is a real message you type in the OpenClaw chat UI.

### Prerequisites
- Claude Cowork with the OpenClaw plugin enabled.
- API keys: Alpha Vantage, Nasdaq Data Link, NewsAPI.
- A Telegram bot token + channel chat id (create via `@BotFather`).

### 0 · Clone the repo inside OpenClaw Chat

```
/bash git clone https://github.com/girisheduru/stockHive && cd stockHive
```

### 1 · Install the plugin

```
/plugin install ./nasdaq-top-movers.plugin
```

OpenClaw reads `plugin.json`, registers the orchestrator, all 5 subagents, all 5 skills, the MCP connections, and the daily scheduled task.

### 2 · Configure secrets

```
/bash cp nasdaq-top-movers.plugin/config/.env.example nasdaq-top-movers.plugin/config/.env && $EDITOR nasdaq-top-movers.plugin/config/.env
```

Fill in `ALPHA_VANTAGE_API_KEY`, `NASDAQ_DATA_LINK_API_KEY`, `NEWS_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

### 3 · Connect the MCP servers

```
/mcp connect ./nasdaq-top-movers.plugin/mcps/mcp-config.json
```

OpenClaw spawns the five MCP servers: `yfinance-mcp`, `alpha-vantage-mcp`, `nasdaq-data-link-mcp`, `news-api-mcp`, `telegram-bot-mcp`.

Verify with:

```
/mcp list
```

### 4 · Smoke-test each subagent (one-at-a-time, shows off ephemeral spawn/teardown)

```
/agent run data-fetcher --input "Use config/nasdaq100-tickers.json and return the top 10 by 4-week return."
/agent run technical-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
/agent run fundamental-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
/agent run sentiment-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```

Each spawns, runs, replies with strict JSON, and tears down — great live demo.

### 5 · Full pipeline on demand (manual trigger of the cron task)

```
/task run nasdaq-daily-top5-buys
```

This is exactly what the scheduler fires at 17:00 ET. Watch the orchestrator:
- select the top 10 (stage 1 log line)
- dispatch 3 ephemeral subagents **in parallel** (stage 2–3)
- pipe the merged JSON through `decision_engine.py` (stage 4)
- hand off to `telegram-publisher` which posts to your channel (stage 5)

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

From then on OpenClaw fires the pipeline every weekday at **17:00 America/New_York**.

To pause during the demo:

```
/schedule disable nasdaq-daily-top5-buys
```

---

## 🎤 Hackathon talking points

- **Ephemeral subagents, by design.** Each analyst spins up for one run with its own context, does its job, and is torn down on reply — cheap, isolated, and audit-friendly.
- **Parallel fan-out.** The orchestrator dispatches technical / fundamental / sentiment in a single turn, so the whole fan-out round-trips in a few seconds of wall time.
- **Composable skills.** Every skill (`stock-data-fetcher`, `technical-indicators`, …) is independently triggerable outside the pipeline — reusable in other OpenClaw workflows.
- **Deterministic decision layer.** `decision_engine.py` is plain Python — no LLM in the critical scoring path, so the BULLISH/BEARISH call is reproducible and unit-testable.
- **One-command install, one-command run.** `/plugin install` then `/task run` — nothing else.

---

## Troubleshooting quick-ref

| Symptom | Fix |
|---|---|
| `mcp: server not found` | Re-run `/mcp connect ./nasdaq-top-movers.plugin/mcps/mcp-config.json`. |
| Orchestrator stalls at stage 1 | Check `ALPHA_VANTAGE_API_KEY` / `NASDAQ_DATA_LINK_API_KEY`. |
| No Telegram message | Verify `TELEGRAM_CHAT_ID` is a channel (`-100…` prefix) and the bot is an admin. |
| Top 5 looks thin | Many tickers excluded for RSI>70 — that's the overbought guardrail firing. |

---

## License

MIT © 2026 Girish Eduru. Submitted as an OpenClaw-native hackathon project.
