#!/usr/bin/env python3
"""Console silences and listener restarts since last patrol (~22:35)."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import re, json

HK = ZoneInfo("Asia/Hong_Kong")
# last 1h patrol already told freezes through 21:42:29-22:01:09 and 22:14:12-22:26:30.
# NOT YET TOLD (must fold): 22:49:18-22:59:56 (634s) from 23:10 backfill,
# and NEW 23:20:38-23:24:23 (224s) seen in box_pauses at patrol start. Watch for any newer.
CUT = datetime(2026, 11, 21, 22, 35, 0, tzinfo=HK)
console = Path("/workspace/screeps/metrics/console.log")
listener = Path("/workspace/screeps/metrics/listener.out")
pauses = Path("/workspace/screeps/metrics/box_pauses.jsonl")

ts_re = re.compile(r"^(20\d\d-\d\d-\d\d \d\d:\d\d:\d\d)")

def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=HK)

print("=== box_pauses after 22:00 ===")
for line in pauses.read_text().splitlines():
    if not line.strip():
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    fr = o.get("from") or o.get("start") or ""
    if fr >= "2026-11-21 21:00:00":
        print(line)

print("=== listener restarts after 22:00 ===")
for line in listener.read_text(errors="replace").splitlines():
    m = ts_re.match(line)
    if m and m.group(1) >= "2026-11-21 21:00:00":
        print(line)

times = []
data = console.read_bytes()
chunk = data[-12_000_000:] if len(data) > 12_000_000 else data
text = chunk.decode("utf-8", "replace")
for line in text.splitlines():
    m = ts_re.match(line)
    if m:
        t = parse_ts(m.group(1))
        if t >= datetime(2026, 11, 21, 21, 0, tzinfo=HK):
            times.append((t, line[:220]))

print(f"console lines after 22:00 in tail: {len(times)}")
if times:
    print("first:", times[0][0], times[0][1][:160])
    print("last:", times[-1][0], times[-1][1][:160])

print("=== console silences >=60s after 22:35 ===")
for a, b in zip(times, times[1:]):
    gap = (b[0] - a[0]).total_seconds()
    if gap >= 60 and b[0] >= CUT:
        print(f"  {a[0].strftime('%Y-%m-%d %H:%M:%S')} -> {b[0].strftime('%Y-%m-%d %H:%M:%S')} ({int(gap)}s)")
        print(f"    last: {a[1]}")
        print(f"    next: {b[1]}")

print("=== short console gaps 3-59s after 22:35 (possible WS) ===")
for a, b in zip(times, times[1:]):
    gap = (b[0] - a[0]).total_seconds()
    if 3 <= gap < 60 and b[0] >= CUT:
        print(f"  {a[0].strftime('%Y-%m-%d %H:%M:%S')} -> {b[0].strftime('%Y-%m-%d %H:%M:%S')} ({int(gap)}s)")
        print(f"    last: {a[1][:160]}")
        print(f"    next: {b[1][:160]}")
