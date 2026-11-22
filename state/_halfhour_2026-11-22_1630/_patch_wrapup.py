#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-22_1630/wrapup_write.py")
t = p.read_text()

def must_replace(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"{label}: found {n} occurrences, expected 1")
    t = t.replace(old, new, 1)

must_replace("T0, T1 = 84416401, 84417100", "T0, T1 = 84416801, 84417500", "T0T1")
must_replace("JP_BASE = 84417100", "JP_BASE = 84417500", "JP_BASE")
must_replace(
    '    ("gap_1602_1602", 84417111, 84417129),\n',
    '    ("gap_1615_1622", 84417291, 84417409),\n    ("gap_1602_1602", 84417111, 84417129),\n',
    "GAPS add 1615",
)
must_replace("    inserted_first = 8086\n", "    inserted_first = 100\n", "inserted_first")
must_replace("    first = tick.get(\"tick_s_used_first_pass\") or 4.21116\n",
             "    first = tick.get(\"tick_s_used_first_pass\") or 4.04902\n",
             "first default")
must_replace(
    '    fill1602 = fill_txt(gaps["gap_1602_1602"])\n',
    '    fill1615 = fill_txt(gaps["gap_1615_1622"])\n    fill1602 = fill_txt(gaps["gap_1602_1602"])\n',
    "fill1615",
)

must_replace(
    '        + "First pass started 2026-11-22 16:05:45 Asia/Hong_Kong and finished 16:06:32 (exit=0): "\n'
    '        + "inserted=8086 already_in_db=18451, first-pass realign committed ts_realigned_first=1873 (first-interval tick_s printed 4.211, exact 4.21116). "\n',
    '        + "First pass started 2026-11-22 16:31:29 Asia/Hong_Kong and finished 16:32:08 (exit=0): "\n'
    '        + "inserted=100 already_in_db=27206, first-pass realign committed ts_realigned_first=10444 (first-interval tick_s printed 4.049, exact 4.04902). "\n',
    "first pass times",
)

must_replace(
    "15:30 half-hour already official-filled through 84416700 / just-published 84416700; 15:32 patrol already official-filled through 84416500 / just-published 84416600; this run is overlap of those windows plus new official 84416800..84417000 and just-published 84417100. ",
    "16:00 half-hour already official-filled through 84417100 / just-published 84417100; 15:30 half-hour official-filled through 84416700 / just-published 84416700; 15:32 patrol already official-filled through 84416500 / just-published 84416600; this run is overlap of those windows plus new official 84417200..84417400 and just-published 84417500. ",
    "overlap sentence",
)

# window start in already-told 404 texts
if t.count("window start 84416401") < 5:
    raise SystemExit(f"unexpected window start count {t.count('window start 84416401')}")
t = t.replace("window start 84416401", "window start 84416801")

must_replace(
    "Just-published 84417100 was not in first pass (first pass ended at published 84417000 / reconstructed 84416401..84417100 at ",
    "Just-published 84417500 was not in first pass (first pass ended at published 84417400 / reconstructed 84416801..84417500 at ",
    "jp sentence",
)
must_replace(
    "game.time=84417167, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} ",
    "game.time=84417537, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} ",
    "jp gt",
)

must_replace(
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=1873 corrective={corrective} "\n'
    '        + f"(later-mean {later}; first-pass realign committed ts_realigned=1873; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use}, later-mean was worse, no corrective realign, still_over_45s_vs_target already 0 vs prev_later). "\n',
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=10444 corrective={corrective} "\n'
    '        + f"(later-mean {later}; first-pass realign committed ts_realigned=10444; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use}, later-mean was worse; applied corrective first realign of 2460 rows at game.time=84417565 tick_s=4.04902, still_over_45s_vs_target=0, skipped_cross_chunk=0). "\n',
    "tick_s narrative",
)

