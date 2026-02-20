#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${JCW_REPO_ROOT:-/opt/jcw}"
REPO_LIST="${REPO_LIST:-/opt/agent-ops/scripts/repos.txt}"

if [ ! -f "$REPO_LIST" ]; then
  echo "Repo list not found: $REPO_LIST" >&2
  exit 1
fi

mkdir -p "$REPO_ROOT"
export GIT_TERMINAL_PROMPT=0

cloned=0
updated=0
failed=0

while IFS= read -r line || [ -n "$line" ]; do
  line="${line%%#*}"
  line="$(echo "$line" | xargs)"
  if [ -z "$line" ]; then
    continue
  fi

  repo="$line"
  name="${repo##*/}"
  dest="$REPO_ROOT/$name"

  if [ -d "$dest/.git" ]; then
    if git -C "$dest" pull --ff-only; then
      updated=$((updated+1))
    else
      echo "WARN: pull failed for $repo" >&2
      failed=$((failed+1))
    fi
  else
    if git clone "https://github.com/${repo}.git" "$dest"; then
      cloned=$((cloned+1))
    else
      echo "WARN: clone failed for $repo" >&2
      failed=$((failed+1))
    fi
  fi
done < "$REPO_LIST"

echo "Sync complete. Cloned: $cloned, Updated: $updated, Failed: $failed"