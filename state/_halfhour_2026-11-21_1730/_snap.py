#!/usr/bin/env python3
import json, os, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
os.chdir("/workspace/screeps")
import db

HK = ZoneInfo("Asia/Hong_Kong")
now = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
print("wrap_at", now)
rooms = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84397101, 84397800
with db.connect() as c:
    window = {}
    for room in rooms:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, TMIN, TMAX),
        ).fetchone()
        window[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
    hole = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN 84397401 AND 84397500"
    ).fetchone()
    tips = {}
    for t in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[t] = c.execute(f"SELECT max(tick) FROM {t}").fetchone()[0]
print("window_db", json.dumps(window))
print("W45N7@84397400", {"distinct": hole[0], "min": hole[1], "max": hole[2], "rows": hole[3]})
print("tips", tips)

listener_line = None
out = subprocess.check_output(["ps", "-eo", "pid,lstart,etime,ppid,cmd"], text=True)
for line in out.splitlines():
    if "tools/listener.py" in line and "grep" not in line:
        listener_line = line.strip()
        print("listener", listener_line)
print("yield_absent", not os.path.exists("metrics/listener_yield_rooms"))
rot = json.loads(open("metrics/listener_rot.json").read())
print("rot", rot)
live = json.load(open("metrics/live.json"))
st = live.get("stats") or {}
print("live", {"updated": live.get("updated"), "slot": live.get("roomSlot"), "stats.t": st.get("t"), "cpu": st.get("cpu"), "b": st.get("b")})
print("last_pause", open("metrics/box_pauses.jsonl").read().splitlines()[-1])
print("last_restart", open("metrics/listener.out").read().splitlines()[-1])
# parse pid/ppid
pid = ppid = started = None
if listener_line:
    parts = listener_line.split()
    pid = int(parts[0])
    ppid = int(parts[5]) if parts[5].isdigit() else int(parts[-2]) if False else None
    # format: PID STARTED... ETIME PPID CMD
    # ps -eo pid,lstart,etime,ppid,cmd
    # lstart is like: Sat Nov 21 17:23:31 2026
    # easier: use ps -o pid,ppid,lstart
snap = {
    "at": now,
    "window_db": window,
    "hole": {"distinct": hole[0], "min": hole[1], "max": hole[2], "rows": hole[3]},
    "tips": tips,
    "rot": rot,
    "yield_absent": not os.path.exists("metrics/listener_yield_rooms"),
    "live_updated": live.get("updated"),
    "roomSlot": live.get("roomSlot"),
    "stats_t": st.get("t"),
    "listener_line": listener_line,
}
open("state/_halfhour_2026-11-21_1730/wrapup_snap.json", "w").write(json.dumps(snap, indent=2) + "\n")
print("wrote snap")
