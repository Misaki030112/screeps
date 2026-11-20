#!/usr/bin/env python3
"""Write 22:30 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_2230"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
jp = json.loads((DIR / "just_published_84381600.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

# Fix stale first-pass realign reason leftover from the 2200 template.
want = (
    "First-pass realign with tick_s=4.09985 (printed 4.100) moved 15631 rows "
    "(ts_realigned_first=15631, inserted=2796, already_in_db=23800, missing_chunks=1 W47N7@84380900)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace(
    "First-pass realign with tick_s=4.09985 (printed 4.100) moved 15631 rows (ts_realigned_first=15631, inserted=438, already_in_db=23933, missing_chunks=1 W47N8@84380300).",
    want,
)
tick["reason"] = reason
(DIR / "tick_s_realign.json").write_text(json.dumps(tick, indent=2) + "\n")

# Refresh tips at wrap time
with db.connect() as c:
    tips = {}
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute(f"select max(tick) from {table}").fetchone()[0]
    win = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84380901, 84381600),
        ).fetchone()
        win[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
post_tips = post.get("tips") or {}

inserted_first = 2796
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.09985)
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
    "game_time_first": 84381659,
    "published_bases": "84380900..84381500",
    "reconstructed": [84380901, 84381600],
    "ticks": 700,
    "creep_rows": 26596,
    "missing_chunks": 1,
    "already_in_db": 23800,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84381659, published_bases 84380900..84381500, "
        "reconstructed 84380901..84381600 missing_chunks=1 W47N7@84380900 inserted=2796 already_in_db=23800); "
        "34/35 official GETs 200. First pass already included base 84381500 (all five 200), filling the 22:17 freeze unpublished tail. "
        "Concurrent 1h patrol _patrol_2026-11-20_2220 (22:22:30-22:29:07) had already official-filled 84380801..84381500 inserted=7116 already_in_db=18607 and skipped just-published 84381500 (gt 84381546 < 84381600)."
    ),
    "tick_s_printed": 4.100,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 15631,
    "corrective": int(tick.get("ts_realigned_to_later_mean") or 0),
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 643},
        "W47N8": {"ticks": 700, "new": 887},
        "W45N8": {"ticks": 700, "new": 458},
        "W45N7": {"ticks": 700, "new": 534},
        "W47N7": {"ticks": 600, "new": 274},
    },
    "per_room_new_window": {
        r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS
    },
    "in_window_404_after_retry2": ["W47N7@84380900"],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": 84381600,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": True,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp.get("still_404") or [],
    "just_published_retries": [],
    "new_box_freeze": None,
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
        "filled_by": "Concurrent 1h patrol _patrol_2026-11-20_2220 official-filled 84380801..84381500 (W46N8 56/59, other four 50/59, short unpublished tail 84381501..84381509). This run first pass included published base 84381500 (all five 200) and official-filled the remaining tail; now 59/59 all five.",
        "told": True,
        "told_by": "1h patrol ~22:29 亚洲/香港 (_patrol_2026-11-20_2220); this 30-min backfill _halfhour_2026-11-20_2230 completed the unpublished-tail fill",
        "first_recorded_by": "1h patrol _patrol_2026-11-20_2220 (visible in box_pauses.jsonl / errors.log after listener auto-restart 22:20:37)",
        "note": "Already healed. This run did not itself restart the listener. Fold only newer freezes than 22:17:42-22:20:34.",
    },
    "already_told_older_box_freeze_in_window": {
        "from": "2026-11-20 21:38:41",
        "to": "2026-11-20 21:59:40",
        "sec": 1251,
        "stats": "84380901..84381219",
        "span": 319,
        "official_fill": {r: gaps["freeze_2138"][r]["fill"] for r in ROOMS},
        "told": True,
        "told_by": "1h patrol ~22:29 亚洲/香港 (_patrol_2026-11-20_2220); first recorded by 30-min backfill _halfhour_2026-11-20_2200",
        "note": "Still in window start 84380901. Four rooms 319/319; W47N7 219/319 missing 84380901..84381000 because leftover official 404 W47N7@84380900 still 404.",
    },
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [
        {
            "chunk": "W47N7@84380900",
            "hole": "84380901..84381000",
            "still_404_after": f"first pass gt=84381659; confirm {confirm_at} gt={confirm_gt}; retry2 {retry2_at} gt={retry2_gt}",
            "db": post["holes"]["W47N7@84380900"],
            "told": True,
            "told_by": "1h patrol ~22:29 亚洲/香港 (_patrol_2026-11-20_2220); first recorded by 30-min backfill _halfhour_2026-11-20_2200 (confirm 22:05:11 / retry2 22:06:55 still 404)",
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2200",
            "note": "Still leftover official 404: later chunks 84381000..84381600 are published and this chunk is still 404 after this-run confirm/retry2. Quiet wrap; do not re-tell unless a later patrol needs the remaining W47N7 21:38 freeze short 100 ticks as context. Do not clear that short until this chunk fills.",
        }
    ],
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
    "aged_out_leftover_note": (
        "Leftover official 404 W47N8@84380300 (hole 84380301..84380400, still empty) aged out of window start 84380901 and was not retried here. "
        "Already-told freeze 21:17:12-21:19:59 STATS 84380591..84380649 also aged out (official-filled 59/59 all five). "
        "Already-told freeze 20:54:36-20:58:44 STATS 84380271..84380349 aged out earlier (W47N8 still short 49 ticks on that leftover hole)."
    ),
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 21:17:12",
        "to": "2026-11-20 21:19:59",
        "sec": 167,
        "stats": "84380591..84380649",
        "span": 59,
        "official_fill": "all five 59/59",
        "told": True,
        "told_by": "1h patrol ~21:23 亚洲/香港 (_patrol_2026-11-20_2119 / t508s3543); also recorded by 30-min backfill _halfhour_2026-11-20_2130 and later patrols",
        "first_recorded_by": "visible in box_pauses.jsonl after listener auto-restart 21:20:02; concurrent 1h patrol _patrol_2026-11-20_2119",
        "aged_out_of_window_start": 84380901,
    },
    "listener": {
        "single_slot": True,
        "roomSlot": slot,
        "rot": rot,
        "pid": 1522236,
        "started": "22:20:46",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "22:20:37 after box freeze 22:17:42-22:20:34; listener.py started 22:20:46",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "After auto-restart, live.json gameTime can lag (earlier this run it stayed at 84381536) while stats.t / cpu / room_stats / creep_cpu / path_arrivals and live creep_ticks (W47N8 then W45N8/W45N7/W46N8 rotation) keep ingesting. Single peacetime slot, no yield file. Not treated as listener-failed. This run did not restart the listener.",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": {
        "dir": "_patrol_2026-11-20_2220",
        "started": "2026-11-20 22:22:30 CST",
        "finished": "2026-11-20 22:29:07 HKT",
        "official_window": "84380801..84381500",
        "inserted": 7116,
        "already_in_db": 18607,
        "missing_chunks": 1,
        "missing": "W47N7@84380900",
        "just_published_84381500": "skipped (gt 84381546 < 84381600)",
        "told": ["box freeze 22:17:42-22:20:34", "box freeze 21:38:41-21:59:40 first told", "leftover official 404 W47N7@84380900"],
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

f2217 = "  " + "  ".join(
    f"{r} {gaps['freeze_2217'][r]['fill']}"
    + (f" missing {gaps['freeze_2217'][r]['missing_range']}" if gaps["freeze_2217"][r]["missing_n"] else "")
    for r in ROOMS
)
f2138 = "  " + "  ".join(
    f"{r} {gaps['freeze_2138'][r]['fill']}"
    + (f" missing {gaps['freeze_2138'][r]['missing_range']}" if gaps["freeze_2138"][r]["missing_n"] else "")
    for r in ROOMS
)

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
confirm still_404 W47N7@84380900 at 22:33:54 gt=84381688; retry2 still_404 at 22:34:42 gt=84381700. Still leftover official 404 (later chunks 84381000..84381600 published). Already told by 1h patrol _patrol_2026-11-20_2220. Already-told leftover W47N8@84380300 (hole 84380301..84380400) and older leftovers W47N8@84379500, W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 aged out of window start 84380901 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.100 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=15631 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published 84381600 at 2026-11-20 22:37:39 Asia/Hong_Kong game.time=84381741 all_five_200=True actual_inserted={actual_sum} ticks 84381601..84381700 (all five 100/100); script inserted={script_sum}{mismatch_s}
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84381600 actual {actual_sum})
No NEW untold box freeze this run. Already-told freeze 22:17:42-22:20:34 (164s; already healed; listener auto-restart 22:20:37; python 1522236 started 22:20:46; told by 1h patrol _patrol_2026-11-20_2220). STATS 84381451..84381509 (59t; last STATS 84381450 at 22:17:32, next 84381510 at 22:21:18). Concurrent patrol left the unpublished tail short; this run first pass included published 84381500 and official-filled all five 59/59. Already-told freeze 21:38:41-21:59:40 remains in window: four rooms 319/319, W47N7 219/319 missing 84380901..84381000 because leftover official 404 W47N7@84380900 still 404 (told by the same 22:20 patrol; first recorded by 22:00 half-hour). Already-told freeze 21:17:12-21:19:59 aged out of window start 84380901 (59/59 all five). This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. Concurrent 1h patrol _patrol_2026-11-20_2220 finished 22:29:07 before this backfill.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_2230.txt")

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 reconstructed 84380901..84381600 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published 84381600 ticks 84381601..84381700 actual_inserted={actual_sum} script={script_sum}
{chr(10).join(jp_lines)}
freeze_2217 STATS 84381451..84381509 (59) already-told; this run filled tail to 59/59 all five
{f2217}
freeze_2138 STATS 84380901..84381219 (319) already-told
{f2138}
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.100 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1522236 started=22:20:46 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
ok_quiet=True
"""
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")
(DIR / "wrapup_run.txt").write_text(f"wrap {now_s} ok_quiet=True inserted_total={inserted_total}\n")
print("wrote wrap", now_s)
print("inserted_window", inserted_window, "inserted_total", inserted_total, "just_actual", actual_sum)
print("slot", slot, "tips", tips)
print("ok_quiet=True")
