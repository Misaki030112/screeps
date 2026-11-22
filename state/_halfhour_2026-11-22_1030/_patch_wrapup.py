#!/usr/bin/env python3
from pathlib import Path

p = Path("/workspace/screeps/state/_halfhour_2026-11-22_1000/wrapup_write.py")
t = p.read_text()
nl = chr(10)
OLD, NEW = "_halfhour_2026-11-22_0930", "_halfhour_2026-11-22_1000"
t = t.replace(OLD, NEW)
t = t.replace("T0, T1 = 84410701, 84411400", "T0, T1 = 84411201, 84411900")
t = t.replace("JP_BASE = 84411400", "JP_BASE = 84411900")

old_gaps = "GAPS = [" + nl + '    ("gap_0914_0919", 84411221, 84411299),' + nl
new_gaps = "GAPS = [" + nl + '    ("gap_0941_0959", 84411621, 84411889),' + nl + '    ("gap_0914_0919", 84411221, 84411299),' + nl
if old_gaps not in t:
    raise SystemExit("GAPS head not found")
t = t.replace(old_gaps, new_gaps, 1)

old_holes = "HOLES = [" + nl + '    ("W47N8", 84409800),' + nl
new_holes = "HOLES = [" + nl + '    ("W45N7", 84411500),' + nl + '    ("W47N8", 84409800),' + nl
if old_holes not in t:
    raise SystemExit("HOLES head not found")
t = t.replace(old_holes, new_holes, 1)

t = t.replace(
    "    # First pass inserted=10151 is the real DB insert. confirm/retry2/late skipped (no targets).",
    "    # First pass inserted=12510 is the real DB insert. confirm recovered W47N7@84411800 inserted=385; retry2/late still 404 W45N7@84411500.",
)
t = t.replace("    inserted_first = 200", "    inserted_first = 12510")
t = t.replace("    inserted_confirm = 0", "    inserted_confirm = inserted_confirm_script")
t = t.replace("or 4.076", "or 4.149")

old_vars = '    w47n8_84409800 = holes["W47N8@84409800"]' + nl
new_vars = '    w45n7_84411500 = holes["W45N7@84411500"]' + nl + '    w47n8_84409800 = holes["W47N8@84409800"]' + nl
if old_vars not in t:
    raise SystemExit("hole vars head not found")
t = t.replace(old_vars, new_vars, 1)

old_fill = '    fill0914 = fill_txt(gaps["gap_0914_0919"])' + nl
new_fill = '    fill0941 = fill_txt(gaps["gap_0941_0959"])' + nl + '    fill0914 = fill_txt(gaps["gap_0914_0919"])' + nl
if old_fill not in t:
    raise SystemExit("fill0914 not found")
t = t.replace(old_fill, new_fill, 1)

# leftover 404 line: turn the plain string into an f-string with hole meta
old_leftover = '+ "NEW leftover official 404 this run: none. "'
new_leftover = (
    '+ f"NEW leftover official 404 this run: W45N7@84411500 '
    "(confirm 10:03:16, retry2 10:03:38, and late retry 10:03:56 still 404; "
    "listener {w45n7_84411500['distinct']}/100 range {w45n7_84411500['min']}..{w45n7_84411500['max']}; "
    "hole {w45n7_84411500['hole_ticks']} ticks {hole_range_txt(w45n7_84411500)}) "
    "-- not yet told; fold into the next 1h patrol USER_LOG. "
    'W47N7@84411800 was 404 in this first pass and recovered on confirm (inserted=385, 100/100); not a leftover. "'
)
if old_leftover not in t:
    raise SystemExit("NEW leftover none sentence not found")
t = t.replace(old_leftover, new_leftover, 1)

