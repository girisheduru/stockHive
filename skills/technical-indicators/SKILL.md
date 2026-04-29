---
name: technical-indicators
description: Compute RSI(14), MACD(12,26,9), SMA20, SMA50 for each ticker and emit a BUY/HOLD/SELL signal.
triggers:
  - "technical analysis for ticker"
  - "RSI MACD"
  - "buy sell signal"
mcps:
  - alpha-vantage-mcp
  - yfinance-mcp
---

# Skill: technical-indicators

## When to use
Use this skill when the orchestrator sends a ticker list for technical analysis.

## Input contract
```json
[
  {"ticker":"AAPL"},
  {"ticker":"MSFT"}
]
```

## Required behavior
For each ticker:
1. Compute or fetch RSI(14).
2. Compute or fetch MACD histogram.
3. Compute SMA20 and SMA50 from recent close history.
4. Determine signal:
   - `BUY` if `close > SMA50` and `MACD_hist > 0` and `40 <= RSI <= 70`
   - `SELL` if `close < SMA50` and `MACD_hist < 0`
   - `HOLD` otherwise
5. Add a short explanatory `note`.

## Output contract
Return JSON only:
```json
[
  {
    "ticker":"AAPL",
    "rsi":62,
    "macd_hist":1.14,
    "sma20":205.1,
    "sma50":198.4,
    "close":210.1,
    "signal":"BUY",
    "note":"above SMA50, MACD positive"
  }
]
```
One row per input ticker.

## Guardrails
- Never fabricate indicators.
- If data is missing, return a conservative result and explain in `note`.
- Do not emit prose outside JSON.
- `signal` must be exactly one of `BUY`, `HOLD`, `SELL`.