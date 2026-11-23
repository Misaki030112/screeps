#!/usr/bin/env python3
from pathlib import Path

p = Path("/workspace/screeps/state/_halfhour_2026-11-23_0900/wrapup_write.py")
src = p.read_text()

old = '    fill0818 = fill_txt(gaps["gap_0818_0822"])\n'
new = old + '    fill0854 = fill_txt(gaps["gap_0854_0905"])\n'
if old not in src:
    raise SystemExit("fill0818 marker not found")
if 'fill0854 = fill_txt' not in src:
    src = src.replace(old, new, 1)

NOW = r'''    now_txt = (
        first_txt
        + "---- wrap " + now + " ----" + NL
        + f"confirm at {confirm_at} gt={confirm_gt} still_404={confirm_still} recovered={confirm_rec} inserted={inserted_confirm}. "
        + f"retry2 at {retry_at} gt={retry_gt} still_404={retry_still} recovered={retry_rec} inserted={inserted_retry2}. "
        + f"late retry at {late_at} gt={late_gt} still_404={late_still} recovered={late_rec} inserted={inserted_late}. "
        + post_line
        + "First pass 31/35 official GETs 200, missing_chunks=4 (W47N8@84431000, W47N8@84431500, W45N8@84431500, W47N7@84431500). "
        + "First pass started 2026-11-23 09:09:08 Asia/Hong_Kong and finished 09:10:00 (exit=0): inserted=13025 already_in_db=10003 ts_realigned=90, printed tick_s=4.254 (exact first-interval 4.25357). Inserts committed. "
        + "Overlap with the 08:30 half-hour (official 84430301..84431000 / JP 84431000, leftover official 404 W47N8@84431000 still 404) accounts for already_in_db=10003. The three 84431500 first-pass 404s were publish lag and were recovered at confirm. "
        + "Aged-out already-told leftovers W47N7@84430800, W47N7@84430700, W46N8@84430500, W47N8@84429900, W47N7@84429300, W45N7@84428300, W45N8@84426200/25500/25800 were not retried this pass; do not relabel NEW. "
        + f"tick_s_check chose live-anchor-best first 4.25357 (first over45={vs_first.get('over45')} mean_off={vs_first.get('mean_off')}; later-mean {later} over45={vs_later.get('over45')} mean_off={vs_later.get('mean_off')}; prev_later over45={vs_prev.get('over45')} mean_off={vs_prev.get('mean_off')}; all_mean over45={vs_all.get('over45')}); corrective_applied={bool(tick.get('corrective_applied'))} nfix={corrective}; skipped_cross_chunk={skipped_chunk}. First interval already inside the 45s gate (over45=0, mean_off=+8.44s); later-mean also over45=0 but worse mean_off, so first 4.25357 was kept. prev_later was not applied. tick_s_in_use=4.25357 (first). "
        + "Last delivered USER_LOG is ~08:34 _patrol_2026-11-23_0821 (finished_at 08:34:04); do not re-tell it. The 12h review _review12h_2026-11-23_08 was already delivered ~08:30; do not re-tell it. This half-hour did not write a patrol or 12h-review folder and did not restart the listener, war_cmd, or pulse. "
        + "Quiet 08:30 half-hour _halfhour_2026-11-23_0830 already wrapped 08:49:44 (baseline correction 08:51:53 after discovering the concurrent 0821 USER_LOG); do not re-tell that collect-only wrap, but carry its still-untold leftover official 404 W47N8@84431000 into the next 3h patrol (do not relabel NEW this wrap). "
        + "Just-published 84431600 was not in first pass (first pass ended at published 84431500 / reconstructed 84430901..84431600 at game.time=84431601, 31/35 200, missing_chunks=4). "
        + f"GET at {jp_at} gt={jp_gt} all_five_200={all_five} still_404={jp_still} recovered={jp_rec} script inserted={jp_ins}. "
        + jp_retry_line
        + f"script={script_sum} actual={actual_sum}; {script_vs_txt}. "
        + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
        + f"W46N8 official empty_no_creep in this first-pass window: {empty_txt('W46N8')}. "
        + f"W47N8 official empty_no_creep in this first-pass window: {empty_txt('W47N8')}. "
        + f"W45N8 official empty_no_creep in this first-pass window: {empty_txt('W45N8')}. "
        + f"W45N7 official empty_no_creep in this first-pass window: {empty_txt('W45N7')}. "
        + f"W47N7 official empty_no_creep in this first-pass window: {empty_txt('W47N7')}. "
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} postjp={inserted_postjp} just_actual={actual_sum} total={inserted_total}. "
        + f"Leftover official 404 W47N8@84431000 (first recorded as a just-published leftover in the quiet 0830 half-hour; confirm {confirm_at} gt={confirm_gt}, retry2 {retry_at} gt={retry_gt}, late {late_at} gt={late_gt}, and postjp {post_at} gt={post_gt} still 404; listener {w47n8_84431000['distinct']}/100 range {w47n8_84431000['min']}..{w47n8_84431000['max']}; hole {w47n8_84431000['hole_ticks']} ticks {hole_range_txt(w47n8_84431000)}) is not labeled NEW this wrap; still NOT YET TOLD; fold into the next 3h patrol. "
        + f"Already-told leftover official 404 W47N7@84430800 (already told in the ~08:33 _patrol_2026-11-23_0821 USER_LOG finished_at 08:34:04; aged out of window start {T0} and was not retried this pass; listener {w47n7_84430800['distinct']}/100 range {w47n7_84430800['min']}..{w47n7_84430800['max']}; hole {w47n7_84430800['hole_ticks']} ticks {hole_range_txt(w47n7_84430800)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W47N7@84430700 (already told in the same ~08:33 0821 USER_LOG; aged out of window start {T0} and was not retried this pass; listener {w47n7_84430700['distinct']}/100 range {w47n7_84430700['min']}..{w47n7_84430700['max']}; hole {w47n7_84430700['hole_ticks']} ticks {hole_range_txt(w47n7_84430700)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W46N8@84430500 (already told in the same ~08:33 0821 USER_LOG; aged out of window start {T0} and was not retried this pass; listener {w46n8_84430500['distinct']}/100 range {w46n8_84430500['min']}..{w46n8_84430500['max']}; hole {w46n8_84430500['hole_ticks']} ticks {hole_range_txt(w46n8_84430500)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W47N8@84429900 (already told in the same ~08:33 0821 USER_LOG; aged out of window start {T0} and was not retried this pass; listener {w47n8_84429900['distinct']}/100 range {w47n8_84429900['min']}..{w47n8_84429900['max']}; hole {w47n8_84429900['hole_ticks']} ticks {hole_range_txt(w47n8_84429900)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W47N7@84429300 (already told in the same ~08:33 0821 USER_LOG; aged out of window start {T0} and was not retried this pass; listener {w47n7_84429300['distinct']}/100 range {w47n7_84429300['min']}..{w47n7_84429300['max']}; hole {w47n7_84429300['hole_ticks']} ticks {hole_range_txt(w47n7_84429300)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84428300 (already told in the ~08:33 0821 USER_LOG as already-told from the ~05:38 _patrol_2026-11-23_0516 USER_LOG; aged out of window start {T0} and was not retried this pass; listener {w45n7_84428300['distinct']}/100 range {w45n7_84428300['min']}..{w45n7_84428300['max']}; hole {w45n7_84428300['hole_ticks']} ticks {hole_range_txt(w45n7_84428300)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84426200 (already told in the ~05:38 0516 USER_LOG and mentioned as already-told in the ~08:33 0821 USER_LOG; aged out of window start {T0} and was not retried this pass; listener {w45n8_84426200['distinct']}/100 range {w45n8_84426200['min']}..{w45n8_84426200['max']}; hole {w45n8_84426200['hole_ticks']} ticks {hole_range_txt(w45n8_84426200)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84425500 and W45N8@84425800 (already told in the ~02:43 _patrol_2026-11-23_0216 USER_LOG and mentioned as already-told in later USER_LOGs; aged out, not retried this pass; listener {w45n8_84425500['distinct']}/100 and {w45n8_84425800['distinct']}/100) are not labeled NEW this wrap; do not re-tell. "
        + "NEW leftover official 404 this run: none. Still-untold leftover official 404 from the quiet 08:30 half-hour: W47N8@84431000 — still NOT YET TOLD; fold into the next 3h patrol. "
        + "NEW 盒子休眠 this run: 08:54:25-09:05:57 Asia/Hong_Kong — NOT YET TOLD; fold into the next 3h patrol. NEW 监听短中断 this run: none. "
        + f"NEW 盒子休眠 08:54:25-09:05:57 Asia/Hong_Kong (686s, box_pauses row; STATS 84431391..84431559, 169t; official-filled {fill0854}; W45N7 0/169 is official empty_no_creep (W45N7 empty ranges 84431349 and 84431351..84431599, no 404 — first-pass official GETs for W45N7@84431300/84431400/84431500 were 200); listener auto-restart 09:06:00, python 2978459 started 09:06:10, parent 4035476) is not yet told; fold into the next 3h patrol. "
        + "Already-told 盒子休眠 through 08:18:40-08:22:01 and 07:38:49-08:00:34 and 07:00:52-07:06:05 and 06:23:39-06:27:58 and 05:48:18-06:06:20 were already told in the ~08:33 0821 USER_LOG; do not re-tell. Already-told 盒子休眠 05:16:36-05:25:46 and 04:53:04-04:58:42 and 04:20:59-04:35:45 and 03:52:38-03:58:50 and 03:22:33-03:29:51 and 02:51:37-02:58:39 were already told in the ~05:38 0516 USER_LOG; do not re-tell. Already-told 盒子休眠 02:19:33-02:28:15 and 01:46:20-02:01:27 and 01:15:53-01:27:13 and 00:51:21-00:57:39 and 00:23:50-00:33:45 and 23:52:01-23:59:48 were already told in the ~02:43 patrol USER_LOG; do not re-tell. Already-told 盒子休眠 22:43:27-23:05:49 and 21:45:57-22:04:37 and 20:49:49-20:59:53 and 19:43:54-19:59:40 and 17:41:00-18:04:50 and older; already-told 监听短中断 through 19:12:43-19:12:57 and 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20; do not re-tell. "
        + f"window_db={window_db}" + NL
        + f"jp_post={post} jp_script_by={script_by} jp_actual_by={actual}" + NL
        + f"tips={tips}" + NL
        + f"listener {listener_lines} rot={rot} yield_absent={yield_absent}" + NL
        + "Single listener 2978459 since 09:06:10 after the NEW 盒子休眠 08:54:25-09:05:57 auto-restart 09:06:00 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "
        + f"listener_rot {rot} tips {tips}." + NL
    )

'''

