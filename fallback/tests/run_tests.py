#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FALLBACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = FALLBACK_ROOT.parent
SCRIPTS = REPO_ROOT / "agent-system" / "scripts"
FALLBACK_SCRIPTS = FALLBACK_ROOT / "scripts"
OUTPUT = REPO_ROOT / "openclawMVP" / "output"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_pick_top10_returns_10_sorted() -> None:
    rows = [
        {"ticker": "A", "return_4w": 0.1},
        {"ticker": "B", "return_4w": 0.4},
        {"ticker": "C", "return_4w": -0.1},
        {"ticker": "D", "return_4w": 0.2},
        {"ticker": "E", "return_4w": 0.3},
        {"ticker": "F", "return_4w": 0.8},
        {"ticker": "G", "return_4w": 0.05},
        {"ticker": "H", "return_4w": 0.07},
        {"ticker": "I", "return_4w": 0.09},
        {"ticker": "J", "return_4w": 0.11},
        {"ticker": "K", "return_4w": 0.12},
    ]
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "pick_top10.py")],
        input=json.dumps(rows),
        capture_output=True,
        text=True,
        check=True,
    )
    top = json.loads(proc.stdout)
    assert_true(len(top) == 10, "pick_top10 should return 10 rows")
    assert_true(top[0]["ticker"] == "F", "highest return should rank first")
    assert_true(top[-1]["ticker"] == "G", "10th-ranked retained ticker should be last")


def test_fallback_local_run_produces_expected_outputs() -> None:
    proc = subprocess.run(
        [sys.executable, str(FALLBACK_SCRIPTS / "run_local_mvp.py")],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    result = json.loads(proc.stdout)
    assert_true(result["market_view"] == "BULLISH", "market view should be BULLISH for mock data")
    assert_true(len(result["top5"]) == 5, "top5 should contain 5 rows")
    excluded = {row["ticker"]: row["reason"] for row in result["excluded"]}
    assert_true("PANW" in excluded, "PANW should be excluded for stretched PE or overbought RSI")
    assert_true((OUTPUT / "telegram_message.md").exists(), "telegram message artifact should exist")
    message = (OUTPUT / "telegram_message.md").read_text()
    assert_true("Daily Top 5 Buys" in message, "formatted message header missing")
    assert_true("Excluded" in message, "formatted message should include exclusions")


def main() -> int:
    tests = [
        ("pick_top10 sorting", test_pick_top10_returns_10_sorted),
        ("fallback local MVP end-to-end", test_fallback_local_run_produces_expected_outputs),
    ]
    failures: list[str] = []
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except Exception as exc:
            print(f"[FAIL] {name}: {exc}")
            failures.append(name)
    if failures:
        print(f"{len(failures)} test(s) failed")
        return 1
    print("All tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