must_replace(
    '        + f"NEW short WS this run: 监听短中断 16:02:42-16:02:55 (WS ping/pong timed out, no box_pauses row; STATS 84417111..84417129, 19t; official-filled {fill1602}; listener auto-restart 16:02:46, python 2540965 started 16:02:55) -- NOT YET TOLD; fold into the next 1h patrol. NEW 盒子休眠 this run: none. 盒子休眠 14:47:50-15:01:16 (797s; STATS 84416041..84416249, 209t; official-filled {fill1447}; listener auto-restart 15:01:19, python 2507398 started 15:01:28) -- already told in the ~15:32 _patrol_2026-11-22_1521 USER_LOG; do not re-tell. 盒子休眠 14:15:32-14:20:01 (269s; STATS 84415571..84415649, 79t; official-filled {fill1415}; listener auto-restart 14:20:04, python 2490792 started 14:20:14) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. 盒子休眠 13:48:49-13:57:59 (544s; STATS 84415191..84415339, 149t; official-filled {fill1348}; listener auto-restart 13:58:02, python 2481423 started 13:58:12) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. "\n',
    '        + f"NEW 盒子休眠 this run: 盒子休眠 16:15:02-16:22:09 (423s; STATS 84417291..84417409, 119t; official-filled {fill1615}; listener auto-restart 16:22:13, python 2548139 started 16:22:22, parent 4035476) -- NOT YET TOLD; fold into the next 1h patrol. 监听短中断 16:02:42-16:02:55 (WS ping/pong timed out, no box_pauses row; STATS 84417111..84417129, 19t; official-filled {fill1602}; listener auto-restart 16:02:46, python 2540965 started 16:02:55) -- recorded in the 16:00 half-hour; still NOT YET TOLD; fold into the next 1h patrol. 盒子休眠 14:47:50-15:01:16 (797s; STATS 84416041..84416249, 209t; official-filled {fill1447}; listener auto-restart 15:01:19, python 2507398 started 15:01:28) -- already told in the ~15:32 _patrol_2026-11-22_1521 USER_LOG; do not re-tell. 盒子休眠 14:15:32-14:20:01 (269s; STATS 84415571..84415649, 79t; official-filled {fill1415}; listener auto-restart 14:20:04, python 2490792 started 14:20:14) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. 盒子休眠 13:48:49-13:57:59 (544s; STATS 84415191..84415339, 149t; official-filled {fill1348}; listener auto-restart 13:58:02, python 2481423 started 13:58:12) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. "\n',
    "NEW freeze narrative",
)

must_replace(
    "Single listener 2540965 since 16:02:55 after the 16:02:42 short WS auto-restart 16:02:46, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
    "Single listener 2548139 since 16:22:22 after the 16:15:02-16:22:09 box freeze auto-restart 16:22:13 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. ",
    "listener sentence",
)

must_replace(
    '        + f"first_pass game.time=84417167 published_bases=84416400..84417000 reconstructed=84416401..84417100 (700) "\n'
    '        + f"35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=18451 ts_realigned_first=1873; tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective={corrective}" + NL\n',
    '        + f"first_pass game.time=84417537 published_bases=84416800..84417400 reconstructed=84416801..84417500 (700) "\n'
    '        + f"35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=27206 ts_realigned_first=10444; tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_first_nfix=2460" + NL\n',
    "verify first_pass",
)

must_replace(
    "just_published 84417100 at {jp_at} gt={jp_gt} all_five_200={jp_all5} script={script_sum} actual={actual_sum} script_by={script_by} actual_by={actual}",
    "just_published 84417500 at {jp_at} gt={jp_gt} all_five_200={jp_all5} script={script_sum} actual={actual_sum} script_by={script_by} actual_by={actual}",
    "verify jp base",
)

must_replace(
    '        + f"gaps 1602={{ { {r: gaps[\'gap_1602_1602\'][r][\'fill\'] for r in ROOMS} } }} 1447=',
    '        + f"gaps 1615={{ { {r: gaps[\'gap_1615_1622\'][r][\'fill\'] for r in ROOMS} } }} 1602={{ { {r: gaps[\'gap_1602_1602\'][r][\'fill\'] for r in ROOMS} } }} 1447=',
    "verify gaps 1615",
)

must_replace(
    "new_box_freeze_untold=[] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=['shortws_1602'] first_pass_source=this_halfhour_1600 concurrent_patrol=delivered_1521_1532 concurrent_12h_review=already_delivered_0833_do_not_write_its_folder",
    "new_box_freeze_untold=['freeze_1615'] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=['shortws_1602'] first_pass_source=this_halfhour_1630 concurrent_patrol=delivered_1521_1532 concurrent_12h_review=already_delivered_0833_do_not_write_its_folder",
    "ok_quiet flags",
)

must_replace(
    '        "new_box_freeze_untold": [],\n',
    '        "new_box_freeze_untold": ["freeze_16:15:02-16:22:09 STATS 84417291..84417409"],\n',
    "snap freeze",
)
must_replace(
    '        "first_pass_realign": "committed ts_realigned=1873; tick_s_in_use=prev_later 4.192072 after tick_s_check, no corrective",\n',
    '        "first_pass_realign": "committed ts_realigned=10444; tick_s_in_use=first 4.04902 after tick_s_check, corrective first realign nfix=2460, still_over_45s_vs_target=0",\n',
    "snap realign",
)

p.write_text(t)
print("wrapup_write.py patched ok")
# sanity
checks = [
    "T0, T1 = 84416801, 84417500",
    "JP_BASE = 84417500",
    "gap_1615_1622",
    "inserted_first = 100",
    "fill1615",
    "16:31:29",
    "already_in_db=27206",
    "ts_realigned_first=10444",
    "Just-published 84417500",
    "NEW 盒子休眠 this run: 盒子休眠 16:15:02-16:22:09",
    "Single listener 2548139",
    "new_box_freeze_untold=['freeze_1615']",
    "first_pass_source=this_halfhour_1630",
    "window start 84416801",
]
for c in checks:
    print(("OK" if c in t else "MISSING"), c)
print("old window start left", t.count("window start 84416401"))
print("old 84417167 left in first_pass", "game.time=84417167" in t)