VERIFY = r'''    verify = (
        f"wrap {now} ok_quiet=True" + NL
        + f"window={T0}..{T1} jp={JP_T0}..{JP_T1}" + NL
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} postjp={inserted_postjp} just_actual={actual_sum} total={inserted_total}" + NL
        + f"tick_s_in_use={tick_s_in_use} name={tick_s_label} corrective_applied={bool(tick.get('corrective_applied'))} nfix={corrective} first_pass_realign=first_4.25357_inside_45s_gate_no_corrective" + NL
        + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
        + f"window_db={window_db}" + NL
        + f"jp_post={post} jp_dup={dup} jp_script_by={script_by} jp_actual_by={actual}" + NL
        + f"holes W47N8@84431000={w47n8_84431000} W47N7@84430700={w47n7_84430700} W47N7@84430800={w47n7_84430800} W46N8@84430500={w46n8_84430500} W47N8@84429900={w47n8_84429900} W47N7@84429300={w47n7_84429300} W45N7@84428300={w45n7_84428300} W45N8@84426200={w45n8_84426200} W45N8@84425500={w45n8_84425500} W45N8@84425800={w45n8_84425800}" + NL
        + f"NEW 盒子休眠 this run: 08:54:25-09:05:57 Asia/Hong_Kong (686s, box_pauses row; STATS 84431391..84431559, 169t; official-filled {fill0854}; W45N7 0/169 is official empty_no_creep in 84431349 and 84431351..84431599, no 404; listener auto-restart 09:06:00, python 2978459 started 09:06:10, parent 4035476) — NOT YET TOLD; fold into the next 3h patrol. Already-told 盒子休眠 through 08:18:40-08:22:01 and 07:38:49-08:00:34 and 07:00:52-07:06:05 and 06:23:39-06:27:58 and 05:48:18-06:06:20 were already told in the ~08:33 0821 USER_LOG; do not re-tell. Already-told 盒子休眠 through 05:16:36-05:25:46 and older were already told in the ~05:38 0516 or earlier USER_LOG; do not re-tell. Still-untold leftover official 404 W47N8@84431000 (from quiet 0830 JP; confirm/retry2/late/postjp still 404; listener {w47n8_84431000['distinct']}/100; hole {w47n8_84431000['hole_ticks']} ticks {hole_range_txt(w47n8_84431000)}) — still NOT YET TOLD; fold into the next 3h patrol. NEW leftover official 404 this run: none. Already-told leftover official 404 W47N7@84430800, W47N7@84430700, W46N8@84430500, W47N8@84429900, W47N7@84429300 (already told in the ~08:33 0821 USER_LOG; aged out of window start {T0}, not retried this pass) are not labeled NEW; do not re-tell. Leftover official 404 W45N7@84428300 and W45N8@84426200 already told in the 0516 USER_LOG (and as already-told in 0821); do not re-tell. Leftover official 404 W45N8@84425500 and W45N8@84425800 already told in the 02:43 patrol USER_LOG; do not re-tell. NEW 监听短中断 none. already_told by _patrol_2026-11-23_0821 USER_LOG ~08:33 finished_at 08:34:04 (do not re-tell): 盒子休眠 08:18:40-08:22:01, 07:38:49-08:00:34, 07:00:52-07:06:05, 06:23:39-06:27:58, 05:48:18-06:06:20; leftover official 404 W47N7@84430800, W47N7@84430700, W46N8@84430500, W47N8@84429900, W47N7@84429300; and as already-told W45N7@84428300, W45N8@84426200. already_told by _patrol_2026-11-23_0516 USER_LOG ~05:38 finished_at 05:40:08 (do not re-tell): 盒子休眠 05:16:36-05:25:46, 04:53:04-04:58:42, 04:20:59-04:35:45, 03:52:38-03:58:50, 03:22:33-03:29:51, 02:51:37-02:58:39; leftover official 404 W45N8@84426200 and W45N7@84428300. already_told by _patrol_2026-11-23_0216 USER_LOG ~02:43 finished_at 02:43:39 (do not re-tell): 盒子休眠 02:19:33-02:28:15, 01:46:20-02:01:27, 01:15:53-01:27:13, 00:51:21-00:57:39, 00:23:50-00:33:45, 23:52:01-23:59:48; leftover official 404 W45N8@84425500 and W45N8@84425800. Older already-told freezes through 22:43:27-23:05:49 / 21:45:57-22:04:37 / 20:49:49-20:59:53 / 19:43:54-19:59:40 / 17:41:00-18:04:50 and leftover official 404s through W45N8@84422100 / W45N8@84422400 and earlier. already-told 监听短中断 through 19:12:43-19:12:57 and 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20." + NL
        + "ok_quiet=True new_official_404_untold=[] still_untold_from_0830=[W47N8@84431000] still_untold_from_0800=[] still_untold_from_0700=[] still_untold_from_0630=[] still_untold_from_0300=[] new_box_freeze_untold=[08:54:25-09:05:57] still_untold_freeze_from_0830=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0630=[] still_untold_freeze_from_0600=[] still_untold_freeze_from_0500=[] still_untold_freeze_from_0430=[] still_untold_freeze_from_0400=[] still_untold_freeze_from_0330=[] still_untold_freeze_from_0300=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0900 concurrent_patrol=already_delivered_patrol_2026-11-23_0821_finished_at_08:34:04_do_not_write_folder last=_patrol_2026-11-23_0821_finished_at_08:34:04_USER_LOG_~08:34 concurrent_12h_review=already_delivered_review12h_2026-11-23_08_~08:30_do_not_write_folder already_told_404s_this_patrol=[W47N7@84430800,W47N7@84430700,W46N8@84430500,W47N8@84429900,W47N7@84429300,W45N7@84428300,W45N8@84426200,W45N8@84425500,W45N8@84425800] already_told_freeze_this_patrol=[08:18:40-08:22:01,07:38:49-08:00:34,07:00:52-07:06:05,06:23:39-06:27:58,05:48:18-06:06:20,05:16:36-05:25:46,04:53:04-04:58:42,04:20:59-04:35:45,03:52:38-03:58:50,03:22:33-03:29:51,02:51:37-02:58:39,02:19:33-02:28:15,01:46:20-02:01:27,01:15:53-01:27:13,00:51:21-00:57:39,00:23:50-00:33:45,23:52:01-23:59:48]" + NL
    )

'''

