# StockHive Compatibility Notes

This file tracks compatibility wrappers retained during the runtime restructure.

## Canonical paths
### Primary runtime
- `agent-system/scripts/nasdaq-orchestrator-runtime.sh`
- `agent-system/runtime/orchestrator-run-input.json`
- `agent-system/runtime/ORCHESTRATOR_RUNTIME.md`

### Fallback runtime
- `fallback/scripts/nasdaq-daily-run.sh`
- `fallback/scripts/run_live_option_b.py`
- `fallback/scripts/run_local_mvp.py`
- `fallback/tests/run_tests.py`
- `fallback/tests/test_agent_system.py`

## Deprecated compatibility wrappers
These remain only to avoid abrupt breakage of older references.

- `agent-system/scripts/nasdaq-daily-run.sh`

## Policy
- Add new fallback implementations under `fallback/`.
- Do not add new real runtime logic to deprecated wrapper paths.
- Prefer canonical paths in docs, schedules, and future edits.
