#!/usr/bin/env python3
from pathlib import Path

p = Path("/workspace/screeps/state/_halfhour_2026-11-22_2030/wrapup_write.py")
t = p.read_text()

def must_replace(old, new, label):
    global t
    if old not in t:
        raise SystemExit(f"NOT FOUND: {label}")
    n = t.count(old)
    t = t.replace(old, new)
    print(f"OK {label} ({n}x)")

must_replace("T0, T1 = 84419801, 84420500", "T0, T1 = 84420301, 84421000", "T0 T1")
must_replace("JP_BASE = 84420500", "JP_BASE = 84421000", "JP_BASE")
must_replace("inserted_first = 12774", "inserted_first = 5152", "inserted_first")
must_replace("first = tick.get(\"tick_s_used_first_pass\") or 4.20156", "first = tick.get(\"tick_s_used_first_pass\") or 4.22106", "first default")

must_replace(
    "        + \"post-JP leftover retry at 2026-11-22 20:09:10 Asia/Hong_Kong gt=84420650 still_404=['W45N7@84419300', 'W45N8@84419600'] recovered=[] inserted=0. \"",
    "        + \"post-JP leftover retry at 2026-11-22 20:44:24 Asia/Hong_Kong gt=None skipped no targets inserted=0. \"",
    "postjp line",
)
must_replace(
    "        + \"First pass started 2026-11-22 20:03:39 Asia/Hong_Kong and finished 20:04:23 (exit=0): \"",
    "        + \"First pass started 2026-11-22 20:36:57 Asia/Hong_Kong and finished 20:37:38 (exit=0): \"",
    "first pass times",
)
must_replace(
    "        + \"inserted=12774 already_in_db=12826, first-pass realign moved 368 rows ts_realigned_first=368 \"",
    "        + \"inserted=5152 already_in_db=21610, first-pass realign moved 0 rows ts_realigned_first=0 \"",
    "inserted/already",
)
must_replace(
    "        + \"(first-interval tick_s printed 4.202, exact 4.20156). No concurrent first-pass of this window (19:30 half-hour already official-filled through 84419900 / just-published 84420000; overlap accounts for already_in_db=12826). \"",
    "        + \"(first-interval tick_s printed 4.221, exact 4.22106). Overlap with the 20:11 half-hour (official 84419801..84420500 / JP through 84420600) and the 20:27 patrol (official+JP through 84420800) accounts for already_in_db=21610. \"",
    "tick_s first-pass overlap",
)
must_replace(
    "        + \"Last delivered USER_LOG is ~19:36 _patrol_2026-11-22_1924 (finished_at 19:36:36); do not re-tell it. No concurrent 1h patrol this run. 12h review last delivered ~08:33 and had not started a _review12h_2026-11-22_20 folder during this collect; do not re-tell or write its folder. \"",
    "        + \"Last delivered USER_LOG is ~20:27 _patrol_2026-11-22_2016 (finished_at 20:26:55); do not re-tell it. No concurrent 1h patrol this run. Concurrent 12h review is running in _review12h_2026-11-22_20; do not re-tell or write its folder. \"",
    "last delivered / 12h",
)
must_replace(
    "        + \"19:30 half-hour already official-filled through 84419900 / just-published 84420000. 19:36 patrol already official-filled and told leftover 404 W45N7@84419300 and W45N8@84419600 (still 404 after 19:00, 1924, and 1930 confirm/retry). 18:38 patrol already told leftover 404 all five @84418900 and W45N7@84419000; this run is overlap of the 19:30 window plus new official 84420100..84420400 and just-published 84420500. \"",
    "        + \"20:11 half-hour already official-filled 84419801..84420500 / just-published through 84420600, leftover official 404 none new. 20:27 patrol already official-filled official+JP through 84420800 all five 800/800 and already told leftover 404 W45N7@84419300 and W45N8@84419600 plus 盒子休眠 19:43:54-19:59:40. This run is overlap of that window plus new official 84420900 and just-published 84421000. \"",
    "overlap context",
)
must_replace(
    "aged out of window start 84419801",
    "aged out of window start 84420301",
    "window start age-out",
)
must_replace(
    '        + f"Just-published 84420500 was not in first pass (first pass ended at published 84420400 / reconstructed 84419801..84420500 at "',
    '        + f"Just-published 84421000 was not in first pass (first pass ended at published 84420900 / reconstructed 84420301..84421000 at "',
    "JP intro",
)
must_replace(
    '        + f"game.time=84420573, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} (first +140 at 20:08:36 gt=84420642 recovered all five rooms; no +200/+300 retry needed). "',
    '        + f"game.time=84421046, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} (first +140 at 20:43:43 gt=84421141 recovered all five rooms; no +200/+300 retry needed). "',
    "JP times",
)
must_replace(
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=368 corrective={corrective} "',
    '        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=0 corrective={corrective} "',
    "ts_realigned in now_txt",
)
must_replace(
    '        + f"(later-mean {later}; first-pass realign moved 368 rows ts_realigned_first=368; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use}; no corrective realign, already inside 45s gate still_over_45s=0, skipped_cross_chunk=0). "',
    '        + f"(later-mean {later}; first-pass realign moved 0 rows ts_realigned_first=0; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use}; no corrective realign, already inside 45s gate still_over_45s=0, skipped_cross_chunk=0). "',
    "tick_s_check now_txt",
)

