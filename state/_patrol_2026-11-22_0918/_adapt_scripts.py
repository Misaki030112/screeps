#!/usr/bin/env python3
from pathlib import Path

# --- tick_s_check.py ---
p = Path("/workspace/screeps/state/_patrol_2026-11-22_0918/tick_s_check.py")
text = p.read_text()
text = text.replace(
    'DIR = ROOT / "state" / "_halfhour_2026-11-22_0900"',
    'DIR = ROOT / "state" / "_patrol_2026-11-22_0918"',
)
start = text.index("# Official chunk timestamps printed by history_backfill.py")
end = text.index("\ndef intervals(d):")
# The above escaped newline is wrong if we used raw; search without escape
end = text.index("def intervals(d):")
# include leading newlines before def
# find last newline before def
end = text.rfind("\n", 0, end)
# simpler: cut to the 'def intervals' line start
end = text.index("def intervals(d):")
new_block = '''# Official chunk timestamps printed by history_backfill.py
# First pass 34 of 35 official GETs 200, missing_chunks=1 W47N7@84411200.
# published_bases 84410600..84411200 at game.time=84411311; reconstructed 84410601..84411300 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84410700-84410600)/1000/100 = 4.01671, script printed 4.017.
# Insert committed inserted=5417 already_in_db=18221, first-pass realign ts_realigned=7354.
# 09:00 half-hour already wrote through 84411000 / just-published 84411000 for all 5.
# Last 1h patrol delivered 08:28 _patrol_2026-11-22_0818. Concurrent none.
# Do not restart the listener or war_cmd/pulse. Single listener 2371673 since 09:19:17
# after NEW box freeze 09:14:15-09:19:05 (283s) and earlier 08:51:14-09:01:02 (581s).
# In-window official 404: W47N7@84411200. Already-told leftovers W47N8@84409800 and older
# aged out of window start 84410601 and are not retried this pass. Unpublished tail
# after 84411300 waits on just-published 84411300.
W46 = {
    84410600: 1795307946021,
    84410700: 1795308347692,
    84410800: 1795308755249,
    84410900: 1795309161287,
    84411000: 1795309580854,
    84411100: 1795309983841,
    84411200: 1795310396821,
}
MIN_ALL = {
    84410600: 1795307946021,  # W46N8
    84410700: 1795308347692,  # W46N8
    84410800: 1795308755249,  # W46N8
    84410900: 1795309161287,  # W46N8
    84411000: 1795309580854,  # W46N8
    84411100: 1795309983841,  # W46N8
    84411200: 1795310395391,  # W45N7 (W47N7 404; W45N7 earlier than W46N8)
}
TMIN, TMAX = 84410601, 84411300
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84410700] - MIN_ALL[84410600]) / 1000.0 / 100  # script printed 4.017, exact 4.01671
GT_FIRST = 84411311
TS_REALIGNED_FIRST = 7354
PREV_LATER_MEAN = 4.099614  # tick_s_in_use from quiet 09:00 halfhour


'''
text = text[:start] + new_block + text[end:]
text = text.replace("printed 4.101", "printed 4.017")
p.write_text(text)
print("patched tick_s_check.py")
print("TICK_S_FIRST", (1795308347692-1795307946021)/1000/100)

# --- backfill_confirm.py ---
p = Path("/workspace/screeps/state/_patrol_2026-11-22_0918/backfill_confirm.py")
text = p.read_text()
start = text.index("# First pass at game.time=")
end = text.index("def load_tick_s():")
new_block = '''# First pass at game.time=84411311; published_bases 84410600..84411200,
# reconstructed 84410601..84411300 (700). inserted=5417, already_in_db=18221,
# ts_realigned_first_pass=7354 (first-interval tick_s=4.01671 script printed 4.017).
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 34 of 35 official GETs 200, missing_chunks=1 W47N7@84411200.
# Leftover official 404s W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900
# and older aged out of this window start 84410601 and are not retried.
# 09:00 half-hour official already through 84410900 / just-published 84411000.
# NEW box freeze 09:14:15-09:19:05 and earlier 08:51:14-09:01:02 sit inside/near this window.
IN_WINDOW = [("W47N7", 84411200)]
AGED = []
TICK_S = 4.017
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUT = "/workspace/screeps/state/_patrol_2026-11-22_0918/backfill_confirm_gets.json"
TICK_S_FILE = "/workspace/screeps/state/_patrol_2026-11-22_0918/tick_s_realign.json"

'''
text = text[:start] + new_block + text[end:]
p.write_text(text)
print("patched backfill_confirm.py")

# --- just_published ---
p = Path("/workspace/screeps/state/_patrol_2026-11-22_0918/backfill_just_published.py")
text = p.read_text()
n1 = text.count("_halfhour_2026-11-22_0900")
text = text.replace("_halfhour_2026-11-22_0900", "_patrol_2026-11-22_0918")
n2 = text.count("JUST_BASE = 84411000")
text = text.replace("JUST_BASE = 84411000", "JUST_BASE = 84411300")
p.write_text(text)
print("patched just_published", "halfhour", n1, "just_base", n2)

# --- late_retry ---
p = Path("/workspace/screeps/state/_patrol_2026-11-22_0918/backfill_late_retry.py")
text = p.read_text()
n = text.count("_halfhour_2026-11-22_0900")
text = text.replace("_halfhour_2026-11-22_0900", "_patrol_2026-11-22_0918")
p.write_text(text)
print("patched late_retry", n)

# --- exact2h ---
p = Path("/workspace/screeps/state/_patrol_2026-11-22_0918/exact2h.py")
text = p.read_text()
old1 = "LAST_TIP = 84409680  # previous 1h patrol analysis tip (07:28:58 later live 84409752 / room_stats 84409750)"
new1 = "LAST_TIP = 84410480  # previous 1h patrol analysis tip (08:23:24 later live/room_stats 84410550 08:28:14)"
old2 = "BF_LO, BF_HI = 84409701, 84410400  # first-pass official window this hour, missing_chunks=1 W47N8@84409800"
new2 = "BF_LO, BF_HI = 84410601, 84411300  # first-pass official window this hour, missing_chunks=1 W47N7@84411200"
assert old1 in text, "LAST_TIP not found"
assert old2 in text, "BF_LO not found"
text = text.replace(old1, new1).replace(old2, new2)
p.write_text(text)
print("patched exact2h.py")
