# StockHive — Agent System

This directory **is** the runtime composition of the StockHive agent system:
a persistent orchestrator plus five ephemeral subagents, shared skills, a scheduled
task, MCP wiring, and deterministic support scripts that together do the work end-to-end.

> An **agent system** is the runtime composition — orchestrator, subagents,
> skills, scheduled tasks — that actually does the work end-to-end.

```
cron (17:00 ET) ─▶ stockhive-orchestrator
                    ├─ data-fetcher         (stock-data-fetcher skill)
                    ├─ technical-analyst    (technical-indicators skill)
                    ├─ fundamental-analyst  (fundamental-snapshot skill)
                    ├─ sentiment-analyst    (sentiment-analyzer skill)
                    ├─ aggregate → decision_engine.py → BULLISH/BEARISH + top 5
                    └─ telegram-publisher   (telegram-formatter skill)
                                              → telegram-bot-mcp → channel
```

## Layout

| Path | Role |
|---|---|
| `../agent-system.json` | Composition manifest (orchestrator + subagents + skills + tasks + mcps) |
| `agents/` | Orchestrator + 5 subagent specs |
| `skills/` | 5 reusable SKILL.md capabilities |
| `scheduled-tasks/nasdaq-daily-schedule.json` | Daily 17:00 ET cron targeting the orchestrator directly |
| `runtime/` | Canonical runtime template + runtime contract docs |
| `scripts/` | Deterministic support scripts only (`pick_random10.py`, `pick_top10.py`, `decision_engine.py`) |
| `mcps/mcp-config.json` | MCP server connection spec |
| `config/` | Nasdaq-100 tickers + `.env.example` |

## Runtime note

The primary runtime is OpenClaw-native:
- the scheduled task targets `stockhive-orchestrator`
- the orchestrator coordinates specialist subagents
- skills define the operational behavior of each specialist
- MCPs provide market, news, and Telegram integrations
- deterministic code is retained only where deterministic code is preferable

The repo does **not** depend on a shell launcher or monolithic Python runtime for normal execution.

Deterministic support scripts retained:
- `scripts/pick_random10.py`
- `scripts/pick_top10.py`
- `scripts/decision_engine.py`

Primary runtime template/docs:
- `runtime/orchestrator-run-input.json`
- `runtime/ORCHESTRATOR_RUNTIME.md`

See the top-level [README](../README.md) for the run sequence.
