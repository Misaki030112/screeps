#!/usr/bin/env python3
from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2200")
src2130 = Path("/workspace/screeps/state/_halfhour_2026-11-20_2130")

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
ins = int(re.search(r"^inserted=(\d+)", text, re.M).group(1))
already = int(re.search(r"already_in_db=(\d+)", text).group(1))
printed = re.search(r"tick_s=([0-9.]+)", text).group(1)
realign = int(re.search(r"ts_realigned=(\d+)", text).group(1))
print("bases", sorted(by))
print("missing", missing, "gt", gt, "window", tmin, tmax, nticks)
print("inserted", ins, "already", already, "tick_s", printed, "realign", realign)
for b in sorted(by):
    rooms = by[b]
    mn = min(rooms.values())
    who = [r for r, t in rooms.items() if t == mn]
    print(b, "min", mn, who, "nrooms", len(rooms))

W46 = {b: by[b]["W46N8"] for b in sorted(by) if "W46N8" in by[b]}
MIN_ALL = {b: min(by[b].values()) for b in sorted(by)}
bases = sorted(MIN_ALL)
b0, b1 = bases[0], bases[1]
first_ts = (MIN_ALL[b1] - MIN_ALL[b0]) / 1000.0 / 100
print("first_ts", first_ts, "from", b0, b1)

src = (src2130 / "tick_s_check.py").read_text()
src = src.replace(
    'DIR = ROOT / "state" / "_halfhour_2026-11-20_2130"',
    'DIR = ROOT / "state" / "_halfhour_2026-11-20_2200"',
)
start = src.index("W46 = {")
end = src.index("def intervals(d):")
w46_lines = ["W46 = {"]
for b in sorted(W46):
    w46_lines.append(f"    {b}: {W46[b]},")
w46_lines.append("}")
min_lines = ["MIN_ALL = {"]
for b in sorted(MIN_ALL):
    who = ",".join(r for r, t in by[b].items() if t == MIN_ALL[b])
    min_lines.append(f"    {b}: {MIN_ALL[b]},  # {who}")
min_lines.append("}")
miss_s = ", ".join(f"{r}@{b}" for r, b in missing) or "none"
block = "\n".join(w46_lines + min_lines) + "\n"
block += f"TMIN, TMAX = {tmin}, {tmax}\n"
block += 'ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")\n'
block += f"TICK_S_FIRST = (MIN_ALL[{b1}] - MIN_ALL[{b0}]) / 1000.0 / 100  # script printed {printed}, exact {first_ts:.5f}\n"
block += f"GT_FIRST = {gt}\n"
block += f"TS_REALIGNED_FIRST = {realign}  # first-pass realign moved {realign} (inserted={ins}, already_in_db={already}, missing_chunks={len(missing)} {miss_s})\n"
block += "PREV_LATER_MEAN = 4.18614  # 21:30 half-hour tick_s_in_use (later_raw)\n\n\n"
src = src[:start] + block + src[end:]
src = src.replace("(printed 4.217)", f"(printed {printed})")
src = src.replace("(printed 4.217, min-all-rooms first two bases)", f"(printed {printed}, min-all-rooms first two bases)")
(DIR / "tick_s_check.py").write_text(src)
print("wrote tick_s_check, first_ts", first_ts)

holes = ", ".join(f'("{r}", {b})' for r, b in missing)
cov = (src2130 / "coverage.py").read_text()
cov = cov.replace("TMIN, TMAX = 84380001, 84380700", f"TMIN, TMAX = {tmin}, {tmax}")
cov = cov.replace(
    'DIR = "/workspace/screeps/state/_halfhour_2026-11-20_2130"',
    'DIR = "/workspace/screeps/state/_halfhour_2026-11-20_2200"',
)
old_in = 'IN_WINDOW_404 = {("W47N8", 84380300)}  # first pass 34/35 official GETs 200, missing_chunks=1 W47N8@84380300. Concurrent 1h patrol 2119 already filled this window except that hole; leftover W47N8@84379500 ages out of window start 84380001 and is not retried here.'
new_in = (
    f"IN_WINDOW_404 = {{{holes}}}  # first pass 34/35 official GETs 200, "
    f"missing_chunks={len(missing)} {miss_s}. Leftover official 404 W47N8@84380300 "
    f"(hole 84380301..84380400) ages out of window start {tmin} and is not retried here."
)
if old_in not in cov:
    raise SystemExit("coverage IN_WINDOW_404 not found")
cov = cov.replace(old_in, new_in)
(DIR / "coverage.py").write_text(cov)
print("wrote coverage")

conf = (src2130 / "backfill_confirm.py").read_text()
old_win = 'IN_WINDOW = [("W47N8", 84380300)]  # first pass 34/35 official GETs 200, missing_chunks=1. Concurrent 1h patrol also 404 at 21:22 and 21:23:43 gt=84380697. Leftover W47N8@84379500 ages out of window start 84380001 and is not retried here (1h patrol already retried 21:23:44, still 404).'
new_win = (
    f"IN_WINDOW = [{holes}]  # first pass 34/35 official GETs 200, missing_chunks={len(missing)}. "
    f"Later chunks after these 404s were already 200 (W47N7@84381000 and @84381100 ok). "
    f"Leftover W47N8@84380300 ages out of window start {tmin} and is not retried here."
)
if old_win not in conf:
    raise SystemExit("confirm IN_WINDOW not found")
conf = conf.replace(old_win, new_win)
conf = conf.replace("TICK_S = 4.21708", f"TICK_S = {first_ts:.5f}")
conf = conf.replace(
    "/workspace/screeps/state/_halfhour_2026-11-20_2130/backfill_confirm_gets.json",
    "/workspace/screeps/state/_halfhour_2026-11-20_2200/backfill_confirm_gets.json",
)
conf = conf.replace(
    "/workspace/screeps/state/_halfhour_2026-11-20_2130/tick_s_realign.json",
    "/workspace/screeps/state/_halfhour_2026-11-20_2200/tick_s_realign.json",
)
(DIR / "backfill_confirm.py").write_text(conf)
print("wrote confirm")

just_base = (tmax // 100) * 100
jp = (src2130 / "backfill_just_published.py").read_text()
jp = jp.replace(
    "Fetch just-published official history base 84380700 once game.time is safely past 84380840.",
    f"Fetch just-published official history base {just_base} once game.time is safely past {just_base + 140}.",
)
jp = jp.replace(
    'sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-20_2130")',
    'sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-20_2200")',
)
jp = jp.replace("JUST_BASE = 84380700", f"JUST_BASE = {just_base}")
jp = jp.replace(
    'DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2130")',
    'DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2200")',
)
(DIR / "backfill_just_published.py").write_text(jp)
print("wrote just_published JUST_BASE", just_base)

print("remaining 2130 refs:")
for p in DIR.glob("*.py"):
    t = p.read_text()
    if "2130" in t:
        for i, line in enumerate(t.splitlines(), 1):
            if "2130" in line:
                print(p.name, i, line[:200])
