#!/usr/bin/env python3
from pathlib import Path
import re

src = Path("/workspace/screeps/state/_halfhour_2026-11-23_0800/tick_s_check.py")
dst = Path("/workspace/screeps/state/_patrol_2026-11-23_0821/tick_s_check.py")
text = src.read_text()

W46 = {}
MIN_ALL = {}
who = {}
pat = re.compile(r"  ok  (W\d+N\d+)@(\d+) ticks=\d+ ts=(\d+)")
for line in Path("/workspace/screeps/state/_patrol_2026-11-23_0821/backfill_first.txt").read_text().splitlines():
    m = pat.match(line)
    if not m:
        continue
    room, base, ts = m.group(1), int(m.group(2)), int(m.group(3))
    if room == "W46N8":
        W46[base] = ts
    if base not in MIN_ALL or ts < MIN_ALL[base]:
        MIN_ALL[base] = ts
        who[base] = room

bases = sorted(MIN_ALL)
first_s = (MIN_ALL[bases[1]] - MIN_ALL[bases[0]]) / 1000.0 / (bases[1] - bases[0])
print("bases", bases[0], bases[-1], "n", len(bases), "first_s", round(first_s, 5), "W46", len(W46))

def fmt_dict(d, comments=None):
    lines = ["{"]
    for k in sorted(d):
        c = ("  # " + comments[k]) if comments and k in comments else ""
        lines.append(f"    {k}: {d[k]},{c}")
    lines.append("}")
    return "\n".join(lines)

text = text.replace('DIR = ROOT / "state" / "_halfhour_2026-11-23_0800"',
                    'DIR = ROOT / "state" / "_patrol_2026-11-23_0821"')
i = text.find("W46 = {")
j = text.find("TMIN, TMAX")
assert i > 0 and j > i
w46_block = "W46 = " + fmt_dict(W46) + "\n\n"
min_block = "MIN_ALL = " + fmt_dict(MIN_ALL, who) + "\n\n"
rest = text[j:]
rest = rest.replace("TMIN, TMAX = 84429901, 84430600", "TMIN, TMAX = 84427701, 84430900")
old_first = "TICK_S_FIRST = (MIN_ALL[84430000] - MIN_ALL[84429900]) / 1000.0 / 100  # script printed 4.298, exact 4.29750"
new_first = f"TICK_S_FIRST = (MIN_ALL[{bases[1]}] - MIN_ALL[{bases[0]}]) / 1000.0 / {bases[1]-bases[0]}  # script printed 4.403, exact {first_s:.5f}"
if old_first not in rest:
    raise SystemExit("TICK_S_FIRST line not found")
rest = rest.replace(old_first, new_first)
rest = rest.replace("GT_FIRST = 84430669", "GT_FIRST = 84430949")
rest = rest.replace(
    "TS_REALIGNED_FIRST = 3859  # first-pass realign moved 3859 rows (inserted=17603 already_in_db=5606)",
    "TS_REALIGNED_FIRST = 0  # first-pass realign crashed on Timescale chunk constraint; tick_s_check applies chunk-safe",
)
rest = rest.replace(
    "PREV_LATER_MEAN = 4.67464  # tick_s_in_use from quiet 0700 half-hour",
    "PREV_LATER_MEAN = 4.29750  # tick_s_in_use from quiet 0800 half-hour",
)
dst.write_text(text[:i] + w46_block + min_block + rest)
compile(dst.read_text(), str(dst), "exec")
print("wrote", dst, "bytes", dst.stat().st_size, "syntax ok")
print("DIR check", ' "_patrol_2026-11-23_0821"' in dst.read_text() or "_patrol_2026-11-23_0821" in dst.read_text())
