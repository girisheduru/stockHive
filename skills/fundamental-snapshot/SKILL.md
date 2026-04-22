---
name: fundamental-snapshot
description: Pull P/E, market cap, sector, and the most recent earnings beat/miss for a ticker and classify earnings health.
triggers:
  - "fundamentals for ticker"
  - "PE market cap sector"
  - "earnings health"
mcps:
  - yfinance-mcp
---

# Skill: fundamental-snapshot

## When to use
A ticker has passed technical screening and needs a quick fundamentals check.

## Steps
1. `yfinance-mcp.info(symbol)` → `trailingPE`, `marketCap`, `sector`, `industry`, `dividendYield`.
2. `yfinance-mcp.earnings(symbol)` → most recent quarter `actual` vs `estimate`.
3. `yfinance-mcp.financials(symbol)` → last-quarter revenue YoY delta.
4. Classify earnings health:
   - `strong` — EPS beat > 5% AND revenue YoY > 0
   - `mixed` — only one of the above
   - `weak` — both negative or data missing
5. Emit a one-line `note`.

## Output shape
```json
{"ticker":"AVGO","pe":42,"market_cap":820000000000,"sector":"Technology","earnings_health":"strong","note":"EPS beat 8%, revenue +12% YoY"}
```

## Guardrails
- Flag `stretched:true` when `pe > 80`.
- Never fabricate a sector; if missing, set `"sector":"Unknown"`.
