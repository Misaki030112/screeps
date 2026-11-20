#!/usr/bin/env python3
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import db, history_backfill as hb

HK = ZoneInfo("Asia/Hong_Kong")
c = db.connect()

def p(*a):
    print(*a, flush=True)

p("=== audit head ===")
print(Path("state/_patrol_2026-11-20_1923/audit_patrol.txt").read_text()[:3500])

p("=== motion 1h head ===")
lines = Path("state/_patrol_2026-11-20_1923/motion_1h.txt").read_text().splitlines()
print("\n".join(lines[:35]))
p("=== motion 2h head ===")
lines2 = Path("state/_patrol_2026-11-20_1923/motion_2h.txt").read_text().splitlines()
print("\n".join(lines2[:35]))

p("=== official_retry hour cov / freeze fills / wrote ===")
for line in Path("state/_patrol_2026-11-20_1923/official_retry.out").read_text().splitlines():
    if "hour-window" in line or line.startswith("  W4") and "/" in line and "post" not in line and "pre" not in line:
        print(line)
    if line.startswith("  fill ") or line.startswith("wrote") or "hour_cov" in line:
        print(line)

p("=== W47 progress around freezes ===")
rows = c.execute("""
  SELECT tick, ts, progress, storage, cpu, creeps
  FROM room_stats WHERE room='W47N8' AND tick>=84378380 ORDER BY tick
""").fetchall()
prev = None
for r in rows:
    tick, ts, prog, stor, cpu, creeps = r
    nup = None
    if isinstance(creeps, dict):
        nup = creeps.get("w8upgrader") or creeps.get("wupgrader")
    elif creeps:
        try:
            d = creeps if isinstance(creeps, dict) else json.loads(creeps) if isinstance(creeps, str) else None
            if d: nup = d.get("w8upgrader") or d.get("wupgrader")
        except Exception:
            nup = creeps
    dprog = (prog - prev[2]) if prev else None
    dt = (tick - prev[0]) if prev else None
    et = (dprog/dt) if dprog is not None and dt else None
    # print around gaps or nup!=2 or every sample near freezes
    interesting = (prev is None or (dt and dt>15) or (nup and nup!=2) or tick in (84378420,84378620,84378860,84378970,84379010)
                   or (tick>=84378700))
    if interesting:
        p(f"  {tick} {ts} p={prog} stor={stor} d={dprog} dt={dt} et={et and round(et,2)} w8up={nup} cpu={cpu}")
    prev = r

p("=== home progress around freezes / nUp ===")
rows = c.execute("""
  SELECT tick, ts, progress, storage, cpu, creeps
  FROM room_stats WHERE room='W46N8' AND tick>=84378380 ORDER BY tick
""").fetchall()
prev = None
for r in rows:
    tick, ts, prog, stor, cpu, creeps = r
    nup = None
    if isinstance(creeps, dict):
        nup = creeps.get("upgrader")
    dprog = (prog - prev[2]) if prev else None
    dt = (tick - prev[0]) if prev else None
    et = (dprog/dt) if dprog is not None and dt else None
    interesting = (prev is None or (dt and dt>15) or tick>=84378700)
    if interesting:
        p(f"  {tick} {ts} p={prog} stor={stor} d={dprog} dt={dt} et={et and round(et,2)} nUp={nup} cpu={cpu}")
    prev = r

p("=== official fill of freeze ranges ===")
freezes = [
    ("18:46-18:58", 84378421, 84378619),
    ("19:16-19:23", 84378861, 84378969),
]
for name, lo, hi in freezes:
    p(f"-- {name} {lo}..{hi} want={hi-lo+1} --")
    for room in ("W46N8","W47N8","W45N8","W45N7","W47N7"):
        n = c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s", (room,lo,hi)).fetchone()[0]
        p(f"  {room} {n}/{hi-lo+1}")

p("=== later room_stats after 84379010 ===")
for room in ("W46N8","W47N8"):
    rows = c.execute("""
      SELECT tick, ts, progress, storage, cpu, bucket, hostiles, sites, creeps
      FROM room_stats WHERE room=%s AND tick>84379010 ORDER BY tick
    """, (room,)).fetchall()
    p(room, "later_n", len(rows))
    for r in rows[-8:]:
        p(" ", r[0], r[1], "p", r[2], "stor", r[3], "cpu", r[4], "bkt", r[5], "host", r[6], "sites", r[7], "creeps", r[8])

p("=== freshness now ===")
for table in ("room_stats","creep_ticks","creep_cpu"):
    p(table, c.execute(f"SELECT max(tick), max(ts), now()-max(ts) FROM {table}").fetchone())

p("=== w8up=3 periods since 84378090 ===")
# parse creeps json
rows = c.execute("SELECT tick, ts, storage, creeps FROM room_stats WHERE room='W47N8' AND tick>=84378090 ORDER BY tick").fetchall()
cur = None
start = None
for tick, ts, stor, creeps in rows:
    n = None
    if isinstance(creeps, dict):
        n = creeps.get("w8upgrader") or creeps.get("wupgrader")
    if n != cur:
        if cur is not None:
            p(f"  w8up={cur} {start[0]}..{tick} stor_start={start[2]} at {start[1]}")
        cur = n
        start = (tick, ts, stor)
if cur is not None and start:
    p(f"  w8up={cur} {start[0]}..end stor_start={start[2]} at {start[1]} last={rows[-1][0]}")

p("=== defender path summary ===")
for r in c.execute("""
  SELECT tick, room, x, y, hits, state
  FROM creep_ticks
  WHERE creep='defender84377983'
  ORDER BY tick
"""):
    pass
# just transitions
prev = None
rows = c.execute("""
  SELECT tick, room, x, y, hits
  FROM creep_ticks
  WHERE creep='defender84377983'
  ORDER BY tick
""").fetchall()
p("n", len(rows), "first", rows[0] if rows else None, "last", rows[-1] if rows else None)
for r in rows:
    if prev is None or r[1]!=prev[1]:
        p("  enter", r)
    prev = r
# last in each room
p("=== labs mineral stocks from last probe events skip ===")
# leave for live q

p("=== retry NEW just-published 404s W45N8@84378900 W47N7@84378900 ===")
# will do via hb after this print; separate later
