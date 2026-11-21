#!/usr/bin/env python3
import json, shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1730")
STATE = Path("/workspace/screeps/state")
HK = ZoneInfo("Asia/Hong_Kong")
AT = "2026-11-21 17:43:55 Asia/Hong_Kong"

window_db = {
    "W46N8": {"distinct": 700, "rows": 7024, "min": 84397101, "max": 84397800},
    "W47N8": {"distinct": 700, "rows": 11046, "min": 84397101, "max": 84397800},
    "W45N8": {"distinct": 700, "rows": 3004, "min": 84397101, "max": 84397800},
    "W45N7": {"distinct": 600, "rows": 1940, "min": 84397101, "max": 84397800},
    "W47N7": {"distinct": 700, "rows": 3431, "min": 84397101, "max": 84397800},
}
rot = {"i": 0, "room": "W46N8", "left": 235.0, "at": "2026-11-21 17:43:53"}
tips = {"room_stats": 84397980, "creep_cpu": 84397960, "path_arrivals": 84397959}

payload = {
    "ok_quiet": True,
    "at": AT,
    "window": [84397101, 84397800],
    "published_bases": [84397100, 84397700],
    "game_time_first": 84397873,
    "first_pass": {
        "gets_200": 34,
        "gets_total": 35,
        "missing_chunks": ["W45N7@84397400"],
        "reconstructed": [84397101, 84397800],
        "creep_rows": 25644,
        "already_in_db": 25644,
        "inserted": 0,
        "ts_realigned": 0,
        "tick_s_printed": 4.189,
        "overlap_compared": 25164,
        "overlap_match": 25145,
        "overlap_differ": 19,
        "overlap_differ_samples": [
            "W45N8 rhauler84396824@84397501 position db=14,37 hist=13,36",
            "W45N8 rhauler84396824 at chunk 84397501..84397508 position off-by-one/stuck hist",
        ],
    },
    "confirm": {
        "at": "2026-11-21 17:38:47 Asia/Hong_Kong",
        "skipped": False,
        "game_time": 84397910,
        "still_404": ["W45N7@84397400"],
        "inserted": 0,
        "recovered": [],
    },
    "retry2": {
        "at": "2026-11-21 17:39:47 Asia/Hong_Kong",
        "skipped": False,
        "game_time": 84397924,
        "still_404": ["W45N7@84397400"],
        "inserted": 0,
        "recovered": [],
    },
    "late_retry": {
        "target": "W45N7@84397400",
        "attempts": [
            {"at": "17:42:27", "game_time": 84397961, "status": 404, "inserted": 0}
        ],
        "still_404": True,
        "inserted": 0,
    },
    "just_published": {
        "base": 84397800,
        "at": "2026-11-21 17:40:59 Asia/Hong_Kong",
        "game_time": 84397941,
        "all_five_200": True,
        "script_sum": 2821,
        "actual_sum": 2816,
        "script_by_room": {"W46N8": 974, "W47N8": 824, "W45N8": 403, "W45N7": 163, "W47N7": 457},
        "actual_by_room": {"W46N8": 972, "W47N8": 824, "W45N8": 402, "W45N7": 162, "W47N7": 456},
        "still_404": [],
    },
    "coverage": {
        "official_recovered": 3400,
        "expected": 3500,
        "empty_no_creep": 0,
        "official_404_missing": 100,
    },
    "inserted_total": 2816,
    "tick_s_in_use": 4.18908,
    "tick_s_in_use_name": "first",
    "tick_s_first": 4.18908,
    "ts_realigned_first": 0,
    "corrective": False,
    "tips": tips,
    "window_db": window_db,
    "listener": {
        "pid": 1983656,
        "started": "17:23:31",
        "parent": 4035476,
        "slot": "W46N8",
        "rot": rot,
        "yield_absent": True,
        "restarted_this_run": False,
    },
    "already_told_by_1733_patrol": {
        "box_freezes_in_window": ["16:48:46-17:04:41"],
        "short_ws_in_window": ["17:23:22"],
        "official_404s_in_window": ["W45N7@84397400"],
        "box_freezes_aged_out": [
            "16:16:43-16:19:24",
            "15:47:29-15:58:30",
            "15:14:38-15:19:30",
            "14:40:53-14:56:54",
            "14:15:50-14:23:29",
            "13:49:01-13:56:56",
            "13:09:46-13:21:14",
        ],
        "short_ws_aged_out": ["16:22:02"],
        "official_404s_aged_out": [
            "W47N7@84395600",
            "W47N8@84395100",
            "W46N8@84394300",
            "W45N8@84392600",
        ],
    },
    "new_untold_box_freezes": [],
    "new_untold_official_404s": [],
    "concurrent_patrol": "17:22/17:33 1h patrol _patrol_2026-11-21_1722 finished 17:34:40 just as this run started; this run did not write a patrol folder",
    "did_not_write_patrol_folder": True,
}

