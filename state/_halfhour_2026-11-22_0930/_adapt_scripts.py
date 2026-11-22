from pathlib import Path

DST = Path("/workspace/screeps/state/_halfhour_2026-11-22_0930")
OLD, NEW = "_halfhour_2026-11-22_0900", "_halfhour_2026-11-22_0930"

# ---- tick_s_check.py ----
p = DST / "tick_s_check.py"
t = p.read_text()
t = t.replace(OLD, NEW)

start = t.index("# Official chunk timestamps printed by history_backfill.py")
end = t.index("def intervals(d):")
new_block = """# Official chunk timestamps printed by history_backfill.py
# First pass 35 of 35 official GETs 200, missing_chunks=0, exit=0.
# published_bases 84410700..84411300 at game.time=84411454; reconstructed 84410701..84411400 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84410800-84410700)/1000/100 = 4.07557, script printed 4.076.
# Insert committed inserted=200 already_in_db=25034, first-pass realign committed
# ts_realigned=0 (no rows over the 45s gate).
# 09:00 half-hour already wrote through 84411000 / just-published 84411000 for all 5.
# Concurrent 1h patrol _patrol_2026-11-22_0918 already delivered 09:29 USER_LOG
# (also official-filled 84410601..84411300 and just-published 84411300 through 84411400).
# 12h review already delivered ~08:33 t508s3618. Do not write those folders.
# Do not restart the listener or war_cmd/pulse. Single listener 2371673 since 09:19:17
# after NEW box freeze 09:14:15-09:19:05 (283s; STATS 84411221..84411299, 79t;
# listener auto-restart 09:19:08). 08:51 and 09:14 freezes already told in the 09:29
# patrol USER_LOG. Leftover official 404 W47N8@84409800 and older aged out of
# window start 84410701 and are not retried this pass. W47N7@84411200 was 404 in
# the patrol first pass and already recovered on that patrol's confirm (this first
# pass got 200). Unpublished tail after 84411400 waits on just-published 84411400.
W46 = {
    84410700: 1795308347692,
    84410800: 1795308755249,
    84410900: 1795309161287,
    84411000: 1795309580854,
    84411100: 1795309983841,
    84411200: 1795310396821,
    84411300: 1795310810262,
}
MIN_ALL = {
    84410700: 1795308347692,  # W46N8
    84410800: 1795308755249,  # W46N8
    84410900: 1795309161287,  # W46N8
    84411000: 1795309580854,  # W46N8
    84411100: 1795309983841,  # W46N8
    84411200: 1795310395391,  # W45N7 (earlier than W46N8 1795310396821)
    84411300: 1795310810262,  # W46N8
}
TMIN, TMAX = 84410701, 84411400
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84410800] - MIN_ALL[84410700]) / 1000.0 / 100  # script printed 4.076, exact 4.07557
GT_FIRST = 84411454
TS_REALIGNED_FIRST = 0  # first-pass realign committed, no rows over 45s
PREV_LATER_MEAN = 4.099614  # tick_s_in_use from quiet 09:00 halfhour


"""
t = t[:start] + new_block + t[end:]

new_err = """    first_pass_realign_error = (
        f"First-pass realign with tick_s={TICK_S_FIRST:.5f} (printed 4.076) committed "
        f"ts_realigned_first=0 (inserted=200 already_in_db=25034, missing_chunks=0; "
        f"no rows over the 45s gate)."
    )
"""
i = t.find("    first_pass_realign_error = (")
if i < 0:
    raise SystemExit("first_pass_realign_error not found")
j = t.find("    reason = (", i)
t = t[:i] + new_err + t[j:]
t = t.replace("printed 4.101", "printed 4.076")
p.write_text(t)
print("tick_s_check.py adapted")

# ---- confirm.py ----
p = DST / "backfill_confirm.py"
t = p.read_text()
t = t.replace(OLD, NEW)
t = t.replace("_halfhour_2026-11-22_0730", NEW)
start = t.index("ROOMS = ")
end = t.index("def load_tick_s():")
t = t[:start] + """ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# First pass at game.time=84411454; published_bases 84410700..84411300,
# reconstructed 84410701..84411400 (700). inserted=200, already_in_db=25034, reconstructed=25234,
# ts_realigned_first_pass=0 (first-interval tick_s=4.07557 script printed 4.076; realign committed, no rows over 45s).
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 35 of 35 official GETs 200, missing_chunks=0. No in-window official 404s to confirm.
# W47N7@84411200 was 404 in the concurrent 09:18 patrol first pass and already recovered
# on that patrol's confirm; this first pass got 200 for it.
# Leftover official 404s W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900
# and older aged out of this window start 84410701 and are not retried.
# 09:00 half-hour official already through 84410900 / just-published 84411000.
# Concurrent patrol already official-filled 84410601..84411300 and JP 84411300 through 84411400.
IN_WINDOW = []
AGED = []
TICK_S = 4.076
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUT = "/workspace/screeps/state/_halfhour_2026-11-22_0930/backfill_confirm_gets.json"
TICK_S_FILE = "/workspace/screeps/state/_halfhour_2026-11-22_0930/tick_s_realign.json"

""" + t[end:]
p.write_text(t)
print("backfill_confirm.py adapted")

# ---- just_published.py ----
p = DST / "backfill_just_published.py"
t = p.read_text()
t = t.replace(OLD, NEW)
t = t.replace("84411000", "84411400")
p.write_text(t)
print("just_published.py adapted")
for line in t.splitlines():
    if any(s in line for s in ("JUST_BASE", "WAIT_UNTIL", "DIR =", "84411400", "84411540", "sys.path")):
        print(" ", line)

# ---- late_retry.py ----
p = DST / "backfill_late_retry.py"
t = p.read_text()
t = t.replace(OLD, NEW)
lines = t.splitlines()
found = False
for i, ln in enumerate(lines):
    if ln.startswith("TARGETS ="):
        lines[i] = "TARGETS = []  # first pass 35/35 200; leftovers aged out of window start 84410701"
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
t = t.replace("TMIN, TMAX = 84410301, 84411000", "TMIN, TMAX = 84410701, 84411400")
p.write_text(t)
print("coverage.py adapted")
for line in t.splitlines():
    if any(s in line for s in ("DIR", "IN_WINDOW", "TMIN", "TMAX")):
        print(" ", line)

print("structural scripts done; wrapup patched separately")
