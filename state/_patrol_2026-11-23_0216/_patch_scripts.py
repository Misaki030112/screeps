#!/usr/bin/env python3
from pathlib import Path
import json, re

D = Path("/workspace/screeps/state/_patrol_2026-11-23_0216")
old_hh = "_patrol_2026-11-23_0216"
old_p = "_patrol_2026-11-23_0216"
new = "_patrol_2026-11-23_0216"
ts = json.loads((D / "chunk_ts.json").read_text())
by = {room: {int(b): t for b, t in d.items()} for room, d in ts["by_room"].items()}
min_all = {int(b): t for b, t in ts["min_all"].items()}
w46 = by["W46N8"]

def fmt_dict(d, annotate=False):
    lines = ["{"]
    for b in sorted(d):
        comment = ""
        if annotate:
            rooms = [r for r, dd in by.items() if dd.get(b) == d[b]]
            comment = "  # " + ",".join(rooms)
        lines.append("    %d: %d,%s" % (b, d[b], comment))
    lines.append("}")
    return "\n".join(lines)

# path-patch every py
for p in sorted(D.glob("*.py")):
    t = p.read_text()
    nt = t.replace(old_hh, new).replace(old_p, new)
    if nt != t:
        p.write_text(nt)
        print("path-patched", p.name)

# tick_s_check
p = D / "tick_s_check.py"
t = p.read_text()
t = re.sub(r"W46 = \{.*?\n\}", "W46 = " + fmt_dict(w46), t, count=1, flags=re.S)
t = re.sub(r"MIN_ALL = \{.*?\n\}", "MIN_ALL = " + fmt_dict(min_all, True), t, count=1, flags=re.S)
t = t.replace("TMIN, TMAX = 84425001, 84425700", "TMIN, TMAX = 84422901, 84426000")
t = t.replace("TMIN, TMAX = 84422701, 84423400", "TMIN, TMAX = 84422901, 84426000")
t = re.sub(
    r"TICK_S_FIRST = .*",
    "TICK_S_FIRST = (MIN_ALL[84423000] - MIN_ALL[84422900]) / 1000.0 / 100  # printed 4.255, exact 4.25489; FIRST INTERVAL INSIDE already-told 22:43 freeze",
    t,
    count=1,
)
t = re.sub(r"GT_FIRST = \d+", "GT_FIRST = 84426099", t, count=1)
t = re.sub(
    r"TS_REALIGNED_FIRST = .*",
    "TS_REALIGNED_FIRST = 76313  # first-pass realign moved 76313 rows (inserted=12578 already_in_db=110962) with freeze-inflated first tick_s=4.255",
    t,
    count=1,
)
t = re.sub(
    r"PREV_LATER_MEAN = .*",
    "PREV_LATER_MEAN = 4.173806666666667  # tick_s_in_use from quiet 02:00 half-hour (live-anchor-best all_mean)",
    t,
    count=1,
)
p.write_text(t)
print("patched tick_s_check.py")

# confirm
p = D / "backfill_confirm.py"
t = p.read_text()
t = re.sub(
    r"IN_WINDOW = \[.*?\]",
    'IN_WINDOW = [("W45N8", 84425500), ("W45N8", 84425800)]',
    t,
    count=1,
    flags=re.S,
)
t = re.sub(
    r"AGED = \[.*?\]",
    'AGED = [("W45N8", 84422100), ("W45N8", 84422400)]  # aged out of window start 84422901, already told, not retried',
    t,
    count=1,
    flags=re.S,
)
t = re.sub(r"^TICK_S = .*$", "TICK_S = 4.173806666666667", t, count=1, flags=re.M)
p.write_text(t)
print("patched backfill_confirm.py")

# just published
for name, base, wait in [
    ("backfill_just_published.py", 84426000, 84426140),
]:
    p = D / name
    t = p.read_text()
    t = re.sub(r"JUST_BASE = \d+", "JUST_BASE = %d" % base, t, count=1)
    t = re.sub(r"WAIT_UNTIL_GT = \d+", "WAIT_UNTIL_GT = %d" % wait, t, count=1)
    # docstring number if present
    t = re.sub(r"base 844\d+", "base %d" % base, t, count=1)
    t = re.sub(r"past 844\d+", "past %d" % wait, t, count=1)
    p.write_text(t)
    print("patched", name, "JUST_BASE", base, "WAIT", wait)

# retry scripts often import JUST_BASE from the main jp script or define their own
for name in [
    "backfill_just_published_retry.py",
    "backfill_just_published_retry2.py",
    "backfill_late_retry.py",
]:
    p = D / name
    t = p.read_text()
    t = re.sub(r"JUST_BASE = \d+", "JUST_BASE = 84426000", t)
    t = re.sub(r"WAIT_UNTIL_GT = \d+", "WAIT_UNTIL_GT = 84426140", t)
    p.write_text(t)
    print("patched", name)

# exact2h
p = D / "exact2h.py"
t = p.read_text()
t = re.sub(
    r"LAST_TIP = \d+.*",
    "LAST_TIP = 84423460  # previous 1h patrol analysis tip (23:24:32 room_stats)",
    t,
    count=1,
)
t = re.sub(
    r"BF_LO, BF_HI = \d+, \d+.*",
    "BF_LO, BF_HI = 84422901, 84426000  # first-pass official window this 3h, missing_chunks=2",
    t,
    count=1,
)
p.write_text(t)
print("patched exact2h.py")

# freeze_clock
p = D / "freeze_clock.py"
t = p.read_text()
t = t.replace(
    "CUT = datetime(2026, 11, 22, 22, 36, 58, tzinfo=HK)",
    "CUT = datetime(2026, 11, 22, 23, 32, 40, tzinfo=HK)",
)
t = t.replace(
    "CUT = datetime(2026, 11, 22, 23, 32, 40, tzinfo=HK)",
    "CUT = datetime(2026, 11, 22, 23, 32, 40, tzinfo=HK)",
)
p.write_text(t)
print("patched freeze_clock.py")

print("ALL PATCHES DONE")