wrap = (
    f"---- wrap {AT} ----\n"
    "confirm at 2026-11-21 17:38:47 Asia/Hong_Kong game.time=84397910 still_404=['W45N7@84397400'] inserted=0 recovered=[]; "
    "retry2 at 2026-11-21 17:39:47 Asia/Hong_Kong game.time=84397924 still_404=['W45N7@84397400'] inserted=0 recovered=[]; "
    "late_retry at 2026-11-21 17:42:27 Asia/Hong_Kong game.time=84397961 still_404 W45N7@84397400 inserted=0. "
    "First pass 34/35 official GETs 200, missing_chunks=1 W45N7@84397400. "
    "Confirm 17:38:47, retry2 17:39:48 and late_retry 17:42:27 all still 404 inserted=0. "
    "Already-told leftover official 404s W47N7@84395600 / W47N8@84395100 / W46N8@84394300 / W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600 aged out of window start 84397101 and were not retried. "
    "Just-published 84397800 at 2026-11-21 17:40:59 Asia/Hong_Kong gt=84397941 all_five_200=True script=2821 actual=2816; "
    "W46N8 script 974 vs actual 972, W47N8 script 824 vs actual 824, W45N8 script 403 vs actual 402, W45N7 script 163 vs actual 162, W47N7 script 457 vs actual 456. "
    "Coverage official_recovered=3400/3500 empty_no_creep=0 official_404=100 (in-window leftover official 404 W45N7@84397400, listener 0/100, hole 100 ticks 84397401..84397500). "
    "Already told by the delivered 17:33 1h patrol and still in this window: box freeze 16:48:46-17:04:41 (954s; STATS 84397201..84397439, 239t) official-filled four rooms 239/239, W45N7 200/239 missing tail 84397401..84397439 because of leftover official 404 W45N7@84397400; listener auto-restart 17:04:44; "
    "short WS ping/pong 17:23:22 (STATS 84397671..84397699, 29t) official-filled all five 29/29; listener restart 17:23:22, python 1983656 started 17:23:31 (before this run's first pass; this run did not restart it); "
    "leftover official 404 W45N7@84397400 still 404 after this run's confirm/retry2/late_retry. "
    "The delivered 17:33 1h patrol had already official-filled 84397101..84397700 plus late retry just-published 84397700 at 17:32:37..17:32:49 gt=84397822 all five 200; the 17:00 backfill already official-filled 84396701..84397400 plus just-published 84397400 except W45N7@84397400. "
    "inserted_first=0 confirm=0 retry2=0 late=0 just_actual=2816 total=2816. "
    "tick_s_printed=4.189 first=4.18908 in_use=4.18908 (first) ts_realigned_first=0 corrective=0. "
    "First-pass overlap compared=25164 match=25145 differ=19 (samples are W45N8 rhauler84396824 at chunk 84397501; existing listener/patrol rows kept, official not overwritten). "
    'Listener pid=1983656 started=17:23:31 parent=4035476 slot=W46N8 rot={"i": 0, "room": "W46N8", "left": 235.0, "at": "2026-11-21 17:43:53"} yield=absent restarted_this_run=false. '
    "Peacetime single-slot 5:5:1:1. This run did not restart the listener or war_cmd/pulse. "
    "The 17:22/17:33 1h patrol _patrol_2026-11-21_1722 finished 17:34:40 just as this run started; this run did not write a patrol folder.\n"
    "NEW not-yet-told for the next 1h patrol: none. "
    "Already told by the delivered 17:33 亚洲/香港 1h patrol and still in official window start 84397101: box freeze 16:48:46-17:04:41 (954s; STATS 84397201..84397439, 239t; official-filled four rooms 239/239, W45N7 200/239 missing tail 84397401..84397439 because of leftover official 404 W45N7@84397400; listener auto-restart 17:04:44), "
    "short WS ping/pong 17:23:22 (not a box freeze; STATS 84397671..84397699, 29t; official-filled all five 29/29; listener restart 17:23:22, python 1983656 started 17:23:31), "
    "leftover official 404 W45N7@84397400 (still 404 after confirm 17:38:47 gt=84397910, retry2 17:39:48 gt=84397924 and late_retry 17:42:27 gt=84397961; listener 0/100, hole 100 ticks 84397401..84397500). "
    "Already told by the 17:33/16:32/15:28 patrols and now age out of window start 84397101: box freeze 16:16:43-16:19:24 (161s; STATS 84396751..84396799, 49t; official-filled all five 49/49; listener auto-restart 16:19:27), "
    "short WS ping/pong 16:22:02 (not a box freeze; STATS 84396821..84396839, 19t; official-filled all five 19/19; listener restart 16:22:05), "
    "box freeze 15:47:29-15:58:30 (655s; STATS 84396331..84396509, 179t; official-filled four rooms 179/179, W45N7 173/179 evac empty tail 84396331..84396336 official 200 not a 404), "
    "box freeze 15:14:38-15:19:30 (292s; STATS 84395871..84395959, 89t; official-filled W46N8/W47N8/W45N8/W47N7 89/89, W45N7 59/89 evac empty tail 84395930..84395959 official 200 not a 404), "
    "leftover official 404 W47N7@84395600 (listener 0/100, hole 100 ticks 84395601..84395700; last retried 17:27:10 gt=84397743 still 404, not retried this run), "
    "leftover official 404 W47N8@84395100 (listener 0/100, hole 100 ticks 84395101..84395200), "
    "leftover official 404 W46N8@84394300 (listener 79/100 84394301..84394379, hole 21 ticks 84394380..84394400), "
    "box freeze 14:40:53-14:56:54 (952s; STATS 84395401..84395639, 239t; official-filled four rooms 239/239, W47N7 200/239 missing 84395601..84395639 because of leftover official 404 W47N7@84395600), "
    "box freeze 14:15:50-14:23:29 (450s; STATS 84395061..84395179, 119t; official-filled four rooms 119/119, W47N8 40/119 missing 84395101..84395179 because of leftover official 404 W47N8@84395100), "
    "box freeze 13:49:01-13:56:56 (475s; STATS 84394681..84394809, 129t; official-filled all five 129/129), box freeze 13:09:46-13:21:14, earlier already-told freezes 12:48:14-12:57:17 / 12:30:42-12:35:35 / 11:49:12-11:57:31 / 11:19:06-11:20:43, short WS gaps 12:10 / 12:18 / 11:12, and older leftover official 404s W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600. "
    "Fold only newer freezes, short WS gaps, or leftover official 404s than the 17:33-told set; do not re-tell 16:48:46-17:04:41, W45N7@84397400, the 17:23:22 short WS, 16:16:43-16:19:24, the 16:22:02 short WS, 15:47:29-15:58:30, W47N7@84395600, or earlier already-told items.\n"
)

