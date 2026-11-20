#!/usr/bin/env python3
from pathlib import Path
import json, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1930")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
NL = chr(10)
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")

cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84378900.json").read_text())
jp79 = json.loads((DIR / "just_published_84379000.json").read_text())
summary = json.loads((DIR / "just_published_post_summary.json").read_text())
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())

post = summary["post"]
actual_by = summary["actual_by_room"]
script_by = summary["script_by_room"]
actual_78900 = int(summary["actual_sum"])
script_78900 = int(summary["script_sum"])
holes = summary["holes"]
gaps = summary["gaps"]

pre79 = json.loads((DIR / "just_published_79000_pre_counts.json").read_text())
script79_by = {g["room"]: int(g.get("inserted") or 0) for g in jp79["gets"]}
post79 = {}
actual79_by = {}
with db.connect() as c:
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84379001, 84379100),
        ).fetchone()
        post79[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
        actual79_by[room] = int(n or 0) - int((pre79.get(room) or {}).get("rows") or 0)
    tips = {table: c.execute(f"select max(tick) from {table}").fetchone()[0] for table in ("room_stats", "creep_cpu", "path_arrivals")}
    d, mn, mx, n = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W45N8", 84378901, 84379000),
    ).fetchone()
    w45n8_hole = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

(DIR / "just_published_79000_post_counts.json").write_text(json.dumps(post79, indent=2) + NL)
actual79 = sum(actual79_by.values())
script79 = sum(script79_by.values())

all_five_200_78900 = all(g.get("code") == 200 and g.get("ok") for g in jp["gets"]) and not jp.get("still_404")
all_five_200_79000 = all(g.get("code") == 200 and g.get("ok") for g in jp79["gets"]) and not jp79.get("still_404")
jp_distinct = ", ".join(f"{room} {post[room]['distinct']}/100" for room in ROOMS)
jp79_distinct = ", ".join(f"{room} {post79[room]['distinct']}/100" for room in ROOMS)

mismatch = [room for room in ROOMS if script_by.get(room, 0) != actual_by[room]]
mismatch_s = ", ".join(f"{r} script {script_by[r]} vs actual {actual_by[r]}" for r in mismatch)
mismatch_suffix = (" (" + mismatch_s + ").") if mismatch_s else "."
mismatch79 = [room for room in ROOMS if script79_by.get(room, 0) != actual79_by[room]]
mismatch79_s = ", ".join(f"{r} script {script79_by[r]} vs actual {actual79_by[r]}" for r in mismatch79)
mismatch79_suffix = (" (" + mismatch79_s + ").") if mismatch79_s else "."

INSERTED_FIRST = 5406
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
JUST_ACTUAL = actual_78900 + actual79
JUST_SCRIPT = script_78900 + script79
INSERTED_TOTAL = INSERTED_WINDOW + JUST_ACTUAL

FILL_1846 = {room: gaps["freeze_1846"][room]["fill"] for room in ROOMS}
FILL_1916 = {room: gaps["freeze_1916"][room]["fill"] for room in ROOMS}
FILL_1645 = {"W46N8": "169/169", "W47N8": "169/169", "W45N8": "169/169", "W45N7": "100/169", "W47N7": "169/169"}
FILL_1709 = {"W46N8": "249/249", "W47N8": "149/249", "W45N8": "249/249", "W45N7": "249/249", "W47N7": "249/249"}
FILL_1743 = {"W46N8": "199/299", "W47N8": "299/299", "W45N8": "299/299", "W45N7": "299/299", "W47N7": "299/299"}

