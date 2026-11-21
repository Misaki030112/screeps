#!/usr/bin/env python3
import json, shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1930")
STATE = Path("/workspace/screeps/state")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
jp = json.loads((DIR / "just_published_84399500.json").read_text())
conf = json.loads((DIR / "backfill_confirm_gets.json").read_text())
late = json.loads((DIR / "backfill_late_retry.json").read_text())
rot = json.loads(Path("/workspace/screeps/metrics/listener_rot.json").read_text())
live = json.loads(Path("/workspace/screeps/metrics/live.json").read_text())

window_db = post["first_pass_window"]
tips = post["tips"]
actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
inserted_first = 3389
inserted_confirm = 0
inserted_retry2 = 0
inserted_late = 0
inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + actual_sum

tick_s_in_use = float(tick["tick_s_in_use"])
tick_s_first = float(tick["tick_s_used_first_pass"])
tick_s_name = tick.get("tick_s_in_use_name") or "prev_later"

new_404 = {
    "room": "W45N8",
    "base": 84399500,
    "ticks": [84399501, 84399600],
    "listener": {"distinct": 28, "rows": 113, "min": 84399548, "max": 84399575},
    "hole_ticks": 72,
    "hole_ranges": [[84399501, 84399547], [84399576, 84399600]],
    "first_seen": "just-published 2026-11-21 19:43:00 Asia/Hong_Kong gt=84399641 still 404",
    "confirm": None,
    "retry2": None,
    "late_retry": {
        "at": late["at"],
        "game_time": late["game_time"],
        "still_404": True,
        "inserted": 0,
    },
    "not_yet_told": True,
}

