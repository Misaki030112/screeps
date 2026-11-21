#!/usr/bin/env python3
from pathlib import Path
import ast

SRC = Path("/workspace/screeps/state/_halfhour_2026-11-21_1700")
DST = Path("/workspace/screeps/state/_halfhour_2026-11-21_1730")

t = (SRC / "backfill_late_retry_w45n7.py").read_text()
t = t.replace(str(SRC), str(DST)).replace("_halfhour_2026-11-21_1700", "_halfhour_2026-11-21_1730")
(DST / "backfill_late_retry_w45n7.py").write_text(t)
print("wrote late_retry")

t = (SRC / "post_counts.py").read_text()
t = t.replace(str(SRC), str(DST)).replace("_halfhour_2026-11-21_1700", "_halfhour_2026-11-21_1730")
t = t.replace("JUST_BASE = 84397400", "JUST_BASE = 84397800")
t = t.replace("WIN_TMIN, WIN_TMAX = 84396701, 84397400", "WIN_TMIN, WIN_TMAX = 84397101, 84397800")

start = t.find("GAPS = [")
end = t.find("]\n\nHK", start)
if start < 0 or end < 0:
    raise SystemExit(f"GAPS block not found start={start} end={end}")

new_gaps = """GAPS = [
    ("gap_1648_1704", 84397201, 84397439),  # already told by the delivered 17:33 1h patrol (box freeze 16:48:46-17:04:41, 954s); STATS 239t; official-filled four rooms 239/239, W45N7 200/239 missing tail 84397401..84397439 because of leftover official 404 W45N7@84397400; listener auto-restart 17:04:44. Still in official window start 84397101.
    ("gap_1723", 84397671, 84397699),  # already told by the delivered 17:33 1h patrol (short WS ping/pong 17:23:22, not a box freeze); 29t; official-filled all five 29/29; listener restart 17:23:22, python 1983656 started 17:23:31. Still in official window start 84397101.
    ("gap_1616_1619", 84396751, 84396799),  # already told by the delivered 16:32/17:33 1h patrols (box freeze 16:16:43-16:19:24, 161s); ages out of official window start 84397101.
    ("gap_1622", 84396821, 84396839),  # already told by the delivered 16:32/17:33 1h patrols (short WS ping/pong 16:22:02, not a box freeze); ages out of official window start 84397101.
    ("gap_1547_1558", 84396331, 84396509),  # already told (box freeze 15:47:29-15:58:30, 655s); ages out
    ("gap_1514_1519", 84395871, 84395959),  # already told (box freeze 15:14:38-15:19:30, 292s); ages out
    ("gap_1440_1456", 84395401, 84395639),  # already told (box freeze 14:40:53-14:56:54); leftover official 404 W47N7@84395600 already told; ages out
    ("gap_1415_1423", 84395061, 84395179),  # already told (box freeze 14:15:50-14:23:29); leftover official 404 W47N8@84395100 already told; ages out
    ("gap_1349_1356", 84394681, 84394809),  # already told (box freeze 13:49:01-13:56:56); ages out
    ("gap_1309_1321", 84394131, 84394299),  # already told (box freeze 13:09:46-13:21:14); ages out
    ("gap_1248_1257", 84393831, 84393969),  # already told (box freeze 12:48:14-12:57:17); ages out
    ("gap_1230_1235", 84393581, 84393659),  # already told (box freeze 12:30:42-12:35:35); ages out
    ("gap_1218", 84393391, 84393419),  # already told short WS gap 12:18; ages out
    ("gap_1210", 84393291, 84393319),  # already told short WS gap 12:10; ages out
    ("gap_1149_1157", 84393001, 84393129),  # already told (box freeze 11:49:12-11:57:31); ages out
    ("gap_1119_1120", 84392571, 84392609),  # already told (box freeze 11:19:06-11:20:43); leftover official 404 W45N8@84392600 already told; ages out
    ("gap_1111_1113", 84392471, 84392499),  # already told short WS gap 11:12; ages out
]
"""
t = t[:start] + new_gaps + t[end + 1 :]
(DST / "post_counts.py").write_text(t)
ast.parse(t)
ast.parse((DST / "backfill_late_retry_w45n7.py").read_text())
print("wrote post_counts, syntax ok")
for ln in t.splitlines():
    if "JUST_BASE" in ln or "WIN_TMIN" in ln or ln.strip().startswith('("gap_'):
        print(ln)
