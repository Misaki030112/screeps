#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-22_2200/wrapup_write.py")
t = p.read_text()
n = 0
q = chr(34)

def repl(old, new, label):
    global t, n
    if old not in t:
        raise SystemExit("NOT FOUND: " + label)
    c = t.count(old)
    t = t.replace(old, new)
    n += c
    print("ok", label, "count", c)

repl("window start 84420701", "window start 84421101", "window start")

repl(
    "post-JP leftover retry at 2026-11-22 21:11:51 Asia/Hong_Kong gt=None skipped no targets inserted=0. ",
    "post-JP leftover retry at 2026-11-22 21:39:38 Asia/Hong_Kong gt=None skipped no targets inserted=0. ",
    "postjp time",
)

repl(
    "First pass started 2026-11-22 21:04:33 Asia/Hong_Kong and finished 21:05:20 (exit=0): ",
    "First pass started 2026-11-22 21:33:49 Asia/Hong_Kong and finished 21:34:30 (exit=0): ",
    "first pass clock",
)

old_nums = (
    "inserted=10859 already_in_db=16517, first-pass realign moved 0 rows ts_realigned_first=0 " + q
    + chr(10)
    + "        + " + q + "(first-interval tick_s printed 4.138, exact 4.13804). Overlap with the 20:46 half-hour (official 84420301..84421000 / JP through 84421100) and the 20:27 patrol (official+JP through 84420800) accounts for already_in_db=16517. "
)
new_nums = (
    "inserted=3043 already_in_db=25736, first-pass realign moved 4464 rows ts_realigned_first=4464 " + q
    + chr(10)
    + "        + " + q + "(first-interval tick_s printed 4.206, exact 4.20551). Overlap with the 21:13 half-hour (official 84420701..84421400 / JP through 84421400) and the 21:27 patrol accounts for already_in_db=25736. "
)
repl(old_nums, new_nums, "first pass numbers")

repl(
    "Last delivered USER_LOG is ~20:27 _patrol_2026-11-22_2016 (finished_at 20:26:55); do not re-tell it. No concurrent 1h patrol this run. 12h review _review12h_2026-11-22_20 already completed ~20:37 (docs-only e7887bd9, not a game deploy); do not re-tell or write its folder. ",
    "Last delivered USER_LOG is ~21:27 _patrol_2026-11-22_2117 (finished_at 21:27:21); do not re-tell it. No concurrent 1h patrol this run. 12h review _review12h_2026-11-22_20 already completed ~20:37 (docs-only e7887bd9, not a game deploy); do not re-tell or write its folder. ",
    "last patrol",
)

repl(
    "20:46 half-hour already official-filled 84420301..84421000 / just-published through 84421100, leftover official 404 none new. 20:27 patrol already official-filled official+JP through 84420800 all five 800/800 and already told leftover 404 W45N7@84419300 and W45N8@84419600 plus 盒子休眠 19:43:54-19:59:40. This run is overlap of that window plus new official 84421100..84421300 and just-published 84421400. ",
    "21:13 half-hour already official-filled 84420701..84421400 / just-published through 84421400, leftover official 404 none new. 21:27 patrol already told leftover 404 W45N7@84419300 and W45N8@84419600 plus 盒子休眠 20:49:49-20:59:53 (and 19:43:54-19:59:40). This run is overlap of that window plus new official 84421500..84421700 and just-published 84421800. ",
    "overlap window",
)

repl(
    "Just-published 84421400 was not in first pass (first pass ended at published 84421300 / reconstructed 84420701..84421400 at ",
    "Just-published 84421800 was not in first pass (first pass ended at published 84421700 / reconstructed 84421101..84421800 at ",
    "jp header",
)

repl(
    "game.time=84421446, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} (first +140 at 21:11:14 gt=84421541 recovered all five rooms; no +200/+300 retry needed). ",
    "game.time=84421867, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} (first +140 at 21:38:59 gt=84421941 recovered all five rooms; no +200/+300 retry needed). ",
    "jp get",
)

repl(
    "tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=0 corrective={corrective} ",
    "tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=4464 corrective={corrective} ",
    "tick_s first0",
)

repl(
    "(later-mean {later}; first-pass realign moved 0 rows ts_realigned_first=0; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use}; no corrective realign, already inside 45s gate still_over_45s=0, skipped_cross_chunk=0). ",
    "(later-mean {later}; first-pass realign moved 4464 rows ts_realigned_first=4464; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use}; no corrective realign, already inside 45s gate still_over_45s=0, skipped_cross_chunk=0). ",
    "tick_s later",
)

repl(
    "and again in the ~20:27 _patrol_2026-11-22_2016 USER_LOG; the 20:11 half-hour overlap retried them, still 404; this run they aged out of window start 84421101 and were not retried; do not re-tell as new)",
    "and again in the ~20:27 _patrol_2026-11-22_2016 and ~21:27 _patrol_2026-11-22_2117 USER_LOG; the 20:11 half-hour overlap retried them, still 404; this run they aged out of window start 84421101 and were not retried; do not re-tell as new)",
    "404 already told 21:27",
)