SNAP = r'''    snap = {
        "at": now,
        "ok_quiet": True,
        "inserted_total": inserted_total,
        "inserted_first": inserted_first,
        "inserted_confirm": inserted_confirm,
        "inserted_confirm_script": inserted_confirm_script,
        "inserted_retry2": inserted_retry2,
        "inserted_retry2_script": inserted_retry2_script,
        "inserted_late": inserted_late,
        "inserted_postjp": inserted_postjp,
        "just_actual": actual_sum,
        "just_script": script_sum,
        "just_script_by": script_by,
        "just_actual_by": actual,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_in_use_name": tick_s_label,
        "window": [T0, T1],
        "window_db": window_db,
        "coverage": {"official_recovered": cov["official_recovered"], "expected": cov["expected"], "empty_no_creep": cov["empty_no_creep"], "official_404": cov["official_404_missing"]},
        "gaps": {k: {r: v[r]["fill"] for r in ROOMS} for k, v in gaps.items()},
        "holes": holes,
        "tips": tips,
        "listener": listener_lines,
        "rot": rot,
        "yield_absent": yield_absent,
        "new_official_404_untold": [],
        "still_untold_from_0830": ["W47N8@84431000"],
        "still_untold_from_0800": [],
        "still_untold_from_0700": [],
        "still_untold_from_0630": [],
        "still_untold_from_0300": [],
        "already_told_404s_this_patrol": ["W47N7@84430800", "W47N7@84430700", "W46N8@84430500", "W47N8@84429900", "W47N7@84429300", "W45N7@84428300", "W45N8@84426200", "W45N8@84425500", "W45N8@84425800"],
        "new_box_freeze_untold": ["08:54:25-09:05:57"],
        "still_untold_freeze_from_0830": [],
        "still_untold_freeze_from_0800": [],
        "still_untold_freeze_from_0700": [],
        "still_untold_freeze_from_0630": [],
        "still_untold_freeze_from_0600": [],
        "still_untold_freeze_from_0500": [],
        "already_told_freeze_this_patrol": ["08:18:40-08:22:01", "07:38:49-08:00:34", "07:00:52-07:06:05", "06:23:39-06:27:58", "05:48:18-06:06:20", "05:16:36-05:25:46", "04:53:04-04:58:42", "04:20:59-04:35:45", "03:52:38-03:58:50", "03:22:33-03:29:51", "02:51:37-02:58:39", "02:19:33-02:28:15", "01:46:20-02:01:27", "01:15:53-01:27:13", "00:51:21-00:57:39", "00:23:50-00:33:45", "23:52:01-23:59:48"],
        "new_short_ws_untold": [],
        "concurrent_patrol": "already_delivered_patrol_2026-11-23_0821_finished_at_08:34:04_do_not_write_folder; last=_patrol_2026-11-23_0821_finished_at_08:34:04_USER_LOG_~08:34",
        "concurrent_12h_review": "already_delivered_review12h_2026-11-23_08_~08:30_do_not_write_folder",
        "did_not_write_patrol_folder": True,
        "first_pass_realign": "first interval 4.25357 already inside 45s gate; live-anchor-best first 4.25357, corrective_applied=False nfix=0",
        "first_pass_source": "this_halfhour_0900",
    }

'''

def replace_block(src, start_marker, end_marker, replacement):
    start = src.index(start_marker)
    end = src.index(end_marker)
    if end <= start:
        raise SystemExit(f"bad span for {start_marker!r}")
    return src[:start] + replacement + src[end:]

src = replace_block(src, "    now_txt = (", '    (DIR / "_halfhour_backfill_now.txt").write_text(now_txt)', NOW)
src = replace_block(src, "    verify = (", '    (DIR / "verify.txt").write_text(verify)', VERIFY)
src = replace_block(src, "    snap = {", '    (DIR / "wrapup_snap.json").write_text(', SNAP)

# compile check
compile(src, str(p), "exec")
p.write_text(src)
print("patched wrapup_write.py ok, bytes", len(src))
print("fill0854 present", "fill0854 =" in src)
print("08:54 freeze present", "08:54:25-09:05:57" in src)
print("stale 0821 running gone", "running_patrol_2026-11-23_0821_not_delivered" not in src)
print("stale nfix=94 gone from verify label", 'nfix=94 first_pass_realign=CRASHED' not in src)
