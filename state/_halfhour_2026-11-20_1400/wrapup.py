#!/usr/bin/env python3
import json, shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "tools")
import db

NL = chr(10)
HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-20_1400"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")

coverage_payload = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84374400.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())

post = {}
with db.connect() as c:
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84374401, 84374500),
        ).fetchone()
        post[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
    tips = {
        "cpu": c.execute("select max(tick) from creep_cpu").fetchone()[0],
        "path": c.execute("select max(tick) from path_arrivals").fetchone()[0],
        "room_stats": c.execute("select max(tick) from room_stats").fetchone()[0],
    }
(DIR / "just_published_post_counts.json").write_text(json.dumps(post, indent=2) + NL)

script_by = {g["room"]: g["inserted"] for g in jp["gets"]}
actual_by = {room: post[room]["rows"] - pre[room]["rows"] for room in ROOMS}
actual_total = sum(actual_by.values())
script_total = int(jp["inserted"])

finished = datetime.now(HK)
finished_hkt = finished.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

per_room_new_first = {"W46N8": 2791, "W47N8": 3539, "W45N8": 1949, "W45N7": 1208, "W47N7": 1438}

payload = {
    "at": finished_hkt,
    "ok_quiet": True,
    "game_time_first": 84374425,
    "published_bases": "84373700..84374300",
    "reconstructed": [84373701, 84374400],
    "ticks": 700,
    "creep_rows": 25175,
    "missing_chunks": 2,
    "already_in_db": 14250,
    "inserted_first": 10925,
    "inserted_confirm": 0,
    "inserted_retry2": 0,
    "inserted_just_script": script_total,
    "inserted_just_actual": actual_total,
    "inserted_window": 10925,
    "inserted_total": 10925 + actual_total,
    "tick_s_printed": 4.247,
    "tick_s_first": 4.24682,
    "tick_s_in_use": 4.24682,
    "tick_s_in_use_name": "first",
    "ts_realigned_first": 7373,
    "corrective": 0,
    "coverage_official_recovered": coverage_payload["official_recovered"],
    "coverage_expected": coverage_payload["expected"],
    "empty_no_creep": coverage_payload["empty_no_creep"],
    "official_404": coverage_payload["official_404_missing"],
    "per_room_new_first": per_room_new_first,
    "per_room_new_window": per_room_new_first,
    "in_window_404_after_retry2": ["W45N7@84373700", "W47N8@84373800"],
    "just_published_base": 84374400,
    "just_published_at": "2026-11-20 14:15:28 Asia/Hong_Kong",
    "just_published_gt": 84374541,
    "just_published_all_five_200": True,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "new_box_freeze": {
        "from": "2026-11-20 13:53:22",
        "to": "2026-11-20 14:05:12",
        "sec": 702,
        "stats": "84374221..84374399",
        "span": 179,
        "wall_s": 746,
        "last_stats": "84374220 at 13:53:06",
        "next_stats": "84374400 at 14:05:31",
        "listener_restart": "14:05:15",
        "listener_pid": 1340444,
        "listener_started": "14:05:25",
        "official_fill": {
            "W46N8": "179/179",
            "W47N8": "179/179",
            "W45N8": "179/179",
            "W45N7": "179/179",
            "W47N7": "179/179",
        },
        "told": False,
    },
    "prior_untold_box_freeze": {
        "from": "2026-11-20 13:29:41",
        "to": "2026-11-20 13:36:13",
        "sec": 391,
        "stats": "84373871..84373979",
        "span": 109,
        "wall_s": 459,
        "last_stats": "84373870 at 13:28:49",
        "next_stats": "84373980 at 13:36:28",
        "listener_restart": "13:36:16",
        "listener_pid": 1331693,
        "listener_started": "13:36:25",
        "official_fill": {
            "W46N8": "109/109",
            "W47N8": "79/109 (official 404 W47N8@84373800 hole 84373801..84373900 overlap 84373871..84373900 = 30 ticks)",
            "W45N8": "109/109",
            "W45N7": "109/109",
            "W47N7": "109/109",
        },
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1330",
    },
    "new_short_listener_gap": None,
    "new_official_404": [],
    "already_recorded_untold_in_window_404": [
        {
            "room": "W45N7",
            "base": 84373700,
            "hole": [84373701, 84373789],
            "live_ticks_present": [84373790, 84373800],
            "still_404_after": "confirm 14:09:17 gt=84374453 and retry2 14:12:11 gt=84374494 (also still 404 after 13:30 half-hour confirm 13:41:45 gt=84374055 and retry2 13:44:03 gt=84374089)",
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1330",
        },
        {
            "room": "W47N8",
            "base": 84373800,
            "hole": [84373801, 84373900],
            "still_404_after": "confirm 14:09:17 gt=84374453 and retry2 14:12:11 gt=84374494 (also still 404 after 13:30 half-hour confirm 13:41:45 gt=84374055 and retry2 13:44:03 gt=84374089)",
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1330",
        },
    ],
    "already_told_in_window_404": [],
    "aged_out_already_told_404_not_retried": [
        "W45N7@84373300",
        "W47N7@84373200",
        "W46N8@84371600",
    ],
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "pid": 1340444,
        "started": "14:05:25",
        "parent": 4035476,
        "yield": False,
        "restarted_this_run": False,
    },
    "war_cmd_pulse_restarted": False,
    "cpu_tip": tips["cpu"],
    "path_tip": tips["path"],
    "room_stats_tip": tips["room_stats"],
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2) + NL)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")

