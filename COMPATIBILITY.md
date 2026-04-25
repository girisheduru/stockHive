# StockHive Compatibility Notes

Compatibility wrappers and fallback runtime paths have been removed.

## Canonical paths
### Primary runtime
- `agent-system/scripts/nasdaq-orchestrator-runtime.sh`
- `agent-system/runtime/orchestrator-run-input.json`
- `agent-system/runtime/ORCHESTRATOR_RUNTIME.md`

### Deterministic support
- `agent-system/scripts/pick_top10.py`
- `agent-system/scripts/decision_engine.py`

## Policy
- Keep runtime logic under `agent-system/`.
- Do not reintroduce fallback or deprecated wrapper paths unless explicitly needed.
