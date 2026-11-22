from pathlib import Path

p = Path("/workspace/screeps/state/_halfhour_2026-11-22_1100/wrapup_write.py")
t = p.read_text()

t = t.replace("T0, T1 = 84411601, 84412300", "T0, T1 = 84412101, 84412800")
t = t.replace("JP_BASE = 84412300", "JP_BASE = 84412800")

old_gaps = "GAPS = [\n    (\"gap_1016_1022\", 84412131, 84412219),\n"
new_gaps = "GAPS = [\n    (\"gap_1045_1106\", 84412541, 84412859),\n    (\"gap_1016_1022\", 84412131, 84412219),\n"
if old_gaps not in t:
    raise SystemExit("GAPS header not found")
t = t.replace(old_gaps, new_gaps, 1)

old_holes = "HOLES = [\n    (\"W45N7\", 84411500),\n"
new_holes = "HOLES = [\n    (\"W47N7\", 84412400),\n    (\"W45N7\", 84411500),\n"
if old_holes not in t:
    raise SystemExit("HOLES header not found")
t = t.replace(old_holes, new_holes, 1)

t = t.replace(
    "    # First pass inserted=2940 is the real DB insert. confirm/retry2/late still 404 W45N7@84411500 (leftover just outside window, not yet told from 10:11).",
    "    # First pass inserted=13067 is the real DB insert. confirm/retry2/late still 404 W47N7@84412400 (in-window leftover, not yet told).",
)
t = t.replace("    inserted_first = 2940", "    inserted_first = 13067")
t = t.replace('    first = tick.get("tick_s_used_first_pass") or 4.195', '    first = tick.get("tick_s_used_first_pass") or 4.117')

needle = '    w45n7_84411500 = holes["W45N7@84411500"]'
if needle not in t:
    raise SystemExit("w45n7 hole var not found")
t = t.replace(
    needle,
    '    w47n7_84412400 = holes["W47N7@84412400"]\n    w45n7_84411500 = holes["W45N7@84411500"]',
)
needle = '    fill1016 = fill_txt(gaps["gap_1016_1022"])'
if needle not in t:
    raise SystemExit("fill1016 not found")
t = t.replace(
    needle,
    '    fill1045 = fill_txt(gaps["gap_1045_1106"])\n    fill1016 = fill_txt(gaps["gap_1016_1022"])',
)

start = t.index("    now_txt = (")
end = t.index('    (DIR / "_halfhour_backfill_now.txt").write_text(now_txt)')

