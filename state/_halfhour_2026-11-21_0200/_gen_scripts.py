#!/usr/bin/env python3
from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_0200")
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
src = src.replace(
    'DIR = ROOT / "state" / "_halfhour_2026-11-21_0130"',
    'DIR = ROOT / "state" / "_halfhour_2026-11-21_0200"',
)
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
    f"PREV_LATER_MEAN = 4.19988  # 01:30 half-hour tick_s_in_use (first)\n\n\n"
)
src = src[:start] + block + src[end:]
src = src.replace("(printed 4.200)", f"(printed {printed})")
src = src.replace("(printed 4.200, min-all-rooms first two bases)", f"(printed {printed}, min-all-rooms first two bases)")
(DIR / "tick_s_check.py").write_text(src)
print("wrote tick_s_check")

holes = ", ".join(f'("{r}", {b})' for r, b in missing)
miss_s = ", ".join(f"{r}@{b}" for r, b in missing) or "none"
cov = (DIR / "coverage.py").read_text()
cov = re.sub(r"TMIN, TMAX = \d+, \d+", f"TMIN, TMAX = {tmin}, {tmax}", cov, count=1)
cov = cov.replace(
    'DIR = "/workspace/screeps/state/_halfhour_2026-11-21_0130"',
    'DIR = "/workspace/screeps/state/_halfhour_2026-11-21_0200"',
)
m = re.search(r"IN_WINDOW_404 = \{[^}]*\}[^\n]*", cov)
if not m:
    raise SystemExit("coverage IN_WINDOW_404 not found")
new_in = (
    f"IN_WINDOW_404 = {{{holes}}}  # first pass {35-len(missing)}/35 official GETs 200, "
    f"missing_chunks={len(missing)}" + (f" {miss_s}" if missing else "") + ". "
    f"Already-told leftover official 404s W45N7@84383500 and W45N7@84383900 age out of window start {tmin} and are not retried here."
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
    f"Already-told leftover official 404s W45N7@84383500 and W45N7@84383900 age out of window start {tmin} and are not retried here."
)
conf = conf[:m.start()] + new_win + conf[m.end():]
conf2 = re.sub(r"TICK_S = [0-9.]+", f"TICK_S = {first_ts:.5f}", conf, count=1)
if conf2 == conf:
    raise SystemExit("TICK_S not found")
conf = conf2
conf = conf.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0200")
(DIR / "backfill_confirm.py").write_text(conf)
print("wrote confirm")

just_base = (tmax // 100) * 100
jp = (DIR / "backfill_just_published.py").read_text()
jp = jp.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0200")
jp = re.sub(
    r"Fetch just-published official history base \d+ once game\.time is safely past \d+\.",
    f"Fetch just-published official history base {just_base} once game.time is safely past {just_base + 140}.",
    jp,
)
jp = re.sub(r"JUST_BASE = \d+", f"JUST_BASE = {just_base}", jp, count=1)
(DIR / "backfill_just_published.py").write_text(jp)
print("wrote just_published JUST_BASE", just_base)

pc = (DIR / "post_counts.py").read_text()
pc = pc.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0200")
pc = re.sub(r"JUST_BASE = \d+", f"JUST_BASE = {just_base}", pc, count=1)
pc = re.sub(r"WIN_TMIN, WIN_TMAX = \d+, \d+", f"WIN_TMIN, WIN_TMAX = {tmin}, {tmax}", pc, count=1)
old_gaps = '''GAPS = [
    ("gap_0110_0124", 84383931, 84384149),  # NEW box freeze 01:10:46-01:24:59 (846s); last STATS 84383930 at 01:10:36, next STATS 84384150 at 01:25:52; 219t; no preceding no-STATS
    ("gap_0050_0057", 84383651, 84383759),  # already-recorded untold by 01:00 half-hour _halfhour_2026-11-21_0100; still in window start 84383501; 109t; official-filled 109/109 all five
    ("gap_0014_0022", 84383131, 84383249),  # already-told by 00:32 1h patrol _patrol_2026-11-21_0022 (no-STATS after 00:14:38 + box freeze 00:19:22-00:22:38); 119t; ages out of window start 84383501
    ("gap_2340_2357", 84382641, 84382889),  # already-told by 00:32 patrol; ages out of window start 84383501; 249t
]'''
new_gaps = '''GAPS = [
    ("gap_0147_0202", 84384461, 84384689),  # NEW box freeze 01:47:58-02:02:50 (884s); last STATS 84384460 at 01:47:24, next STATS 84384690 at 02:03:19; 229t; no preceding no-STATS
    ("gap_0110_0124", 84383931, 84384149),  # already-told by 01:33 1h patrol _patrol_2026-11-21_0124 (box freeze 01:10:46-01:24:59, 846s); 219t; partial in window start 84384001
    ("gap_0050_0057", 84383651, 84383759),  # already-told by 01:33 patrol (box freeze 00:50:52-00:57:30); ages out of window start 84384001; 109t
    ("gap_0014_0022", 84383131, 84383249),  # already-told by 00:32 patrol (no-STATS after 00:14:38 + box freeze 00:19:22-00:22:38); ages out of window start 84384001; 119t
]'''
if old_gaps not in pc:
    raise SystemExit("GAPS block not found")
pc = pc.replace(old_gaps, new_gaps)
(DIR / "post_counts.py").write_text(pc)
print("wrote post_counts")

wp = (DIR / "wrapup_write.py").read_text()
wp = wp.replace("_halfhour_2026-11-21_0130", "_halfhour_2026-11-21_0200")
(DIR / "wrapup_write.py").write_text(wp)
print("path-replaced wrapup")
print("done")
