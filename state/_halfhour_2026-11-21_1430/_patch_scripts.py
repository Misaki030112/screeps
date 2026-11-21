#!/usr/bin/env python3
from pathlib import Path
import shutil

src = Path("/workspace/screeps/state/_halfhour_2026-11-21_1400")
dst = Path("/workspace/screeps/state/_halfhour_2026-11-21_1430")

# --- tick_s_check ---
t = (src / "tick_s_check.py").read_text()
t = t.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
# Replace the constant block from W46 = through PREV_LATER_MEAN
start = t.find("W46 = {")
end = t.find("\ndef intervals")
if start < 0 or end < 0:
    raise SystemExit(f"tick_s constants not found {start} {end}")
block = '''W46 = {
    84394500: 1795239808169,
    84394600: 1795240222717,
    84394700: 1795240655231,
    84394800: 1795241078694,
    84394900: 1795241516543,
    84395000: 1795241952287,
    84395100: 1795242378966,
}
MIN_ALL = {
    84394500: 1795239808169,  # W46N8
    84394600: 1795240222717,  # W46N8
    84394700: 1795240655231,  # W46N8
    84394800: 1795241078694,  # W46N8
    84394900: 1795241516543,  # W46N8
    84395000: 1795241952287,  # W46N8
    84395100: 1795242375788,  # W45N7 (W47N8@84395100 first-pass 404)
}
TMIN, TMAX = 84394501, 84395200
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84394600] - MIN_ALL[84394500]) / 1000.0 / 100  # script printed 4.145, exact 4.14548
GT_FIRST = 84395263
TS_REALIGNED_FIRST = 20366  # first-pass realign moved 20366 (inserted=500, already_in_db=27169, missing_chunks=1)
PREV_LATER_MEAN = 4.26294  # 14:00 half-hour tick_s_in_use (span_mean)

'''
t = t[:start] + block + t[end:]
# comments above W46
# leave the stale 15:xx comments; they are historical in the file. Update printed tick_s strings later in file.
t = t.replace("(printed 4.278)", "(printed 4.145)")
t = t.replace("(printed 4.206, min-all-rooms first two bases)", "(printed 4.145, min-all-rooms first two bases)")
t = t.replace(
    "(ts_realigned_first={TS_REALIGNED_FIRST}, inserted=3305, already_in_db=21922, missing_chunks=0).",
    "(ts_realigned_first={TS_REALIGNED_FIRST}, inserted=500, already_in_db=27169, missing_chunks=1).",
)
(dst / "tick_s_check.py").write_text(t)
print("tick_s_check patched")

# --- backfill_confirm ---
c = (src / "backfill_confirm.py").read_text()
c = c.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
# replace IN_WINDOW / AGED / TICK_S
# Find IN_WINDOW line
import re
c2, n = re.subn(
    r"IN_WINDOW = \[.*?\]\s*#.*",
    'IN_WINDOW = [("W47N8", 84395100)]  # first pass 34/35 official GETs 200, missing_chunks=1 W47N8@84395100. In-window first-pass official 404: W47N8@84395100 (not yet told; retried here). Already-told leftover official 404 W46N8@84394300 (told by the delivered 13:32 1h patrol t508s3575; listener 79/100 84394301..84394379, hole 21 ticks 84394380..84394400) ages out of window start 84394501 and is not retried here. Already-told leftover official 404s W45N8@84392600, W46N8@84390800, W47N7@84390900, W46N8@84390400, W45N7@84388500, W45N8@84386600 and older also age out of window start 84394501 and are not retried here.',
    c,
    count=1,
    flags=re.S,
)
if n != 1:
    # IN_WINDOW is a single line; try non-dotall to first newline only by doing a tighter replace
    start = c.find("IN_WINDOW = ")
    if start < 0:
        raise SystemExit("IN_WINDOW not found")
    end = c.find("\nAGED = ")
    if end < 0:
        end = c.find("\nTICK_S = ")
    if end < 0:
        raise SystemExit("AGED/TICK_S not found after IN_WINDOW")
    new_in = 'IN_WINDOW = [("W47N8", 84395100)]  # first pass 34/35 official GETs 200, missing_chunks=1 W47N8@84395100. In-window first-pass official 404: W47N8@84395100 (not yet told; retried here). Already-told leftover official 404 W46N8@84394300 (told by the delivered 13:32 1h patrol t508s3575) ages out of window start 84394501 and is not retried here. Already-told leftover official 404s W45N8@84392600, W46N8@84390800, W47N7@84390900, W46N8@84390400, W45N7@84388500, W45N8@84386600 and older also age out of window start 84394501 and are not retried here.\n'
    c = c[:start] + new_in + c[end+1:]  # keep AGED line
else:
    c = c2
c = c.replace("TICK_S = 4.27826", "TICK_S = 4.14548")
(dst / "backfill_confirm.py").write_text(c)
# verify
cc = c
assert "_halfhour_2026-11-21_1430" in cc and "_halfhour_2026-11-21_1400" not in cc
assert 'IN_WINDOW = [("W47N8", 84395100)]' in cc
print("backfill_confirm patched; IN_WINDOW ok")

