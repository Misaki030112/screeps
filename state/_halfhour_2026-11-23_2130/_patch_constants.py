
from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_2130")

p = DIR / "tick_s_check.py"
t = p.read_text()
old_w46 = """W46 = {
    84441000: 1795436531012,
    84441100: 1795436950877,
    84441200: 1795437375675,
    84441300: 1795437801350,
    84441400: 1795438222444,
    84441500: 1795438644907,
    84441600: 1795439070096,
}
MIN_ALL = {
    84441000: 1795436531012,  # W46N8
    84441100: 1795436950877,  # W46N8
    84441200: 1795437375675,  # W46N8
    84441300: 1795437801350,  # W46N8
    84441400: 1795438222444,  # W46N8
    84441500: 1795438644907,  # W46N8
    84441600: 1795439070096,  # W46N8
}
TMIN, TMAX = 84441001, 84441700
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84441100] - MIN_ALL[84441000]) / 1000.0 / 100  # script printed 4.199, exact 4.19865
GT_FIRST = 84441737
TS_REALIGNED_FIRST = 12  # first-pass realign committed 12 rows (inserted=9432 already_in_db=16526)
PREV_LATER_MEAN = 4.29368  # tick_s_in_use from quiet 2030 half-hour (live-anchor-best all_mean)
"""
new_w46 = """W46 = {
    84441300: 1795437801350,
    84441400: 1795438222444,
    84441500: 1795438644907,
    84441600: 1795439070096,
    84441700: 1795439502191,
    84441800: 1795439930538,
    84441900: 1795440360904,
}
MIN_ALL = {
    84441300: 1795437801350,  # W46N8
    84441400: 1795438222444,  # W46N8
    84441500: 1795438644907,  # W46N8
    84441600: 1795439070096,  # W46N8
    84441700: 1795439502191,  # W46N8
    84441800: 1795439930538,  # W46N8
    84441900: 1795440360904,  # W46N8
}
TMIN, TMAX = 84441301, 84442000
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84441400] - MIN_ALL[84441300]) / 1000.0 / 100  # script printed 4.211, exact 4.21094
GT_FIRST = 84442098
TS_REALIGNED_FIRST = 599  # first-pass realign committed 599 rows (inserted=6456 already_in_db=18944)
PREV_LATER_MEAN = 4.23844  # tick_s_in_use from quiet 2100 half-hour (live-anchor-best later_raw)
"""
if old_w46 not in t:
    raise SystemExit("tick_s_check constants block not found")
p.write_text(t.replace(old_w46, new_w46, 1))
print("tick_s_check updated")

p = DIR / "backfill_confirm.py"
t = p.read_text()
old = """IN_WINDOW = [
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441001 by 1 tick; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441001; retry as near-window; do not relabel NEW
]
AGED = []  # W45N8@84437100 and W47N7@84436400 already told in 17:46 1728 patrol; aged out of window start 84441001; not retried. Older already-told leftovers also aged out; not retried; do not relabel NEW.
TICK_S = 4.29368
"""
new = """IN_WINDOW = [
    ("W45N7", 84441900),  # NEW first-pass in-window 404 this 2130 pass; retry
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441301; retry as near-window; do not relabel NEW
]
AGED = []  # W45N8@84437100 and W47N7@84436400 already told in 17:46 1728 patrol; aged out of window start 84441301; not retried. Older already-told leftovers also aged out; not retried; do not relabel NEW.
TICK_S = 4.23844
"""
if old not in t:
    raise SystemExit("confirm IN_WINDOW not found")
p.write_text(t.replace(old, new, 1))
print("backfill_confirm IN_WINDOW updated")

old_t = """TARGETS = [
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441001 by 1 tick; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441001; retry as near-window; do not relabel NEW
]"""
new_t = """TARGETS = [
    ("W45N7", 84441900),  # NEW first-pass in-window 404 this 2130 pass; retry
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441301; retry as near-window; do not relabel NEW
]"""
for name in ("backfill_late_retry.py", "backfill_postjp_retry.py"):
    p = DIR / name
    t = p.read_text()
    if old_t not in t:
        raise SystemExit(name + " TARGETS not found")
    p.write_text(t.replace(old_t, new_t, 1))
    print(name, "TARGETS updated")