now_txt = r'''    now_txt = (
        "source=this_halfhour_first_pass _halfhour_2026-11-22_1100" + NL
        + first_txt
        + f"---- wrap {now} ----" + NL
        + f"confirm at {confirm_at} gt={confirm_gt} still_404 W47N7@84412400 inserted={inserted_confirm_script}. "
        + f"retry2 at {retry2_at} gt={retry2_gt} still_404 W47N7@84412400 inserted={inserted_retry2_script}. "
        + f"late retry at {late_at} gt={late_gt} still_404 W47N7@84412400 inserted={inserted_late}. "
        + "First pass 34/35 official GETs 200, missing_chunks=1 W47N7@84412400. "
        + "First pass started 2026-11-22 11:08:37 Asia/Hong_Kong and finished 11:09:26 (exit=0): "
        + "inserted=13067 already_in_db=13275, first-pass realign committed ts_realigned_first=0 (no rows over the 45s gate). "
        + "tick_s_check chose live-anchor-best all_mean 4.16192 (later-mean-robust 4.17088 was worse: over45=0 mean_off=13.9 vs all_mean over45=0 mean_off=9.8) and did not apply a corrective realign; still_over_45s_vs_target=0, skipped_cross_chunk=0. "
        + "Concurrent 1h patrol already delivered ~10:37 _patrol_2026-11-22_1022 t508s3620 USER_LOG; do not re-tell or write its folder. 12h review already delivered ~08:33 t508s3618; do not re-tell or write its folder. "
        + "10:30 half-hour already official-filled through 84412200 / just-published 84412300; this run is idempotent overlap plus new official 84412400..84412700 (except W47N7@84412400) and just-published 84412800. "
        + "Already-told leftover official 404s W45N7@84411500, W47N8@84409800, W46N8@84408300, W47N8@84408300, W47N7@84407900, W46N8@84407000, W45N8@84407700, W45N8@84406400, W46N8@84406600, W46N8@84406700, "
        + "W45N7@84403800, W45N7@84403700, W45N7@84400400, W45N7@84400300, and W47N8@84400100 aged out of window start 84412101 "
        + "and were not retried this pass (already told in the 10:37 _patrol_2026-11-22_1022 t508s3620 or earlier USER_LOG; do not re-tell). "
        + f"Just-published 84412800 was not in first pass (first pass ended at published 84412700 / reconstructed 84412101..84412800 at "
        + f"game.time=84412884, 34/35 200, missing_chunks=1 W47N7@84412400). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} "
        + f"script={script_sum} actual={actual_sum}; {script_vs_txt}. "
        + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
        + "W46N8 official empty_no_creep in this first-pass window: none. "
        + "W47N8 official empty_no_creep in this first-pass window: none. "
        + "W45N8 / W45N7 official empty_no_creep in this first-pass window: none. "
        + "W47N7 official empty_no_creep in this first-pass window: none (the 100-tick gap is official_404 W47N7@84412400, ticks 84412401..84412500). "
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=0 corrective={corrective} "
        + f"(later-raw later-mean {later}; first-pass realign committed ts_realigned=0; live-anchor-best all_mean 4.16192, no corrective realign, still_over_45s=0). "
        + f"NEW leftover official 404 this run: W47N7@84412400 (this confirm 11:10:45, retry2 11:11:19, and late retry 11:11:21 still 404; listener {w47n7_84412400['distinct']}/100 range {w47n7_84412400['min']}..{w47n7_84412400['max']}; hole {w47n7_84412400['hole_ticks']} ticks {hole_range_txt(w47n7_84412400)}) -- not yet told; fold into the next 1h patrol USER_LOG. "
        + f"Already-told leftover official 404 W45N7@84411500 aged out of window start 84412101 and was not retried this pass (listener {w45n7_84411500['distinct']}/100 range {w45n7_84411500['min']}..{w45n7_84411500['max']}; hole {w45n7_84411500['hole_ticks']} ticks {hole_range_txt(w45n7_84411500)}) -- already told in the 10:37 _patrol_2026-11-22_1022 t508s3620 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W47N8@84409800 aged out of window start 84412101 and was not retried this pass (listener {w47n8_84409800['distinct']}/100 range {w47n8_84409800['min']}..{w47n8_84409800['max']}; hole {w47n8_84409800['hole_ticks']} ticks {hole_range_txt(w47n8_84409800)}) -- already told in the 08:28 _patrol_2026-11-22_0818 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W46N8@84408300 aged out of window start 84412101 and was not retried this pass (listener {w46n8_84408300['distinct']}/100; hole {w46n8_84408300['hole_ticks']} ticks {hole_range_txt(w46n8_84408300)}) -- already told in the 06:44 _patrol_2026-11-22_0625 t508s3614 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W47N8@84408300 aged out of window start 84412101 and was not retried this pass (listener {w47n8_84408300['distinct']}/100; hole {w47n8_84408300['hole_ticks']} ticks {hole_range_txt(w47n8_84408300)}) -- already told in the 06:44 patrol t508s3614 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W47N7@84407900 aged out of window start 84412101 and was not retried this pass (listener {w47n7_84407900['distinct']}/100; hole {w47n7_84407900['hole_ticks']} ticks {hole_range_txt(w47n7_84407900)}) -- already told in the 06:44 patrol t508s3614 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84407700 aged out of window start 84412101 and was not retried this pass (listener {w45n8_84407700['distinct']}/100; hole {w45n8_84407700['hole_ticks']} ticks {hole_range_txt(w45n8_84407700)}) -- already told in the 05:38 _patrol_2026-11-22_0522 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W46N8@84407000 aged out of window start 84412101 and was not retried this pass (listener {w46n8_84407000['distinct']}/100; hole {w46n8_84407000['hole_ticks']} ticks {hole_range_txt(w46n8_84407000)}) -- already told in the 05:38 _patrol_2026-11-22_0522 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404s aged out of window start 84412101 and were not retried: W45N8@84406400 (listener {w45n8_84406400['distinct']}/100; hole {w45n8_84406400['hole_ticks']} ticks {hole_range_txt(w45n8_84406400)}), W46N8@84406600 (listener {w46n8_84406600['distinct']}/100; hole {w46n8_84406600['hole_ticks']} ticks {hole_range_txt(w46n8_84406600)}), W46N8@84406700 (listener {w46n8_84406700['distinct']}/100; hole {w46n8_84406700['hole_ticks']} ticks {hole_range_txt(w46n8_84406700)}) -- already told in the 04:33 _patrol_2026-11-22_0422 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84403800 aged out of window start 84412101 and was not retried (listener {w45n7_84403800['distinct']}/100; hole {w45n7_84403800['hole_ticks']} ticks {hole_range_txt(w45n7_84403800)}) -- already told in the 01:31 _patrol_2026-11-22_0121 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84403700 aged out of window start 84412101 and was not retried (listener {w45n7_84403700['distinct']}/100; hole {w45n7_84403700['hole_ticks']} ticks {hole_range_txt(w45n7_84403700)}) -- already told in the 01:31 patrol USER_LOG; do not re-tell. "
        + "NEW short WS this run: none. "
        + f"NEW box freeze this run: 盒子休眠 10:45:15-11:06:19 (1264s; STATS 84412541..84412859, 319t; official-filled {fill1045}; listener auto-restart 11:06:22, python 2409363 started 11:06:32) -- not yet told; fold into the next 1h patrol USER_LOG. "
        + f"盒子休眠 10:16:39-10:22:23 (338s; STATS 84412131..84412219, 89t; official-filled {fill1016}; listener auto-restart 10:22:26, python 2394456 started 10:22:36) -- already told in the 10:37 _patrol_2026-11-22_1022 t508s3620 USER_LOG; do not re-tell. "
        + f"盒子休眠 09:41:41-09:59:05 (1037s; STATS 84411621..84411889, 269t; official-filled {fill0941}; listener auto-restart 09:59:08, python 2385251 started 09:59:17) -- already told in the 10:37 _patrol_2026-11-22_1022 t508s3620 USER_LOG; do not re-tell. "
        + f"盒子休眠 09:14:15-09:19:05 (283s; STATS 84411221..84411299, 79t; official-filled {fill0914}; listener auto-restart 09:19:08, python 2371673 started 09:19:17) -- already told in the 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. "
        + f"盒子休眠 08:51:14-09:01:02 (581s; STATS 84410881..84411039, 159t; official-filled {fill0851}; listener auto-restart 09:01:06, python 2364487 started 09:01:15) -- already told in the 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. "
        + "_patrol_2026-11-22_1022 USER_LOG (delivered ~10:37 t508s3620) already includes (treat as already told; do not re-tell): 盒子休眠 10:16:39-10:22:23 and 09:41:41-09:59:05; leftover official 404 W45N7@84411500. "
        + "_patrol_2026-11-22_0918 USER_LOG (delivered 09:29) already includes (treat as already told; do not re-tell): 盒子休眠 08:51:14-09:01:02 and 09:14:15-09:19:05; W47N7@84411200 first-pass 404 recovered on confirm (no leftover). "
        + "_patrol_2026-11-22_0818 USER_LOG (delivered 08:28) already includes (treat as already told; do not re-tell): "
        + f"盒子休眠 07:44:22-08:02:42 (1093s; STATS 84409901..84410189, 289t; official-filled {fill0744}; listener auto-restart 08:02:45); "
        + f"leftover official 404 W47N8@84409800 (listener {w47n8_84409800['distinct']}/100 range {w47n8_84409800['min']}..{w47n8_84409800['max']}; hole {w47n8_84409800['hole_ticks']} ticks {hole_range_txt(w47n8_84409800)}). "
        + "_patrol_2026-11-22_0725 USER_LOG (delivered 07:35) already includes (treat as already told; do not re-tell): "
        + f"盒子休眠 07:20:32-07:26:28 (356s; STATS 84409551..84409649, 99t; official-filled {fill0720}) and 06:50:03-07:02:08 (725s; STATS 84409111..84409299, 189t; official-filled {fill0650}); leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. "
        + "_patrol_2026-11-22_0625 USER_LOG t508s3614 already includes (treat as already told; do not re-tell): 盒子休眠 05:52:44-06:04:12 and 06:21:56-06:26:26. "
        + "_patrol_2026-11-22_0522 USER_LOG already includes (treat as already told; do not re-tell): 盒子休眠 04:41:06-04:59:17 and 05:17:11-05:23:17; 监听短中断 05:25:19-05:27:20; leftover official 404 W46N8@84407000 and W45N8@84407700. "
        + "Older already-told freezes through 04:18 / 03:47 / 02:44 and leftover official 404s through W45N8@84406400 / W46N8@84406600 / W46N8@84406700 and earlier remain already told. "
        + f"Official-filled freeze spans for the next patrol: 10:45 STATS 84412541..84412859 319t official-filled {fill1045}; 10:16 STATS 84412131..84412219 89t official-filled {fill1016}; 09:41 STATS 84411621..84411889 269t official-filled {fill0941}; 09:14 STATS 84411221..84411299 79t official-filled {fill0914}; 08:51 STATS 84410881..84411039 159t official-filled {fill0851}; 07:44 STATS 84409901..84410189 289t official-filled {fill0744}; 07:20 STATS 84409551..84409649 99t official-filled {fill0720}; 06:50 STATS 84409111..84409299 189t official-filled {fill0650}; 06:21 STATS 84408691..84408779 89t official-filled {fill0621}; 05:52 STATS 84408271..84408449 179t official-filled {fill0552}; 05:17 STATS 84407741..84407849 109t official-filled {fill0517}; 05:25 short WS STATS 84407871..84407899 29t official-filled {fill0525}; 04:41 STATS 84407211..84407499 289t official-filled {fill0441}; 04:18 STATS 84406881..84406949 69t official-filled {fill0418}; 03:47 STATS 84406431..84406719 289t official-filled {fill0347}; 02:44 STATS 84405501..84405799 299t official-filled {fill0244}. "
        + "_patrol_2026-11-22_0422 USER_LOG already includes (treat as already told; do not re-tell): 盒子休眠 03:47:58-04:06:12 and 04:18:46-04:22:28; leftover official 404 W45N8@84406400 / W46N8@84406600 / W46N8@84406700. "
        + "Single listener 2409363 since 11:06:32 after the 10:45 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "
        + f"listener_rot {rot} tips {tips}."
        + NL
    )

'''
t = t[:start] + now_txt + t[end:]