# --- coverage ---
cov = (src / "coverage.py").read_text()
cov = cov.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
cov = cov.replace("TMIN, TMAX = 84394101, 84394800", "TMIN, TMAX = 84394501, 84395200")
start = cov.find("IN_WINDOW_404 = ")
end = cov.find("\nOUT = ")
if start < 0 or end < 0:
    raise SystemExit(f"coverage IN_WINDOW_404 not found {start} {end}")
cov = cov[:start] + 'IN_WINDOW_404 = {("W47N8", 84395100)}  # first pass 34/35 official GETs 200, missing_chunks=1 W47N8@84395100. Already-told leftover official 404 W46N8@84394300 ages out of window start 84394501 and is not retried here.\n' + cov[end+1:]
(dst / "coverage.py").write_text(cov)
assert "84394501, 84395200" in cov
print("coverage patched")

# --- just_published ---
jp = (src / "backfill_just_published.py").read_text()
jp = jp.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
jp = jp.replace("JUST_BASE = 84394800", "JUST_BASE = 84395200")
jp = jp.replace("base 84394800 once game.time is safely past 84394940", "base 84395200 once game.time is safely past 84395340")
(dst / "backfill_just_published.py").write_text(jp)
assert "84395200" in jp and "1400" not in jp
print("just_published patched")

# --- post_counts (GAPS will be rewritten precisely) ---
pc = (src / "post_counts.py").read_text()
pc = pc.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
pc = pc.replace("JUST_BASE = 84394800", "JUST_BASE = 84395200")
pc = pc.replace("WIN_TMIN, WIN_TMAX = 84394101, 84394800", "WIN_TMIN, WIN_TMAX = 84394501, 84395200")
gstart = pc.find("GAPS = [")
gend = pc.find("]\nHK = ")
if gstart < 0 or gend < 0:
    # try without escaped
    raise SystemExit(f"GAPS markers {gstart} {gend}")
gaps = '''GAPS = [
    ("gap_1415_1423", 84395061, 84395179),  # NEW this run, not yet told (box freeze 14:15:50-14:23:29, 450s); 119t; last_stats 84395060 at 14:15:39, next 84395180 at 14:24:16; listener auto-restart 14:23:32, python 1910963 started 14:23:42; official window start 84394501 covers the whole 119t (chunks 84395000 and 84395100). Concurrent 1h patrol _patrol_2026-11-21_1423 is running; do not write its folder.
    ("gap_1349_1356", 84394681, 84394809),  # recorded not-yet-told by the 14:00 half-hour backfill (box freeze 13:49:01-13:56:56, 475s); 129t; official-filled all five 129/129; still in official window start 84394501. Keep as not-yet-told unless the concurrent 14:23 patrol has already delivered it.
    ("gap_1309_1321", 84394131, 84394299),  # already told by the delivered 13:32 1h patrol t508s3575 (box freeze 13:09:46-13:21:14, 680s); 169t; official-filled all five 169/169; ages out of official window start 84394501.
    ("gap_1248_1257", 84393831, 84393969),  # already told by the delivered 13:32 1h patrol t508s3575 (box freeze 12:48:14-12:57:17, 534s); 139t; official-filled all five 139/139; ages out of official window start 84394501.
    ("gap_1230_1235", 84393581, 84393659),  # already told by the delivered 13:32 1h patrol t508s3575 (box freeze 12:30:42-12:35:35, 283s); 79t; official-filled all five 79/79; ages out of official window start 84394501.
    ("gap_1218", 84393391, 84393419),  # already told by the 12:26/13:32 1h patrols (short listener WS ping/pong 12:18:13, restart 12:18:17; not a box freeze); 29t; ages out of official window start 84394501
    ("gap_1210", 84393291, 84393319),  # already told by the 12:26/13:32 1h patrols (short listener WS ping/pong 12:10:56, restart 12:10:59; not a box freeze); 29t; ages out of official window start 84394501
    ("gap_1149_1157", 84393001, 84393129),  # already told by the 12:26/13:32 1h patrols (box freeze 11:49:12-11:57:31, 494s); 129t; official-filled all five 129/129; ages out of window start 84394501
    ("gap_1119_1120", 84392571, 84392609),  # already told by the 11:28/13:32 1h patrols (box freeze 11:19:06-11:20:43, 88s); leftover official 404 W45N8@84392600 already told; ages out of window start 84394501
    ("gap_1111_1113", 84392471, 84392499),  # already told by the 12:26/13:32 1h patrols (short listener WS ping/pong 11:12:51-11:12:54, not a box freeze); official-filled all five 29/29; ages out of window start 84394501
]
'''
# find HK after GAPS closing
idx_hk = pc.find("HK = ZoneInfo", gstart)
if idx_hk < 0:
    raise SystemExit("HK after GAPS not found")
pc = pc[:gstart] + gaps + pc[idx_hk:]
(dst / "post_counts.py").write_text(pc)
print("post_counts patched")

# late retry template copy; constants updated later if needed
if (src / "backfill_late_retry.py").exists():
    lr = (src / "backfill_late_retry.py").read_text()
    lr = lr.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
    lr = lr.replace("84394300", "84395100")
    lr = lr.replace("W46N8", "W47N8")
    (dst / "backfill_late_retry.py").write_text(lr)
    print("late_retry copied (W47N8@84395100)")

print("all scripts ready")
