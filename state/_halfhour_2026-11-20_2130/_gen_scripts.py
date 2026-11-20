#!/usr/bin/env python3
from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2130")
src2100 = Path("/workspace/screeps/state/_halfhour_2026-11-20_2100")

text = (DIR / "history_backfill_first_attempt.txt").read_text()
(DIR / "history_backfill.txt").write_text(text)
pat = re.compile(r"  ok  (W\d+N\d+)@(\d+) ticks=(\d+) ts=(\d+)")
by = {}
for m in pat.finditer(text):
    room, base, ticks, ts = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    by.setdefault(base, {})[room] = ts
print("bases", sorted(by))
for b in sorted(by):
    rooms = by[b]
    mn = min(rooms.values())
    who = [r for r, t in rooms.items() if t == mn]
    print(b, "min", mn, who, "all", rooms)

W46 = {b: by[b]["W46N8"] for b in sorted(by)}
MIN_ALL = {b: min(by[b].values()) for b in sorted(by)}

src = (src2100 / "tick_s_check.py").read_text()
src = src.replace(
    'DIR = ROOT / "state" / "_halfhour_2026-11-20_2100"',
    'DIR = ROOT / "state" / "_halfhour_2026-11-20_2130"',
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
first_ts = (MIN_ALL[84380100] - MIN_ALL[84380000]) / 1000.0 / 100
block = "\n".join(w46_lines + min_lines) + f"""
TMIN, TMAX = 84380001, 84380700
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84380100] - MIN_ALL[84380000]) / 1000.0 / 100  # script printed 4.217, exact {first_ts:.5f}
GT_FIRST = 84380798
TS_REALIGNED_FIRST = 18  # first-pass realign moved 18 (inserted=438, already_in_db=23933, missing_chunks=1 W47N8@84380300)
PREV_LATER_MEAN = 4.16599  # 21:00 half-hour tick_s_in_use (prev_later)


"""
src = src[:start] + block + src[end:]
src = src.replace(
    'f"First-pass realign with tick_s={TICK_S_FIRST:.5f} (printed 4.166) moved {TS_REALIGNED_FIRST} rows "\n        f"(ts_realigned_first={TS_REALIGNED_FIRST}, inserted=6533, already_in_db=19711, missing_chunks=0)."',
    'f"First-pass realign with tick_s={TICK_S_FIRST:.5f} (printed 4.217) moved {TS_REALIGNED_FIRST} rows "\n        f"(ts_realigned_first={TS_REALIGNED_FIRST}, inserted=438, already_in_db=23933, missing_chunks=1 W47N8@84380300)."',
)
src = src.replace(
    'f"first-interval tick_s={TICK_S_FIRST:.5f} (printed 4.166, min-all-rooms first two bases) "',
    'f"first-interval tick_s={TICK_S_FIRST:.5f} (printed 4.217, min-all-rooms first two bases) "',
)
(DIR / "tick_s_check.py").write_text(src)
print("wrote tick_s_check, first_ts", first_ts)

cov = (src2100 / "coverage.py").read_text()
cov = cov.replace("TMIN, TMAX = 84379601, 84380300", "TMIN, TMAX = 84380001, 84380700")
cov = cov.replace(
    'DIR = "/workspace/screeps/state/_halfhour_2026-11-20_2100"',
    'DIR = "/workspace/screeps/state/_halfhour_2026-11-20_2130"',
)
cov = cov.replace(
    'IN_WINDOW_404 = set()  # first pass 35/35 official GETs 200, missing_chunks=0. Leftover official 404 W47N8@84379500 aged out of window start 84379601 and was not retried.',
    'IN_WINDOW_404 = {("W47N8", 84380300)}  # first pass 34/35 official GETs 200, missing_chunks=1 W47N8@84380300. Concurrent 1h patrol 2119 already filled this window except that hole; leftover W47N8@84379500 ages out of window start 84380001 and is not retried here.',
)
(DIR / "coverage.py").write_text(cov)
print("wrote coverage")

conf = (src2100 / "backfill_confirm.py").read_text()
conf = conf.replace(
    'IN_WINDOW = []  # first pass 35/35 official GETs 200, missing_chunks=0. Leftover official 404 W47N8@84379500 aged out of window start 84379601 and is not retried.',
    'IN_WINDOW = [("W47N8", 84380300)]  # first pass 34/35 official GETs 200, missing_chunks=1. Concurrent 1h patrol also 404 at 21:22 and 21:23:43 gt=84380697. Leftover W47N8@84379500 ages out of window start 84380001 and is not retried here (1h patrol already retried 21:23:44, still 404).',
)
conf = conf.replace("TICK_S = 4.16611", f"TICK_S = {first_ts:.5f}")
conf = conf.replace(
    "/workspace/screeps/state/_halfhour_2026-11-20_2100/backfill_confirm_gets.json",
    "/workspace/screeps/state/_halfhour_2026-11-20_2130/backfill_confirm_gets.json",
)
conf = conf.replace(
    "/workspace/screeps/state/_halfhour_2026-11-20_2100/tick_s_realign.json",
    "/workspace/screeps/state/_halfhour_2026-11-20_2130/tick_s_realign.json",
)
(DIR / "backfill_confirm.py").write_text(conf)
print("wrote confirm")

jp = (src2100 / "backfill_just_published.py").read_text()
jp = jp.replace(
    "Fetch just-published official history base 84380300 once game.time is safely past 84380440.",
    "Fetch just-published official history base 84380700 once game.time is safely past 84380840.",
)
jp = jp.replace(
    'sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-20_2100")',
    'sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-20_2130")',
)
jp = jp.replace("JUST_BASE = 84380300", "JUST_BASE = 84380700")
jp = jp.replace(
    'DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2100")',
    'DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2130")',
)
(DIR / "backfill_just_published.py").write_text(jp)
print("wrote just_published")
print("remaining 2100 refs:")
for p in DIR.glob("*.py"):
    t = p.read_text()
    if "2100" in t:
        for i, line in enumerate(t.splitlines(), 1):
            if "2100" in line:
                print(p.name, i, line)
