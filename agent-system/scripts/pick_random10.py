#!/usr/bin/env python3
"""
pick_random10.py — deterministically randomize candidate rows and emit up to 10.

Reads a JSON array on stdin and writes a JSON array to stdout.
Rows must contain at least a `ticker` field.

Input:  [{"ticker":"AAPL","return_4w":0.053,"last_close":...}, ...]
Output: up to 10 rows in deterministic pseudo-random order.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime
from typing import Any


def pick(rows: list[dict[str, Any]], n: int = 10, seed: str | None = None) -> list[dict[str, Any]]:
    cleaned = [r for r in rows if isinstance(r.get("ticker"), str) and r.get("ticker")]
    run_seed = seed or datetime.now().strftime("%Y-%m-%d")
    rng = random.Random(run_seed)
    shuffled = cleaned[:]
    rng.shuffle(shuffled)
    return shuffled[:n]


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
