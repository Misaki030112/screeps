from pathlib import Path

DST = Path("/workspace/screeps/state/_halfhour_2026-11-22_0900")
OLD, NEW = "_halfhour_2026-11-22_0830", "_halfhour_2026-11-22_0900"

# ---- tick_s_check.py ----
p = DST / "tick_s_check.py"
t = p.read_text()
t = t.replace(OLD, NEW)

start = t.index("# Official chunk timestamps printed by history_backfill.py")
end = t.index("def intervals(d):")
new_block = '''# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0, exit=0.
# published_bases 84410300..84410900 at game.time=84411068; reconstructed 84410301..84411000 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84410400-84410300)/1000/100 = 4.10147, script printed 4.101.
# Insert committed inserted=9250 already_in_db=15658, first-pass realign succeeded
# ts_realigned=23.
# 08:30 half-hour already wrote through 84410600 / just-published 84410600 for all 5.
# 1h patrol already delivered 08:28 _patrol_2026-11-22_0818. Concurrent none.
# Do not restart the listener or war_cmd/pulse. Single listener 2364487 since 09:01:15
# after NEW box freeze 08:51:14-09:01:02 (581s; STATS 84410881..84411039, 159t;
# listener auto-restart 09:01:06). Leftover official 404 W47N8@84409800 and older
# aged out of window start 84410301 and are not retried this pass. Unpublished tail
# after 84411000 waits on just-published 84411000.
W46 = {
    84410300: 1795306701333,
    84410400: 1795307111480,
    84410500: 1795307542103,
    84410600: 1795307946021,
    84410700: 1795308347692,
    84410800: 1795308755249,
    84410900: 1795309161287,
}
MIN_ALL = {
    84410300: 1795306701333,  # W46N8
    84410400: 1795307111480,  # W46N8
    84410500: 1795307541399,  # W45N7 (earlier than W46N8 1795307542103)
    84410600: 1795307946021,  # W46N8
    84410700: 1795308347692,  # W46N8
    84410800: 1795308755249,  # W46N8
    84410900: 1795309161287,  # W46N8
}
TMIN, TMAX = 84410301, 84411000
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84410400] - MIN_ALL[84410300]) / 1000.0 / 100  # script printed 4.101, exact 4.10147
GT_FIRST = 84411068
TS_REALIGNED_FIRST = 23  # first-pass realign succeeded
PREV_LATER_MEAN = 4.11553  # tick_s_in_use from quiet 08:30 halfhour


'''
t = t[:start] + new_block + t[end:]

new_err = '''    first_pass_realign_error = (
        f"First-pass realign with tick_s={TICK_S_FIRST:.5f} (printed 4.101) succeeded "
        f"ts_realigned_first=23 (inserted=9250 already_in_db=15658, missing_chunks=0)."
    )
'''
i = t.find("    first_pass_realign_error = (")
if i < 0:
    raise SystemExit("first_pass_realign_error not found")
j = t.find("    reason = (", i)
t = t[:i] + new_err + t[j:]
t = t.replace("printed 3.997", "printed 4.101")
p.write_text(t)
print("tick_s_check.py adapted")

# ---- confirm.py ----
p = DST / "backfill_confirm.py"
t = p.read_text()
t = t.replace(OLD, NEW)
t = t.replace("_halfhour_2026-11-22_0730", NEW)
start = t.index("ROOMS = ")
end = t.index("def load_tick_s():")
t = t[:start] + '''ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# First pass at game.time=84411068; published_bases 84410300..84410900,
# reconstructed 84410301..84411000 (700). inserted=9250, already_in_db=15658, reconstructed=24908,
# ts_realigned_first_pass=23 (first-interval tick_s=4.10147 script printed 4.101; realign succeeded).
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 35 of 35 official GETs 200, missing_chunks=0. No in-window official 404s to confirm.
# Leftover official 404s W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900
# and older aged out of this window start 84410301 and are not retried.
# 08:30 half-hour official already through 84410500 / just-published 84410600.
# NEW box freeze 08:51:14-09:01:02 STATS 84410881..84411039 sits partly inside this window
# (official-200 chunks 84410800 and 84410900 cover 84410881..84411000; unpublished tail
# 84411001..84411039 waits on just-published 84411000).
IN_WINDOW = []
AGED = []
TICK_S = 4.101
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUT = "/workspace/screeps/state/_halfhour_2026-11-22_0900/backfill_confirm_gets.json"
TICK_S_FILE = "/workspace/screeps/state/_halfhour_2026-11-22_0900/tick_s_realign.json"

''' + t[end:]
p.write_text(t)
print("backfill_confirm.py adapted")

# ---- just_published.py ----
p = DST / "backfill_just_published.py"
t = p.read_text()
t = t.replace(OLD, NEW)
t = t.replace("84410600", "84411000")
p.write_text(t)
print("just_published.py adapted")
for line in t.splitlines():
    if any(s in line for s in ("JUST_BASE", "WAIT_UNTIL", "DIR =", "84411000", "84411140", "sys.path")):
        print(" ", line)

# ---- late_retry.py ----
p = DST / "backfill_late_retry.py"
t = p.read_text()
t = t.replace(OLD, NEW)
lines = t.splitlines()
found = False
for i, ln in enumerate(lines):
    if ln.startswith("TARGETS ="):
        lines[i] = "TARGETS = []  # first pass 35/35 200; leftovers aged out of window start 84410301"
        found = True
        break
if not found:
    raise SystemExit("TARGETS not found in late_retry")
p.write_text("\n".join(lines) + "\n")
print("late_retry.py adapted")
for line in p.read_text().splitlines():
    if "TARGETS" in line or "DIR =" in line:
        print(" ", line)

# ---- coverage.py ----
p = DST / "coverage.py"
t = p.read_text()
t = t.replace(OLD, NEW)
t = t.replace("TMIN, TMAX = 84409901, 84410600", "TMIN, TMAX = 84410301, 84411000")
# keep IN_WINDOW_404 = set()
p.write_text(t)
print("coverage.py adapted")
for line in t.splitlines():
    if any(s in line for s in ("DIR", "IN_WINDOW", "TMIN", "TMAX")):
        print(" ", line)
