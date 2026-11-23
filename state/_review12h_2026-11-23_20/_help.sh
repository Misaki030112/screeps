#!/bin/bash
set -e
cd /workspace/screeps
OUT=state/_review12h_2026-11-23_20
# model / ledger like last review - check how they were invoked from last run notes or scripts
# try common invocations
if [ -x tools/model.py ] || [ -f tools/model.py ]; then
  python3 tools/model.py --help 2>&1 | head -40 || true
fi
echo '======= LEDGER HELP ======='
python3 tools/ledger.py --help 2>&1 | head -40 || true
echo '======= MODEL_W8 HELP ======='
python3 tools/model_w8.py --help 2>&1 | head -40 || true
