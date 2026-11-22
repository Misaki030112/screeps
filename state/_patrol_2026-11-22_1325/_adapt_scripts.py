#!/usr/bin/env python3
from pathlib import Path

DIR = Path("/workspace/screeps/state/_patrol_2026-11-22_1022")
OLD = "_patrol_2026-11-22_0918"
NEW = "_patrol_2026-11-22_1022"

# --- tick_s_check.py ---
p = DIR / "tick_s_check.py"
text = p.read_text()
text = text.replace(
    'DIR = ROOT / "state" / "_patrol_2026-11-22_0918"',
    'DIR = ROOT / "state" / "_patrol_2026-11-22_1022"',
)
start = text.index("# Official chunk timestamps printed by history_backfill.py")
end = text.index("def intervals(d):")
new_block = '''# Official chunk timestamps printed by history_backfill.py
# First pass 34 of 35 official GETs 200, missing_chunks=1 W45N7@84411500.
# published_bases 84411500..84412100 at game.time=84412236; reconstructed 84411501..84412200 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84411600-84411500)/1000/100 = 4.01041, script printed 4.010.
# Insert committed inserted=5999 already_in_db=18882, first-pass realign ts_realigned=15398.
# 10:11 half-hour already wrote through 84411800 / just-published 84411900 for all 5
# except leftover W45N7@84411500 (listener 29/100 84411524..84411552).
# Last 1h patrol delivered 09:29 _patrol_2026-11-22_0918. Concurrent none.
# Do not restart the listener or war_cmd/pulse. Single listener 2394456 since 10:22:36
# after NEW box freeze 10:16:39-10:22:23 (338s) and earlier 09:41:41-09:59:05 (1037s).
# In-window official 404: W45N7@84411500 (leftover from 10:11, still to retry).
# Already-told leftovers W47N8@84409800 and older aged out of window start 84411501
# and are not retried this pass. Unpublished tail after 84412200 waits on just-published 84412200.
W46 = {
    84411500: 1795311638059,
    84411600: 1795312040124,
    84411700: 1795312461565,
    84411800: 1795312862803,
    84411900: 1795313271439,
    84412000: 1795313693159,
    84412100: 1795314102770,
}
MIN_ALL = {
    84411500: 1795311638059,  # W46N8 (W45N7 404)
    84411600: 1795312039100,  # W45N7
    84411700: 1795312458589,  # W45N7
    84411800: 1795312862803,  # W46N8
    84411900: 1795313271439,  # W46N8
    84412000: 1795313693159,  # W46N8
    84412100: 1795314102770,  # W46N8
}
TMIN, TMAX = 84411501, 84412200
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84411600] - MIN_ALL[84411500]) / 1000.0 / 100  # script printed 4.010, exact 4.01041
GT_FIRST = 84412236
TS_REALIGNED_FIRST = 15398
PREV_LATER_MEAN = 4.112353333333333  # tick_s_in_use from quiet 10:11 halfhour


'''
text = text[:start] + new_block + text[end:]
# leftover printed-tick_s string if any from 0918
text = text.replace("printed 4.017", "printed 4.010")
p.write_text(text)
print("patched tick_s_check.py")
print("TICK_S_FIRST", (1795312039100-1795311638059)/1000/100)

