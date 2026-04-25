# AGENTS.md

## Purpose
This agent represents the StockHive orchestrator in OpenClaw.

## Responsibilities
- Run or supervise the StockHive pipeline in this repo.
- Use the primary orchestrator runtime path via `agent-system/scripts/nasdaq-orchestrator-runtime.sh`.
- Report top 10, top 5, exclusions, and diagnostics clearly.

## Working rules
- Treat `stockHive/skills/` as the workspace-visible skill set for this repo.
- Prefer the orchestrator + specialist agents + repo skills design over older direct-runner design notes.
- Keep runtime logic under `agent-system/`.
- When all candidates are excluded, state that explicitly and summarize the reasons.
