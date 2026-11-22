#!/usr/bin/env python3
"""Console silences and listener restarts since last patrol (~16:32 / delivered 16:33:58)."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import re, json

HK = ZoneInfo("Asia/Hong_Kong")
# last 1h patrol already told freezes through 16:15:02-16:22:09 and 14:47:50-15:01:16
# and 14:15:32-14:20:01 and 13:48:49-13:57:59 and 13:16:57-13:26:20 and 12:51:44-13:03:45
# and 12:20:45-12:23:11 and 11:45:08-12:00:47 and 10:45:15-11:06:19 and 10:16:39-10:22:23
# and 09:41:41-09:59:05 and older,
# plus already-told 监听短中断 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20.
# NOT YET TOLD from 17:07 backfill: 16:44:58-16:59:18 (850s), listener restart 16:59:21 / python 2562267 16:59:30.
# Watch for any newer freezes or short WS after 16:33:58.
CUT = datetime(2026, 11, 22, 16, 33, 58, tzinfo=HK)
console = Path("/workspace/screeps/metrics/console.log")
listener = Path("/workspace/screeps/metrics/listener.out")
pauses = Path("/workspace/screeps/metrics/box_pauses.jsonl")

ts_re = re.compile(r"^(20\d\d-\d\d-\d\d \d\d:\d\d:\d\d)")

def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=HK)

print("=== box_pauses after 16:22 ===")
for line in pauses.read_text().splitlines():
    if not line.strip():
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    fr = o.get("from") or o.get("start") or ""
    if fr >= "2026-11-22 16:22:09":
        print(line)

print("=== listener restarts after 16:22 ===")
for line in listener.read_text(errors="replace").splitlines():
    m = ts_re.match(line)
    if m and m.group(1) >= "2026-11-22 16:22:09" and "restart" in line:
        print(line)

times = []
data = console.read_bytes()
chunk = data[-16_000_000:] if len(data) > 16_000_000 else data
text = chunk.decode("utf-8", "replace")
for line in text.splitlines():
    m = ts_re.match(line)
    if m:
        t = parse_ts(m.group(1))
        if t >= datetime(2026, 11, 22, 15, 0, tzinfo=HK):
            times.append((t, line[:220]))

print(f"console lines after 15:00 in tail: {len(times)}")
if times:
    print("first:", times[0][0], times[0][1][:160])
    print("last:", times[-1][0], times[-1][1][:160])

print("=== console silences >=60s after 16:33 ===")
for a, b in zip(times, times[1:]):
    gap = (b[0] - a[0]).total_seconds()
    if gap >= 60 and b[0] >= CUT:
        print(f"  {a[0].strftime('%Y-%m-%d %H:%M:%S')} -> {b[0].strftime('%Y-%m-%d %H:%M:%S')} ({int(gap)}s)")
        print(f"    last: {a[1]}")
        print(f"    next: {b[1]}")

print("=== short console gaps 3-59s after 16:33 (possible WS) ===")
for a, b in zip(times, times[1:]):
    gap = (b[0] - a[0]).total_seconds()
    if 3 <= gap < 60 and b[0] >= CUT:
        print(f"  {a[0].strftime('%Y-%m-%d %H:%M:%S')} -> {b[0].strftime('%Y-%m-%d %H:%M:%S')} ({int(gap)}s)")
        print(f"    last: {a[1][:160]}")
        print(f"    next: {b[1][:160]}")
