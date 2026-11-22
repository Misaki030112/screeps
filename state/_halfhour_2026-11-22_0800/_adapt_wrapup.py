#!/usr/bin/env python3
from pathlib import Path

src = Path("/workspace/screeps/state/_halfhour_2026-11-22_0730/wrapup_write.py")
dst = Path("/workspace/screeps/state/_halfhour_2026-11-22_0800/wrapup_write.py")
NL = chr(10)
t = src.read_text()
t = t.replace("_halfhour_2026-11-22_0730", "_halfhour_2026-11-22_0800")
t = t.replace("T0, T1 = 84409001, 84409700", "T0, T1 = 84409501, 84410200")
t = t.replace("JP_BASE = 84409700", "JP_BASE = 84410200")

old_gaps = (
    "GAPS = [" + NL
    + '    ("gap_0720_0726", 84409551, 84409649),' + NL
)
new_gaps = (
    "GAPS = [" + NL
    + '    ("gap_0744_0802", 84409901, 84410189),' + NL
    + '    ("gap_0720_0726", 84409551, 84409649),' + NL
)
if old_gaps not in t:
    raise SystemExit("GAPS anchor not found")
t = t.replace(old_gaps, new_gaps, 1)

old_holes = (
    "HOLES = [" + NL
    + '    ("W46N8", 84408300),' + NL
)
new_holes = (
    "HOLES = [" + NL
    + '    ("W47N8", 84409800),' + NL
    + '    ("W46N8", 84408300),' + NL
)
if old_holes not in t:
    raise SystemExit("HOLES anchor not found")
t = t.replace(old_holes, new_holes, 1)

old_var = '    w46n8_84408300 = holes["W46N8@84408300"]' + NL
new_var = '    w47n8_84409800 = holes["W47N8@84409800"]' + NL + old_var
if old_var not in t:
    raise SystemExit("hole var anchor not found")
t = t.replace(old_var, new_var, 1)

old_fill = '    fill0720 = fill_txt(gaps["gap_0720_0726"])' + NL
new_fill = '    fill0744 = fill_txt(gaps["gap_0744_0802"])' + NL + old_fill
if old_fill not in t:
    raise SystemExit("fill0720 not found")
t = t.replace(old_fill, new_fill, 1)

t = t.replace("inserted_first = 300", "inserted_first = 13527")
t = t.replace("or 3.959", "or 4.173")
t = t.replace("window start 84409001", "window start 84409501")

old_conf = (
    '        + f"confirm at {confirm_at} gt={confirm_gt} skipped no targets (missing_chunks=0; leftover official 404s aged out of window start 84409501). "'
    + NL
    + '        + f"retry2 at {retry2_at} gt={retry2_gt} skipped no targets. "'
    + NL
    + '        + f"late retry at {late_at} gt={late_gt} skipped no targets inserted={inserted_late}. "'
    + NL
    + '        + "First pass 35/35 official GETs 200, missing_chunks=0. "'
)
new_conf = (
    '        + f"confirm at {confirm_at} gt={confirm_gt} still_404 W47N8@84409800 inserted={inserted_confirm_script}. "'
    + NL
    + '        + f"retry2 at {retry2_at} gt={retry2_gt} still_404 W47N8@84409800 inserted={inserted_retry2_script}. "'
    + NL
    + '        + f"late retry at {late_at} gt={late_gt} still_404 W47N8@84409800 inserted={inserted_late}. "'
    + NL
    + '        + "First pass 34/35 official GETs 200, missing_chunks=1 W47N8@84409800. "'
)
if old_conf not in t:
    raise SystemExit("confirm narrative not found")
t = t.replace(old_conf, new_conf, 1)

