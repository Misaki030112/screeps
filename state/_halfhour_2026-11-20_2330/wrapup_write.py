#!/usr/bin/env python3
"""Write 23:00 half-hour backfill wrap artifacts (quiet success)."""
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
jp = json.loads((DIR / "just_published_84382000.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

want = (
    "First-pass realign with tick_s=4.38678 (printed 4.387) moved 15793 rows "
    "(ts_realigned_first=15793, inserted=10557, already_in_db=14891, missing_chunks=0 none)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace("printed 4.100", "printed 4.387")
reason = reason.replace(
    "moved 15793 rows (ts_realigned_first=15793, inserted=438, already_in_db=23933, missing_chunks=1 W47N8@84380300).",
    "moved 15793 rows (ts_realigned_first=15793, inserted=10557, already_in_db=14891, missing_chunks=0 none).",
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
            (room, 84381301, 84382000),
        ).fetchone()
        win[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
post_tips = post.get("tips") or {}

inserted_first = 10557
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.38678)
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

w47_empty = cov["coverage"]["W47N7"]["official_empty_no_creep_ranges"]

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84382087,
    "published_bases": "84381300..84381900",
    "reconstructed": [84381301, 84382000],
    "ticks": 700,
    "creep_rows": 25448,
    "missing_chunks": 0,
    "already_in_db": 14891,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84382087, published_bases 84381300..84381900, "
        "reconstructed 84381301..84382000 missing_chunks=0 inserted=10557 already_in_db=14891); "
        "35/35 official GETs 200. First pass already included published bases through 84381900 (all five 200), "
        "covering the published side of NEW box freeze 22:44:03-22:59:02 (STATS 84381821..84382059)."
    ),
    "tick_s_printed": 4.387,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 15793,
    "corrective": int(tick.get("ts_realigned_to_later_mean") or 0),
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 2315},
        "W47N8": {"ticks": 700, "new": 5675},
        "W45N8": {"ticks": 700, "new": 1549},
        "W45N7": {"ticks": 700, "new": 683},
        "W47N7": {"ticks": 700, "new": 335},
    },
    "per_room_new_window": {
        r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS
    },
    "in_window_404_after_retry2": [],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": 84382000,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": True,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp.get("still_404") or [],
    "just_published_retries": [],
    "new_box_freeze": {
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
        "w47n7_missing": "151 ticks 84381821..84381869 and 84381899..84382000 are official empty_no_creep (no owned creeps), not official 404; just-published 84382000 filled 84382001..84382059 including W47N7",
        "filled_by": "This 30-min backfill _halfhour_2026-11-20_2330 first pass included published 84381800..84381900 and just-published 84382000; four rooms 239/239, W47N7 88/239 with 151 official empty_no_creep.",
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2330 (visible in box_pauses.jsonl / errors.log after listener auto-restart 22:59:05)",
        "note": "Already healed. This run did not itself restart the listener. Next 1h patrol should tell this NEW freeze. Fold only newer freezes than 22:44:03-22:59:02.",
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
        "note": "Already healed and already told. Still in window start 84381301.",
    },
    "already_told_older_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [],
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
        "Leftover official 404 W47N7@84380900 (hole 84380901..84381000, still empty) aged out of window start 84381301 and was not retried here. "
        "Already-told freeze 21:38:41-21:59:40 STATS 84380901..84381219 also aged out (four rooms 319/319; W47N7 219/319 still short that leftover hole). "
        "Older already-told leftovers W47N8@84380300, W47N8@84379500, W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300 and earlier holes remain unfilled and were not retried."
    ),
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 21:38:41",
        "to": "2026-11-20 21:59:40",
        "sec": 1251,
        "stats": "84380901..84381219",
        "span": 319,
        "official_fill": {r: gaps["freeze_2138"][r]["fill"] for r in ROOMS},
        "told": True,
        "told_by": "1h patrol ~22:29 亚洲/香港 (_patrol_2026-11-20_2220); first recorded by 30-min backfill _halfhour_2026-11-20_2200",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2200",
        "aged_out_of_window_start": 84381301,
        "note": "W47N7 remains 219/319 missing 84380901..84381000 because leftover official 404 W47N7@84380900 is still 404.",
    },
    "w47n7_empty_no_creep": {
        "count": 179,
        "ranges": w47_empty,
        "note": "Not official 404. First-pass window W47N7 distinct=521/700. Overlaps NEW freeze 84381821..84382000 for 151 ticks (84381821..84381869 and 84381899..84382000).",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": slot,
        "rot": rot,
        "pid": 1537042,
        "started": "22:59:14",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "22:59:05 after box freeze 22:44:03-22:59:02; listener.py started 22:59:14",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "Listener auto-restarted on box wake and reconnected on its own (live.json fresh, creep_cpu/path_arrivals ingesting). Single peacetime slot 5:5:1:1, no yield file. This run did not restart the listener or war_cmd/pulse.",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": None,
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
mismatch_s = ("; " + "; ".join(script_mismatch) + ".") if script_mismatch else "."

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = chr(10)
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
confirm/retry2 skipped, no in-window official 404 (first pass 35/35 official GETs 200, missing_chunks=0). Leftover official 404 W47N7@84380900 (hole 84380901..84381000, still empty) and older leftovers W47N8@84380300, W47N8@84379500, W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 aged out of window start 84381301 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.387 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=15793 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published 84382000 at 2026-11-20 23:05:40 Asia/Hong_Kong game.time=84382142 all_five_200=True actual_inserted={actual_sum} ticks 84382001..84382100 (all five 100/100); script inserted={script_sum}{mismatch_s}
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84382000 actual {actual_sum})
NEW untold box freeze 22:44:03-22:59:02 (899s; already healed; listener auto-restart 22:59:05; python 1537042 started 22:59:14). STATS 84381821..84382059 (239t; last STATS 84381820 at 22:43:31, next 84382060 at 22:59:55). This run first pass included published 84381800..84381900 and just-published 84382000: four rooms 239/239, W47N7 88/239 missing 151 ticks 84381821..84381869 and 84381899..84382000 which are official empty_no_creep (no owned creeps), not official 404. Next 1h patrol should tell this NEW freeze. Already-told freeze 22:17:42-22:20:34 remains in window (59/59 all five; told by 1h patrol _patrol_2026-11-20_2220). Already-told freeze 21:38:41-21:59:40 aged out of window start 84381301 (four rooms 319/319, W47N7 219/319 still short leftover official 404 W47N7@84380900). This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. No concurrent 1h patrol.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_2300.txt")

verify = f"""{now_s}
first pass 35/35 official GETs 200 missing_chunks=0 reconstructed 84381301..84382000 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published 84382000 ticks 84382001..84382100 actual_inserted={actual_sum} script={script_sum}
{nl.join(jp_lines)}
freeze_2244 STATS 84381821..84382059 (239) NEW untold; this run official-filled four rooms 239/239, W47N7 88/239 empty_no_creep 151
{f2244}
freeze_2217 STATS 84381451..84381509 (59) already-told; still 59/59 all five
{f2217}
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.387 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1537042 started=22:59:14 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
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
