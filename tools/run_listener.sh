#!/bin/bash
# Keeps the websocket listener alive (restart on exit). Start: nohup tools/run_listener.sh >/dev/null 2>&1 &
cd "$(dirname "$0")/.."
echo $$ > metrics/listener.pid
while true; do PYTHONUNBUFFERED=1 .venv/bin/python tools/listener.py >> metrics/listener.out 2>&1; echo "$(date '+%F %T') restart" >> metrics/listener.out; sleep 10; done
