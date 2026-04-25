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
    assert len(top) == 10
    assert top[0]["ticker"] == "F"
    assert top[-1]["ticker"] == "G"


def test_fallback_local_run_produces_expected_outputs() -> None:
    proc = subprocess.run(
        [sys.executable, str(FALLBACK_SCRIPTS / "run_local_mvp.py")],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    result = json.loads(proc.stdout)
    assert result["market_view"] == "BULLISH"
    assert len(result["top5"]) == 5
    excluded = {row["ticker"]: row["reason"] for row in result["excluded"]}
    assert "PANW" in excluded
    assert (OUTPUT / "telegram_message.md").exists()
    message = (OUTPUT / "telegram_message.md").read_text()
    assert "Daily Top 5 Buys" in message
    assert "Excluded" in message
