---
name: stock-data-fetcher
description: Fetch daily OHLCV for a list of Nasdaq-100 tickers, compute 4-week returns, and return a deterministic daily random sample of exactly 10 usable tickers.
triggers:
  - "randomize Nasdaq tickers"
  - "deterministic daily sample"
  - "random top 10 sample"
mcps:
  - yfinance-mcp
  - nasdaq-data-link-mcp
---

# Skill: stock-data-fetcher

## When to use
Use this skill when you need the runtime to select exactly 10 usable Nasdaq-100 tickers for the day.

## Input contract
```json
{
  "universe_file": "agent-system/config/nasdaq100-tickers.json",
  "selection_mode": "deterministic_daily_sample",
  "target_count": 10,
  "must_return_exactly": 10
}
```

## Required behavior
1. Load the ticker universe from the provided file.
2. Build a deterministic daily randomized order so the same trading day yields the same pseudo-random traversal order.
3. Fetch recent daily close history for each ticker.
4. Compute:
   ```
   return_4w = close[-1] / close[-20] - 1
   ```
5. Use `agent-system/scripts/pick_random10.py` to derive the deterministic daily random candidate order.
6. If a ticker is unusable, continue to the next ticker in that order.
7. Stop only when exactly `target_count` usable tickers have been collected.
8. If the universe cannot satisfy the target count, fail explicitly.

## Output contract
Return JSON only:
```json
[
  {"ticker":"AAPL","return_4w":0.05,"last_close":210.11}
]
```
Exactly 10 entries when successful.

## Guardrails
- Never fabricate prices.
- Do not return commentary outside JSON.
- Preserve stable field names: `ticker`, `return_4w`, `last_close`.
- If you fail, keep the error concise and operational.