#!/usr/bin/env python3
import json, shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1830")
STATE = Path("/workspace/screeps/state")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
jp = json.loads((DIR / "just_published_84398600.json").read_text())
conf = json.loads((DIR / "backfill_confirm_gets.json").read_text())
rot = json.loads(Path("/workspace/screeps/metrics/listener_rot.json").read_text())
live = json.loads(Path("/workspace/screeps/metrics/live.json").read_text())

window_db = post["first_pass_window"]
tips = post["tips"]
actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
inserted_first = 2022
inserted_total = inserted_first + actual_sum  # confirm=0 retry2=0 late=0

tick_s_in_use = float(tick["tick_s_in_use"])
tick_s_first = float(tick["tick_s_used_first_pass"])
tick_s_name = tick.get("tick_s_in_use_name") or "first"

payload = {
    "ok_quiet": True,
    "at": AT,
    "window": [84397901, 84398600],
    "published_bases": [84397900, 84398500],
    "game_time_first": 84398668,
    "first_pass": {
        "gets_200": 35,
        "gets_total": 35,
        "missing_chunks": [],
        "reconstructed": [84397901, 84398600],
        "creep_rows": 23722,
        "already_in_db": 21700,
        "inserted": inserted_first,
        "ts_realigned": 0,
        "tick_s_printed": 4.311,
        "overlap_compared": 21369,
        "overlap_match": 20662,
        "overlap_differ": 707,
        "overlap_differ_samples": [
            {"key": ["rhauler84397559", 84398469, "W46N8"], "db": [49, 21, 1600, 170], "hist": [49, 21, 1600, 0], "note": "store-only"},
            {"key": ["w8builder84397308", 84398501, "W47N8"], "db": [26, 35, 1800, 209], "hist": [25, 35, 1800, 209], "note": "opening-tick hist matches listener 84398500"},
            {"key": ["w8upgrader84397472", 84398501, "W47N8"], "db": [12, 25, 1300, 20], "hist": [12, 25, 1300, 30], "note": "opening-tick hist matches listener 84398500"},
            {"key": ["w8hauler84397786", 84398501, "W47N8"], "db": [13, 27, 1500, 180], "hist": [12, 28, 1500, 180], "note": "opening-tick hist matches listener 84398500"},
            {"key": ["w8miner84398206", 84398501, "W47N8"], "db": [26, 11, 800, 48], "hist": [26, 11, 800, 36], "note": "opening-tick hist matches listener 84398500"},
            {"key": ["w8upgrader84398262", 84398501, "W47N8"], "db": [14, 27, 1300, 30], "hist": [14, 27, 1300, 40], "note": "opening-tick hist matches listener 84398500"},
            {"key": ["w8rhauler84397654", 84398501, "W47N8"], "db": [14, 30, 2400, 592], "hist": [15, 31, 2400, 592], "note": "opening-tick hist matches listener 84398500"},
            {"key": ["w8rhauler84397144", 84398501, "W47N8"], "db": [12, 28, 2400, 266], "hist": [13, 29, 2400, 266], "note": "opening-tick hist matches listener 84398500"},
        ],
        "overlap_note": "Backfill does not overwrite existing rows. 707 diffs vs live/earlier official rows; samples show W47N8@84398501 opening tick one behind live (null-open keep-previous-state) and one W46N8 store-only mismatch.",
    },
    "confirm": {
        "at": "2026-11-21 18:36:47 Asia/Hong_Kong",
        "skipped": True,
        "game_time": None,
        "still_404": [],
        "inserted": 0,
        "recovered": [],
        "reason": "no targets",
    },
    "retry2": {
        "at": "2026-11-21 18:36:47 Asia/Hong_Kong",
        "skipped": True,
        "game_time": None,
        "still_404": [],
        "inserted": 0,
        "recovered": [],
        "reason": "no targets",
    },
    "late_retry": None,
    "just_published": {
        "base": 84398600,
        "at": "2026-11-21 18:38:26 Asia/Hong_Kong",
        "game_time": 84398742,
        "all_five_200": True,
        "script_sum": script_sum,
        "actual_sum": actual_sum,
        "script_by_room": script_by,
        "actual_by_room": actual_by,
        "still_404": [],
        "w45n7_note": "just-published W45N7 52/100 distinct min=84398649..84398700 after Invader Core evac; official 200, not a 404",
    },
    "coverage": {
        "official_recovered": cov["official_recovered"],
        "expected": cov["expected"],
        "empty_no_creep": cov["empty_no_creep"],
        "official_404_missing": cov["official_404_missing"],
        "w45n7_empty": "84398461..84398600 (140t) evac after Invader Core 84398417; official 200, not a 404",
    },
    "inserted_total": inserted_total,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_name,
    "tick_s_first": tick_s_first,
    "ts_realigned_first": 0,
    "corrective": False,
    "tips": tips,
    "window_db": window_db,
    "listener": {
        "pid": 2000028,
        "started": "17:58:45",
        "parent": 4035476,
        "slot": live.get("roomSlot") or rot.get("room"),
        "rot": rot,
        "yield_absent": True,
        "restarted_this_run": False,
        "auto_restarted_before_first_pass": {
            "listener_out": "2026-11-21 17:58:36 restart",
            "python_started": "17:58:45",
            "reason": "box freeze 17:51:07-17:58:33 ended; run_listener.sh relaunched listener.py; already told by the 18:27 1h patrol",
        },
    },
    "already_told_by_1827_patrol": {
        "box_freezes_in_window": ["17:51:07-17:58:33"],
        "short_ws_in_window": [],
        "official_404s_in_window": [],
        "box_freezes_aged_out": [
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
    "new_untold_official_404s": [],
    "new_untold_short_ws": [],
    "concurrent_patrol": None,
    "did_not_write_patrol_folder": True,
}
NL = chr(10)

wrap = (
    f"---- wrap {AT} ----" + NL
    + "confirm at 2026-11-21 18:36:47 Asia/Hong_Kong skipped no targets inserted=0; "
    + "retry2 at 2026-11-21 18:36:47 Asia/Hong_Kong skipped no targets inserted=0. "
    + "First pass 35/35 official GETs 200, missing_chunks=0. "
    + "Already-told leftover official 404s W45N7@84397400 / W47N7@84395600 / W47N8@84395100 / W46N8@84394300 / W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600 aged out of window start 84397901 and were not retried. "
    + "W45N7 evac empty after Invader Core 84398417: official window 84398461..84398600 is 0/140 creeps (chunk 84398401..84398500 is 60/100, max 84398460); not a 404. "
    + f"Just-published 84398600 at 2026-11-21 18:38:26 Asia/Hong_Kong gt=84398742 all_five_200=True script={script_sum} actual={actual_sum}; "
    + f"W46N8 script {script_by['W46N8']} vs actual {actual_by['W46N8']}, "
    + f"W47N8 script {script_by['W47N8']} vs actual {actual_by['W47N8']}, "
    + f"W45N8 script {script_by['W45N8']} vs actual {actual_by['W45N8']}, "
    + f"W45N7 script {script_by['W45N7']} vs actual {actual_by['W45N7']}, "
    + f"W47N7 script {script_by['W47N7']} vs actual {actual_by['W47N7']}. "
    + "Just-published W45N7 52/100 distinct 84398649..84398700 is evac empty start, official 200 not a 404. "
    + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
    + "inserted_first=2022 confirm=0 retry2=0 late=0 "
    + f"just_actual={actual_sum} total={inserted_total}. "
    + f"tick_s_printed=4.311 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_name}) "
    + "ts_realigned_first=0 corrective=0. "
    + "First-pass overlap compared=21369 match=20662 differ=707 (not overwritten; W47N8@84398501 opening tick hist matches listener 84398500; W46N8 rhauler84397559@84398469 store-only db 170 vs hist 0). "
    + f"Listener pid=2000028 started=17:58:45 parent=4035476 slot={live.get('roomSlot') or rot.get('room')} "
    + f"rot={json.dumps(rot, separators=(', ', ': '))} yield=absent restarted_this_run=false "
    + "(listener auto-restarted 17:58:36 after the 17:51:07-17:58:33 box freeze, python 2000028 started 17:58:45, before this run's first pass; already told by the 18:27 1h patrol; this run did not restart it). "
    + "Peacetime single-slot 5:5:1:1. This run did not restart the listener or war_cmd/pulse. "
    + "No concurrent 1h patrol; this run did not write a patrol folder."
    + NL
    + "NEW not-yet-told for the next 1h patrol: none (no new box freeze, short WS, or leftover official 404 this window). "
    + "Already told by the delivered 18:27 亚洲/香港 1h patrol and still in official window start 84397901: "
    + "box freeze 17:51:07-17:58:33 (442s, already healed; STATS 84398081..84398189, 109t; official-filled all five 109/109; listener auto-restart 17:58:36, python 2000028 started 17:58:45). "
    + "Already told by the 18:27/17:33/16:32 patrols and now age out of window start 84397901: "
    + "short WS ping/pong 17:23:22 (not a box freeze; STATS 84397671..84397699, 29t; official-filled all five 29/29; listener restart 17:23:22), "
    + "box freeze 16:48:46-17:04:41 (954s; STATS 84397201..84397439, 239t; official-filled four rooms 239/239, W45N7 200/239 missing tail 84397401..84397439 because of leftover official 404 W45N7@84397400; listener auto-restart 17:04:44), "
    + "leftover official 404 W45N7@84397400 (listener 0/100, hole 100 ticks 84397401..84397500; last retried 17:42:27 gt=84397961 still 404, not retried this run), "
    + "box freeze 16:16:43-16:19:24 (161s; STATS 84396751..84396799, 49t; official-filled all five 49/49; listener auto-restart 16:19:27), "
    + "short WS ping/pong 16:22:02 (not a box freeze; STATS 84396821..84396839, 19t; official-filled all five 19/19; listener restart 16:22:05), "
    + "box freeze 15:47:29-15:58:30 (655s; STATS 84396331..84396509, 179t; official-filled four rooms 179/179, W45N7 173/179 evac empty tail 84396331..84396336 official 200 not a 404), "
    + "box freeze 15:14:38-15:19:30 (292s; STATS 84395871..84395959, 89t; official-filled W46N8/W47N8/W45N8/W47N7 89/89, W45N7 59/89 evac empty tail 84395930..84395959 official 200 not a 404), "
    + "leftover official 404 W47N7@84395600 (listener 0/100, hole 100 ticks 84395601..84395700; not retried this run), "
    + "leftover official 404 W47N8@84395100 (listener 0/100, hole 100 ticks 84395101..84395200), "
    + "leftover official 404 W46N8@84394300 (listener 79/100 84394301..84394379, hole 21 ticks 84394380..84394400), "
    + "box freeze 14:40:53-14:56:54 (952s; STATS 84395401..84395639, 239t; official-filled four rooms 239/239, W47N7 200/239 missing 84395601..84395639 because of leftover official 404 W47N7@84395600), "
    + "box freeze 14:15:50-14:23:29 (450s; STATS 84395061..84395179, 119t; official-filled four rooms 119/119, W47N8 40/119 missing 84395101..84395179 because of leftover official 404 W47N8@84395100), "
    + "box freeze 13:49:01-13:56:56 (475s; STATS 84394681..84394809, 129t; official-filled all five 129/129), box freeze 13:09:46-13:21:14, earlier already-told freezes 12:48:14-12:57:17 / 12:30:42-12:35:35 / 11:49:12-11:57:31 / 11:19:06-11:20:43, short WS gaps 12:10 / 12:18 / 11:12, and older leftover official 404s W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600. "
    + "Fold only newer freezes, short WS gaps, or leftover official 404s than the already-told 18:27 set (which includes 17:51:07-17:58:33); do not re-tell 17:51:07-17:58:33, 17:23:22 short WS, 16:48:46-17:04:41, W45N7@84397400, 16:16:43-16:19:24, the 16:22:02 short WS, 15:47:29-15:58:30, W47N7@84395600, or earlier already-told items."
    + NL
)

verify = (
    f"wrap {AT}" + NL
    + "window 84397901..84398600 first_pass 35/35 missing_chunks=0" + NL
    + f"db_window {json.dumps(window_db, separators=(', ', ': '))}" + NL
    + "W45N7 evac empty 84398461..84398600 official 200 not a 404 (distinct=560/700, max=84398460)" + NL
    + "W45N7@84397400 already-told leftover aged out distinct=0 rows=0 range=None..None (listener 0/100, not retried this run)" + NL
    + "W47N7@84395600 aged-out hole distinct=0 rows=0 range=None..None (listener 0/100, not retried this run)" + NL
    + "W47N8@84395100 aged-out hole distinct=0 rows=0 range=None..None (listener 0/100, not retried this run)" + NL
    + "W46N8@84394300 aged-out hole distinct=79 rows=893 range=84394301..84394379 (listener 79/100, not retried this run)" + NL
    + f"just_published 84398600 all_five_200=True script={script_sum} actual={actual_sum} "
    + f"by_actual={json.dumps(actual_by, separators=(', ', ': '))} "
    + f"by_script={json.dumps(script_by, separators=(', ', ': '))} still_404=[] "
    + "W45N7 just-pub 52/100 84398649..84398700 evac empty start official 200" + NL
    + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
    + f"inserted_first=2022 confirm=0 retry2=0 late=0 just_actual={actual_sum} total={inserted_total}" + NL
    + f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first=0 corrective=0" + NL
    + "already_told_in_window box_freeze 17:51:07-17:58:33 all_five=109/109; short_ws 17:23:22 aged out all_five=29/29" + NL
    + "overlap_differ=707 not overwritten" + NL
    + f"tips {tips}" + NL
    + f"listener pid=2000028 started=17:58:45 parent=4035476 slot={live.get('roomSlot') or rot.get('room')} "
    + f"rot={json.dumps(rot, separators=(', ', ': '))} yield_absent=True restarted_this_run=False" + NL
    + "ok_quiet=True new_official_404_untold=[] new_box_freeze_untold=[] new_short_ws_untold=[]" + NL
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
    "new_untold_official_404s": [],
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
