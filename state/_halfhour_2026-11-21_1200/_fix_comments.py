#!/usr/bin/env python3
from pathlib import Path
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1200")
old = (
    "Already-told leftover official 404s W47N8@84385300, W45N7@84383500, W45N7@84383900, "
    "W45N8@84382600, W45N7@84382700, W46N8@84382900, W47N8@84385900, W46N8@84386400, "
    "and W45N8@84386600 age out of window start 84392401 and are not retried here."
)
new = (
    "Already-told leftover official 404s W46N8@84390400, W46N8@84390800, W47N7@84390900, "
    "W45N7@84388500, W45N8@84386600 and older age out of window start 84392401 and are not retried here."
)
for name in ("backfill_confirm.py", "coverage.py"):
    p = DIR / name
    t = p.read_text()
    if old not in t:
        i = t.find("Already-told")
        print(name, "OLD leftover text not found")
        print(repr(t[i:i+350]))
    else:
        p.write_text(t.replace(old, new))
        print(name, "leftover comment fixed")

p = DIR / "post_counts.py"
t = p.read_text()
start = t.index("GAPS = [")
end = t.index("]", start) + 1
new_gaps = """GAPS = [
    ("gap_1149_1157", 84393001, 84393129),  # NEW this run, not yet told (box freeze 11:49:12-11:57:31, 494s); 129t; last_stats 84393000 at 11:48:55, next 84393130 at 11:58:04; listener auto-restart 11:57:34, python 1849703 started 11:57:44; sits in official window start 84392401 (chunks 84393000..84393100).
    ("gap_1119_1120", 84392571, 84392609),  # already-told by the 11:28 1h patrol (box freeze 11:19:06-11:20:43, 88s); 39t; official-filled 39/39 except W45N8 30/39 missing tail 84392601..84392609 due to leftover official 404 W45N8@84392600; still in official window start 84392401
    ("gap_1111_1113", 84392471, 84392499),  # recorded by the 11:30 backfill, not a box freeze: short listener WS ping/pong timeout 11:12:51, restart 11:12:54; 29t; official-filled all five 29/29; not told by the 11:28 patrol as a freeze; still in official window start 84392401
    ("gap_1047_1059", 84392131, 84392309),  # already-told by the 11:28 1h patrol (box freeze 10:47:36-10:59:07, 684s); 179t; official-filled all five 179/179; ages out of window start 84392401
    ("gap_1017_1024", 84391711, 84391819),  # already-told by the 10:31 1h patrol (box freeze 10:17:34-10:24:42, 423s); official-filled all five 109/109; ages out of window start 84392401
    ("gap_0958_1005", 84391431, 84391549),  # already-told by the 10:31 1h patrol (box freeze 09:58:02-10:05:00, 412s); ages out of window start 84392401
    ("gap_0915_0923", 84390831, 84390959),  # already-told by the 09:42 1h patrol (box freeze 09:15:27-09:23:48, 492s); ages out of window start 84392401
]"""
p.write_text(t[:start] + new_gaps + t[end:])
print("post_counts GAPS replaced, starts with", p.read_text()[p.read_text().index("GAPS"):p.read_text().index("GAPS")+80])
