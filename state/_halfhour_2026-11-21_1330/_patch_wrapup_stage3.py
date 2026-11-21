#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-21_1330/wrapup_write.py")
src = p.read_text()

def rep(old, new, label, expected=1):
    global src
    n = src.count(old)
    if n != expected:
        raise SystemExit(f"{label}: found {n} occurrences, expected {expected}\n---OLD---\n{old[:400]}")
    src = src.replace(old, new)
    print("ok", label, expected)

# window-start notes that should move to 84393701 (not historical first-pass numbers)
for old, new, label in [
    (
        'official-filled all five 129/129. Ages out of window start 84393201. Do not re-tell.",',
        'official-filled all five 129/129. Ages out of window start 84393701. Do not re-tell.",',
        "1149-note",
    ),
    (
        'official-filled all five 29/29. Still in official window start 84393201. Do not re-tell.",',
        'official-filled all five 29/29. Ages out of official window start 84393701. Do not re-tell.",',
        "1210-note",
    ),
    (
        '"Still in official window start 84393201. Do not re-tell."',
        '"Ages out of official window start 84393701. Do not re-tell."',
        "1218-note",
    ),
    (
        "Ages out of window start 84393201 and was not retried here. Listener 29/100; hole 71 ticks.",
        "Ages out of window start 84393701 and was not retried here. Listener 29/100; hole 71 ticks.",
        "926-note",
    ),
    (
        "Aged out of window start 84393201 and was not retried here.",
        "Aged out of window start 84393701 and was not retried here.",
        "aged-leftovers",
    ),
]:
    exp = src.count(old)
    if exp < 1:
        raise SystemExit(f"{label} not found:\n{old}")
    src = src.replace(old, new)
    print("ok", label, exp)

rep('    "already_told_box_freeze_in_window": None,  # 11:49 freeze ages out of window start 84393201',
    '    "already_told_box_freeze_in_window": None,  # 11:49 freeze ages out of window start 84393701',
    "comment-1149")

rep('    "game_time_first": 84393990,',
    '    "game_time_first": 84394426,',
    "gt_first")
rep('    "published_bases": "84393200..84393800",',
    '    "published_bases": "84393700..84394300",',
    "pub_bases")
rep('    "reconstructed": [84393201, 84393900],',
    '    "reconstructed": [84393701, 84394400],',
    "recon")
rep('    "creep_rows": 25437,',
    '    "creep_rows": 26630,',
    "creep_rows")
rep('    "missing_chunks": 0,',
    '    "missing_chunks": 1,',
    "missing_chunks")
rep('    "already_in_db": 19540,',
    '    "already_in_db": 26099,',
    "already")

old_first_pass_by = '''    "first_pass_by": (
        "this 13:00 half-hour routine ran tools/history_backfill.py --minutes 40 "
        "(game.time=84393990, published_bases 84393200..84393800, reconstructed 84393201..84393900 "
        "missing_chunks=0 inserted=5897 already_in_db=19540); 35/35 official GETs 200. "
        f"Confirm {confirm_at} skipped={confirm_skipped} no targets, inserted={inserted_confirm}. "
        f"retry2 {retry2_at} skipped={retry2_skipped} no targets, inserted={inserted_retry2}. "
        "Prior 12:30 half-hour official-filled 84392901..84393600 plus just-published 84393600 actual 3192; "
        "that run also recorded still-untold box freeze 12:30:42-12:35:35 (official-filled all five 79/79)."
    ),'''
new_first_pass_by = '''    "first_pass_by": (
        "this 13:30 half-hour routine ran tools/history_backfill.py --minutes 40 "
        "(game.time=84394426, published_bases 84393700..84394300, reconstructed 84393701..84394400 "
        "missing_chunks=1 W46N8@84394300 inserted=531 already_in_db=26099); 34/35 official GETs 200. "
        f"Confirm {confirm_at} skipped={confirm_skipped} still_404={confirm_still} inserted={inserted_confirm}. "
        f"retry2 {retry2_at} skipped={retry2_skipped} still_404={retry2_still} inserted={inserted_retry2}. "
        "Late retry 13:39:21 gt=84394550 still 404 W46N8@84394300 inserted=0. "
        "Prior 13:00 half-hour official-filled 84393201..84393900 plus just-published 84393900 actual 3109; "
        "that run also recorded still-untold box freeze 12:48:14-12:57:17 (official-filled all five 139/139) "
        "and carried still-untold 12:30:42-12:35:35 (official-filled all five 79/79)."
    ),'''
