#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${JCW_REPO_ROOT:-/opt/jcw}"
REPO_LIST="${REPO_LIST:-/opt/agent-ops/scripts/repos.txt}"
OUT_ROOT="${CRAWL_OUT_ROOT:-/opt/agent-ops/data/crawls}"
MAX_BYTES="${CRAWL_MAX_BYTES:-2097152}"

if [ ! -f "$REPO_LIST" ]; then
  echo "Repo list not found: $REPO_LIST" >&2
  exit 1
fi

mkdir -p "$OUT_ROOT"
ts="$(date -u +%Y%m%d-%H%M%S)"
outdir="$OUT_ROOT/$ts"
mkdir -p "$outdir"

indexed=0
failed=0
missing=0

while IFS= read -r line || [ -n "$line" ]; do
  line="${line%%#*}"
  line="$(echo "$line" | xargs)"
  if [ -z "$line" ]; then
    continue
  fi

  repo="$line"
  name="${repo##*/}"
  repo_path="$REPO_ROOT/$name"
  if [ ! -d "$repo_path" ]; then
    echo "WARN: repo missing at $repo_path" >&2
    missing=$((missing+1))
    continue
  fi

  db="$outdir/repo_${name}.sqlite"
  if python3 /opt/agent-ops/scripts/crawl_repo.py --root "$repo_path" --db "$db" --max-bytes "$MAX_BYTES"; then
    indexed=$((indexed+1))
  else
    echo "WARN: crawl failed for $repo" >&2
    failed=$((failed+1))
  fi
done < "$REPO_LIST"

python3 /opt/agent-ops/scripts/merge_indexes.py --input-dir "$outdir" --output "$outdir/repo_unified.sqlite" || true
ln -sfn "$outdir" "$OUT_ROOT/latest"

echo "Crawl complete. Indexed: $indexed, Missing: $missing, Failed: $failed"
echo "Outputs: $outdir"