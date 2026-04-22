#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

MVP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MVP_ROOT.parent
MOCKS = MVP_ROOT / "mocks"
OUTPUT = MVP_ROOT / "output"
SCRIPTS = REPO_ROOT / "agent-system" / "scripts"


def log(stage: str, message: str) -> None:
    print(f"{stage} {message}", file=sys.stderr)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def run_pick_top10(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "pick_top10.py")],
        input=json.dumps(rows),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_decision_engine(payload: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "decision_engine.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def build_merged_payload(run_date: str, top10: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "date": run_date,
        "top10": top10,
        "technical": read_json(MOCKS / "mock_technical.json"),
        "fundamental": read_json(MOCKS / "mock_fundamental.json"),
        "sentiment": read_json(MOCKS / "mock_sentiment.json"),
    }


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    run_date = datetime.now().strftime("%Y-%m-%d")

    log("[STAGE 1/6]", "Loading mock market data and ranking top 10.")
    market_rows = read_json(MOCKS / "mock_market_data.json")
    top10 = run_pick_top10(market_rows)
    (OUTPUT / "top10.json").write_text(json.dumps(top10, indent=2) + "\n")

    log("[STAGE 2/6]", "Loading mock subagent outputs in parallel.")
    with ThreadPoolExecutor(max_workers=3) as pool:
        tech_f = pool.submit(read_json, MOCKS / "mock_technical.json")
        fund_f = pool.submit(read_json, MOCKS / "mock_fundamental.json")
        sent_f = pool.submit(read_json, MOCKS / "mock_sentiment.json")
        technical = tech_f.result()
        fundamental = fund_f.result()
        sentiment = sent_f.result()

    (OUTPUT / "technical.json").write_text(json.dumps(technical, indent=2) + "\n")
    (OUTPUT / "fundamental.json").write_text(json.dumps(fundamental, indent=2) + "\n")
    (OUTPUT / "sentiment.json").write_text(json.dumps(sentiment, indent=2) + "\n")

    log("[STAGE 3/6]", "Aggregating subagent outputs.")
    merged = {
        "date": run_date,
        "top10": top10,
        "technical": technical,
        "fundamental": fundamental,
        "sentiment": sentiment,
    }
    (OUTPUT / "merged.json").write_text(json.dumps(merged, indent=2) + "\n")

    log("[STAGE 4/6]", "Running decision engine.")
    decision = run_decision_engine(merged)
    (OUTPUT / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")

    log("[STAGE 5/6]", "Formatting local publish message.")
    from telegram_formatter import format_message

    message = format_message(run_date, decision)
    (OUTPUT / "telegram_message.md").write_text(message + "\n")

    log("[STAGE 6/6]", "Writing orchestrator result.")
    result = {
        "run_date": run_date,
        "market_view": decision["market_view"],
        "top5": decision["top5"],
        "excluded": decision["excluded"],
        "telegram_message_id": "local-mvp-dry-run",
    }
    (OUTPUT / "orchestrator_result.json").write_text(json.dumps(result, indent=2) + "\n")
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
