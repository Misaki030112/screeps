#!/usr/bin/env python3
"""Console silences and listener restarts since last patrol (~22:31 / delivered 22:36:58)."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import re, json

HK = ZoneInfo("Asia/Hong_Kong")
# last 1h patrol already told freezes through 20:49:49-20:59:53 and 19:43:54-19:59:40
# and 17:41:00-18:04:50 and 17:12:37-17:22:45 and 16:44:58-16:59:18 and older,
# plus already-told 监听短中断 19:12:43-19:12:57 and 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20.
# Watch for any newer freezes or short WS after 22:36:58.
CUT = datetime(2026, 11, 22, 23, 32, 40, tzinfo=HK)
console = Path("/workspace/screeps/metrics/console.log")
listener = Path("/workspace/screeps/metrics/listener.out")
pauses = Path("/workspace/screeps/metrics/box_pauses.jsonl")

ts_re = re.compile(r"^(20\d\d-\d\d-\d\d \d\d:\d\d:\d\d)")

def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=HK)

print("=== box_pauses after 22:04:37 (already-told end) ===")
for line in pauses.read_text().splitlines():
    if not line.strip():
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    fr = o.get("from") or o.get("start") or ""
    if fr >= "2026-11-22 22:04:37":
        print(line)

print("=== listener restarts after 22:04:37 ===")
for line in listener.read_text(errors="replace").splitlines():
    m = ts_re.match(line)
    if m and m.group(1) >= "2026-11-22 22:04:37" and ("restart" in line or "frozen" in line or "ping/pong" in line or "ws error" in line or "started" in line.lower()):
        print(line)

times = []
data = console.read_bytes()
chunk = data[-16_000_000:] if len(data) > 16_000_000 else data
text = chunk.decode("utf-8", "replace")
for line in text.splitlines():
    m = ts_re.match(line)
    if m:
        t = parse_ts(m.group(1))
        if t >= datetime(2026, 11, 22, 20, 0, tzinfo=HK):
            times.append((t, line[:220]))

print(f"console lines after 20:00 in tail: {len(times)}")
if times:
    print("first:", times[0][0], times[0][1][:160])
    print("last:", times[-1][0], times[-1][1][:160])

print("=== console silences >=60s after 22:36:58 ===")
for a, b in zip(times, times[1:]):
    gap = (b[0] - a[0]).total_seconds()
    if gap >= 60 and b[0] >= CUT:
        print(f"  {a[0].strftime('%Y-%m-%d %H:%M:%S')} -> {b[0].strftime('%Y-%m-%d %H:%M:%S')} ({int(gap)}s)")
        print(f"    last: {a[1]}")
        print(f"    next: {b[1]}")

print("=== short console gaps 3-59s after 22:36:58 (possible WS) ===")
for a, b in zip(times, times[1:]):
    gap = (b[0] - a[0]).total_seconds()
    if 3 <= gap < 60 and b[0] >= CUT:
        print(f"  {a[0].strftime('%Y-%m-%d %H:%M:%S')} -> {b[0].strftime('%Y-%m-%d %H:%M:%S')} ({int(gap)}s)")
        print(f"    last: {a[1][:160]}")
        print(f"    next: {b[1][:160]}")
