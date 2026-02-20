#!/usr/bin/env bash
set -euo pipefail

BUCKET="${PAYROLL_GCS_BUCKET:-jcw-labor-timekeeper}"
DB_NAME="${PAYROLL_GCS_DB_NAME:-app.db}"
OUT_DIR="${PAYROLL_RECON_DIR:-/opt/agent-ops/data/payroll/prod}"
EXPORTS_DIR="${PAYROLL_EXPORTS_DIR:-/opt/agent-ops/data/exports}"

mkdir -p "$OUT_DIR"

if ! command -v gsutil >/dev/null 2>&1; then
  echo "gsutil not found; install Google Cloud SDK" >&2
  exit 1
fi

echo "Downloading gs://${BUCKET}/${DB_NAME}"
gsutil -q cp "gs://${BUCKET}/${DB_NAME}" "$OUT_DIR/app.db"

python3 /opt/agent-ops/scripts/payroll_db_summary.py --db "$OUT_DIR/app.db"

if [ -d "$EXPORTS_DIR" ] && ls "$EXPORTS_DIR"/*.xlsx >/dev/null 2>&1; then
  echo "Running reconcile against exports in $EXPORTS_DIR"
  python3 /opt/agent-ops/scripts/payroll_reconcile.py --exports-dir "$EXPORTS_DIR" --db "$OUT_DIR/app.db"
else
  echo "No exports found in $EXPORTS_DIR (skip XLSX reconcile)"
fi