start = t.index("    verify = (")
end = t.index('    (DIR / "verify.txt").write_text(verify)')
verify = r'''    verify = (
        f"wrap {now}" + NL
        + f"ok_quiet=True inserted_total={inserted_total}" + NL
        + f"first_pass game.time=84412884 published_bases=84412100..84412700 reconstructed=84412101..84412800 (700) "
        + f"34/35 200 missing_chunks=1 W47N7@84412400 inserted_first={inserted_first} already_in_db=13275 ts_realigned_first=0 (no rows over 45s); tick_s_check no corrective, still_over_45s=0 (in_use=all_mean 4.16192)" + NL
        + "confirm/retry2/late still_404 W47N7@84412400 inserted=0 (NEW leftover, not yet told; fold into next 1h patrol). Already-told leftover official 404s W45N7@84411500 / W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900 and older aged out of window start 84412101, already told in the 10:37 patrol or earlier, not retried" + NL
        + f"just_published 84412800 at {jp_at} gt={jp_gt} all_five_200={jp_all5} script={script_sum} actual={actual_sum} script_by={script_by} actual_by={actual}" + NL
        + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_applied={bool(tick.get('corrective_applied'))} nfix={corrective}" + NL
        + f"window_db={window_db}" + NL
        + f"dup={dup}" + NL
        + f"tips={tips}" + NL
        + f"listener {listener_lines} rot={rot} yield_absent={yield_absent}" + NL
        + f"gaps 1045={{ { {r: gaps['gap_1045_1106'][r]['fill'] for r in ROOMS} } }} 1016={{ { {r: gaps['gap_1016_1022'][r]['fill'] for r in ROOMS} } }} 0941={{ { {r: gaps['gap_0941_0959'][r]['fill'] for r in ROOMS} } }} 0914={{ { {r: gaps['gap_0914_0919'][r]['fill'] for r in ROOMS} } }} 0851={{ { {r: gaps['gap_0851_0901'][r]['fill'] for r in ROOMS} } }} 0744={{ { {r: gaps['gap_0744_0802'][r]['fill'] for r in ROOMS} } }} 0720={{ { {r: gaps['gap_0720_0726'][r]['fill'] for r in ROOMS} } }} 0650={{ { {r: gaps['gap_0650_0702'][r]['fill'] for r in ROOMS} } }} 0621={{ { {r: gaps['gap_0621_0626'][r]['fill'] for r in ROOMS} } }} 0552={{ { {r: gaps['gap_0552_0604'][r]['fill'] for r in ROOMS} } }} 0517={{ { {r: gaps['gap_0517_0523'][r]['fill'] for r in ROOMS} } }} 0525={{ { {r: gaps['gap_0525_0527'][r]['fill'] for r in ROOMS} } }} 0441={{ { {r: gaps['gap_0441_0459'][r]['fill'] for r in ROOMS} } }}" + NL
        + f"holes={holes}" + NL
        + "already_told by _patrol_2026-11-22_1022 USER_LOG t508s3620 (do not re-tell): 盒子休眠 10:16:39-10:22:23 and 09:41:41-09:59:05; leftover official 404 W45N7@84411500. Already told by _patrol_2026-11-22_0918 USER_LOG (do not re-tell): 盒子休眠 08:51:14-09:01:02 and 09:14:15-09:19:05; W47N7@84411200 first-pass 404 recovered on confirm (no leftover). Already told by _patrol_2026-11-22_0818 USER_LOG (do not re-tell): 盒子休眠 07:44:22-08:02:42; leftover official 404 W47N8@84409800. Already told by _patrol_2026-11-22_0725 USER_LOG (do not re-tell): 盒子休眠 07:20:32-07:26:28 and 06:50:03-07:02:08; leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. Already told by _patrol_2026-11-22_0625 USER_LOG t508s3614 (do not re-tell): 盒子休眠 05:52:44-06:04:12 and 06:21:56-06:26:26. Already told by _patrol_2026-11-22_0522 USER_LOG (do not re-tell): 盒子休眠 04:41:06-04:59:17 and 05:17:11-05:23:17; 监听短中断 05:25:19-05:27:20; leftover official 404 W46N8@84407000 and W45N8@84407700. Older already-told freezes through 04:18 / 03:47 / 02:44 and leftover official 404s through W45N8@84406400 / W46N8@84406600 / W46N8@84406700 and earlier." + NL
        + "ok_quiet=True new_official_404_untold=[W47N7@84412400] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[10:45:15-11:06:19 STATS 84412541..84412859 319t] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_1100 concurrent_patrol=already_delivered_1037_do_not_write_its_folder concurrent_12h_review=already_delivered_0833_do_not_write_its_folder" + NL
    )

'''
t = t[:start] + verify + t[end:]

