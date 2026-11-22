#!/usr/bin/env python3
from pathlib import Path

p = Path("/workspace/screeps/state/_halfhour_2026-11-22_1700/wrapup_write.py")
t = p.read_text()

def must_replace(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {n}")
    t = t.replace(old, new, 1)
    print("ok", label)

must_replace("T0, T1 = 84416801, 84417500", "T0, T1 = 84417201, 84417900", "T0T1")
must_replace("JP_BASE = 84417500", "JP_BASE = 84417900", "JP_BASE")
must_replace(
    '    ("gap_1615_1622", 84417291, 84417409),\n',
    '    ("gap_1644_1659", 84417731, 84417949),\n    ("gap_1615_1622", 84417291, 84417409),\n',
    "GAPS add 1644",
)
must_replace("    inserted_first = 100\n", "    inserted_first = 10327\n", "inserted_first")
must_replace(
    '    first = tick.get("tick_s_used_first_pass") or 4.04902\n',
    '    first = tick.get("tick_s_used_first_pass") or 4.24597\n',
    "first default",
)
must_replace(
    '    fill1615 = fill_txt(gaps["gap_1615_1622"])\n',
    '    fill1644 = fill_txt(gaps["gap_1644_1659"])\n    fill1615 = fill_txt(gaps["gap_1615_1622"])\n',
    "fill1644",
)

must_replace(
    '        + "First pass started 2026-11-22 16:31:29 Asia/Hong_Kong and finished 16:32:08 (exit=0): "\n'
    '        + "inserted=100 already_in_db=27206, first-pass realign committed ts_realigned_first=10444 (first-interval tick_s printed 4.049, exact 4.04902). "\n',
    '        + "First pass started 2026-11-22 17:02:12 Asia/Hong_Kong and finished 17:03:00 (exit=0): "\n'
    '        + "inserted=10327 already_in_db=16276, first-pass realign committed ts_realigned_first=16503 (first-interval tick_s printed 4.246, exact 4.24597). "\n',
    "first pass times",
)

must_replace(
    "Last delivered USER_LOG is ~15:32 _patrol_2026-11-22_1521 (finished_at 15:34:21); do not re-tell it or write a patrol folder. 12h review already delivered ~08:33; do not re-tell or write its folder. ",
    "Last delivered USER_LOG is ~16:32 _patrol_2026-11-22_1621 (finished_at 16:33:58); do not re-tell it or write a patrol folder. 12h review already delivered ~08:33; do not re-tell or write its folder. ",
    "last USER_LOG",
)

must_replace(
    "16:00 half-hour already official-filled through 84417100 / just-published 84417100; 15:30 half-hour official-filled through 84416700 / just-published 84416700; 15:32 patrol already official-filled through 84416500 / just-published 84416600; this run is overlap of those windows plus new official 84417200..84417400 and just-published 84417500. ",
    "16:30 half-hour already official-filled through 84417500 / just-published 84417500; 16:00 half-hour official-filled through 84417100 / just-published 84417100; 16:32 patrol already official-filled through 84417300 / just-published 84417400; this run is overlap of those windows plus new official 84417600..84417800 and just-published 84417900. ",
    "overlap sentence",
)

n = t.count("window start 84416801")
if n < 5:
    raise SystemExit(f"unexpected window start count {n}")
t = t.replace("window start 84416801", "window start 84417201")
print(f"ok window start x{n}")

must_replace(
    "Just-published 84417500 was not in first pass (first pass ended at published 84417400 / reconstructed 84416801..84417500 at ",
    "Just-published 84417900 was not in first pass (first pass ended at published 84417800 / reconstructed 84417201..84417900 at ",
    "jp sentence",
)
must_replace(
    "game.time=84417537, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} ",
    "game.time=84417985, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} ",
    "jp gt",
)

must_replace(
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=10444 corrective={corrective} "\n'
    '        + f"(later-mean {later}; first-pass realign committed ts_realigned=10444; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use}, later-mean was worse; applied corrective first realign of 2460 rows at game.time=84417565 tick_s=4.04902, still_over_45s_vs_target=0, skipped_cross_chunk=0). "\n',
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=16503 corrective={corrective} "\n'
    '        + f"(later-mean {later}; first-pass realign committed ts_realigned=16503; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use}, later-mean was worse; applied corrective first realign of 0 rows at game.time=84418011 tick_s=4.24597, still_over_45s_vs_target=0, skipped_cross_chunk=0). "\n',
    "tick_s narrative",
)

must_replace(
    "(15:32 patrol also recorded the age-out)",
    "(16:32 patrol also recorded the age-out)",
    "age-out 16:32 in now_txt",
)

OLD_FREEZE = (
    '        + f"NEW 盒子休眠 this run: 盒子休眠 16:15:02-16:22:09 (423s; STATS 84417291..84417409, 119t; official-filled {fill1615}; listener auto-restart 16:22:13, python 2548139 started 16:22:22, parent 4035476) -- NOT YET TOLD; fold into the next 1h patrol. 监听短中断 16:02:42-16:02:55 (WS ping/pong timed out, no box_pauses row; STATS 84417111..84417129, 19t; official-filled {fill1602}; listener auto-restart 16:02:46, python 2540965 started 16:02:55) -- recorded in the 16:00 half-hour; still NOT YET TOLD; fold into the next 1h patrol. 盒子休眠 14:47:50-15:01:16 (797s; STATS 84416041..84416249, 209t; official-filled {fill1447}; listener auto-restart 15:01:19, python 2507398 started 15:01:28) -- already told in the ~15:32 _patrol_2026-11-22_1521 USER_LOG; do not re-tell. 盒子休眠 14:15:32-14:20:01 (269s; STATS 84415571..84415649, 79t; official-filled {fill1415}; listener auto-restart 14:20:04, python 2490792 started 14:20:14) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. 盒子休眠 13:48:49-13:57:59 (544s; STATS 84415191..84415339, 149t; official-filled {fill1348}; listener auto-restart 13:58:02, python 2481423 started 13:58:12) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. "\n'
)
NEW_FREEZE = (
    '        + f"NEW 盒子休眠 this run: 盒子休眠 16:44:58-16:59:18 (850s; STATS 84417731..84417949, 219t; official-filled {fill1644}; listener auto-restart 16:59:21, python 2562267 started 16:59:30, parent 4035476) -- NOT YET TOLD; fold into the next 1h patrol. NEW 监听短中断 this run: none. 盒子休眠 16:15:02-16:22:09 (423s; STATS 84417291..84417409, 119t; official-filled {fill1615}; listener auto-restart 16:22:13, python 2548139 started 16:22:22, parent 4035476) -- already told in the ~16:32 _patrol_2026-11-22_1621 USER_LOG; do not re-tell. 监听短中断 16:02:42-16:02:55 (WS ping/pong timed out, no box_pauses row; STATS 84417111..84417129, 19t; official-filled {fill1602}; listener auto-restart 16:02:46, python 2540965 started 16:02:55) -- already told in the ~16:32 _patrol_2026-11-22_1621 USER_LOG; do not re-tell. 盒子休眠 14:47:50-15:01:16 (797s; STATS 84416041..84416249, 209t; official-filled {fill1447}; listener auto-restart 15:01:19, python 2507398 started 15:01:28) -- already told in the ~15:32 _patrol_2026-11-22_1521 USER_LOG; do not re-tell. 盒子休眠 14:15:32-14:20:01 (269s; STATS 84415571..84415649, 79t; official-filled {fill1415}; listener auto-restart 14:20:04, python 2490792 started 14:20:14) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. 盒子休眠 13:48:49-13:57:59 (544s; STATS 84415191..84415339, 149t; official-filled {fill1348}; listener auto-restart 13:58:02, python 2481423 started 13:58:12) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. "\n'
)
must_replace(OLD_FREEZE, NEW_FREEZE, "NEW freeze narrative")

must_replace(
    "Single listener 2548139 since 16:22:22 after the 16:15:02-16:22:09 box freeze auto-restart 16:22:13 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
    "Single listener 2562267 since 16:59:30 after the 16:44:58-16:59:18 box freeze auto-restart 16:59:21 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
    "listener sentence",
)

must_replace(
    '        + f"first_pass game.time=84417537 published_bases=84416800..84417400 reconstructed=84416801..84417500 (700) "\n'
    '        + f"35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=27206 ts_realigned_first=10444; tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_first_nfix=2460" + NL\n',
    '        + f"first_pass game.time=84417985 published_bases=84417200..84417800 reconstructed=84417201..84417900 (700) "\n'
    '        + f"35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=16276 ts_realigned_first=16503; tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_first_nfix=0" + NL\n',
    "verify first_pass",
)

must_replace(
    "15:32 patrol also recorded the age-out",
    "16:32 patrol also recorded the age-out",
    "verify age-out 16:32",
)

must_replace(
    "just_published 84417500 at {jp_at} gt={jp_gt} all_five_200={jp_all5} script={script_sum} actual={actual_sum} script_by={script_by} actual_by={actual}",
    "just_published 84417900 at {jp_at} gt={jp_gt} all_five_200={jp_all5} script={script_sum} actual={actual_sum} script_by={script_by} actual_by={actual}",
    "verify jp base",
)

must_replace(
    "gaps 1615={{ { {r: gaps['gap_1615_1622'][r]['fill'] for r in ROOMS} } }} 1602=",
    "gaps 1644={{ { {r: gaps['gap_1644_1659'][r]['fill'] for r in ROOMS} } }} 1615={{ { {r: gaps['gap_1615_1622'][r]['fill'] for r in ROOMS} } }} 1602=",
    "verify gaps 1644",
)

must_replace(
    "already_told by _patrol_2026-11-22_1521 USER_LOG ~15:32 finished_at 15:34:21 (do not re-tell): 盒子休眠 14:47:50-15:01:16. ",
    "already_told by _patrol_2026-11-22_1621 USER_LOG ~16:32 finished_at 16:33:58 (do not re-tell): 盒子休眠 16:15:02-16:22:09; 监听短中断 16:02:42-16:02:55. already_told by _patrol_2026-11-22_1521 USER_LOG ~15:32 finished_at 15:34:21 (do not re-tell): 盒子休眠 14:47:50-15:01:16. ",
    "verify already_told 1621",
)

must_replace(
    "ok_quiet=True new_official_404_untold=[] still_untold_from_1230=[] still_untold_from_1100=[] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=['freeze_1615'] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=['shortws_1602'] first_pass_source=this_halfhour_1630 concurrent_patrol=delivered_1521_1532 concurrent_12h_review=already_delivered_0833_do_not_write_its_folder",
    "ok_quiet=True new_official_404_untold=[] still_untold_from_1230=[] still_untold_from_1100=[] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=['freeze_1644'] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_1700 concurrent_patrol=delivered_1621_1633 concurrent_12h_review=already_delivered_0833_do_not_write_its_folder",
    "verify ok_quiet line",
)

must_replace(
    '"new_box_freeze_untold": ["freeze_16:15:02-16:22:09 STATS 84417291..84417409"],',
    '"new_box_freeze_untold": ["freeze_16:44:58-16:59:18 STATS 84417731..84417949"],',
    "snap freeze untold",
)
must_replace(
    '"new_short_ws_untold": ["shortws_16:02:42-16:02:55 STATS 84417111..84417129"],',
    '"new_short_ws_untold": [],',
    "snap shortws untold",
)
must_replace(
    '"concurrent_patrol": "delivered_1521_1532",',
    '"concurrent_patrol": "delivered_1621_1633",',
    "snap concurrent patrol",
)
must_replace(
    '"first_pass_realign": "committed ts_realigned=10444; tick_s_in_use=first 4.04902 after tick_s_check, corrective first realign nfix=2460, still_over_45s_vs_target=0",',
    '"first_pass_realign": "committed ts_realigned=16503; tick_s_in_use=first 4.24597 after tick_s_check, corrective first realign nfix=0, still_over_45s_vs_target=0",',
    "snap first_pass_realign",
)

p.write_text(t)
print("wrapup_write.py patched")

left_old = []
for s in [
    "inserted=100 already_in_db=27206",
    "ts_realigned_first=10444",
    "freeze_1615']",
    "shortws_1602",
    "delivered_1521_1532",
    "this_halfhour_1630",
    "JP_BASE = 84417500",
    "T0, T1 = 84416801",
    "window start 84416801",
]:
    if s in t:
        left_old.append(s)
print("leftover old tokens:", left_old or "none")
print("T0T1", [l for l in t.splitlines() if l.startswith("T0, T1") or l.startswith("JP_BASE")])
print("gap/fill", [l.strip() for l in t.splitlines() if "gap_1644" in l or "fill1644" in l])