repl(
    "NEW 盒子休眠 this run: 20:49:49-20:59:53 (596s, box_pauses row; STATS 84421221..84421389, 169t; official-filled {fill2049}; listener auto-restart 20:59:56, python 2672097 started 21:00:05, parent 4035476). Already-told 盒子休眠 19:43:54-19:59:40",
    "NEW 盒子休眠 this run: none. Already-told 盒子休眠 20:49:49-20:59:53 (596s, box_pauses row; STATS 84421221..84421389, 169t; official-filled {fill2049}; listener auto-restart 20:59:56, python 2672097 started 21:00:05, parent 4035476) -- already told in the ~21:27 _patrol_2026-11-22_2117 USER_LOG; do not re-tell. Already-told 盒子休眠 19:43:54-19:59:40",
    "new freeze none",
)

repl(
    "_patrol_2026-11-22_2016 USER_LOG (delivered ~20:27, finished_at 20:26:55, state-only bb6d55bd, live still 2b5398f7; treat as already told; do not re-tell): W47 upgrade HOLDS (fifth dual after 15:32);",
    "_patrol_2026-11-22_2117 USER_LOG (delivered ~21:27, finished_at 21:27:21, state 688ebe02, live still 2b5398f7; treat as already told; do not re-tell): W47 upgrade HOLDS (sixth dual after 15:32); home upgrade FORMAL already cleared; storage formal still cleared; W47 threat/seal already told; 盒子休眠 20:49:49-20:59:53; leftover official 404 W45N7@84419300 and W45N8@84419600. _patrol_2026-11-22_2016 USER_LOG (delivered ~20:27, finished_at 20:26:55, state-only bb6d55bd, live still 2b5398f7; treat as already told; do not re-tell): W47 upgrade HOLDS (fifth dual after 15:32);",
    "patrol 2117 preface",
)

repl(
    "NEW 盒子休眠 this run 20:49:49-20:59:53 (596s; STATS 84421221..84421389 official-filled all five; listener auto-restart 20:59:56 python 2672097 started 21:00:05). already_told by _patrol_2026-11-22_2016 USER_LOG ~20:27 finished_at 20:26:55 (do not re-tell): 盒子休眠 19:43:54-19:59:40; leftover official 404 W45N7@84419300 and W45N8@84419600.",
    "NEW 盒子休眠 this run none. already_told by _patrol_2026-11-22_2117 USER_LOG ~21:27 finished_at 21:27:21 (do not re-tell): 盒子休眠 20:49:49-20:59:53; leftover official 404 W45N7@84419300 and W45N8@84419600. already_told by _patrol_2026-11-22_2016 USER_LOG ~20:27 finished_at 20:26:55 (do not re-tell): 盒子休眠 19:43:54-19:59:40; leftover official 404 W45N7@84419300 and W45N8@84419600.",
    "verify new freeze",
)

repl(
    "new_box_freeze_untold=[20:49:49-20:59:53] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_2100 concurrent_patrol=none_already_delivered_2016_finished_2026",
    "new_box_freeze_untold=[] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_2130 concurrent_patrol=none_already_delivered_2117_finished_2127",
    "verify flags",
)

repl("just_published 84421400 at", "just_published 84421800 at", "verify jp base")

repl(
    '"new_official_404_untold": [],  # none this run; W45N7@84419300 and W45N8@84419600 already told in 19:36 and 20:27 patrols; aged out of this window start 84421101, not retried; do not re-tell as new',
    '"new_official_404_untold": [],  # none this run; W45N7@84419300 and W45N8@84419600 already told in 19:36, 20:27 and 21:27 patrols; aged out of this window start 84421101, not retried; do not re-tell as new',
    "snap 404 comment",
)

old_freeze = (
    '"new_box_freeze_untold": ["20:49:49-20:59:53 596s STATS 84421221..84421389 official-filled all five 169/169 listener auto-restart 20:59:56 python 2672097 started 21:00:05 parent 4035476"],  # not yet told; 19:43:54-19:59:40 already told in 20:27 patrol'
)
new_freeze = (
    '"new_box_freeze_untold": [],  # 20:49:49-20:59:53 already told in 21:27 patrol; 19:43:54-19:59:40 already told in 20:27 and 21:27 patrols'
)
repl(old_freeze, new_freeze, "snap freeze untold")

repl(
    '"concurrent_patrol": "none_already_delivered_2016_finished_2026",',
    '"concurrent_patrol": "none_already_delivered_2117_finished_2127",',
    "snap concurrent patrol",
)

repl(
    '"first_pass_realign": "moved 0 rows ts_realigned_first=0; tick_s_in_use=all_mean 4.17540 after tick_s_check live-anchor-best, no corrective, still_over_45s=0",',
    '"first_pass_realign": "moved 4464 rows ts_realigned_first=4464; tick_s_in_use=first 4.20551 after tick_s_check live-anchor-best, no corrective, still_over_45s=0",',
    "snap realign",
)

p.write_text(t)
print("TOTAL replacements", n)

for s in [
    "inserted_first = 3043",
    "T0, T1 = 84421101, 84421800",
    "JP_BASE = 84421800",
    "new_box_freeze_untold=[]",
    "ts_realigned_first=4464",
    "21:38:59",
    "_patrol_2026-11-22_2117",
]:
    print("has", s, s in t)
for s in [
    "inserted_first = 10859",
    "T0, T1 = 84420701, 84421400",
    "JP_BASE = 84421400",
    "new_box_freeze_untold=[20:49",
    "First pass started 2026-11-22 21:04:33",
    "this_halfhour_2100",
]:
    print("stale?", s, s in t)
