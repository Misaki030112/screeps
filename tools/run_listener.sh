#!/bin/bash
# Keeps the websocket listener alive (restart on exit). Start: nohup tools/run_listener.sh >/dev/null 2>&1 &
# Single loop (flock on metrics/listener.loop.lock); listener.py also refuses a second copy (metrics/listener.lock).
# Restart a stalled listener by killing listener.py only; this loop relaunches it.
# Peacetime the listener holds ONE room slot (W46N8:W47N8:W45N8:W45N7 = 5:5:1:1). Do not start a second listener.
# Wartime, when the Screeps指挥官 bot is live-commanding: touch metrics/listener_yield_rooms
# (room subscription drops within ~5s; console and cpu stay). Commander takes the battle rooms.
# Handback: commander unsubscribes, then rm metrics/listener_yield_rooms. See docs/COMMANDER.md.
cd "$(dirname "$0")/.."
exec 9>metrics/listener.loop.lock
flock -n 9 || { echo "$(date '+%F %T') run_listener.sh already running; exit" >> metrics/listener.out; exit 0; }
echo $$ > metrics/listener.pid
while true; do PYTHONUNBUFFERED=1 .venv/bin/python tools/listener.py >> metrics/listener.out 2>&1 9>&-; echo "$(date '+%F %T') restart" >> metrics/listener.out; sleep 10; done
