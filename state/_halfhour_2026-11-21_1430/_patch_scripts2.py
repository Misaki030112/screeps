#!/usr/bin/env python3
from pathlib import Path

src = Path("/workspace/screeps/state/_halfhour_2026-11-21_1400")
dst = Path("/workspace/screeps/state/_halfhour_2026-11-21_1430")

# --- confirm: recopy and patch only specific lines ---
c = (src / "backfill_confirm.py").read_text()
c = c.replace("/workspace/screeps/state/_halfhour_2026-11-21_1400/", "/workspace/screeps/state/_halfhour_2026-11-21_1430/")
lines = c.splitlines(keepends=True)
out = []
for line in lines:
    if line.startswith("IN_WINDOW = "):
        out.append(
            'IN_WINDOW = [("W47N8", 84395100)]  # first pass 34/35 official GETs 200, missing_chunks=1 W47N8@84395100. '
            "In-window first-pass official 404: W47N8@84395100 (not yet told; retried here). "
            "Already-told leftover official 404 W46N8@84394300 (told by the delivered 13:32 1h patrol t508s3575) "
            "ages out of window start 84394501 and is not retried here. Already-told leftover official 404s "
            "W45N8@84392600, W46N8@84390800, W47N7@84390900, W46N8@84390400, W45N7@84388500, W45N8@84386600 "
            "and older also age out of window start 84394501 and are not retried here.\n"
        )
    elif line.startswith("TICK_S = "):
        out.append("TICK_S = 4.14548\n")
    else:
        out.append(line)
text = "".join(out)
(dst / "backfill_confirm.py").write_text(text)
assert "def retry_one" in text and "def main" in text
assert text.count("IN_WINDOW = ") == 1
assert 'IN_WINDOW = [("W47N8", 84395100)]' in text
assert "/workspace/screeps/state/_halfhour_2026-11-21_1430/" in text
assert "/workspace/screeps/state/_halfhour_2026-11-21_1400/" not in text
print("confirm ok, bytes", len(text), "lines", text.count(chr(10)))

# --- coverage ---
cov = (src / "coverage.py").read_text()
cov = cov.replace("/workspace/screeps/state/_halfhour_2026-11-21_1400", "/workspace/screeps/state/_halfhour_2026-11-21_1430")
# also DIR = "..." form
cov = cov.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
cov = cov.replace("TMIN, TMAX = 84394101, 84394800", "TMIN, TMAX = 84394501, 84395200")
olines = []
for line in cov.splitlines(keepends=True):
    if line.startswith("IN_WINDOW_404 = "):
        olines.append(
            'IN_WINDOW_404 = {("W47N8", 84395100)}  # first pass 34/35 official GETs 200, missing_chunks=1 W47N8@84395100. '
            "Already-told leftover official 404 W46N8@84394300 ages out of window start 84394501 and is not retried here.\n"
        )
    else:
        olines.append(line)
cov = "".join(olines)
(dst / "coverage.py").write_text(cov)
assert "def main" in cov and "84394501, 84395200" in cov
print("coverage ok, bytes", len(cov))

# --- just_published ---
jp = (src / "backfill_just_published.py").read_text()
jp = jp.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
jp = jp.replace("JUST_BASE = 84394800", "JUST_BASE = 84395200")
jp = jp.replace("base 84394800 once game.time is safely past 84394940", "base 84395200 once game.time is safely past 84395340")
(dst / "backfill_just_published.py").write_text(jp)
assert "JUST_BASE = 84395200" in jp
assert "_halfhour_2026-11-21_1430" in jp
assert "_halfhour_2026-11-21_1400" not in jp
print("just_published ok, bytes", len(jp))

