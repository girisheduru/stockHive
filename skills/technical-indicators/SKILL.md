---
name: technical-indicators
description: Compute RSI(14), MACD(12,26,9), SMA20, SMA50 for a ticker and emit a BUY/HOLD/SELL signal.
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
A ticker needs momentum / trend analysis before a trade decision.

## Steps
1. `alpha-vantage-mcp.RSI(symbol, interval="daily", time_period=14, series_type="close")` → latest RSI value.
2. `alpha-vantage-mcp.MACD(symbol, interval="daily", series_type="close")` → MACD, signal, histogram.
3. `yfinance-mcp.history(period="90d", interval="1d")` → compute `SMA20` and `SMA50` from closing prices.
4. Combine into a signal:
   - **BUY**: `close > SMA50` AND `MACD_hist > 0` AND `40 ≤ RSI ≤ 70`
   - **SELL**: `close < SMA50` AND `MACD_hist < 0`
   - **HOLD**: otherwise
5. Add a one-line `note` explaining which rule fired.

## Output shape
```json
{"ticker":"AVGO","rsi":66,"macd_hist":1.2,"sma20":1820,"sma50":1705,"close":1842,"signal":"BUY","note":"above SMA50, MACD positive, RSI in range"}
```

## Guardrails
- If RSI > 70, signal is never BUY — downgrade to HOLD and flag `overbought:true`.
- If any indicator is missing, return `signal:"HOLD"` with `confidence:"low"`.
