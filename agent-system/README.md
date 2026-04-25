# StockHive — Agent System

This directory **is** the runtime composition of the StockHive agent system:
a persistent orchestrator plus the ephemeral subagents, skills, scheduled
task, MCP wiring, and scripts that together do the work end-to-end.

> An **agent system** is the runtime composition — orchestrator, subagents,
> skills, scheduled tasks — that actually does the work end-to-end.

```
cron (17:00 ET) ─▶ orchestrator ─▶ data-fetcher (stock-data-fetcher skill)
                                 ├─ technical-analyst   (technical-indicators skill)
                                 ├─ fundamental-analyst (fundamental-snapshot skill)
                                 └─ sentiment-analyst   (sentiment-analyzer skill)
                                 └─ aggregate → decision_engine.py → BULLISH/BEARISH + top 5
                                                              │
                                                              ▼
                                              telegram-publisher (telegram-formatter skill)
                                              → telegram-bot-mcp → channel
```

## Layout

| Path | Role |
|---|---|
| `../agent-system.json` | Composition manifest (orchestrator + subagents + skills + tasks + mcps) |
| `agents/` | Orchestrator + 5 subagent specs |
| `skills/` | 5 reusable SKILL.md capabilities |
| `scheduled-tasks/nasdaq-daily-schedule.json` | Daily 17:00 ET cron targeting the primary orchestrator launcher |
| `runtime/` | Primary orchestrator runtime template + runtime contract docs |
| `scripts/` | Primary launcher (`nasdaq-orchestrator-runtime.sh`) + deterministic support scripts |
| `mcps/mcp-config.json` | MCP server connection spec |
| `config/` | Nasdaq-100 tickers + `.env.example` |

## Runtime note

The intended primary runtime is the orchestrator plus specialist subagents plus repo skills.

The repo now uses a single primary runtime path.

The scheduled task targets `scripts/nasdaq-orchestrator-runtime.sh` as the primary entrypoint.

Primary runtime template/docs:
- `runtime/orchestrator-run-input.json`
- `runtime/ORCHESTRATOR_RUNTIME.md`

See the top-level [README](../README.md) for the run sequence.
