#!/usr/bin/env python3
from pathlib import Path
import json, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2030")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
NL = chr(10)
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")

cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84380000.json").read_text())
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

INSERTED_FIRST = 3968
INSERTED_CONFIRM = 491
INSERTED_RETRY2 = 0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
JUST_ACTUAL = actual_sum
JUST_SCRIPT = script_sum
INSERTED_TOTAL = INSERTED_WINDOW + JUST_ACTUAL

FILL_2017 = {room: gaps["freeze_2017"][room]["fill"] for room in ROOMS}
FILL_1942 = {room: gaps["freeze_1942"][room]["fill"] for room in ROOMS}

w47n8_hole = holes.get("W47N8@84379500")
w45n8_hole = holes.get("W45N8@84378900")

TICK_S_PRINTED = 4.166
TICK_S_FIRST = 4.16599
TICK_S_IN_USE = float(tickj["tick_s_in_use"])
TICK_S_IN_USE_NAME = tickj.get("tick_s_in_use_name") or "first"

payload = {
    "at": AT,
    "ok_quiet": True,
    "game_time_first": 84380007,
    "published_bases": "84379300..84379900",
    "reconstructed": [84379301, 84380000],
    "ticks": 700,
    "creep_rows": 26925,
    "missing_chunks": 2,
    "already_in_db": 22957,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_script": JUST_SCRIPT,
    "inserted_just_actual": JUST_ACTUAL,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "first_pass_by": "this run tools/history_backfill.py --minutes 40 finished ~20:36 (game.time=84380007, published_bases 84379300..84379900, reconstructed 84379301..84380000 missing_chunks=2 W47N8@84379500 and W47N7@84379900 inserted=3968 already_in_db=22957); 33/35 official GETs 200. Concurrent 1h patrol _patrol_2026-11-20_2024 had already filled 84379101..84379800 at 20:26:41 gt=84379868 (still 404 W47N8@84379500); this run did its own first pass because 84379800 and 84379900 had since published.",
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
    "per_room_new_first": {"W46N8": 761, "W47N8": 1998, "W45N8": 337, "W45N7": 413, "W47N7": 459},
    "per_room_new_window": {"W46N8": 761, "W47N8": 1998, "W45N8": 337, "W45N7": 413, "W47N7": 950},
    "in_window_404_after_retry2": ["W47N8@84379500"],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": ["W47N7@84379900"],
    "just_published_base": 84380000,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": all_five_200,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp.get("still_404") or [],
    "new_box_freeze": {
        "from": "2026-11-20 20:17:58",
        "to": "2026-11-20 20:20:29",
        "sec": 146,
        "why": "box frozen ~146s since 2026-11-20 20:17:58 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "20:20:32",
        "listener_pid": 1473092,
        "listener_started": "20:20:41",
        "stats": "84379751..84379799",
        "span": 49,
        "last_stats": "84379750 at 20:17:49",
        "next_stats": "84379800 at 20:21:17",
        "official_fill": FILL_2017,
        "filled_by": "Concurrent 1h patrol official first pass 20:26 plus this run first pass through 84380000. All five rooms 49/49. No official-404 hole in this STATS gap.",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2030 (visible in box_pauses.jsonl / errors.log after listener auto-restart 20:20:32; concurrent 1h patrol _patrol_2026-11-20_2024 started 20:24 after it had already healed)",
        "note": "This run did not itself restart the listener (run_listener.sh auto-restarted after the freeze). Left to the concurrent/next 1h patrol to tell. Fold only newer freezes than 20:17:58-20:20:29 once the 19:42:02-20:00:29 freeze has also been told.",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": {
        "from": "2026-11-20 19:42:02",
        "to": "2026-11-20 20:00:29",
        "sec": 1106,
        "why": "box frozen ~1106s since 2026-11-20 19:42:02 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "20:00:32",
        "stats": "84379221..84379509 clipped in this window to 84379301..84379509",
        "span_full": 289,
        "span_in_window": 209,
        "last_stats": "84379220 at 19:41:18",
        "next_stats": "84379510 at 20:01:12",
        "official_fill": FILL_1942,
        "filled_by": "Prior 20:00 half-hour / concurrent 20:26 patrol first pass plus this run. In the clipped window: W46N8/W45N8/W45N7/W47N7 209/209. W47N8 200/209 missing 84379501..84379509 (9t) because official 404 W47N8@84379500 remains unfilled (not empty-no-creep).",
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2000",
        "note": "Already recorded untold; left to the next 1h patrol (currently _patrol_2026-11-20_2024). Still partly in this window start 84379301.",
    },
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [],
    "already_recorded_untold_in_window_404": [{
        "chunk": "W47N8@84379500",
        "hole": "84379501..84379600",
        "live_ticks_present": "none (0t)",
        "still_404_after": "this run first pass ~20:36 gt=84380007, confirm 20:37:54 gt=84380039, and retry2 20:45:49 gt=84380153 (also still 404 at 20:00 half-hour 20:10:26/20:12:38/20:14:30 and concurrent patrol 20:26 gt=84379868).",
        "db": w47n8_hole,
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2000 official just-published 20:10:26",
        "note": "In-window leftover; retried this run and remains unfilled. Left to the concurrent/next 1h patrol to tell. Fold only newer official 404s than W47N8@84379500 once told.",
    }],
    "already_told_in_window_404": [],
    "already_recorded_untold_just_published_404": [],
    "aged_out_already_told_404_not_retried": [
        "W45N8@84378900", "W47N7@84378000", "W46N8@84377600", "W47N8@84377100",
        "W45N7@84376800", "W46N8@84376100", "W45N8@84375300", "W45N7@84373700",
        "W47N8@84373800", "W45N7@84373300", "W47N7@84373200", "W46N8@84371600",
    ],
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 19:16:42", "to": "2026-11-20 19:23:50", "sec": 424,
        "stats": "84378861..84378969", "span": 109,
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1923 ~19:35",
        "first_recorded_by": "concurrent 1h patrol _patrol_2026-11-20_1923 / 19:30 half-hour",
        "aged_out_of_window_start": 84379301,
        "note": "W45N8 still missing 84378901..84379000 (100t) because already-told official 404 W45N8@84378900 remains unfilled. Aged out and was not retried.",
    },
    "also_prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 18:46:28", "to": "2026-11-20 18:58:51", "sec": 742,
        "stats": "84378421..84378619", "span": 199,
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1923 ~19:35",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1900",
        "aged_out_of_window_start": 84379301,
    },
    "listener": {
        "single_slot": True, "roomSlot": live.get("roomSlot"), "rot": rot,
        "pid": 1473092, "started": "20:20:41", "parent": 4035476, "yield": False,
        "restarted_this_run": False,
        "auto_restart": "20:20:32 after box freeze 20:17:58-20:20:29; listener.py started 20:20:41",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": "_patrol_2026-11-20_2024 started 20:24; official first pass done 20:26:41; still running live queries when this half-hour began",
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + NL)
shutil.copy2(DIR / "history_backfill.json", STATE / "history_backfill.json")

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + NL
wrap = (
    f"---- wrap {AT} ----" + NL
    + "confirm retried in-window leftover official 404 W47N8@84379500 (hole 84379501..84379600) at 20:37:54 gt=84380039 and retry2 20:45:49 gt=84380153; still 404, inserted=0. Already recorded untold by the 20:00 half-hour; left to the concurrent/next 1h patrol. Confirm also recovered first-pass 404 W47N7@84379900 at 20:37:55 gt=84380039 (100 ticks, inserted=491). Already-told leftovers W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 aged out of window start 84379301 and were not retried." + NL
    + f"tick_s_first={TICK_S_FIRST} printed={TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} ({TICK_S_IN_USE_NAME}) ts_realigned_first=0 corrective=0" + NL
    + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
    + f"just-published 84380000 at {jp.get('at')} game.time={jp.get('game_time')} all_five_200={all_five_200} actual_inserted={JUST_ACTUAL} ticks 84380001..84380100 ({jp_distinct}); script inserted={JUST_SCRIPT}{mismatch_suffix}" + NL
    + f"inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL} (first {INSERTED_FIRST} + confirm {INSERTED_CONFIRM} + retry2 0 + just 84380000 actual {JUST_ACTUAL})" + NL
    + "ok_quiet=True" + NL
)
(DIR / "history_backfill_now.txt").write_text(first + NL + wrap)
(DIR / "history_backfill.txt").write_text(first)
shutil.copy2(DIR / "history_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

ua = cov["unique_after"]
verify_lines = [
    f"{AT} verify",
    "first pass this run finished ~20:36 game.time=84380007 published_bases=84379300..84379900 reconstructed 84379301..84380000 (700) creep_rows=26925 missing_chunks=2 W47N8@84379500 W47N7@84379900; 33/35 official GETs 200",
    f"already_in_db=22957 inserted_first=3968 confirm=491 retry2=0 just_80000_script={JUST_SCRIPT} just_80000_actual={JUST_ACTUAL} just_script={JUST_SCRIPT} just_actual={JUST_ACTUAL} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}",
    "per_room first W46N8:700t/761new W47N8:600t/1998new W45N8:700t/337new W45N7:700t/413new W47N7:600t/459new. Confirm recovered W47N7@84379900 (+491, now 700t). In-window official 404 after confirm+retry2: W47N8@84379500 still 404 (already recorded untold by the 20:00 half-hour). Aged-out already-told leftovers including W45N8@84378900 were not retried.",
    f"tick_s_first={TICK_S_FIRST} printed={TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} ({TICK_S_IN_USE_NAME}) ts_realigned_first=0 corrective=0",
    f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']} unique_room_ticks={ua['distinct_room_ticks']} unique_creep_tick_rows={ua['unique_creep_tick_rows']} (no dups).",
    "Official 404 in this first-pass window: W47N8@84379500 (ticks 84379501..84379600). Official empty-no-creep in-window: none. W46N8/W45N8/W45N7/W47N7 700/700; W47N8 600/700 (100 official 404).",
    f"just-published 84380000 at {jp.get('at')} game.time={jp.get('game_time')} all_five_200={all_five_200} actual_inserted={JUST_ACTUAL} ticks 84380001..84380100 ({jp_distinct}); script inserted={JUST_SCRIPT}{mismatch_suffix}",
    "NEW box freeze 20:17:58-20:20:29 (146s; box_pauses.jsonl / errors.log); listener auto-restart 20:20:32, pid 1473092 started 20:20:41. STATS 84379751..84379799 (49t) last STATS 84379750 at 20:17:49 to next STATS 84379800 at 20:21:17. Official-filled all five rooms 49/49. first recorded by this half-hour (concurrent 1h patrol started 20:24 after it had healed), told=false, left to that patrol. This run did not itself restart the listener.",
    "Already-recorded untold box freeze 19:42:02-20:00:29 (1106s) STATS 84379221..84379509 clipped in window start 84379301 to 84379301..84379509 (209t); official-filled W46N8/W45N8/W45N7/W47N7 209/209, W47N8 200/209 missing 84379501..84379509 (9t) because official 404 W47N8@84379500 still unfilled. first recorded by the 20:00 half-hour, told=false, left to the next 1h patrol.",
    "Prior box freeze 19:16:42-19:23:50 STATS 84378861..84378969 aged out of window start 84379301 (already told by the 19:35 1h patrol). W45N8@84378900 aged out and was not retried.",
    "Prior box freeze 18:46:28-18:58:51 and earlier already-told freezes aged out of window start 84379301.",
    f"listener single_slot=True roomSlot={live.get('roomSlot')} pid=1473092 started 20:20:41 after auto-restart 20:20:32; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips['creep_cpu']} path_tip={tips['path_arrivals']} room_stats_tip={tips['room_stats']}.",
]
(DIR / "verify.txt").write_text(NL.join(verify_lines) + NL)
shutil.copy2(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")

retry_lines = [
    "confirm W47N8@84379500 still 404 at 20:37:54 gt=84380039 and retry2 20:45:49 gt=84380153 (already recorded untold by 20:00 half-hour).",
    "confirm recovered W47N7@84379900 at 20:37:55 gt=84380039 100 ticks inserted=491.",
    f"just-published 84380000 all five 200 actual_inserted={JUST_ACTUAL} script={JUST_SCRIPT}.",
]
(DIR / "backfill_retry2.txt").write_text(NL.join(retry_lines) + NL)
shutil.copy2(DIR / "backfill_retry2.txt", STATE / "_halfhour_backfill_retry2_2030.txt")

(DIR / "wrapup_run.txt").write_text(f"wrapup wrote {AT} ok_quiet=True inserted_total={INSERTED_TOTAL}" + NL)
(DIR / "wrapup_write.py").write_text(f"# wrapup executed inline for 2030; status written {AT}" + NL)

print("AT", AT)
print("JUST_ACTUAL", JUST_ACTUAL, "JUST_SCRIPT", JUST_SCRIPT)
print("INSERTED_WINDOW", INSERTED_WINDOW, "INSERTED_TOTAL", INSERTED_TOTAL)
print("all_five_200", all_five_200)
print("tick_s_in_use", TICK_S_IN_USE, TICK_S_IN_USE_NAME)
print("tips", tips)
print("ok")