payload = {
    "at": AT,
    "ok_quiet": True,
    "game_time_first": 84378977,
    "published_bases": "84378200..84378800",
    "reconstructed": [84378201, 84378900],
    "ticks": 700,
    "creep_rows": 21812,
    "missing_chunks": 0,
    "already_in_db": 16406,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_script": JUST_SCRIPT,
    "inserted_just_actual": JUST_ACTUAL,
    "inserted_just_78900_script": script_78900,
    "inserted_just_78900_actual": actual_78900,
    "inserted_just_79000_script": script79,
    "inserted_just_79000_actual": actual79,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "first_pass_by": "reused from concurrent 1h patrol _patrol_2026-11-20_1923 history_backfill finished 19:25:23 (game.time=84378977, published_bases 84378200..84378800, reconstructed 84378201..84378900 missing_chunks=0 inserted=5406 already_in_db=16406)",
    "tick_s_printed": 4.244,
    "tick_s_first": 4.244,
    "tick_s_in_use": 4.244,
    "tick_s_in_use_name": "patrol_first",
    "ts_realigned_first": 0,
    "corrective": 0,
    "coverage_official_recovered": cov["official_recovered"],
    "coverage_expected": cov["expected"],
    "empty_no_creep": cov["empty_no_creep"],
    "official_404": cov["official_404_missing"],
    "per_room_new_first": {"W46N8": 1259, "W47N8": 1839, "W45N8": 621, "W45N7": 612, "W47N7": 1075},
    "per_room_new_window": {"W46N8": 1259, "W47N8": 1839, "W45N8": 621, "W45N7": 612, "W47N7": 1075},
    "in_window_404_after_retry2": [],
    "first_pass_404_recovered_before_confirm": [],
    "just_published_base": 84378900,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": all_five_200_78900,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp.get("still_404") or ["W45N8@84378900"],
    "just_published_79000_base": 84379000,
    "just_published_79000_at": jp79.get("at"),
    "just_published_79000_gt": jp79.get("game_time"),
    "just_published_79000_all_five_200": all_five_200_79000,
    "just_published_79000_script_by_room": script79_by,
    "just_published_79000_actual_by_room": actual79_by,
    "just_published_79000_still_404": jp79.get("still_404") or [],
    "just_published_79000_post": post79,
    "new_box_freeze": None,
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": {
        "from": "2026-11-20 18:46:28",
        "to": "2026-11-20 18:58:51",
        "sec": 742,
        "why": "box frozen ~742s since 2026-11-20 18:46:28 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "18:58:54 then 18:59:10 after SSL EOF",
        "stats": "84378421..84378619",
        "span": 199,
        "last_stats": "84378420 at 18:46:00",
        "next_stats": "84378620 at 18:59:51",
        "wall_s": 831,
        "official_fill": FILL_1846,
        "filled_by": "Prior 19:00 half-hour first pass through 84378600 plus just-published 84378600. W46N8/W47N8/W45N8/W47N7 199/199. W45N7 171/199 missing 84378423..84378450 (28t) is official empty-no-creep (GET 200 on W45N7@84378400), not a 404.",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1900",
        "note": "Still in this window start 84378201. Left to concurrent 1h patrol _patrol_2026-11-20_1923 to tell (patrol was already running during this half-hour).",
    },
    "already_recorded_untold_new_freeze_1916": {
        "from": "2026-11-20 19:16:42",
        "to": "2026-11-20 19:23:50",
        "sec": 424,
        "why": "box frozen ~424s since 2026-11-20 19:16:42 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "19:23:53",
        "listener_pid": 1452906,
        "listener_started": "19:24:03",
        "stats": "84378861..84378969",
        "span": 109,
        "last_stats": "84378860 at 19:16:32",
        "next_stats": "84378970 at 19:24:08",
        "official_fill": FILL_1916,
        "filled_by": "Concurrent patrol first pass through 84378900 plus this run's recovered just-published W47N7@84378900 and already-written W46N8/W47N8/W45N7@84378900. W46N8/W47N8/W45N7/W47N7 109/109. W45N8 40/109 missing 84378901..84378969 (69t) because official 404 W45N8@84378900 remains unfilled (not empty-no-creep).",
        "told": False,
        "first_recorded_by": "concurrent 1h patrol _patrol_2026-11-20_1923 (box_pauses 19:23; official_retries 19:27 already saw W45N8@84378900 404 and gap fill 84378861..84378969). Also recorded here for the next 1h patrol if the concurrent one has not yet told it.",
        "note": "This run did not itself restart the listener (run_listener.sh auto-restarted after the freeze). Left to the concurrent 1h patrol to tell.",
    },
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [],
    "already_recorded_untold_in_window_404": [],
    "already_recorded_untold_just_published_404": [{
        "chunk": "W45N8@84378900",
        "hole": "84378901..84379000",
        "live_ticks_present": "none (0t)",
        "still_404_after": "this run just-published GET 19:34:06 gt=84379113, retry 19:35:54 gt=84379141, and retry2 19:37:01 gt=84379158 (also still 404 after concurrent patrol just-published GET 19:27:35 gt=84379016). Sits after first-pass TMAX=84378900 so it is not an in-window first-pass 404.",
        "db": w45n8_hole,
        "told": False,
        "told_by": None,
        "first_recorded_by": "concurrent 1h patrol _patrol_2026-11-20_1923 official just-published 19:27:35",
        "note": "Left to concurrent 1h patrol to tell. This half-hour retried and it remains unfilled.",
    }],
    "already_told_in_window_404": [],
    "aged_out_already_told_404_not_retried": [
        "W47N7@84378000", "W46N8@84377600", "W47N8@84377100", "W45N7@84376800",
        "W46N8@84376100", "W45N8@84375300", "W45N7@84373700", "W47N8@84373800",
        "W45N7@84373300", "W47N7@84373200", "W46N8@84371600",
    ],
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 17:43:34", "to": "2026-11-20 18:02:53", "sec": 1158,
        "stats": "84377521..84377819", "span": 299,
        "official_fill": FILL_1743,
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1819 ~18:31",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1800",
        "aged_out_of_window_start": 84378201,
        "note": "W46N8 still missing 84377601..84377700 (100t) because already-told official 404 W46N8@84377600 remains unfilled. Aged out of this window start 84378201 and was not retried.",
    },
    "also_prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 17:09:11", "to": "2026-11-20 17:26:01", "sec": 1005,
        "stats": "84377041..84377289", "span": 249, "official_fill": FILL_1709,
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1725 ~17:40",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1730",
        "aged_out_of_window_start": 84378201,
        "note": "W47N8 still missing 84377101..84377200 (100t) because already-told official 404 W47N8@84377100 remains unfilled.",
    },
    "also_aged_out_already_told_box_freeze_1645": {
        "from": "2026-11-20 16:45:36", "to": "2026-11-20 16:56:32", "sec": 647,
        "stats": "84376701..84376869", "span": 169, "official_fill": FILL_1645,
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1725 ~17:40",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1700",
        "aged_out_of_window_start": 84378201,
        "note": "W45N7 still missing 84376801..84376869 (69t) because already-told official 404 W45N7@84376800 remains unfilled.",
    },
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-20 16:17:08", "to": "2026-11-20 16:22:02", "sec": 289,
        "stats": "84376291..84376369", "span": 79, "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "1h patrol _patrol_2026-11-20_1624",
        "aged_out_of_window_start": 84378201,
    },
    "also_aged_out_already_told_box_freeze_1544": {
        "from": "2026-11-20 15:44:21", "to": "2026-11-20 16:03:39", "sec": 1152,
        "stats": "84375811..84376109", "span": 299, "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1600",
        "aged_out_of_window_start": 84378201,
    },
    "also_aged_out_already_told_box_freeze_1515": {
        "from": "2026-11-20 15:15:12", "to": "2026-11-20 15:26:38", "sec": 686,
        "stats": "84375391..84375569", "span": 179, "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1526 ~15:29",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1530",
        "aged_out_of_window_start": 84378201,
    },
    "listener": {
        "single_slot": True, "roomSlot": live.get("roomSlot"), "rot": rot,
        "pid": 1452906, "started": "19:24:03", "parent": 4035476, "yield": False,
        "restarted_this_run": False,
        "auto_restart": "19:23:53 after box freeze 19:16:42-19:23:50; listener.py started 19:24:03",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": "_patrol_2026-11-20_1923 (started ~19:23, history_backfill finished 19:25:23, official retries/just-published ~19:27; still running during this half-hour; first pass reused, this run did not write the patrol folder)",
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + NL)
shutil.copy2(DIR / "history_backfill.json", STATE / "history_backfill.json")

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + NL
wrap = (
    f"---- wrap {AT} ----" + NL
    + "confirm skipped (no in-window first-pass 404s; first pass missing_chunks=0). Leftover already-told official 404 W47N7@84378000 (hole 84378001..84378100) aged out of window start 84378201 and was not retried, along with already-told W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600." + NL
    + "tick_s_first=4.244 printed=4.244 in_use=4.244 (patrol_first) ts_realigned_first=0 corrective=0" + NL
    + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
    + f"just-published 84378900 at {jp.get('at')} game.time={jp.get('game_time')} all_five_200={all_five_200_78900} actual_inserted={actual_78900} ticks 84378901..84379000 ({jp_distinct}); script inserted={script_78900}{mismatch_suffix} Concurrent patrol had already written W46N8/W47N8/W45N7; this run recovered W47N7@84378900. W45N8@84378900 still 404 after this run GET 19:34:06 gt=84379113, retry 19:35:54 gt=84379141, retry2 19:37:01 gt=84379158 (also 404 at patrol 19:27:35 gt=84379016); first recorded by the concurrent 1h patrol, told=false, left to that patrol." + NL
    + f"just-published 84379000 at {jp79.get('at')} game.time={jp79.get('game_time')} all_five_200={all_five_200_79000} actual_inserted={actual79} ticks 84379001..84379100 ({jp79_distinct}); script inserted={script79}{mismatch79_suffix}" + NL
    + f"inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL} (first 5406 reused from patrol + just 84378900 actual {actual_78900} + just 84379000 actual {actual79})" + NL
    + "ok_quiet=True" + NL
)
(DIR / "history_backfill_now.txt").write_text(first + NL + wrap)
(DIR / "history_backfill.txt").write_text(first)
shutil.copy2(DIR / "history_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

ua = cov["unique_after"]
empty_ranges = cov["coverage"]["W45N7"]["official_empty_no_creep_ranges"]
verify_lines = [
    f"{AT} verify",
    "first pass reused from concurrent 1h patrol _patrol_2026-11-20_1923 finished 19:25:23 game.time=84378977 published_bases=84378200..84378800 reconstructed 84378201..84378900 (700) creep_rows=21812 missing_chunks=0",
    f"already_in_db=16406 inserted_first=5406 confirm=0 retry2=0 just_78900_script={script_78900} just_78900_actual={actual_78900} just_79000_script={script79} just_79000_actual={actual79} just_script={JUST_SCRIPT} just_actual={JUST_ACTUAL} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}",
    "per_room first W46N8:700t/1259new W47N8:700t/1839new W45N8:700t/621new W45N7:700t/612new W47N7:700t/1075new. First pass reused from concurrent 1h patrol; this run did not re-GET the 35 official chunks. In-window official 404 after confirm: none (missing_chunks=0; leftover W47N7@84378000 aged out).",
    "tick_s_first=4.244 printed=4.244 in_use=4.244 (patrol_first) ts_realigned_first=0 corrective=0",
    f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']} unique_room_ticks={ua['distinct_room_ticks']} unique_creep_tick_rows={ua['unique_creep_tick_rows']} (no dups).",
    f"Official 404 in this first-pass window: none. Official empty-no-creep in-window: W45N7 {cov['empty_no_creep']}t {empty_ranges} (GET 200, not a 404). W46N8/W47N8/W45N8/W47N7 700/700; W45N7 670/700 (30 official empty-no-creep).",
    f"just-published 84378900 at {jp.get('at')} game.time={jp.get('game_time')} all_five_200={all_five_200_78900} actual_inserted={actual_78900} ticks 84378901..84379000 ({jp_distinct}); script inserted={script_78900}{mismatch_suffix} W47N7@84378900 recovered this run (patrol had 404). W45N8@84378900 still 404 after this run GET 19:34:06/19:35:54/19:37:01 and patrol 19:27:35; hole 84378901..84379000, no live ticks; first recorded by concurrent 1h patrol, told=false, left to that patrol.",
    f"just-published 84379000 at {jp79.get('at')} game.time={jp79.get('game_time')} all_five_200={all_five_200_79000} actual_inserted={actual79} ticks 84379001..84379100 ({jp79_distinct}); script inserted={script79}{mismatch79_suffix}",
    "Already-recorded untold box freeze 18:46:28-18:58:51 (742s) STATS 84378421..84378619 (199t) still in window start 84378201; official-filled W46N8/W47N8/W45N8/W47N7 199/199, W45N7 171/199 (28t official empty-no-creep 84378423..84378450). first recorded by 19:00 half-hour, told=false, left to concurrent 1h patrol.",
    "Already-recorded untold box freeze 19:16:42-19:23:50 (424s; box_pauses.jsonl); listener auto-restart 19:23:53, pid 1452906 started 19:24:03. STATS 84378861..84378969 (109t) last STATS 84378860 at 19:16:32 to next STATS 84378970 at 19:24:08. Official-filled W46N8 109/109, W47N8 109/109, W45N8 40/109, W45N7 109/109, W47N7 109/109. W45N8 missing 84378901..84378969 (69t) because official 404 W45N8@84378900 still unfilled. first recorded by concurrent 1h patrol, told=false, left to that patrol. This run did not itself restart the listener.",
    "Prior box freeze 17:43:34-18:02:53 STATS 84377521..84377819 aged out of window start 84378201 (already told by the 18:31 1h patrol). W46N8 missing 84377601..84377700 (100t) because already-told official 404 W46N8@84377600 still unfilled; aged out and not retried.",
    "Prior box freeze 17:09:11-17:26:01 STATS 84377041..84377289 aged out of window start 84378201 (already told by the 17:40 1h patrol). W47N8 missing 84377101..84377200 (100t) because already-told official 404 W47N8@84377100 still unfilled.",
    "Prior box freeze 16:45:36-16:56:32 STATS 84376701..84376869 aged out of window start 84378201 (already told by the 17:40 1h patrol). W45N7 missing 84376801..84376869 (69t) because already-told official 404 W45N7@84376800 still unfilled.",
    "Prior box freeze 16:17:08-16:22:02 STATS 84376291..84376369 aged out of window start 84378201 (already told by the 16:31 1h patrol).",
    "Prior box freeze 15:44:21-16:03:39 STATS 84375811..84376109 aged out of window start 84378201 (already told by the 16:31 1h patrol).",
    "Prior box freeze 15:15:12-15:26:38 STATS 84375391..84375569 aged out of window start 84378201 (already told by the 15:29 1h patrol).",
    f"listener single_slot=True roomSlot={live.get('roomSlot')} pid=1452906 started 19:24:03 after auto-restart 19:23:53; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips['creep_cpu']} path_tip={tips['path_arrivals']} room_stats_tip={tips['room_stats']}.",
]
(DIR / "verify.txt").write_text(NL.join(verify_lines) + NL)
shutil.copy2(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")

retry_lines = [
    "confirm skipped (no in-window first-pass 404).",
    "W47N7@84378900 recovered 19:34:10 gt=84379113 inserted_script=600 actual=483.",
    "W45N8@84378900 still 404 after 19:34:06 gt=84379113, 19:35:54 gt=84379141, 19:37:01 gt=84379158.",
    f"just-published 84379000 all five 200 actual_inserted={actual79} script={script79}.",
]
(DIR / "backfill_retry2.txt").write_text(NL.join(retry_lines) + NL)
shutil.copy2(DIR / "backfill_retry2.txt", STATE / "_halfhour_backfill_retry2_1930.txt")

(DIR / "wrapup_run.txt").write_text(f"wrapup wrote {AT} ok_quiet=True inserted_total={INSERTED_TOTAL}" + NL)
(DIR / "wrapup_write.py").write_text(f"# wrapup executed inline for 1930; status written {AT}" + NL)

print("AT", AT)
print("JUST_ACTUAL", JUST_ACTUAL, "78900", actual_78900, "79000", actual79)
print("JUST_SCRIPT", JUST_SCRIPT, "78900", script_78900, "79000", script79)
print("INSERTED_TOTAL", INSERTED_TOTAL)
print("jp79 post", json.dumps(post79))
print("actual79_by", actual79_by)
print("tips", tips)
print("w45n8_hole", w45n8_hole)
print("mismatch", mismatch_suffix, "|", mismatch79_suffix)
print("ok")
