#!/usr/bin/env python3
"""Console silences and listener restarts since last patrol (~02:24)."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import re, json

HK = ZoneInfo("Asia/Hong_Kong")
# last patrol already told freezes up through 01:47:52-02:03:04 and short gap 02:20:54-02:22:17
CUT = datetime(2026, 11, 21, 6, 22, 57, tzinfo=HK)
console = Path("/workspace/screeps/metrics/console.log")
listener = Path("/workspace/screeps/metrics/listener.out")
pauses = Path("/workspace/screeps/metrics/box_pauses.jsonl")

ts_re = re.compile(r"^(20\d\d-\d\d-\d\d \d\d:\d\d:\d\d)")

def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=HK)

times = []
data = console.read_bytes()
chunk = data[-8_000_000:] if len(data) > 8_000_000 else data
text = chunk.decode("utf-8", "replace")
for line in text.splitlines():
    m = ts_re.match(line)
    if m:
        t = parse_ts(m.group(1))
        if t >= datetime(2026, 11, 21, 6, 0, tzinfo=HK):
            times.append((t, line[:180]))

print(f"console lines after 06:00 in tail: {len(times)}")
print("=== console silences >=60s after 06:22 ===")
for a, b in zip(times, times[1:]):
    gap = (b[0] - a[0]).total_seconds()
    if gap >= 60 and b[0] >= CUT:
        print(f"  {a[0].strftime('%Y-%m-%d %H:%M:%S')} -> {b[0].strftime('%Y-%m-%d %H:%M:%S')} ({int(gap)}s)")
        print(f"    last: {a[1]}")
        print(f"    next: {b[1]}")

print("=== listener.out interesting lines ===")
if listener.exists():
    for line in listener.read_text(errors="replace").splitlines():
        if re.search(r"start|restart|subscribe|rot|yield|slot|freeze|hibern", line, re.I):
            print(line[:240])

print("=== box_pauses after 05:03 ===")
for line in pauses.read_text().splitlines()[-20:]:
    rec = json.loads(line)
    to = datetime.strptime(rec["to"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=HK)
    fr = datetime.strptime(rec["from"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=HK)
    if to >= CUT or fr >= datetime(2026, 11, 21, 5, 3, tzinfo=HK):
        print(rec)

print("=== listener.out tail ===")
if listener.exists():
    for line in listener.read_text(errors="replace").splitlines()[-40:]:
        print(line[:240])
