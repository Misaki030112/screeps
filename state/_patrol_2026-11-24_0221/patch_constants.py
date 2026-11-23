#!/usr/bin/env python3
"""Update tick_s_check, coverage, confirm, exact2h constants for this 1728 first pass."""
from pathlib import Path
import json, re

D = Path("/workspace/screeps/state/_patrol_2026-11-24_0221")
parsed = json.loads((D / "backfill_first_parsed.json").read_text())
maps = (D / "tick_s_maps.py.txt").read_text()
W46_lit = maps.split("MIN_ALL = ", 1)[0].replace("W46 = ", "", 1).strip()
MIN_ALL_lit = maps.split("MIN_ALL = ", 1)[1].strip()

# --- tick_s_check.py ---
p = D / "tick_s_check.py"
t = p.read_text()
# replace the comment + maps + constants up to PREV_LATER_MEAN line
start = t.index("# Official chunk timestamps")
end = t.index("def intervals(d):")
new_block = '''# Official chunk timestamps from history_backfill first pass --minutes 210.
# reconstructed 84435501..84438700 (3200), game.time=84438711
# published_bases=84435500..84438600, inserted=17810 already_in_db=120450
# missing_chunks=3; first-pass realign committed ts_realigned=79168
# printed tick_s=4.213 (exact first-interval 4.21257)
# In-window leftover official 404s (retry at confirm; do not relabel already-told / still-untold as NEW):
#   already-told in 14:44 1427 USER_LOG: W47N8@84435500
#   still-untold from quiet 1500: W47N7@84436400
#   still-untold from quiet 1600: W45N8@84437100
# No additional first-pass 404s this 3h window.
# prev_later / tick_s_in_use carried from quiet 1700: 4.26410 (all_mean)
# Run ONLY on this first-pass window (do not point tick_s_check at a half-hour window).
W46 = ''' + W46_lit + '''
MIN_ALL = ''' + MIN_ALL_lit + '''
TMIN, TMAX = 84435501, 84438700
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84435600] - MIN_ALL[84435500]) / 1000.0 / 100  # script printed 4.213, exact 4.21257
GT_FIRST = 84438711
TS_REALIGNED_FIRST = 79168  # first-pass realign committed 79168 rows (inserted=17810 already_in_db=120450)
PREV_LATER_MEAN = 4.26410  # tick_s_in_use from quiet 1700 half-hour (all_mean)

'''
t = t[:start] + new_block + t[end:]
p.write_text(t)
print("patched tick_s_check.py")

# --- coverage.py ---
p = D / "coverage.py"
t = p.read_text()
t = t.replace("TMIN, TMAX = 84432901, 84436100", "TMIN, TMAX = 84435501, 84438700")
t = t.replace(
    'IN_WINDOW_404 = {("W45N8", 84433100), ("W47N8", 84433300), ("W47N7", 84434000), ("W45N7", 84434800), ("W45N7", 84435400), ("W47N8", 84435500)}',
    'IN_WINDOW_404 = {("W47N8", 84435500), ("W47N7", 84436400), ("W45N8", 84437100)}',
)
p.write_text(t)
print("patched coverage.py")

# --- backfill_confirm.py ---
p = D / "backfill_confirm.py"
t = p.read_text()
t = t.replace(
    """IN_WINDOW = [
    ("W45N8", 84433100),  # already told 1129; retry; do not label NEW
    ("W47N8", 84433300),  # already told 1129; retry; do not label NEW
    ("W47N7", 84434000),  # still-untold from quiet 1200; retry; do not relabel NEW
    ("W45N7", 84434800),  # still-untold from quiet 1300 JP; retry; do not relabel NEW
    ("W45N7", 84435400),  # still-untold NEW from quiet 1400; retry; do not relabel NEW
    ("W47N8", 84435500),  # still-untold NEW from quiet 1400; retry; do not relabel NEW
]
AGED = []
TICK_S = 4.253028333333334  # fallback prev_later from 1400; load_tick_s overrides""",
    """IN_WINDOW = [
    ("W47N8", 84435500),  # already told in 14:44 1427 USER_LOG; retry; do not relabel NEW
    ("W47N7", 84436400),  # still-untold from quiet 1500; retry; do not relabel NEW
    ("W45N8", 84437100),  # still-untold from quiet 1600; retry; do not relabel NEW
]
AGED = [
    ("W45N7", 84435400),  # already told in 14:44 1427; immediately before window start 84435501 (near); retry confirm/late/postjp; do not relabel NEW
]
TICK_S = 4.26410  # fallback tick_s_in_use from quiet 1700 (all_mean); load_tick_s overrides""",
)
p.write_text(t)
print("patched backfill_confirm.py")

# --- exact2h.py BF window ---
p = D / "exact2h.py"
t = p.read_text()
t = t.replace(
    "BF_LO, BF_HI = 84432901, 84436100  # first-pass official window this 3h, missing_chunks=6",
    "BF_LO, BF_HI = 84435501, 84438700  # first-pass official window this 3h, missing_chunks=3",
)
p.write_text(t)
print("patched exact2h.py")
print("done")
