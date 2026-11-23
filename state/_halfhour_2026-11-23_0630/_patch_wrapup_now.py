#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-23_0600/wrapup_write.py")
t = p.read_text()

def sub(old, new, label):
    global t
    if old not in t:
        raise SystemExit(f"NOT FOUND: {label}")
    t = t.replace(old, new, 1)
    print("ok", label)

sub("    inserted_first = 300\n", "    inserted_first = 12706\n", "inserted_first")
sub(
    '    first = tick.get("tick_s_used_first_pass") or 4.22793\n',
    '    first = tick.get("tick_s_used_first_pass") or 4.32606\n',
    "first default",
)
sub(
    '    fill0516 = fill_txt(gaps["gap_0516_0525"])\n',
    '    fill0548 = fill_txt(gaps["gap_0548_0606"])\n    fill0516 = fill_txt(gaps["gap_0516_0525"])\n',
    "fill0548",
)

sub(
'''        + "First pass 34/35 official GETs 200, missing_chunks=1 W45N7@84428300. "
        + "First pass started 2026-11-23 05:34:32 Asia/Hong_Kong and finished 05:35:13 (exit=0): "
        + "inserted=300 already_in_db=25450, first-pass realign moved 1304 rows ts_realigned_first=1304 "
        + "(first-interval tick_s printed 4.228, exact 4.22793). Overlap with the 05:00 half-hour (official 84427501..84428200 / JP 84428200) and the concurrent 0516 patrol first pass (official 84425101..84428500 / JP 84428500) accounts for already_in_db=25450. "
        + "Confirm 05:36:48 gt=84428688 still_404=['W45N7@84428300'] inserted=0; retry2 05:37:34 gt=84428700 still 404 inserted=0; late 05:41:15 gt=84428750 still 404 inserted=0; post-JP leftover retry 05:41:26 gt=84428752 still 404 inserted=0. First-pass insert matched would_insert=300. "''',
'''        + "First pass 35/35 official GETs 200, missing_chunks=0. "
        + "First pass started 2026-11-23 06:09:46 Asia/Hong_Kong and finished 06:10:35 (exit=0): "
        + "inserted=12706 already_in_db=11048, first-pass realign moved 14041 rows ts_realigned_first=14041 "
        + "(first-interval tick_s printed 4.326, exact 4.32606). Overlap with the 05:30 half-hour (official 84427901..84428600 / JP 84428600) accounts for already_in_db=11048. "
        + "First-pass insert matched would_insert=12706. Already-told leftover W45N7@84428300 (near window start 84428401, not a first-pass 404 this window) was retried on confirm/retry2/late/postjp; do not label NEW. "''',
    "first-pass prose",
)

sub(
'''        + "Last delivered USER_LOG is ~05:38 _patrol_2026-11-23_0516 (finished_at 05:40:08); do not re-tell it. This half-hour did not write a patrol or 12h-review folder. Concurrent 0516 patrol already wrote USER_LOG.txt and finished_at 05:40:08 while this collect-only run was waiting for just-published 84428600. 12h review _review12h_2026-11-22_20 already completed ~20:37 (docs-only, LIVE still 2b5398f7, not a game deploy); do not re-tell or write its folder. "
        + "05:00 half-hour already official-filled 84427501..84428200 / just-published 84428200, wrap 05:12:54, with then-untold leftover official 404 W45N8@84426200 and then-untold 盒子休眠 04:53:04-04:58:42 / 04:20:59-04:35:45 / 03:52:38-03:58:50 / 03:22:33-03:29:51 / 02:51:37-02:58:39; those items are now already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG and must not be re-told. "''',
'''        + "Last delivered USER_LOG is ~05:38 _patrol_2026-11-23_0516 (finished_at 05:40:08); do not re-tell it. This half-hour did not write a patrol or 12h-review folder. No concurrent patrol this run. Quiet 05:30 half-hour _halfhour_2026-11-23_0530 already wrapped 05:45:16; do not re-tell that collect-only wrap. 12h review _review12h_2026-11-22_20 already completed ~20:37 (docs-only, LIVE still 2b5398f7, not a game deploy); do not re-tell or write its folder. "
        + "05:30 half-hour already official-filled 84427901..84428600 / just-published 84428600, wrap 05:45:16, with no NEW leftover official 404 or box freeze beyond the 0516 already-told set. "''',
    "USER_LOG prose",
)

sub(
'''        + f"Just-published 84428600 was not in first pass (first pass ended at published 84428500 / reconstructed 84427901..84428600 at game.time=84428656, 34/35 200, missing_chunks=1 W45N7@84428300, still 404 after confirm/retry2/late/postjp). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5}. "''',
'''        + f"Just-published 84429100 was not in first pass (first pass ended at published 84429000 / reconstructed 84428401..84429100 at game.time=84429119, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5}. "''',
    "JP prose",
)

sub(
'''        + f"W47N7 official empty_no_creep in this first-pass window: {empty_txt('W47N7')} (80 ticks 84428303..84428382 is the designed civilian hold during the W47N7 invader threat FSM recorded in the 0516 patrol, not a 404). "''',
'''        + f"W47N7 official empty_no_creep in this first-pass window: {empty_txt('W47N7')}. "''',
    "W47N7 empty",
)

