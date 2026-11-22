#!/usr/bin/env python3
from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-22_2030")

# --- coverage.py ---
p = DIR / "coverage.py"
t = p.read_text()
t = t.replace("TMIN, TMAX = 84419801, 84420500", "TMIN, TMAX = 84420301, 84421000")
old = '''# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84419800..84420400 at game.time=84420573; reconstructed 84419801..84420500 (700).
# 19:30 half-hour already official-filled through 84419900 / just-published 84420000.
# This first pass inserted=12774 already_in_db=12826, ts_realigned=368,
# tick_s printed 4.202 (exact 4.20156); tick_s_in_use=4.18009 later_raw (live-anchor-best, over45=0).
# No in-window official 404. Leftover W45N7@84419300 and W45N8@84419600 sit
# before window start 84419801 (84419600 near; retried in confirm, not in this
# coverage window). Already-told leftover all five @84418900 and W45N7@84419000
# aged out, not retried. NEW box freeze 19:43:54-19:59:40 STATS 84420281..84420519
# (tail 84420501..84420519 is just past this official window; JP 84420500 covers 84420501..84420600).
# Do not restart the listener. Do not write a patrol folder.'''
new = '''# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84420300..84420900 at game.time=84421046; reconstructed 84420301..84421000 (700).
# 20:11 half-hour official-filled 84419801..84420500; 20:27 patrol official+JP through 84420800.
# This first pass inserted=5152 already_in_db=21610, ts_realigned=0,
# tick_s printed 4.221 (exact first-interval 4.22106).
# No in-window official 404. Leftover W45N7@84419300 and W45N8@84419600 aged
# out of window start 84420301 (7+ bases before), not retried this pass.
# Already-told freeze 19:43:54-19:59:40 is before/overlap early window, already filled.
# Do not restart the listener. Do not write a patrol folder.'''
if old not in t:
    raise SystemExit("coverage comment block not found")
t = t.replace(old, new, 1)
p.write_text(t)
print("coverage.py updated")

# --- tick_s_check.py ---
p = DIR / "tick_s_check.py"
t = p.read_text()
old = '''W46 = {
    84419800: 1795346245163,
    84419900: 1795346667898,
    84420000: 1795347081431,
    84420100: 1795347504993,
    84420200: 1795347933570,
    84420300: 1795348335839,
    84420400: 1795348757945,
}
MIN_ALL = {
    84419800: 1795346245163,  # W46N8
    84419900: 1795346665319,  # W45N7
    84420000: 1795347081431,  # W46N8
    84420100: 1795347504993,  # W46N8
    84420200: 1795347933570,  # W46N8
    84420300: 1795348335839,  # W46N8
    84420400: 1795348757945,  # W46N8
}
TMIN, TMAX = 84419801, 84420500
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84419900] - MIN_ALL[84419800]) / 1000.0 / 100  # script printed 4.202, exact 4.20156
GT_FIRST = 84420573
TS_REALIGNED_FIRST = 368  # first-pass realign moved 368 rows (inserted=12774 already_in_db=12826)
PREV_LATER_MEAN = 4.08344  # tick_s_in_use from quiet 19:30 halfhour (first)'''
new = '''W46 = {
    84420300: 1795348335839,
    84420400: 1795348757945,
    84420500: 1795349168939,
    84420600: 1795349588416,
    84420700: 1795350016945,
    84420800: 1795350432266,
    84420900: 1795350846567,
}
MIN_ALL = {
    84420300: 1795348335839,  # W46N8
    84420400: 1795348757945,  # W46N8
    84420500: 1795349168939,  # W46N8
    84420600: 1795349588416,  # W46N8
    84420700: 1795350016945,  # W46N8
    84420800: 1795350430749,  # W45N7
    84420900: 1795350846567,  # W46N8
}
TMIN, TMAX = 84420301, 84421000
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84420400] - MIN_ALL[84420300]) / 1000.0 / 100  # script printed 4.221, exact 4.22106
GT_FIRST = 84421046
TS_REALIGNED_FIRST = 0  # first-pass realign moved 0 rows (inserted=5152 already_in_db=21610)
PREV_LATER_MEAN = 4.18009  # tick_s_in_use from quiet 20:11 halfhour'''
if old not in t:
    raise SystemExit("tick_s constants block not found")
t = t.replace(old, new, 1)

