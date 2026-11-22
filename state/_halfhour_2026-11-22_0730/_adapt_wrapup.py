#!/usr/bin/env python3
from pathlib import Path

src = Path("/workspace/screeps/state/_halfhour_2026-11-22_0700/wrapup_write.py")
dst = Path("/workspace/screeps/state/_halfhour_2026-11-22_0730/wrapup_write.py")
NL = chr(10)
t = src.read_text()
t = t.replace("_halfhour_2026-11-22_0700", "_halfhour_2026-11-22_0730")
t = t.replace("T0, T1 = 84408601, 84409300", "T0, T1 = 84409001, 84409700")
t = t.replace("JP_BASE = 84409300", "JP_BASE = 84409700")

old_gaps = (
    "GAPS = [" + NL
    + '    ("gap_0650_0702", 84409111, 84409299),' + NL
    + '    ("gap_0621_0626", 84408691, 84408779),' + NL
)
new_gaps = (
    "GAPS = [" + NL
    + '    ("gap_0720_0726", 84409551, 84409649),' + NL
    + '    ("gap_0650_0702", 84409111, 84409299),' + NL
    + '    ("gap_0621_0626", 84408691, 84408779),' + NL
)
if old_gaps not in t:
    raise SystemExit("GAPS anchor not found")
t = t.replace(old_gaps, new_gaps, 1)

old_fill = '    fill0650 = fill_txt(gaps["gap_0650_0702"])' + NL
new_fill = '    fill0720 = fill_txt(gaps["gap_0720_0726"])' + NL + old_fill
if old_fill not in t:
    raise SystemExit("fill0650 not found")
t = t.replace(old_fill, new_fill, 1)

t = t.replace("inserted_first = 10151", "inserted_first = 300")
t = t.replace("or 4.051", "or 3.959")
t = t.replace("window start 84408601", "window start 84409001")
t = t.replace(
    "first_pass game.time=84409335 published_bases=84408600..84409200 reconstructed=84408601..84409300 (700) ",
    "first_pass game.time=84409768 published_bases=84409000..84409600 reconstructed=84409001..84409700 (700) ",
)
t = t.replace("already_in_db=13284 ts_realigned_first=1316", "already_in_db=26735 ts_realigned_first=15602")
t = t.replace("just_published 84409300 at", "just_published 84409700 at")
t = t.replace(
    "First pass completed cleanly at 2026-11-22 07:06:04 Asia/Hong_Kong (exit=0, no abort). ",
    "First pass completed cleanly at 2026-11-22 07:35:35 Asia/Hong_Kong (exit=0, no abort, started 07:34:55). ",
)
t = t.replace(
    "No concurrent 1h patrol this run (last delivered 06:44 t508s3614 _patrol_2026-11-22_0625; next ~07:25). Do not write a patrol folder. ",
    "Concurrent 1h patrol _patrol_2026-11-22_0725 is still running (started 07:25:55; last delivered 06:44 t508s3614 _patrol_2026-11-22_0625). Do not write its patrol folder. ",
)
t = t.replace(
    "06:30 half-hour already official-filled through 84408800 / just-published 84408900; this run is idempotent overlap plus new official 84409000..84409200 and just-published 84409300. ",
    "07:00 half-hour already official-filled through 84409300 / just-published 84409300; this run is idempotent overlap plus new official 84409400..84409600 and just-published 84409700. ",
)
t = t.replace(
    "Just-published 84409300 was not in first pass (first pass ended at published 84409200 / reconstructed 84408601..84409300 at ",
    "Just-published 84409700 was not in first pass (first pass ended at published 84409600 / reconstructed 84409001..84409700 at ",
)
t = t.replace(
    "game.time=84409335, 35/35 200, missing_chunks=0). GET at ",
    "game.time=84409768, 35/35 200, missing_chunks=0). GET at ",
)

old_tick = (
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=1316 corrective={corrective} "' + NL
    + '        + f"(later-mean {later} slightly worse than live-anchor-best {tick_s_label}; first-pass realign moved 1316; no corrective realign; still_over_45s_vs_target=0). "'
)
new_tick = (
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=15602 corrective={corrective} "' + NL
    + '        + f"(later-mean {later} worse than live-anchor-best {tick_s_label} {tick_s_in_use}; first-pass realign moved 15602; corrective first realign nfix={corrective}; still_over_45s_vs_target=0). "'
)
if old_tick not in t:
    idx = t.find("ts_realigned_first=")
    raise SystemExit("tick_s sentence not found: " + repr(t[idx:idx + 450] if idx >= 0 else "missing"))
