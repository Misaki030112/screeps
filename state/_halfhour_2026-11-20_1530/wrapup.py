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
DIR = ROOT / "state" / "_halfhour_2026-11-20_1530"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84375600
JUST_T0, JUST_T1 = JUST_BASE + 1, JUST_BASE + 100
GAP_S, GAP_E, GAP_SPAN = 84375391, 84375569, 179
PRIOR_S, PRIOR_E, PRIOR_SPAN = 84374991, 84375229, 239

coverage_payload = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / f"just_published_{JUST_BASE}.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())

post = {}
official_fill = {}
prior_gap_fill = {}
w45n8_404_live = {}
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
            (room, PRIOR_S, PRIOR_E),
        ).fetchone()[0] or 0
        prior_gap_fill[room] = f"{int(pd)}/{PRIOR_SPAN}"
    d, mn, mx, n = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W45N8", 84375301, 84375400),
    ).fetchone()
    w45n8_404_live = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
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

per_room_new_first = {"W46N8": 1062, "W47N8": 1491, "W45N8": 364, "W45N7": 69, "W47N7": 414}
INSERTED_WINDOW = 3400
TICK_S_FIRST = 4.21402
TICK_S_IN_USE = 4.178623333333333

payload = {
    "at": finished_hkt,
    "ok_quiet": True,
    "game_time_first": 84375643,
    "published_bases": "84374900..84375500",
    "reconstructed": [84374901, 84375600],
    "ticks": 700,
    "creep_rows": 24881,
    "missing_chunks": 1,
    "already_in_db": 21481,
    "inserted_first": 3400,
    "inserted_confirm": 0,
    "inserted_retry2": 0,
    "inserted_just_script": script_total,
    "inserted_just_actual": actual_total,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_WINDOW + actual_total,
    "tick_s_printed": 4.214,
    "tick_s_first": TICK_S_FIRST,
    "tick_s_in_use": TICK_S_IN_USE,
    "tick_s_in_use_name": "span_mean",
    "ts_realigned_first": 6594,
    "corrective": 0,
    "coverage_official_recovered": coverage_payload["official_recovered"],
    "coverage_expected": coverage_payload["expected"],
    "empty_no_creep": coverage_payload["empty_no_creep"],
    "official_404": coverage_payload["official_404_missing"],
    "per_room_new_first": per_room_new_first,
    "per_room_new_window": per_room_new_first,
    "in_window_404_after_retry2": ["W45N8@84375300"],
    "just_published_base": JUST_BASE,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": all_five_200,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "new_box_freeze": {
        "from": "2026-11-20 15:15:12",
        "to": "2026-11-20 15:26:38",
        "sec": 686,
        "why": "box frozen ~686s since 2026-11-20 15:15:12 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "15:26:41",
        "listener_pid": 1369176,
        "listener_started": "15:26:50",
        "stats": "84375391..84375569",
        "span": 179,
        "last_stats": "84375390 at 15:14:24",
        "next_stats": "84375570 at 15:26:56",
        "wall_s": 752,
        "official_fill": official_fill,
        "filled_by": "first pass through 84375600 (published 84375400 and 84375500 already 200 for all 5). W45N8 missing 84375391..84375400 (10t) because official 404 W45N8@84375300 still unfilled after confirm+retry2; W45N7 55/179 is official empty-no-creep after 84375446 (creeps not in room), not a 404.",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1530",
        "note": "Concurrent 1h patrol _patrol_2026-11-20_1526 was already running when this backfill started; this run did not write into that folder. Leave telling the freeze to the 1h patrol.",
    },
    "new_short_listener_gap": None,
    "already_recorded_untold_short_listener_gap_in_window": {
        "why": "ws ping/pong timed out 15:02:26 (not a box freeze; box_pauses.jsonl unchanged)",
        "listener_restart": "15:02:29",
        "listener_pid": 1362384,
        "listener_started": "15:02:39",
        "stats": "84374991..84375229",
        "span": 239,
        "last_stats": "84374990 at 14:46:25",
        "next_stats": "84375230 at 15:03:14",
        "wall_s": 1009,
        "official_fill": prior_gap_fill,
        "filled_by": "15:00 first pass through 84375200 plus just-published 84375200 (ticks 84375201..84375300)",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1500",
    },
    "aged_out_already_recorded_untold_short_listener_gap": {
        "why": "ws ping/pong timed out 14:34:16 (not a box freeze)",
        "stats": "84374801..84374819",
        "span": 19,
        "official_fill": "19/19 all 5 (14:30 just-published 84374800)",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1430",
        "aged_out_of_window_start": 84374901,
    },
    "new_official_404": [
        {
            "chunk": "W45N8@84375300",
            "hole": "84375301..84375400",
            "live_ticks_present": "84375304..84375332 (29t)",
            "still_404_after": "confirm 15:34:28 gt=84375678 and retry2 15:34:37 gt=84375680",
            "db": w45n8_404_live,
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1530",
        }
    ],
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
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1421 ~14:28",
        "also_aged_out": "13:29:41-13:36:13 STATS 84373871..84373979 also already told by that patrol",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "pid": 1369176,
        "started": "15:26:50",
        "parent": 4035476,
        "yield": False,
        "restarted_this_run": False,
        "auto_restart": "15:26:41 after box freeze 15:15:12-15:26:38",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": "_patrol_2026-11-20_1526",
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
    + "confirm 15:34:27 Asia/Hong_Kong W45N8@84375300 still 404 at 15:34:28 gt=84375678 (pre distinct=29 rows=111 range=84375304..84375332)" + NL
    + "retry2 15:34:36 Asia/Hong_Kong W45N8@84375300 still 404 at 15:34:37 gt=84375680; leftover 404s W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 and older aged out of window start 84374901 and were not retried" + NL
    + f"tick_s_first=4.21402 printed=4.214 in_use=4.17862 (span_mean) ts_realigned_first=6594 corrective=0" + NL
    + f"coverage official_recovered={coverage_payload['official_recovered']}/{coverage_payload['expected']} empty_no_creep={coverage_payload['empty_no_creep']} official_404={coverage_payload['official_404_missing']}" + NL
    + just_note + NL
    + f"inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_WINDOW + actual_total}" + NL
    + "ok_quiet=True" + NL
)
(DIR / "history_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

fill_s = ", ".join(f"{r} {official_fill[r]}" for r in ROOMS)
prior_s = ", ".join(f"{r} {prior_gap_fill[r]}" for r in ROOMS)
verify = (
    f"{finished_hkt} verify" + NL
    + "first pass game.time=84375643 published_bases=84374900..84375500 reconstructed 84374901..84375600 (700) creep_rows=24881 missing_chunks=1 W45N8@84375300" + NL
    + f"already_in_db=21481 inserted_first=3400 confirm=0 retry2=0 just_script={script_total} just_actual={actual_total} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_WINDOW + actual_total}" + NL
    + "per_room first W46N8:700t/1062new W47N8:700t/1491new W45N8:600t/364new W45N7:700t/69new W47N7:700t/414new; after confirm+retry2 W45N8@84375300 still 404 (29 live ticks 84375304..84375332 present, hole 71t 84375301..84375303 and 84375333..84375400). W45N7 official empty-no-creep 155t (84375445 and 84375447..84375600)." + NL
    + "tick_s_first=4.21402 printed=4.214 in_use=4.17862 (span_mean) ts_realigned_first=6594 corrective=0" + NL
    + f"coverage official_recovered={coverage_payload['official_recovered']}/{coverage_payload['expected']} empty_no_creep={coverage_payload['empty_no_creep']} official_404={coverage_payload['official_404_missing']} unique_room_ticks={coverage_payload['official_recovered']}" + NL
    + "Official 404 in this first-pass window after confirm+retry2: W45N8@84375300 (hole 84375301..84375400, 29 live ticks present, still 404 after 15:34:28/15:34:37 retries). Official empty-no-creep: W45N7 155t. W46N8/W47N8/W47N7 700/700; W45N8 629/700 (71 official 404); W45N7 545/700 (155 empty)." + NL
    + just_note + NL
    + f"NEW box freeze 15:15:12-15:26:38 (686s; box_pauses.jsonl); listener auto-restart 15:26:41, pid 1369176 started 15:26:50. STATS 84375391..84375569 (179t) wall ~752s from last STATS 84375390 at 15:14:24 to next 84375570 at 15:26:56. Official-filled {fill_s} via first pass through 84375600. W45N8 169/179 missing 84375391..84375400 because official 404 W45N8@84375300; W45N7 55/179 is official empty-no-creep after 84375446, not a 404. told=false, first recorded by this 15:30 half-hour, left to 1h patrol. This run did not itself restart the listener. Concurrent 1h patrol _patrol_2026-11-20_1526 was already running; this run did not write into that folder." + NL
    + f"Prior short listener gap 15:02:26 STATS 84374991..84375229 sits inside this window and remains official-filled {prior_s}; already recorded by the 15:00 half-hour, told=false, still left to 1h patrol. Prior short gap 14:34:16 STATS 84374801..84374819 aged out of window start 84374901 (already official-filled 19/19 all 5; recorded by the 14:30 half-hour, told=false). Prior freeze 13:53:22-14:05:12 STATS 84374221..84374399 aged out and was already told by the 14:28 1h patrol. Earlier freeze 13:29:41-13:36:13 also aged out and was already told by that patrol." + NL
    + "NEW leftover official 404 W45N8@84375300 (hole 84375301..84375400, 29 live ticks 84375304..84375332 present, still 404 after confirm+retry2); told=false, first recorded by this 15:30 half-hour, left to 1h patrol. Already-told leftover official 404s W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 and older leftover 404s aged out and were not retried (still unfilled; already told)." + NL
    + f"listener single_slot=True roomSlot={live.get('roomSlot')} pid=1369176 started 15:26:50 after auto-restart 15:26:41; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips['cpu']} path_tip={tips['path']} room_stats_tip={tips['room_stats']}." + NL
)
(DIR / "verify.txt").write_text(verify)
shutil.copyfile(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")

wrap = (
    f"{finished_hkt} wrapup ok" + NL
    + "wrote history_backfill.json history_backfill_now.txt verify.txt" + NL
    + f"inserted=3400+0+0+just{actual_total} coverage={coverage_payload['official_recovered']}/{coverage_payload['expected']} tick_s_in_use=4.17862" + NL
    + f"ok_line ok_quiet=True coverage={coverage_payload['official_recovered']}/{coverage_payload['expected']} inserted_total={INSERTED_WINDOW + actual_total}" + NL
)
(DIR / "wrapup_run.txt").write_text(wrap)
(DIR / "wrapup_run_live.txt").write_text(wrap)
(DIR / "wrapup_run_stdout.txt").write_text(wrap)
(DIR / "wrapup_run.err").write_text("")
print(wrap)
print("actual_by", actual_by, "total", actual_total)
print("official_fill", official_fill)
print("prior_gap_fill", prior_gap_fill)
print("w45n8_404_live", w45n8_404_live)
print("wrote status files")
print("just_note", just_note)