payload = {
    "ok_quiet": True,
    "at": AT,
    "window": [84398801, 84399500],
    "published_bases": [84398800, 84399400],
    "game_time_first": 84399534,
    "first_pass": {
        "gets_200": 29,
        "gets_total": 35,
        "missing_chunks": [
            "W46N8@84399100", "W47N8@84399100", "W45N8@84399100",
            "W45N7@84399100", "W47N7@84399100", "W45N8@84399300",
        ],
        "reconstructed": [84398801, 84399500],
        "creep_rows": 23086,
        "already_in_db": 19697,
        "inserted": inserted_first,
        "ts_realigned": 4275,
        "tick_s_printed": 4.261,
        "overlap_compared": 17889,
        "overlap_match": 17889,
        "overlap_differ": 0,
        "overlap_note": "Backfill does not overwrite existing rows. First-pass overlap 17889/17889 match.",
    },
    "confirm": {
        "at": "2026-11-21 19:36:23 Asia/Hong_Kong",
        "skipped": False,
        "game_time": 84399548,
        "still_404": [
            "W46N8@84399100", "W47N8@84399100", "W45N8@84399100",
            "W45N7@84399100", "W47N7@84399100", "W45N8@84399300",
        ],
        "inserted": 0,
        "recovered": [],
    },
    "retry2": {
        "at": "2026-11-21 19:37:45 Asia/Hong_Kong",
        "skipped": False,
        "game_time": 84399568,
        "still_404": [
            "W46N8@84399100", "W47N8@84399100", "W45N8@84399100",
            "W45N7@84399100", "W47N7@84399100", "W45N8@84399300",
        ],
        "inserted": 0,
        "recovered": [],
    },
    "late_retry": {
        "at": late["at"],
        "game_time": late["game_time"],
        "target": "W45N8@84399500",
        "still_404": True,
        "inserted": 0,
    },
    "just_published": {
        "base": 84399500,
        "at": "2026-11-21 19:43:00 Asia/Hong_Kong",
        "game_time": 84399641,
        "all_five_200": False,
        "script_sum": script_sum,
        "actual_sum": actual_sum,
        "script_by_room": script_by,
        "actual_by_room": actual_by,
        "still_404": ["W45N8@84399500"],
        "w47n7_note": "W47N7 script 366 vs actual 365 (1-row difference; typical).",
        "w45n8_note": "NEW leftover official 404 W45N8@84399500; late retry 19:45:06 gt=84399671 still 404; listener 28/100 84399548..84399575; hole 72 ticks 84399501..84399547 and 84399576..84399600.",
    },
    "coverage": {
        "official_recovered": cov["official_recovered"],
        "expected": cov["expected"],
        "empty_no_creep": cov["empty_no_creep"],
        "official_404_missing": cov["official_404_missing"],
        "w45n7_empty": "official 200 empty 84398866..84399000 (135t, evac after Invader Core 84398417) plus 84399201..84399248 (48t) and 84399287..84399300 (14t) in official-200 chunk 84399200; 197t total, not 404s.",
    },
    "inserted_total": inserted_total,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_name,
    "tick_s_first": tick_s_first,
    "ts_realigned_first": 4275,
    "corrective": False,
    "tips": tips,
    "window_db": window_db,
    "listener": {
        "pid": 2035841,
        "started": "19:18:58",
        "parent": 4035476,
        "slot": live.get("roomSlot") or rot.get("room"),
        "rot": rot,
        "yield_absent": True,
        "restarted_this_run": False,
        "auto_restarted_before_first_pass": {
            "listener_out": "2026-11-21 19:18:48 restart",
            "python_started": "19:18:58",
            "python_pid": 2035841,
            "reason": "box freeze 19:10:45-19:18:45 ended; run_listener.sh relaunched listener.py; already told by the delivered 19:18/19:28 1h patrol",
        },
    },
    "already_told_by_1918_patrol": {
        "box_freezes_in_window": ["18:47:50-18:58:17", "19:10:45-19:18:45"],
        "short_ws_in_window": [],
        "official_404s_in_window": [
            "W46N8@84399100", "W47N8@84399100", "W45N8@84399100",
            "W45N7@84399100", "W47N7@84399100", "W45N8@84399300",
        ],
        "box_freezes_aged_out": [
            "17:51:07-17:58:33",
            "16:48:46-17:04:41",
            "16:16:43-16:19:24",
            "15:47:29-15:58:30",
            "15:14:38-15:19:30",
            "14:40:53-14:56:54",
            "14:15:50-14:23:29",
            "13:49:01-13:56:56",
            "13:09:46-13:21:14",
        ],
        "short_ws_aged_out": ["17:23:22", "16:22:02"],
        "official_404s_aged_out": [
            "W45N7@84397400",
            "W47N7@84395600",
            "W47N8@84395100",
            "W46N8@84394300",
            "W45N8@84392600",
        ],
    },
    "new_untold_box_freezes": [],
    "new_untold_official_404s": [new_404],
    "new_untold_short_ws": [],
    "concurrent_patrol": "finished _patrol_2026-11-21_1918 at 19:29:30 CST before this run; did not write that folder",
    "did_not_write_patrol_folder": True,
}
NL = chr(10)

slot = live.get("roomSlot") or rot.get("room")
rot_s = json.dumps(rot, separators=(", ", ": "))

