#!/usr/bin/env bash
# DEPRECATED compatibility wrapper for the StockHive fallback runner.
# Canonical fallback path: fallback/scripts/nasdaq-daily-run.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_DIR"

exec ./fallback/scripts/nasdaq-daily-run.sh "$@"
