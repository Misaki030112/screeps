#!/bin/sh
# Commit routine-written artifacts (patrol state, sim snapshot, terrain caches, route map) so they never block deploys.
# Usage: sh scripts/commit_state.sh   (safe to run every patrol; no-op when clean; never touches src/)
cd "$(dirname "$0")/.." || exit 1
git add state/ data/ docs/model_routes.png 2>/dev/null
git diff --cached --quiet || git commit -qm "routine state $(date '+%F %H:%M')" -- state data docs/model_routes.png