repls = [
    (
        "confirm at {confirm_at} gt={confirm_gt} skipped no targets inserted={inserted_confirm_script}. ",
        "confirm at {confirm_at} gt={confirm_gt} recovered W47N7@84411800 inserted={inserted_confirm_script}; still_404 W45N7@84411500. ",
    ),
    (
        "retry2 at {retry2_at} gt={retry2_gt} skipped no targets inserted={inserted_retry2_script}. ",
        "retry2 at {retry2_at} gt={retry2_gt} still_404 W45N7@84411500 inserted={inserted_retry2_script}. ",
    ),
    (
        "late retry at {late_at} gt={late_gt} skipped no targets inserted={inserted_late}. ",
        "late retry at {late_at} gt={late_gt} still_404 W45N7@84411500 inserted={inserted_late}. ",
    ),
    (
        "First pass 35/35 official GETs 200, missing_chunks=0. ",
        "First pass 33/35 official GETs 200, missing_chunks=2 W45N7@84411500 and W47N7@84411800. ",
    ),
    (
        "First pass started 2026-11-22 09:29:58 Asia/Hong_Kong and finished 09:30:41 (exit=0): ",
        "First pass started 2026-11-22 10:01:17 Asia/Hong_Kong and finished 10:02:04 (exit=0): ",
    ),
    (
        "inserted=200 already_in_db=25034, first-pass realign committed ts_realigned_first=0 (no rows over the 45s gate). ",
        "inserted=12510 already_in_db=10921, first-pass realign committed ts_realigned_first=0 (no rows over the 45s gate). ",
    ),
    (
        "tick_s_check chose live-anchor-best first 4.07557 already inside the 45s gate (over45=0), so no corrective realign. ",
        "tick_s_check chose live-anchor-best span_mean 4.11235 already inside the 45s gate (over45=0), so no corrective realign. ",
    ),
    (
        "09:00 half-hour already official-filled through 84410900 / just-published 84411000; the 09:18 patrol already official-filled 84410601..84411300 and just-published 84411300 through 84411400; this run is idempotent overlap plus just-published 84411400. ",
        "09:30 half-hour already official-filled through 84411300 / just-published 84411400; this run is idempotent overlap plus new official 84411500..84411800 and just-published 84411900. ",
    ),
    (
        "Just-published 84411400 was not in first pass (first pass ended at published 84411300 / reconstructed 84410701..84411400 at ",
        "Just-published 84411900 was not in first pass (first pass ended at published 84411800 / reconstructed 84411201..84411900 at ",
    ),
    (
        "game.time=84411454, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} ",
        "game.time=84411913, 33/35 200, missing_chunks=2). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} ",
    ),
    (
        "(later-raw later-mean {later}; first-pass realign committed ts_realigned=0; live-anchor-best first already inside 45s gate (over45=0), no corrective realign). ",
        "(later-raw later-mean {later}; first-pass realign committed ts_realigned=0; live-anchor-best span_mean already inside 45s gate (over45=0), no corrective realign). ",
    ),
    (
        "NEW box freeze observed this run: 盒子休眠 09:14:15-09:19:05 (283s; STATS 84411221..84411299, 79t; official-filled {fill0914}; listener auto-restart 09:19:08, python 2371673 started 09:19:17) -- already told in the just-delivered 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. ",
        "NEW box freeze this run: 盒子休眠 09:41:41-09:59:05 (1037s; STATS 84411621..84411889, 269t; official-filled {fill0941}; listener auto-restart 09:59:08, python 2385251 started 09:59:17) -- not yet told; fold into the next 1h patrol USER_LOG. ",
    ),
    (
        "Official fill re-verified this run: 09:14 STATS 84411221..84411299 79t official-filled {fill0914}; ",
        "Official fill re-verified this run: 09:41 STATS 84411621..84411889 269t official-filled {fill0941}; 09:14 STATS 84411221..84411299 79t official-filled {fill0914}; ",
    ),
    (
        "Single listener 2371673 since 09:19:17 after the 09:14 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
        "Single listener 2385251 since 09:59:17 after the 09:41 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
    ),
    (
        "first_pass game.time=84411454 published_bases=84410700..84411300 reconstructed=84410701..84411400 (700) ",
        "first_pass game.time=84411913 published_bases=84411200..84411800 reconstructed=84411201..84411900 (700) ",
    ),
    (
        "35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=25034 ts_realigned_first=0 (realign committed, no rows over 45s)",
        "33/35 200 missing_chunks=2 W45N7@84411500 W47N7@84411800 inserted_first={inserted_first} already_in_db=10921 ts_realigned_first=0 (realign committed, no rows over 45s)",
    ),
    (
        "confirm/retry2/late skipped no targets inserted=0 (leftover official 404s W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900 and older aged out of window start 84410701, already told in 08:28 patrol or earlier)",
        "confirm recovered W47N7@84411800 inserted=385; retry2/late still_404 W45N7@84411500 inserted=0 (NEW leftover official 404, not yet told). Already-told leftover official 404s W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900 and older aged out of window start 84411201, already told in 08:28 patrol or earlier",
    ),
    (
        "just_published 84411400 at {jp_at}",
        "just_published 84411900 at {jp_at}",
    ),
    (
        "ok_quiet=True new_official_404_untold=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0930 concurrent_patrol=already_delivered_0929_do_not_write_its_folder concurrent_12h_review=already_delivered_0833_do_not_write_its_folder",
        "ok_quiet=True new_official_404_untold=[W45N7@84411500] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[09:41:41-09:59:05 STATS 84411621..84411889 269t] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_1000 concurrent_patrol=already_delivered_0929_do_not_write_its_folder concurrent_12h_review=already_delivered_0833_do_not_write_its_folder",
    ),
    (
        '"new_official_404_untold": [],',
        '"new_official_404_untold": ["W45N7@84411500"],',
    ),
    (
        '"new_box_freeze_untold": [],',
        '"new_box_freeze_untold": ["09:41:41-09:59:05 STATS 84411621..84411889 269t"],',
    ),
    (
        '"first_pass_realign": "committed ts_realigned=0; tick_s_check no corrective when over45=0 (in_use=first 4.07557)",',
        '"first_pass_realign": "committed ts_realigned=0; tick_s_check no corrective when over45=0 (in_use=span_mean 4.11235)",',
    ),
]
for old, new in repls:
    if old not in t:
        raise SystemExit(f"literal not found: {old[:120]!r}")
    t = t.replace(old, new)

