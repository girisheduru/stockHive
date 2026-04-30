#!/usr/bin/env python3
"""
decision_engine.py — StockHive aggregator.

Reads a JSON payload on stdin containing the three per-ticker reports
(technical, fundamental, sentiment) for the top-10 gainers, scores them,
labels the market view BULLISH or BEARISH, and picks the top 5 buys.

Input shape:
{
  "date": "YYYY-MM-DD",
  "top10": [{"ticker":"AVGO","return_4w":0.181,"last_close":1842.10}, ...],
  "technical":  [{"ticker":"AVGO","rsi":66,"macd_hist":1.2,"sma20":...,"sma50":...,"close":...,"signal":"BUY","note":"..."}, ...],
  "fundamental":[{"ticker":"AVGO","pe":42,"market_cap":...,"sector":"...","earnings_health":"strong","note":"..."}, ...],
  "sentiment":  [{"ticker":"AVGO","score":0.55,"top_theme":"...","n_headlines":10}, ...]
}

Output shape:
{
  "market_view": "BULLISH" | "BEARISH",
  "top5": [ {ticker, return_4w, rsi, pe, sentiment, composite, rationale} x5 ],
  "excluded": [ {ticker, reason} ],
  "breadth_buy_count": int,
  "rsi_avg": int,
  "sent_avg": float
}
"""
from __future__ import annotations

import json
import sys
from statistics import mean
from typing import Any

W_TECH = 0.4
W_FUND = 0.3
W_SENT = 0.3


def index_by_ticker(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {r["ticker"]: r for r in rows}


def technical_score(t: dict[str, Any]) -> float:
    sig = t.get("signal", "HOLD")
    base = {"BUY": 1.0, "HOLD": 0.0, "SELL": -1.0}.get(sig, 0.0)
    rsi = t.get("rsi") or 50
    # penalise overbought
    if rsi and rsi > 70:
        base -= 0.5
    return max(-1.0, min(1.0, base))


def fundamental_score(f: dict[str, Any]) -> float:
    health = f.get("earnings_health", "mixed")
    base = {"strong": 1.0, "mixed": 0.2, "weak": -0.6}.get(health, 0.0)
    pe = f.get("pe") or 0
    if pe and pe > 80:
        base -= 0.5  # stretched
    return max(-1.0, min(1.0, base))


def sentiment_score(s: dict[str, Any]) -> float:
    val = s.get("score", 0.0)
    try:
        val = float(val)
    except (TypeError, ValueError):
        val = 0.0
    return max(-1.0, min(1.0, val))


def decide(payload: dict[str, Any]) -> dict[str, Any]:
    tech = index_by_ticker(payload.get("technical", []))
    fund = index_by_ticker(payload.get("fundamental", []))
    sent = index_by_ticker(payload.get("sentiment", []))

    rows: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for base in payload.get("top10", []):
        t = base["ticker"]
        tr = tech.get(t, {})
        fr = fund.get(t, {})
        sr = sent.get(t, {})

        rsi = tr.get("rsi")
        pe = fr.get("pe")

        if rsi is not None and rsi > 70:
            excluded.append({"ticker": t, "reason": f"RSI {rsi} overbought"})
            continue
        if pe is not None and pe > 80:
            excluded.append({"ticker": t, "reason": f"PE {pe} stretched"})
            continue

        composite = (
            W_TECH * technical_score(tr)
            + W_FUND * fundamental_score(fr)
            + W_SENT * sentiment_score(sr)
        )

        rationale_bits = []
        if tr.get("note"): rationale_bits.append(f"Tech: {tr['note']}")
        if fr.get("note"): rationale_bits.append(f"Fund: {fr['note']}")
        if sr.get("top_theme"): rationale_bits.append(f"News: {sr['top_theme']}")

        rows.append({
            "ticker": t,
            "return_4w": base.get("return_4w"),
            "rsi": rsi,
            "pe": pe,
            "sentiment": sr.get("score"),
            "composite": round(composite, 3),
            "rationale": " | ".join(rationale_bits),
        })

    rows.sort(key=lambda r: r["composite"], reverse=True)
    top5 = rows[:5]

    # Market view
    buys = sum(1 for r in payload.get("technical", []) if r.get("signal") == "BUY")
    rsi_vals = [r["rsi"] for r in payload.get("technical", []) if isinstance(r.get("rsi"), (int, float))]
    sent_vals = [float(r["score"]) for r in payload.get("sentiment", []) if r.get("score") is not None]

    rsi_avg = int(round(mean(rsi_vals))) if rsi_vals else 0
    sent_avg = round(mean(sent_vals), 2) if sent_vals else 0.0

    bullish = (buys >= 6) and (sent_avg >= 0.1) and (rsi_avg < 70)
    market_view = "BULLISH" if bullish else "BEARISH"

    return {
        "market_view": market_view,
        "top5": top5,
        "excluded": excluded,
        "breadth_buy_count": buys,
        "rsi_avg": rsi_avg,
        "sent_avg": sent_avg,
    }


def main() -> int:
    payload = json.load(sys.stdin)
    result = decide(payload)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
