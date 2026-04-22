#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from typing import Any


def _fmt_pct(v: Any) -> str:
    if isinstance(v, (int, float)):
        return f"{v * 100:+.1f}%"
    return "n/a"


def format_message(run_date: str, decision: dict[str, Any]) -> str:
    dt = datetime.strptime(run_date, "%Y-%m-%d")
    lines: list[str] = []
    lines.append("** Nasdaq 100 — Daily Top 5 Buys **")
    lines.append(f"Date: {dt.strftime('%d %b %Y')}  |  Local MVP run")
    lines.append("")
    lines.append(f"Market view:  [ {decision.get('market_view', 'UNKNOWN')} ]")
    lines.append(
        f"Breadth {decision.get('breadth_buy_count', 0)}/10 up, "
        f"RSI avg {decision.get('rsi_avg', 0)}, sentiment {decision.get('sent_avg', 0.0):+.2f}"
    )
    lines.append("")
    lines.append("Top 5 Buy Candidates")
    lines.append("--------------------")

    for idx, row in enumerate(decision.get("top5", []), start=1):
        lines.append(
            f"{idx}. {row.get('ticker','?')}  {_fmt_pct(row.get('return_4w'))}  "
            f"RSI {row.get('rsi','n/a')}  PE {row.get('pe','n/a')}"
        )
        if row.get("rationale"):
            lines.append(f"   {row['rationale']}")

    excluded = decision.get("excluded", [])
    if excluded:
        lines.append("")
        lines.append("Excluded")
        lines.append("--------")
        for row in excluded:
            lines.append(f"- {row.get('ticker','?')}: {row.get('reason','n/a')}")

    lines.append("")
    lines.append("--")
    lines.append("StockHive MVP  |  Local test run")
    return "\n".join(lines)


if __name__ == "__main__":
    import json
    import sys

    payload = json.load(sys.stdin)
    print(format_message(payload["run_date"], payload["decision"]))
