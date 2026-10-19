#!/bin/bash
# Keeps the websocket listener alive (restart on exit). Start: nohup tools/run_listener.sh >/dev/null 2>&1 &
# Single loop (flock on metrics/listener.loop.lock); listener.py also refuses a second copy (metrics/listener.lock).
# Restart a stalled listener by killing listener.py only; this loop relaunches it.
cd "$(dirname "$0")/.."
exec 9>metrics/listener.loop.lock
flock -n 9 || { echo "$(date '+%F %T') run_listener.sh already running; exit" >> metrics/listener.out; exit 0; }
echo $$ > metrics/listener.pid
while true; do PYTHONUNBUFFERED=1 .venv/bin/python tools/listener.py >> metrics/listener.out 2>&1 9>&-; echo "$(date '+%F %T') restart" >> metrics/listener.out; sleep 10; done