# 19300/19600 this-run retry narrative -> aged out, not retried
must_replace(
    '''        + f"Already-told leftover official 404 W45N7@84419300 and W45N8@84419600 (already told in the ~19:36 _patrol_2026-11-22_1924 USER_LOG; still 404 after 19:00, 1924, and 1930 confirm/retry; this overlap retried them again, still 404, do not re-tell as new): W45N7@84419300 (confirm 20:05:57 gt=84420605, retry2 20:06:23 gt=84420611, late 20:06:54 gt=84420618, and post-JP 20:09:10 gt=84420650, all still 404, inserted=0; later official chunks including 84419400/84419500/84419700/84419800 already 200 including W45N7, so leftover official-history hole; slightly before window start 84419801 but near enough to retry; listener {w45n7_84419300['distinct']}/100 range {w45n7_84419300['min']}..{w45n7_84419300['max']}; hole {w45n7_84419300['hole_ticks']} ticks {hole_range_txt(w45n7_84419300)}) and W45N8@84419600 (other rooms 200; later official 84419700+ already 200 for W45N8, so leftover hole not unpublished-latest lag; near window start, confirm/retry2/late/post-JP still 404, inserted=0; listener {w45n8_84419600['distinct']}/100 range {w45n8_84419600['min']}..{w45n8_84419600['max']}; hole {w45n8_84419600['hole_ticks']} ticks {hole_range_txt(w45n8_84419600)}). "''',
    '''        + f"Already-told leftover official 404 W45N7@84419300 and W45N8@84419600 (already told in the ~19:36 _patrol_2026-11-22_1924 USER_LOG and again in the ~20:27 _patrol_2026-11-22_2016 USER_LOG; the 20:11 half-hour overlap retried them, still 404; this run they aged out of window start 84420301 and were not retried; do not re-tell as new): W45N7@84419300 (listener {w45n7_84419300['distinct']}/100 range {w45n7_84419300['min']}..{w45n7_84419300['max']}; hole {w45n7_84419300['hole_ticks']} ticks {hole_range_txt(w45n7_84419300)}) and W45N8@84419600 (listener {w45n8_84419600['distinct']}/100 range {w45n8_84419600['min']}..{w45n8_84419600['max']}; hole {w45n8_84419600['hole_ticks']} ticks {hole_range_txt(w45n8_84419600)}). "''',
    "19300/19600 this-run",
)

