from pathlib import Path
import re

DST = Path("/workspace/screeps/state/_halfhour_2026-11-22_0830")

# ---- tick_s_check.py ----
p = DST / "tick_s_check.py"
t = p.read_text()
t = t.replace("_halfhour_2026-11-22_0800", "_halfhour_2026-11-22_0830")

start = t.index("# Official chunk timestamps printed by history_backfill.py")
end = t.index("def intervals(d):")
new_block = '''# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84409900..84410500 at game.time=84410669; reconstructed 84409901..84410600 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84410000-84409900)/1000/100 = 3.99694, script printed 3.997.
# Insert committed inserted=2813 already_in_db=24222, but first-pass realign then
# raised CheckViolation on _hyper_6_88_chunk constraint_88 (would-be ts
# 2026-11-22 08:00:02.731301+08 for W46N8 hauler84408751 tick 84410122) and the
# realign transaction rolled back, so ts_realigned_first=0.
# 08:00 half-hour already wrote through 84410200 / just-published 84410200 for all 5.
# Concurrent 12h review started ~08:22; do not write its folder. 1h patrol already
# delivered 08:28 _patrol_2026-11-22_0818 (told freeze 07:44:22-08:02:42 and leftover
# W47N8@84409800). Do not restart the listener or war_cmd/pulse. Single listener
# 2336374 since 08:02:54. Leftover official 404 W47N8@84409800 and older
# (W46N8@84408300 / W47N8@84408300 / W47N7@84407900 / ...) aged out of window
# start 84409901 and are not retried this pass. Unpublished tail after 84410600
# waits on just-published 84410600.
W46 = {
    84409900: 1795305072785,
    84410000: 1795305472479,
    84410100: 1795305894098,
    84410200: 1795306286160,
    84410300: 1795306701333,
    84410400: 1795307111480,
    84410500: 1795307542103,
}
MIN_ALL = {
    84409900: 1795305072785,  # W46N8
    84410000: 1795305472479,  # W46N8
    84410100: 1795305874542,  # W45N7 (earlier than W46N8 1795305894098)
    84410200: 1795306286160,  # W46N8
    84410300: 1795306701333,  # W46N8
    84410400: 1795307111480,  # W46N8
    84410500: 1795307541399,  # W45N7 (earlier than W46N8 1795307542103)
}
TMIN, TMAX = 84409901, 84410600
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84410000] - MIN_ALL[84409900]) / 1000.0 / 100  # script printed 3.997, exact 3.99694
GT_FIRST = 84410669
TS_REALIGNED_FIRST = 0  # first-pass realign failed CheckViolation; insert already committed
PREV_LATER_MEAN = 4.1147  # tick_s_in_use from quiet 08:00 halfhour


'''
t = t[:start] + new_block + t[end:]

new_err = '''    first_pass_realign_error = (
        f"First-pass realign with tick_s={TICK_S_FIRST:.5f} (printed 3.997) FAILED "
        f"CheckViolation on _hyper_6_88_chunk constraint_88 (would-be ts 2026-11-22 "
        f"08:00:02.731301+08 for W46N8 hauler84408751 tick 84410122); realign transaction "
        f"rolled back so ts_realigned_first=0 (inserted=2813 already committed, "
        f"already_in_db=24222, missing_chunks=0)."
    )
'''
i = t.find("    first_pass_realign_error = (")
if i < 0:
    raise SystemExit("first_pass_realign_error not found")
j = t.find("    reason = (", i)
t = t[:i] + new_err + t[j:]
t = t.replace("printed 3.959", "printed 3.997")
p.write_text(t)
print("tick_s_check.py adapted")

# ---- confirm.py ----
p = DST / "backfill_confirm.py"
t = p.read_text()
t = t.replace("_halfhour_2026-11-22_0730", "_halfhour_2026-11-22_0830")
t = t.replace("_halfhour_2026-11-22_0800", "_halfhour_2026-11-22_0830")
start = t.index("ROOMS = ")
end = t.index("def load_tick_s():")
t = t[:start] + '''ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# First pass at game.time=84410669; published_bases 84409900..84410500,
# reconstructed 84409901..84410600 (700). inserted=2813, already_in_db=24222, reconstructed=27035,
# ts_realigned_first_pass=0 (first-interval tick_s=3.99694 script printed 3.997;
# realign failed CheckViolation and rolled back).
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 35 of 35 official GETs 200, missing_chunks=0. No in-window official 404s to confirm.
# Leftover official 404s W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900
# and older aged out of this window start 84409901 and are not retried.
# 08:00 half-hour official already through 84410200 / just-published 84410200.
# Already-told box freeze 07:44:22-08:02:42 STATS 84409901..84410189 sits inside this window
# and is covered by official-200 chunks 84409900, 84410000 and 84410100 (pre_run already 289/289 all five).
IN_WINDOW = []
AGED = []
TICK_S = 3.997
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUT = "/workspace/screeps/state/_halfhour_2026-11-22_0830/backfill_confirm_gets.json"
TICK_S_FILE = "/workspace/screeps/state/_halfhour_2026-11-22_0830/tick_s_realign.json"

''' + t[end:]
p.write_text(t)
print("backfill_confirm.py adapted")

# ---- just_published.py ----
p = DST / "backfill_just_published.py"
t = p.read_text()
t = t.replace("_halfhour_2026-11-22_0800", "_halfhour_2026-11-22_0830")
t = t.replace("84410200", "84410600")
p.write_text(t)
print("just_published.py adapted")
for line in t.splitlines():
    if any(s in line for s in ("JUST_BASE", "WAIT_UNTIL", "DIR =", "84410600", "84410200", "84410740")):
        print(" ", line)

# ---- late_retry.py ----
p = DST / "backfill_late_retry.py"
t = p.read_text()
t = t.replace("_halfhour_2026-11-22_0800", "_halfhour_2026-11-22_0830")
lines = t.splitlines()
found = False
for i, ln in enumerate(lines):
    if ln.startswith("TARGETS ="):
        lines[i] = "TARGETS = []  # first pass 35/35 200; leftovers aged out of window start 84409901"
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
t = t.replace("_halfhour_2026-11-22_0800", "_halfhour_2026-11-22_0830")
t = t.replace('IN_WINDOW_404 = {("W47N8", 84409800)}', "IN_WINDOW_404 = set()")
# coverage may have hardcoded T0/T1 for previous window; print them
p.write_text(t)
print("coverage.py adapted")
for line in t.splitlines():
    if any(s in line for s in ("DIR", "IN_WINDOW", "T0", "T1", "84409", "84410", "WINDOW")):
        print(" ", line)