verify = (
    f"wrap {AT}\n"
    "window 84397101..84397800 first_pass 34/35 missing_chunks=1 W45N7@84397400\n"
    f"db_window {json.dumps(window_db, separators=(', ', ': '))}\n"
    "W45N7@84397400 already-told leftover still 404 distinct=0 rows=0 range=None..None (listener 0/100, confirm+retry2+late_retry still 404)\n"
    "W47N7@84395600 aged-out hole distinct=0 rows=0 range=None..None (listener 0/100, not retried this run)\n"
    "W47N8@84395100 aged-out hole distinct=0 rows=0 range=None..None (listener 0/100, not retried this run)\n"
    "W46N8@84394300 aged-out hole distinct=79 rows=893 range=84394301..84394379 (listener 79/100, not retried this run)\n"
    "just_published 84397800 all_five_200=True script=2821 actual=2816 by_actual={'W46N8': 972, 'W47N8': 824, 'W45N8': 402, 'W45N7': 162, 'W47N7': 456} by_script={'W46N8': 974, 'W47N8': 824, 'W45N8': 403, 'W45N7': 163, 'W47N7': 457} still_404=[]\n"
    "coverage official_recovered=3400/3500 empty_no_creep=0 official_404=100\n"
    "inserted_first=0 confirm=0 retry2=0 late=0 just_actual=2816 total=2816\n"
    "tick_s_in_use=4.18908 (first) first=4.18908 ts_realigned_first=0 corrective=0\n"
    "already_told_in_window freeze 16:48:46-17:04:41 four_rooms=239/239 W45N7=200/239 missing_tail=84397401..84397439 due_to_W45N7@84397400; short_ws 17:23:22 all_five=29/29\n"
    "overlap_differ=19 kept_existing_listener_rows\n"
    f"tips {tips}\n"
    f"listener pid=1983656 started=17:23:31 parent=4035476 slot=W46N8 rot={json.dumps(rot, separators=(', ', ': '))} yield_absent=True restarted_this_run=False\n"
    "ok_quiet=True new_official_404_untold=[] new_box_freeze_untold=[]\n"
    + wrap.split("NEW not-yet-told", 1)[1]
)
# the last line above starts mid-sentence; prepend the marker
# Fix: include the NEW paragraph from wrap
verify = verify.rsplit("\n", 1)[0] + "\nNEW not-yet-told" + wrap.split("NEW not-yet-told", 1)[1]

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2) + "\n")
first = (DIR / "history_backfill_first_attempt.txt").read_text()
if not first.endswith("\n"):
    first += "\n"
now_txt = first + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_verify.txt").write_text(verify)
(DIR / "verify.txt").write_text(verify)
(DIR / "wrapup_run.txt").write_text(f"wrap {AT} ok_quiet=True inserted_total=2816\n")

# top-level copies for the next 1h patrol
shutil.copy2(DIR / "history_backfill.json", STATE / "history_backfill.json")
shutil.copy2(DIR / "history_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")
print("wrote wrapup files")
print("ok_quiet", payload["ok_quiet"], "inserted_total", payload["inserted_total"])
print("now_txt bytes", len(now_txt), "verify bytes", len(verify))
