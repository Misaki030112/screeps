#!/usr/bin/env python3
from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-22_1630")

# --- tick_s_check.py ---
p = DIR / "tick_s_check.py"
t = p.read_text()
old = '''# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0, exit=0.
# published_bases 84416400..84417000 at game.time=84417167; reconstructed 84416401..84417100 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84416500-84416400)/1000/100 = 4.21116, script printed 4.211.
# Insert committed inserted=8086 already_in_db=18451, first-pass realign committed
# ts_realigned=1873.
# No in-window official 404. Already-told leftover W45N8@84415500 and older aged
# out of window start 84416401 and were not retried (already told in the 14:28
# or earlier patrol; 15:32 patrol also recorded the age-out).
# 15:30 half-hour already official-filled through 84416700 / just-published 84416700.
# 15:32 patrol already official-filled through 84416500 / just-published 84416600
# (finished_at 15:34:21).
# Box freeze 14:47:50-15:01:16 already told in the 15:32 patrol.
# NEW short WS 16:02:42-16:02:55 (ping/pong timeout, no box_pauses row);
# STATS gap 84417111..84417129 (19t) sits just after this first-pass window
# (in unpublished 84417100). Listener 2540965 started 16:02:55 (parent 4035476).
# Do not restart. Do not write a patrol/12h-review folder.
# Last delivered USER_LOG is 15:32 _patrol_2026-11-22_1521. Fold only newer leftover
# official 404s / freezes / short WS than that already-told set.
W46 = {
    84416400: 1795332018595,
    84416500: 1795332439711,
    84416600: 1795332845854,
    84416700: 1795333261961,
    84416800: 1795333671696,
    84416900: 1795334076598,
    84417000: 1795334503505,
}
MIN_ALL = {
    84416400: 1795332018595,  # W46N8
    84416500: 1795332439711,  # W46N8
    84416600: 1795332845854,  # W46N8
    84416700: 1795333261961,  # W46N8
    84416800: 1795333671696,  # W46N8
    84416900: 1795334076598,  # W46N8
    84417000: 1795334503505,  # W46N8
}
TMIN, TMAX = 84416401, 84417100
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84416500] - MIN_ALL[84416400]) / 1000.0 / 100  # script printed 4.211, exact 4.21116
GT_FIRST = 84417167
TS_REALIGNED_FIRST = 1873  # first-pass realign committed 1873 (inserted=8086 already_in_db=18451)
PREV_LATER_MEAN = 4.192072  # later_mean_w46 from quiet 15:30 halfhour
'''
new = '''# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0, exit=0.
# published_bases 84416800..84417400 at game.time=84417537; reconstructed 84416801..84417500 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84416900-84416800)/1000/100 = 4.04902, script printed 4.049.
# Insert committed inserted=100 already_in_db=27206, first-pass realign committed
# ts_realigned=10444.
# No in-window official 404. Already-told leftover W45N8@84415500 and older aged
# out of window start 84416801 and were not retried (already told in the 14:28
# or earlier patrol; 15:32 patrol also recorded the age-out).
# 16:00 half-hour already official-filled through 84417100 / just-published 84417100.
# 15:30 half-hour official-filled through 84416700 / just-published 84416700.
# 15:32 patrol already official-filled through 84416500 / just-published 84416600
# (finished_at 15:34:21).
# NEW box freeze 16:15:02-16:22:09 (423s, box_pauses row); STATS 84417291..84417409
# (119t) sits inside this first-pass window. Listener auto-restart 16:22:13,
# python 2548139 started 16:22:22 (parent 4035476). Do not restart.
# short WS 16:02:42-16:02:55 STATS 84417111..84417129 recorded in the 16:00
# half-hour; not yet told. Do not write a patrol/12h-review folder.
# Last delivered USER_LOG is 15:32 _patrol_2026-11-22_1521. Fold only newer leftover
# official 404s / freezes / short WS than that already-told set.
W46 = {
    84416800: 1795333671696,
    84416900: 1795334076598,
    84417000: 1795334503505,
    84417100: 1795334918185,
    84417200: 1795335334980,
    84417300: 1795335759577,
    84417400: 1795336158078,
}
MIN_ALL = {
    84416800: 1795333671696,  # W46N8
    84416900: 1795334076598,  # W46N8
    84417000: 1795334503505,  # W46N8
    84417100: 1795334917727,  # W45N7
    84417200: 1795335334980,  # W46N8
    84417300: 1795335759577,  # W46N8
    84417400: 1795336158078,  # W46N8
}
TMIN, TMAX = 84416801, 84417500
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84416900] - MIN_ALL[84416800]) / 1000.0 / 100  # script printed 4.049, exact 4.04902
GT_FIRST = 84417537
TS_REALIGNED_FIRST = 10444  # first-pass realign committed 10444 (inserted=100 already_in_db=27206)
PREV_LATER_MEAN = 4.127588  # later_mean_w46 from quiet 16:00 halfhour
'''
if old not in t:
    raise SystemExit("tick_s_check header block not found")
