from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_2230")

p = DIR / "tick_s_check.py"
t = p.read_text()
old_w46 = """W46 = {
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
new_w46 = """W46 = {
    84442300: 1795442073687,
    84442400: 1795442502633,
    84442500: 1795442928244,
    84442600: 1795443358557,
    84442700: 1795443780299,
    84442800: 1795444202146,
    84442900: 1795444633865,
}
MIN_ALL = {
    84442300: 1795442073570,  # W45N7 (117ms before W46N8 1795442073687)
    84442400: 1795442502633,  # W46N8
    84442500: 1795442928244,  # W46N8
    84442600: 1795443358557,  # W46N8
    84442700: 1795443780299,  # W46N8
    84442800: 1795444202146,  # W46N8
    84442900: 1795444633865,  # W46N8
}
TMIN, TMAX = 84442301, 84443000
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84442400] - MIN_ALL[84442300]) / 1000.0 / 100  # script printed 4.291, exact 4.29063
GT_FIRST = 84443044
TS_REALIGNED_FIRST = 0  # first-pass realign committed 0 rows (inserted=13825 already_in_db=13054)
PREV_LATER_MEAN = 4.28346  # tick_s_in_use from quiet 2200 half-hour (live-anchor-best later_raw)
"""
if old_w46 not in t:
    raise SystemExit("tick_s_check constants block not found")
p.write_text(t.replace(old_w46, new_w46, 1))
print("tick_s_check updated")

p = DIR / "backfill_confirm.py"
t = p.read_text()
old = """IN_WINDOW = [
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
new = """IN_WINDOW = [
    ("W45N7", 84441900),  # still-untold leftover from quiet 2130 first-pass; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84442301; retry as near-window; do not relabel NEW
]
AGED = []  # W45N8@84437100 and W47N7@84436400 already told in 17:46 1728 patrol; aged out of window start 84442301; not retried. Older already-told leftovers also aged out; not retried; do not relabel NEW.
TICK_S = 4.28346
"""
if old not in t:
    raise SystemExit("confirm IN_WINDOW not found")
p.write_text(t.replace(old, new, 1))
print("backfill_confirm IN_WINDOW updated")

old_t = """TARGETS = [
    ("W45N7", 84441900),  # still-untold leftover from quiet 2130 first-pass; still in window start 84441801; retry; do not relabel NEW
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441801; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441801; retry as near-window; do not relabel NEW
]"""
new_t = """TARGETS = [
    ("W45N7", 84441900),  # still-untold leftover from quiet 2130 first-pass; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84442301; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84442301; retry as near-window; do not relabel NEW
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
if "TMIN, TMAX = 84441801, 84442500" not in t:
    raise SystemExit("coverage TMIN not found")
t = t.replace("TMIN, TMAX = 84441801, 84442500", "TMIN, TMAX = 84442301, 84443000", 1)
# leftover 404 is now outside this first-pass window; keep the set empty for this window
old_c = """IN_WINDOW_404 = {
    ("W45N7", 84441900),
}"""
new_c = """IN_WINDOW_404 = {
    # no first-pass in-window official 404 this 2230 pass; still-untold leftover W45N7@84441900 aged out of 84442301..84443000
}"""
if old_c not in t:
    raise SystemExit("coverage IN_WINDOW_404 not found")
t = t.replace(old_c, new_c, 1)
p.write_text(t)
print("coverage updated")

for name in ("backfill_just_published.py", "backfill_just_published_retry.py", "backfill_just_published_retry2.py"):
    p = DIR / name
    t = p.read_text()
    if "JUST_BASE = 84442500" not in t:
        raise SystemExit(name + " JUST_BASE not 84442500")
    t = t.replace("JUST_BASE = 84442500", "JUST_BASE = 84443000", 1)
    t = t.replace("base 84442500", "base 84443000")
    p.write_text(t)
    print(name, "JUST_BASE -> 84443000")

p = DIR / "wrapup_snap.py"
t = p.read_text()
if "TMIN, TMAX = 84441801, 84442500" not in t:
    raise SystemExit("wrapup_snap TMIN not found")
t = t.replace("TMIN, TMAX = 84441801, 84442500", "TMIN, TMAX = 84442301, 84443000", 1)
t = t.replace("JP_BASE = 84442500", "JP_BASE = 84443000", 1)

old_f = '''    "freeze_2143_2201": (84442251, 84442509),  # NEW 盒子休眠 21:43:28-22:01:34 (1078s, box_pauses); STATS 259t; not yet told; first pass included published 84442200..84442400
}
'''
new_f = '''    "freeze_2143_2201": (84442251, 84442509),  # still-untold from quiet 2200; 盒子休眠 21:43:28-22:01:34; STATS 259t; official-filled all five 259/259 after 2200 first pass plus JP 84442500; do not relabel NEW
    "freeze_2223_2235": (84442741, 84442989),  # NEW 盒子休眠 22:23:02-22:35:40 (747s, box_pauses); STATS 249t; not yet told; first pass included published 84442700..84442900
}
'''
if old_f not in t:
    raise SystemExit("wrapup_snap FREEZES tail not found")
t = t.replace(old_f, new_f, 1)
p.write_text(t)
print("wrapup_snap updated")

t = (DIR / "tick_s_check.py").read_text()
assert "TMIN, TMAX = 84442301, 84443000" in t
assert "PREV_LATER_MEAN = 4.28346" in t
assert "GT_FIRST = 84443044" in t
assert "1795442073570" in t
t = (DIR / "backfill_just_published.py").read_text()
assert "JUST_BASE = 84443000" in t
assert "JUST_BASE = 84442500" not in t
t = (DIR / "coverage.py").read_text()
assert "TMIN, TMAX = 84442301, 84443000" in t
t = (DIR / "wrapup_snap.py").read_text()
assert "JP_BASE = 84443000" in t
assert "freeze_2223_2235" in t
t = (DIR / "backfill_confirm.py").read_text()
assert "TICK_S = 4.28346" in t
assert "window start 84442301" in t
print("all patches ok")
