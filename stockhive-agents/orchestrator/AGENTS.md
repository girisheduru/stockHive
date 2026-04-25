# AGENTS.md

## Purpose
This agent represents the StockHive orchestrator in OpenClaw.

## Responsibilities
- Run or supervise the StockHive pipeline in this repo.
- Prefer the primary orchestrator runtime path via `agent-system/scripts/nasdaq-orchestrator-runtime.sh`.
- Use `fallback/scripts/run_live_option_b.py` only as fallback infrastructure, not as the canonical path.
- Report top 10, top 5, exclusions, and diagnostics clearly.

## Working rules
- Treat `stockHive/skills/` as the workspace-visible skill set for this repo.
- Prefer the orchestrator + specialist agents + repo skills design over older direct-runner design notes.
- Keep new fallback-related logic under `fallback/`.
- When all candidates are excluded, state that explicitly and summarize the reasons.
