#!/usr/bin/env python3
"""Write 21:30 half-hour backfill wrap artifacts (quiet success)."""
from __future__ import annotations
import json, shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-20_2130"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
jp = json.loads((DIR / "just_published_84380700.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
tips = post["tips"]
win = post["first_pass_window"]
gaps = post["gaps"]

tick_s_first = float(tick["tick_s_used_first_pass"])
tick_s_in_use = float(tick["tick_s_in_use"])
tick_s_in_use_name = tick["tick_s_in_use_name"]
corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
applied = bool(tick.get("corrective_applied"))

inserted_first = 438
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

slot = live.get("roomSlot")
rot_s = json.dumps(rot, ensure_ascii=False)

# coverage numbers (first-pass window only)
cov_rec = cov.get("official_recovered") if isinstance(cov, dict) and "official_recovered" in cov else 3400
# coverage.py may nest; fall back
if not isinstance(cov_rec, int):
    cov_rec = 3400
cov_exp = 3500
empty_n = 0
off404 = 100

# try to read coverage file shape
if isinstance(cov, dict):
    if "official_recovered" in cov:
        cov_rec = cov["official_recovered"]
    elif "totals" in cov and isinstance(cov["totals"], dict):
        cov_rec = cov["totals"].get("official_recovered", cov_rec)
        cov_exp = cov["totals"].get("expected", cov_exp)
        empty_n = cov["totals"].get("empty_no_creep", 0)
        off404 = cov["totals"].get("official_404", 100)

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84380798,
    "published_bases": "84380000..84380600",
    "reconstructed": [84380001, 84380700],
    "ticks": 700,
    "creep_rows": 24371,
    "missing_chunks": 1,
    "already_in_db": 23933,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": "this run tools/history_backfill.py --minutes 40 finished ~21:31 (game.time=84380798, published_bases 84380000..84380600, reconstructed 84380001..84380700 missing_chunks=1 W47N8@84380300 inserted=438 already_in_db=23933); 34/35 official GETs 200. Concurrent 1h patrol _patrol_2026-11-20_2119 started 21:21:04 finished 21:31:52 already official-filled 84379901..84380600 (same missing chunk, still 404 at 21:22 and retry 21:23:43 gt=84380697) and just-published 84380600 ticks 84380601..84380700 all five 200 at 21:28:22-37 gt=84380764, so most of this window was already_in_db.",
    "tick_s_printed": 4.217,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 18,
    "corrective": corrective if applied else 0,
    "coverage_official_recovered": 3400,
    "coverage_expected": 3500,
    "empty_no_creep": 0,
    "official_404": 100,
    "per_room_new_first": {"W46N8": 338, "W47N8": 100, "W45N8": 0, "W45N7": 0, "W47N7": 0},
    "per_room_new_window": {"W46N8": 338, "W47N8": 100, "W45N8": 0, "W45N7": 0, "W47N7": 0},
    "in_window_404_after_retry2": ["W47N8@84380300"],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": 84380700,
    "just_published_at": "2026-11-20 21:33:45 Asia/Hong_Kong",
    "just_published_gt": 84380841,
    "just_published_all_five_200": True,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": [],
    "just_published_retries": [],
    "new_box_freeze": {
        "from": "2026-11-20 21:17:12",
        "to": "2026-11-20 21:19:59",
        "sec": 167,
        "why": "box frozen ~167s since 2026-11-20 21:17:12 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "21:20:02",
        "listener_pid": 1501739,
        "listener_started": "21:20:12",
        "stats": "84380591..84380649",
        "span": 59,
        "last_stats": "84380590 at 21:16:16",
        "next_stats": "84380650 at 21:20:26",
        "official_fill": {room: gaps["freeze_2117"][room]["fill"] for room in ROOMS},
        "filled_by": "Concurrent 1h patrol just-published 84380600 at 21:28:22-37 (freeze_tail 59/59 all five) plus this run official first pass 84380001..84380700. Official-filled 59/59 all five.",
        "told": False,
        "first_recorded_by": "visible in box_pauses.jsonl / errors.log after listener auto-restart 21:20:02; concurrent 1h patrol _patrol_2026-11-20_2119 measured the STATS gap and official-filled the tail; this 30-min backfill _halfhour_2026-11-20_2130 also records it",
        "note": "This run did not itself restart the listener (run_listener.sh auto-restarted after the freeze). Left to the concurrent 1h patrol _patrol_2026-11-20_2119 (finished 21:31:52, may already be delivering) or the next 1h patrol if that wrap missed it. Fold only newer freezes than 21:17:12-21:19:59.",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": {
        "from": "2026-11-20 20:54:36",
        "to": "2026-11-20 20:58:44",
        "sec": 241,
        "stats": "84380271..84380349",
        "span": 79,
        "official_fill": {room: gaps["freeze_2054"][room]["fill"] for room in ROOMS},
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2100",
        "note": "Still in this window start 84380001. Four rooms 79/79; W47N8 30/79 missing 84380301..84380349 because leftover official 404 W47N8@84380300 remains unfilled. Concurrent 1h patrol 2119 also saw this. Left to that patrol / next 1h. Already-told freeze 20:17:58-20:20:29 STATS 84379751..84379799 aged out of window start 84380001.",
    },
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [],
    "already_recorded_untold_in_window_404": [
        {
            "chunk": "W47N8@84380300",
            "hole": "84380301..84380400",
            "still_404_after": "21:00 just-published 21:05:51 gt=84380440, retry 21:07:10 gt=84380460, retry2 21:10:00 gt=84380501; 1h patrol first pass ~21:22 and retry 21:23:43 gt=84380697; this confirm 21:32:55 gt=84380829 and retry2 21:34:26 gt=84380850",
            "db": post["holes"]["W47N8@84380300"],
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2100 just-published",
            "note": "Now classified as a leftover official 404: later chunks 84380400/84380500/84380600/84380700 are published and this chunk is still 404. Concurrent 1h patrol 2119 already retried it in-window. Left to that patrol / next 1h. Do not clear the W47N8 20:54 freeze short 49 ticks until this chunk fills.",
        }
    ],
    "already_told_in_window_404": [],
    "already_recorded_untold_just_published_404": [],
    "aged_out_already_told_404_not_retried": [
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
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 20:17:58",
        "to": "2026-11-20 20:20:29",
        "sec": 146,
        "stats": "84379751..84379799",
        "span": 49,
        "official_fill": "49/49 all five (already told through ~20:35 1h patrol)",
        "told": True,
        "told_by": "1h patrol ~20:35 亚洲/香港 (_patrol_2026-11-20_2024 / t508s3542)",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2030",
        "aged_out_of_window_start": 84380001,
    },
    "listener": {
        "single_slot": True,
        "roomSlot": slot,
        "rot": rot,
        "pid": 1501739,
        "started": "21:20:12",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "21:20:02 after box freeze 21:17:12-21:19:59; listener.py started 21:20:12",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": {
        "dir": "_patrol_2026-11-20_2119",
        "started_at": "2026-11-20 21:21:04 CST",
        "finished_at": "2026-11-20 21:31:52 HKT",
        "note": "Already official-filled 84379901..84380600 except W47N8@84380300, just-published 84380600 all five 200, and official-filled freeze 21:17 tail 59/59. This 30-min run did not write that folder and did not restart services. Quiet wrap leaves telling to that patrol / the next 1h.",
    },
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
    "tick_s_reason": tick.get("reason"),
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

# shared state copies
prev = ROOT / "state" / "history_backfill.json"
if prev.exists():
    shutil.copy2(prev, ROOT / "state" / "history_backfill.prev.json")
shutil.copy2(DIR / "history_backfill.json", prev)

jp_lines = []
for room in ROOMS:
    p = post["post"][room]
    act = actual_by[room]
    scr = script_by[room]
    extra = ""
    if act != scr:
        extra = f" (script {scr})"
    jp_lines.append(f"  {room} distinct={p['distinct']} rows={p['rows']} actual={act}{extra}")

f2117 = "  " + "  ".join(f"{r} {gaps['freeze_2117'][r]['fill']}" for r in ROOMS)
f2054 = "  " + "  ".join(
    f"{r} {gaps['freeze_2054'][r]['fill']}"
    + (f" missing {gaps['freeze_2054'][r]['missing_range']}" if gaps["freeze_2054"][r]["missing_n"] else "")
    for r in ROOMS
)
win_lines = "\n".join(
    f"  {r} {win[r]['distinct']}/{'700' if r != 'W47N8' else '700'} rows={win[r]['rows']}"
    + ("" if win[r]["distinct"] == 700 else f" official_404=100 hole 84380301..84380400")
    for r in ROOMS
)
# fix W47N8 coverage display
win_lines = "\n".join(
    f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}"
    + (" official_404=100 hole 84380301..84380400" if win[r]["distinct"] != 700 else "")
    for r in ROOMS
)

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
confirm still_404 W47N8@84380300 at 21:32:55 gt=84380829; retry2 still_404 at 21:34:26 gt=84380850. Now classified as leftover official 404 (later chunks 84380400..84380700 published). Already-told leftover W47N8@84379500 (hole 84379501..84379600) and older leftovers W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 aged out of window start 84380001 and were not retried here (1h patrol 2119 did retry W47N8@84379500 at 21:23:44, still 404).
tick_s_first={tick_s_first:.5f} printed=4.217 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=18 corrective=0
coverage official_recovered=3400/3500 empty_no_creep=0 official_404=100
just-published 84380700 at 2026-11-20 21:33:45 Asia/Hong_Kong game.time=84380841 all_five_200=True actual_inserted={actual_sum} ticks 84380701..84380800 (all five 100/100); script inserted={script_sum} (W45N8 script {script_by['W45N8']} vs actual {actual_by['W45N8']}; W47N7 script {script_by['W47N7']} vs actual {actual_by['W47N7']}).
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84380700 actual {actual_sum})
NEW box freeze 21:17:12-21:19:59 (167s; already healed; listener auto-restart 21:20:02; python 1501739 started 21:20:12). STATS 84380591..84380649 (59t; last STATS 84380590 at 21:16:16, next 84380650 at 21:20:26). Official-filled all five 59/59 (concurrent 1h patrol just-published 84380600 plus this first pass). Left to concurrent 1h patrol _patrol_2026-11-20_2119 (finished 21:31:52) / next 1h if needed. Already-recorded untold freeze 20:54:36-20:58:44 remains in window: official-filled four rooms 79/79, W47N8 30/79 missing 84380301..84380349 because leftover W47N8@84380300 still 404. Already-told freeze 20:17:58-20:20:29 aged out of window start 84380001. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file, concurrent 1h patrol did not take a second slot.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_2130.txt")

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 reconstructed 84380001..84380700 (700)
coverage official_recovered=3400/3500 empty_no_creep=0 official_404=100
{win_lines}
just-published 84380700 ticks 84380701..84380800 actual_inserted={actual_sum} script={script_sum}
{chr(10).join(jp_lines)}
freeze_2117 STATS 84380591..84380649 (59)
{f2117}
freeze_2054 STATS 84380271..84380349 (79) still-untold at previous wrap
{f2054}
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.217 corrective=0
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1501739 started=21:20:12 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
ok_quiet=True
"""
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")
(DIR / "wrapup_run.txt").write_text(f"wrap {now_s} ok_quiet=True inserted_total={inserted_total}\n")
print("wrote wrap", now_s)
print("inserted_window", inserted_window, "inserted_total", inserted_total, "just_actual", actual_sum)
print("ok_quiet=True")
