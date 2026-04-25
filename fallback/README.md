# StockHive Fallback Runtime

This directory contains the current and future fallback implementations for StockHive.

## Purpose
Keep the primary runtime design centered on:
- orchestrator
- specialist agents
- repo skills
- deterministic decision engine

while isolating direct shell/Python fallback flows for readability and operational safety.

## Current fallback contents
- `scripts/nasdaq-daily-run.sh` — fallback shell entrypoint
- `scripts/run_live_option_b.py` — direct live fallback runner
- `scripts/run_local_mvp.py` — direct local/mock fallback runner
- `tests/` — fallback-oriented tests

## Compatibility
Existing `openclawMVP/scripts/*` and `openclawMVP/tests/*` entrypoints are retained as thin wrappers so older references continue to work while the repo is restructured.