# --- backfill_confirm.py ---
p = DIR / "backfill_confirm.py"
text = p.read_text()
start = text.index("# First pass at game.time=")
end = text.index("def load_tick_s():")
new_block = '''# First pass at game.time=84412236; published_bases 84411500..84412100,
# reconstructed 84411501..84412200 (700). inserted=5999, already_in_db=18882,
# ts_realigned_first_pass=15398 (first-interval tick_s=4.01041 script printed 4.010).
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 34 of 35 official GETs 200, missing_chunks=1 W45N7@84411500.
# Leftover official 404s W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900
# / W45N8@84407700 / W46N8@84407000 and older aged out of this window start 84411501
# and are not retried.
# 10:11 half-hour official already through 84411800 / just-published 84411900,
# with leftover W45N7@84411500 still 404 after confirm/retry2/late retry.
# NEW box freeze 10:16:39-10:22:23 and earlier 09:41:41-09:59:05 sit inside/near this window.
IN_WINDOW = [("W45N7", 84411500)]
AGED = []
TICK_S = 4.010
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUT = "/workspace/screeps/state/_patrol_2026-11-22_1022/backfill_confirm_gets.json"
TICK_S_FILE = "/workspace/screeps/state/_patrol_2026-11-22_1022/tick_s_realign.json"

'''
text = text[:start] + new_block + text[end:]
p.write_text(text)
print("patched backfill_confirm.py")

# --- just_published ---
p = DIR / "backfill_just_published.py"
text = p.read_text()
n1 = text.count(OLD)
text = text.replace(OLD, NEW)
n2 = text.count("JUST_BASE = 84411300")
text = text.replace("JUST_BASE = 84411300", "JUST_BASE = 84412200")
# docstring
text = text.replace("base 84411000 once game.time is safely past 84411140",
                    "base 84412200 once game.time is safely past 84412340")
p.write_text(text)
print("patched just_published", "dir", n1, "just_base", n2)

# --- late_retry ---
p = DIR / "backfill_late_retry.py"
text = p.read_text()
n = text.count(OLD)
text = text.replace(OLD, NEW)
# set leftover target if still 404 after confirm/retry2
text = text.replace(
    "TARGETS = []  # first pass 35/35 200; leftovers aged out of window start 84410301",
    "TARGETS = [(\"W45N7\", 84411500)]  # leftover official 404 still in this window",
)
p.write_text(text)
print("patched late_retry", n)

# --- exact2h ---
p = DIR / "exact2h.py"
text = p.read_text()
old1 = "LAST_TIP = 84410480  # previous 1h patrol analysis tip (08:23:24 later live/room_stats 84410550 08:28:14)"
new1 = "LAST_TIP = 84411380  # previous 1h patrol analysis tip (09:24:53 later live/room_stats 84411420 09:27:39)"
old2 = "BF_LO, BF_HI = 84410601, 84411300  # first-pass official window this hour, missing_chunks=1 W47N7@84411200"
new2 = "BF_LO, BF_HI = 84411501, 84412200  # first-pass official window this hour, missing_chunks=1 W45N7@84411500"
assert old1 in text, "LAST_TIP not found"
assert old2 in text, "BF_LO not found"
text = text.replace(old1, new1).replace(old2, new2)
text = text.replace(
    "/workspace/screeps/state/_patrol_2026-11-22_0918/exact2h_copy.txt",
    "/workspace/screeps/state/_patrol_2026-11-22_1022/exact2h_copy.txt",
)
p.write_text(text)
print("patched exact2h.py")

# --- coverage ---
p = DIR / "coverage.py"
text = p.read_text()
text = text.replace("TMIN, TMAX = 84410301, 84411000", "TMIN, TMAX = 84411501, 84412200")
text = text.replace(
    'DIR = "/workspace/screeps/state/_halfhour_2026-11-22_0900"',
    'DIR = "/workspace/screeps/state/_patrol_2026-11-22_1022"',
)
text = text.replace("IN_WINDOW_404 = set()", 'IN_WINDOW_404 = {("W45N7", 84411500)}')
p.write_text(text)
print("patched coverage.py")

# --- q scripts DIR ---
for name in ("q_live1.py", "q_live2.py", "q_live3.py", "q_extra.py", "q_later.py", "q_threat.py"):
    p = DIR / name
    text = p.read_text()
    n = text.count(OLD)
    text = text.replace(OLD, NEW)
    p.write_text(text)
    print("patched", name, "dir", n)

