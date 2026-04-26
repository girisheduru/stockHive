# StockHive Orchestrator Runtime

This document defines the executable shape of the primary StockHive runtime.

## Purpose
Make the OpenClaw-native path explicit and reviewable:
- orchestrator
- specialist subagents
- repo skills
- deterministic decision engine
- publisher agent

The runtime is centered on a single orchestrator-driven execution path.

## Runtime input template
Use `orchestrator-run-input.json` as the canonical input shape for an orchestrator-driven run.

The scheduled task targets `stockhive-orchestrator` directly.
There is no shell launcher in the normal runtime path.

The orchestrator may still materialize dated run artifacts if desired, but those artifacts are not required for execution.

## Primary runtime flow
1. `stockhive-orchestrator` reads the runtime input.
2. `data-fetcher` returns exactly 10 usable tickers using `agent-system/scripts/pick_random10.py` as the deterministic selector.
3. `technical-analyst`, `fundamental-analyst`, and `sentiment-analyst` run in parallel.
4. The orchestrator merges outputs.
5. `agent-system/scripts/decision_engine.py` produces `market_view`, `top5`, and `excluded`.
6. `telegram-publisher` formats and publishes.
7. The orchestrator returns a final JSON run summary.

## Runtime contracts
### Selection stage
Input:
```json
{
  "universe_file": "agent-system/config/nasdaq100-tickers.json",
  "selection_mode": "deterministic_daily_random_sample",
  "selection_script": "agent-system/scripts/pick_random10.py",
  "target_count": 10,
  "must_return_exactly": true
}
```
Output:
```json
[
  {"ticker":"AAPL","return_4w":0.05,"last_close":210.11}
]
```

### Specialist stages
Input:
```json
[
  {"ticker":"AAPL"},
  {"ticker":"MSFT"}
]
```
Output rows must match each specialist agent contract.

### Decision stage
Input is the merged payload:
```json
{
  "date": "YYYY-MM-DD",
  "top10": [],
  "technical": [],
  "fundamental": [],
  "sentiment": []
}
```
Output is the decision engine result.

### Publish stage
Input is the decision payload plus `run_date`.
Output:
```json
{
  "telegram_message_id": "123",
  "chars_sent": 1024
}
```

## Runtime policy
The repo uses a single primary orchestrator-driven runtime path.
The runtime does not rely on `nasdaq-orchestrator-runtime.sh` or `run_primary_runtime.py`.
Deterministic support scripts retained in the repo:
- `pick_random10.py`
- `pick_top10.py`
- `decision_engine.py`
