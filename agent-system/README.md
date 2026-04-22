# StockHive — Agent System

This directory **is** the runtime composition of the StockHive agent system:
a persistent orchestrator plus the ephemeral subagents, skills, scheduled
task, MCP wiring, and scripts that together do the work end-to-end.

> An **agent system** is the runtime composition — orchestrator, subagents,
> skills, scheduled tasks — that actually does the work end-to-end.

```
cron (17:00 ET) ─▶ orchestrator ─▶ 3× ephemeral subagents (parallel)
                                 ├─ technical-analyst   (technical-indicators skill)
                                 ├─ fundamental-analyst (fundamental-snapshot skill)
                                 └─ sentiment-analyst   (sentiment-analyzer skill)
                   ▲
                   │  (preceded by data-fetcher ephemeral → stock-data-fetcher skill)
                   │
                   └── aggregate → decision_engine.py → BULLISH/BEARISH + top 5
                                                              │
                                                              ▼
                                              telegram-publisher (ephemeral)
                                              → telegram-bot-mcp → channel
```

## Layout

| Path | Role |
|---|---|
| `../agent-system.json` | Composition manifest (orchestrator + subagents + skills + tasks + mcps) |
| `agents/` | Orchestrator + 5 subagent specs |
| `skills/` | 5 reusable SKILL.md capabilities |
| `scheduled-tasks/nasdaq-daily-schedule.json` | Daily 17:00 ET cron |
| `scripts/` | Runner (`nasdaq-daily-run.sh`) + `pick_top10.py` + `decision_engine.py` |
| `mcps/mcp-config.json` | MCP server connection spec |
| `config/` | Nasdaq-100 tickers + `.env.example` |

See the top-level [README](../README.md) for the run sequence.