# NEW freeze sentence starts with "NEW 盒子休眠 this run:"
old_new = "NEW 盒子休眠 this run: 19:43:54-19:59:40 (946s, box_pauses row; STATS 84420281..84420519, 239t; official-filled {fill1943}; listener auto-restart 19:59:43, python 2641627 started 19:59:53, parent 4035476) -- NOT YET TOLD; fold into the next 1h patrol. NEW 监听短中断 this run: none."
new_new = "NEW 盒子休眠 this run: none. 盒子休眠 19:43:54-19:59:40 (946s, box_pauses row; STATS 84420281..84420519, 239t; official-filled {fill1943}; listener auto-restart 19:59:43, python 2641627 started 19:59:53, parent 4035476) -- already told in the ~20:27 _patrol_2026-11-22_2016 USER_LOG; do not re-tell. NEW 监听短中断 this run: none."
if old_new not in t:
    raise SystemExit("NEW freeze sentence not found")
t = t.replace(old_new, new_new)
print("OK NEW freeze sentence")

# prepend 20:27 patrol to the already-told patrol list in now_txt
must_replace(
    "_patrol_2026-11-22_1924 USER_LOG (delivered ~19:36, finished_at 19:36:36; treat as already told; do not re-tell): leftover official 404 W45N7@84419300 and W45N8@84419600; 监听短中断 19:12:43-19:12:57; 盒子休眠 through 17:41:00-18:04:50 and earlier.",
    "_patrol_2026-11-22_2016 USER_LOG (delivered ~20:27, finished_at 20:26:55, state-only bb6d55bd, live still 2b5398f7; treat as already told; do not re-tell): W47 upgrade HOLDS (fifth dual after 15:32); home upgrade FORMAL already cleared; storage formal still cleared; W47 threat/seal already told; 盒子休眠 19:43:54-19:59:40; leftover official 404 W45N7@84419300 and W45N8@84419600. _patrol_2026-11-22_1924 USER_LOG (delivered ~19:36, finished_at 19:36:36; treat as already told; do not re-tell): leftover official 404 W45N7@84419300 and W45N8@84419600; 监听短中断 19:12:43-19:12:57; 盒子休眠 through 17:41:00-18:04:50 and earlier.",
    "prepend 2016 patrol in now_txt",
)

# verify first_pass line
must_replace(
    '        + f"first_pass game.time=84420573 published_bases=84419800..84420400 reconstructed=84419801..84420500 (700) "',
    '        + f"first_pass game.time=84421046 published_bases=84420300..84420900 reconstructed=84420301..84421000 (700) "',
    "verify first_pass header",
)
must_replace(
    '        + f"35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=12826 ts_realigned_first=368; tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_first_nfix=0" + NL',
    '        + f"35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=21610 ts_realigned_first=0; tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_first_nfix=0" + NL',
    "verify first_pass numbers",
)
must_replace(
    '        + f"confirm/retry2/late/postjp still_404 W45N7@84419300 / W45N8@84419600 inserted=0 (already told in ~19:36 _patrol_2026-11-22_1924; this overlap retried, still 404; do not re-tell as new). Already-told leftover official 404 all five @84418900 and W45N7@84419000 aged out of window start 84420301, already told in ~18:38 _patrol_2026-11-22_1822 USER_LOG; not retried this pass; do not re-tell. Already-told leftover official 404s W45N8@84415500 / W46N8@84414700 / W46N8@84413700 / W47N7@84412400 / W45N7@84411500 / W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900 and older aged out of window start 84420301, already told in the 14:28 or earlier patrol, not retried" + NL',
    '        + f"confirm/retry2/late/postjp skipped no targets inserted=0. Already-told leftover official 404 W45N7@84419300 and W45N8@84419600 aged out of window start 84420301 (already told in ~19:36 _patrol_2026-11-22_1924 and ~20:27 _patrol_2026-11-22_2016; 20:11 overlap retried, still 404; not retried this pass; do not re-tell as new). Already-told leftover official 404 all five @84418900 and W45N7@84419000 aged out of window start 84420301, already told in ~18:38 _patrol_2026-11-22_1822 USER_LOG; not retried this pass; do not re-tell. Already-told leftover official 404s W45N8@84415500 / W46N8@84414700 / W46N8@84413700 / W47N7@84412400 / W45N7@84411500 / W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900 and older aged out of window start 84420301, already told in the 14:28 or earlier patrol, not retried" + NL',
    "verify confirm line",
)
must_replace(
    "already_told by _patrol_2026-11-22_1924 USER_LOG ~19:36 finished_at 19:36:36 (do not re-tell): leftover official 404 W45N7@84419300 and W45N8@84419600; 监听短中断 19:12:43-19:12:57; 盒子休眠 through 17:41:00-18:04:50 and earlier.",
    "already_told by _patrol_2026-11-22_2016 USER_LOG ~20:27 finished_at 20:26:55 (do not re-tell): 盒子休眠 19:43:54-19:59:40; leftover official 404 W45N7@84419300 and W45N8@84419600. already_told by _patrol_2026-11-22_1924 USER_LOG ~19:36 finished_at 19:36:36 (do not re-tell): leftover official 404 W45N7@84419300 and W45N8@84419600; 监听短中断 19:12:43-19:12:57; 盒子休眠 through 17:41:00-18:04:50 and earlier.",
    "verify already_told prepend 2016",
)
must_replace(
    "ok_quiet=True new_official_404_untold=[] still_untold_from_1230=[] still_untold_from_1100=[] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=['盒子休眠 19:43:54-19:59:40 STATS 84420281..84420519'] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_2000 concurrent_patrol=none_already_delivered_1924_finished_1936 concurrent_12h_review=not_started_yet_last_delivered_0833_do_not_write_its_folder",
    "ok_quiet=True new_official_404_untold=[] still_untold_from_1230=[] still_untold_from_1100=[] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_2030 concurrent_patrol=none_already_delivered_2016_finished_2026 concurrent_12h_review=running_review12h_2026-11-22_20_do_not_write_its_folder",
    "verify ok_quiet flags",
)

