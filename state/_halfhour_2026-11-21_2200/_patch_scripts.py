#!/usr/bin/env python3
from pathlib import Path
import re

dirp = Path("/workspace/screeps/state/_halfhour_2026-11-21_2200")

p = dirp / "tick_s_check.py"
text = p.read_text()
old_start = text.index("W46 = {")
old_end = text.index("def intervals")
new_block = '''W46 = {
    84400400: 1795265084304,
    84400500: 1795265501392,
    84400600: 1795265927618,
    84400700: 1795266353503,
    84400800: 1795266786675,
    84400900: 1795267230453,
    84401000: 1795267669207,
}
MIN_ALL = {
    84400400: 1795265084304,  # W46N8 (W45N7@84400400 404)
    84400500: 1795265501392,  # W46N8
    84400600: 1795265927618,  # W46N8
    84400700: 1795266353503,  # W46N8
    84400800: 1795266786675,  # W46N8
    84400900: 1795267230453,  # W46N8
    84401000: 1795267669207,  # W46N8
}
TMIN, TMAX = 84400401, 84401100
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84400500] - MIN_ALL[84400400]) / 1000.0 / 100  # script printed 4.171, exact 4.17088
GT_FIRST = 84401126
TS_REALIGNED_FIRST = 15307  # first-pass realign moved 15307 (inserted=2941, already_in_db=22480, missing_chunks=1)
PREV_LATER_MEAN = 4.27314  # 21:00 half-hour tick_s_in_use (all_mean)

'''
p.write_text(text[:old_start] + new_block + text[old_end:])
print("patched tick_s_check.py")

p = dirp / "backfill_confirm.py"
text = p.read_text()
pat = r"IN_WINDOW = \[.*?\]  #.*?\nAGED = \[\]\nTICK_S = [0-9.]+"
repl = """IN_WINDOW = [
    ("W45N7", 84400400),
]  # first pass 34/35 official GETs 200, missing_chunks=1: leftover W45N7@84400400 (not yet told from 21:00 backfill). Window 84400401..84401100 (published_bases 84400400..84401000 at game.time=84401126). Aged-out leftover W45N7@84400300 and W47N8@84400100 are not retried. Just-published 84401000 included in first pass, all five 200.
AGED = []
TICK_S = 4.17088"""
text2, n = re.subn(pat, repl, text, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"confirm IN_WINDOW replace failed n={n}")
p.write_text(text2)
print("patched backfill_confirm.py")

p = dirp / "backfill_just_published.py"
text = p.read_text()
text = text.replace("JUST_BASE = 84400700", "JUST_BASE = 84401000")
text = text.replace("base 84400700 once game.time is safely past 84400840", "base 84401000 once game.time is safely past 84401140")
p.write_text(text)
print("patched backfill_just_published.py")

p = dirp / "backfill_late_retry.py"
text = p.read_text()
text = text.replace(
    'TARGETS = [("W47N8", 84400100), ("W45N7", 84400300), ("W45N7", 84400400)]',
    'TARGETS = [("W45N7", 84400400)]',
)
p.write_text(text)
print("patched backfill_late_retry.py")

p = dirp / "coverage.py"
text = p.read_text()
text = text.replace("TMIN, TMAX = 84400101, 84400800", "TMIN, TMAX = 84400401, 84401100")
pat = r"IN_WINDOW_404 = \{.*?\}  #.*?\nOUT ="
repl = """IN_WINDOW_404 = {
    ("W45N7", 84400400),
}  # first pass 34/35 official GETs 200, missing_chunks=1. Window 84400401..84401100. Aged-out leftover W45N7@84400300 / W47N8@84400100 not retried. Update this set after confirm/retry if a 404 recovers.
OUT ="""
text2, n = re.subn(pat, repl, text, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"coverage IN_WINDOW_404 replace failed n={n}")
p.write_text(text2)
print("patched coverage.py")

print("---- confirm snippet ----")
for i, l in enumerate((dirp / "backfill_confirm.py").read_text().splitlines()[20:36], start=21):
    print(f"{i}:{l}")
print("---- tick_s constants ----")
for i, l in enumerate((dirp / "tick_s_check.py").read_text().splitlines()[34:72], start=35):
    print(f"{i}:{l}")
print("---- just JUST_BASE ----")
for l in (dirp / "backfill_just_published.py").read_text().splitlines():
    if "JUST_BASE" in l or "2100" in l or "2130" in l:
        print(l)
print("---- late TARGETS ----")
for l in (dirp / "backfill_late_retry.py").read_text().splitlines():
    if "TARGETS" in l or "2100" in l or "2130" in l:
        print(l)
print("---- coverage ----")
for i, l in enumerate((dirp / "coverage.py").read_text().splitlines()[10:30], start=11):
    print(f"{i}:{l}")
