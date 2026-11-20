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
DIR = ROOT / "state" / "_halfhour_2026-11-20_1500"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84375200
JUST_T0, JUST_T1 = JUST_BASE + 1, JUST_BASE + 100
GAP_S, GAP_E, GAP_SPAN = 84374991, 84375229, 239

coverage_payload = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / f"just_published_{JUST_BASE}.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())

post = {}
official_fill = {}
prior_gap_fill = {}
with db.connect() as c:
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, JUST_T0, JUST_T1),
        ).fetchone()
        post[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
        gd = c.execute(
            "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, GAP_S, GAP_E),
        ).fetchone()[0] or 0
        official_fill[room] = f"{int(gd)}/{GAP_SPAN}"
        pd = c.execute(
            "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84374801, 84374819),
        ).fetchone()[0] or 0
        prior_gap_fill[room] = f"{int(pd)}/19"
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
all_five_200 = all(g.get("code") == 200 and g.get("ok") for g in jp["gets"]) and not jp.get("still_404")
jp_distinct = ", ".join(f"{room} {post[room]['distinct']}/100" for room in ROOMS)
mismatch = [room for room in ROOMS if script_by.get(room, 0) != actual_by[room]]
mismatch_s = ", ".join(f"{r} script {script_by[r]} vs actual {actual_by[r]}" for r in mismatch)
just_note = (
    f"just-published {JUST_BASE} at {jp.get('at')} game.time={jp.get('game_time')} "
    f"all_five_200={all_five_200} actual_inserted={actual_total} ticks {JUST_T0}..{JUST_T1} "
    f"({jp_distinct}); script inserted={script_total}"
    + (f" ({mismatch_s})." if mismatch_s else ".")
)

finished = datetime.now(HK)
finished_hkt = finished.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

per_room_new_first = {"W46N8": 2689, "W47N8": 3175, "W45N8": 1145, "W45N7": 1015, "W47N7": 1729}

payload = {
    "at": finished_hkt,
    "ok_quiet": True,
    "game_time_first": 84375281,
    "published_bases": "84374500..84375100",
    "reconstructed": [84374501, 84375200],
    "ticks": 700,
    "creep_rows": 25384,
    "missing_chunks": 0,
    "already_in_db": 15631,
    "inserted_first": 9753,
    "inserted_confirm": 0,
    "inserted_retry2": 0,
    "inserted_just_script": script_total,
    "inserted_just_actual": actual_total,
    "inserted_window": 9753,
    "inserted_total": 9753 + actual_total,
    "tick_s_printed": 4.152,
    "tick_s_first": 4.15205,
    "tick_s_in_use": 4.15205,
    "tick_s_in_use_name": "first",
    "ts_realigned_first": 0,
    "corrective": 0,
    "coverage_official_recovered": coverage_payload["official_recovered"],
    "coverage_expected": coverage_payload["expected"],
    "empty_no_creep": coverage_payload["empty_no_creep"],
    "official_404": coverage_payload["official_404_missing"],
    "per_room_new_first": per_room_new_first,
    "per_room_new_window": per_room_new_first,
    "in_window_404_after_retry2": [],
    "just_published_base": JUST_BASE,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": all_five_200,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "new_box_freeze": None,
    "new_short_listener_gap": {
        "why": "ws ping/pong timed out 15:02:26 (not a box freeze; box_pauses.jsonl unchanged)",
        "listener_restart": "15:02:29",
        "listener_pid": 1362384,
        "listener_started": "15:02:39",
        "stats": "84374991..84375229",
        "span": 239,
        "last_stats": "84374990 at 14:46:25",
        "next_stats": "84375230 at 15:03:14",
        "wall_s": 1009,
        "official_fill": official_fill,
        "filled_by": "first pass through 84375200 plus just-published 84375200 (ticks 84375201..84375300)",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1500",
    },
    "already_recorded_untold_short_listener_gap_in_window": {
        "why": "ws ping/pong timed out 14:34:16 (not a box freeze; box_pauses.jsonl unchanged)",
        "listener_restart": "14:34:19",
        "listener_pid": 1355718,
        "listener_started": "14:34:28",
        "stats": "84374801..84374819",
        "span": 19,
        "last_stats": "84374800 at 14:33:22",
        "next_stats": "84374820 at 14:34:45",
        "wall_s": 83,
        "official_fill": prior_gap_fill,
        "filled_by": "14:30 just-published 84374800 (ticks 84374801..84374900, all 5 rooms 100/100)",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1430",
    },
    "new_official_404": [],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [],
    "aged_out_already_told_404_not_retried": [
        "W45N7@84373700",
        "W47N8@84373800",
        "W45N7@84373300",
        "W47N7@84373200",
        "W46N8@84371600",
    ],
    "prior_told_box_freeze_in_window": None,
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-20 13:53:22",
        "to": "2026-11-20 14:05:12",
        "sec": 702,
        "stats": "84374221..84374399",
        "span": 179,
        "official_fill": {
            "W46N8": "179/179",
            "W47N8": "179/179",
            "W45N8": "179/179",
            "W45N7": "179/179",
            "W47N7": "179/179",
        },
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1421 ~14:28",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "pid": 1362384,
        "started": "15:02:39",
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
    + "confirm 15:08:39 Asia/Hong_Kong skipped, no targets (missing_chunks=0; leftover 404s aged out of window start 84374501)" + NL
    + "retry2 15:08:39 Asia/Hong_Kong skipped, no targets" + NL
    + "tick_s_first=4.15205 printed=4.152 in_use=4.15205 (first) ts_realigned_first=0 corrective=0" + NL
    + f"coverage official_recovered={coverage_payload['official_recovered']}/{coverage_payload['expected']} empty_no_creep={coverage_payload['empty_no_creep']} official_404={coverage_payload['official_404_missing']}" + NL
    + just_note + NL
    + f"inserted_window=9753 inserted_total={9753 + actual_total}" + NL
    + "ok_quiet=True" + NL
)
(DIR / "history_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

fill_s = ", ".join(f"{r} {official_fill[r]}" for r in ROOMS)
verify = (
    f"{finished_hkt} verify" + NL
    + "first pass game.time=84375281 published_bases=84374500..84375100 reconstructed 84374501..84375200 (700) creep_rows=25384 missing_chunks=0" + NL
    + f"already_in_db=15631 inserted_first=9753 confirm=0 retry2=0 just_script={script_total} just_actual={actual_total} inserted_window=9753 inserted_total={9753 + actual_total}" + NL
    + "per_room first W46N8:700t/2689new W47N8:700t/3175new W45N8:700t/1145new W45N7:700t/1015new W47N7:700t/1729new; after confirm window all 5 rooms 700/700" + NL
    + "tick_s_first=4.15205 printed=4.152 in_use=4.15205 (first) ts_realigned_first=0 corrective=0" + NL
    + f"coverage official_recovered={coverage_payload['official_recovered']}/{coverage_payload['expected']} empty_no_creep={coverage_payload['empty_no_creep']} official_404={coverage_payload['official_404_missing']} unique_room_ticks={coverage_payload['official_recovered']}" + NL
    + "Official 404 in this first-pass window after confirm+retry2: none (first pass 35/35 official GETs 200). Official empty-no-creep: none. All 5 rooms 700/700." + NL
    + just_note + NL
    + f"NEW short listener gap 15:02:26 ws ping/pong timed out (not a box freeze; box_pauses.jsonl unchanged); listener auto-restart 15:02:29, pid 1362384 started 15:02:39. STATS 84374991..84375229 (239t) wall ~1009s from last STATS 84374990 at 14:46:25 to next 84375230 at 15:03:14. Official-filled {fill_s} via first pass through 84375200 plus just-published 84375200. told=false, first recorded by this 15:00 half-hour, left to next 1h patrol. This run did not itself restart the listener. Prior short gap 14:34:16 STATS 84374801..84374819 sits inside this window and remains official-filled 19/19 all 5; already recorded by the 14:30 half-hour, told=false, still left to next 1h patrol. Prior freeze 13:53:22-14:05:12 STATS 84374221..84374399 aged out of window start 84374501 and was already told by the 14:28 1h patrol. Earlier freeze 13:29:41-13:36:13 also aged out and was already told by that patrol." + NL
    + "No leftover official 404s in this window. Already-told leftover official 404s W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 and older leftover 404s aged out and were not retried (still unfilled; already told)." + NL
    + f"listener single_slot=True roomSlot={live.get('roomSlot')} pid=1362384 started 15:02:39 after auto-restart 15:02:29; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips['cpu']} path_tip={tips['path']} room_stats_tip={tips['room_stats']}." + NL
)
(DIR / "verify.txt").write_text(verify)
shutil.copyfile(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")

wrap = (
    f"{finished_hkt} wrapup ok" + NL
    + "wrote history_backfill.json history_backfill_now.txt verify.txt" + NL
    + f"inserted=9753+0+0+just{actual_total} coverage={coverage_payload['official_recovered']}/{coverage_payload['expected']} tick_s_in_use=4.15205" + NL
    + f"ok_line ok_quiet=True coverage={coverage_payload['official_recovered']}/{coverage_payload['expected']} inserted_total={9753 + actual_total}" + NL
)
(DIR / "wrapup_run.txt").write_text(wrap)
(DIR / "wrapup_run_live.txt").write_text(wrap)
(DIR / "wrapup_run_stdout.txt").write_text(wrap)
(DIR / "wrapup_run.err").write_text("")
print(wrap)
print("actual_by", actual_by, "total", actual_total)
print("official_fill", official_fill)
print("wrote status files")
