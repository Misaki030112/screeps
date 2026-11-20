#!/usr/bin/env python3
from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_0230")
text = (DIR / "history_backfill_first_attempt.txt").read_text()

pat = re.compile(r"  ok  (W\d+N\d+)@(\d+) ticks=(\d+) ts=(\d+)")
by = {}
for m in pat.finditer(text):
    room, base = m.group(1), int(m.group(2))
    ts = int(m.group(4))
    by.setdefault(base, {})[room] = ts
missing = [(r, int(b)) for r, b in re.findall(r"  404 (W\d+N\d+)@(\d+)", text)]
gt = int(re.search(r"game\.time=(\d+)", text).group(1))
rec = re.search(r"reconstructed ticks=(\d+)\.\.(\d+) \((\d+)\)", text)
tmin, tmax, nticks = int(rec.group(1)), int(rec.group(2)), int(rec.group(3))
ins_m = re.search(r"^inserted=(\d+)", text, re.M)
ins = int(ins_m.group(1)) if ins_m else 0
already = int(re.search(r"already_in_db=(\d+)", text).group(1))
printed = re.search(r"tick_s=([0-9.]+)", text).group(1)
realign = int(re.search(r"ts_realigned=(\d+)", text).group(1))
print("bases", sorted(by))
print("missing", missing, "gt", gt, "window", tmin, tmax, nticks)
print("inserted", ins, "already", already, "tick_s", printed, "realign", realign)

MIN_ALL = {b: min(rooms.values()) for b, rooms in by.items()}
W46 = {b: rooms["W46N8"] for b, rooms in by.items() if "W46N8" in rooms}
bases = sorted(MIN_ALL)
b0, b1 = bases[0], bases[1]
first_ts = (MIN_ALL[b1] - MIN_ALL[b0]) / 1000.0 / 100
print("first_ts", first_ts)
for b in bases:
    rooms = by[b]
    mn = MIN_ALL[b]
    who = [r for r, t in rooms.items() if t == mn]
    print(b, "min", mn, who, "nrooms", len(rooms))

src = (DIR / "tick_s_check.py").read_text()
src = src.replace("_halfhour_2026-11-21_0200", "_halfhour_2026-11-21_0230")
src = src.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0230")
start = src.index("W46 = {")
end = src.index("def intervals(d):")
w46_lines = ",\n    ".join(f"{b}: {W46[b]}" for b in sorted(W46))
min_lines = []
for b in sorted(MIN_ALL):
    who = [r for r, t in by[b].items() if t == MIN_ALL[b]]
    min_lines.append(f"    {b}: {MIN_ALL[b]},  # {','.join(who)}")
block = (
    "W46 = {\n    " + w46_lines + ",\n}\n"
    "MIN_ALL = {\n" + "\n".join(min_lines) + "\n}\n"
    f"TMIN, TMAX = {tmin}, {tmax}\n"
    'ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")\n'
    f"TICK_S_FIRST = (MIN_ALL[{b1}] - MIN_ALL[{b0}]) / 1000.0 / 100  # script printed {printed}, exact {first_ts:.5f}\n"
    f"GT_FIRST = {gt}\n"
    f"TS_REALIGNED_FIRST = {realign}  # first-pass realign moved {realign} (inserted={ins}, already_in_db={already}, missing_chunks={len(missing)})\n"
    f"PREV_LATER_MEAN = 4.156295  # 02:00 half-hour tick_s_in_use (all_mean)\n\n\n"
)
src = src[:start] + block + src[end:]
# refresh printed tick_s mentions that gen usually rewrites
src = src.replace("(printed 4.114)", f"(printed {printed})")
src = src.replace("(printed 4.137)", f"(printed {printed})")
(DIR / "tick_s_check.py").write_text(src)
print("wrote tick_s_check")

holes = ", ".join(f'("{r}", {b})' for r, b in missing)
miss_s = ", ".join(f"{r}@{b}" for r, b in missing) or "none"
leftover = (
    f"Already-told leftover official 404s W45N7@84383500, W45N7@84383900, "
    f"W45N8@84382600, W45N7@84382700, and W46N8@84382900 age out of window start {tmin} and are not retried here."
)
cov = (DIR / "coverage.py").read_text()
cov = re.sub(r"TMIN, TMAX = \d+, \d+", f"TMIN, TMAX = {tmin}, {tmax}", cov, count=1)
cov = cov.replace("_halfhour_2026-11-21_0200", "_halfhour_2026-11-21_0230")
cov = cov.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0230")
m = re.search(r"IN_WINDOW_404 = \{[^}]*\}[^\n]*", cov)
if not m:
    raise SystemExit("coverage IN_WINDOW_404 not found")
