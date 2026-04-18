# nasdaq-top-movers.plugin

OpenClaw plugin that powers **StockHive** — a daily, fully automated Nasdaq 100 top-movers analyzer.

```
cron (17:00 ET) ─▶ orchestrator ─▶ 4× ephemeral subagents (parallel)
                                 ├─ data-fetcher        (stock-data-fetcher skill)
                                 ├─ technical-analyst   (technical-indicators skill)
                                 ├─ fundamental-analyst (fundamental-snapshot skill)
                                 └─ sentiment-analyst   (sentiment-analyzer skill)
                   ▲
                   └── aggregate → decision_engine.py → BULLISH/BEARISH + top 5
                                                              │
                                                              ▼
                                              telegram-publisher (ephemeral)
                                              → telegram-bot-mcp → channel
```

See the top-level [README.md](../README.md) for hackathon run instructions.