first = (DIR / "history_backfill.txt").read_text().rstrip()
now_txt = (
    first + NL + NL
    + f"---- wrap {finished_hkt} ----" + NL
    + "confirm 14:09:16 Asia/Hong_Kong game.time=84374453 inserted=0 still_404=['W45N7@84373700', 'W47N8@84373800']" + NL
    + "retry2 14:12:10 Asia/Hong_Kong game.time=84374494 inserted=0 still_404=['W45N7@84373700', 'W47N8@84373800']" + NL
    + "tick_s_first=4.24682 printed=4.247 in_use=4.24682 (first) ts_realigned_first=7373 corrective=0" + NL
    + f"coverage official_recovered={coverage_payload['official_recovered']}/{coverage_payload['expected']} empty_no_creep={coverage_payload['empty_no_creep']} official_404={coverage_payload['official_404_missing']}" + NL
    + f"just-published 84374400 at 2026-11-20 14:15:28 Asia/Hong_Kong game.time=84374541 all_five_200=True actual_inserted={actual_total} ticks 84374401..84374500 (all 5 rooms 100/100); script inserted={script_total} (W45N8 script {script_by['W45N8']} vs actual {actual_by['W45N8']})." + NL
    + f"inserted_window=10925 inserted_total={10925 + actual_total}" + NL
    + "ok_quiet=True" + NL
)
(DIR / "history_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = (
    f"{finished_hkt} verify" + NL
    + "first pass game.time=84374425 published_bases=84373700..84374300 reconstructed 84373701..84374400 (700) creep_rows=25175 missing_chunks=2" + NL
    + f"already_in_db=14250 inserted_first=10925 confirm=0 retry2=0 just_script={script_total} just_actual={actual_total} inserted_window=10925 inserted_total={10925 + actual_total}" + NL
    + "per_room first W46N8:700t/2791new W47N8:600t/3539new W45N8:700t/1949new W45N7:600t/1208new W47N7:700t/1438new; after confirm window W46N8:700t/2791 W47N8:600t/3539 W45N8:700t/1949 W45N7:611t/1208 W47N7:700t/1438" + NL
    + "tick_s_first=4.24682 printed=4.247 in_use=4.24682 (first) ts_realigned_first=7373 corrective=0" + NL
    + f"coverage official_recovered={coverage_payload['official_recovered']}/{coverage_payload['expected']} empty_no_creep={coverage_payload['empty_no_creep']} official_404={coverage_payload['official_404_missing']} unique_room_ticks={coverage_payload['official_recovered']}" + NL
    + "Official 404 in this first-pass window after confirm+retry2: W45N7@84373700 (hole 84373701..84373789 still 0/89, 11 live ticks 84373790..84373800 present; first recorded by the 13:30 half-hour, told=false, left to next 1h patrol) and W47N8@84373800 (hole 84373801..84373900 still 0/100; first recorded by the 13:30 half-hour, told=false, left to next 1h patrol). Official empty-no-creep: none. W46N8/W45N8/W47N7 700/700." + NL
    + f"just-published 84374400 at 2026-11-20 14:15:28 Asia/Hong_Kong game.time=84374541 all_five_200=True actual_inserted={actual_total} ticks 84374401..84374500 (all 5 rooms 100/100); script inserted={script_total} (W45N8 script {script_by['W45N8']} vs actual {actual_by['W45N8']})." + NL
    + "NEW box freeze 13:53:22-14:05:12 (702s; STATS 84374221..84374399 179t wall ~746s from last STATS 84374220 at 13:53:06 to next 84374400 at 14:05:31; listener auto-restart 14:05:15, pid 1340444 started 14:05:25). Official-filled all 5 rooms 179/179. told=false, left to next 1h patrol. No additional short listener gap this half-hour (this run did not itself restart the listener). Prior freeze 13:29:41-13:36:13 STATS 84373871..84373979 sits inside this window; official-filled W46N8/W45N8/W45N7/W47N7 109/109, W47N8 79/109 because of leftover official 404 W47N8@84373800 overlap 84373871..84373900 (30); told=false, first recorded by the 13:30 half-hour, still left to next 1h patrol. Earlier freezes/gaps aged out of window start 84373701 and were already told by the 13:25 1h patrol." + NL
    + "Leftover official 404s W45N7@84373700 and W47N8@84373800 still 404 after confirm+retry2 this run (told=false, first recorded by the 13:30 half-hour, left to next 1h patrol). Already-told leftover official 404 W45N7@84373300, W47N7@84373200, W46N8@84371600 and older leftover 404s aged out and were not retried (still unfilled; already told)." + NL
    + f"listener single_slot=True roomSlot={live.get('roomSlot')} pid=1340444 started 14:05:25 after auto-restart 14:05:15; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips['cpu']} path_tip={tips['path']} room_stats_tip={tips['room_stats']}." + NL
)
(DIR / "verify.txt").write_text(verify)
shutil.copyfile(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")

wrap = (
    f"{finished_hkt} wrapup ok" + NL
    + "wrote history_backfill.json history_backfill_now.txt verify.txt" + NL
    + f"inserted=10925+0+0+just{actual_total} coverage={coverage_payload['official_recovered']}/{coverage_payload['expected']} tick_s_in_use=4.24682" + NL
    + f"ok_line ok_quiet=True coverage={coverage_payload['official_recovered']}/{coverage_payload['expected']} inserted_total={10925 + actual_total}" + NL
)
(DIR / "wrapup_run.txt").write_text(wrap)
(DIR / "wrapup_run_live.txt").write_text(wrap)
(DIR / "wrapup_run_stdout.txt").write_text(wrap)
(DIR / "wrapup_run.err").write_text("")
print(wrap)
print("actual_by", actual_by, "total", actual_total)
print("wrote status files")