t = t.replace(old, new, 1)
t = t.replace("(printed 4.035)", "(printed 4.049)")
t = t.replace("(printed 4.035, min-all-rooms first two bases)", "(printed 4.049, min-all-rooms first two bases)")
p.write_text(t)
print("tick_s_check.py updated")

# --- confirm ---
p = DIR / "backfill_confirm.py"
t = p.read_text()
old = '''# First pass at game.time=84417167; published_bases 84416400..84417000,
# reconstructed 84416401..84417100 (700). inserted=8086, already_in_db=18451,
# ts_realigned_first_pass=1873 (first-interval tick_s script printed 4.211, exact 4.21116).
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# 15:30 half-hour already official-filled through 84416700 / just-published 84416700;
# 15:32 patrol already official-filled through 84416500 / just-published 84416600.
# Already-told leftover official 404 W45N8@84415500 and older aged out of window
# start 84416401 and are not retried this pass (already told in the 14:28 or earlier
# patrol; 15:32 patrol also recorded the age-out). No in-window official 404.
IN_WINDOW = []
AGED = []
TICK_S = 4.211
'''
new = '''# First pass at game.time=84417537; published_bases 84416800..84417400,
# reconstructed 84416801..84417500 (700). inserted=100, already_in_db=27206,
# ts_realigned_first_pass=10444 (first-interval tick_s script printed 4.049, exact 4.04902).
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# 16:00 half-hour already official-filled through 84417100 / just-published 84417100;
# 15:30 half-hour official-filled through 84416700 / just-published 84416700;
# 15:32 patrol already official-filled through 84416500 / just-published 84416600.
# Already-told leftover official 404 W45N8@84415500 and older aged out of window
# start 84416801 and are not retried this pass (already told in the 14:28 or earlier
# patrol; 15:32 patrol also recorded the age-out). No in-window official 404.
IN_WINDOW = []
AGED = []
TICK_S = 4.049
'''
if old not in t:
    raise SystemExit("confirm header not found")
t = t.replace(old, new, 1)
p.write_text(t)
print("backfill_confirm.py updated")

# --- just_published ---
p = DIR / "backfill_just_published.py"
t = p.read_text()
t = t.replace("Fetch just-published official history base 84417100 once game.time is safely past 84417240.",
              "Fetch just-published official history base 84417500 once game.time is safely past 84417640.")
t = t.replace("JUST_BASE = 84417100", "JUST_BASE = 84417500")
p.write_text(t)
print("backfill_just_published.py updated, JUST_BASE now:")
for line in t.splitlines():
    if "JUST_BASE" in line or "WAIT_UNTIL" in line:
        print(" ", line)

# --- coverage ---
p = DIR / "coverage.py"
t = p.read_text()
old = '''TMIN, TMAX = 84416401, 84417100
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
DIR = "/workspace/screeps/state/_halfhour_2026-11-22_1630"
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84416400..84417000 at game.time=84417167; reconstructed 84416401..84417100 (700).
# 15:30 half-hour already official-filled through 84416700 / just-published 84416700.
# 15:32 patrol already official-filled through 84416500 / just-published 84416600.
# This first pass inserted=8086 already_in_db=18451, ts_realigned=1873.
# No in-window official 404. Already-told leftover W45N8@84415500 and older aged out
# of this window start 84416401 and were not retried. NEW short WS 16:02:42-16:02:55
# STATS 84417111..84417129 sits after this first-pass window (in unpublished 84417100).
# Do not restart the listener.
'''
new = '''TMIN, TMAX = 84416801, 84417500
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
DIR = "/workspace/screeps/state/_halfhour_2026-11-22_1630"
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84416800..84417400 at game.time=84417537; reconstructed 84416801..84417500 (700).
# 16:00 half-hour already official-filled through 84417100 / just-published 84417100.
# 15:30 half-hour official-filled through 84416700 / just-published 84416700.
# 15:32 patrol already official-filled through 84416500 / just-published 84416600.
# This first pass inserted=100 already_in_db=27206, ts_realigned=10444.
# No in-window official 404. Already-told leftover W45N8@84415500 and older aged out
# of this window start 84416801 and were not retried. NEW box freeze 16:15:02-16:22:09
# STATS 84417291..84417409 sits inside this first-pass window.
# short WS 16:02:42-16:02:55 STATS 84417111..84417129 also in this window (already official-filled 19/19).
# Do not restart the listener.
'''
if old not in t:
    raise SystemExit("coverage header not found")
t = t.replace(old, new, 1)
p.write_text(t)
print("coverage.py updated")
print("done")