must_replace(
    '        "new_official_404_untold": [],  # W45N7@84419300 and W45N8@84419600 already told in 19:36 patrol; this overlap retried, still 404; do not re-tell as new',
    '        "new_official_404_untold": [],  # W45N7@84419300 and W45N8@84419600 already told in 19:36 and 20:27 patrols; aged out of this window, not retried; do not re-tell as new',
    "snap 404 comment",
)
must_replace(
    '        "new_box_freeze_untold": ["盒子休眠 19:43:54-19:59:40 STATS 84420281..84420519"],',
    '        "new_box_freeze_untold": [],  # 19:43:54-19:59:40 already told in 20:27 patrol',
    "snap freeze",
)
must_replace(
    '        "new_short_ws_untold": [],  # 19:12 already told in 19:36 patrol',
    '        "new_short_ws_untold": [],  # none new; 19:12 already told in 19:36 patrol',
    "snap shortws",
)
must_replace(
    '        "concurrent_patrol": "none_already_delivered_1924_finished_1936",',
    '        "concurrent_patrol": "none_already_delivered_2016_finished_2026",',
    "snap patrol",
)
must_replace(
    '        "concurrent_12h_review": "not_started_yet_last_delivered_0833_do_not_write_its_folder",',
    '        "concurrent_12h_review": "running_review12h_2026-11-22_20_do_not_write_its_folder",',
    "snap 12h",
)
must_replace(
    '        "first_pass_realign": "moved 368 rows ts_realigned_first=368; tick_s_in_use=later_raw 4.18009 after tick_s_check live-anchor-best, no corrective, still_over_45s=0",',
    '        "first_pass_realign": "moved 0 rows ts_realigned_first=0; tick_s_in_use=first 4.22106 after tick_s_check live-anchor-best, no corrective, still_over_45s=0",',
    "snap realign",
)

p.write_text(t)
print("wrapup_write.py patched")

# leftover stale numbers check
stale = []
for s in ["inserted=12774", "already_in_db=12826", "ts_realigned_first=368", "4.20156", "20:03:39", "game.time=84420573 published_bases=84419800", "T0, T1 = 84419801, 84420500", "inserted_first = 12774", "new_box_freeze_untold=['盒子休眠 19:43:54", "this_halfhour_2000", "NOT YET TOLD"]:
    if s in t:
        stale.append(s)
print("STALE leftover:", stale or "none")
