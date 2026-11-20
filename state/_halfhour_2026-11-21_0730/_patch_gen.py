#!/usr/bin/env python3
from pathlib import Path
import re

p = Path("/workspace/screeps/state/_halfhour_2026-11-21_0730/_gen_scripts.py")
s = p.read_text()
s2, n = re.subn(
    r"PREV_LATER_MEAN = [0-9.]+  # [^\n]+",
    "PREV_LATER_MEAN = 4.22596  # 07:00 half-hour tick_s_in_use (all_mean)",
    s,
    count=1,
)
print("PREV_LATER_MEAN replacements", n)
s = s2
m = re.search(r"new_gaps = f'''GAPS = \[.*?\]'''", s, re.S)
if not m:
    raise SystemExit("new_gaps block not found")
new_gaps = """new_gaps = f'''GAPS = [
    ("gap_0722_0725", 84389231, 84389299),  # NEW this run, not yet told by a 1h patrol (box freeze 07:22:15-07:25:56, 214s); 69t; last_stats 84389230 at 07:21:52, next 84389300 at 07:26:45; listener auto-restart 07:25:59, python 1733733 started 07:26:09; sits in official window start {tmin}..end (chunk 84389200)
    ("gap_0642_0704", 84388671, 84388999),  # first seen by 07:00/07:18 half-hour, not yet told by a 1h patrol (box freeze 06:42:51-07:04:46, 1315s); 329t; last_stats 84388670 at 06:42:15, next 84389000 at 07:05:30; listener auto-restart 07:04:49; still in official window start {tmin} (chunks 84388600..84388900)
    ("gap_0634_0637", 84388561, 84388599),  # first seen by 07:00/07:18 half-hour, not yet told (ping/pong timeout 06:36:25, listener restart 06:36:28); 39t; official-fill missing W45N7 all 39 due to leftover official 404 W45N7@84388500; ages out of window start {tmin}
    ("gap_0619_0622", 84388331, 84388399),  # already-told by the 06:33 1h patrol (box freeze 06:19:18-06:22:57, 218s); 69t; official-filled all five 69/69; ages out of window start {tmin}
    ("gap_0542_0601", 84387811, 84388109),  # already-told by the 06:33 1h patrol (box freeze 05:42:11-06:01:46, 1169s); 299t; official-filled all five 299/299; ages out of window start {tmin}
    ("gap_0442_0503", 84386961, 84387269),  # already-told by the 05:26 1h patrol (box freeze 04:42:19-05:03:11, 1245s); 309t; official-filled all five 309/309; ages out of window start {tmin}
    ("gap_0410_0418", 84386511, 84386629),  # already-told by the 04:18/04:29 1h patrol (box freeze 04:10:40-04:18:06, 439s); 119t; official-fill missing W45N8 84386601..84386629; ages out of window start {tmin}
    ("gap_0354_0357", 84386281, 84386339),  # already-told by the 04:18/04:29 1h patrol (short freeze 03:54:27-03:57:32, 178s); 59t; official-filled all five 59/59; ages out of window start {tmin}
    ("gap_0245_0305", 84385301, 84385599),  # already-told by 03:17 backfill / 03:30 1h patrol (box freeze 02:45:59-03:05:48, ~1189s); 299t; official 404 W47N8@84385300 leaves W47N8 missing 84385301..84385400; ages out of window start {tmin}
]'''"""
s = s[: m.start()] + new_gaps + s[m.end() :]
p.write_text(s)
print("GAPS patched ok")
