#!/usr/bin/env python3
from pathlib import Path
import json, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2000")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
NL = chr(10)
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")

cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84379500.json").read_text())
summary = json.loads((DIR / "just_published_post_summary.json").read_text())
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())
tickj = json.loads((DIR / "tick_s_realign.json").read_text())

post = summary["post"]
actual_by = summary["actual_by_room"]
script_by = summary["script_by_room"]
actual_sum = int(summary["actual_sum"])
script_sum = int(summary["script_sum"])
holes = summary["holes"]
gaps = summary["gaps"]
tips = summary["tips"]

all_five_200 = all(g.get("code") == 200 and g.get("ok") for g in jp["gets"]) and not jp.get("still_404")
jp_distinct = ", ".join(f"{room} {post[room]['distinct']}/100" for room in ROOMS)

mismatch = [room for room in ROOMS if script_by.get(room, 0) != actual_by[room]]
mismatch_s = ", ".join(f"{r} script {script_by[r]} vs actual {actual_by[r]}" for r in mismatch)
mismatch_suffix = (" (" + mismatch_s + ").") if mismatch_s else "."

INSERTED_FIRST = 14451
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
JUST_ACTUAL = actual_sum
JUST_SCRIPT = script_sum
INSERTED_TOTAL = INSERTED_WINDOW + JUST_ACTUAL

FILL_1942 = {room: gaps["freeze_1942"][room]["fill"] for room in ROOMS}
FILL_1916 = {room: gaps["freeze_1916"][room]["fill"] for room in ROOMS}

w47n8_hole = holes.get("W47N8@84379500")
w45n8_hole = holes.get("W45N8@84378900")

TICK_S_PRINTED = 4.168
TICK_S_FIRST = 4.16761
TICK_S_IN_USE = float(tickj["tick_s_in_use"])
TICK_S_IN_USE_NAME = tickj.get("tick_s_in_use_name") or "all_mean"

