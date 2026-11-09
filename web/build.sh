#!/usr/bin/env bash
# Build the browser version with pygbag into build/self-driving-racer/build/web/.
#
#   bash web/build.sh            # build only
#   bash web/build.sh --serve    # build, then serve on http://localhost:8000
set -euo pipefail

# CI installs pygbag with pip; locally: uv run --no-project --with pygbag==0.9.3 bash web/build.sh

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/build/self-driving-racer"

rm -rf "$APP"
mkdir -p "$APP/src" "$APP/assets"
cp "$ROOT/web/main.py" "$APP/main.py"
cp -R "$ROOT/src/racer" "$APP/src/racer"
rm -rf "$APP/src/racer/__pycache__"
cp -R "$ROOT/src/weights" "$APP/src/weights"
# Only the sprites the game loads; the others would just slow the download.
cp "$ROOT/assets/car-rear.png" "$ROOT/assets/car-rear-turn-left-subtle.png" "$APP/assets/"
cp -R "$ROOT/ghosts" "$APP/ghosts"
cp "$ROOT/leaderboard.json" "$APP/leaderboard.json"

if [[ "${1:-}" == "--serve" ]]; then
    python -m pygbag --ume_block 0 "$APP"
else
    python -m pygbag --build --ume_block 0 "$APP"
fi