wrap = (
    f"---- wrap {AT} ----" + NL
    + "confirm at 2026-11-21 19:36:23 Asia/Hong_Kong gt=84399548 still_404 all five @84399100 and W45N8@84399300 inserted=0; "
    + "retry2 at 2026-11-21 19:37:45 Asia/Hong_Kong gt=84399568 still_404 same six inserted=0. "
    + "First pass 29/35 official GETs 200, missing_chunks=6 (all five @84399100 and W45N8@84399300, already told by the delivered 19:18/19:28 1h patrol). "
    + "Already-told leftover official 404s W45N7@84397400 / W47N7@84395600 / W47N8@84395100 / W46N8@84394300 / W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600 aged out of window start 84398801 and were not retried. "
    + "W45N7 official-200 empty in this window: 84398866..84399000 (135t evac after Invader Core 84398417) plus 84399201..84399248 (48t) and 84399287..84399300 (14t) in official-200 chunk 84399200, 197t total, not 404s. "
    + f"Just-published 84399500 at 2026-11-21 19:43:00 Asia/Hong_Kong gt=84399641 all_five_200=False script={script_sum} actual={actual_sum}; "
    + f"W46N8 script {script_by['W46N8']} vs actual {actual_by['W46N8']}, "
    + f"W47N8 script {script_by['W47N8']} vs actual {actual_by['W47N8']}, "
    + f"W45N8 script {script_by['W45N8']} vs actual {actual_by['W45N8']}, "
    + f"W45N7 script {script_by['W45N7']} vs actual {actual_by['W45N7']}, "
    + f"W47N7 script {script_by['W47N7']} vs actual {actual_by['W47N7']}. "
    + "W46N8/W47N8/W45N7/W47N7 just-pub 100/100 official 200; W45N8 still 404. "
    + "Late retry W45N8@84399500 at 2026-11-21 19:45:06 Asia/Hong_Kong gt=84399671 still 404 inserted=0. "
    + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
    + "inserted_first=3389 confirm=0 retry2=0 late=0 "
    + f"just_actual={actual_sum} total={inserted_total}. "
    + f"tick_s_printed=4.261 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_name}) "
    + "ts_realigned_first=4275 corrective=0. "
    + "First-pass overlap compared=17889 match=17889 differ=0 (not overwritten). "
    + f"Listener pid=2035841 started=19:18:58 parent=4035476 slot={slot} "
    + f"rot={rot_s} yield=absent restarted_this_run=False (auto-restart 19:18:48 after already-told freeze 19:10:45-19:18:45). "
    + "NEW not-yet-told leftover official 404 W45N8@84399500 (just-published 19:43:00 gt=84399641 and late retry 19:45:06 gt=84399671 still 404; listener 28/100 84399548..84399575; hole 72 ticks 84399501..84399547 and 84399576..84399600). "
    + "No new box freeze or short WS this run. Already told by the delivered 19:18/19:28 1h patrol and still in official window start 84398801: "
    + "box freeze 19:10:45-19:18:45 (476s; STATS 84399191..84399309, 119t; official-filled W46N8 115/119, W47N8 109/119, W45N8 100/119, W45N7 47/119, W47N7 109/119; missing head leftover official 404 84399100; listener auto-restart 19:18:48, python 2035841 started 19:18:58), "
    + "box freeze 18:47:50-18:58:17 (626s; STATS 84398871..84399029, 159t; official-filled W46N8/W47N8/W45N8/W47N7 159/159, W45N7 29/159 evac empty 84398871..84399000 official 200 not a 404), "
    + "leftover official 404 all five @84399100 (confirm 19:36:23 and retry2 19:37:45 still 404; listener partial W46N8 36/100 84399161..84399196, W47N8 5/100 84399101..84399105, W45N8 28/100 84399106..84399133, W45N7 27/100 84399134..84399160, W47N7 0/100), "
    + "leftover official 404 W45N8@84399300 (confirm+retry2 still 404; listener 0/100; hole 100 ticks 84399301..84399400). "
    + "Already-told and now aged out of window start 84398801: box freeze 17:51:07-17:58:33, short WS 17:23:22, leftover official 404 W45N7@84397400, and earlier already-told freezes/404s. "
    + "Fold only newer freezes, short WS gaps, or leftover official 404s than the already-told 19:18/19:28 set plus this NEW W45N8@84399500 once it is told; do not re-tell 19:10:45-19:18:45, 18:47:50-18:58:17, all-five @84399100, W45N8@84399300, 17:51:07-17:58:33, or earlier already-told items."
    + NL
)