rep(old_first_pass_by, new_first_pass_by, "first_pass_by")

rep('    "tick_s_printed": 4.272,',
    '    "tick_s_printed": 4.236,',
    "tick_s_printed")

old_corr = '''    "corrective_note": (
        f"no corrective realign; live-anchor-best later_raw {tick_s_in_use:.5f} already inside 45s gate "
        "(over45=0 mean_off=10.4) at game.time=84394017; first-pass tick_s=4.27231 (printed 4.272) realigned 0 rows"
    ),'''
new_corr = '''    "corrective_note": (
        f"no corrective realign; live-anchor-best span_mean {tick_s_in_use:.5f} already inside 45s gate "
        "(over45=0 mean_off=-0.5) at game.time=84394465; first-pass tick_s=4.23635 (printed 4.236) realigned 0 rows"
    ),'''
rep(old_corr, new_corr, "corrective_note")

old_empty = '''    "empty_no_creep_note": (
        "W45N7 official empty-no-creep 178 ticks: 84393411 and 84393413..84393580 "
        "(evac after W45N7 Invader core from ~12:15 / tick 84393366; not a 404), "
        "plus 84393793..84393798 and 84393817..84393819 (official empty-no-creep, not a 404)."
    ),'''
new_empty = '''    "empty_no_creep_note": (
        "W45N7 official empty-no-creep 9 ticks: 84393793..84393798 and 84393817..84393819 "
        "(same official empty-no-creep pattern after the earlier W45N7 Invader-core evac; not a 404). "
        "The older evac empty range 84393411 / 84393413..84393580 now sits before official window start 84393701."
    ),'''
rep(old_empty, new_empty, "empty_note")

old_per = '''    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 1397},
        "W47N8": {"ticks": 700, "new": 1904},
        "W45N8": {"ticks": 700, "new": 1523},
        "W45N7": {"ticks": 700, "new": 324},
        "W47N7": {"ticks": 700, "new": 749},
    },'''
new_per = '''    "per_room_new_first": {
        "W46N8": {"ticks": 600, "new": 0},
        "W47N8": {"ticks": 700, "new": 300},
        "W45N8": {"ticks": 700, "new": 0},
        "W45N7": {"ticks": 700, "new": 0},
        "W47N7": {"ticks": 700, "new": 231},
    },'''
rep(old_per, new_per, "per_room")

rep('    "in_window_404_after_retry2": [],',
    '    "in_window_404_after_retry2": ["W46N8@84394300"],',
    "in_window_404")

rep('    "new_official_404": [],',
    '''    "new_official_404": [{
        "chunk": "W46N8@84394300",
        "hole": "84394380..84394400",
        "missing_n": 21,
        "listener": "84394301..84394379",
        "listener_n": 79,
        "distinct": hole943_d,
        "rows": hole943_n,
        "range": None if hole943_mn is None else f"{hole943_mn}..{hole943_mx}",
        "told": False,
        "told_by": None,
        "first_recorded_by": "13:30 half-hour backfill",
        "note": (
            "NEW leftover official 404 this run, not yet told. First pass 404 at game.time=84394426; "
            "confirm 13:33:07 gt=84394463, retry2 13:33:42 gt=84394471, and late retry 13:39:21 gt=84394550 still 404. "
            "Other four rooms at base 84394300 returned 200 on the first pass. "
            "Listener already has 79/100 ticks 84394301..84394379; hole 21 ticks 84394380..84394400. "
            "Next 1h patrol should tell this leftover together with the new 13:09 freeze."
        ),
    }],''',
    "new_official_404")

