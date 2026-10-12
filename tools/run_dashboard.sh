#!/bin/bash
# Serves the dashboard at http://127.0.0.1:8787/tools/dashboard.html (box-local)
cd "$(dirname "$0")/.."
cp data/terrain_W46N8.txt terrain.txt
exec .venv/bin/python -m http.server 8787 --bind 127.0.0.1
