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

## Retained artifact area
- `openclawMVP/mocks/`
- `openclawMVP/output/`
- `openclawMVP/live_output/`

## Policy
- Keep runtime logic under `agent-system/`.
- Keep retained mock/output artifacts under `openclawMVP/`.
- Do not reintroduce fallback or deprecated wrapper paths unless explicitly needed.