verify = (
    f"wrap {AT}" + NL
    + "window 84398801..84399500 first_pass 29/35 missing_chunks=6 all five @84399100 and W45N8@84399300" + NL
    + f"db_window {json.dumps(window_db, separators=(', ', ': '))}" + NL
    + "W45N7 official-200 empty 84398866..84399000 (135t evac) plus 84399201..84399248 (48t) and 84399287..84399300 (14t), 197t total, not a 404" + NL
    + "already-told leftover all five @84399100 still 404 after confirm+retry2; listener partial as above" + NL
    + "already-told leftover W45N8@84399300 still 404 after confirm+retry2 distinct=0 rows=0 range=None..None (listener 0/100, hole 100 ticks 84399301..84399400)" + NL
    + "W45N7@84397400 already-told leftover aged out distinct=0 rows=0 range=None..None (listener 0/100, not retried this run)" + NL
    + "W47N7@84395600 aged-out hole distinct=0 rows=0 range=None..None (listener 0/100, not retried this run)" + NL
    + "W47N8@84395100 aged-out hole distinct=0 rows=0 range=None..None (listener 0/100, not retried this run)" + NL
    + "W46N8@84394300 aged-out hole distinct=79 rows=893 range=84394301..84394379 (listener 79/100, not retried this run)" + NL
    + f"just_published 84399500 all_five_200=False script={script_sum} actual={actual_sum} "
    + f"by_actual={json.dumps(actual_by, separators=(', ', ': '))} "
    + f"by_script={json.dumps(script_by, separators=(', ', ': '))} still_404=['W45N8@84399500'] "
    + "W46N8/W47N8/W45N7/W47N7 just-pub 100/100 official 200; W47N7 script 366 vs actual 365" + NL
    + "late_retry W45N8@84399500 19:45:06 Asia/Hong_Kong gt=84399671 still 404 inserted=0 listener 28/100 84399548..84399575 hole 72" + NL
    + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
    + f"inserted_first=3389 confirm=0 retry2=0 late=0 just_actual={actual_sum} total={inserted_total}" + NL
    + f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first=4275 corrective=0" + NL
    + "NEW_untold leftover official 404 W45N8@84399500 just-pub+late-retry still 404 listener 28/100 hole 72" + NL
    + "already_told_in_window box_freeze 19:10:45-19:18:45; box_freeze 18:47:50-18:58:17; leftover all-five @84399100; leftover W45N8@84399300" + NL
    + "already_told_aged_out box_freeze 17:51:07-17:58:33 all_five=109/109; short_ws 17:23:22 all_five=29/29" + NL
    + "overlap_differ=0 not overwritten" + NL
    + f"tips {tips}" + NL
    + f"listener pid=2035841 started=19:18:58 parent=4035476 slot={slot} "
    + f"rot={rot_s} yield_absent=True restarted_this_run=False" + NL
    + "ok_quiet=True new_official_404_untold=['W45N8@84399500'] new_box_freeze_untold=[] new_short_ws_untold=[]" + NL
    + "NEW not-yet-told" + wrap.split("NEW not-yet-told", 1)[1]
)

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2) + NL)
first = (DIR / "history_backfill_first_attempt.txt").read_text()
if not first.endswith(NL):
    first += NL
now_txt = first + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_verify.txt").write_text(verify)
(DIR / "verify.txt").write_text(verify)
(DIR / "wrapup_run.txt").write_text(f"wrap {AT} ok_quiet=True inserted_total={inserted_total}" + NL)
(DIR / "wrapup_snap.json").write_text(json.dumps({
    "at": AT,
    "ok_quiet": True,
    "inserted_total": inserted_total,
    "just_actual": actual_sum,
    "coverage": payload["coverage"],
    "new_untold_box_freezes": payload["new_untold_box_freezes"],
    "new_untold_official_404s": payload["new_untold_official_404s"],
    "new_untold_short_ws": [],
    "tips": tips,
    "listener": payload["listener"],
}, indent=2) + NL)

shutil.copy2(DIR / "history_backfill.json", STATE / "history_backfill.json")
shutil.copy2(DIR / "history_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")
print("wrote wrapup files")
print("ok_quiet", payload["ok_quiet"], "inserted_total", payload["inserted_total"], "at", AT)
print("now_txt bytes", len(now_txt), "verify bytes", len(verify))
print("new_untold_freeze", payload["new_untold_box_freezes"])
print("new_untold_404", payload["new_untold_official_404s"])
