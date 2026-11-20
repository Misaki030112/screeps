#!/usr/bin/env python3
from pathlib import Path
DST = Path("/workspace/screeps/state/_halfhour_2026-11-20_1200")
SRC = Path("/workspace/screeps/state/_halfhour_2026-11-20_1130")

# recopy clean sources
for name in ("tick_s_check.py", "coverage.py", "backfill_confirm.py", "backfill_just_published.py", "_post_counts.py"):
    (DST / name).write_text((SRC / name).read_text())

# --- tick_s_check.py ---
p = DST / "tick_s_check.py"
t = p.read_text()
t = t.replace('"_halfhour_2026-11-20_1130"', '"_halfhour_2026-11-20_1200"')
start = t.index("W46 = {")
end = t.index("def intervals(d):")
new_block = '''W46 = {
    84371900: 1795144716160,
    84372000: 1795145126274,
    84372100: 1795145570141,
    84372200: 1795145986370,
    84372300: 1795146405869,
    84372400: 1795146813466,
    84372500: 1795147222710,
}
MIN_ALL = {
    84371900: 1795144716160,  # W46N8 (W45N7 1795144717451 later)
    84372000: 1795145126274,  # W46N8 (W45N7 1795145127247 later)
    84372100: 1795145570073,  # W45N7 (W46N8 1795145570141 later)
    84372200: 1795145986370,  # W46N8 (W45N7 1795145987712 later)
    84372300: 1795146405869,  # W46N8 (W45N7 1795146408003 later)
    84372400: 1795146813466,  # W46N8 (W45N7 1795146815325 later)
    84372500: 1795147222710,  # W46N8 (W45N7 1795147225317 later)
}
TMIN, TMAX = 84371901, 84372600
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84372000] - MIN_ALL[84371900]) / 1000.0 / 100  # script printed 4.101
GT_FIRST = 84372662
TS_REALIGNED_FIRST = 7921  # first-pass realign moved 7921 (inserted=11969, already_in_db=16613, missing_chunks=0)
PREV_LATER_MEAN = 4.279486666666667  # 11:30 half-hour later_mean_w46


'''
t = t[:start] + new_block + t[end:]
t = t.replace("printed 4.214", "printed 4.101")
t = t.replace("inserted=5417, already_in_db=17896, missing_chunks=1", "inserted=11969, already_in_db=16613, missing_chunks=0")
p.write_text(t)
print("patched tick_s_check.py")

# --- coverage.py ---
p = DST / "coverage.py"
t = p.read_text()
t = t.replace("/_halfhour_2026-11-20_1130", "/_halfhour_2026-11-20_1200")
t = t.replace("TMIN, TMAX = 84371601, 84372200", "TMIN, TMAX = 84371901, 84372600")
old = 'IN_WINDOW_404 = {("W46N8", 84371600)}  # 84372200 all-404 is the unpublished just-published base, outside first-pass TMAX=84372200'
new = "IN_WINDOW_404 = set()  # first pass 35/35 official GETs 200, missing_chunks=0; just-published base 84372600 is outside first-pass TMAX=84372600"
if old not in t:
    raise SystemExit("IN_WINDOW_404 line not found")
t = t.replace(old, new)
p.write_text(t)
print("patched coverage.py")

# --- backfill_confirm.py ---
p = DST / "backfill_confirm.py"
t = p.read_text()
t = t.replace("/_halfhour_2026-11-20_1130", "/_halfhour_2026-11-20_1200")
old = 'IN_WINDOW = [("W46N8", 84371600)]'
new = "IN_WINDOW = []  # first pass 35/35, missing_chunks=0; W46N8@84371600 aged out of window start 84371901"
if old not in t:
    raise SystemExit("IN_WINDOW line not found")
t = t.replace(old, new)
t = t.replace("TICK_S = 4.214", "TICK_S = 4.101")
p.write_text(t)
print("patched backfill_confirm.py")

# --- just_published ---
p = DST / "backfill_just_published.py"
t = p.read_text()
t = t.replace("/_halfhour_2026-11-20_1130", "/_halfhour_2026-11-20_1200")
t = t.replace("JUST_BASE = 84372200", "JUST_BASE = 84372600")
t = t.replace("base 84372200 once game.time is safely past 84372340", "base 84372600 once game.time is safely past 84372740")
p.write_text(t)
print("patched just_published.py")

# --- post_counts: only DIR/T0/T1 now; gap section rewritten later ---
p = DST / "_post_counts.py"
t = p.read_text()
t = t.replace("/_halfhour_2026-11-20_1130", "/_halfhour_2026-11-20_1200")
t = t.replace("T0, T1 = 84372201, 84372300", "T0, T1 = 84372601, 84372700")
t = t.replace("just-published 84372200 ticks 84372201..84372300:", "just-published 84372600 ticks 84372601..84372700:")
p.write_text(t)
print("patched _post_counts.py prelim")

# sanity
for name in ("tick_s_check.py", "coverage.py", "backfill_confirm.py", "backfill_just_published.py"):
    txt = (DST / name).read_text()
    if "_halfhour_2026-11-20_1130" in txt:
        raise SystemExit(f"leftover 1130 path in {name}")
print("no leftover 1130 paths")
# print key constants
for line in (DST / "tick_s_check.py").read_text().splitlines():
    if line.startswith(("TMIN", "TICK_S_FIRST", "GT_FIRST", "TS_REALIGNED", "PREV_LATER", "DIR")):
        print("tick_s:", line[:220])
for line in (DST / "coverage.py").read_text().splitlines():
    if line.startswith(("TMIN", "DIR", "IN_WINDOW")):
        print("cov:", line[:220])
for line in (DST / "backfill_just_published.py").read_text().splitlines():
    if "JUST_BASE" in line or "WAIT_UNTIL" in line or "DIR =" in line:
        print("just:", line[:220])
