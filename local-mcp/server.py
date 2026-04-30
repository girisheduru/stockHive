#!/usr/bin/env python3
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone


SERVER_NAME = os.environ.get("MCP_SERVER_NAME", "local-mcp")
MODE = os.environ.get("MCP_MODE", "generic")


def _json(obj):
    return json.dumps(obj, ensure_ascii=False)


def http_json(url, params=None, headers=None):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "OpenClaw-Local-MCP/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_text(url, params=None, data=None, headers=None):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    body = None
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers or {"User-Agent": "OpenClaw-Local-MCP/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def av_api(function, **params):
    key = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
    if not key:
        raise RuntimeError("Missing ALPHA_VANTAGE_API_KEY")
    return http_json("https://www.alphavantage.co/query", {"function": function, "apikey": key, **params})


def news_api(query, page_size=10):
    key = os.environ.get("NEWS_API_KEY", "")
    if not key:
        raise RuntimeError("Missing NEWS_API_KEY")
    return http_json(
        "https://newsapi.org/v2/everything",
        {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
        },
        headers={"X-Api-Key": key, "User-Agent": "OpenClaw-Local-MCP/1.0"},
    )


def telegram_send_message(text, chat_id=None, reply_to_message_id=None, parse_mode="Markdown"):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")
    if chat_id is None:
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not chat_id:
        raise RuntimeError("Missing chat_id and TELEGRAM_CHAT_ID")
    data = {
        "chat_id": str(chat_id),
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_to_message_id is not None:
        data["reply_to_message_id"] = str(reply_to_message_id)
    if parse_mode:
        data["parse_mode"] = parse_mode
    raw = http_text(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    obj = json.loads(raw)
    if not obj.get("ok"):
        raise RuntimeError(f"Telegram send failed: {obj}")
    return obj.get("result", {})


def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def compute_indicators(closes):
    closes = [c for c in closes if c is not None]
    if len(closes) < 50:
        raise RuntimeError("Not enough price history for indicators")

    def sma(vals, n):
        return sum(vals[-n:]) / n

    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]
    avg_gain = sum(gains[:14]) / 14
    avg_loss = sum(losses[:14]) / 14
    for i in range(14, len(deltas)):
        avg_gain = (avg_gain * 13 + gains[i]) / 14
        avg_loss = (avg_loss * 13 + losses[i]) / 14
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - 100 / (1 + rs)

    def ema_series(vals, span):
        k = 2 / (span + 1)
        out = []
        ema = vals[0]
        for v in vals:
            ema = v * k + ema * (1 - k)
            out.append(ema)
        return out

    ema12 = ema_series(closes, 12)
    ema26 = ema_series(closes, 26)
    macd = [a - b for a, b in zip(ema12, ema26)]
    signal = ema_series(macd, 9)
    hist = macd[-1] - signal[-1]

    close = closes[-1]
    sma20 = sma(closes, 20)
    sma50 = sma(closes, 50)
    if close > sma50 and hist > 0 and 40 <= rsi <= 70:
        sig = "BUY"
        note = "close above SMA50, MACD_hist positive, RSI in 40-70"
    elif close < sma50 and hist < 0:
        sig = "SELL"
        note = "close below SMA50, MACD_hist negative"
    else:
        sig = "HOLD"
        note = f"mixed setup: close {close:.2f}, SMA50 {sma50:.2f}, MACD_hist {hist:.4f}, RSI {rsi:.1f}"
    return {
        "rsi": round(rsi, 4),
        "macd_hist": round(hist, 6),
        "sma20": round(sma20, 4),
        "sma50": round(sma50, 4),
        "close": round(close, 4),
        "signal": sig,
        "note": note,
    }


def tool_definitions():
    if MODE in {"yfinance", "nasdaq", "alpha"}:
        tools = [
            {
                "name": "get_daily_history",
                "description": "Fetch recent daily OHLCV history for a US stock ticker. Returns rows newest-first and convenience fields last_close and return_4w.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "outputsize": {"type": "string", "enum": ["compact", "full"]}
                    },
                    "required": ["ticker"]
                }
            },
            {
                "name": "get_technical_indicators",
                "description": "Compute RSI(14), MACD histogram, SMA20, SMA50, close, signal, and note for a ticker using recent daily closes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"ticker": {"type": "string"}},
                    "required": ["ticker"]
                }
            },
            {
                "name": "get_overview",
                "description": "Fetch fundamental overview for a ticker including PE, market cap, sector, and a simple earnings health classification.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"ticker": {"type": "string"}},
                    "required": ["ticker"]
                }
            },
        ]
        return tools
    if MODE == "news":
        return [{
            "name": "get_headlines",
            "description": "Fetch recent relevant headlines for a ticker and return a simple sentiment score, top theme, and headline list.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20}
                },
                "required": ["ticker"]
            }
        }]
    if MODE == "telegram":
        return [{
            "name": "send_message",
            "description": "Send a Telegram message. chat_id/reply_to_message_id are optional if defaults are configured.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "chat_id": {"type": ["string", "integer"]},
                    "reply_to_message_id": {"type": ["string", "integer"]},
                    "parse_mode": {"type": "string"}
                },
                "required": ["text"]
            }
        }]
    return []


