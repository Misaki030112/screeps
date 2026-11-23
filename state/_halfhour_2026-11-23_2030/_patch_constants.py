from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_2030")

new_block = """W46 = {
    84440600: 1795434799465,
    84440700: 1795435225630,
    84440800: 1795435649753,
    84440900: 1795436092383,
    84441000: 1795436531012,
    84441100: 1795436950877,
    84441200: 1795437375675,
}
MIN_ALL = {
    84440600: 1795434799465,  # W46N8
    84440700: 1795435224056,  # W45N7
    84440800: 1795435649753,  # W46N8
    84440900: 1795436092383,  # W46N8
    84441000: 1795436531012,  # W46N8
    84441100: 1795436950877,  # W46N8
    84441200: 1795437375675,  # W46N8
}
TMIN, TMAX = 84440601, 84441300
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84440700] - MIN_ALL[84440600]) / 1000.0 / 100  # script printed 4.246, exact 4.24591
GT_FIRST = 84441321
TS_REALIGNED_FIRST = 0  # first-pass realign committed 0 rows (inserted=3005 already_in_db=24454)
PREV_LATER_MEAN = 4.272365  # tick_s_in_use from quiet 2000 half-hour (live-anchor-best all_mean)
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
    ("W45N8", 84439200),  # still-untold leftover from quiet 1830; aged out of window start 84440101; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # still-untold leftover from quiet 1830; aged out of window start 84440101; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # still-untold leftover from quiet 1830; aged out of window start 84440101; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # still-untold leftover from quiet 1730 JP; aged out of window start 84440101; retry as near-window; do not relabel NEW
]
AGED = []  # W45N8@84437100 already told in 17:46 1728 patrol; aged out of window start 84440101; not retried. W47N7@84436400 already told in 17:46 1728 patrol; aged out; not retried. Older already-told leftovers also aged out; not retried; do not relabel NEW.
TICK_S = 4.272365"""
new_in = """IN_WINDOW = [
    ("W47N7", 84440900),  # first-pass in-window 404 this 2030 pass (also 404 in concurrent 2028 patrol --minutes 210 at gt=84441217); retry
    ("W45N8", 84439200),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # still-untold leftover from quiet 1730 JP; aged out of window start 84440601; retry as near-window; do not relabel NEW
]
AGED = []  # W45N8@84437100 already told in 17:46 1728 patrol; aged out of window start 84440601; not retried. W47N7@84436400 already told in 17:46 1728 patrol; aged out; not retried. Older already-told leftovers also aged out; not retried; do not relabel NEW.
TICK_S = 4.272365"""
if old_in not in t:
    raise SystemExit("confirm IN_WINDOW block not found")
p.write_text(t.replace(old_in, new_in, 1))
print("confirm IN_WINDOW updated")

old_t = """TARGETS = [
    ("W45N8", 84439200),  # still-untold leftover from quiet 1830; aged out of window start 84440101; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # still-untold leftover from quiet 1830; aged out of window start 84440101; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # still-untold leftover from quiet 1830; aged out of window start 84440101; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # still-untold leftover from quiet 1730 JP; aged out of window start 84440101; retry as near-window; do not relabel NEW
]"""
new_t = """TARGETS = [
    ("W47N7", 84440900),  # first-pass in-window 404 this 2030 pass; retry
    ("W45N8", 84439200),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # still-untold leftover from quiet 1830; aged out of window start 84440601; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # still-untold leftover from quiet 1730 JP; aged out of window start 84440601; retry as near-window; do not relabel NEW
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
if "TMIN, TMAX = 84440101, 84440800" not in t:
    raise SystemExit("coverage TMIN not found")
t = t.replace("TMIN, TMAX = 84440101, 84440800", "TMIN, TMAX = 84440601, 84441300", 1)
old = "IN_WINDOW_404 = {\n}"
new = "IN_WINDOW_404 = {\n    (\"W47N7\", 84440900),\n}"
if old not in t:
    raise SystemExit("coverage IN_WINDOW_404 not found")
p.write_text(t.replace(old, new, 1))
print("coverage updated")

for name in ("backfill_just_published.py", "backfill_just_published_retry.py", "backfill_just_published_retry2.py"):
    p = DIR / name
    t = p.read_text()
    if "JUST_BASE = 84440800" not in t:
        raise SystemExit(f"{name} JUST_BASE not 84440800: " + ("present " + str("JUST_BASE" in t)))
    t = t.replace("JUST_BASE = 84440800", "JUST_BASE = 84441300", 1)
    t = t.replace("base 84440800", "base 84441300")
    p.write_text(t)
    print(name, "JUST_BASE -> 84441300")

print("all patches ok")
