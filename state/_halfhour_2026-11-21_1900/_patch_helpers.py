#!/usr/bin/env python3
from pathlib import Path

# --- tick_s_check.py ---
p = Path("/workspace/screeps/state/_halfhour_2026-11-21_1900/tick_s_check.py")
t = p.read_text()
t = t.replace("_halfhour_2026-11-21_1830", "_halfhour_2026-11-21_1900")

old_comment = """# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84397900..84398500 at game.time=84398668; reconstructed 84397901..84398600 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84398000-84397900)/1000/100 = 4.31144, script printed 4.311. First-pass realign moved 0
# (inserted=2022; already_in_db=21700). Overlap compared=21369 match=20662 differ=707; backfill does not
# overwrite existing rows. Samples: W47N8@84398501 opening tick looks one tick behind live (hist matches
# listener 84398500), consistent with null opening-tick keep-previous-state; W46N8 rhauler84397559@84398469
# store-only db 170 vs hist 0 (xy/hits match).
# 18:00 half-hour already wrote through 84398200 / just-published 84398200 for all 5
# (ticks 84398201..84398300 at 18:09:31 gt=84398341). 18:17 1h patrol already official-filled 84397701..84398400
# and just-published 84398400 (all_five_200). This run must not restart the listener or war_cmd/pulse.
# No new box freeze after already-told 17:51:07-17:58:33 (STATS 84398081..84398189, 109t, official-filled all five
# 109/109; listener auto-restart 17:58:36, python 2000028 started 17:58:45). Short WS 17:23:22 STATS 84397671..84397699
# ages out of window start 84397901. Already-told leftover official 404 W45N7@84397400 ages out and was not retried.
# W45N7 evac empty after Invader Core 84398417: official 84398401..84398500 is 60/100 (max 84398460), 84398501..84398600 is 0/100, not a 404.
# No concurrent 1h patrol (last _patrol_2026-11-21_1817 finished ~18:27). Do not write a patrol folder.
# MIN_ALL uses W45N7 on 84397900 and 84398100 (slightly earlier than W46N8); every other base uses W46N8."""

new_comment = """# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84398300..84398900 at game.time=84399054; reconstructed 84398301..84399000 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84398400-84398300)/1000/100 = 4.33285, script printed 4.333. First-pass realign moved 2937
# (inserted=8839; already_in_db=15768). Overlap compared=15667 match=14358 differ=1309; backfill does not
# overwrite existing rows. Samples: W47N8@84398501 opening tick looks one tick behind live (hist matches
# listener 84398500), plus w8builder@84398502 same pattern; consistent with null opening-tick keep-previous-state.
# 18:30 half-hour already wrote through 84398600 / just-published 84398600 for all 5
# (ticks 84398601..84398700 at 18:38:26 gt=84398742). This run must not restart the listener or war_cmd/pulse.
# NEW box freeze 18:47:50-18:58:17 (626s, already healed); STATS 84398871..84399029 (159t);
# listener auto-restart 18:58:20, python 2029084 started 18:58:29. Not yet told; leave to next 1h patrol.
# Already-told 17:51:07-17:58:33 STATS 84398081..84398189 ages out of window start 84398301.
# Short WS 17:23:22 STATS 84397671..84397699 already aged out. Already-told leftover official 404
# W45N7@84397400 ages out and was not retried. W45N7 evac empty after Invader Core 84398417 continues
# in this window (db_after distinct=377/700 max 84398865); official 200, not a 404.
# No concurrent 1h patrol (last _patrol_2026-11-21_1817 finished ~18:27). Do not write a patrol folder.
# MIN_ALL equals W46N8 on every published base in this window."""

if old_comment not in t:
    raise SystemExit("old tick_s comment block not found")
t = t.replace(old_comment, new_comment)

old_maps = """W46 = {
    84397900: 1795254339046,
    84398000: 1795254768719,
    84398100: 1795255197043,
    84398200: 1795255628684,
    84398300: 1795256065062,
    84398400: 1795256498347,
    84398500: 1795256930397,
}
MIN_ALL = {
    84397900: 1795254337575,  # W45N7
    84398000: 1795254768719,  # W46N8
    84398100: 1795255196185,  # W45N7
    84398200: 1795255628684,  # W46N8
    84398300: 1795256065062,  # W46N8
    84398400: 1795256498347,  # W46N8
    84398500: 1795256930397,  # W46N8
}
TMIN, TMAX = 84397901, 84398600
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84398000] - MIN_ALL[84397900]) / 1000.0 / 100  # script printed 4.311, exact 4.31144
GT_FIRST = 84398668
TS_REALIGNED_FIRST = 0  # first-pass realign moved 0 (inserted=2022, already_in_db=21700, missing_chunks=0)
PREV_LATER_MEAN = 4.278866  # 18:00 half-hour tick_s_in_use (later_raw)"""

