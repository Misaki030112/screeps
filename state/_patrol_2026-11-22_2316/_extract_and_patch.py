#!/usr/bin/env python3
from pathlib import Path
import re, json

DIR = Path("/workspace/screeps/state/_patrol_2026-11-22_2316")
text = (DIR / "history_backfill.txt").read_text()
pat = re.compile(r"ok\s+(\w+)@(\d+) ticks=\d+ ts=(\d+)")
rows = pat.findall(text)
by = {}
for room, base, ts in rows:
    by.setdefault(int(base), {})[room] = int(ts)
print("bases", sorted(by))
for b in sorted(by):
    print(b, by[b])
w46 = {b: d["W46N8"] for b, d in by.items() if "W46N8" in d}
min_all = {b: min(d.values()) for b, d in by.items()}
print("W46", w46)
print("MIN_ALL", min_all)
bs = sorted(min_all)
TICK_S_FIRST = (min_all[84422000] - min_all[84421900]) / 1000.0 / 100
print("TICK_S_FIRST", TICK_S_FIRST, "from 84421900->84422000")
(DIR / "chunk_ts.json").write_text(
    json.dumps({"w46": w46, "min_all": min_all, "by": {str(k): v for k, v in by.items()}}, indent=2) + "\n"
)

def dict_src(d):
    lines = ["{"]
    for k in sorted(int(x) for x in d):
        lines.append(f"    {k}: {d[k]},")
    lines.append("}")
    return "\n".join(lines)

# confirm.py
p = DIR / "backfill_confirm.py"
t = p.read_text()
t = t.replace("/workspace/screeps/state/_halfhour_2026-11-22_2200", str(DIR))
t = re.sub(r"TICK_S = [0-9.]+", f"TICK_S = {TICK_S_FIRST}", t, count=1)
p.write_text(t)
print("patched confirm")

# coverage.py
p = DIR / "coverage.py"
t = p.read_text()
t = t.replace("/workspace/screeps/state/_halfhour_2026-11-22_2200", str(DIR))
t = t.replace("TMIN, TMAX = 84421801, 84422500", "TMIN, TMAX = 84421901, 84422600")
p.write_text(t)
print("patched coverage")

# late_retry
p = DIR / "backfill_late_retry.py"
t = p.read_text()
t = t.replace("/workspace/screeps/state/_halfhour_2026-11-22_2200", str(DIR))
p.write_text(t)
print("patched late_retry")

# just_published
p = DIR / "backfill_just_published.py"
t = p.read_text()
t = t.replace("/workspace/screeps/state/_halfhour_2026-11-22_2200", str(DIR))
t = t.replace("JUST_BASE = 84422500", "JUST_BASE = 84422600")
t = t.replace("base 84422500 once game.time is safely past 84422640", "base 84422600 once game.time is safely past 84422740")
p.write_text(t)
print("patched JP")

for name in ("backfill_just_published_retry.py", "backfill_just_published_retry2.py"):
    p = DIR / name
    if p.exists():
        t = p.read_text()
        t = t.replace("/workspace/screeps/state/_halfhour_2026-11-22_2200", str(DIR))
        t = t.replace("JUST_BASE = 84422500", "JUST_BASE = 84422600")
        p.write_text(t)
        print("patched", name)

# tick_s_check.py
p = DIR / "tick_s_check.py"
t = p.read_text()
t = t.replace('DIR = ROOT / "state" / "_halfhour_2026-11-22_2200"', 'DIR = ROOT / "state" / "_patrol_2026-11-22_2316"')
new_consts = (
    f"W46 = {dict_src(w46)}\n"
    f"MIN_ALL = {dict_src(min_all)}\n"
    "TMIN, TMAX = 84421901, 84422600\n"
    'ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")\n'
    f"TICK_S_FIRST = (MIN_ALL[84422000] - MIN_ALL[84421900]) / 1000.0 / 100  # script printed 4.189, exact {TICK_S_FIRST:.5f}\n"
    "GT_FIRST = 84422636\n"
    "TS_REALIGNED_FIRST = 15440  # first-pass realign moved 15440 rows (inserted=3081 already_in_db=21946)\n"
    "PREV_LATER_MEAN = 4.16058  # tick_s_in_use from 22:00 halfhour\n"
)
t2 = re.sub(
    r"W46 = \{.*?\nPREV_LATER_MEAN = [0-9.]+\s*(?:#[^\n]*)?\n",
    new_consts + "\n",
    t,
    count=1,
    flags=re.S,
)
if t2 == t:
    print("WARN: tick_s_check const replace failed")
    (DIR / "tick_s_check_replace_failed.txt").write_text("failed\n")
else:
    p.write_text(t2)
    print("patched tick_s_check")
    if "84421901" in t2 and "_patrol_2026-11-22_2316" in t2:
        print("tick_s_check looks retargeted")
    else:
        print("WARN missing expected strings")
