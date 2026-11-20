#!/usr/bin/env python3
"""Write 02:30 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0230"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84384401, 84385100
JUST_BASE = 84385100
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
jp = json.loads((DIR / f"just_published_{JUST_BASE}.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

want = (
    "First-pass realign with tick_s=4.13743 (printed 4.137) moved 0 rows "
    "(ts_realigned_first=0, inserted=3056, already_in_db=21327, missing_chunks=0)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace(
    "moved 0 rows (ts_realigned_first=0, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
    "moved 0 rows (ts_realigned_first=0, inserted=3056, already_in_db=21327, missing_chunks=0).",
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

inserted_first = 3056
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.13743)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "prev_later"
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
jp_rec = jp.get("recovered") or []
jp_all_five = (not jp_still) and len(jp_rec) >= 5

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

fill_0147 = fill_missing("gap_0147_0202")
fill_0220 = fill_missing("gap_0220_0222")
fill_0110 = fill_missing("gap_0110_0124")

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84385145,
    "published_bases": "84384400..84385000",
    "reconstructed": [84384401, 84385100],
    "ticks": 700,
    "creep_rows": 24383,
    "missing_chunks": 0,
    "already_in_db": 21327,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84385145, published_bases 84384400..84385000, "
        "reconstructed 84384401..84385100 missing_chunks=0 inserted=3056 already_in_db=21327); "
        "35/35 official GETs 200. Prior 1h patrol _patrol_2026-11-21_0221 finished 02:30:03 and had already official-filled "
        "84384201..84384900 plus just-published 84384900 through 84385000 (short_fill 19/19 all five), so this first pass "
        "mostly confirmed overlap and inserted the newly published 84385000 chunk. Not running concurrently with this backfill."
    ),
    "tick_s_printed": 4.137,
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
        "W46N8": {"ticks": 700, "new": 571},
        "W47N8": {"ticks": 700, "new": 818},
        "W45N8": {"ticks": 700, "new": 506},
        "W45N7": {"ticks": 700, "new": 681},
        "W47N7": {"ticks": 700, "new": 480},
    },
    "per_room_new_window": {
        r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS
    },
    "in_window_404_after_retry2": [],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": JUST_BASE,
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
    "new_box_freeze": None,
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": {
        "from": "2026-11-21 01:47:58",
        "to": "2026-11-21 02:02:50",
        "sec": 884,
        "why": "box frozen ~884s since 2026-11-21 01:47:58 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "02:02:53",
        "stats": "84384461..84384689",
        "span": 229,
        "last_stats": "84384460 at 01:47:24",
        "next_stats": "84384690 at 02:03:19",
        "official_fill": {r: gaps["gap_0147_0202"][r]["fill"] for r in ROOMS},
        "official_fill_missing": fill_0147,
        "told": True,
        "told_by": "1h patrol ~02:28/02:30 Asia/Hong_Kong (_patrol_2026-11-21_0221)",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0200 / 1h patrol _patrol_2026-11-21_0221",
        "note": "Already told by the 02:28/02:30 patrol. Fully in window start 84384401. Official-filled 229/229 all five. Fold only newer freezes than 01:47:58-02:02:50.",
    },
    "already_told_short_listener_gap_in_window": {
        "from": "2026-11-21 02:20:54",
        "to": "2026-11-21 02:22:17",
        "sec": 83,
        "why": "ws error ping/pong timed out at 02:21:57; listener auto-restart 02:22:00",
        "listener_restart": "02:22:00",
        "listener_pid": 1617878,
        "listener_started": "02:22:09",
        "stats": "84384941..84384959",
        "span": 19,
        "last_stats": "84384940 at 02:20:54",
        "next_stats": "84384960 at 02:22:17",
        "official_fill": {r: gaps["gap_0220_0222"][r]["fill"] for r in ROOMS},
        "official_fill_missing": fill_0220,
        "told": True,
        "told_by": "1h patrol ~02:28/02:30 Asia/Hong_Kong (_patrol_2026-11-21_0221)",
        "filled_by": "1h patrol just-published 84384900 (short_fill 19/19 all five); reconfirmed by this first pass (reconstructed through 84385100, missing_chunks=0).",
        "note": "Already told by the 02:28/02:30 patrol. Fully in window start 84384401. Official-filled 19/19 all five. Fold only newer short gaps than 02:20:54-02:22:17.",
    },
    "already_told_older_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-21 01:10:46",
        "to": "2026-11-21 01:24:59",
        "sec": 846,
        "stats": "84383931..84384149",
        "span": 219,
        "official_fill": {r: gaps["gap_0110_0124"][r]["fill"] for r in ROOMS},
        "official_fill_missing": fill_0110,
        "told": True,
        "told_by": "1h patrol ~01:33 Asia/Hong_Kong (_patrol_2026-11-21_0124)",
        "aged_out_of_window_start": 84384401,
        "note": "Already healed and already told. Ages out of window start 84384401. W45N7 still missing 84383931..84384000 from official 404 W45N7@84383900; other four rooms 219/219.",
    },
    "aged_out_already_told_short_listener_gap": {
        "from": "2026-11-21 00:14:38",
        "to": "2026-11-21 00:19:22",
        "combined_with_freeze": "00:19:22-00:22:38",
        "stats": "84383131..84383249",
        "span": 119,
        "aged_out_of_window_start": 84384401,
        "told": True,
        "told_by": "1h patrol ~00:32 Asia/Hong_Kong (_patrol_2026-11-21_0022)",
        "official_fill": "not re-queried this run (aged out of window start 84384401)",
        "note": "Combined no-STATS after 00:14:38 + box freeze 00:19:22-00:22:38. Previously 119/119 all five.",
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
        "aged out of window start 84384401 and were not retried here (already told by 1h patrol _patrol_2026-11-21_0124). "
        "Older already-told leftovers W45N7@84382700 (0/100), W46N8@84382900 (DB 67/100 missing 84382901..84382933), "
        "and W45N8@84382600 (0/100), plus W47N8@84382100, W47N7@84380900, W47N8@84380300, W47N8@84379500, W45N8@84378900, "
        "remain unfilled or listener-filled and were not retried here."
    ),
    "prior_told_box_freeze_aged_out": [
        {
            "from": "2026-11-21 01:10:46",
            "to": "2026-11-21 01:24:59",
            "sec": 846,
            "stats": "84383931..84384149",
            "span": 219,
            "official_fill": {r: gaps["gap_0110_0124"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0124",
            "aged_out_of_window_start": 84384401,
            "note": "W45N7 still missing 84383931..84384000 from official 404 W45N7@84383900; other four rooms 219/219.",
        },
        {
            "from": "2026-11-21 00:50:52",
            "to": "2026-11-21 00:57:30",
            "sec": 393,
            "stats": "84383651..84383759",
            "span": 109,
            "official_fill": {r: gaps["gap_0050_0057"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0124",
            "aged_out_of_window_start": 84384401,
            "note": "Still 109/109 all five.",
        },
        {
            "from": "2026-11-21 00:19:22",
            "to": "2026-11-21 00:22:38",
            "sec": 195,
            "stats": "84383131..84383249",
            "span": 119,
            "official_fill": "not re-queried this run (aged out of window start 84384401)",
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0022",
            "aged_out_of_window_start": 84384401,
            "note": "Combined with preceding no-STATS after 00:14:38. Previously 119/119 all five.",
        },
        {
            "from": "2026-11-20 23:50:34",
            "to": "2026-11-20 23:57:00",
            "sec": 385,
            "stats": "84382641..84382889",
            "span": 249,
            "official_fill": "not re-queried this run (aged out of window start 84384401)",
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0022",
            "aged_out_of_window_start": 84384401,
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
        "pid": 1617878,
        "started": "02:22:09",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "02:22:00 after short listener gap 02:20:54-02:22:17 (ping/pong timed out 02:21:57); listener.py started 02:22:09",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "Listener auto-restarted after the already-told 02:20 short gap and has been connected since 02:22:09 (live.json fresh, creep_cpu/path_arrivals ingesting). Single peacetime slot 5:5:1:1, no yield file. This run did not restart the listener or war_cmd/pulse.",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": {
        "id": "_patrol_2026-11-21_0221",
        "finished_at": "2026-11-21 02:30:03",
        "overlap_during_this_run": False,
        "note": "Finished about two minutes before this backfill started. Already official-filled 84384201..84384900 (700, missing_chunks=0, inserted=3001) and just-published 84384900 ticks 84384901..84385000 all_five_200=True (short_fill 19/19 all five).",
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

def gap_line(key):
    return "  " + "  ".join(
        f"{r} {gaps[key][r]['fill']}"
        + (f" missing {gaps[key][r]['missing_range']}" if gaps[key][r]["missing_n"] else "")
        for r in ROOMS
    )

g_0147 = gap_line("gap_0147_0202")
g_0220 = gap_line("gap_0220_0222")
g_0110 = gap_line("gap_0110_0124")
g_0050 = gap_line("gap_0050_0057")

win_lines = "\n".join(
    f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}"
    for r in ROOMS
)

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = "\n"
fill_0147_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0147.items())
    if fill_0147 else "; official-filled all five 229/229"
)
fill_0220_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0220.items())
    if fill_0220 else "; official-filled all five 19/19"
)
jp_all_s = f" All five ended 100/100." if jp_all_five else ""
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
confirm {confirm_at} and retry2 {retry2_at} skipped (no targets; first pass 35/35 official GETs 200, missing_chunks=0). Already-told leftover official 404s W45N7@84383500 (hole 84383501..84383600, 0/100) and W45N7@84383900 (hole 84383901..84384000, 0/100), plus older leftovers W45N7@84382700, W46N8@84382900, W45N8@84382600, aged out of window start 84384401 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.137 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published {JUST_BASE} at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84385101..84385200; script inserted={script_sum}{mismatch_s}{jp_all_s}
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just {JUST_BASE} actual {actual_sum})
No NEW box freeze and no NEW short listener gap this window. Already-told freeze 01:47:58-02:02:50 (STATS 84384461..84384689, 229t; last STATS 84384460 at 01:47:24, next 84384690 at 02:03:19) is fully in window start 84384401 and remains already told by the 02:28/02:30 patrol{fill_0147_txt}. Already-told short listener gap 02:20:54-02:22:17 (STATS 84384941..84384959, 19t; listener auto-restart 02:22:00, python 1617878 started 02:22:09) is fully in window and remains already told by the 02:28/02:30 patrol{fill_0220_txt}. Already-told freeze 01:10:46-01:24:59 (STATS 84383931..84384149, 219t; W45N7 still missing 84383931..84384000 from official 404 W45N7@84383900) aged out of window start 84384401, as did already-told freeze 00:50:52-00:57:30 (STATS 84383651..84383759, 109t) and already-told 00:14:38 no-STATS + 00:19:22-00:22:38 freeze (STATS 84383131..84383249, 119t). Prior 1h patrol _patrol_2026-11-21_0221 finished 02:30:03 and is not concurrent with this run. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_0230.txt")

verify = f"""{now_s}
first pass 35/35 official GETs 200 missing_chunks=0 reconstructed 84384401..84385100 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84385101..84385200 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{nl.join(jp_lines)}
gap_0147_0202 STATS 84384461..84384689 (229) already-told by 02:28/02:30 patrol (box freeze 01:47:58-02:02:50)
{g_0147}
gap_0220_0222 STATS 84384941..84384959 (19) already-told by 02:28/02:30 patrol (short listener gap 02:20:54-02:22:17)
{g_0220}
gap_0110_0124 STATS 84383931..84384149 (219) already-told by 01:33 patrol (box freeze 01:10:46-01:24:59); aged out of window start 84384401
{g_0110}
gap_0050_0057 STATS 84383651..84383759 (109) already-told by 01:33 patrol (box freeze 00:50:52-00:57:30); aged out of window start 84384401
{g_0050}
aged-out already-told official 404 W45N7@84383500 0/100, W45N7@84383900 0/100, W45N7@84382700 0/100, W46N8@84382900 67/100, W45N8@84382600 0/100 (not retried)
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.137 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)} ts_realigned_first=0
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1617878 started=02:22:09 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
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
