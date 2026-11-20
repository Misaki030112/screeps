#!/usr/bin/env python3
"""Write 22:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_2200"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
jp = json.loads((DIR / "just_published_84381200.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

# Refresh tips at wrap time
with db.connect() as c:
    tips_now = {
        "room_stats": c.execute("select max(tick) from room_stats").fetchone()[0],
        "creep_cpu": c.execute("select max(tick) from creep_cpu").fetchone()[0],
        "path_arrivals": c.execute("select max(tick) from path_arrivals").fetchone()[0],
    }
post_tips = post.get("tips") or {}

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
tips = tips_now
win = post["first_pass_window"]
gaps = post["gaps"]

tick_s_first = float(tick["tick_s_used_first_pass"])
tick_s_in_use = float(tick["tick_s_in_use"])
tick_s_in_use_name = tick["tick_s_in_use_name"]
corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
applied = bool(tick.get("corrective_applied"))

inserted_first = 14966
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

slot = live.get("roomSlot")
rot_s = json.dumps(rot, ensure_ascii=False)
stats = live.get("stats") or {}

cov_rec = cov.get("official_recovered", 3400)
cov_exp = cov.get("expected", 3500)
empty_n = cov.get("empty_no_creep", 0)
off404 = cov.get("official_404_missing", 100)

# Fix stale first-pass numbers accidentally left in tick_s_realign reason.
tick["ts_realigned_first_pass_error"] = (
    "First-pass realign with tick_s=4.17226 (printed 4.172) moved 0 rows "
    "(ts_realigned_first=0, inserted=14966, already_in_db=9865, missing_chunks=1 W47N7@84380900)."
)
tick["reason"] = (
    "first-interval tick_s=4.17226 (printed 4.172, min-all-rooms first two bases) is in the sane 3-6s band; "
    "later-mean-robust 4.20516 (raw later-mean 4.20516; delta first-robust -0.05138 s/tick, ~38.5s at tmin). "
    + tick["ts_realigned_first_pass_error"]
    + " live-anchor-best later_raw 4.20516 already inside 45s gate (over45=0), no corrective realign"
)
(DIR / "tick_s_realign.json").write_text(json.dumps(tick, indent=2) + "\n")

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84381251,
    "published_bases": "84380500..84381100",
    "reconstructed": [84380501, 84381200],
    "ticks": 700,
    "creep_rows": 24831,
    "missing_chunks": 1,
    "already_in_db": 9865,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": "this run tools/history_backfill.py --minutes 40 (game.time=84381251, published_bases 84380500..84381100, reconstructed 84380501..84381200 missing_chunks=1 W47N7@84380900 inserted=14966 already_in_db=9865); 34/35 official GETs 200. No concurrent 1h patrol this run.",
    "tick_s_printed": 4.172,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 0,
    "corrective": corrective if applied else 0,
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {"W46N8": 3296, "W47N8": 5824, "W45N8": 2257, "W45N7": 1264, "W47N7": 2325},
    "per_room_new_window": {"W46N8": 3296, "W47N8": 5824, "W45N8": 2257, "W45N7": 1264, "W47N7": 2325},
    "in_window_404_after_retry2": ["W47N7@84380900"],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": 84381200,
    "just_published_at": "2026-11-20 22:09:01 Asia/Hong_Kong",
    "just_published_gt": 84381341,
    "just_published_all_five_200": True,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": [],
    "just_published_retries": [],
    "new_box_freeze": {
        "from": "2026-11-20 21:38:41",
        "to": "2026-11-20 21:59:40",
        "sec": 1251,
        "why": "box frozen ~1251s since 2026-11-20 21:38:41 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "21:59:44",
        "listener_pid": 1513434,
        "listener_started": "21:59:53",
        "stats": "84380901..84381219",
        "span": 319,
        "last_stats": "84380900 at 21:38:31",
        "next_stats": "84381220 at 22:00:29",
        "official_fill": {room: gaps["freeze_2138"][room]["fill"] for room in ROOMS},
        "filled_by": "This run official first pass 84380501..84381200 plus just-published 84381200 ticks 84381201..84381300 (covers freeze tail 84381201..84381219). Four rooms 319/319; W47N7 219/319 missing 84380901..84381000 because leftover official 404 W47N7@84380900 still 404.",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2200 (visible in box_pauses.jsonl / errors.log after listener auto-restart 21:59:44)",
        "note": "This run did not itself restart the listener (run_listener.sh auto-restarted after the freeze). Quiet wrap; leave telling to the next 1h patrol. Fold only newer freezes than 21:38:41-21:59:40.",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": {
        "from": "2026-11-20 21:17:12",
        "to": "2026-11-20 21:19:59",
        "sec": 167,
        "stats": "84380591..84380649",
        "span": 59,
        "official_fill": {room: gaps["freeze_2117"][room]["fill"] for room in ROOMS},
        "told": True,
        "told_by": "1h patrol ~21:23 亚洲/香港 (_patrol_2026-11-20_2119 / t508s3543); also recorded by 30-min backfill _halfhour_2026-11-20_2130",
        "official_fill_note": "59/59 all five (already filled last hour)",
    },
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [
        {
            "chunk": "W47N7@84380900",
            "hole": "84380901..84381000",
            "still_404_after": "first pass gt=84381251; confirm 22:05:11 gt=84381287; retry2 22:06:55 gt=84381311",
            "db": post["holes"]["W47N7@84380900"],
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2200",
            "note": "Classified as leftover official 404: later chunks 84381000/84381100/84381200 are published and this chunk is still 404. Quiet wrap; leave telling to the next 1h patrol. Do not clear the W47N7 21:38 freeze short 100 ticks until this chunk fills.",
        }
    ],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [],
    "already_recorded_untold_just_published_404": [],
    "aged_out_already_told_404_not_retried": [
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
    "aged_out_leftover_note": "Leftover official 404 W47N8@84380300 (hole 84380301..84380400, still empty) aged out of window start 84380501 and was not retried here. Already-told freeze 20:54:36-20:58:44 STATS 84380271..84380349 also aged out (W47N8 still short 49 ticks on that leftover hole). Already-told freeze 20:17:58-20:20:29 aged out earlier.",
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 20:54:36",
        "to": "2026-11-20 20:58:44",
        "sec": 241,
        "stats": "84380271..84380349",
        "span": 79,
        "official_fill": "four rooms 79/79, W47N8 30/79 missing 84380301..84380349 because leftover W47N8@84380300 still 404",
        "told": True,
        "told_by": "1h patrol ~21:23 亚洲/香港 (_patrol_2026-11-20_2119 / t508s3543); also recorded by 30-min backfills 2100/2130",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2100",
        "aged_out_of_window_start": 84380501,
    },
    "listener": {
        "single_slot": True,
        "roomSlot": slot,
        "rot": rot,
        "pid": 1513434,
        "started": "21:59:53",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "21:59:44 after box freeze 21:38:41-21:59:40; listener.py started 21:59:53",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "After auto-restart, live.json gameTime stayed None and objects_n stayed 0, but stats.t / cpu / room_stats / creep_cpu / path_arrivals and live creep_ticks (W47N8 then W45N8/W45N7 rotation) were ingesting. Single peacetime slot, no yield file. Not treated as listener-failed.",
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

f2138 = "  " + "  ".join(
    f"{r} {gaps['freeze_2138'][r]['fill']}"
    + (f" missing {gaps['freeze_2138'][r]['missing_range']}" if gaps["freeze_2138"][r]["missing_n"] else "")
    for r in ROOMS
)
f2117 = "  " + "  ".join(f"{r} {gaps['freeze_2117'][r]['fill']}" for r in ROOMS)

win_lines = "\n".join(
    f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}"
    + (" official_404=100 hole 84380901..84381000" if win[r]["distinct"] != 700 else "")
    for r in ROOMS
)

script_mismatch = []
for r in ROOMS:
    if actual_by[r] != script_by[r]:
        script_mismatch.append(f"{r} script {script_by[r]} vs actual {actual_by[r]}")
mismatch_s = ("; " + "; ".join(script_mismatch) + ".") if script_mismatch else "."

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
confirm still_404 W47N7@84380900 at 22:05:11 gt=84381287; retry2 still_404 at 22:06:55 gt=84381311. Now classified as leftover official 404 (later chunks 84381000..84381200 published). Already-told leftover W47N8@84380300 (hole 84380301..84380400) and older leftovers W47N8@84379500, W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 aged out of window start 84380501 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.172 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective=0
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published 84381200 at 2026-11-20 22:09:01 Asia/Hong_Kong game.time=84381341 all_five_200=True actual_inserted={actual_sum} ticks 84381201..84381300 (all five 100/100); script inserted={script_sum}{mismatch_s}
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84381200 actual {actual_sum})
NEW box freeze 21:38:41-21:59:40 (1251s; already healed; listener auto-restart 21:59:44; python 1513434 started 21:59:53). STATS 84380901..84381219 (319t; last STATS 84380900 at 21:38:31, next 84381220 at 22:00:29). Official-filled four rooms 319/319; W47N7 219/319 missing 84380901..84381000 because leftover official 404 W47N7@84380900 still 404 (first pass plus just-published 84381200 covers the freeze tail 84381201..84381219). Left to the next 1h patrol. Already-told freeze 21:17:12-21:19:59 remains in window: official-filled all five 59/59. Already-told freeze 20:54:36-20:58:44 aged out of window start 84380501. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file, no concurrent 1h patrol.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_2200.txt")

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 reconstructed 84380501..84381200 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published 84381200 ticks 84381201..84381300 actual_inserted={actual_sum} script={script_sum}
{chr(10).join(jp_lines)}
freeze_2138 STATS 84380901..84381219 (319) NEW untold
{f2138}
freeze_2117 STATS 84380591..84380649 (59) already-told
{f2117}
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.172 corrective=0
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1513434 started=21:59:53 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
ok_quiet=True
"""
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")
(DIR / "wrapup_run.txt").write_text(f"wrap {now_s} ok_quiet=True inserted_total={inserted_total}\n")
print("wrote wrap", now_s)
print("inserted_window", inserted_window, "inserted_total", inserted_total, "just_actual", actual_sum)
print("slot", slot, "tips", tips)
print("ok_quiet=True")