rep('    "prior_untold_box_freeze_in_window": prior_untold_freeze_1230,',
    '    "prior_untold_box_freeze_in_window": prior_untold_freeze_1248,\n    "prior_untold_box_freeze_aged_out": prior_untold_freeze_1230,',
    "prior_untold_keys")

rep(
    '        "reason": "first pass 35/35 official GETs 200, missing_chunks=0; no in-window official 404s to retry",',
    '        "reason": "first pass 34/35 official GETs 200, missing_chunks=1 W46N8@84394300; confirm still 404, inserted=0",',
    "confirm_reason")
# retry2 reason "no targets" - replace uniquely in retry2 block
old_r2 = '''    "retry2": {
        "at": retry2_at,
        "game_time": retry2_gt,
        "still_404": retry2_still,
        "inserted": inserted_retry2,
        "recovered": retry2_rec,
        "skipped": retry2_skipped,
        "reason": "no targets",
    },'''
new_r2 = '''    "retry2": {
        "at": retry2_at,
        "game_time": retry2_gt,
        "still_404": retry2_still,
        "inserted": inserted_retry2,
        "recovered": retry2_rec,
        "skipped": retry2_skipped,
        "reason": "W46N8@84394300 still 404 at 13:33:42 gt=84394471; late retry 13:39:21 gt=84394550 also 404",
    },'''
rep(old_r2, new_r2, "retry2_reason")

old_listener = '''    "listener": {
        "pid": 1876378,
        "started": "12:57:29",
        "parent": 4035476,
        "slot": slot,
        "rot": rot,
        "yield": "absent" if yield_absent else "present",
        "restarted_this_run": False,
        "last_auto_restart": "12:57:20 after box freeze 12:48:14-12:57:17; existing run_listener.sh parent 4035476 relaunched listener.py; this run did not restart the listener or war_cmd/pulse",
        "peacetime_single_slot": "W46N8:W47N8:W45N8:W45N7=5:5:1:1",
    },'''
new_listener = '''    "listener": {
        "pid": 1883231,
        "started": "13:21:26",
        "parent": 4035476,
        "slot": slot,
        "rot": rot,
        "yield": "absent" if yield_absent else "present",
        "restarted_this_run": False,
        "last_auto_restart": "13:21:17 after box freeze 13:09:46-13:21:14; existing run_listener.sh parent 4035476 relaunched listener.py; this run did not restart the listener or war_cmd/pulse",
        "peacetime_single_slot": "W46N8:W47N8:W45N8:W45N7=5:5:1:1",
    },'''
rep(old_listener, new_listener, "listener")

old_prior_hh = '''    "prior_halfhour": (
        "_halfhour_2026-11-21_1330 finished ~12:44; official through 84393600 + just-published 84393600 actual 3192; "
        "recorded still-untold box freeze 12:30:42-12:35:35 (official-filled all five 79/79); "
        "leftover official 404 W45N8@84392600 already told by the 12:26 1h patrol and aged out"
    ),'''
new_prior_hh = '''    "prior_halfhour": (
        "_halfhour_2026-11-21_1300 finished ~13:07; official through 84393900 + just-published 84393900 actual 3109; "
        "recorded still-untold box freeze 12:48:14-12:57:17 (official-filled all five 139/139) and carried still-untold 12:30:42-12:35:35 (official-filled all five 79/79); "
        "leftover official 404 W45N8@84392600 already told by the 12:26 1h patrol and aged out"
    ),'''
rep(old_prior_hh, new_prior_hh, "prior_halfhour")

old_prior_1h = '''        "Do not re-tell those. Fold the still-untold 12:30:42-12:35:35 freeze and the newer 12:48:14-12:57:17 freeze."'''
new_prior_1h = '''        "Do not re-tell those. Fold the new 13:09:46-13:21:14 freeze, the still-untold 12:48:14-12:57:17 and 12:30:42-12:35:35 freezes, and the new leftover official 404 W46N8@84394300."'''
rep(old_prior_1h, new_prior_1h, "prior_1h_fold")

rep('shutil.copy2(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1300.txt")',
    'shutil.copy2(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1330.txt")',
    "retry2_copy")

p.write_text(src)
print("wrote stage3", p.stat().st_size)