t = t.replace(old_tick, new_tick, 1)

old_newfreeze = (
    '        + f"NEW box freeze this run: 盒子休眠 06:50:03-07:02:08 (725s, already healed; STATS 84409111..84409299, 189t; official-filled {fill0650}; listener auto-restart 07:02:11, python 2315680 started 07:02:21) -- not yet told, fold into the next 1h patrol. "'
)
new_newfreeze = (
    '        + f"NEW box freeze this run: 盒子休眠 07:20:32-07:26:28 (356s, already healed; STATS 84409551..84409649, 99t; official-filled {fill0720}; listener auto-restart 07:26:31, python 2325173 started 07:26:41) -- not yet told, fold into the next 1h patrol (concurrent _patrol_2026-11-22_0725 may also see it). "' + NL
    + '        + f"Still untold from the quiet 07:00 backfill (unless the concurrent 07:25 patrol already tells it): 盒子休眠 06:50:03-07:02:08 (725s, already healed; STATS 84409111..84409299, 189t; official-filled {fill0650}; listener auto-restart 07:02:11). "'
)
if old_newfreeze not in t:
    idx = t.find("NEW box freeze")
    raise SystemExit("new freeze sentence not found: " + repr(t[idx:idx + 450] if idx >= 0 else "missing"))
t = t.replace(old_newfreeze, new_newfreeze, 1)

t = t.replace(
    "Official fill re-verified this run: 06:50 STATS 84409111..84409299 189t official-filled {fill0650}; ",
    "Official fill re-verified this run: 07:20 STATS 84409551..84409649 99t official-filled {fill0720}; 06:50 STATS 84409111..84409299 189t official-filled {fill0650}; ",
)
t = t.replace(
    "Single listener 2315680 since 07:02:21 after the 06:50 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
    "Single listener 2325173 since 07:26:41 after the 07:20 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
)

# Simple prefix insert in the verify gaps line
if "gaps 0650=" not in t:
    raise SystemExit("gaps 0650= not found")
t = t.replace(
    "gaps 0650=",
    "gaps 0720={{ { {r: gaps['gap_0720_0726'][r]['fill'] for r in ROOMS} } }} 0650=",
    1,
)

t = t.replace(
    "ok_quiet=True new_official_404_untold=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=['06:50:03-07:02:08'] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0700 concurrent_patrol=none",
    "ok_quiet=True new_official_404_untold=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=['07:20:32-07:26:28'] still_untold_freeze_from_0700=['06:50:03-07:02:08'] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0730 concurrent_patrol=_patrol_2026-11-22_0725",
)

old_snap = (
    '"new_box_freeze_untold": ["06:50:03-07:02:08"],' + NL
    + '        "still_untold_freeze_from_0600": [],' + NL
    + '        "new_short_ws_untold": [],' + NL
    + '        "concurrent_patrol": None,'
)
new_snap = (
    '"new_box_freeze_untold": ["07:20:32-07:26:28"],' + NL
    + '        "still_untold_freeze_from_0700": ["06:50:03-07:02:08"],' + NL
    + '        "still_untold_freeze_from_0600": [],' + NL
    + '        "new_short_ws_untold": [],' + NL
    + '        "concurrent_patrol": "_patrol_2026-11-22_0725",'
)
if old_snap not in t:
    raise SystemExit("snap block not found")
t = t.replace(old_snap, new_snap, 1)

dst.write_text(t)
print("wrote", dst, "bytes", len(t))

needles = [
    "T0, T1 = 84409001, 84409700",
    "JP_BASE = 84409700",
    "gap_0720_0726",
    "fill0720",
    "inserted_first = 300",
    "_halfhour_2026-11-22_0730",
    "07:20:32-07:26:28",
    "06:50:03-07:02:08",
    "_patrol_2026-11-22_0725",
    "84409700 was not in first pass",
    "ts_realigned_first=15602",
    "2325173",
    "window start 84409001",
    "corrective first realign nfix=",
    "gaps 0720=",
    "still_untold_freeze_from_0700",
]
for n in needles:
    print(("OK " if n in t else "MISSING "), n)
for bad in [
    "_halfhour_2026-11-22_0700",
    "JP_BASE = 84409300",
    "inserted_first = 10151",
    "ts_realigned_first=1316",
    "python 2315680",
]:
    if bad in t:
        print("WARN leftover", bad)