t = t.replace(
    "First pass completed cleanly at 2026-11-22 07:35:35 Asia/Hong_Kong (exit=0, no abort, started 07:34:55). ",
    "First pass completed cleanly at 2026-11-22 08:05:55 Asia/Hong_Kong (exit=0, no abort, started 08:05:13). ",
)
t = t.replace(
    "Concurrent 1h patrol _patrol_2026-11-22_0725 is still running (started 07:25:55; last delivered 06:44 t508s3614 _patrol_2026-11-22_0625). Do not write its patrol folder. ",
    "No concurrent 1h patrol this run (last delivered 07:35 _patrol_2026-11-22_0725; next ~08:25). A 12h review may start around 08:00; do not write its folder. ",
)
t = t.replace(
    "07:00 half-hour already official-filled through 84409300 / just-published 84409300; this run is idempotent overlap plus new official 84409400..84409600 and just-published 84409700. ",
    "07:30 half-hour already official-filled through 84409700 / just-published 84409700; this run is idempotent overlap plus new official 84409800..84410100 and just-published 84410200. ",
)
t = t.replace(
    "and were not retried this pass (already told in the 06:44 patrol t508s3614 or earlier USER_LOG; do not re-tell). ",
    "and were not retried this pass (already told in the 07:35 _patrol_2026-11-22_0725 or earlier USER_LOG; do not re-tell). ",
)
t = t.replace(
    "Just-published 84409700 was not in first pass (first pass ended at published 84409600 / reconstructed 84409001..84409700 at ",
    "Just-published 84410200 was not in first pass (first pass ended at published 84410100 / reconstructed 84409501..84410200 at ",
)
t = t.replace(
    "game.time=84409768, 35/35 200, missing_chunks=0). GET at ",
    "game.time=84410215, 34/35 200, missing_chunks=1 W47N8@84409800). GET at ",
)

old_tick = (
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=15602 corrective={corrective} "' + NL
    + '        + f"(later-mean {later} worse than live-anchor-best {tick_s_label} {tick_s_in_use}; first-pass realign moved 15602; corrective first realign nfix={corrective}; still_over_45s_vs_target=0). "'
)
new_tick = (
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=11563 corrective={corrective} "' + NL
    + '        + f"(later-mean {later} worse than live-anchor-best {tick_s_label} {tick_s_in_use}; first-pass realign moved 11563; no corrective realign; still_over_45s_vs_target=0 vs prev_later). "'
)
if old_tick not in t:
    idx = t.find("ts_realigned_first=")
    raise SystemExit("tick_s sentence not found: " + repr(t[idx:idx+500] if idx>=0 else "missing"))
t = t.replace(old_tick, new_tick, 1)

# NEW leftover + NEW freeze. Use chr(39) to avoid quote nesting in this adapter if needed.
dq = '"'
old_new = (
    '        + "NEW leftover official 404 this run: none. "' + NL
    + '        + "NEW short WS this run: none. "' + NL
    + '        + f"NEW box freeze this run: 盒子休眠 07:20:32-07:26:28 (356s, already healed; STATS 84409551..84409649, 99t; official-filled {fill0720}; listener auto-restart 07:26:31, python 2325173 started 07:26:41) -- not yet told, fold into the next 1h patrol (concurrent _patrol_2026-11-22_0725 may also see it). "' + NL
    + '        + f"Still untold from the quiet 07:00 backfill (unless the concurrent 07:25 patrol already tells it): 盒子休眠 06:50:03-07:02:08 (725s, already healed; STATS 84409111..84409299, 189t; official-filled {fill0650}; listener auto-restart 07:02:11). "' + NL
    + '        + f"_patrol_2026-11-22_0625 USER_LOG (delivered 06:44 as t508s3614) already includes (treat as already told; do not re-tell): "' + NL
)
new_new = (
    "        + f" + dq + "NEW leftover official 404 this run: W47N8@84409800 (confirm 08:07:21 gt=84410246, retry2 08:09:01 gt=84410270, late 08:09:32 gt=84410278 still 404, inserted=0; listener {w47n8_84409800['distinct']}/100 range {w47n8_84409800['min']}..{w47n8_84409800['max']}; hole {w47n8_84409800['hole_ticks']} ticks {hole_range_txt(w47n8_84409800)}) -- not yet told, fold into the next 1h patrol. " + dq + NL
    + '        + "NEW short WS this run: none. "' + NL
    + '        + f"NEW box freeze this run: 盒子休眠 07:44:22-08:02:42 (1093s, already healed; STATS 84409901..84410189, 289t; official-filled {fill0744}; listener auto-restart 08:02:45, python 2336374 started 08:02:54) -- not yet told, fold into the next 1h patrol. "' + NL
    + '        + f"_patrol_2026-11-22_0725 USER_LOG (delivered 07:35) already includes (treat as already told; do not re-tell): "' + NL
    + '        + f"盒子休眠 07:20:32-07:26:28 (356s; STATS 84409551..84409649, 99t; official-filled {fill0720}; listener auto-restart 07:26:31, python 2325173 started 07:26:41); "' + NL
    + '        + f"盒子休眠 06:50:03-07:02:08 (725s; STATS 84409111..84409299, 189t; official-filled {fill0650}; listener auto-restart 07:02:11); "' + NL
    + '        + "leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. "' + NL
    + '        + f"_patrol_2026-11-22_0625 USER_LOG (delivered 06:44 as t508s3614) already includes (treat as already told; do not re-tell): "' + NL
)
if old_new not in t:
    idx = t.find("NEW leftover official 404 this run")
    raise SystemExit("NEW block not found: " + repr(t[idx:idx+800] if idx>=0 else "missing"))
