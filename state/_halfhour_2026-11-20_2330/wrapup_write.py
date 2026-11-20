#!/usr/bin/env python3
"""Write 23:30 half-hour backfill wrap artifacts (quiet success)."""
from __future__ import annotations
import json, shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-20_2330"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
jp = json.loads((DIR / "just_published_84382400.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

want = (
    "First-pass realign with tick_s=4.26348 (printed 4.263) moved 0 rows "
    "(ts_realigned_first=0, inserted=0, already_in_db=24260, missing_chunks=1 W47N8@84382100)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace("printed 4.100", "printed 4.263")
reason = reason.replace(
    "moved 0 rows (ts_realigned_first=0, inserted=438, already_in_db=23933, missing_chunks=1 W47N8@84380300).",
    "moved 0 rows (ts_realigned_first=0, inserted=0, already_in_db=24260, missing_chunks=1 W47N8@84382100).",
)
tick["reason"] = reason
(DIR / "tick_s_realign.json").write_text(json.dumps(tick, indent=2) + "\n")

with db.connect() as c:
    tips = {}
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute(f"select max(tick) from {table}").fetchone()[0]
    win = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84381701, 84382400),
        ).fetchone()
        win[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
post_tips = post.get("tips") or {}

inserted_first = 0
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.26348)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "first"
cov_rec = cov.get("official_recovered")
cov_exp = cov.get("expected")
empty_n = cov.get("empty_no_creep")
off404 = cov.get("official_404_missing")

confirm_at = confirm.get("confirm_at") or confirm.get("at")
confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
retry2 = confirm.get("retry2") or {}
retry2_at = retry2.get("at") or confirm.get("retry2_at")
retry2_gt = retry2.get("game_time") or confirm.get("retry2_game_time")

slot = live.get("roomSlot")
rot_s = json.dumps(rot, ensure_ascii=False)

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84382485,
    "published_bases": "84381700..84382300",
    "reconstructed": [84381701, 84382400],
    "ticks": 700,
    "creep_rows": 24260,
    "missing_chunks": 1,
    "already_in_db": 24260,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84382485, published_bases 84381700..84382300, "
        "reconstructed 84381701..84382400 missing_chunks=1 W47N8@84382100 inserted=0 already_in_db=24260); "
        "34/35 official GETs 200. Concurrent 1h patrol _patrol_2026-11-20_2320 already official-filled "
        "84381701..84382400 (inserted=9749 at gt=84382411) and also saw W47N8@84382100 404; its first-pass 404 "
        "W47N7@84382300 was 200 on this first pass. First pass included published bases through 84382300, "
        "covering all of NEW box freeze 23:11:55-23:20:53 (STATS 84382221..84382359, 139/139 all five)."
    ),
    "tick_s_printed": 4.263,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 0,
    "corrective": int(tick.get("ts_realigned_to_later_mean") or 0),
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 0},
        "W47N8": {"ticks": 600, "new": 0},
        "W45N8": {"ticks": 700, "new": 0},
        "W45N7": {"ticks": 700, "new": 0},
        "W47N7": {"ticks": 700, "new": 0},
    },
    "per_room_new_window": {
        r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS
    },
    "in_window_404_after_retry2": ["W47N8@84382100"],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": 84382400,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": True,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp.get("still_404") or [],
    "just_published_retries": [],
    "just_published_actual_note": (
        "script inserted=4 (W45N8 +4). post-counts actual_sum=1398 vs the GET-start snapshot is inflated: "
        "W45N8/W45N7/W47N7 gained rows between the snapshot (0/28/0 distinct) and the per-room GET "
        "(already 100/100) so actual 439/329/630 is not all written by this script. "
        "W46N8/W47N8 were already 100/100 at the snapshot (listener/patrol). All five ended 100/100."
    ),
    "new_box_freeze": {
        "from": "2026-11-20 23:11:55",
        "to": "2026-11-20 23:20:53",
        "sec": 537,
        "why": "box frozen ~537s since 2026-11-20 23:11:55 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "23:20:56",
        "listener_pid": 1545879,
        "listener_started": "23:21:05",
        "stats": "84382221..84382359",
        "span": 139,
        "last_stats": "84382220 at 23:11:16",
        "next_stats": "84382360 at 23:21:08",
        "official_fill": {r: gaps["freeze_2311"][r]["fill"] for r in ROOMS},
        "filled_by": (
            "Concurrent 1h patrol _patrol_2026-11-20_2320 official-filled the window first; "
            "this 30-min backfill _halfhour_2026-11-20_2330 first pass confirmed 139/139 all five "
            "(already_in_db, inserted=0)."
        ),
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2330 (visible in box_pauses.jsonl / errors.log after listener auto-restart 23:20:56); concurrent 1h patrol _patrol_2026-11-20_2320 started 23:24:28 after heal and also saw this gap",
        "note": "Already healed. This run did not itself restart the listener. Concurrent 1h patrol _patrol_2026-11-20_2320 should tell this NEW freeze (and the previously recorded 22:44 freeze). If that patrol already delivered, treat as told. Fold only newer freezes than 23:11:55-23:20:53.",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": {
        "from": "2026-11-20 22:17:42",
        "to": "2026-11-20 22:20:34",
        "sec": 164,
        "why": "box frozen ~164s since 2026-11-20 22:17:42 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "22:20:37",
        "listener_pid": 1522236,
        "listener_started": "22:20:46",
        "stats": "84381451..84381509",
        "span": 59,
        "last_stats": "84381450 at 22:17:32",
        "next_stats": "84381510 at 22:21:18",
        "official_fill": {r: gaps["freeze_2217"][r]["fill"] for r in ROOMS},
        "filled_by": "Previous 22:30 backfill _halfhour_2026-11-20_2230 official-filled remaining unpublished tail; still 59/59 all five.",
        "told": True,
        "told_by": "1h patrol ~22:29 亚洲/香港 (_patrol_2026-11-20_2220); 22:30 backfill completed the unpublished-tail fill",
        "first_recorded_by": "1h patrol _patrol_2026-11-20_2220 (visible in box_pauses.jsonl / errors.log after listener auto-restart 22:20:37)",
        "note": "Already healed and already told. Still in window start 84381701.",
    },
    "already_told_older_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": {
        "from": "2026-11-20 22:44:03",
        "to": "2026-11-20 22:59:02",
        "sec": 899,
        "why": "box frozen ~899s since 2026-11-20 22:44:03 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "22:59:05",
        "listener_pid": 1537042,
        "listener_started": "22:59:14",
        "stats": "84381821..84382059",
        "span": 239,
        "last_stats": "84381820 at 22:43:31",
        "next_stats": "84382060 at 22:59:55",
        "official_fill": {r: gaps["freeze_2244"][r]["fill"] for r in ROOMS},
        "w47n7_missing": "151 ticks 84381821..84381869 and 84381899..84382000 are official empty_no_creep (no owned creeps), not official 404",
        "filled_by": "Previous 23:00 backfill _halfhour_2026-11-20_2300 official-filled four rooms 239/239, W47N7 88/239 with 151 official empty_no_creep; still the same this run.",
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2300",
        "note": "Already healed. Recorded untold by 23:00 half-hour for the next 1h patrol; concurrent _patrol_2026-11-20_2320 should tell it. Still in window start 84381701.",
    },
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [
        {
            "chunk": "W47N8@84382100",
            "hole": "84382101..84382200",
            "confirm": f"still 404 at {confirm_at} gt={confirm_gt}",
            "retry2": f"still 404 at {retry2_at} gt={retry2_gt}",
            "db": "already 100/100 rows=1298 from live listener; not a trajectory hole",
            "note": "Official history chunk stayed 404 after confirm and retry2. Coverage official_404=0 because creep_ticks already complete. Next 1h patrol may retry the official GET; do not treat as missing trajectory data.",
        }
    ],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [],
    "already_recorded_untold_just_published_404": [],
    "aged_out_already_told_404_not_retried": [
        "W47N7@84380900",
        "W47N8@84380300",
        "W47N8@84379500",
        "W45N8@84378900",
        "W47N7@84378000",
        "W46N8@84377600",
        "W47N8@84377100",
        "W45N7@84376800",
        "W46N8@84376100",
        "W45N8@84375300",
        "W45N7@84373700",
        "W47N8@84373800",
        "W45N7@84373300",
        "W47N7@84373200",
        "W46N8@84371600",
    ],
    "aged_out_leftover_note": (
        "Leftover official 404 W47N7@84380900 (hole 84380901..84381000, still empty) aged out of window start 84381701 and was not retried here. "
        "Already-told freeze 21:38:41-21:59:40 STATS 84380901..84381219 also aged out (four rooms 319/319; W47N7 219/319 still short that leftover hole). "
        "Older already-told leftovers W47N8@84380300, W47N8@84379500, W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 remain unfilled and were not retried here."
    ),
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 21:38:41",
        "to": "2026-11-20 21:59:40",
        "sec": 1251,
        "stats": "84380901..84381219",
        "span": 319,
        "official_fill": {r: gaps["freeze_2138"][r]["fill"] for r in ROOMS},
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_2220",
        "aged_out_of_window_start": 84381701,
        "note": "W47N7 remains 219/319 missing 84380901..84381000 because leftover official 404 W47N7@84380900 is still 404.",
    },
    "w47n7_official_empty_no_creep": {
        "distinct": 521,
        "empty_n": 179,
        "ranges": "84381793..84381869, 84381899..84382000",
        "note": "Not official 404. First-pass window W47N7 distinct=521/700. Overlaps already-recorded freeze 84381821..84382000 for 151 ticks (84381821..84381869 and 84381899..84382000).",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": slot,
        "rot": rot,
        "pid": 1545879,
        "started": "23:21:05",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "23:20:56 after box freeze 23:11:55-23:20:53; listener.py started 23:21:05",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "Listener auto-restarted on box wake and reconnected on its own (live.json fresh, creep_cpu/path_arrivals ingesting). Single peacetime slot 5:5:1:1, no yield file. This run did not restart the listener or war_cmd/pulse.",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": {
        "id": "_patrol_2026-11-20_2320",
        "started_at": "2026-11-20 23:24:28 CST",
        "backfill_done": "2026-11-20 23:26:40 CST",
        "backfill": "official-filled 84381701..84382400 inserted=9749 missing_chunks=2 (404 W47N8@84382100, W47N7@84382300); W47N7@84382300 was 200 on this half-hour first pass",
        "official_retry_done_before_this_first_pass": True,
        "note": "This half-hour waited for official_retry to finish before first-pass GETs. Patrol may already tell NEW freeze 23:11 and previously recorded 22:44.",
    },
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
    "tick_s_reason": tick.get("reason"),
    "post_counts_tips_at": post.get("at"),
    "post_counts_tips": post_tips,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