payload = {
    "at": AT,
    "ok_quiet": True,
    "game_time_first": 84379542,
    "published_bases": "84378800..84379400",
    "reconstructed": [84378801, 84379500],
    "ticks": 700,
    "creep_rows": 26199,
    "missing_chunks": 1,
    "already_in_db": 11748,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_script": JUST_SCRIPT,
    "inserted_just_actual": JUST_ACTUAL,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "first_pass_by": "this run tools/history_backfill.py --minutes 40 finished ~20:04 (game.time=84379542, published_bases 84378800..84379400, reconstructed 84378801..84379500 missing_chunks=1 W45N8@84378900 inserted=14451 already_in_db=11748); 34/35 official GETs 200",
    "tick_s_printed": TICK_S_PRINTED,
    "tick_s_first": TICK_S_FIRST,
    "tick_s_in_use": TICK_S_IN_USE,
    "tick_s_in_use_name": TICK_S_IN_USE_NAME,
    "ts_realigned_first": 0,
    "corrective": 0,
    "coverage_official_recovered": cov["official_recovered"],
    "coverage_expected": cov["expected"],
    "empty_no_creep": cov["empty_no_creep"],
    "official_404": cov["official_404_missing"],
    "per_room_new_first": {"W46N8": 3985, "W47N8": 4231, "W45N8": 2469, "W45N7": 1257, "W47N7": 2509},
    "per_room_new_window": {"W46N8": 3985, "W47N8": 4231, "W45N8": 2469, "W45N7": 1257, "W47N7": 2509},
    "in_window_404_after_retry2": ["W45N8@84378900"],
    "first_pass_404_recovered_before_confirm": [],
    "just_published_base": 84379500,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": all_five_200,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp.get("still_404") or ["W47N8@84379500"],
    "new_box_freeze": {
        "from": "2026-11-20 19:42:02",
        "to": "2026-11-20 20:00:29",
        "sec": 1106,
        "why": "box frozen ~1106s since 2026-11-20 19:42:02 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "20:00:32",
        "listener_pid": 1464342,
        "listener_started": "20:00:42",
        "stats": "84379221..84379509",
        "span": 289,
        "last_stats": "84379220 at 19:41:18",
        "next_stats": "84379510 at 20:01:12",
        "official_fill": FILL_1942,
        "filled_by": "This run first pass through 84379500 plus just-published 84379500 for W46N8/W45N8/W45N7/W47N7. W46N8/W45N8/W45N7/W47N7 289/289. W47N8 280/289 missing 84379501..84379509 (9t) because official 404 W47N8@84379500 remains unfilled (not empty-no-creep).",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2000",
        "note": "This run did not itself restart the listener (run_listener.sh auto-restarted after the freeze). Left to the next 1h patrol to tell. Fold only newer freezes than 19:42:02-20:00:29.",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": {
        "from": "2026-11-20 19:16:42",
        "to": "2026-11-20 19:23:50",
        "sec": 424,
        "why": "box frozen ~424s since 2026-11-20 19:16:42 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "19:23:53",
        "stats": "84378861..84378969",
        "span": 109,
        "last_stats": "84378860 at 19:16:32",
        "next_stats": "84378970 at 19:24:08",
        "official_fill": FILL_1916,
        "filled_by": "Prior 19:30 half-hour / 19:35 patrol first pass through 84378900 plus just-published recoveries. W46N8/W47N8/W45N7/W47N7 109/109. W45N8 40/109 missing 84378901..84378969 (69t) because already-told official 404 W45N8@84378900 remains unfilled.",
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1923 ~19:35",
        "first_recorded_by": "concurrent 1h patrol _patrol_2026-11-20_1923 / 19:30 half-hour",
        "note": "Still in this window start 84378801.",
    },
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [{
        "chunk": "W45N8@84378900",
        "hole": "84378901..84379000",
        "live_ticks_present": "none (0t)",
        "still_404_after": "this run first pass ~20:04 gt=84379542, confirm 20:05:29 gt=84379572, and retry2 20:12:40 gt=84379675 (also still 404 after 19:30 half-hour / 19:35 patrol retries).",
        "db": w45n8_hole,
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1923 ~19:35",
        "first_recorded_by": "concurrent 1h patrol _patrol_2026-11-20_1923 official just-published 19:27:35",
        "note": "In-window leftover; retried this run and remains unfilled.",
    }],
    "already_recorded_untold_just_published_404": [{
        "chunk": "W47N8@84379500",
        "hole": "84379501..84379600",
        "live_ticks_present": "none in the official chunk at wrapup (0 distinct in 84379501..84379600); live rotation later sits after this chunk (W47N8 near tip 84379682..).",
        "still_404_after": "this run just-published GET 20:10:26 gt=84379642, retry 20:12:38 gt=84379675, and retry2 20:14:30 gt=84379702. Sits after first-pass TMAX=84379500 so it is not an in-window first-pass 404.",
        "db": w47n8_hole,
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2000 official just-published 20:10:26",
        "note": "Left to the next 1h patrol to tell. This half-hour retried twice after the first GET and it remains unfilled. Fold only newer official 404s than W47N8@84379500 once told.",
    }],
    "aged_out_already_told_404_not_retried": [
        "W47N7@84378000", "W46N8@84377600", "W47N8@84377100", "W45N7@84376800",
        "W46N8@84376100", "W45N8@84375300", "W45N7@84373700", "W47N8@84373800",
        "W45N7@84373300", "W47N7@84373200", "W46N8@84371600",
    ],
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 18:46:28", "to": "2026-11-20 18:58:51", "sec": 742,
        "stats": "84378421..84378619", "span": 199,
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1923 ~19:35",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1900",
        "aged_out_of_window_start": 84378801,
    },
    "also_prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 17:43:34", "to": "2026-11-20 18:02:53", "sec": 1158,
        "stats": "84377521..84377819", "span": 299,
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1819 ~18:31",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1800",
        "aged_out_of_window_start": 84378801,
        "note": "W46N8 still missing 84377601..84377700 (100t) because already-told official 404 W46N8@84377600 remains unfilled. Aged out and was not retried.",
    },
    "listener": {
        "single_slot": True, "roomSlot": live.get("roomSlot"), "rot": rot,
        "pid": 1464342, "started": "20:00:42", "parent": 4035476, "yield": False,
        "restarted_this_run": False,
        "auto_restart": "20:00:32 after box freeze 19:42:02-20:00:29; listener.py started 20:00:42",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": None,
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + NL)
shutil.copy2(DIR / "history_backfill.json", STATE / "history_backfill.json")

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + NL
wrap = (
    f"---- wrap {AT} ----" + NL
    + "confirm retried in-window leftover official 404 W45N8@84378900 (hole 84378901..84379000) at 20:05:29 gt=84379572 and retry2 20:12:40 gt=84379675; still 404, inserted=0. Already told by the 19:35 1h patrol. Already-told leftovers W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 aged out of window start 84378801 and were not retried." + NL
    + f"tick_s_first={TICK_S_FIRST} printed={TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} ({TICK_S_IN_USE_NAME}) ts_realigned_first=0 corrective=0" + NL
    + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
    + f"just-published 84379500 at {jp.get('at')} game.time={jp.get('game_time')} all_five_200={all_five_200} actual_inserted={JUST_ACTUAL} ticks 84379501..84379600 ({jp_distinct}); script inserted={JUST_SCRIPT}{mismatch_suffix} W47N8@84379500 still 404 after this run GET 20:10:26 gt=84379642, retry 20:12:38 gt=84379675, retry2 20:14:30 gt=84379702; hole 84379501..84379600, first recorded by this half-hour, told=false, left to the next 1h patrol." + NL
    + f"inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL} (first {INSERTED_FIRST} + confirm 0 + retry2 0 + just 84379500 actual {JUST_ACTUAL})" + NL
    + "ok_quiet=True" + NL
)
(DIR / "history_backfill_now.txt").write_text(first + NL + wrap)
(DIR / "history_backfill.txt").write_text(first)
shutil.copy2(DIR / "history_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

ua = cov["unique_after"]
verify_lines = [
    f"{AT} verify",
    "first pass this run finished ~20:04 game.time=84379542 published_bases=84378800..84379400 reconstructed 84378801..84379500 (700) creep_rows=26199 missing_chunks=1 W45N8@84378900; 34/35 official GETs 200",
    f"already_in_db=11748 inserted_first=14451 confirm=0 retry2=0 just_79500_script={JUST_SCRIPT} just_79500_actual={JUST_ACTUAL} just_script={JUST_SCRIPT} just_actual={JUST_ACTUAL} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}",
    "per_room first W46N8:700t/3985new W47N8:700t/4231new W45N8:600t/2469new W45N7:700t/1257new W47N7:700t/2509new. In-window official 404 after confirm+retry2: W45N8@84378900 still 404 (already told by the 19:35 1h patrol). Aged-out already-told leftovers were not retried.",
    f"tick_s_first={TICK_S_FIRST} printed={TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} ({TICK_S_IN_USE_NAME}) ts_realigned_first=0 corrective=0",
    f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']} unique_room_ticks={ua['distinct_room_ticks']} unique_creep_tick_rows={ua['unique_creep_tick_rows']} (no dups).",
    "Official 404 in this first-pass window: W45N8@84378900 (ticks 84378901..84379000). Official empty-no-creep in-window: none. W46N8/W47N8/W45N7/W47N7 700/700; W45N8 600/700 (100 official 404).",
    f"just-published 84379500 at {jp.get('at')} game.time={jp.get('game_time')} all_five_200={all_five_200} actual_inserted={JUST_ACTUAL} ticks 84379501..84379600 ({jp_distinct}); script inserted={JUST_SCRIPT}{mismatch_suffix} W47N8@84379500 still 404 after this run GET 20:10:26/20:12:38/20:14:30; hole 84379501..84379600, no official ticks; first recorded by this half-hour, told=false, left to the next 1h patrol.",
    "NEW box freeze 19:42:02-20:00:29 (1106s; box_pauses.jsonl / errors.log); listener auto-restart 20:00:32, pid 1464342 started 20:00:42. STATS 84379221..84379509 (289t) last STATS 84379220 at 19:41:18 to next STATS 84379510 at 20:01:12. Official-filled W46N8 289/289, W47N8 280/289, W45N8 289/289, W45N7 289/289, W47N7 289/289. W47N8 missing 84379501..84379509 (9t) because official 404 W47N8@84379500 still unfilled. first recorded by this half-hour, told=false, left to the next 1h patrol. This run did not itself restart the listener.",
    "Already-told box freeze 19:16:42-19:23:50 (424s) STATS 84378861..84378969 (109t) still in window start 84378801; official-filled W46N8/W47N8/W45N7/W47N7 109/109, W45N8 40/109 missing 84378901..84378969 (69t) because already-told official 404 W45N8@84378900 still unfilled. told by the 19:35 1h patrol.",
    "Prior box freeze 18:46:28-18:58:51 STATS 84378421..84378619 aged out of window start 84378801 (already told by the 19:35 1h patrol).",
    "Prior box freeze 17:43:34-18:02:53 and earlier already-told freezes aged out of window start 84378801.",
    f"listener single_slot=True roomSlot={live.get('roomSlot')} pid=1464342 started 20:00:42 after auto-restart 20:00:32; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips['creep_cpu']} path_tip={tips['path_arrivals']} room_stats_tip={tips['room_stats']}.",
]
(DIR / "verify.txt").write_text(NL.join(verify_lines) + NL)
shutil.copy2(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")

retry_lines = [
    "confirm W45N8@84378900 still 404 at 20:05:29 gt=84379572 and retry2 20:12:40 gt=84379675 (already told).",
    f"just-published 84379500 four rooms 200 actual_inserted={JUST_ACTUAL} script={JUST_SCRIPT}.",
    "W47N8@84379500 still 404 after 20:10:26 gt=84379642, 20:12:38 gt=84379675, 20:14:30 gt=84379702 (new leftover, told=false).",
]
(DIR / "backfill_retry2.txt").write_text(NL.join(retry_lines) + NL)
shutil.copy2(DIR / "backfill_retry2.txt", STATE / "_halfhour_backfill_retry2_2000.txt")

(DIR / "wrapup_run.txt").write_text(f"wrapup wrote {AT} ok_quiet=True inserted_total={INSERTED_TOTAL}" + NL)
(DIR / "wrapup_write.py").write_text(f"# wrapup executed inline for 2000; status written {AT}" + NL)

print("AT", AT)
print("JUST_ACTUAL", JUST_ACTUAL, "JUST_SCRIPT", JUST_SCRIPT)
print("INSERTED_TOTAL", INSERTED_TOTAL)
print("all_five_200", all_five_200)
print("tick_s_in_use", TICK_S_IN_USE, TICK_S_IN_USE_NAME)
print("tips", tips)
print("ok")
