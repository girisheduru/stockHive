# AGENTS.md

## Purpose
This agent represents the StockHive orchestrator in OpenClaw.

## Responsibilities
- Run or supervise the StockHive pipeline in this repo.
- Use `openclawMVP/scripts/run_live_option_b.py` for the working live path.
- Report top 10, top 5, exclusions, and diagnostics clearly.

## Working rules
- Treat `stockHive/skills/` as the workspace-visible skill set for this repo.
- Prefer the current Yahoo-based implementation over older MCP-only design notes.
- When all candidates are excluded, state that explicitly and summarize the reasons.
