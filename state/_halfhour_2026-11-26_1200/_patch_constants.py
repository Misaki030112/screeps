#!/usr/bin/env python3
from pathlib import Path
import re

d = Path("/workspace/screeps/state/_halfhour_2026-11-26_1200")

p = d / "tick_s_check.py"
text = p.read_text()
start = text.index("W46 = {")
end = text.index("\ndef intervals(d):")
new_block = '''W46 = {
    84493300: 1795663394832,
    84493400: 1795663831614,
    84493500: 1795664266253,
    84493600: 1795664707595,
    84493700: 1795665136690,
    84493800: 1795665579417,
    84493900: 1795666010080,
}
MIN_ALL = {
    84493300: 1795663394832,  # W46N8 (W45N7 1795663397348 / W45N8 1795663437836 / W47N8 1795663441652 / W47N7 1795663472200)
    84493400: 1795663831614,  # W46N8 (W45N7 1795663833661 / W45N8 1795663864299 / W47N8 1795663866618 / W47N7 1795663895544)
    84493500: 1795664266253,  # W46N8 (W45N7 1795664267704 / W45N8 1795664295979 / W47N8 1795664298449 / W47N7 1795664323013)
    84493600: 1795664707595,  # W46N8 (W45N7 1795664708345 / W45N8 1795664742857 / W47N8 1795664748408 / W47N7 1795664774120)
    84493700: 1795665136690,  # W46N8 (W45N7 1795665137733 / W45N8 1795665165070 / W47N8 1795665166719 / W47N7 1795665191447)
    84493800: 1795665579417,  # W46N8 (W45N7 1795665580471 / W45N8 1795665612738 / W47N8 1795665615661 / W47N7 1795665643141)
    84493900: 1795666008850,  # W45N7 (W46N8 1795666010080 / W45N8 1795666039316 / W47N8 1795666040726 / W47N7 404)
}
TMIN, TMAX = 84493301, 84494000
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84493400] - MIN_ALL[84493300]) / 1000.0 / 100  # script printed 4.368, exact 4.36782
GT_FIRST = 84494010
TS_REALIGNED_FIRST = 0
PREV_LATER_MEAN = 4.38390  # later_mean_robust / tick_s_in_use from 1130 wrap (all_mean / live-anchor best)


'''
if start < 0 or end < 0:
    raise SystemExit(f"markers not found start={start} end={end}")
p.write_text(text[:start] + new_block + text[end:])
print("tick_s_check constants updated")
print("TICK_S_FIRST would be", (1795663831614 - 1795663394832) / 1000.0 / 100)

p = d / "backfill_confirm.py"
text = p.read_text()
text2, n = re.subn(
    r"IN_WINDOW = \[.*?\]\nAGED = \[\]",
    '''IN_WINDOW = [
    ("W47N7", 84493900),  # NEW first-pass in-window official 404 this 1200 pass at gt=84494010; other four rooms already 200 on 84493900; retry; if still 404 after confirm/retry2/late/postjp, leftover official 404 (hole 84493901..84494000)
]
AGED = []''',
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit(f"IN_WINDOW replace count={n}")
p.write_text(text2)
print("confirm IN_WINDOW updated")

new_targets = '''TARGETS = [
    ("W47N7", 84493900),  # NEW first-pass in-window official 404 this 1200 pass; retry; do not skip
]
'''
for fname in ("backfill_late_retry.py", "backfill_postjp_retry.py"):
    p = d / fname
    text = p.read_text()
    text2, n = re.subn(
        r"TARGETS = \[.*?\]\n",
        new_targets,
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit(f"{fname} TARGETS replace count={n}")
    p.write_text(text2)
    print(fname, "TARGETS updated")

for fname in (
    "backfill_just_published.py",
    "backfill_just_published_retry.py",
    "backfill_just_published_retry2.py",
):
    p = d / fname
    text = p.read_text()
    if "JUST_BASE = 84493500" not in text:
        raise SystemExit(f"{fname} missing old JUST_BASE=84493500, got: " + [ln for ln in text.splitlines() if "JUST_BASE" in ln][0])
    text = text.replace("JUST_BASE = 84493500", "JUST_BASE = 84494000")
    p.write_text(text)
    print(fname, "JUST_BASE -> 84494000")

# coverage window including upcoming JP 84494000; IN_WINDOW_404 for first-pass miss
p = d / "coverage.py"
text = p.read_text()
text2, n = re.subn(r"TMIN, TMAX = 84492801, 84493600", "TMIN, TMAX = 84493301, 84494100", text, count=1)
if n != 1:
    raise SystemExit(f"coverage TMIN replace count={n}")
text3, n = re.subn(
    r"IN_WINDOW_404 = \{.*?\}\n",
    '''IN_WINDOW_404 = {
    ("W47N7", 84493900),  # first-pass in-window official 404 this 1200 pass; update after retries if recovered
}
''',
    text2,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit(f"coverage IN_WINDOW_404 replace count={n}")
p.write_text(text3)
print("coverage TMIN/TMAX and IN_WINDOW_404 updated")

print("all constant updates ok")
