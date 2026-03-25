#!/usr/bin/env bash
set -euo pipefail

# Determine whether build/test jobs should run based on changed files.
# Outputs run_tests=true/false to $GITHUB_OUTPUT.
#
# Required env vars:
#   EVENT_NAME   - github.event_name (push or pull_request)
#   BASE_SHA     - github.event.pull_request.base.sha (PRs only)
#   BEFORE_SHA   - github.event.before (push only, previous HEAD)

# Determine changed files
if [[ "$EVENT_NAME" == "push" ]]; then
  # All-zero BEFORE_SHA means new branch; run everything
  if [[ "$BEFORE_SHA" == "0000000000000000000000000000000000000000" ]]; then
    echo "run_tests=true" >> "$GITHUB_OUTPUT"
    echo "New branch push: running all jobs"
    exit 0
  fi
  changed_files="$(git diff --name-only "$BEFORE_SHA" HEAD)"
else
  changed_files="$(git diff --name-only "${BASE_SHA}...HEAD")"
fi

code_changed=0
while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  # Skip docs subtree
  [[ "$file" =~ ^docs/ ]] && continue
  code_changed=1
  break
done <<< "$changed_files"

if [[ $code_changed -eq 1 ]]; then
  echo "run_tests=true" >> "$GITHUB_OUTPUT"
  echo "Code changes detected: running all jobs"
else
  echo "run_tests=false" >> "$GITHUB_OUTPUT"
  echo "Docs-only changes: skipping build and test jobs"
fi
