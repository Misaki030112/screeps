#!/usr/bin/env python3
from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1330")
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
        "_halfhour_2026-11-21_1300",
        "_halfhour_2026-11-21_1230",
        "_halfhour_2026-11-21_1200",
        "_halfhour_2026-11-21_1130",
        "_halfhour_2026-11-21_1030",
        "_halfhour_2026-11-21_1000",
        "_halfhour_2026-11-21_0930",
        "_halfhour_2026-11-21_0900",
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
        src = src.replace(old, "_halfhour_2026-11-21_1330")
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
    f"Already-told leftover official 404s W45N8@84392600, W46N8@84390800, W47N7@84390900, "
    f"W46N8@84390400, W45N7@84388500, W45N8@84386600 and older age out of window start {tmin} and are not retried here. "
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
    ("gap_1309_1321", 84394131, 84394299),  # NEW this run, not yet told (box freeze 13:09:46-13:21:14, 680s); 169t; last_stats 84394130 at 13:09:20, next 84394300 at 13:21:31; listener auto-restart 13:21:17, python 1883231 started 13:21:26; official window start {tmin} covers the whole 169t (chunks 84394100 and 84394200).
    ("gap_1248_1257", 84393831, 84393969),  # still not yet told (recorded by 13:00 half-hour backfill; box freeze 12:48:14-12:57:17, 534s); 139t; official-filled all five 139/139 at 13:00 run; still in official window start {tmin}. Fold into next 1h patrol together with 13:09 freeze.
    ("gap_1230_1235", 84393581, 84393659),  # still not yet told (recorded by 12:30 half-hour backfill; box freeze 12:30:42-12:35:35, 283s); 79t; official-filled all five 79/79; ages out of official window start {tmin}. Still fold into next 1h patrol; do not treat as already told.
    ("gap_1218", 84393391, 84393419),  # already-told by the 12:26 1h patrol (short listener WS ping/pong 12:18:13, restart 12:18:17; not a box freeze); 29t; W45N7 may have empty-no-creep after evac; ages out of official window start {tmin}
    ("gap_1210", 84393291, 84393319),  # already-told by the 12:26 1h patrol (short listener WS ping/pong 12:10:56, restart 12:10:59; not a box freeze); 29t; official-filled all five 29/29; ages out of official window start {tmin}
    ("gap_1149_1157", 84393001, 84393129),  # already-told by the 12:26 1h patrol (box freeze 11:49:12-11:57:31, 494s); 129t; official-filled all five 129/129; ages out of window start {tmin}
    ("gap_1119_1120", 84392571, 84392609),  # already-told by the 11:28 1h patrol (box freeze 11:19:06-11:20:43, 88s); leftover official 404 W45N8@84392600 already told by 12:26 patrol; ages out of window start {tmin}
    ("gap_1111_1113", 84392471, 84392499),  # already-told by the 12:26 1h patrol (short listener WS ping/pong 11:12:51-11:12:54, not a box freeze); official-filled all five 29/29; ages out of window start {tmin}
]'''
pc = pc[:m.start()] + new_gaps + pc[m.end():]
(DIR / "post_counts.py").write_text(pc)
print("wrote post_counts")

wp = retarget((DIR / "wrapup_write.py").read_text())
(DIR / "wrapup_write.py").write_text(wp)
print("path-replaced wrapup")
print("done")
