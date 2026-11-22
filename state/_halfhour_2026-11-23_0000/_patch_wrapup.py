from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-23_0000/wrapup_write.py")
t = p.read_text()

replacements = [
    ("T0, T1 = 84422901, 84423600", "T0, T1 = 84423301, 84424000"),
    ("JP_BASE = 84423600", "JP_BASE = 84424000"),
    (
        "GAPS = [
    ("gap_2243_2305", 84422871, 84423199),",
        "GAPS = [
    ("gap_2352_2359", 84423801, 84423969),
    ("gap_2243_2305", 84422871, 84423199),",
    ),
    ("    inserted_first = 1545", "    inserted_first = 7763"),
    ("    first = tick.get("tick_s_used_first_pass") or 4.25489", "    first = tick.get("tick_s_used_first_pass") or 4.25255"),
    (
        "    fill2243 = fill_txt(gaps["gap_2243_2305"])",
        "    fill2352 = fill_txt(gaps["gap_2352_2359"])
    fill2243 = fill_txt(gaps["gap_2243_2305"])",
    ),
    (
        "        + "First pass 32/35 official GETs 200, missing_chunks=3 W47N8@84423500, W45N8@84423500, W47N7@84423500. "",
        "        + "First pass 32/35 official GETs 200, missing_chunks=3 W47N8@84423900, W45N8@84423900, W47N7@84423900. "",
    ),
    (
        "        + "First pass started 2026-11-22 23:34:57 Asia/Hong_Kong and finished 23:35:39 (exit=0): "",
        "        + "First pass started 2026-11-23 00:03:00 Asia/Hong_Kong and finished 00:03:44 (exit=0): "",
    ),
    (
        "        + "inserted=1545 already_in_db=22962, first-pass realign moved 1243 rows ts_realigned_first=1243 "",
        "        + "inserted=7763 already_in_db=16711, first-pass realign moved 0 rows ts_realigned_first=0 "",
    ),
    (
        "        + "(first-interval tick_s printed 4.255, exact 4.25489). Overlap with the 23:17 half-hour (official 84422501..84423200 / JP 84423200) and the 23:31 patrol (official+JP through 84423500) accounts for already_in_db=22962. "",
        "        + "(first-interval tick_s printed 4.253, exact 4.25255). Overlap with the 23:45 half-hour (official 84422901..84423600 / JP 84423600) and the 23:31 patrol (official+JP through 84423500) accounts for already_in_db=16711. "",
    ),
    (
        "        + "Confirm 23:36:55 gt=84423635 recovered all three first-pass 404s inserted=1548 still_404=[]. No same-payload extra-row collision this first pass. "",
        "        + "Confirm 00:05:26 gt=84424042 recovered all three first-pass 404s inserted=2354 still_404=[]. No same-payload extra-row collision this first pass. "",
    ),
    (
        "        + "23:17 half-hour already official-filled 84422501..84423200 / just-published 84423200. 23:31 patrol already official+JP filled through 84423500, and already told leftover 404 W45N8@84422100 and W45N8@84422400 plus 盒子休眠 22:43:27-23:05:49 (and 21:45:57-22:04:37 and 20:49:49-20:59:53 and 19:43:54-19:59:40). This run is overlap of that window plus new official 84422900..84423500 and just-published 84423600. "",
        "        + "23:45 half-hour already official-filled 84422901..84423600 / just-published 84423600. 23:31 patrol already official+JP filled through 84423500, and already told leftover 404 W45N8@84422100 and W45N8@84422400 plus 盒子休眠 22:43:27-23:05:49 (and 21:45:57-22:04:37 and 20:49:49-20:59:53 and 19:43:54-19:59:40). This run is overlap of that window plus new official 84423300..84423900 and just-published 84424000. "",
    ),
    (
        "aged out of window start 84422901 and were not retried this pass (already told in the 22:37 patrol and mentioned as already-told in the 23:31 _patrol_2026-11-22_2316 USER_LOG; do not re-tell). ",
        "aged out of window start 84423301 and were not retried this pass (already told in the 22:37 patrol and mentioned as already-told in the 23:31 _patrol_2026-11-22_2316 USER_LOG; do not re-tell). ",
    ),
    (
        "also aged out of window start 84422901 and were not retried this pass; do not re-tell. ",
        "also aged out of window start 84423301 and were not retried this pass; do not re-tell. ",
    ),
    (
        "        + f"Just-published 84423600 was not in first pass (first pass ended at published 84423500 / reconstructed 84422901..84423600 at "",
        "        + f"Just-published 84424000 was not in first pass (first pass ended at published 84423900 / reconstructed 84423301..84424000 at "",
    ),
    (
        "        + f"game.time=84423607, 32/35 200, missing_chunks=3 recovered on confirm). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5}. "",
        "        + f"game.time=84424007, 32/35 200, missing_chunks=3 recovered on confirm). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5}. "",
    ),
    (
        "        + "NEW leftover official 404 this run: none (first-pass 404s W47N8@84423500, W45N8@84423500, W47N7@84423500 all recovered on confirm). "",
        "        + "NEW leftover official 404 this run: none (first-pass 404s W47N8@84423900, W45N8@84423900, W47N7@84423900 all recovered on confirm). "",
    ),
    (
        "aged out of window start 84422901 and were not retried this pass; already told in the ~22:37 patrol and mentioned as already-told in the ~23:31 _patrol_2026-11-22_2316 USER_LOG; do not re-tell. ",
        "aged out of window start 84423301 and were not retried this pass; already told in the ~22:37 patrol and mentioned as already-told in the ~23:31 _patrol_2026-11-22_2316 USER_LOG; do not re-tell. ",
    ),
    (
        "        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=1243 corrective={corrective} "",
        "        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=0 corrective={corrective} "",
    ),
    (
        "        + f"(later-mean {later}; first-pass realign moved 1243 rows with first-interval 4.25489, over45=0 vs first after that realign; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use} inside 45s gate, no corrective realign, skipped_cross_chunk=0). "",
        "        + f"(later-mean {later}; first-pass realign moved 0 rows with first-interval 4.25255, over45=0 vs first; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use} inside 45s gate, no corrective realign, skipped_cross_chunk=0). "",
    ),
    (
        "        + f"NEW 盒子休眠 this run: none. NEW 监听短中断 this run: none. Already-told 盒子休眠 22:43:27-23:05:49 (1334s; STATS 84422871..84423199 official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476; already told in the 23:31 patrol; do not re-tell). "",
        "        + f"NEW 盒子休眠 this run 23:52:01-23:59:48 Asia/Hong_Kong (459s, box_pauses row; STATS 84423801..84423969, 169t; official-filled {fill2352}; listener auto-restart 23:59:51, python 2749374 started 00:00:01, parent 4035476). The 23:51:41 no-STATS reconnect (197s) sits at the front of the same STATS gap and is not a separate 监听短中断. NEW 监听短中断 this run: none. Already-told 盒子休眠 22:43:27-23:05:49 (1334s; STATS 84422871..84423199 official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476; already told in the 23:31 patrol; do not re-tell). "",
    ),
    (
        "        + "Single listener 2722653 since 23:06:02 after the already-told 盒子休眠 22:43:27-23:05:49 auto-restart 23:05:52 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "",
        "        + "Single listener 2749374 since 00:00:01 after the NEW 盒子休眠 23:52:01-23:59:48 auto-restart 23:59:51 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "",
    ),
    (
        "        + f"gaps 2243={{ { {r: gaps['gap_2243_2305'][r]['fill'] for r in ROOMS} } }} 2145={{ { {r: gaps['gap_2145_2204'][r]['fill'] for r in ROOMS} } }} 2049={{ { {r: gaps['gap_2049_2059'][r]['fill'] for r in ROOMS} } }} 1943={{ { {r: gaps['gap_1943_1959'][r]['fill'] for r in ROOMS} } }} 1912={{ { {r: gaps['gap_1912_1913'][r]['fill'] for r in ROOMS} } }} 1741={{ { {r: gaps['gap_1741_1804'][r]['fill'] for r in ROOMS} } }} 1712={{ { {r: gaps['gap_1712_1722'][r]['fill'] for r in ROOMS} } }} 1644={{ { {r: gaps['gap_1644_1659'][r]['fill'] for r in ROOMS} } }} 1615={{ { {r: gaps['gap_1615_1622'][r]['fill'] for r in ROOMS} } }} 1602={{ { {r: gaps['gap_1602_1602'][r]['fill'] for r in ROOMS} } }}" + NL",
        "        + f"gaps 2352={{ { {r: gaps['gap_2352_2359'][r]['fill'] for r in ROOMS} } }} 2243={{ { {r: gaps['gap_2243_2305'][r]['fill'] for r in ROOMS} } }} 2145={{ { {r: gaps['gap_2145_2204'][r]['fill'] for r in ROOMS} } }} 2049={{ { {r: gaps['gap_2049_2059'][r]['fill'] for r in ROOMS} } }} 1943={{ { {r: gaps['gap_1943_1959'][r]['fill'] for r in ROOMS} } }} 1912={{ { {r: gaps['gap_1912_1913'][r]['fill'] for r in ROOMS} } }} 1741={{ { {r: gaps['gap_1741_1804'][r]['fill'] for r in ROOMS} } }} 1712={{ { {r: gaps['gap_1712_1722'][r]['fill'] for r in ROOMS} } }} 1644={{ { {r: gaps['gap_1644_1659'][r]['fill'] for r in ROOMS} } }} 1615={{ { {r: gaps['gap_1615_1622'][r]['fill'] for r in ROOMS} } }} 1602={{ { {r: gaps['gap_1602_1602'][r]['fill'] for r in ROOMS} } }}" + NL",
    ),
    (
        "        + f"NEW 盒子休眠 this run: none. NEW leftover official 404 none this run (first-pass W47N8/W45N8/W47N7@84423500 recovered on confirm). already_told by _patrol_2026-11-22_2316 USER_LOG ~23:31 finished_at 23:32:40 (do not re-tell): 盒子休眠 22:43:27-23:05:49 (STATS 84422871..84423199 official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476). already_told by _patrol_2026-11-22_2224 USER_LOG ~22:37 finished_at 22:36:58 (do not re-tell): 盒子休眠 21:45:57-22:04:37; leftover official 404 W45N8@84422100 and W45N8@84422400. already_told by _patrol_2026-11-22_2117 USER_LOG ~21:27 finished_at 21:27:21 (do not re-tell): 盒子休眠 20:49:49-20:59:53; leftover official 404 W45N7@84419300 and W45N8@84419600. already_told by _patrol_2026-11-22_2016 USER_LOG ~20:27 finished_at 20:26:55 (do not re-tell): 盒子休眠 19:43:54-19:59:40. already_told by _patrol_2026-11-22_1924 USER_LOG ~19:36 finished_at 19:36:36 (do not re-tell): 监听短中断 19:12:43-19:12:57; 盒子休眠 17:41:00-18:04:50 and earlier leftover official 404 all five @84418900 and W45N7@84419000. Older already-told freezes through 17:12:37-17:22:45 / 16:44:58-16:59:18 / 16:15:02-16:22:09 and leftover official 404s through W45N8@84415500 / W46N8@84414700 / W46N8@84413700 and earlier. already-told 监听短中断 through 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20." + NL",
        "        + f"NEW 盒子休眠 this run 23:52:01-23:59:48 (459s; STATS 84423801..84423969 official-filled {fill2352}; listener auto-restart 23:59:51, python 2749374 started 00:00:01, parent 4035476). The 23:51:41 no-STATS reconnect (197s) shares that STATS gap and is not a separate 监听短中断. NEW leftover official 404 none this run (first-pass W47N8/W45N8/W47N7@84423900 recovered on confirm). already_told by _patrol_2026-11-22_2316 USER_LOG ~23:31 finished_at 23:32:40 (do not re-tell): 盒子休眠 22:43:27-23:05:49 (STATS 84422871..84423199 official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476). already_told by _patrol_2026-11-22_2224 USER_LOG ~22:37 finished_at 22:36:58 (do not re-tell): 盒子休眠 21:45:57-22:04:37; leftover official 404 W45N8@84422100 and W45N8@84422400. already_told by _patrol_2026-11-22_2117 USER_LOG ~21:27 finished_at 21:27:21 (do not re-tell): 盒子休眠 20:49:49-20:59:53; leftover official 404 W45N7@84419300 and W45N8@84419600. already_told by _patrol_2026-11-22_2016 USER_LOG ~20:27 finished_at 20:26:55 (do not re-tell): 盒子休眠 19:43:54-19:59:40. already_told by _patrol_2026-11-22_1924 USER_LOG ~19:36 finished_at 19:36:36 (do not re-tell): 监听短中断 19:12:43-19:12:57; 盒子休眠 17:41:00-18:04:50 and earlier leftover official 404 all five @84418900 and W45N7@84419000. Older already-told freezes through 17:12:37-17:22:45 / 16:44:58-16:59:18 / 16:15:02-16:22:09 and leftover official 404s through W45N8@84415500 / W46N8@84414700 / W46N8@84413700 and earlier. already-told 监听短中断 through 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20." + NL",
    ),
    (
        "ok_quiet=True new_official_404_untold=[] still_untold_from_1230=[] still_untold_from_1100=[] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_2330 concurrent_patrol=already_delivered_patrol_2026-11-22_2316_do_not_write_its_folder concurrent_12h_review=already_completed_review12h_2026-11-22_20_do_not_write_its_folder",
        "ok_quiet=True new_official_404_untold=[] still_untold_from_1230=[] still_untold_from_1100=[] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[23:52:01-23:59:48] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0000 concurrent_patrol=already_delivered_patrol_2026-11-22_2316_do_not_write_its_folder concurrent_12h_review=already_completed_review12h_2026-11-22_20_do_not_write_its_folder",
    ),
]

