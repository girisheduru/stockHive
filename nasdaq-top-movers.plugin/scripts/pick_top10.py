#!/usr/bin/env python3
"""
pick_top10.py — rank tickers by 4-week % return and emit the top 10.

Used by the data-fetcher subagent. Reads a JSON array on stdin, writes a JSON
array to stdout.

Input:  [{"ticker":"AAPL","return_4w":0.053,"last_close":...}, ...]
Output: top-10 by return_4w, descending.
"""
from __future__ import annotations

import json
import sys
from typing import Any

MIN_RETURN = -1.0  # keep all; screening happens in decision_engine


def pick(rows: list[dict[str, Any]], n: int = 10) -> list[dict[str, Any]]:
    cleaned = [r for r in rows if isinstance(r.get("return_4w"), (int, float))]
    cleaned.sort(key=lambda r: r["return_4w"], reverse=True)
    return cleaned[:n]


def main() -> int:
    rows = json.load(sys.stdin)
    if not isinstance(rows, list):
        print("expected a JSON array on stdin", file=sys.stderr)
        return 1
    top = pick(rows, n=10)
    json.dump(top, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
