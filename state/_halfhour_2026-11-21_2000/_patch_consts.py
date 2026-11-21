from pathlib import Path
import re

# coverage.py
p = Path("/workspace/screeps/state/_halfhour_2026-11-21_2000/coverage.py")
t = p.read_text()
t = t.replace("TMIN, TMAX = 84398801, 84399500", "TMIN, TMAX = 84399201, 84399900")
start = t.index("IN_WINDOW_404 = {")
end = t.index("OUT =")
new = '''IN_WINDOW_404 = {
    ("W45N8", 84399300),
    ("W45N8", 84399500),
    ("W45N7", 84399800),
}  # first pass 32/35 official GETs 200, missing_chunks=3: W45N8@84399300 (already told), W45N8@84399500 (not yet told from 19:47), W45N7@84399800 (new first-pass 404). Window 84399201..84399900. Aged-out leftovers all five @84399100 not retried. W45N7 evac empty 84399201..84399248 and 84399287..84399300 in official-200 chunk 84399200, not 404s.
'''
p.write_text(t[:start] + new + t[end:])
print("patched coverage.py")

# post_counts.py
p = Path("/workspace/screeps/state/_halfhour_2026-11-21_2000/post_counts.py")
t = p.read_text()
t = t.replace("JUST_BASE = 84399500", "JUST_BASE = 84399900")
t = t.replace("WIN_TMIN, WIN_TMAX = 84398801, 84399500", "WIN_TMIN, WIN_TMAX = 84399201, 84399900")
start = t.index("GAPS = [")
end = t.index("HK = ZoneInfo")
new = '''GAPS = [
    ("gap_1952_2002", 84399771, 84399919),  # NEW not yet told (box freeze 19:52:19-20:02:21, 599s, already healed); STATS 149t; listener auto-restart 20:02:25, python 2055432 started 20:02:34.
    ("gap_1910_1918", 84399191, 84399309),  # already told by the delivered 19:18/19:28 1h patrol (box freeze 19:10:45-19:18:45, 476s); STATS 119t; overlaps window head; leftover official 404 84399100 aged out of official window start 84399201.
    ("gap_1847_1858", 84398871, 84399029),  # already told by the delivered 19:18/19:28 1h patrol (box freeze 18:47:50-18:58:17, 626s); ages out of official window start 84399201.
]


'''
p.write_text(t[:start] + new + t[end:])
t = p.read_text()
old = '''for room, base in [("W45N7", 84397400), ("W47N7", 84395600), ("W47N8", 84395100), ("W46N8", 84394300), ("W45N8", 84392600), ("W46N8", 84390800), ("W47N7", 84390900), ("W46N8", 84390400), ("W45N7", 84388500), ("W45N8", 84386600), ("W47N8", 84385300), ("W45N7", 84383500), ("W45N7", 84383900), ("W45N7", 84382700), ("W46N8", 84382900), ("W45N8", 84382600), ("W46N8", 84386400), ("W47N8", 84385900)]:'''
newh = '''for room, base in [("W45N8", 84399300), ("W45N8", 84399500), ("W45N7", 84399800), ("W46N8", 84399100), ("W47N8", 84399100), ("W45N8", 84399100), ("W45N7", 84399100), ("W47N7", 84399100)]:'''
if old not in t:
    raise SystemExit("holes list not found")
p.write_text(t.replace(old, newh, 1))
print("patched post_counts.py")
