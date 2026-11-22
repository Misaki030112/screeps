#!/usr/bin/env python3
"""Console silences and listener restarts since last patrol (~08:18 / delivered 08:28)."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import re, json

HK = ZoneInfo("Asia/Hong_Kong")
# last 1h patrol already told freezes through 07:44:22-08:02:42 and 07:20:32-07:26:28
# and 06:50:03-07:02:08 and older 06:21:56-06:26:26 / 05:52:44-06:04:12 / 05:17 / 04:41 / 04:18 / 03:47 and earlier,
# plus already-told 监听短中断 05:25:19-05:27:20.
# NOT YET TOLD from 09:09 backfill: 08:51:14-09:01:02 (581s).
# Watch for any newer freezes or short WS after 09:01:02 (and after last patrol 08:28).
CUT = datetime(2026, 11, 22, 8, 28, 0, tzinfo=HK)
console = Path("/workspace/screeps/metrics/console.log")
listener = Path("/workspace/screeps/metrics/listener.out")
pauses = Path("/workspace/screeps/metrics/box_pauses.jsonl")

ts_re = re.compile(r"^(20\d\d-\d\d-\d\d \d\d:\d\d:\d\d)")

def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=HK)

print("=== box_pauses after 08:28 ===")
for line in pauses.read_text().splitlines():
    if not line.strip():
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    fr = o.get("from") or o.get("start") or ""
    if fr >= "2026-11-22 08:28:00":
        print(line)

print("=== listener restarts after 08:28 ===")
for line in listener.read_text(errors="replace").splitlines():
    m = ts_re.match(line)
    if m and m.group(1) >= "2026-11-22 08:28:00" and "restart" in line:
        print(line)

times = []
data = console.read_bytes()
chunk = data[-16_000_000:] if len(data) > 16_000_000 else data
text = chunk.decode("utf-8", "replace")
for line in text.splitlines():
    m = ts_re.match(line)
    if m:
        t = parse_ts(m.group(1))
        if t >= datetime(2026, 11, 22, 8, 10, tzinfo=HK):
            times.append((t, line[:220]))

print(f"console lines after 08:10 in tail: {len(times)}")
if times:
    print("first:", times[0][0], times[0][1][:160])
    print("last:", times[-1][0], times[-1][1][:160])

print("=== console silences >=60s after 08:28 ===")
for a, b in zip(times, times[1:]):
    gap = (b[0] - a[0]).total_seconds()
    if gap >= 60 and b[0] >= CUT:
        print(f"  {a[0].strftime('%Y-%m-%d %H:%M:%S')} -> {b[0].strftime('%Y-%m-%d %H:%M:%S')} ({int(gap)}s)")
        print(f"    last: {a[1]}")
        print(f"    next: {b[1]}")

print("=== short console gaps 3-59s after 08:28 (possible WS) ===")
for a, b in zip(times, times[1:]):
    gap = (b[0] - a[0]).total_seconds()
    if 3 <= gap < 60 and b[0] >= CUT:
        print(f"  {a[0].strftime('%Y-%m-%d %H:%M:%S')} -> {b[0].strftime('%Y-%m-%d %H:%M:%S')} ({int(gap)}s)")
        print(f"    last: {a[1][:160]}")
        print(f"    next: {b[1][:160]}")