# --- post_counts ---
pc = (src / "post_counts.py").read_text()
pc = pc.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
pc = pc.replace("JUST_BASE = 84394800", "JUST_BASE = 84395200")
pc = pc.replace("WIN_TMIN, WIN_TMAX = 84394101, 84394800", "WIN_TMIN, WIN_TMAX = 84394501, 84395200")
lines = pc.splitlines(keepends=True)
out = []
i = 0
while i < len(lines):
    if lines[i].startswith("GAPS = ["):
        out.append('''GAPS = [
    ("gap_1415_1423", 84395061, 84395179),  # NEW this run, not yet told (box freeze 14:15:50-14:23:29, 450s); 119t; last_stats 84395060 at 14:15:39, next 84395180 at 14:24:16; listener auto-restart 14:23:32, python 1910963 started 14:23:42; official window start 84394501 covers the whole 119t (chunks 84395000 and 84395100). Concurrent 1h patrol _patrol_2026-11-21_1423 is running; do not write its folder.
    ("gap_1349_1356", 84394681, 84394809),  # recorded not-yet-told by the 14:00 half-hour backfill (box freeze 13:49:01-13:56:56, 475s); 129t; official-filled all five 129/129; still in official window start 84394501. Keep as not-yet-told unless the concurrent 14:23 patrol has already delivered it.
    ("gap_1309_1321", 84394131, 84394299),  # already told by the delivered 13:32 1h patrol t508s3575 (box freeze 13:09:46-13:21:14, 680s); 169t; official-filled all five 169/169; ages out of official window start 84394501.
    ("gap_1248_1257", 84393831, 84393969),  # already told by the delivered 13:32 1h patrol t508s3575 (box freeze 12:48:14-12:57:17, 534s); 139t; official-filled all five 139/139; ages out of official window start 84394501.
    ("gap_1230_1235", 84393581, 84393659),  # already told by the delivered 13:32 1h patrol t508s3575 (box freeze 12:30:42-12:35:35, 283s); 79t; official-filled all five 79/79; ages out of official window start 84394501.
    ("gap_1218", 84393391, 84393419),  # already told by the 12:26/13:32 1h patrols (short listener WS ping/pong 12:18:13, restart 12:18:17; not a box freeze); 29t; ages out of official window start 84394501
    ("gap_1210", 84393291, 84393319),  # already told by the 12:26/13:32 1h patrols (short listener WS ping/pong 12:10:56, restart 12:10:59; not a box freeze); 29t; ages out of official window start 84394501
    ("gap_1149_1157", 84393001, 84393129),  # already told by the 12:26/13:32 1h patrols (box freeze 11:49:12-11:57:31, 494s); 129t; official-filled all five 129/129; ages out of window start 84394501
    ("gap_1119_1120", 84392571, 84392609),  # already told by the 11:28/13:32 1h patrols (box freeze 11:19:06-11:20:43, 88s); leftover official 404 W45N8@84392600 already told; ages out of window start 84394501
    ("gap_1111_1113", 84392471, 84392499),  # already told by the 12:26/13:32 1h patrols (short listener WS ping/pong 11:12:51-11:12:54, not a box freeze); official-filled all five 29/29; ages out of window start 84394501
]
''')
        # skip until line that is just ']'
        i += 1
        while i < len(lines) and lines[i].strip() != "]":
            i += 1
        if i < len(lines) and lines[i].strip() == "]":
            i += 1  # skip closing ]
        continue
    out.append(lines[i])
    i += 1
pc = "".join(out)
(dst / "post_counts.py").write_text(pc)
assert "gap_1415_1423" in pc and "JUST_BASE = 84395200" in pc
assert "def " not in pc or True
print("post_counts ok, bytes", len(pc), "GAPS start ok")

# late retry
lr = (src / "backfill_late_retry.py").read_text()
lr = lr.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
# only replace target room/base constants, not all W46N8 mentions blindly
# read and print constant lines first after write of a careful version
(dst / "backfill_late_retry.py").write_text(lr)
print("late_retry copied raw; inspect constants:")
for i, line in enumerate(lr.splitlines(), 1):
    if any(k in line for k in ("ROOM", "BASE", "DIR", "1400", "94300", "TICK")):
        print(f"  {i}:{line}")