t = t.replace(old_new, new_new, 1)

t = t.replace(
    "Official fill re-verified this run: 07:20 STATS 84409551..84409649 99t official-filled {fill0720}; ",
    "Official fill re-verified this run: 07:44 STATS 84409901..84410189 289t official-filled {fill0744}; 07:20 STATS 84409551..84409649 99t official-filled {fill0720}; ",
)
t = t.replace(
    "Single listener 2325173 since 07:26:41 after the 07:20 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
    "Single listener 2336374 since 08:02:54 after the 07:44 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
)

t = t.replace(
    "first_pass game.time=84409768 published_bases=84409000..84409600 reconstructed=84409001..84409700 (700) ",
    "first_pass game.time=84410215 published_bases=84409500..84410100 reconstructed=84409501..84410200 (700) ",
)
t = t.replace(
    "35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=26735 ts_realigned_first=15602",
    "34/35 200 missing_chunks=1 W47N8@84409800 inserted_first={inserted_first} already_in_db=11546 ts_realigned_first=11563",
)
t = t.replace(
    "confirm/retry2/late skipped no targets (missing_chunks=0; leftover official 404s W46N8@84408300 / W47N8@84408300 / W47N7@84407900 and older aged out of window start 84409501, already told in 06:44 patrol t508s3614 or earlier)",
    "confirm/retry2/late still_404 W47N8@84409800 inserted=0 (leftover official 404s W46N8@84408300 / W47N8@84408300 / W47N7@84407900 and older aged out of window start 84409501, already told in 07:35 patrol or earlier)",
)
t = t.replace("just_published 84409700 at", "just_published 84410200 at")

if "gaps 0720=" not in t:
    raise SystemExit("gaps 0720= not found")
t = t.replace(
    "gaps 0720=",
    "gaps 0744={{ { {r: gaps['gap_0744_0802'][r]['fill'] for r in ROOMS} } }} 0720=",
    1,
)