# comment header
old = '''# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0; insert committed
# inserted=12774 already_in_db=12826; first-pass realign ts_realigned_first=368
# with printed tick_s=4.202 (exact first-interval 4.20156). No concurrent
# first-pass of this window (last half-hour 1930 official-filled through
# 84419900 / just-published 84420000; overlap already_in_db=12826).
# published_bases 84419800..84420400 at game.time=84420573;
# reconstructed 84419801..84420500 (700). No in-window official 404.
# Leftover W45N7@84419300 and W45N8@84419600 are before window start 84419801
# (84419600 is near; retry this overlap). Already-told leftover official 404
# all five @84418900 and W45N7@84419000 aged out, not retried.
# Listener 2641627 started 19:59:53 (parent 4035476) after NEW box freeze
# 19:43:54-19:59:40. Do not restart the listener or war_cmd/pulse.
# Single-slot 5:5:1:1. Do not write a patrol folder.'''
new = '''# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0; insert committed
# inserted=5152 already_in_db=21610; first-pass realign ts_realigned_first=0
# with printed tick_s=4.221 (exact first-interval 4.22106). Overlap with
# 20:11 half-hour (through 84420500) and 20:27 patrol (through 84420800).
# published_bases 84420300..84420900 at game.time=84421046;
# reconstructed 84420301..84421000 (700). No in-window official 404.
# Leftover W45N7@84419300 and W45N8@84419600 aged out of window start 84420301,
# not retried. Listener 2641627 started 19:59:53 (parent 4035476).
# Do not restart the listener or war_cmd/pulse.
# Single-slot 5:5:1:1. Do not write a patrol folder.'''
if old not in t:
    raise SystemExit("tick_s comment block not found")
t = t.replace(old, new, 1)

t = t.replace(
    'f"First-pass realign with tick_s={TICK_S_FIRST:.5f} (printed 4.202) succeeded, "\n'
    '        f"ts_realigned_first={TS_REALIGNED_FIRST} (inserted=12774 already_in_db=12826, missing_chunks=0)."',
    'f"First-pass realign with tick_s={TICK_S_FIRST:.5f} (printed 4.221) succeeded, "\n'
    '        f"ts_realigned_first={TS_REALIGNED_FIRST} (inserted=5152 already_in_db=21610, missing_chunks=0)."',
)
# the above replace may fail because of how I escaped; do a simpler replace
t = t.replace("(printed 4.202) succeeded", "(printed 4.221) succeeded")
t = t.replace("(inserted=12774 already_in_db=12826, missing_chunks=0).", "(inserted=5152 already_in_db=21610, missing_chunks=0).")
t = t.replace("(printed 4.202, min-all-rooms first two bases)", "(printed 4.221, min-all-rooms first two bases)")
p.write_text(t)
print("tick_s_check.py updated")

# --- confirm.py ---
p = DIR / "backfill_confirm.py"
t = p.read_text()
old = '''# First pass at game.time=84420573; published_bases 84419800..84420400,
# reconstructed 84419801..84420500 (700). inserted=12774, already_in_db=12826,
# ts_realigned_first_pass=368; first-interval tick_s script printed 4.202, exact 4.20156.
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check (4.18009 later_raw).
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# 19:30 half-hour already official-filled through 84419900 / just-published 84420000.
# Leftover official 404 all five @84418900 and W45N7@84419000 aged out of
# window start 84419801 and are not retried this pass.
# Near-window leftover official 404 (already told in 19:36 patrol; retry this overlap):
# W45N7@84419300 (aged slightly before) and W45N8@84419600 (near, 2 bases before).
# No new in-window first-pass 404s.
IN_WINDOW = [
    ("W45N7", 84419300),
    ("W45N8", 84419600),
]
AGED = []
TICK_S = 4.18009'''
new = '''# First pass at game.time=84421046; published_bases 84420300..84420900,
# reconstructed 84420301..84421000 (700). inserted=5152, already_in_db=21610,
# ts_realigned_first_pass=0; first-interval tick_s script printed 4.221, exact 4.22106.
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# 20:11 half-hour official-filled through 84420500; 20:27 patrol through 84420800.
# Leftover official 404 W45N7@84419300 and W45N8@84419600 aged out of
# window start 84420301 (already retried still 404 last overlap) and are not retried.
# No new in-window first-pass 404s.
IN_WINDOW = []
AGED = []
TICK_S = 4.22106'''
if old not in t:
    raise SystemExit("confirm header not found")
t = t.replace(old, new, 1)
p.write_text(t)
print("backfill_confirm.py updated")

# --- late_retry ---
p = DIR / "backfill_late_retry.py"
t = p.read_text()
old = '''TARGETS = [
    ("W45N7", 84419300),
    ("W45N8", 84419600),
]  # near-window leftovers already told in 19:36 patrol; W45N7@84419000 and all five @84418900 aged out of window start 84419801'''
new = '''TARGETS = []  # no in-window 404; leftovers W45N7@84419300 and W45N8@84419600 aged out of window start 84420301'''
if old not in t:
    raise SystemExit("late_retry TARGETS not found")
t = t.replace(old, new, 1)
p.write_text(t)
print("backfill_late_retry.py updated")

# --- postjp ---
p = DIR / "backfill_postjp_retry.py"
t = p.read_text()
old = 'TARGETS = [("W45N7", 84419300), ("W45N8", 84419600)]'
new = 'TARGETS = []  # no leftover in/near this window'
if old not in t:
    raise SystemExit("postjp TARGETS not found")
t = t.replace(old, new, 1)
p.write_text(t)
print("backfill_postjp_retry.py updated")

# --- just published scripts ---
for name in ("backfill_just_published.py", "backfill_just_published_retry.py", "backfill_just_published_retry2.py"):
    p = DIR / name
    t = p.read_text()
    n = t.count("84420500")
    t = t.replace("84420500", "84421000")
    p.write_text(t)
    print(f"{name} replaced 84420500 -> 84421000 ({n} times)")

print("all script updates done")
