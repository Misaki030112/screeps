#!/usr/bin/env python3
from pathlib import Path

D = Path("/workspace/screeps/state/_patrol_2026-11-24_0820")
maps = (D / "tick_s_maps.py.txt").read_text()
W46_lit = maps.split("MIN_ALL = ", 1)[0].replace("W46 = ", "", 1).strip()
MIN_ALL_lit = maps.split("MIN_ALL = ", 1)[1].strip()

p = D / "tick_s_check.py"
t = p.read_text()
start = t.index("# Official chunk timestamps")
end = t.index("def intervals(d):")
new_block = '''# Official chunk timestamps from history_backfill first pass --minutes 210.
# reconstructed 84447901..84451100 (3200), game.time=84451171
# published_bases=84447900..84451000, inserted=44520 already_in_db=110907
# missing_chunks=5; first-pass realign committed ts_realigned=66148
# printed tick_s=4.345 (exact first-interval 4.34494)
# In-window leftover official 404s (retry at confirm; do not relabel already-told / still-untold as NEW):
#   already-told in 05:38 0522 USER_LOG: W47N8@84448400, W46N8@84448500, W45N8@84448600
#   still-untold from quiet 0730: W46N8@84450500
#   first-pass this 3h (may be lag, retry): W46N8@84450800
# prev_later / tick_s_in_use carried from quiet 0730: 4.30087 (first)
# Run ONLY on this first-pass window (do not point tick_s_check at a half-hour window).
W46 = ''' + W46_lit + '''
MIN_ALL = ''' + MIN_ALL_lit + '''
TMIN, TMAX = 84447901, 84451100
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84448000] - MIN_ALL[84447900]) / 1000.0 / 100  # script printed 4.345, exact 4.34494
GT_FIRST = 84451171
TS_REALIGNED_FIRST = 66148  # first-pass realign committed 66148 rows (inserted=44520 already_in_db=110907)
PREV_LATER_MEAN = 4.30087  # tick_s_in_use from quiet 0730 half-hour (first)

'''
t = t[:start] + new_block + t[end:]
p.write_text(t)
print("patched tick_s_check.py")

p = D / "coverage.py"
t = p.read_text()
old_tmin = None
for line in t.splitlines():
    if line.startswith("TMIN, TMAX"):
        old_tmin = line
        break
if not old_tmin:
    raise SystemExit("missing coverage TMIN")
t = t.replace(old_tmin, "TMIN, TMAX = 84447901, 84451100")
import re
t2, n = re.subn(r"IN_WINDOW_404 = \{[^}]*\}",
    'IN_WINDOW_404 = {("W47N8", 84448400), ("W46N8", 84448500), ("W45N8", 84448600), ("W46N8", 84450500), ("W46N8", 84450800)}',
    t, count=1)
if n != 1:
    raise SystemExit(f"coverage IN_WINDOW_404 replace count={n}")
p.write_text(t2)
print("patched coverage.py")

p = D / "backfill_confirm.py"
t = p.read_text()
start = t.index("IN_WINDOW = [")
end = t.index("PASS = ")
new_block = '''IN_WINDOW = [
    ("W47N8", 84448400),  # already told in 05:38 0522 USER_LOG; retry; do not relabel NEW
    ("W46N8", 84448500),  # already told in 05:38 0522 USER_LOG; listener 50/100; retry; do not relabel NEW
    ("W45N8", 84448600),  # already told in 05:38 0522 USER_LOG; listener 12/100; retry; do not relabel NEW
    ("W46N8", 84450500),  # still-untold from quiet 0730; retry; do not relabel NEW
    ("W46N8", 84450800),  # first-pass this 3h; may be lag; retry
]
AGED = [
    ("W47N8", 84447700),  # already told in 05:38 0522 USER_LOG; immediately before window start 84447901; retry; do not relabel NEW
    ("W45N8", 84447400),  # already told in 05:38 0522 USER_LOG; aged out; retry; do not relabel NEW
    ("W47N7", 84446600),  # already told in 05:38 0522 USER_LOG; aged out; retry; do not relabel NEW
]
TICK_S = 4.30087  # fallback tick_s_in_use from quiet 0730 (first); load_tick_s overrides

'''
t = t[:start] + new_block + t[end:]
p.write_text(t)
print("patched backfill_confirm.py")

p = D / "exact2h.py"
t = p.read_text()
old = "BF_LO, BF_HI = 84445501, 84448700  # first-pass official window this 3h"
new = "BF_LO, BF_HI = 84447901, 84451100  # first-pass official window this 3h, missing_chunks=5"
if old not in t:
    # try any BF_LO line
    found = [ln for ln in t.splitlines() if "BF_LO, BF_HI" in ln]
    print("MISSING exact2h needle, found:", found)
    raise SystemExit("exact2h BF_LO needle missing")
p.write_text(t.replace(old, new))
print("patched exact2h.py")
print("done")