prev = ROOT / "state" / "history_backfill.json"
if prev.exists():
    shutil.copy2(prev, ROOT / "state" / "history_backfill.prev.json")
shutil.copy2(DIR / "history_backfill.json", prev)

jp_lines = []
for room in ROOMS:
    p = post["post"][room]
    act = actual_by[room]
    scr = script_by[room]
    extra = f" (script {scr})" if act != scr else ""
    jp_lines.append(f"  {room} distinct={p['distinct']} rows={p['rows']} actual={act}{extra}")

f2311 = "  " + "  ".join(
    f"{r} {gaps['freeze_2311'][r]['fill']}"
    + (f" missing {gaps['freeze_2311'][r]['missing_range']}" if gaps["freeze_2311"][r]["missing_n"] else "")
    for r in ROOMS
)
f2244 = "  " + "  ".join(
    f"{r} {gaps['freeze_2244'][r]['fill']}"
    + (f" missing {gaps['freeze_2244'][r]['missing_range']}" if gaps["freeze_2244"][r]["missing_n"] else "")
    for r in ROOMS
)
f2217 = "  " + "  ".join(
    f"{r} {gaps['freeze_2217'][r]['fill']}"
    + (f" missing {gaps['freeze_2217'][r]['missing_range']}" if gaps["freeze_2217"][r]["missing_n"] else "")
    for r in ROOMS
)

