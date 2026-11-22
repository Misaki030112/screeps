#!/usr/bin/env python3
from pathlib import Path

p = Path("/workspace/screeps/state/_halfhour_2026-11-22_0930/wrapup_write.py")
t = p.read_text()
nl = chr(10)
OLD, NEW = "_halfhour_2026-11-22_0900", "_halfhour_2026-11-22_0930"
t = t.replace(OLD, NEW)
t = t.replace("T0, T1 = 84410301, 84411000", "T0, T1 = 84410701, 84411400")
t = t.replace("JP_BASE = 84411000", "JP_BASE = 84411400")

old_gaps = "GAPS = [" + nl + '    ("gap_0851_0901", 84410881, 84411039),' + nl
new_gaps = "GAPS = [" + nl + '    ("gap_0914_0919", 84411221, 84411299),' + nl + '    ("gap_0851_0901", 84410881, 84411039),' + nl
if old_gaps not in t:
    raise SystemExit("GAPS head not found")
t = t.replace(old_gaps, new_gaps, 1)

t = t.replace("    inserted_first = 9250", "    inserted_first = 200")
t = t.replace("or 4.101", "or 4.076")

old_fill = '    fill0851 = fill_txt(gaps["gap_0851_0901"])' + nl
new_fill = '    fill0914 = fill_txt(gaps["gap_0914_0919"])' + nl + '    fill0851 = fill_txt(gaps["gap_0851_0901"])' + nl
if old_fill not in t:
    raise SystemExit("fill0851 not found")
t = t.replace(old_fill, new_fill, 1)

# Replace unique contiguous string literals (they are separate Python concatenations).
repls = [
    (
        "First pass started 2026-11-22 09:03:26 Asia/Hong_Kong and finished 09:04:12 (exit=0): ",
        "First pass started 2026-11-22 09:29:58 Asia/Hong_Kong and finished 09:30:41 (exit=0): ",
    ),
    (
        "inserted=9250 already_in_db=15658, first-pass realign succeeded ts_realigned_first=23. ",
        "inserted=200 already_in_db=25034, first-pass realign committed ts_realigned_first=0 (no rows over the 45s gate). ",
    ),
    (
        "tick_s_check at 09:05:07 chose live-anchor-best later_raw 4.09961 already inside the 45s gate (over45=0), so no corrective realign. ",
        "tick_s_check chose live-anchor-best first 4.07557 already inside the 45s gate (over45=0), so no corrective realign. ",
    ),
    (
        "1h patrol already delivered 08:28 _patrol_2026-11-22_0818. 12h review already delivered ~08:33 t508s3618; do not re-tell or write its folder. ",
        "Concurrent 1h patrol already delivered 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell or write its folder. 12h review already delivered ~08:33 t508s3618; do not re-tell or write its folder. ",
    ),
    (
        "08:30 half-hour already official-filled through 84410500 / just-published 84410600; this run is idempotent overlap plus new official 84410700..84410900 and just-published 84411000. ",
        "09:00 half-hour already official-filled through 84410900 / just-published 84411000; the 09:18 patrol already official-filled 84410601..84411300 and just-published 84411300 through 84411400; this run is idempotent overlap plus just-published 84411400. ",
    ),
    (
        "and W47N8@84400100 aged out of window start 84410301 ",
        "and W47N8@84400100 aged out of window start 84410701 ",
    ),
    (
        "Just-published 84411000 was not in first pass (first pass ended at published 84410900 / reconstructed 84410301..84411000 at ",
        "Just-published 84411400 was not in first pass (first pass ended at published 84411300 / reconstructed 84410701..84411400 at ",
    ),
    (
        "game.time=84411068, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} ",
        "game.time=84411454, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} ",
    ),
    (
        "ts_realigned_first=23 corrective={corrective} ",
        "ts_realigned_first=0 corrective={corrective} ",
    ),
    (
        "(later-raw later-mean {later}; first-pass realign succeeded ts_realigned=23; live-anchor-best later_raw already inside 45s gate, no corrective realign; still_over_45s_vs_target=0 vs later_raw). ",
        "(later-raw later-mean {later}; first-pass realign committed ts_realigned=0; live-anchor-best first already inside 45s gate (over45=0), no corrective realign). ",
    ),
    (
        "first_pass game.time=84411068 published_bases=84410300..84410900 reconstructed=84410301..84411000 (700) ",
        "first_pass game.time=84411454 published_bases=84410700..84411300 reconstructed=84410701..84411400 (700) ",
    ),
    (
        "35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=15658 ts_realigned_first=23 (realign succeeded)",
        "35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=25034 ts_realigned_first=0 (realign committed, no rows over 45s)",
    ),
    (
        "just_published 84411000 at {jp_at}",
        "just_published 84411400 at {jp_at}",
    ),
    (
        "Single listener 2364487 since 09:01:15 after the 08:51 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
        "Single listener 2371673 since 09:19:17 after the 09:14 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
    ),
    (
        "Official fill re-verified this run: 08:51 STATS 84410881..84411039 159t official-filled {fill0851}; ",
        "Official fill re-verified this run: 09:14 STATS 84411221..84411299 79t official-filled {fill0914}; 08:51 STATS 84410881..84411039 159t official-filled {fill0851}; ",
    ),
    (
        "new_box_freeze_untold=[08:51:14-09:01:02 STATS 84410881..84411039 159t]",
        "new_box_freeze_untold=[]",
    ),
    (
        "first_pass_source=this_halfhour_0900 concurrent_patrol=none concurrent_12h_review=already_delivered_0833_do_not_write_its_folder",
        "first_pass_source=this_halfhour_0930 concurrent_patrol=already_delivered_0929_do_not_write_its_folder concurrent_12h_review=already_delivered_0833_do_not_write_its_folder",
    ),
    (
        '"new_box_freeze_untold": ["08:51:14-09:01:02 STATS 84410881..84411039 159t"],',
        '"new_box_freeze_untold": [],',
    ),
    (
        '"concurrent_patrol": None,',
        '"concurrent_patrol": "already_delivered_0929_do_not_write_its_folder",',
    ),
    (
        '"first_pass_realign": "succeeded ts_realigned=23; tick_s_check no corrective, over45 vs later_raw=0",',
        '"first_pass_realign": "committed ts_realigned=0; tick_s_check no corrective when over45=0 (in_use=first 4.07557)",',
    ),
]
for old, new in repls:
    if old not in t:
        raise SystemExit(f"literal not found: {old[:80]!r}")
    t = t.replace(old, new)

