#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${JCW_REPO_ROOT:-/opt/jcw}"
OUT_PATH="${JCW_REPO_OUTPUT:-/opt/agent-ops/inventory/repo_inventory.md}"

export JCW_REPO_ROOT="$REPO_ROOT"
export JCW_REPO_OUTPUT="$OUT_PATH"

python3 /opt/agent-ops/scripts/update_repo_inventory.py