new_in = (
    f"IN_WINDOW_404 = {{{holes}}}  # first pass {35-len(missing)}/35 official GETs 200, "
    f"missing_chunks={len(missing)}" + (f" {miss_s}" if missing else "") + ". "
    + leftover
)
cov = cov[:m.start()] + new_in + cov[m.end():]
(DIR / "coverage.py").write_text(cov)
print("wrote coverage")

conf = (DIR / "backfill_confirm.py").read_text()
m = re.search(r"IN_WINDOW = \[[^\]]*\][^\n]*", conf)
if not m:
    raise SystemExit("confirm IN_WINDOW not found")
new_win = (
    f"IN_WINDOW = [{holes}]  # first pass {35-len(missing)}/35 official GETs 200, missing_chunks={len(missing)}. "
    + leftover
)
conf = conf[:m.start()] + new_win + conf[m.end():]
conf2 = re.sub(r"TICK_S = [0-9.]+", f"TICK_S = {first_ts:.5f}", conf, count=1)
if conf2 == conf:
    raise SystemExit("TICK_S not found")
conf = conf2
conf = conf.replace("_halfhour_2026-11-21_0200", "_halfhour_2026-11-21_0230")
conf = conf.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0230")
(DIR / "backfill_confirm.py").write_text(conf)
print("wrote confirm")

just_base = (tmax // 100) * 100
jp = (DIR / "backfill_just_published.py").read_text()
jp = jp.replace("_halfhour_2026-11-21_0200", "_halfhour_2026-11-21_0230")
jp = jp.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0230")
jp = re.sub(
    r"Fetch just-published official history base \d+ once game\.time is safely past \d+\.",
    f"Fetch just-published official history base {just_base} once game.time is safely past {just_base + 140}.",
    jp,
)
jp = re.sub(r"JUST_BASE = \d+", f"JUST_BASE = {just_base}", jp, count=1)
(DIR / "backfill_just_published.py").write_text(jp)
print("wrote just_published JUST_BASE", just_base)

pc = (DIR / "post_counts.py").read_text()
pc = pc.replace("_halfhour_2026-11-21_0200", "_halfhour_2026-11-21_0230")
pc = pc.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0230")
pc = re.sub(r"JUST_BASE = \d+", f"JUST_BASE = {just_base}", pc, count=1)
pc = re.sub(r"WIN_TMIN, WIN_TMAX = \d+, \d+", f"WIN_TMIN, WIN_TMAX = {tmin}, {tmax}", pc, count=1)
m = re.search(r"GAPS = \[[\s\S]*?\]", pc)
if not m:
    raise SystemExit("GAPS block not found")
new_gaps = f'''GAPS = [
    ("gap_0147_0202", 84384461, 84384689),  # already-told by 02:28/02:30 1h patrol _patrol_2026-11-21_0221 (box freeze 01:47:58-02:02:50, 884s); 229t; fully in window start {tmin}
    ("gap_0220_0222", 84384941, 84384959),  # already-told by 02:28/02:30 1h patrol (short listener gap 02:20:54-02:22:17, ~83s); 19t; official-filled 19/19 via patrol just-published 84384900
    ("gap_0110_0124", 84383931, 84384149),  # already-told by 01:33 patrol (box freeze 01:10:46-01:24:59); ages out of window start {tmin}; 219t
    ("gap_0050_0057", 84383651, 84383759),  # already-told by 01:33 patrol (box freeze 00:50:52-00:57:30); ages out of window start {tmin}; 109t
]'''
pc = pc[:m.start()] + new_gaps + pc[m.end():]
(DIR / "post_counts.py").write_text(pc)
print("wrote post_counts")

wp = (DIR / "wrapup_write.py").read_text()
wp = wp.replace("_halfhour_2026-11-21_0200", "_halfhour_2026-11-21_0230")
wp = wp.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0230")
(DIR / "wrapup_write.py").write_text(wp)
print("path-replaced wrapup")
print("done")