t = t.replace("aged out of window start 84410301", "aged out of window start 84410701")

# NEW box freeze f-string (contiguous in source)
old_freeze = (
    'f"NEW box freeze this run: 盒子休眠 08:51:14-09:01:02 (581s; STATS 84410881..84411039, 159t; official-filled {fill0851}; listener auto-restart 09:01:06, python 2364487 started 09:01:15) -- not yet told; fold into the next 1h patrol USER_LOG. "'
)
new_freeze = (
    'f"NEW box freeze observed this run: 盒子休眠 09:14:15-09:19:05 (283s; STATS 84411221..84411299, 79t; official-filled {fill0914}; listener auto-restart 09:19:08, python 2371673 started 09:19:17) -- already told in the just-delivered 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. "'
    + nl
    + '        + f"盒子休眠 08:51:14-09:01:02 (581s; STATS 84410881..84411039, 159t; official-filled {fill0851}; listener auto-restart 09:01:06, python 2364487 started 09:01:15) -- already told in the 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. "'
    + nl
    + '        + f"_patrol_2026-11-22_0918 USER_LOG (delivered 09:29) already includes (treat as already told; do not re-tell): 盒子休眠 08:51:14-09:01:02 and 09:14:15-09:19:05; W47N7@84411200 first-pass 404 recovered on confirm (no leftover). "'
)
if old_freeze not in t:
    raise SystemExit("old NEW box freeze f-string not found")
t = t.replace(old_freeze, new_freeze)

# After the leftover 404 sentence that ends '...and were not retried this pass ... do not re-tell). '
# insert a W47N7 recovered note as its own concatenated string if possible.
marker = "and were not retried this pass (already told in the 08:28 _patrol_2026-11-22_0818 or earlier USER_LOG; do not re-tell). "
insert_after = (
    marker
    + '"'
    + nl
    + '        + "W47N7@84411200 was 404 in the 09:18 patrol first pass and already recovered on that patrol confirm (this first pass 200); not a leftover. '
)
if marker not in t:
    raise SystemExit("aged-out leftover sentence not found for W47N7 note")
if "W47N7@84411200 was 404 in the 09:18 patrol first pass" not in t:
    t = t.replace(marker, insert_after, 1)

# verify gaps line: add 0914 before 0851
if "gaps 0851=" not in t:
    raise SystemExit("verify gaps line not found")
t = t.replace(
    "gaps 0851=",
    "gaps 0914={{ { {r: gaps['gap_0914_0919'][r]['fill'] for r in ROOMS} } }} 0851=",
    1,
)

old_told = "already_told by _patrol_2026-11-22_0818 USER_LOG (do not re-tell): 盒子休眠 07:44:22-08:02:42; leftover official 404 W47N8@84409800. "
new_told = (
    "already_told by _patrol_2026-11-22_0918 USER_LOG (do not re-tell): 盒子休眠 08:51:14-09:01:02 and 09:14:15-09:19:05; W47N7@84411200 first-pass 404 recovered on confirm (no leftover). "
    "Already told by _patrol_2026-11-22_0818 USER_LOG (do not re-tell): 盒子休眠 07:44:22-08:02:42; leftover official 404 W47N8@84409800. "
)
if old_told not in t:
    raise SystemExit("already_told verify sentence not found")
t = t.replace(old_told, new_told)

p.write_text(t)
print("wrapup_write.py patched")

needles = {
    "_halfhour_2026-11-22_0900": False,
    "inserted_first = 9250": False,
    "JP_BASE = 84411000": False,
    "T0, T1 = 84410301": False,
    "new_box_freeze_untold=[08:51": False,
    "concurrent_patrol=none": False,
    "ts_realigned_first=23": False,
    "game.time=84411068": False,
    "Just-published 84411000 was not in first pass": False,
    "fold into the next 1h patrol USER_LOG": False,
    "fill0914": True,
    "gap_0914_0919": True,
    "JP_BASE = 84411400": True,
    "T0, T1 = 84410701, 84411400": True,
    "already_delivered_0929": True,
    "inserted_first = 200": True,
    "Single listener 2371673": True,
    "tick_s_check chose live-anchor-best first 4.07557": True,
    "W47N7@84411200 was 404 in the 09:18 patrol first pass": True,
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