p = DIR / "coverage.py"
t = p.read_text()
if "TMIN, TMAX = 84441001, 84441700" not in t:
    raise SystemExit("coverage TMIN not found")
t = t.replace("TMIN, TMAX = 84441001, 84441700", "TMIN, TMAX = 84441301, 84442000", 1)
old = "IN_WINDOW_404 = {\n}"
new = 'IN_WINDOW_404 = {\n    ("W45N7", 84441900),\n}'
if old not in t:
    raise SystemExit("coverage IN_WINDOW_404 not found")
t = t.replace(old, new, 1)
p.write_text(t)
print("coverage updated")

for name in ("backfill_just_published.py", "backfill_just_published_retry.py", "backfill_just_published_retry2.py"):
    p = DIR / name
    t = p.read_text()
    if "JUST_BASE = 84441700" not in t:
        raise SystemExit(name + " JUST_BASE not 84441700")
    t = t.replace("JUST_BASE = 84441700", "JUST_BASE = 84442000", 1)
    t = t.replace("base 84441700", "base 84442000")
    p.write_text(t)
    print(name, "JUST_BASE -> 84442000")

p = DIR / "wrapup_snap.py"
t = p.read_text()
if "TMIN, TMAX = 84441001, 84441700" not in t:
    raise SystemExit("wrapup_snap TMIN not found")
t = t.replace("TMIN, TMAX = 84441001, 84441700", "TMIN, TMAX = 84441301, 84442000", 1)
t = t.replace("JP_BASE = 84441700", "JP_BASE = 84442000", 1)

old_h = 'HOLES = [("W47N7", 84440900), ("W45N8", 84439200), ("W45N8", 84439300), ("W45N8", 84439500), ("W47N7", 84438700), ("W45N8", 84437100), ("W47N7", 84436400)]'
new_h = 'HOLES = [("W45N7", 84441900), ("W47N7", 84440900), ("W45N8", 84439200), ("W45N8", 84439300), ("W45N8", 84439500), ("W47N7", 84438700), ("W45N8", 84437100), ("W47N7", 84436400)]'
if old_h not in t:
    raise SystemExit("wrapup_snap HOLES not found")
t = t.replace(old_h, new_h, 1)

old_f = '''    "freeze_2056_2101": (84441591, 84441679),  # NEW 盒子休眠 20:56:44-21:01:46 (292s, box_pauses); STATS 89t; not yet told; first pass included published 84441600
}
'''
new_f = '''    "freeze_2056_2101": (84441591, 84441679),  # still-untold from quiet 2100; 盒子休眠 20:56:44-21:01:46; STATS 89t; official-filled all five 89/89; do not relabel NEW
    "freeze_2121_2128": (84441901, 84442049),  # NEW 盒子休眠 21:21:51-21:28:39 (400s, box_pauses); STATS 149t; not yet told; first pass included published 84441900 except W45N7@84441900 404
}
'''
if old_f not in t:
    raise SystemExit("wrapup_snap FREEZES tail not found")
t = t.replace(old_f, new_f, 1)
p.write_text(t)
print("wrapup_snap updated")

t = (DIR / "tick_s_check.py").read_text()
assert "TMIN, TMAX = 84441301, 84442000" in t
assert "PREV_LATER_MEAN = 4.23844" in t
assert "GT_FIRST = 84442098" in t
t = (DIR / "backfill_just_published.py").read_text()
assert "JUST_BASE = 84442000" in t
assert "JUST_BASE = 84441700" not in t
t = (DIR / "coverage.py").read_text()
assert "TMIN, TMAX = 84441301, 84442000" in t
assert '("W45N7", 84441900)' in t
t = (DIR / "wrapup_snap.py").read_text()
assert "JP_BASE = 84442000" in t
assert "freeze_2121_2128" in t
t = (DIR / "backfill_confirm.py").read_text()
assert '("W45N7", 84441900)' in t
print("all patches ok")
