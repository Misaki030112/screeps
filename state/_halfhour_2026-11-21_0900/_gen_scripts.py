#!/usr/bin/env python3
from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_0900")
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

def retarget(src: str) -> str:
    for old in (
        "_halfhour_2026-11-21_0830",
        "_halfhour_2026-11-21_0800",
        "_halfhour_2026-11-21_0730",
        "_halfhour_2026-11-21_0700",
        "_halfhour_2026-11-21_0630",
        "_halfhour_2026-11-21_0600",
        "_halfhour_2026-11-21_0530",
        "_halfhour_2026-11-21_0500",
        "_halfhour_2026-11-21_0430",
        "_halfhour_2026-11-21_0400",
        "_halfhour_2026-11-21_0330",
        "_halfhour_2026-11-21_0300",
    ):
        src = src.replace(old, "_halfhour_2026-11-21_0900")
    return src

src = retarget((DIR / "tick_s_check.py").read_text())
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
    f"PREV_LATER_MEAN = 4.222478  # 07:30 half-hour tick_s_in_use (later_raw)\n\n\n"
)
src = src[:start] + block + src[end:]
for old in ("4.114", "4.137", "4.236"):
    src = src.replace(f"(printed {old})", f"(printed {printed})")
(DIR / "tick_s_check.py").write_text(src)
print("wrote tick_s_check")

holes = ", ".join(f'("{r}", {b})' for r, b in missing)
miss_s = ", ".join(f"{r}@{b}" for r, b in missing) or "none"
leftover = (
    f"Already-told leftover official 404s W47N8@84385300, W45N7@84383500, W45N7@84383900, "
    f"W45N8@84382600, W45N7@84382700, W46N8@84382900, W47N8@84385900, W46N8@84386400, and W45N8@84386600 age out of window start {tmin} and are not retried here. "
    + (f"In-window first-pass official 404s: {miss_s}." if missing else "No in-window official 404s this first pass.")
)
cov = retarget((DIR / "coverage.py").read_text())
cov = re.sub(r"TMIN, TMAX = \d+, \d+", f"TMIN, TMAX = {tmin}, {tmax}", cov, count=1)
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

conf = retarget((DIR / "backfill_confirm.py").read_text())
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
(DIR / "backfill_confirm.py").write_text(conf)
print("wrote confirm")

just_base = (tmax // 100) * 100
jp = retarget((DIR / "backfill_just_published.py").read_text())
jp = re.sub(
    r"Fetch just-published official history base \d+ once game\.time is safely past \d+\.",
    f"Fetch just-published official history base {just_base} once game.time is safely past {just_base + 140}.",
    jp,
)
jp = re.sub(r"JUST_BASE = \d+", f"JUST_BASE = {just_base}", jp, count=1)
(DIR / "backfill_just_published.py").write_text(jp)
print("wrote just_published JUST_BASE", just_base)

pc = retarget((DIR / "post_counts.py").read_text())
pc = re.sub(r"JUST_BASE = \d+", f"JUST_BASE = {just_base}", pc, count=1)
pc = re.sub(r"WIN_TMIN, WIN_TMAX = \d+, \d+", f"WIN_TMIN, WIN_TMAX = {tmin}, {tmax}", pc, count=1)
m = re.search(r"GAPS = \[[\s\S]*?\]", pc)
if not m:
    raise SystemExit("GAPS block not found")
new_gaps = f'''GAPS = [
    ("gap_0743_0801", 84389531, 84389789),  # NEW this run, not yet told by a 1h patrol (box freeze 07:43:15-08:01:01, 1056s); 259t; last_stats 84389530 at 07:43:03, next 84389790 at 08:01:21; listener auto-restart 08:01:04, python 1745776 started 08:01:13; sits in official window start {tmin}..end (chunks 84389500..84389700). W47N7 first-pass 404 @84389700 may leave 84389701..84389789 unfilled until confirm/retry.
    ("gap_0722_0725", 84389231, 84389299),  # already-told by the 07:37 1h patrol (box freeze 07:22:15-07:25:56, 214s); 69t; last_stats 84389230 at 07:21:52, next 84389300 at 07:26:45; official-filled all five 69/69; still in official window start {tmin} (chunk 84389200)
    ("gap_0642_0704", 84388671, 84388999),  # already-told by the 07:37 1h patrol (box freeze 06:42:51-07:04:46, 1315s); 329t; official-filled all five 329/329; ages out of window start {tmin}
    ("gap_0634_0637", 84388561, 84388599),  # already-told by the 07:37 1h patrol (short listener gap 06:34:33-06:37:21); 39t; official-fill missing W45N7 all 39 due to already-told leftover official 404 W45N7@84388500; ages out of window start {tmin}
    ("gap_0619_0622", 84388331, 84388399),  # already-told by the 06:33 1h patrol (box freeze 06:19:18-06:22:57, 218s); 69t; official-filled all five 69/69; ages out of window start {tmin}
    ("gap_0542_0601", 84387811, 84388109),  # already-told by the 06:33 1h patrol (box freeze 05:42:11-06:01:46, 1169s); 299t; official-filled all five 299/299; ages out of window start {tmin}
    ("gap_0442_0503", 84386961, 84387269),  # already-told by the 05:26 1h patrol (box freeze 04:42:19-05:03:11, 1245s); 309t; official-filled all five 309/309; ages out of window start {tmin}
    ("gap_0410_0418", 84386511, 84386629),  # already-told by the 04:18/04:29 1h patrol (box freeze 04:10:40-04:18:06, 439s); 119t; official-fill missing W45N8 84386601..84386629; ages out of window start {tmin}
    ("gap_0354_0357", 84386281, 84386339),  # already-told by the 04:18/04:29 1h patrol (short freeze 03:54:27-03:57:32, 178s); 59t; official-filled all five 59/59; ages out of window start {tmin}
]'''
pc = pc[:m.start()] + new_gaps + pc[m.end():]
(DIR / "post_counts.py").write_text(pc)
print("wrote post_counts")

wp = retarget((DIR / "wrapup_write.py").read_text())
(DIR / "wrapup_write.py").write_text(wp)
print("path-replaced wrapup")
print("done")