t = t.replace(
    "already_told by _patrol_2026-11-22_0625 USER_LOG t508s3614 (do not re-tell): 盒子休眠 05:52:44-06:04:12 and 06:21:56-06:26:26; leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. Already told by _patrol_2026-11-22_0522 USER_LOG (do not re-tell): 盒子休眠 04:41:06-04:59:17 and 05:17:11-05:23:17; 监听短中断 05:25:19-05:27:20; leftover official 404 W46N8@84407000 and W45N8@84407700. Older already-told freezes through 04:18 / 03:47 / 02:44 and leftover official 404s through W45N8@84406400 / W46N8@84406600 / W46N8@84406700 and earlier.",
    "already_told by _patrol_2026-11-22_0725 USER_LOG (do not re-tell): 盒子休眠 07:20:32-07:26:28 and 06:50:03-07:02:08; leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. Already told by _patrol_2026-11-22_0625 USER_LOG t508s3614 (do not re-tell): 盒子休眠 05:52:44-06:04:12 and 06:21:56-06:26:26. Already told by _patrol_2026-11-22_0522 USER_LOG (do not re-tell): 盒子休眠 04:41:06-04:59:17 and 05:17:11-05:23:17; 监听短中断 05:25:19-05:27:20; leftover official 404 W46N8@84407000 and W45N8@84407700. Older already-told freezes through 04:18 / 03:47 / 02:44 and leftover official 404s through W45N8@84406400 / W46N8@84406600 / W46N8@84406700 and earlier.",
)

t = t.replace(
    "ok_quiet=True new_official_404_untold=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=['07:20:32-07:26:28'] still_untold_freeze_from_0700=['06:50:03-07:02:08'] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0730 concurrent_patrol=_patrol_2026-11-22_0725",
    "ok_quiet=True new_official_404_untold=['W47N8@84409800'] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=['07:44:22-08:02:42'] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0800 concurrent_patrol=none",
)

old_snap = (
    '"new_official_404_untold": [],' + NL
    + '        "still_untold_from_0600": [],' + NL
    + '        "still_untold_from_0530": [],' + NL
    + '        "new_box_freeze_untold": ["07:20:32-07:26:28"],' + NL
    + '        "still_untold_freeze_from_0700": ["06:50:03-07:02:08"],' + NL
    + '        "still_untold_freeze_from_0600": [],' + NL
    + '        "new_short_ws_untold": [],' + NL
    + '        "concurrent_patrol": "_patrol_2026-11-22_0725",'
)
new_snap = (
    '"new_official_404_untold": ["W47N8@84409800"],' + NL
    + '        "still_untold_from_0730": [],' + NL
    + '        "still_untold_from_0700": [],' + NL
    + '        "still_untold_from_0600": [],' + NL
    + '        "still_untold_from_0530": [],' + NL
    + '        "new_box_freeze_untold": ["07:44:22-08:02:42"],' + NL
    + '        "still_untold_freeze_from_0730": [],' + NL
    + '        "still_untold_freeze_from_0700": [],' + NL
    + '        "still_untold_freeze_from_0600": [],' + NL
    + '        "new_short_ws_untold": [],' + NL
    + '        "concurrent_patrol": None,'
)
if old_snap not in t:
    idx = t.find('"new_official_404_untold"')
    raise SystemExit("snap block not found: " + repr(t[idx:idx+700] if idx>=0 else "missing"))
t = t.replace(old_snap, new_snap, 1)

dst.write_text(t)
print("wrote", dst, "bytes", len(t))

needles = [
    "T0, T1 = 84409501, 84410200",
    "JP_BASE = 84410200",
    "gap_0744_0802",
    "fill0744",
    '("W47N8", 84409800)',
    "w47n8_84409800",
    "inserted_first = 13527",
    "_halfhour_2026-11-22_0800",
    "07:44:22-08:02:42",
    "W47N8@84409800",
    "84410200 was not in first pass",
    "ts_realigned_first=11563",
    "2336374",
    "window start 84409501",
    "gaps 0744=",
    "first_pass_source=this_halfhour_0800",
    "concurrent_patrol=none",
    "07:35 _patrol_2026-11-22_0725",
    "new_official_404_untold=['W47N8@84409800']",
]
for n in needles:
    print(("OK " if n in t else "MISSING "), n)
for bad in [
    "_halfhour_2026-11-22_0730",
    "JP_BASE = 84409700",
    "inserted_first = 300",
    "ts_realigned_first=15602",
    "T0, T1 = 84409001, 84409700",
    "new_box_freeze_untold=['07:20:32-07:26:28']",
]:
    if bad in t:
        print("WARN leftover", bad)
