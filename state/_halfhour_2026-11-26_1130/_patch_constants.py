#!/usr/bin/env python3
from pathlib import Path
import re

# --- tick_s_check.py: replace constant block ---
p = Path("/workspace/screeps/state/_halfhour_2026-11-26_1130/tick_s_check.py")
text = p.read_text()
start = text.index("W46 = {")
end = text.index("\ndef intervals(d):")
new_block = '''W46 = {
    84492800: 1795661201276,
    84492900: 1795661632993,
    84493000: 1795662063846,
    84493100: 1795662508320,
    84493200: 1795662946691,
    84493300: 1795663394832,
    84493400: 1795663831614,
}
MIN_ALL = {
    84492800: 1795661201276,  # W46N8 (W45N7 1795661202592 / W45N8 1795661237626 / W47N8 1795661241051 / W47N7 1795661269964)
    84492900: 1795661632993,  # W46N8 (W45N7 1795661633852 / W45N8 1795661666347 / W47N8 1795661668970 / W47N7 1795661695197)
    84493000: 1795662063846,  # W46N8 (W45N7 1795662064180 / W45N8 1795662097220 / W47N8 1795662100363 / W47N7 1795662129570)
    84493100: 1795662508320,  # W46N8 (W45N7 1795662509625 / W45N8 1795662550496 / W47N8 1795662554647 / W47N7 1795662592757)
    84493200: 1795662946691,  # W46N8 (W45N7 1795662948510 / W45N8 1795662986710 / W47N8 1795662990498 / W47N7 1795663022557)
    84493300: 1795663394832,  # W46N8 (W45N7 1795663397348 / W45N8 1795663437836 / W47N8 1795663441652 / W47N7 1795663472200)
    84493400: 1795663831614,  # W46N8 (W45N7 1795663833661 / W45N8 1795663864299 / W47N8 1795663866618 / W47N7 1795663895544)
}
TMIN, TMAX = 84492801, 84493500
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84492900] - MIN_ALL[84492800]) / 1000.0 / 100  # script printed 4.317, exact 4.31717
GT_FIRST = 84493548
TS_REALIGNED_FIRST = 13254
PREV_LATER_MEAN = 4.38457  # later_mean_robust from 1100 wrap (tick_s_in_use was 4.51671 first/live-anchor)


'''
if start < 0 or end < 0:
    raise SystemExit(f"markers not found start={start} end={end}")
p.write_text(text[:start] + new_block + text[end:])
print("tick_s_check constants updated")
print("TICK_S_FIRST would be", (1795661632993 - 1795661201276) / 1000.0 / 100)

# --- backfill_confirm.py IN_WINDOW ---
p = Path("/workspace/screeps/state/_halfhour_2026-11-26_1130/backfill_confirm.py")
text = p.read_text()
text2, n = re.subn(
    r"IN_WINDOW = \[.*?\]\nAGED = \[\]",
    '''IN_WINDOW = [
    ("W47N8", 84492600),  # already-untold leftover official 404 first recorded in 0930 80-min top-up; aged just outside this window start 84492801 (near-window); still 404 through 1100 first pass/confirm/retry2/late/postjp official inserted=0; listener 0/100 ticks 84492601..84492700; retry as near-window; do not relabel NEW
    ("W47N7", 84492300),  # already-untold leftover official 404 first recorded in 0930 80-min top-up; further outside this window start 84492801; still 404 through 1100 confirm/retry2/late/postjp official inserted=0; listener 0/100 ticks 84492301..84492400; retry as near-window; do not relabel NEW
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

# --- late + postjp TARGETS ---
new_targets = '''TARGETS = [
    ("W47N8", 84492600),  # already-untold leftover official 404; near-window (outside start 84492801); still 404 through 1100; retry; do not relabel NEW
    ("W47N7", 84492300),  # already-untold leftover official 404; further outside start 84492801; still 404 through 1100; retry as near-window; do not relabel NEW
]
'''
for fname in ("backfill_late_retry.py", "backfill_postjp_retry.py"):
    p = Path("/workspace/screeps/state/_halfhour_2026-11-26_1130") / fname
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

# --- JUST_BASE in JP scripts ---
for fname in (
    "backfill_just_published.py",
    "backfill_just_published_retry.py",
    "backfill_just_published_retry2.py",
):
    p = Path("/workspace/screeps/state/_halfhour_2026-11-26_1130") / fname
    text = p.read_text()
    if "JUST_BASE = 84493200" not in text:
        raise SystemExit(f"{fname} missing old JUST_BASE")
    text = text.replace("JUST_BASE = 84493200", "JUST_BASE = 84493500")
    p.write_text(text)
    print(fname, "JUST_BASE -> 84493500")

print("all constant updates ok")
