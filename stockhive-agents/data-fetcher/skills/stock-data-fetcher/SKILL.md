---
name: stock-data-fetcher
description: Fetch daily OHLCV for a list of tickers and compute 4-week % returns. Use whenever you need to rank tickers by recent performance.
triggers:
  - "rank tickers by return"
  - "4 week gainers"
  - "top N Nasdaq movers"
mcps:
  - yfinance-mcp
  - nasdaq-data-link-mcp
---

# Skill: stock-data-fetcher

## When to use
You have a list of tickers and need each ticker's trailing 20-trading-day (~4 week) return so you can pick the top gainers.

## Steps
1. Load tickers from `config/nasdaq100-tickers.json` (or the input array).
2. Call `yfinance-mcp.history(period="60d", interval="1d")` for each (batch if supported).
3. For each ticker, compute:
   ```
   return_4w = close[-1] / close[-20] - 1
   ```
4. If history < 20 bars, retry via `nasdaq-data-link-mcp` (dataset `WIKI/EOD`).
5. Pipe results into `scripts/pick_top10.py` which sorts desc and slices to 10.

## Output shape
```json
[{"ticker":"AVGO","return_4w":0.181,"last_close":1842.10}, ...]
```

## Guardrails
- Exclude tickers with >2 missing trading days in the window.
- Never invent prices. On persistent failure, drop the ticker and note it.