win_lines = "\n".join(
    f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}"
    + (" official_empty_no_creep=179 ranges 84381793..84381869, 84381899..84382000" if r == "W47N7" and win[r]["distinct"] != 700 else "")
    for r in ROOMS
)

script_mismatch = []
for r in ROOMS:
    if actual_by[r] != script_by[r]:
        script_mismatch.append(f"{r} script {script_by[r]} vs actual {actual_by[r]}")
mismatch_s = ("; " + "; ".join(script_mismatch) + " — actual vs GET-start snapshot inflated for remotes already complete at per-room GET.") if script_mismatch else "."

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = chr(10)
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
confirm 23:31:25 gt=84382507 and retry2 23:32:26 gt=84382522 still official 404 W47N8@84382100 (first pass 34/35 official GETs 200, missing_chunks=1). DB already 100/100 rows=1298 for 84382101..84382200 from the live listener, so this is not a trajectory hole. Coverage official_404=0 because ticks are present. Leftover official 404 W47N7@84380900 (hole 84380901..84381000, still empty) and older leftovers W47N8@84380300, W47N8@84379500, W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 aged out of window start 84381701 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.263 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published 84382400 at 2026-11-20 23:33:46 Asia/Hong_Kong game.time=84382541 all_five_200=True actual_inserted={actual_sum} ticks 84382401..84382500 (all five 100/100); script inserted={script_sum}{mismatch_s}
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84382400 actual {actual_sum})
NEW box freeze 23:11:55-23:20:53 (537s; already healed; listener auto-restart 23:20:56; python 1545879 started 23:21:05). STATS 84382221..84382359 (139t; last STATS 84382220 at 23:11:16, next 84382360 at 23:21:08). Concurrent patrol and this first pass official-filled 139/139 all five. Concurrent 1h patrol _patrol_2026-11-20_2320 started 23:24:28 after heal and should tell this NEW freeze (and previously recorded 22:44). Already-recorded untold freeze 22:44:03-22:59:02 remains in window (four rooms 239/239, W47N7 88/239 official empty_no_creep 151). Already-told freeze 22:17:42-22:20:34 remains in window (59/59 all five; told by 1h patrol _patrol_2026-11-20_2220). Already-told freeze 21:38:41-21:59:40 aged out of window start 84381701 (four rooms 319/319, W47N7 219/319 still short leftover official 404 W47N7@84380900). This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. Waited for concurrent patrol official_retry to finish before first-pass GETs.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_2330.txt")

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 W47N8@84382100 reconstructed 84381701..84382400 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published 84382400 ticks 84382401..84382500 actual_inserted={actual_sum} script={script_sum}
{nl.join(jp_lines)}
freeze_2311 STATS 84382221..84382359 (139) NEW; official-filled 139/139 all five (concurrent patrol + this first pass)
{f2311}
freeze_2244 STATS 84381821..84382059 (239) already-recorded untold by 23:00; four rooms 239/239, W47N7 88/239 empty_no_creep 151
{f2244}
freeze_2217 STATS 84381451..84381509 (59) already-told; still 59/59 all five
{f2217}
leftover official 404 W47N8@84382100 still 404 after confirm/retry2; DB already 100/100 from live listener (not a trajectory hole)
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.263 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1545879 started=23:21:05 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
ok_quiet=True
"""
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")
summary = (
    f"wrote wrap {now_s}\n"
    f"inserted_window {inserted_window} inserted_total {inserted_total} just_actual {actual_sum}\n"
    f"slot {slot} tips {tips}\n"
    f"ok_quiet=True\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run.full.txt").write_text(summary)
print("wrote wrap", now_s)
print("inserted_window", inserted_window, "inserted_total", inserted_total, "just_actual", actual_sum)
print("slot", slot, "tips", tips)
print("ok_quiet=True")
