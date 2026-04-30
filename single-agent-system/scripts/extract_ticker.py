#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load_universe(path: str) -> set[str]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("tickers", [])
    else:
        items = []

    universe: set[str] = set()
    for item in items:
        if isinstance(item, str):
            universe.add(item.upper())
        elif isinstance(item, dict) and isinstance(item.get("ticker"), str):
            universe.add(item["ticker"].upper())
    return universe


def extract(text: str, universe: set[str]) -> str | None:
    candidates = re.findall(r"\b[A-Za-z]{1,5}\b", text.upper())
    for token in candidates:
        if token in universe:
            return token
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--universe", required=True)
    args = parser.parse_args()

    universe = load_universe(args.universe)
    ticker = extract(args.text, universe)

    if not ticker:
        json.dump({"ok": False, "reason": "no_valid_ticker_found"}, sys.stdout)
        sys.stdout.write("\n")
        return 2

    json.dump({"ok": True, "ticker": ticker}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