def handle_tool(name, args):
    if name == "get_daily_history":
        ticker = args["ticker"].upper()
        data = av_api("TIME_SERIES_DAILY", symbol=ticker, outputsize=args.get("outputsize", "compact"))
        series = data.get("Time Series (Daily)") or {}
        rows = []
        for d, vals in series.items():
            rows.append({
                "date": d,
                "open": _to_float(vals.get("1. open")),
                "high": _to_float(vals.get("2. high")),
                "low": _to_float(vals.get("3. low")),
                "close": _to_float(vals.get("4. close")),
                "volume": _to_float(vals.get("5. volume")),
            })
        rows.sort(key=lambda r: r["date"])
        closes = [r["close"] for r in rows if r.get("close") is not None]
        last_close = closes[-1] if closes else None
        return_4w = None
        if len(closes) >= 21 and closes[-21] not in (None, 0):
            return_4w = last_close / closes[-21] - 1
        return {
            "ticker": ticker,
            "last_close": last_close,
            "return_4w": return_4w,
            "rows": list(reversed(rows[-100:])),
        }

    if name == "get_technical_indicators":
        hist = handle_tool("get_daily_history", {"ticker": args["ticker"], "outputsize": "compact"})
        closes = [r["close"] for r in reversed(hist["rows"]) if r.get("close") is not None]
        result = compute_indicators(closes)
        result["ticker"] = args["ticker"].upper()
        return result

    if name == "get_overview":
        ticker = args["ticker"].upper()
        data = av_api("OVERVIEW", symbol=ticker)
        pe = _to_float(data.get("PERatio"))
        market_cap = int(float(data.get("MarketCapitalization"))) if data.get("MarketCapitalization") not in (None, "", "None") else None
        sector = data.get("Sector")
        qrev = _to_float(data.get("QuarterlyRevenueGrowthYOY"))
        qearn = _to_float(data.get("QuarterlyEarningsGrowthYOY"))
        if qrev is not None and qearn is not None and qrev > 0.05 and qearn > 0.05:
            health = "strong"
        elif (qrev is not None and qrev < 0) or (qearn is not None and qearn < 0):
            health = "weak"
        else:
            health = "mixed"
        note_bits = []
        if qrev is not None:
            note_bits.append(f"Revenue YoY {qrev*100:.1f}%")
        if qearn is not None:
            note_bits.append(f"EPS YoY {qearn*100:.1f}%")
        if pe is None:
            note_bits.append("P/E unavailable")
        return {
            "ticker": ticker,
            "pe": pe,
            "market_cap": market_cap,
            "sector": sector,
            "earnings_health": health,
            "note": "; ".join(note_bits) or "Overview data available"
        }

    if name == "get_headlines":
        ticker = args["ticker"].upper()
        limit = int(args.get("limit", 10))
        data = news_api(ticker, page_size=limit)
        articles = data.get("articles") or []
        titles = [a.get("title", "") for a in articles if a.get("title")]
        positive = ["beat", "surge", "gain", "growth", "record", "bull", "strong", "upgrade", "raise", "ai"]
        negative = ["miss", "fall", "drop", "cut", "weak", "bear", "lawsuit", "downgrade", "risk", "delay"]
        score = 0
        counts = {}
        for t in titles:
            tl = t.lower()
            for w in positive:
                if w in tl:
                    score += 1
            for w in negative:
                if w in tl:
                    score -= 1
            for token in re.findall(r"[a-zA-Z]{4,}", tl):
                if token in {ticker.lower(), "stock", "shares", "company", "says", "will", "with", "from", "amid"}:
                    continue
                counts[token] = counts.get(token, 0) + 1
        norm = 0.0 if not titles else max(-1.0, min(1.0, score / max(len(titles) * 2, 1)))
        top_theme = max(counts, key=counts.get) if counts else "coverage mixed"
        return {
            "ticker": ticker,
            "score": round(norm, 2),
            "top_theme": top_theme,
            "n_headlines": len(titles),
            "headlines": titles[:limit],
        }

    if name == "send_message":
        result = telegram_send_message(
            text=args["text"],
            chat_id=args.get("chat_id"),
            reply_to_message_id=args.get("reply_to_message_id"),
            parse_mode=args.get("parse_mode", "Markdown"),
        )
        return {
            "telegram_message_id": str(result.get("message_id")),
            "chat_id": str(result.get("chat", {}).get("id")),
            "chars_sent": len(args["text"]),
        }

    raise RuntimeError(f"Unknown tool: {name}")


def make_response(_id, result=None, error=None):
    if error is not None:
        return {"jsonrpc": "2.0", "id": _id, "error": {"code": -32000, "message": str(error)}}
    return {"jsonrpc": "2.0", "id": _id, "result": result}


def read_message(inp):
    headers = {}
    while True:
        line = inp.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        k, v = line.decode().split(":", 1)
        headers[k.strip().lower()] = v.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = inp.read(length)
    return json.loads(body.decode())


def write_message(out, msg):
    body = json.dumps(msg).encode()
    out.write(f"Content-Length: {len(body)}\r\n\r\n".encode())
    out.write(body)
    out.flush()


def main():
    while True:
        msg = read_message(sys.stdin.buffer)
        if msg is None:
            break
        method = msg.get("method")
        _id = msg.get("id")
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": "0.1.0"},
                }
                if _id is not None:
                    write_message(sys.stdout.buffer, make_response(_id, result))
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                write_message(sys.stdout.buffer, make_response(_id, {"tools": tool_definitions()}))
            elif method == "tools/call":
                params = msg.get("params", {})
                result = handle_tool(params.get("name"), params.get("arguments", {}))
                write_message(sys.stdout.buffer, make_response(_id, {"content": [{"type": "text", "text": _json(result)}]}))
            else:
                if _id is not None:
                    write_message(sys.stdout.buffer, make_response(_id, error=f"Unsupported method: {method}"))
        except Exception as e:
            if _id is not None:
                write_message(sys.stdout.buffer, make_response(_id, error=e))


if __name__ == "__main__":
    main()
