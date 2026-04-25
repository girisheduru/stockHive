#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_DIR = REPO_ROOT / "agent-system"
CONFIG_ENV = SYSTEM_DIR / "config" / ".env"
CONFIG_TICKERS = SYSTEM_DIR / "config" / "nasdaq100-tickers.json"
DECISION_ENGINE = SYSTEM_DIR / "scripts" / "decision_engine.py"
PICK_RANDOM10 = SYSTEM_DIR / "scripts" / "pick_random10.py"
GENERATED_DIR = SYSTEM_DIR / "runtime" / "generated"


def log(stage: str, message: str) -> None:
    print(f"{stage} {message}", file=sys.stderr)


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        if k not in os.environ:
            os.environ[k] = v


def require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"missing env: {name}")
    return val


def to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    except Exception:
        return None


def load_tickers() -> list[str]:
    payload = json.loads(CONFIG_TICKERS.read_text())
    return payload["tickers"]


def fetch_history(ticker: str, period: str = "3mo") -> pd.DataFrame:
    try:
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=False)
    except Exception as exc:
        raise RuntimeError(f"yahoo fetch failed for {ticker}: {type(exc).__name__}") from exc
    if hist is None or hist.empty:
        raise RuntimeError(f"no history for {ticker}")
    return hist


def compute_rsi(series: pd.Series, window: int = 14) -> float | None:
    delta = series.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(window=window, min_periods=window).mean()
    avg_loss = losses.rolling(window=window, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return None if pd.isna(val) else float(val)


def compute_macd_hist(series: pd.Series) -> float | None:
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    val = hist.iloc[-1]
    return None if pd.isna(val) else float(val)


def fetch_candidate_rows() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    for ticker in load_tickers():
        try:
            hist = fetch_history(ticker, period="3mo")
            closes = hist["Close"].dropna()
            if len(closes) < 21:
                diagnostics.append({"ticker": ticker, "stage": "prices", "reason": f"insufficient_closes:{len(closes)}"})
                continue
            last_close = float(closes.iloc[-1])
            prev = float(closes.iloc[-21])
            ret = (last_close / prev) - 1
            rows.append({"ticker": ticker, "return_4w": ret, "last_close": last_close})
        except Exception as exc:
            diagnostics.append({"ticker": ticker, "stage": "prices", "reason": str(exc).strip() or type(exc).__name__})
    return rows, diagnostics


def select_top10(rows: list[dict[str, Any]], run_date: str) -> list[dict[str, Any]]:
    proc = subprocess.run(
        [sys.executable, str(PICK_RANDOM10)],
        input=json.dumps(rows),
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "STOCKHIVE_RANDOM_SEED": run_date},
    )
    return json.loads(proc.stdout)