t = t.replace("aged out of window start 84410701", "aged out of window start 84411201")

old_after_new = (
    'f"NEW box freeze this run: 盒子休眠 09:41:41-09:59:05 (1037s; STATS 84411621..84411889, 269t; official-filled {fill0941}; listener auto-restart 09:59:08, python 2385251 started 09:59:17) -- not yet told; fold into the next 1h patrol USER_LOG. "'
    + nl
    + '        + f"盒子休眠 08:51:14-09:01:02 (581s; STATS 84410881..84411039, 159t; official-filled {fill0851}; listener auto-restart 09:01:06, python 2364487 started 09:01:15) -- already told in the 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. "'
)
new_after_new = (
    'f"NEW box freeze this run: 盒子休眠 09:41:41-09:59:05 (1037s; STATS 84411621..84411889, 269t; official-filled {fill0941}; listener auto-restart 09:59:08, python 2385251 started 09:59:17) -- not yet told; fold into the next 1h patrol USER_LOG. "'
    + nl
    + '        + f"盒子休眠 09:14:15-09:19:05 (283s; STATS 84411221..84411299, 79t; official-filled {fill0914}; listener auto-restart 09:19:08, python 2371673 started 09:19:17) -- already told in the 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. "'
    + nl
    + '        + f"盒子休眠 08:51:14-09:01:02 (581s; STATS 84410881..84411039, 159t; official-filled {fill0851}; listener auto-restart 09:01:06, python 2364487 started 09:01:15) -- already told in the 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. "'
)
if old_after_new not in t:
    raise SystemExit("post-new-freeze 08:51 sentence not found in expected place")
t = t.replace(old_after_new, new_after_new)

if "gaps 0914=" not in t:
    raise SystemExit("verify gaps line not found")
t = t.replace(
    "gaps 0914=",
    "gaps 0941={{ { {r: gaps['gap_0941_0959'][r]['fill'] for r in ROOMS} } }} 0914=",
    1,
)

p.write_text(t)
print("wrapup_write.py patched")

needles = {
    "_halfhour_2026-11-22_0930": False,
    "inserted_first = 200": False,
    "inserted_confirm = 0": False,
    "JP_BASE = 84411400": False,
    "T0, T1 = 84410701": False,
    "new_official_404_untold=[]": False,
    "new_box_freeze_untold=[]": False,
    "first_pass_source=this_halfhour_0930": False,
    "game.time=84411454": False,
    "Just-published 84411400 was not in first pass": False,
    "Single listener 2371673": False,
    "skipped no targets": False,
    "35/35": False,
    "fill0941": True,
    "gap_0941_0959": True,
    "JP_BASE = 84411900": True,
    "T0, T1 = 84411201, 84411900": True,
    "inserted_first = 12510": True,
    "inserted_confirm = inserted_confirm_script": True,
    "Single listener 2385251": True,
    "W45N7@84411500": True,
    "09:41:41-09:59:05": True,
    "span_mean 4.11235": True,
    "already_delivered_0929": True,
    "fold into the next 1h patrol USER_LOG": True,
    "w45n7_84411500": True,
}
ok = True
for needle, expect in needles.items():
    present = needle in t
    print(f"  {needle!r}: {present} (expect {expect})")
    if present != expect:
        ok = False
if not ok:
    raise SystemExit("sanity failed")
print("sanity ok")