# Also patch snap dict keys if present
more = [
    ('"new_box_freeze_untold": [],', '"new_box_freeze_untold": ["23:52:01-23:59:48"],'),
    ('"first_pass_source": "this_halfhour_2330"', '"first_pass_source": "this_halfhour_0000"'),
    ('first_pass_source=this_halfhour_2330', 'first_pass_source=this_halfhour_0000'),
]
# apply more after checking they exist; include in replacements if found

missing = []
for i, (old, new) in enumerate(replacements):
    if old not in t:
        missing.append(i)
    else:
        t = t.replace(old, new, 1)

for old, new in more:
    if old in t:
        t = t.replace(old, new)

if missing:
    raise SystemExit(f"missing replacement indices: {missing}")

# sanity
needles = [
    "T0, T1 = 84423301, 84424000",
    "JP_BASE = 84424000",
    "gap_2352_2359",
    "inserted_first = 7763",
    "fill2352",
    "NEW 盒子休眠 this run 23:52:01-23:59:48",
    "Single listener 2749374",
    "new_box_freeze_untold=[23:52:01-23:59:48]",
    "first_pass_source=this_halfhour_0000",
    "W47N8@84423900",
]
for n in needles:
    if n not in t:
        raise SystemExit(f"sanity missing: {n}")

# leftover old first-pass numbers that should not remain in narrative (DIR comments ok)
p.write_text(t)
print("wrapup_write patched ok, len", len(t))