t = t.replace(
    '"new_official_404_untold": [],',
    '"new_official_404_untold": ["W47N7@84412400"],',
)
t = t.replace(
    '"still_untold_from_1000": ["W45N7@84411500"],',
    '"still_untold_from_1000": [],',
)
t = t.replace(
    '"new_box_freeze_untold": ["10:16:39-10:22:23 STATS 84412131..84412219 89t"],',
    '"new_box_freeze_untold": ["10:45:15-11:06:19 STATS 84412541..84412859 319t"],',
)
t = t.replace(
    '"still_untold_freeze_from_1000": ["09:41:41-09:59:05 STATS 84411621..84411889 269t"],',
    '"still_untold_freeze_from_1000": [],',
)
t = t.replace(
    '"concurrent_patrol": "already_delivered_0929_do_not_write_its_folder",',
    '"concurrent_patrol": "already_delivered_1037_do_not_write_its_folder",',
)
t = t.replace(
    '"first_pass_realign": "committed ts_realigned=13903; tick_s_check corrective first 272 rows, still_over_45s=0 (in_use=first 4.19489)",',
    '"first_pass_realign": "committed ts_realigned=0; tick_s_check no corrective, still_over_45s=0 (in_use=all_mean 4.16192)",',
)

if "T0, T1 = 84411601" in t:
    raise SystemExit("T0/T1 not updated")
if "JP_BASE = 84412300" in t:
    raise SystemExit("JP_BASE not updated")
if "inserted_first = 2940" in t:
    raise SystemExit("inserted_first not updated")
if "_halfhour_2026-11-22_1030" in t:
    print("WARN leftover 1030 path still in file")

compile(t, str(p), "exec")
p.write_text(t)
print("wrapup_write.py patched and syntax-ok")
