#!/usr/bin/env python3
import re, json
from pathlib import Path
from collections import defaultdict

D = Path("/workspace/screeps/state/_patrol_2026-11-24_0221")
text = (D / "backfill_first.txt").read_text()
rows = re.findall(r"^\s+(ok|404)\s+(\w+)@(\d+)(?:\s+ticks=(\d+)\s+ts=(\d+))?", text, re.M)
by_base = defaultdict(dict)
missing = []
ok_count = 0
for st, room, base, ticks, ts in rows:
    base = int(base)
    if st == "404":
        missing.append((room, base))
        by_base[base][room] = None
    else:
        ok_count += 1
        by_base[base][room] = int(ts)

bases = sorted(by_base)
W46 = {b: by_base[b]["W46N8"] for b in bases if by_base[b].get("W46N8")}
MIN_ALL = {}
MIN_ALL_ROOM = {}
for b in bases:
    present = {r: ts for r, ts in by_base[b].items() if ts is not None}
    if present:
        room = min(present, key=lambda r: present[r])
        MIN_ALL[b] = present[room]
        MIN_ALL_ROOM[b] = room

b0, b1 = bases[0], bases[1]
first = (MIN_ALL[b1] - MIN_ALL[b0]) / 1000.0 / (b1 - b0)
head = text.splitlines()[0]
print("head", head)
print("bases", bases[0], bases[-1], "n", len(bases))
print("ok_count", ok_count, "total_gets", ok_count + len(missing), "missing", missing)
print("first_interval", first, "rounded", round(first, 3))
print("W46 first two", W46[b0], W46[b1], "w46_first", (W46[b1] - W46[b0]) / 1000 / 100)

parsed = {
    "head": head,
    "ok_count": ok_count,
    "total_gets": ok_count + len(missing),
    "missing_chunks": [{"room": r, "base": b} for r, b in missing],
    "n_bases": len(bases),
    "first_base": bases[0],
    "last_base": bases[-1],
    "TMIN": bases[0] + 1,
    "TMAX": bases[-1] + 100,
    "tick_s_first_exact": first,
    "W46": W46,
    "MIN_ALL": MIN_ALL,
    "MIN_ALL_ROOM": MIN_ALL_ROOM,
}
(D / "backfill_first_parsed.json").write_text(json.dumps(parsed, indent=2) + "\n")
print("wrote parsed")

def lit(d, rooms=None):
    lines = ["{"]
    for b in sorted(d):
        extra = f"  # {rooms[b]}" if rooms else ""
        lines.append(f"    {b}: {d[b]},{extra}")
    lines.append("}")
    return "\n".join(lines)

(D / "tick_s_maps.py.txt").write_text(
    "W46 = " + lit(W46) + "\nMIN_ALL = " + lit(MIN_ALL, MIN_ALL_ROOM) + "\n"
)
print("wrote tick_s_maps")
