---
name: fundamental-snapshot
description: Pull P/E, market cap, sector, and a recent earnings-health snapshot for each ticker.
triggers:
  - "fundamentals for ticker"
  - "PE market cap sector"
  - "earnings health"
mcps:
  - yfinance-mcp
---

# Skill: fundamental-snapshot

## When to use
Use this skill when the orchestrator sends a ticker list for fundamental analysis.

## Input contract
```json
[
  {"ticker":"AAPL"},
  {"ticker":"MSFT"}
]
```

## Required behavior
For each ticker:
1. Fetch or derive `pe`, `market_cap`, and `sector`.
2. Inspect recent earnings and revenue trend data when available.
3. Classify `earnings_health` as `strong`, `mixed`, or `weak`.
4. Add a short `note` explaining the classification.

## Output contract
Return JSON only:
```json
[
  {
    "ticker":"AAPL",
    "pe":31.5,
    "market_cap":3000000000000,
    "sector":"Technology",
    "earnings_health":"strong",
    "note":"EPS beat 8%, revenue +12% YoY"
  }
]
```
One row per input ticker.

## Guardrails
- Never fabricate sector or earnings metrics.
- If a field is missing, use a safe fallback and explain in `note`.
- Do not emit prose outside JSON.
- `earnings_health` must be exactly `strong`, `mixed`, or `weak`.