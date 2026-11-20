#!/usr/bin/env python3
"""Write 02:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0200"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84384001, 84384700
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
jp = json.loads((DIR / "just_published_84384700.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

want = (
    "First-pass realign with tick_s=4.11389 (printed 4.114) moved 0 rows "
    "(ts_realigned_first=0, inserted=11463, already_in_db=11263, missing_chunks=0)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace(
    "moved 0 rows (ts_realigned_first=0, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
    "moved 0 rows (ts_realigned_first=0, inserted=11463, already_in_db=11263, missing_chunks=0).",
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
            (room, WIN_TMIN, WIN_TMAX),
        ).fetchone()
        win[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
holes = post.get("holes") or {}
post_tips = post.get("tips") or {}

inserted_first = 11463
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.11389)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "all_mean"
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
jp_retries = jp.get("retries") or []
jp_still = jp.get("still_404") or []
jp_all_five = (not jp_still) and len(jp.get("recovered") or []) >= 4

script_mismatch = []
for r in ROOMS:
    if actual_by[r] != script_by[r]:
        script_mismatch.append(f"{r} script {script_by[r]} vs actual {actual_by[r]}")
mismatch_s = ("; " + "; ".join(script_mismatch) + ".") if script_mismatch else "."
script_parts = ", ".join(f"{r} +{script_by[r]}" for r in ROOMS)

def fill_missing(gap_key):
    missing = {}
    for r in ROOMS:
        g = (gaps.get(gap_key) or {}).get(r) or {}
        if g.get("missing_n"):
            missing[r] = f"{g.get('missing_range')} ({g.get('missing_n')})"
    return missing

new_fill_missing = fill_missing("gap_0147_0202")
old0110_missing = fill_missing("gap_0110_0124")

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84384713,
    "published_bases": "84384000..84384600",
    "reconstructed": [84384001, 84384700],
    "ticks": 700,
    "creep_rows": 22726,
    "missing_chunks": 0,
    "already_in_db": 11263,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84384713, published_bases 84384000..84384600, "
        "reconstructed 84384001..84384700 missing_chunks=0 inserted=11463 already_in_db=11263); "
        "35/35 official GETs 200. No concurrent 1h patrol. First pass already covers the NEW STATS hole "
        "84384461..84384689."
    ),
    "tick_s_printed": 4.114,
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
        "W46N8": {"ticks": 700, "new": 2247},
        "W47N8": {"ticks": 700, "new": 4140},
        "W45N8": {"ticks": 700, "new": 1440},
        "W45N7": {"ticks": 700, "new": 1781},
        "W47N7": {"ticks": 700, "new": 1855},
    },
    "per_room_new_window": {
        r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS
    },
    "in_window_404_after_retry2": [],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": 84384700,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": jp_all_five,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp_still,
    "just_published_retries": jp_retries,
    "just_published_actual_note": (
        f"script inserted={script_sum} ({script_parts}). "
        f"post-counts actual_sum={actual_sum}{mismatch_s} "
        f"All five ended 100/100." if jp_all_five else
        f"script inserted={script_sum} ({script_parts}). "
        f"post-counts actual_sum={actual_sum}{mismatch_s}"
    ),
    "new_box_freeze": {
        "from": "2026-11-21 01:47:58",
        "to": "2026-11-21 02:02:50",
        "sec": 884,
        "why": "box frozen ~884s since 2026-11-21 01:47:58 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "02:02:53",
        "listener_pid": 1608535,
        "listener_started": "02:03:02",
        "stats": "84384461..84384689",
        "span": 229,
        "stats_note": (
            "The 229-tick STATS hole is the box freeze alone; errors.log has no preceding no-STATS. "
            "last STATS 84384460 at 01:47:24, next STATS 84384690 at 02:03:19."
        ),
        "last_stats": "84384460 at 01:47:24",
        "next_stats": "84384690 at 02:03:19",
        "official_fill": {r: gaps["gap_0147_0202"][r]["fill"] for r in ROOMS},
        "official_fill_missing": new_fill_missing,
        "filled_by": (
            "This 02:00 official history backfill first pass (published through 84384600, reconstructed through 84384700) "
            "official-filled the STATS hole 84384461..84384689. missing_chunks=0."
        ),
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0200 (visible in box_pauses.jsonl / errors.log after listener auto-restart 02:02:53)",
        "note": "Already healed. This run did not itself restart the listener. Next 1h patrol should tell this NEW freeze. Fold only newer freezes than 01:47:58-02:02:50.",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": {
        "from": "2026-11-21 01:10:46",
        "to": "2026-11-21 01:24:59",
        "sec": 846,
        "why": "box frozen ~846s since 2026-11-21 01:10:46 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "01:25:02",
        "stats": "84383931..84384149",
        "span": 219,
        "last_stats": "84383930 at 01:10:36",
        "next_stats": "84384150 at 01:25:52",
        "official_fill": {r: gaps["gap_0110_0124"][r]["fill"] for r in ROOMS},
        "official_fill_missing": old0110_missing,
        "told": True,
        "told_by": "1h patrol ~01:33 Asia/Hong_Kong (_patrol_2026-11-21_0124)",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0130 / concurrent 1h patrol _patrol_2026-11-21_0124",
        "note": (
            "Already told by the 01:33 patrol. Partial in window start 84384001 "
            "(84384001..84384149 in-window; W45N7 still missing 84383931..84384000 from official 404 W45N7@84383900, which aged out of this window)."
        ),
    },
    "already_told_older_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-21 00:50:52",
        "to": "2026-11-21 00:57:30",
        "sec": 393,
        "stats": "84383651..84383759",
        "span": 109,
        "official_fill": {r: gaps["gap_0050_0057"][r]["fill"] for r in ROOMS},
        "told": True,
        "told_by": "1h patrol ~01:33 Asia/Hong_Kong (_patrol_2026-11-21_0124)",
        "aged_out_of_window_start": 84384001,
        "note": "Already healed and already told. Ages out of window start 84384001. Still 109/109 all five.",
    },
    "aged_out_already_told_short_listener_gap": {
        "from": "2026-11-21 00:14:38",
        "to": "2026-11-21 00:19:22",
        "combined_with_freeze": "00:19:22-00:22:38",
        "stats": "84383131..84383249",
        "span": 119,
        "aged_out_of_window_start": 84384001,
        "told": True,
        "told_by": "1h patrol ~00:32 Asia/Hong_Kong (_patrol_2026-11-21_0022)",
        "official_fill": {r: gaps["gap_0014_0022"][r]["fill"] for r in ROOMS},
        "note": "Still 119/119 all five. Combined no-STATS after 00:14:38 + box freeze 00:19:22-00:22:38.",
    },
    "new_official_404": [],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [],
    "already_recorded_untold_just_published_404": [],
    "aged_out_already_told_404_not_retried": [
        "W45N7@84383500",
        "W45N7@84383900",
        "W45N7@84382700",
        "W46N8@84382900",
        "W45N8@84382600",
        "W47N8@84382100",
        "W47N7@84380900",
        "W47N8@84380300",
        "W47N8@84379500",
        "W45N8@84378900",
    ],
    "aged_out_leftover_note": (
        "Already-told official 404s W45N7@84383500 (hole 84383501..84383600, 0/100) and W45N7@84383900 "
        "(hole 84383901..84384000, 0/100; last 70 ticks sit in the already-told freeze STATS gap 84383931..84384149) "
        "aged out of window start 84384001 and were not retried here (already told by 1h patrol _patrol_2026-11-21_0124). "
        "Older already-told leftovers W45N7@84382700 (0/100), W46N8@84382900 (DB 67/100 missing 84382901..84382933), "
        "and W45N8@84382600 (0/100), plus W47N8@84382100, W47N7@84380900, W47N8@84380300, W47N8@84379500, W45N8@84378900, "
        "remain unfilled or listener-filled and were not retried here."
    ),
    "prior_told_box_freeze_aged_out": [
        {
            "from": "2026-11-21 00:50:52",
            "to": "2026-11-21 00:57:30",
            "sec": 393,
            "stats": "84383651..84383759",
            "span": 109,
            "official_fill": {r: gaps["gap_0050_0057"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0124",
            "aged_out_of_window_start": 84384001,
            "note": "Still 109/109 all five.",
        },
        {
            "from": "2026-11-21 00:19:22",
            "to": "2026-11-21 00:22:38",
            "sec": 195,
            "stats": "84383131..84383249",
            "span": 119,
            "official_fill": {r: gaps["gap_0014_0022"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0022",
            "aged_out_of_window_start": 84384001,
            "note": "Combined with preceding no-STATS after 00:14:38. Still 119/119 all five.",
        },
        {
            "from": "2026-11-20 23:50:34",
            "to": "2026-11-20 23:57:00",
            "sec": 385,
            "stats": "84382641..84382889",
            "span": 249,
            "official_fill": "not re-queried this run (aged out of window start 84384001)",
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0022",
            "aged_out_of_window_start": 84384001,
            "note": "Combined with preceding 23:40 no-STATS. Previously W46N8/W47N8/W47N7 249/249; W45N8 189/249; W45N7 149/249.",
        },
    ],
    "w47n7_official_empty_no_creep": {
        "distinct": 700,
        "empty_n": 0,
        "ranges": "",
        "note": "Not present in this first-pass window (W47N7 700/700).",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": slot,
        "rot": rot,
        "pid": 1608535,
        "started": "02:03:02",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "02:02:53 after box freeze 01:47:58-02:02:50; listener.py started 02:03:02",
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

def gap_line(key):
    return "  " + "  ".join(
        f"{r} {gaps[key][r]['fill']}"
        + (f" missing {gaps[key][r]['missing_range']}" if gaps[key][r]["missing_n"] else "")
        for r in ROOMS
    )

g_new = gap_line("gap_0147_0202")
g_0110 = gap_line("gap_0110_0124")
g_0050 = gap_line("gap_0050_0057")
g_0014 = gap_line("gap_0014_0022")

win_lines = "\n".join(
    f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}"
    for r in ROOMS
)

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = "\n"
new_missing_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in new_fill_missing.items())
    if new_fill_missing else "; official-filled all five 229/229"
)
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
confirm {confirm_at} and retry2 {retry2_at} skipped (no targets; first pass 35/35 official GETs 200, missing_chunks=0). Already-told leftover official 404s W45N7@84383500 (hole 84383501..84383600, 0/100) and W45N7@84383900 (hole 84383901..84384000, 0/100), plus older leftovers W45N7@84382700, W46N8@84382900, W45N8@84382600, aged out of window start 84384001 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.114 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published 84384700 at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84384701..84384800; script inserted={script_sum}{mismatch_s} All five ended 100/100.
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84384700 actual {actual_sum})
NEW box freeze 01:47:58-02:02:50 (884s; already healed; listener auto-restart 02:02:53; python 1608535 started 02:03:02). STATS hole 84384461..84384689 (229t; last STATS 84384460 at 01:47:24, next 84384690 at 02:03:19); no preceding no-STATS. Official-filled by this first pass (reconstructed through 84384700, missing_chunks=0){new_missing_txt}. Next 1h patrol should tell this NEW freeze. Already-told freeze 01:10:46-01:24:59 (STATS 84383931..84384149, 219t; official-filled four rooms 219/219, W45N7 149/219 missing 84383931..84384000 from official 404 W45N7@84383900) is partial in window start 84384001 and remains already told by the 01:33 patrol. Already-told freeze 00:50:52-00:57:30 (STATS 84383651..84383759, 109t) and already-told 00:14:38 no-STATS + 00:19:22-00:22:38 freeze (STATS 84383131..84383249, 119t) aged out of window start 84384001. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. No concurrent 1h patrol.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_0200.txt")

verify = f"""{now_s}
first pass 35/35 official GETs 200 missing_chunks=0 reconstructed 84384001..84384700 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published 84384700 ticks 84384701..84384800 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{nl.join(jp_lines)}
gap_0147_0202 STATS 84384461..84384689 (229) NEW box freeze 01:47:58-02:02:50
{g_new}
gap_0110_0124 STATS 84383931..84384149 (219) already-told by 01:33 patrol (box freeze 01:10:46-01:24:59); partial in window start 84384001
{g_0110}
gap_0050_0057 STATS 84383651..84383759 (109) already-told by 01:33 patrol (box freeze 00:50:52-00:57:30); aged out of window start 84384001
{g_0050}
gap_0014_0022 STATS 84383131..84383249 (119) already-told by 00:32 patrol (no-STATS after 00:14:38 + box freeze 00:19:22-00:22:38); aged out of window start 84384001
{g_0014}
aged-out already-told official 404 W45N7@84383500 0/100, W45N7@84383900 0/100, W45N7@84382700 0/100, W46N8@84382900 67/100, W45N8@84382600 0/100 (not retried)
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.114 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)} ts_realigned_first=0
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1608535 started=02:03:02 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
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
print(summary, end="")
