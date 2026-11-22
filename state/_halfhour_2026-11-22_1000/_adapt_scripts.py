from pathlib import Path

DST = Path("/workspace/screeps/state/_halfhour_2026-11-22_1000")
OLD, NEW = "_halfhour_2026-11-22_0930", "_halfhour_2026-11-22_1000"

# ---- tick_s_check.py ----
p = DST / "tick_s_check.py"
t = p.read_text()
t = t.replace(OLD, NEW)

start = t.index("# Official chunk timestamps printed by history_backfill.py")
end = t.index("def intervals(d):")
new_block = """# Official chunk timestamps printed by history_backfill.py
# First pass 33 of 35 official GETs 200, missing_chunks=2 W45N7@84411500 and
# W47N7@84411800, exit=0.
# published_bases 84411200..84411800 at game.time=84411913; reconstructed 84411201..84411900 (700).
# First-pass tick_s used min-of-all-rooms on the first two published bases,
# computed (MIN 84411300-84411200)/1000/100 = 4.14871, script printed 4.149.
# Insert committed inserted=12510 already_in_db=10921, first-pass realign committed
# ts_realigned=0 (no rows over the 45s gate).
# 09:30 half-hour already wrote through 84411400 / just-published 84411400 for all 5.
# Concurrent 1h patrol _patrol_2026-11-22_0918 already delivered 09:29 USER_LOG.
# 12h review already delivered ~08:33 t508s3618. Do not write those folders.
# Do not restart the listener or war_cmd/pulse. Single listener 2385251 since 09:59:17
# after NEW box freeze 09:41:41-09:59:05 (1037s; STATS 84411621..84411889, 269t;
# listener auto-restart 09:59:08). 08:51 and 09:14 freezes already told in the 09:29
# patrol USER_LOG; fold 09:41 freeze into the next 1h patrol.
# Leftover official 404 W47N8@84409800 and older aged out of window start 84411201
# and are not retried this pass. In-window first-pass 404s W45N7@84411500 and
# W47N7@84411800 wait on confirm. Unpublished tail after 84411900 waits on
# just-published 84411900.
W46 = {
    84411200: 1795310396821,
    84411300: 1795310810262,
    84411400: 1795311227501,
    84411500: 1795311638059,
    84411600: 1795312040124,
    84411700: 1795312461565,
    84411800: 1795312862803,
}
MIN_ALL = {
    84411200: 1795310395391,  # W45N7 (earlier than W46N8 1795310396821)
    84411300: 1795310810262,  # W46N8
    84411400: 1795311227501,  # W46N8
    84411500: 1795311638059,  # W46N8 (W45N7 404)
    84411600: 1795312039100,  # W45N7
    84411700: 1795312458589,  # W45N7
    84411800: 1795312862803,  # W46N8 (W47N7 404)
}
TMIN, TMAX = 84411201, 84411900
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84411300] - MIN_ALL[84411200]) / 1000.0 / 100  # script printed 4.149, exact 4.14871
GT_FIRST = 84411913
TS_REALIGNED_FIRST = 0  # first-pass realign committed, no rows over 45s
PREV_LATER_MEAN = 4.07557  # tick_s_in_use from quiet 09:30 halfhour


"""
t = t[:start] + new_block + t[end:]

new_err = """    first_pass_realign_error = (
        f"First-pass realign with tick_s={TICK_S_FIRST:.5f} (printed 4.149) committed "
        f"ts_realigned_first=0 (inserted=12510 already_in_db=10921, missing_chunks=2 "
        f"W45N7@84411500 W47N7@84411800; no rows over the 45s gate)."
    )
"""
i = t.find("    first_pass_realign_error = (")
if i < 0:
    raise SystemExit("first_pass_realign_error not found")
j = t.find("    reason = (", i)
t = t[:i] + new_err + t[j:]
t = t.replace("printed 4.076", "printed 4.149")
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
# First pass at game.time=84411913; published_bases 84411200..84411800,
# reconstructed 84411201..84411900 (700). inserted=12510, already_in_db=10921, reconstructed=23431,
# ts_realigned_first_pass=0 (first-interval tick_s=4.14871 script printed 4.149; realign committed, no rows over 45s).
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 33 of 35 official GETs 200, missing_chunks=2: W45N7@84411500 and W47N7@84411800.
# Leftover official 404s W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900
# and older aged out of this window start 84411201 and are not retried.
# 09:30 half-hour official already through 84411300 / just-published 84411400.
IN_WINDOW = [("W45N7", 84411500), ("W47N7", 84411800)]
AGED = []
TICK_S = 4.149
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUT = "/workspace/screeps/state/_halfhour_2026-11-22_1000/backfill_confirm_gets.json"
TICK_S_FILE = "/workspace/screeps/state/_halfhour_2026-11-22_1000/tick_s_realign.json"

""" + t[end:]
p.write_text(t)
print("backfill_confirm.py adapted")

# ---- just_published.py ----
p = DST / "backfill_just_published.py"
t = p.read_text()
t = t.replace(OLD, NEW)
t = t.replace("84411400", "84411900")
# also catch leftover 84411140 if any (WAIT is computed as JUST_BASE+140)
p.write_text(t)
print("just_published.py adapted")
for line in t.splitlines():
    if any(s in line for s in ("JUST_BASE", "WAIT_UNTIL", "DIR =", "84411900", "84412040", "sys.path")):
        print(" ", line)

# ---- late_retry.py ----
p = DST / "backfill_late_retry.py"
t = p.read_text()
t = t.replace(OLD, NEW)
lines = t.splitlines()
found = False
for i, ln in enumerate(lines):
    if ln.startswith("TARGETS ="):
        # will be rewritten after confirm/retry2 if still 404 remain
        lines[i] = "TARGETS = []  # placeholder; rewrite after confirm/retry2 if still-404 remain"
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
t = t.replace("TMIN, TMAX = 84410701, 84411400", "TMIN, TMAX = 84411201, 84411900")
# first-pass 404s; coverage IN_WINDOW_404 may be narrowed after confirm
if "IN_WINDOW_404 = set()" in t:
    t = t.replace("IN_WINDOW_404 = set()", "IN_WINDOW_404 = {('W45N7', 84411500), ('W47N7', 84411800)}")
p.write_text(t)
print("coverage.py adapted")
for line in t.splitlines():
    if any(s in line for s in ("DIR", "IN_WINDOW", "TMIN", "TMAX")):
        print(" ", line)

print("structural scripts done; wrapup patched later")