sub(
'''        + f"Already-told leftover official 404 W45N7@84428300 (already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG finished_at 05:40:08; first-pass 404 in this window; confirm 05:36:48, retry2 05:37:34, late 05:41:15 and postjp 05:41:26 still 404, same as the 0516 patrol confirm/retry2; listener {w45n7_84428300['distinct']}/100 range {w45n7_84428300['min']}..{w45n7_84428300['max']}; hole {w45n7_84428300['hole_ticks']} ticks {hole_range_txt(w45n7_84428300)}; sits outside this run's already-told 05:16 freeze STATS 84428401..84428539) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84426200 (already told in the same ~05:38 0516 USER_LOG; previously still-untold from the 03:00 half-hour; not a first-pass 404 in this window; aged out of window start 84427901 and was not retried this pass; listener {w45n8_84426200['distinct']}/100 range {w45n8_84426200['min']}..{w45n8_84426200['max']}; hole {w45n8_84426200['hole_ticks']} ticks {hole_range_txt(w45n8_84426200)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84425500 and W45N8@84425800 (already told in the ~02:43 _patrol_2026-11-23_0216 USER_LOG and mentioned as already-told in the ~05:38 0516 USER_LOG; aged out of window start 84427901 and were not retried this pass; listener {w45n8_84425500['distinct']}/100 and {w45n8_84425800['distinct']}/100; holes {w45n8_84425500['hole_ticks']} ticks {hole_range_txt(w45n8_84425500)} and {w45n8_84425800['hole_ticks']} ticks {hole_range_txt(w45n8_84425800)}) are not labeled NEW this wrap; do not re-tell. "
        + "Already-told leftover official 404s W45N8@84422100 and W45N8@84422400 aged out of window start 84427901 and were not retried this pass (already told in the 22:37 patrol and mentioned as already-told later; do not re-tell). "
        + "NEW leftover official 404 none this run beyond what the 0516 USER_LOG already told (first pass 34/35 200, missing_chunks=1 W45N7@84428300, still 404 after confirm/retry2/late/postjp). NEW 盒子休眠 this run: none beyond the 05:16:36-05:25:46 freeze already told in the 0516 USER_LOG. NEW 监听短中断 this run: none. "''',
'''        + f"Already-told leftover official 404 W45N7@84428300 (already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG finished_at 05:40:08; not a first-pass 404 in this window; sits immediately before window start 84428401 so it was retried as near; confirm 06:12:18, retry2 06:12:20, and late/postjp still 404; listener {w45n7_84428300['distinct']}/100 range {w45n7_84428300['min']}..{w45n7_84428300['max']}; hole {w45n7_84428300['hole_ticks']} ticks {hole_range_txt(w45n7_84428300)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84426200 (already told in the same ~05:38 0516 USER_LOG; previously still-untold from the 03:00 half-hour; not a first-pass 404 in this window; aged out of window start 84428401 and was not retried this pass; listener {w45n8_84426200['distinct']}/100 range {w45n8_84426200['min']}..{w45n8_84426200['max']}; hole {w45n8_84426200['hole_ticks']} ticks {hole_range_txt(w45n8_84426200)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84425500 and W45N8@84425800 (already told in the ~02:43 _patrol_2026-11-23_0216 USER_LOG and mentioned as already-told in the ~05:38 0516 USER_LOG; aged out of window start 84428401 and were not retried this pass; listener {w45n8_84425500['distinct']}/100 and {w45n8_84425800['distinct']}/100; holes {w45n8_84425500['hole_ticks']} ticks {hole_range_txt(w45n8_84425500)} and {w45n8_84425800['hole_ticks']} ticks {hole_range_txt(w45n8_84425800)}) are not labeled NEW this wrap; do not re-tell. "
        + "Already-told leftover official 404s W45N8@84422100 and W45N8@84422400 aged out of window start 84428401 and were not retried this pass (already told in the 22:37 patrol and mentioned as already-told later; do not re-tell). "
        + "NEW leftover official 404 none this run (first pass 35/35 200, missing_chunks=0). NEW 盒子休眠 this run: 05:48:18-06:06:20 Asia/Hong_Kong — NOT YET TOLD; fold into the next 3h patrol. NEW 监听短中断 this run: none. "''',
    "404/NEW freeze now_txt",
)

sub(
'''        + f"Already-told 盒子休眠 05:16:36-05:25:46 Asia/Hong_Kong (545s, box_pauses row; STATS 84428401..84428539, 139t; official-filled {fill0516}; listener auto-restart 05:25:49, python 2883580 started 05:25:59, parent 4035476) was already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG; do not re-tell. "''',
'''        + f"NEW 盒子休眠 05:48:18-06:06:20 Asia/Hong_Kong (1075s, box_pauses row; STATS 84428841..84429079, 239t; official-filled {fill0548}; listener auto-restart 06:06:23, python 2899745 started 06:06:33, parent 4035476) is not yet told; fold into the next 3h patrol. "
        + f"Already-told 盒子休眠 05:16:36-05:25:46 Asia/Hong_Kong (545s, box_pauses row; STATS 84428401..84428539, 139t; official-filled {fill0516}; listener auto-restart 05:25:49, python 2883580 started 05:25:59, parent 4035476) was already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG; do not re-tell. "''',
    "insert NEW freeze before 0516",
)

sub(
'''        + "Single listener 2883580 since 05:25:59 after the already-told 盒子休眠 05:16:36-05:25:46 auto-restart 05:25:49 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "''',
'''        + "Single listener 2899745 since 06:06:33 after the NEW 盒子休眠 05:48:18-06:06:20 auto-restart 06:06:23 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "''',
    "listener now_txt",
)

p.write_text(t)
print("wrote wrapup after now_txt patches")
needles = [
    "NEW 盒子休眠 this run: none.",
    "new_box_freeze_untold=[]",
    "first_pass_source=this_halfhour_0530",
    "missing_chunks=1 W45N7@84428300",
    "moved 1304 rows",
    "Single listener 2883580",
    "inserted_first = 300",
    "fill0548",
    "new_box_freeze_untold=[05:48:18-06:06:20]",
]
for n in needles:
    print(("STILL" if n in t else "gone "), n)
