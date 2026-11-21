#!/usr/bin/env python3
from pathlib import Path
import re

SRC = Path("/workspace/screeps/state/_halfhour_2026-11-21_1700")
DST = Path("/workspace/screeps/state/_halfhour_2026-11-21_1730")

# --- confirm ---
t = (SRC / "backfill_confirm.py").read_text()
t = t.replace(str(SRC), str(DST))
# Replace the IN_WINDOW / AGED / TICK_S block by locating the assignment lines.
lines = t.splitlines(True)
out = []
i = 0
replaced = False
while i < len(lines):
    if lines[i].startswith("IN_WINDOW = "):
        # skip this line and following AGED / TICK_S if present
        out.append(
            'IN_WINDOW = [("W45N7", 84397400)]  # first pass 34/35 official GETs 200, missing_chunks=1 W45N7@84397400. Window 84397101..84397800 (published_bases 84397100..84397700 at game.time=84397873). Already-told leftover official 404s age out of window start 84397101 and are not retried.\n'
        )
        i += 1
        if i < len(lines) and lines[i].startswith("AGED = "):
            out.append("AGED = []\n")
            i += 1
        if i < len(lines) and lines[i].startswith("TICK_S = "):
            out.append("TICK_S = 4.189\n")
            i += 1
        replaced = True
        continue
    out.append(lines[i])
    i += 1
if not replaced:
    raise SystemExit("confirm: IN_WINDOW not found")
(DST / "backfill_confirm.py").write_text("".join(out))
print("wrote confirm, IN_WINDOW ok")

# --- just_published ---
t = (SRC / "backfill_just_published.py").read_text()
t = t.replace(str(SRC), str(DST))
t = t.replace("84397400", "84397800")
t = t.replace("safely past 84397540", "safely past 84397940")
(DST / "backfill_just_published.py").write_text(t)
print("wrote just_published")
for line in t.splitlines():
    if "JUST_BASE" in line or "WAIT_UNTIL" in line or "Fetch just" in line:
        print(" ", line)

# --- coverage ---
t = (SRC / "coverage.py").read_text()
t = t.replace(str(SRC), str(DST))
t = t.replace("TMIN, TMAX = 84396701, 84397400", "TMIN, TMAX = 84397101, 84397800")
t = t.replace(
    "IN_WINDOW_404 = set()  # first pass 35/35 official GETs 200, missing_chunks=0. Already-told leftover official 404s age out of window start 84396701 and are not retried.",
    'IN_WINDOW_404 = {("W45N7", 84397400)}  # first pass 34/35 official GETs 200, missing_chunks=1 W45N7@84397400. Already-told leftover official 404s age out of window start 84397101 and are not retried.',
)
if "TMIN, TMAX = 84397101, 84397800" not in t:
    raise SystemExit("coverage TMIN patch failed")
(DST / "coverage.py").write_text(t)
print("wrote coverage")

# --- tick_s_check ---
t = (SRC / "tick_s_check.py").read_text()
t = t.replace(str(SRC), str(DST))
w46 = '''W46 = {
    84397100: 1795250917931,
    84397200: 1795251336839,
    84397300: 1795251764308,
    84397400: 1795252202921,
    84397500: 1795252627120,
    84397600: 1795253057610,
    84397700: 1795253492945,
}
MIN_ALL = {
    84397100: 1795250917931,  # W46N8
    84397200: 1795251336839,  # W46N8
    84397300: 1795251764308,  # W46N8
    84397400: 1795252202921,  # W46N8
    84397500: 1795252627120,  # W46N8
    84397600: 1795253057610,  # W46N8
    84397700: 1795253492945,  # W46N8
}
TMIN, TMAX = 84397101, 84397800
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84397200] - MIN_ALL[84397100]) / 1000.0 / 100  # script printed 4.189, exact 4.18908
GT_FIRST = 84397873
TS_REALIGNED_FIRST = 0  # first-pass realign moved 0 (inserted=0, already_in_db=25644, missing_chunks=1 W45N7@84397400)
PREV_LATER_MEAN = 4.23884  # 17:00 half-hour tick_s_in_use (first)'''
t2, n = re.subn(r"W46 = \{.*?\nPREV_LATER_MEAN = [^\n]+", w46, t, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"tick_s_check W46 block replace count={n}")
if "84397100: 1795250917931" not in t2 or "TMIN, TMAX = 84397101, 84397800" not in t2:
    raise SystemExit("tick_s_check patch failed")
if "_halfhour_2026-11-21_1700" in t2:
    raise SystemExit("leftover 1700 path in tick_s_check")
(DST / "tick_s_check.py").write_text(t2)
print("wrote tick_s_check")
# print constants
for i, line in enumerate(t2.splitlines(), 1):
    if 20 <= i <= 65:
        print(f"{i:3d} {line}")
