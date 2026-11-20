#!/usr/bin/env python3
from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2230")
src2200 = Path("/workspace/screeps/state/_halfhour_2026-11-20_2200")

for name in ("tick_s_check.py", "coverage.py", "backfill_confirm.py",
             "backfill_just_published.py", "post_counts.py", "wrapup_write.py"):
    (DIR / name).write_text((src2200 / name).read_text())

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

src = (src2200 / "tick_s_check.py").read_text()
src = src.replace(
    'DIR = ROOT / "state" / "_halfhour_2026-11-20_2200"',
    'DIR = ROOT / "state" / "_halfhour_2026-11-20_2230"',
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
nl = chr(10)
block = nl.join(w46_lines + min_lines) + nl
block += f"TMIN, TMAX = {tmin}, {tmax}" + nl
block += 'ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")' + nl
block += f"TICK_S_FIRST = (MIN_ALL[{b1}] - MIN_ALL[{b0}]) / 1000.0 / 100  # script printed {printed}, exact {first_ts:.5f}" + nl
block += f"GT_FIRST = {gt}" + nl
block += f"TS_REALIGNED_FIRST = {realign}  # first-pass realign moved {realign} (inserted={ins}, already_in_db={already}, missing_chunks={len(missing)} {miss_s})" + nl
block += "PREV_LATER_MEAN = 4.20516  # 22:00 half-hour tick_s_in_use (later_raw)" + nl + nl + nl
src = src[:start] + block + src[end:]
src = src.replace("(printed 4.172)", f"(printed {printed})")
src = src.replace("(printed 4.172, min-all-rooms first two bases)", f"(printed {printed}, min-all-rooms first two bases)")
(DIR / "tick_s_check.py").write_text(src)
print("wrote tick_s_check, first_ts", first_ts)

holes = ", ".join(f'("{r}", {b})' for r, b in missing)
cov = (src2200 / "coverage.py").read_text()
cov = re.sub(r"TMIN, TMAX = \d+, \d+", f"TMIN, TMAX = {tmin}, {tmax}", cov, count=1)
cov = cov.replace(
    'DIR = "/workspace/screeps/state/_halfhour_2026-11-20_2200"',
    'DIR = "/workspace/screeps/state/_halfhour_2026-11-20_2230"',
)
m = re.search(r"IN_WINDOW_404 = \{[^}]*\}[^\n]*", cov)
if not m:
    raise SystemExit("coverage IN_WINDOW_404 not found")
new_in = (
    f"IN_WINDOW_404 = {{{holes}}}  # first pass 34/35 official GETs 200, "
    f"missing_chunks={len(missing)} {miss_s}. Concurrent 1h patrol _patrol_2026-11-20_2220 "
    f"already filled 84380801..84381500 except this hole; leftover official 404 "
    f"W47N8@84380300 ages out of window start {tmin} and is not retried here. "
    f"First pass already included just-published-style base 84381500 (all five 200)."
)
cov = cov[:m.start()] + new_in + cov[m.end():]
(DIR / "coverage.py").write_text(cov)
print("wrote coverage")

conf = (src2200 / "backfill_confirm.py").read_text()
m = re.search(r"IN_WINDOW = \[[^\]]*\][^\n]*", conf)
if not m:
    raise SystemExit("confirm IN_WINDOW not found")
new_win = (
    f"IN_WINDOW = [{holes}]  # first pass 34/35 official GETs 200, missing_chunks={len(missing)}. "
    f"Later chunks after this 404 were already 200 (W47N7@84381000 through @84381500 ok). "
    f"Leftover W47N8@84380300 ages out of window start {tmin} and is not retried here. "
    f"22:00 confirm/retry2 and 22:20 patrol retry still 404."
)
conf = conf[:m.start()] + new_win + conf[m.end():]
conf2 = re.sub(r"TICK_S = [0-9.]+", f"TICK_S = {first_ts:.5f}", conf, count=1)
if conf2 == conf:
    raise SystemExit("TICK_S not found")
conf = conf2
conf = conf.replace(
    "/workspace/screeps/state/_halfhour_2026-11-20_2200/backfill_confirm_gets.json",
    "/workspace/screeps/state/_halfhour_2026-11-20_2230/backfill_confirm_gets.json",
)
conf = conf.replace(
    "/workspace/screeps/state/_halfhour_2026-11-20_2200/tick_s_realign.json",
    "/workspace/screeps/state/_halfhour_2026-11-20_2230/tick_s_realign.json",
)
(DIR / "backfill_confirm.py").write_text(conf)
print("wrote confirm")

just_base = (tmax // 100) * 100
jp = (src2200 / "backfill_just_published.py").read_text()
jp = jp.replace("_halfhour_2026-11-20_2200", "_halfhour_2026-11-20_2230")
jp = re.sub(
    r"Fetch just-published official history base \d+ once game\.time is safely past \d+\.",
    f"Fetch just-published official history base {just_base} once game.time is safely past {just_base + 140}.",
    jp,
)
jp = re.sub(r"JUST_BASE = \d+", f"JUST_BASE = {just_base}", jp, count=1)
(DIR / "backfill_just_published.py").write_text(jp)
print("wrote just_published JUST_BASE", just_base)

pc = (DIR / "post_counts.py").read_text()
pc = pc.replace("_halfhour_2026-11-20_2200", "_halfhour_2026-11-20_2230")
(DIR / "post_counts.py").write_text(pc)

wp = (DIR / "wrapup_write.py").read_text()
wp = wp.replace("_halfhour_2026-11-20_2200", "_halfhour_2026-11-20_2230")
(DIR / "wrapup_write.py").write_text(wp)

print("remaining 2200 refs:")
for p in DIR.glob("*.py"):
    t = p.read_text()
    if "2200" in t:
        for i, line in enumerate(t.splitlines(), 1):
            if "2200" in line:
                print(p.name, i, line[:220])
