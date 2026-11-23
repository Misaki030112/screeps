from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_2100")

new_block = """W46 = {
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

p = DIR / "tick_s_check.py"
t = p.read_text()
pat = re.compile(r"W46 = \{.*?\nPREV_LATER_MEAN = [^\n]+\n", re.S)
t2, n = pat.subn(new_block, t, count=1)
if n != 1:
    raise SystemExit(f"tick_s_check W46 block replace count={n}")
p.write_text(t2)
print("tick_s_check constants updated")

p = DIR / "backfill_confirm.py"
t = p.read_text()
old_in = """IN_WINDOW = [
    ("W47N7", 84440900),  # first-pass in-window 404 this 2030 pass (also 404 in concurrent 2028 patrol --minutes 210 at gt=84441217); retry
    ("W45N8", 84439200),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # still-untold leftover from quiet 1730 JP; aged out of window start 84440601; retry as near-window; do not relabel NEW
]
AGED = []  # W45N8@84437100 already told in 17:46 1728 patrol; aged out of window start 84440601; not retried. W47N7@84436400 already told in 17:46 1728 patrol; aged out; not retried. Older already-told leftovers also aged out; not retried; do not relabel NEW.
TICK_S = 4.272365"""
new_in = """IN_WINDOW = [
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441001 by 1 tick; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441001; retry as near-window; do not relabel NEW
]
AGED = []  # W45N8@84437100 and W47N7@84436400 already told in 17:46 1728 patrol; aged out of window start 84441001; not retried. Older already-told leftovers also aged out; not retried; do not relabel NEW.
TICK_S = 4.29368"""
if old_in not in t:
    raise SystemExit("confirm IN_WINDOW block not found")
p.write_text(t.replace(old_in, new_in, 1))
print("confirm IN_WINDOW updated")

old_t = """TARGETS = [
    ("W47N7", 84440900),  # first-pass in-window 404 this 2030 pass; retry
    ("W45N8", 84439200),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # still-untold leftover from quiet 1730 JP; aged out of window start 84440601; retry as near-window; do not relabel NEW
]"""
new_t = """TARGETS = [
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; leftover from quiet 2030 first-pass; aged out of window start 84441001 by 1 tick; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830; aged out of window start 84441001; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; aged out of window start 84441001; retry as near-window; do not relabel NEW
]"""
for name in ("backfill_late_retry.py", "backfill_postjp_retry.py"):
    p = DIR / name
    t = p.read_text()
    if old_t not in t:
        raise SystemExit(f"{name} TARGETS not found")
    p.write_text(t.replace(old_t, new_t, 1))
    print(name, "TARGETS updated")

p = DIR / "coverage.py"
t = p.read_text()
if "TMIN, TMAX = 84440601, 84441300" not in t:
    raise SystemExit("coverage TMIN not found")
t = t.replace("TMIN, TMAX = 84440601, 84441300", "TMIN, TMAX = 84441001, 84441700", 1)
old = "IN_WINDOW_404 = {\n    (\"W47N7\", 84440900),\n}"
new = "IN_WINDOW_404 = {\n}"
if old not in t:
    raise SystemExit("coverage IN_WINDOW_404 not found")
t = t.replace(old, new, 1)
old_c = """# First pass --minutes 40. First pass 35/35 official GETs 200, missing_chunks=0.
# published_bases 84440100..84440700 at game.time=84440883; reconstructed
# 84440101..84440800 (700). 19:30 half-hour official-filled 84439801..84440500
# / JP 84440500. No first-pass in-window 404. W47N7 distinct=507/700 is
# official empty_no_creep 84440302..84440494 (193t; 507+193=700), not a 404.
# Still-untold leftover official 404s W45N8@84439200 / W45N8@84439300 /
# W45N8@84439500 (from quiet 1830) and W47N7@84438700 (from quiet 1730 JP)
# aged out of window start 84440101; retried as near-window on
# confirm/retry2/late and still 404; retry on postjp; do not relabel NEW.
# Already-told leftovers W45N8@84437100, W47N7@84436400 and older aged out
# of 84440101; not retried.
# First pass inserted=5939 already_in_db=20328 ts_realigned=9131; tick_s printed 4.293.
# tick_s_in_use=4.272365 (all_mean). Do not restart the listener. Do not write a patrol folder.
"""
new_c = """# First pass --minutes 40. First pass 35/35 official GETs 200, missing_chunks=0.
# published_bases 84441000..84441600 at game.time=84441737; reconstructed
# 84441001..84441700 (700). Quiet 2030 official-filled 84440601..84441300
# / JP 84441300. No first-pass in-window 404 this 2100 pass.
# Already-told leftover official 404 W47N7@84440900 (from quiet 2030 /
# told in 20:44 2028 patrol) aged out of window start 84441001 by 1 tick;
# retried as near-window on confirm/retry2/late/postjp; do not relabel NEW.
# Already-told leftovers W45N8@84439200 / W45N8@84439300 / W45N8@84439500
# (from quiet 1830) and W47N7@84438700 (from quiet 1730 JP) also aged out;
# retry as near-window; do not relabel NEW.
# Already-told leftovers W45N8@84437100, W47N7@84436400 and older aged out
# of 84441001; not retried.
# First pass inserted=9432 already_in_db=16526 ts_realigned=12; tick_s printed 4.199.
# Do not restart the listener. Do not write a patrol folder.
"""
if old_c not in t:
    print("WARN coverage comment block not found; TMIN/IN_WINDOW already patched")
else:
    t = t.replace(old_c, new_c, 1)
p.write_text(t)
print("coverage updated")

for name in ("backfill_just_published.py", "backfill_just_published_retry.py", "backfill_just_published_retry2.py"):
    p = DIR / name
    t = p.read_text()
    if "JUST_BASE = 84441300" not in t:
        raise SystemExit(f"{name} JUST_BASE not 84441300")
    t = t.replace("JUST_BASE = 84441300", "JUST_BASE = 84441700", 1)
    t = t.replace("base 84441300", "base 84441700")
    p.write_text(t)
    print(name, "JUST_BASE -> 84441700")

p = DIR / "wrapup_snap.py"
t = p.read_text()
if "TMIN, TMAX = 84440101, 84440800" not in t:
    if "TMIN, TMAX = 84440601, 84441300" in t:
        t = t.replace("TMIN, TMAX = 84440601, 84441300", "TMIN, TMAX = 84441001, 84441700", 1)
        t = t.replace("JP_BASE = 84441300", "JP_BASE = 84441700", 1)
    else:
        raise SystemExit("wrapup_snap TMIN not found")
else:
    t = t.replace("TMIN, TMAX = 84440101, 84440800", "TMIN, TMAX = 84441001, 84441700", 1)
    t = t.replace("JP_BASE = 84440800", "JP_BASE = 84441700", 1)

old_h = 'HOLES = [("W45N8", 84439200), ("W45N8", 84439300), ("W45N8", 84439500), ("W47N7", 84438700), ("W45N8", 84437100), ("W47N7", 84436400)]'
new_h = 'HOLES = [("W47N7", 84440900), ("W45N8", 84439200), ("W45N8", 84439300), ("W45N8", 84439500), ("W47N7", 84438700), ("W45N8", 84437100), ("W47N7", 84436400)]'
if old_h not in t:
    raise SystemExit("wrapup_snap HOLES not found")
t = t.replace(old_h, new_h, 1)

old_f = '''    "freeze_1816_1835": (84439341, 84439619),  # still-untold from quiet 1830; 盒子休眠 18:16:12-18:35:22; STATS 279t; do not relabel NEW
    "freeze_1852_1858": (84439851, 84439959),  # still-untold from quiet 1900; 盒子休眠 18:52:46-18:58:58; STATS 109t; do not relabel NEW
    "freeze_1921_1934": (84440261, 84440459),  # still-untold from quiet 1930; 盒子休眠 19:21:55-19:34:51; STATS 199t; do not relabel NEW
    "shortws_2001": (84440811, 84440839),  # NEW 监听短中断 20:01:56 ws ping/pong timed out; no box_pauses row; listener auto-restarted 20:01:59, python 3249780 started 20:02:09; STATS 29t; JP 84440800 may fill official after first-pass window end 84440800
}
'''
new_f = '''    "freeze_1816_1835": (84439341, 84439619),  # already told in 20:44 2028 patrol; 盒子休眠 18:16:12-18:35:22; STATS 279t
    "freeze_1852_1858": (84439851, 84439959),  # already told in 20:44 2028 patrol; 盒子休眠 18:52:46-18:58:58; STATS 109t
    "freeze_1921_1934": (84440261, 84440459),  # already told in 20:44 2028 patrol; 盒子休眠 19:21:55-19:34:51; STATS 199t
    "shortws_2001": (84440811, 84440839),  # already told in 20:44 2028 patrol; 监听短中断 20:01:56; STATS 29t
    "freeze_2014_2028": (84441001, 84441209),  # already told in 20:44 2028 patrol; 盒子休眠 20:14:37-20:28:31; STATS 209t; official-filled all five 209/209
    "freeze_2056_2101": (84441591, 84441679),  # NEW 盒子休眠 20:56:44-21:01:46 (292s, box_pauses); STATS 89t; not yet told; first pass included published 84441600
}
'''
if old_f not in t:
    raise SystemExit("wrapup_snap FREEZES tail not found")
t = t.replace(old_f, new_f, 1)
p.write_text(t)
print("wrapup_snap updated")

t = (DIR / "tick_s_check.py").read_text()
assert "TMIN, TMAX = 84441001, 84441700" in t
assert "PREV_LATER_MEAN = 4.29368" in t
t = (DIR / "backfill_just_published.py").read_text()
assert "JUST_BASE = 84441700" in t
assert "JUST_BASE = 84441300" not in t
t = (DIR / "coverage.py").read_text()
assert "TMIN, TMAX = 84441001, 84441700" in t
assert "IN_WINDOW_404 = {" in t and '("W47N7", 84440900)' not in t
t = (DIR / "wrapup_snap.py").read_text()
assert "JP_BASE = 84441700" in t
assert "freeze_2056_2101" in t
print("all patches ok")