new_maps = """W46 = {
    84398300: 1795256065062,
    84398400: 1795256498347,
    84398500: 1795256930397,
    84398600: 1795257358119,
    84398700: 1795257779780,
    84398800: 1795258206579,
    84398900: 1795258632694,
}
MIN_ALL = {
    84398300: 1795256065062,  # W46N8
    84398400: 1795256498347,  # W46N8
    84398500: 1795256930397,  # W46N8
    84398600: 1795257358119,  # W46N8
    84398700: 1795257779780,  # W46N8
    84398800: 1795258206579,  # W46N8
    84398900: 1795258632694,  # W46N8
}
TMIN, TMAX = 84398301, 84399000
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84398400] - MIN_ALL[84398300]) / 1000.0 / 100  # script printed 4.333, exact 4.33285
GT_FIRST = 84399054
TS_REALIGNED_FIRST = 2937  # first-pass realign moved 2937 (inserted=8839, already_in_db=15768, missing_chunks=0)
PREV_LATER_MEAN = 4.31144  # 18:30 half-hour tick_s_in_use (first)"""

if old_maps not in t:
    raise SystemExit("old tick_s maps not found")
t = t.replace(old_maps, new_maps)

t = t.replace("(printed 4.311) moved", "(printed 4.333) moved")
t = t.replace("inserted=2022, already_in_db=21700, missing_chunks=0).", "inserted=8839, already_in_db=15768, missing_chunks=0).")
t = t.replace("(printed 4.311, min-all-rooms first two bases)", "(printed 4.333, min-all-rooms first two bases)")
p.write_text(t)
print("tick_s_check patched, leftover 1830?", "_halfhour_2026-11-21_1830" in t)

# --- confirm.py ---
c = Path("/workspace/screeps/state/_halfhour_2026-11-21_1900/backfill_confirm.py")
ct = c.read_text()
ct = ct.replace("_halfhour_2026-11-21_1830", "_halfhour_2026-11-21_1900")
old_in = """IN_WINDOW = []  # first pass 35/35 official GETs 200, missing_chunks=0. Window 84397901..84398600 (published_bases 84397900..84398500 at game.time=84398668). Already-told leftover official 404 W45N7@84397400 aged out of window start 84397901 and is not retried. W45N7 evac empty after 84398460 is not a 404.
AGED = []
TICK_S = 4.311"""
new_in = """IN_WINDOW = []  # first pass 35/35 official GETs 200, missing_chunks=0. Window 84398301..84399000 (published_bases 84398300..84398900 at game.time=84399054). Already-told leftover official 404 W45N7@84397400 aged out of window start 84398301 and is not retried. W45N7 evac empty after Invader Core 84398417 (db_after 377/700 max 84398865) is official 200, not a 404.
AGED = []
TICK_S = 4.333"""
if old_in not in ct:
    raise SystemExit("confirm IN_WINDOW block not found")
ct = ct.replace(old_in, new_in)
c.write_text(ct)
print("confirm patched, leftover 1830?", "_halfhour_2026-11-21_1830" in ct)

# --- just_published.py ---
j = Path("/workspace/screeps/state/_halfhour_2026-11-21_1900/backfill_just_published.py")
jt = j.read_text()
jt = jt.replace("_halfhour_2026-11-21_1830", "_halfhour_2026-11-21_1900")
jt = jt.replace("JUST_BASE = 84398600", "JUST_BASE = 84399000")
jt = jt.replace("base 84398600 once game.time is safely past 84398340", "base 84399000 once game.time is safely past 84399140")
j.write_text(jt)
print("just_published patched, leftover 1830?", "_halfhour_2026-11-21_1830" in jt)
for line in jt.splitlines():
    if "JUST_BASE" in line or "WAIT_UNTIL" in line or "DIR =" in line:
        print(" ", line)
