from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_2200")

p = DIR / "tick_s_check.py"
t = p.read_text()
old_w46 = """W46 = {
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
new_w46 = """W46 = {
    84441800: 1795439930538,
    84441900: 1795440360904,
    84442000: 1795440785198,
    84442100: 1795441211469,
    84442200: 1795441633849,
    84442300: 1795442073687,
    84442400: 1795442502633,
}
MIN_ALL = {
    84441800: 1795439930538,  # W46N8
    84441900: 1795440360904,  # W46N8 (W45N7 official 404)
    84442000: 1795440785198,  # W46N8
    84442100: 1795441211469,  # W46N8
    84442200: 1795441633849,  # W46N8
    84442300: 1795442073570,  # W45N7 (117ms before W46N8 1795442073687)
    84442400: 1795442502633,  # W46N8
}
TMIN, TMAX = 84441801, 84442500
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84441900] - MIN_ALL[84441800]) / 1000.0 / 100  # script printed 4.304, exact 4.30366
GT_FIRST = 84442567
TS_REALIGNED_FIRST = 32  # first-pass realign committed 32 rows (inserted=13622 already_in_db=12334)
PREV_LATER_MEAN = 4.26592  # tick_s_in_use from quiet 2130 half-hour (live-anchor-best all_mean)
"""
if old_w46 not in t:
    raise SystemExit("tick_s_check constants block not found")
p.write_text(t.replace(old_w46, new_w46, 1))
print("tick_s_check updated")

p = DIR / "backfill_confirm.py"
t = p.read_text()
old = """IN_WINDOW = [
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
new = """IN_WINDOW = [
    ("W45N7", 84441900),  # still-untold leftover from quiet 2130 first-pass; still in window start 84441801; retry; do not relabel NEW
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441801; retry as near-window; do not relabel NEW
]
AGED = []  # W45N8@84437100 and W47N7@84436400 already told in 17:46 1728 patrol; aged out of window start 84441801; not retried. Older already-told leftovers also aged out; not retried; do not relabel NEW.
TICK_S = 4.26592
"""
if old not in t:
    raise SystemExit("confirm IN_WINDOW not found")
p.write_text(t.replace(old, new, 1))
print("backfill_confirm IN_WINDOW updated")

old_t = """TARGETS = [
    ("W45N7", 84441900),  # NEW first-pass in-window 404 this 2130 pass; retry
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441301; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441301; retry as near-window; do not relabel NEW
]"""
new_t = """TARGETS = [
    ("W45N7", 84441900),  # still-untold leftover from quiet 2130 first-pass; still in window start 84441801; retry; do not relabel NEW
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441801; retry as near-window; do not relabel NEW
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
if "TMIN, TMAX = 84441301, 84442000" not in t:
    raise SystemExit("coverage TMIN not found")
t = t.replace("TMIN, TMAX = 84441301, 84442000", "TMIN, TMAX = 84441801, 84442500", 1)
if '("W45N7", 84441900)' not in t:
    raise SystemExit("coverage IN_WINDOW_404 missing W45N7@84441900")
p.write_text(t)
print("coverage updated")

for name in ("backfill_just_published.py", "backfill_just_published_retry.py", "backfill_just_published_retry2.py"):
    p = DIR / name
    t = p.read_text()
    if "JUST_BASE = 84442000" not in t:
        raise SystemExit(name + " JUST_BASE not 84442000")
    t = t.replace("JUST_BASE = 84442000", "JUST_BASE = 84442500", 1)
    t = t.replace("base 84442000", "base 84442500")
    p.write_text(t)
    print(name, "JUST_BASE -> 84442500")

p = DIR / "wrapup_snap.py"
t = p.read_text()
if "TMIN, TMAX = 84441301, 84442000" not in t:
    raise SystemExit("wrapup_snap TMIN not found")
t = t.replace("TMIN, TMAX = 84441301, 84442000", "TMIN, TMAX = 84441801, 84442500", 1)
t = t.replace("JP_BASE = 84442000", "JP_BASE = 84442500", 1)

old_f = '''    "freeze_2121_2128": (84441901, 84442049),  # NEW 盒子休眠 21:21:51-21:28:39 (400s, box_pauses); STATS 149t; not yet told; first pass included published 84441900 except W45N7@84441900 404
}
'''
new_f = '''    "freeze_2121_2128": (84441901, 84442049),  # still-untold from quiet 2130; 盒子休眠 21:21:51-21:28:39; STATS 149t; official-filled W46N8/W47N8/W45N8/W47N7 149/149, W45N7 49/149 due to leftover official 404 W45N7@84441900; do not relabel NEW
    "freeze_2143_2201": (84442251, 84442509),  # NEW 盒子休眠 21:43:28-22:01:34 (1078s, box_pauses); STATS 259t; not yet told; first pass included published 84442200..84442400
}
'''
if old_f not in t:
    raise SystemExit("wrapup_snap FREEZES tail not found")
t = t.replace(old_f, new_f, 1)
p.write_text(t)
print("wrapup_snap updated")

t = (DIR / "tick_s_check.py").read_text()
assert "TMIN, TMAX = 84441801, 84442500" in t
assert "PREV_LATER_MEAN = 4.26592" in t
assert "GT_FIRST = 84442567" in t
assert "1795442073570" in t
t = (DIR / "backfill_just_published.py").read_text()
assert "JUST_BASE = 84442500" in t
assert "JUST_BASE = 84442000" not in t
t = (DIR / "coverage.py").read_text()
assert "TMIN, TMAX = 84441801, 84442500" in t
assert '("W45N7", 84441900)' in t
t = (DIR / "wrapup_snap.py").read_text()
assert "JP_BASE = 84442500" in t
assert "freeze_2143_2201" in t
t = (DIR / "backfill_confirm.py").read_text()
assert "TICK_S = 4.26592" in t
assert "window start 84441801" in t
print("all patches ok")