def analyze_technical(top10: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in top10:
        ticker = row["ticker"]
        hist = fetch_history(ticker, period="6mo")
        closes = hist["Close"].dropna()
        close = float(closes.iloc[-1])
        sma20 = float(closes.tail(20).mean())
        sma50 = float(closes.tail(50).mean())
        rsi = compute_rsi(closes)
        macd_hist = compute_macd_hist(closes)
        signal = "HOLD"
        note = []
        if close > sma50:
            note.append("above SMA50")
        if macd_hist is not None and macd_hist > 0:
            note.append("MACD positive")
        if rsi is not None and 40 <= rsi <= 70 and close > sma50 and (macd_hist or 0) > 0:
            signal = "BUY"
        elif close < sma50 and (macd_hist or 0) < 0:
            signal = "SELL"
        out.append({
            "ticker": ticker,
            "rsi": None if rsi is None else round(rsi),
            "macd_hist": None if macd_hist is None else round(macd_hist, 3),
            "sma20": round(sma20, 2),
            "sma50": round(sma50, 2),
            "close": round(close, 2),
            "signal": signal,
            "note": ", ".join(note) if note else "mixed setup",
        })
    return out


def analyze_fundamental(top10: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in top10:
        ticker = row["ticker"]
        info = yf.Ticker(ticker).info or {}
        pe = to_float(info.get("trailingPE"))
        market_cap = to_float(info.get("marketCap"))
        sector = info.get("sector")
        earnings_growth = to_float(info.get("earningsGrowth"))
        revenue_growth = to_float(info.get("revenueGrowth"))
        if earnings_growth is not None and earnings_growth > 0.05 and revenue_growth is not None and revenue_growth > 0:
            health = "strong"
        elif (earnings_growth is not None and earnings_growth > 0) or (revenue_growth is not None and revenue_growth > 0):
            health = "mixed"
        else:
            health = "weak"
        note_bits = []
        if earnings_growth is not None:
            note_bits.append(f"earnings growth {earnings_growth * 100:+.0f}%")
        if revenue_growth is not None:
            note_bits.append(f"revenue growth {revenue_growth * 100:+.0f}%")
        out.append({
            "ticker": ticker,
            "pe": None if pe is None else round(pe, 2),
            "market_cap": market_cap,
            "sector": sector,
            "earnings_health": health,
            "note": ", ".join(note_bits) if note_bits else "growth data limited",
        })
    return out


def news_api_sentiment_score(text: str) -> tuple[float, str]:
    positive = ["beat", "growth", "upgrade", "strong", "surge", "gain", "bullish", "expands", "record", "demand"]
    negative = ["miss", "cut", "weak", "lawsuit", "decline", "drop", "bearish", "risk", "probe", "slowdown"]
    low = text.lower()
    pos = sum(low.count(w) for w in positive)
    neg = sum(low.count(w) for w in negative)
    score = 0.0
    if pos or neg:
        score = max(-1.0, min(1.0, (pos - neg) / max(pos + neg, 1)))
    theme = "mixed news flow"
    if "ai" in low:
        theme = "AI demand in focus"
    elif "cloud" in low:
        theme = "Cloud demand in focus"
    elif "security" in low:
        theme = "Security demand in focus"
    elif "chip" in low or "semiconductor" in low:
        theme = "Semiconductor momentum"
    return round(score, 2), theme


def analyze_sentiment(top10: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    api_key = require_env("NEWS_API_KEY")
    out: list[dict[str, Any]] = []
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    source = "newsapi"
    for row in top10:
        ticker = row["ticker"]
        params = {
            "q": ticker,
            "from": since,
            "pageSize": 10,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": api_key,
        }
        r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=30)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        joined = " ".join(filter(None, [f"{a.get('title','')} {a.get('description','')}" for a in articles]))
        score, theme = news_api_sentiment_score(joined)
        out.append({"ticker": ticker, "score": score, "top_theme": theme, "n_headlines": len(articles)})
    return out, source


def run_decision_engine(payload: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(DECISION_ENGINE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def format_message(run_date: str, decision: dict[str, Any], mode: str) -> str:
    top5 = decision.get("top5", [])
    excluded = decision.get("excluded", [])
    lines = [
        "** Nasdaq 100 — Daily Top 5 Buys **",
        f"Date: {run_date}  |  {'Dry run' if mode == 'dry-run' else 'Live publish'}",
        "",
        f"Market view:  [ {decision.get('market_view', 'UNKNOWN')} ]",
        f"Breadth {decision.get('breadth_buy_count', 0)}/10 up, RSI avg {decision.get('rsi_avg', 0)}, sentiment {decision.get('sent_avg', 0.0):+.2f}",
        "",
        "Top 5 Buy Candidates",
        "--------------------",
    ]
    if top5:
        for idx, row in enumerate(top5, start=1):
            lines.append(f"{idx}. {row['ticker']}  {row['return_4w'] * 100:+.1f}%  RSI {row.get('rsi','n/a')}  PE {row.get('pe','n/a')}")
            if row.get("rationale"):
                lines.append(f"   {row['rationale']}")
    if excluded:
        lines.extend(["", "Excluded", "--------"])
        for row in excluded:
            lines.append(f"- {row['ticker']}: {row['reason']}")
    lines.extend(["", "--", "StockHive  |  Primary runtime"])
    return "\n".join(lines)


def maybe_publish(message: str, mode: str) -> dict[str, Any]:
    bot_token = require_env("TELEGRAM_BOT_TOKEN")
    raw_chat_id = require_env("TELEGRAM_CHAT_ID").strip()
    thread_id = os.environ.get("TELEGRAM_MESSAGE_THREAD_ID", "").strip()
    payload: dict[str, Any] = {
        "chat_id": raw_chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    if thread_id:
        payload["message_thread_id"] = int(thread_id)
    if mode == "dry-run":
        result = {"telegram_message_id": "dry-run-not-sent", "chars_sent": len(message), "chat_id": raw_chat_id}
        if thread_id:
            result["message_thread_id"] = int(thread_id)
        return result
    r = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    body = r.json()
    result = {
        "telegram_message_id": str(body.get("result", {}).get("message_id")),
        "chars_sent": len(message),
        "chat_id": raw_chat_id,
    }
    if thread_id:
        result["message_thread_id"] = int(thread_id)
    return result


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: run_primary_runtime.py <runtime_json> <result_json>", file=sys.stderr)
        return 2
    runtime_json = Path(sys.argv[1])
    result_json = Path(sys.argv[2])
    load_env_file(CONFIG_ENV)
    runtime = json.loads(runtime_json.read_text())
    run_date = runtime.get("run_date") or datetime.now().strftime("%Y-%m-%d")
    mode = os.environ.get("STOCKHIVE_PUBLISH_MODE", "dry-run")

    log("[STAGE 1/6]", "Fetching candidate market data.")
    candidate_rows, diagnostics = fetch_candidate_rows()
    top10 = select_top10(candidate_rows, run_date)

    log("[STAGE 2/6]", "Running analyst stages in parallel.")
    with ThreadPoolExecutor(max_workers=3) as pool:
        tech_f = pool.submit(analyze_technical, top10)
        fund_f = pool.submit(analyze_fundamental, top10)
        sent_f = pool.submit(analyze_sentiment, top10)
        technical = tech_f.result()
        fundamental = fund_f.result()
        sentiment, sentiment_source = sent_f.result()

    log("[STAGE 3/6]", "Aggregating outputs.")
    merged = {
        "date": run_date,
        "top10": top10,
        "technical": technical,
        "fundamental": fundamental,
        "sentiment": sentiment,
    }

    log("[STAGE 4/6]", "Running decision engine.")
    decision = run_decision_engine(merged)

    log("[STAGE 5/6]", f"Formatting message ({mode}).")
    message = format_message(run_date, decision, mode)

    log("[STAGE 6/6]", "Publishing final result.")
    publish = maybe_publish(message, mode)

    result = {
        "run_date": run_date,
        "mode": mode,
        "market_view": decision["market_view"],
        "top5": decision["top5"],
        "excluded": decision["excluded"],
        "top10_count": len(top10),
        "diagnostic_count": len(diagnostics),
        "sentiment_source": sentiment_source,
        **publish,
    }
    result_json.write_text(json.dumps(result, indent=2) + "\n")
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
