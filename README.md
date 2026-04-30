# StockHive <a href="https://t.me/+keb_oQG0jM1kZDBk" target="_blank" rel="noopener noreferrer" class="join-btn">
  <span class="ticker">BEEH 🍯</span> • 🐝 Join Now on Telegram
</a>

> **OpenClaw-native agent system — Nasdaq 100 Top 5 Buy Candidates, delivered daily to Telegram.**
>
> Built for the **[Encode Club — April Agentic Mini-Hack](https://www.encodeclub.com/my-programmes/april-agentic-mini-hack)**.
> Platform: **Claude Cowork + OpenClaw**.

StockHive demonstrates what a production-grade agentic system looks like when built natively on OpenClaw: a persistent orchestrator that spawns, coordinates, and tears down ephemeral specialist subagents to produce a real financial output on a real schedule.

Every trading day at **17:00 ET (post-close)** the system:

1. Selects a **deterministic daily random sample of 10 usable Nasdaq-100 tickers**.
2. Spawns **three ephemeral specialist subagents in parallel** — technical, fundamental, sentiment — after a sequential data-fetch stage.
3. Aggregates their structured outputs and runs `decision_engine.py` to label the market **BULLISH** or **BEARISH**.
4. Posts the **Top 5 Buy Candidates** — with rationale and any exclusions — to a Telegram channel.

The cleaned version of the repo is now genuinely OpenClaw-native in its runtime path: the scheduled task targets the orchestrator directly, specialist work stays with specialist subagents and skills, MCPs handle external integrations, and only deterministic helper scripts remain as code.

The orchestrator is also intended to behave as a persistent always-on agent session. Scheduled runs should bind back to that same `stockhive-orchestrator` session rather than creating a fresh orchestration context on each schedule fire.

Everything is wired through a single composition manifest ([`agent-system.json`](./agent-system.json)) and registered with **one OpenClaw command**.

---

## What this demonstrates

| OpenClaw capability | How StockHive uses it |
|---|---|
| **Agent system registration** | `agent-system.json` declares orchestrator, subagents, skills, schedule, and MCPs — registered atomically with `/agents register` |
| **Persistent orchestrator** | `stockhive-orchestrator` is a long-lived always-on coordinator; scheduled runs reuse the same session and it holds continuity across all six stages |
| **Ephemeral subagents** | 5 subagents spawn on demand, run isolated, tear down on reply — zero state bleed |
| **Parallel fan-out** | Technical, fundamental, and sentiment analysts dispatched in a single orchestrator turn |
| **Skills** | 5 reusable skills callable independently or from any agent in the workspace |
| **MCP connections** | 5 external data sources (Yahoo Finance, Alpha Vantage, Nasdaq Data Link, NewsAPI, Telegram) wired declaratively |
| **Scheduled task** | Weekday 17:00 ET cron, manually triggerable any time with `/task run`, reusing the same persistent orchestrator session |

---

## Architecture

```
                      ┌─────────────────────────────┐
                      │    nasdaq-daily-schedule      │  cron: 17:00 ET weekdays
                      └──────────────┬──────────────┘
                                     │
                      ┌──────────────▼──────────────┐
                      │     stockhive-orchestrator    │  persistent
                      └──┬───────────────────────┬──┘
                         │                       │
              ┌──────────▼─────────┐   parallel fan-out
              │    data-fetcher     │   ┌───────────────────┐
              │  (ephemeral)        │   │  technical-analyst │
              │  stock-data-fetcher │   │  technical-        │
              │  skill              │   │  indicators skill  │
              └──────────┬─────────┘   ├───────────────────┤
                         │             │ fundamental-analyst│
                    10 tickers         │  fundamental-      │
                         │             │  snapshot skill    │
                         └────────────►├───────────────────┤
                                       │  sentiment-analyst │
                                       │  sentiment-        │
                                       │  analyzer skill    │
                                       └────────┬──────────┘
                                                │
                              ┌─────────────────▼──────────────┐
                              │   decision_engine.py            │
                              │   (plain Python, no LLM)        │
                              │   → BULLISH / BEARISH + Top 5   │
                              └─────────────────┬──────────────┘
                                                │
                              ┌─────────────────▼──────────────┐
                              │      telegram-publisher          │
                              │      (ephemeral)                 │
                              │      telegram-formatter skill    │
                              └────────────────────────────────┘
```

---

## Repository layout

```
stockHive/
├── agent-system.json                      ← OpenClaw composition manifest
├── agent-system/
│   ├── agents/                            ← orchestrator + 5 subagent specs
│   │   ├── stockhive-orchestrator.md
│   │   ├── data-fetcher.md
│   │   ├── technical-analyst.md
│   │   ├── fundamental-analyst.md
│   │   ├── sentiment-analyst.md
│   │   └── telegram-publisher.md
│   ├── skills/                            ← 5 independently reusable skills
│   │   ├── stock-data-fetcher/SKILL.md
│   │   ├── technical-indicators/SKILL.md
│   │   ├── fundamental-snapshot/SKILL.md
│   │   ├── sentiment-analyzer/SKILL.md
│   │   └── telegram-formatter/SKILL.md
│   ├── scheduled-tasks/
│   │   └── nasdaq-daily-schedule.json     ← weekday 17:00 ET cron spec
│   ├── mcps/
│   │   └── mcp-config.json                ← 5 MCP server declarations
│   ├── scripts/
│   │   ├── pick_random10.py               ← deterministic daily ticker selection
│   │   ├── pick_top10.py                  ← return-ranked top-10 selector (retained)
│   │   └── decision_engine.py             ← BULLISH/BEARISH scoring (no LLM)
│   ├── runtime/
│   │   ├── ORCHESTRATOR_RUNTIME.md        ← full runtime contract reference
│   │   └── orchestrator-run-input.json    ← canonical input template
│   └── config/
│       ├── nasdaq100-tickers.json         ← 100-ticker universe
│       └── .env.example                   ← required secrets template
└── RUNBOOK.md                             ← step-by-step OpenClaw Chat walkthrough
```

---

## Running it in OpenClaw Chat

Paste these commands in order inside **OpenClaw Chat**. See [RUNBOOK.md](./RUNBOOK.md) for the full step-by-step walkthrough with expected outputs and troubleshooting.

### Prerequisites

| Secret | How to obtain |
|--------|--------------|
| `ALPHA_VANTAGE_API_KEY` | [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key) |
| `NASDAQ_DATA_LINK_API_KEY` | [data.nasdaq.com/account/api](https://data.nasdaq.com/account/api) |
| `NEWS_API_KEY` | [newsapi.org/register](https://newsapi.org/register) |
| `TELEGRAM_BOT_TOKEN` | Chat `@BotFather` → `/newbot` |
| `TELEGRAM_CHAT_ID` | Add the bot to your channel as admin; the id starts with `-100` |

### Step 1 — Clone

```
/bash git clone https://github.com/girisheduru/stockHive && cd stockHive
```

### Step 2 — Register the agent system

```
/agents register ./agent-system.json
```

Registers in one step: persistent orchestrator, 5 ephemeral subagents, 5 skills, 1 scheduled task, MCP config. Verify:

```
/agents list
/skills list
/tasks list
```

### Step 3 — Configure secrets

```
/bash cp agent-system/config/.env.example agent-system/config/.env
```

Fill in the five keys from the prerequisites table above.

### Step 4 — Connect MCP servers

```
/mcp connect ./agent-system/mcps/mcp-config.json
```

OpenClaw spawns all five MCP servers. Verify with `/mcp list` — all five should show `status: running`.

### Step 5 — Smoke-test ephemeral subagents

Each command below spawns a subagent, executes it, gets strict JSON back, then tears it down. This is the ephemeral lifecycle live:

```
/agent run data-fetcher --input '{"universe_file":"agent-system/config/nasdaq100-tickers.json","selection_mode":"deterministic_daily_random_sample","target_count":10,"must_return_exactly":true}'
```
```
/agent run technical-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```
```
/agent run fundamental-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```
```
/agent run sentiment-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'
```

### Step 6 — Run the full pipeline on demand

```
/task run nasdaq-daily-top5-buys
```

Same execution the scheduler fires daily through the orchestrator-native path. Watch the staged orchestration flow and the Telegram alert arrive in your channel.

### Step 7 — Enable the recurring schedule

```
/schedule enable nasdaq-daily-top5-buys
```

Fires every weekday at **17:00 America/New_York** from now on. Pause with `/schedule disable nasdaq-daily-top5-buys`.

---

## Design decisions

**Agent system, not a package.** StockHive is a runtime composition registered directly with OpenClaw — not an installable library or standalone app. One manifest wires every piece together.

**Ephemeral subagents by design.** Each analyst spins up for exactly one run with its own isolated context, does its job, and is torn down on reply. No state bleed between runs. Cheap to scale horizontally.

**Parallel fan-out at stage 3.** The orchestrator dispatches technical, fundamental, and sentiment analysts in a single turn — the serial bottleneck is only the upstream data-fetch stage, which must complete before the universe is known.

**Deterministic decision layer.** `decision_engine.py` is plain Python — no LLM in the scoring path. The BULLISH/BEARISH call and Top 5 ranking are reproducible, auditable, and unit-testable independently of any model run.

**Composable skills.** Each skill (`stock-data-fetcher`, `technical-indicators`, `fundamental-snapshot`, `sentiment-analyzer`, `telegram-formatter`) is independently triggerable from OpenClaw and reusable by any other agent system in the workspace.

**One-command register, one-command run.** `/agents register` then `/task run` — no shell launcher or monolithic Python runtime in the active execution path.

---

## Teardown

```
/schedule disable nasdaq-daily-top5-buys
/mcp disconnect --all-from ./agent-system/mcps/mcp-config.json
/agents unregister ./agent-system.json
```

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

---

## License

MIT © 2026 Girish Eduru.
