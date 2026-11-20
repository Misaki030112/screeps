from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1600")

# ---- tick_s_check.py ----
p = DIR / "tick_s_check.py"
s = p.read_text()
s = s.replace("_halfhour_2026-11-20_1530", "_halfhour_2026-11-20_1600")

old_comment_start = "# Official chunk timestamps printed by history_backfill.py"
idx = s.find(old_comment_start)
idx2 = s.find("W46 = {")
if idx < 0 or idx2 < 0:
    raise SystemExit("tick_s comment/W46 block not found")

new_header = '''# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84375400..84376000 at game.time=84376148; reconstructed 84375401..84376100 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84375500-84375400)/1000/100 = 4.14626, script printed 4.146. First-pass realign moved 0 (inserted=12174; already_in_db=10519).
# 15:30 half-hour already wrote through 84375700 / reconstructed through 84375600 and just-published 84375600 for all 5 (ticks 84375601..84375700 at 15:38:53 gt=84375741).
# No concurrent 1h patrol (last _patrol_2026-11-20_1526 finished ~15:29). This run must not restart the listener or war_cmd/pulse.
# NEW box freeze 15:44:21-16:03:39 (1152s; box_pauses.jsonl); listener auto-restart 16:03:42 (pid 1380270 started 16:03:51). STATS 84375811..84376109 (299t) last STATS 84375810 at 15:43:36 next STATS 84376110 at 16:04:19.
# Already-recorded untold freeze 15:15:12-15:26:38 STATS 84375391..84375569 and short gap 15:02:26 STATS 84374991..84375229 sit in/age around this window (told=false, left to 1h patrol).
# Official 404 leftover W45N8@84375300 (hole 84375301..84375400, told=false) ages out of this window start 84375401 and was not retried.
# MIN_ALL uses W45N7 on 84375500 (slightly earlier than W46N8); every other base uses W46N8 (earliest timestamp).
'''
s = s[:idx] + new_header + s[idx2:]

old_w46 = '''W46 = {
    84374900: 1795157262312,
    84375000: 1795157683714,
    84375100: 1795158104606,
    84375200: 1795158514875,
    84375300: 1795158939639,
    84375400: 1795159354860,
    84375500: 1795159769562,
}
MIN_ALL = {
    84374900: 1795157262312,  # W46N8
    84375000: 1795157683714,  # W46N8
    84375100: 1795158104606,  # W46N8
    84375200: 1795158514875,  # W46N8
    84375300: 1795158939639,  # W46N8
    84375400: 1795159354860,  # W46N8
    84375500: 1795159769486,  # W45N7
}
TMIN, TMAX = 84374901, 84375600
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84375000] - MIN_ALL[84374900]) / 1000.0 / 100  # script printed 4.214
GT_FIRST = 84375643
TS_REALIGNED_FIRST = 6594  # first-pass realign moved 6594 (inserted=3400, already_in_db=21481, missing_chunks=1)
PREV_LATER_MEAN = 4.15205  # 15:00 half-hour tick_s_in_use
'''
new_w46 = '''W46 = {
    84375400: 1795159354860,
    84375500: 1795159769562,
    84375600: 1795160195932,
    84375700: 1795160605757,
    84375800: 1795161023007,
    84375900: 1795161433003,
    84376000: 1795161849607,
}
MIN_ALL = {
    84375400: 1795159354860,  # W46N8
    84375500: 1795159769486,  # W45N7
    84375600: 1795160195932,  # W46N8
    84375700: 1795160605757,  # W46N8
    84375800: 1795161023007,  # W46N8
    84375900: 1795161433003,  # W46N8
    84376000: 1795161849607,  # W46N8
}
TMIN, TMAX = 84375401, 84376100
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84375500] - MIN_ALL[84375400]) / 1000.0 / 100  # script printed 4.146
GT_FIRST = 84376148
TS_REALIGNED_FIRST = 0  # first-pass realign moved 0 (inserted=12174, already_in_db=10519, missing_chunks=0)
PREV_LATER_MEAN = 4.178623333333333  # 15:30 half-hour tick_s_in_use (span_mean)
'''
if old_w46 not in s:
    raise SystemExit("W46 block not found after comment replace")
s = s.replace(old_w46, new_w46)

s = s.replace("printed 4.214", "printed 4.146")
s = s.replace("inserted=9753, already_in_db=15631, missing_chunks=0", "inserted=12174, already_in_db=10519, missing_chunks=0")
s = s.replace("inserted=3400, already_in_db=21481, missing_chunks=1", "inserted=12174, already_in_db=10519, missing_chunks=0")
p.write_text(s)
if "_halfhour_2026-11-20_1530" in s:
    raise SystemExit("tick_s_check still has 1530")
print("patched tick_s_check.py")

# ---- coverage.py ----
p = DIR / "coverage.py"
s = p.read_text()
s = s.replace("_halfhour_2026-11-20_1530", "_halfhour_2026-11-20_1600")
s = s.replace("TMIN, TMAX = 84374901, 84375600", "TMIN, TMAX = 84375401, 84376100")
# Replace IN_WINDOW_404 assignment
old = 'IN_WINDOW_404 = {("W45N8", 84375300)}  # first pass 34/35 200, missing_chunks=1'
new = "IN_WINDOW_404 = set()  # first pass 35/35 200, missing_chunks=0"
if old not in s:
    raise SystemExit("IN_WINDOW_404 not found")
s = s.replace(old, new)
p.write_text(s)
if "_halfhour_2026-11-20_1530" in s:
    raise SystemExit("coverage still has 1530")
print("patched coverage.py")

# ---- backfill_confirm.py ----
p = DIR / "backfill_confirm.py"
s = p.read_text()
s = s.replace("_halfhour_2026-11-20_1530", "_halfhour_2026-11-20_1600")
# Find and replace IN_WINDOW / AGED / TICK_S / TMIN if present
# The 1530 file has:
# IN_WINDOW = [("W45N8", 84375300)]  # first pass missing_chunks=1
# AGED = []
# TICK_S = 4.21402
if 'IN_WINDOW = [("W45N8", 84375300)]' not in s and "IN_WINDOW = [(" not in s:
    # show nearby
    for i, line in enumerate(s.splitlines(), 1):
        if "IN_WINDOW" in line or "TICK_S =" in line or "AGED" in line:
            print("confirm line", i, line)
s = s.replace('IN_WINDOW = [("W45N8", 84375300)]  # first pass missing_chunks=1', "IN_WINDOW = []  # first pass missing_chunks=0, no 404s to retry")
s = s.replace("TICK_S = 4.21402", "TICK_S = 4.14626")
p.write_text(s)
if "_halfhour_2026-11-20_1530" in s:
    raise SystemExit("confirm still has 1530")
print("patched backfill_confirm.py")

# ---- just_published.py ----
p = DIR / "backfill_just_published.py"
s = p.read_text()
s = s.replace("_halfhour_2026-11-20_1530", "_halfhour_2026-11-20_1600")
s = s.replace("JUST_BASE = 84375600", "JUST_BASE = 84376100")
s = s.replace("Fetch just-published official history base 84375600 once game.time is safely past 84375740.",
              "Fetch just-published official history base 84376100 once game.time is safely past 84376240.")
p.write_text(s)
if "_halfhour_2026-11-20_1530" in s or "84375600" in s:
    raise SystemExit(f"just_published still stale: 1530={'1530' in s} 84375600={'84375600' in s}")
print("patched backfill_just_published.py")
print("all patches ok")
