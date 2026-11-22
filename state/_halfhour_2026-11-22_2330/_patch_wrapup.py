#!/usr/bin/env python3
from pathlib import Path
src = Path("/workspace/screeps/state/_halfhour_2026-11-22_2300/wrapup_write.py")
dst = Path("/workspace/screeps/state/_halfhour_2026-11-22_2330/wrapup_write.py")
t = src.read_text()
pairs = [
    ("_halfhour_2026-11-22_2300", "_halfhour_2026-11-22_2330"),
    ("T0, T1 = 84422501, 84423200", "T0, T1 = 84422901, 84423600"),
    ("JP_BASE = 84423200", "JP_BASE = 84423600"),
    ("inserted_first = 19379", "inserted_first = 1545"),
    ("or 4.15209", "or 4.25489"),
    ("First pass 35/35 official GETs 200, missing_chunks=0. ",
     "First pass 32/35 official GETs 200, missing_chunks=3 W47N8@84423500, W45N8@84423500, W47N7@84423500. "),
    ("First pass started 2026-11-22 23:10:07 Asia/Hong_Kong and finished 23:11:00 (exit=0): ",
     "First pass started 2026-11-22 23:34:57 Asia/Hong_Kong and finished 23:35:39 (exit=0): "),
    ("inserted=19379 already_in_db=9762, first-pass realign moved 0 rows ts_realigned_first=0 ",
     "inserted=1545 already_in_db=22962, first-pass realign moved 1243 rows ts_realigned_first=1243 "),
    ("(first-interval tick_s printed 4.152, exact 4.15209). Overlap with the 22:32 half-hour (official 84421801..84422500 / JP 84422500) and the 22:37 patrol accounts for already_in_db=9762. ",
     "(first-interval tick_s printed 4.255, exact 4.25489). Overlap with the 23:17 half-hour (official 84422501..84423200 / JP 84423200) and the 23:31 patrol (official+JP through 84423500) accounts for already_in_db=22962. "),
    ("No same-payload extra-row collision this first pass. ",
     "Confirm 23:36:55 gt=84423635 recovered all three first-pass 404s inserted=1548 still_404=[]. No same-payload extra-row collision this first pass. "),
    ("Last delivered USER_LOG is ~22:37 _patrol_2026-11-22_2224 (finished_at 22:36:58); do not re-tell it. No concurrent 1h patrol folder is being written by this run. ",
     "Last delivered USER_LOG is ~23:31 _patrol_2026-11-22_2316 (finished_at 23:32:40); do not re-tell it. This half-hour did not write a patrol or 12h-review folder. "),
    ("22:32 half-hour already official-filled 84421801..84422500 / just-published 84422500, leftover official 404 W45N8@84422100 and W45N8@84422400 (already told in the 22:37 patrol). 22:37 patrol already told leftover 404 W45N8@84422100 and W45N8@84422400 plus 盒子休眠 21:45:57-22:04:37 (and 20:49:49-20:59:53 and 19:43:54-19:59:40). This run is overlap of that window plus new official 84422500..84423100 and just-published 84423200. ",
     "23:17 half-hour already official-filled 84422501..84423200 / just-published 84423200. 23:31 patrol already official+JP filled through 84423500, and already told leftover 404 W45N8@84422100 and W45N8@84422400 plus 盒子休眠 22:43:27-23:05:49 (and 21:45:57-22:04:37 and 20:49:49-20:59:53 and 19:43:54-19:59:40). This run is overlap of that window plus new official 84422900..84423500 and just-published 84423600. "),
    ("aged out of window start 84422501 and were not retried this pass (already told in the 22:37 _patrol_2026-11-22_2224 USER_LOG; do not re-tell). ",
     "aged out of window start 84422901 and were not retried this pass (already told in the 22:37 patrol and mentioned as already-told in the 23:31 _patrol_2026-11-22_2316 USER_LOG; do not re-tell). "),
    ("also aged out of window start 84422501 and were not retried this pass; do not re-tell. ",
     "also aged out of window start 84422901 and were not retried this pass; do not re-tell. "),
    ("Just-published 84423200 was not in first pass (first pass ended at published 84423100 / reconstructed 84422501..84423200 at ",
     "Just-published 84423600 was not in first pass (first pass ended at published 84423500 / reconstructed 84422901..84423600 at "),
    ("game.time=84423254, 35/35 200, missing_chunks=0). GET at ",
     "game.time=84423607, 32/35 200, missing_chunks=3 recovered on confirm). GET at "),
    ("NEW leftover official 404 this run: none. ",
     "NEW leftover official 404 this run: none (first-pass 404s W47N8@84423500, W45N8@84423500, W47N7@84423500 all recovered on confirm). "),
    ("aged out of window start 84422501 and were not retried this pass; already told in the ~22:37 _patrol_2026-11-22_2224 USER_LOG; do not re-tell. ",
     "aged out of window start 84422901 and were not retried this pass; already told in the ~22:37 patrol and mentioned as already-told in the ~23:31 _patrol_2026-11-22_2316 USER_LOG; do not re-tell. "),
    ("tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=0 corrective={corrective} ",
     "tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=1243 corrective={corrective} "),
    ("(later-mean {later}; first-pass realign moved 0 rows with first-interval 4.15209, over45=0 vs first; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use} inside 45s gate, no corrective realign, skipped_cross_chunk=0). ",
     "(later-mean {later}; first-pass realign moved 1243 rows with first-interval 4.25489, over45=0 vs first after that realign; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use} inside 45s gate, no corrective realign, skipped_cross_chunk=0). "),
    ("NEW 盒子休眠 this run 22:43:27-23:05:49 Asia/Hong_Kong (1334s, box_pauses row; STATS 84422871..84423199, 329 t; official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476). ",
     "NEW 盒子休眠 this run: none. NEW 监听短中断 this run: none. Already-told 盒子休眠 22:43:27-23:05:49 (1334s; STATS 84422871..84423199 official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476; already told in the 23:31 patrol; do not re-tell). "),
    ("after the NEW 盒子休眠 22:43:27-23:05:49 auto-restart",
     "after the already-told 盒子休眠 22:43:27-23:05:49 auto-restart"),
    ('"new_box_freeze_untold": ["22:43:27-23:05:49"],',
     '"new_box_freeze_untold": [],'),
    ('"concurrent_patrol": "none",',
     '"concurrent_patrol": "already_delivered_patrol_2026-11-22_2316_do_not_write_its_folder",'),
    ('"first_pass_realign": "moved 0 rows ts_realigned_first=0 with first=4.15209; tick_s_check live-anchor-best later_raw 4.16048, corrective nfix=0, after still_over_45s=0",',
     '"first_pass_realign": "moved 1243 rows ts_realigned_first=1243 with first=4.25489; tick_s_check live-anchor-best span_mean 4.22644, corrective nfix=0, after still_over_45s=0",'),
    ("first_pass_source=this_halfhour_2300 concurrent_patrol=none ",
     "first_pass_source=this_halfhour_2330 concurrent_patrol=already_delivered_patrol_2026-11-22_2316_do_not_write_its_folder "),
    ("new_box_freeze_untold=[22:43:27-23:05:49] ",
     "new_box_freeze_untold=[] "),
]
# verify paragraph lead
pairs.append((
    "NEW 盒子休眠 this run 22:43:27-23:05:49 (1334s; STATS 84422871..84423199 official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476). NEW leftover official 404 none this run. already_told by _patrol_2026-11-22_2224 USER_LOG ~22:37 finished_at 22:36:58 (do not re-tell): 盒子休眠 21:45:57-22:04:37; leftover official 404 W45N8@84422100 and W45N8@84422400. ",
    "NEW 盒子休眠 this run: none. NEW leftover official 404 none this run (first-pass W47N8/W45N8/W47N7@84423500 recovered on confirm). already_told by _patrol_2026-11-22_2316 USER_LOG ~23:31 finished_at 23:32:40 (do not re-tell): 盒子休眠 22:43:27-23:05:49 (STATS 84422871..84423199 official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476). already_told by _patrol_2026-11-22_2224 USER_LOG ~22:37 finished_at 22:36:58 (do not re-tell): 盒子休眠 21:45:57-22:04:37; leftover official 404 W45N8@84422100 and W45N8@84422400. ",
))

missing = []
for i, (old, new) in enumerate(pairs):
    n = t.count(old)
    expect = 0 if not old else (2 if i == 0 else 1)
    # i==0 is the folder name, appears in DIR and source= text; replace all.
    if i == 0:
        if n < 1:
            missing.append((i, n, old[:80]))
        else:
            t = t.replace(old, new)
        continue
    if n != 1:
        missing.append((i, n, old[:80]))
    else:
        t = t.replace(old, new, 1)
if missing:
    for i, n, s in missing:
        print(f"FAIL i={i} count={n}: {s!r}")
    raise SystemExit("replacement counts not 1")
dst.write_text(t)
print("wrapup_write.py written", len(t))
print("ok")