# --- q_threat windows ---
p = DIR / "q_threat.py"
text = p.read_text()
text = text.replace("84410750 AND 84411380", "84411300 AND 84412500")
text = text.replace(
    "if tick in (84410840, 84410850, 84410860, 84410880, 84411039, 84411040, 84411200, 84411300): flag = True",
    "if tick in (84411380, 84411420, 84411621, 84411889, 84411900, 84412000, 84412100, 84412200): flag = True",
)
text = text.replace("since last tip 84410480", "since last tip 84411380")
text = text.replace("tick>=84410480", "tick>=84411380")
text = text.replace("tick BETWEEN 84410800 AND 84411350", "tick BETWEEN 84411380 AND 84412500")
text = text.replace("tick BETWEEN 84410700 AND 84411350", "tick BETWEEN 84411380 AND 84412500")
# freeze STATS labels will be adapted in freeze_clock; keep query flexible by rewriting the list if present
old_freezes = '''for label, fr, to in [
    ("freeze1 08:51-09:01", "2026-11-22 08:51:14", "2026-11-22 09:01:02"),
    ("freeze2 09:14-09:19", "2026-11-22 09:14:15", "2026-11-22 09:19:05"),
]:'''
new_freezes = '''for label, fr, to in [
    ("freeze 09:41-09:59", "2026-11-22 09:41:41", "2026-11-22 09:59:05"),
    ("freeze 10:16-10:22", "2026-11-22 10:16:39", "2026-11-22 10:22:23"),
]:'''
if old_freezes in text:
    text = text.replace(old_freezes, new_freezes)
    print("patched q_threat freeze windows")
else:
    print("WARN q_threat freeze list not found exactly")
p.write_text(text)

# --- freeze_clock ---
p = DIR / "freeze_clock.py"
text = p.read_text()
text = text.replace(
    '"""Console silences and listener restarts since last patrol (~08:18 / delivered 08:28)."""',
    '"""Console silences and listener restarts since last patrol (~09:18 / delivered 09:29)."""',
)
# replace comments and CUT
start = text.index("HK = ZoneInfo")
end = text.index("console = Path")
new_block = '''HK = ZoneInfo("Asia/Hong_Kong")
# last 1h patrol already told freezes through 09:14:15-09:19:05 and 08:51:14-09:01:02
# and older 07:44:22-08:02:42 / 07:20:32-07:26:28 / 06:50:03-07:02:08 and earlier,
# plus already-told 监听短中断 05:25:19-05:27:20.
# NOT YET TOLD from 10:11 backfill: 09:41:41-09:59:05 (1037s) and leftover 404 W45N7@84411500.
# Watch for any newer freezes or short WS after 09:59:05 (and after last patrol 09:29).
# Already saw box_pauses 10:16:39-10:22:23 (338s) and listener restart 10:22:26 / python 2394456 10:22:36.
CUT = datetime(2026, 11, 22, 9, 29, 0, tzinfo=HK)
'''
text = text[:start] + new_block + text[end:]
text = text.replace("box_pauses after 08:28", "box_pauses after 09:29")
text = text.replace('fr >= "2026-11-22 08:28:00"', 'fr >= "2026-11-22 09:29:00"')
text = text.replace("listener restarts after 08:28", "listener restarts after 09:29")
text = text.replace('m.group(1) >= "2026-11-22 08:28:00"', 'm.group(1) >= "2026-11-22 09:29:00"')
text = text.replace("console lines after 08:10", "console lines after 09:10")
text = text.replace("datetime(2026, 11, 22, 8, 10, tzinfo=HK)", "datetime(2026, 11, 22, 9, 10, tzinfo=HK)")
text = text.replace("console silences >=60s after 08:28", "console silences >=60s after 09:29")
text = text.replace("short console gaps 3-59s after 08:28", "short console gaps 3-59s after 09:29")
p.write_text(text)
print("patched freeze_clock.py")

print("ALL ADAPT DONE")
