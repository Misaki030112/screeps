#!/usr/bin/env python3
"""Write 03:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0300"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84384901, 84385600
JUST_BASE = 84385600
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
    "First-pass realign with tick_s=4.23559 (printed 4.236) moved 3363 rows "
    "(ts_realigned_first=3363, inserted=13714, already_in_db=12273, missing_chunks=1 W47N8@84385300)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace(
    "moved 3363 rows (ts_realigned_first=3363, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
    "moved 3363 rows (ts_realigned_first=3363, inserted=13714, already_in_db=12273, missing_chunks=1 W47N8@84385300).",
)
reason = reason.replace(
    "(printed 4.137, min-all-rooms first two bases)",
    "(printed 4.236, min-all-rooms first two bases)",
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

inserted_first = 13714
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.23559)
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
confirm_still = confirm.get("still_404") or []
retry2_still = retry2.get("still_404") or confirm.get("retry2_still_404") or []
confirm_rec = confirm.get("recovered") or []
retry2_rec = retry2.get("recovered") or confirm.get("retry2_recovered") or []

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

fill_0245 = fill_missing("gap_0245_0305")
fill_0220 = fill_missing("gap_0220_0222")
fill_0147 = fill_missing("gap_0147_0202")
fill_0110 = fill_missing("gap_0110_0124")

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84385617,
    "published_bases": "84384900..84385500",
    "reconstructed": [84384901, 84385600],
    "ticks": 700,
    "creep_rows": 25987,
    "missing_chunks": 1,
    "already_in_db": 12273,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84385617, published_bases 84384900..84385500, "
        "reconstructed 84384901..84385600 missing_chunks=1 W47N8@84385300 inserted=13714 already_in_db=12273); "
        "34/35 official GETs 200. Prior 02:30 half-hour _halfhour_2026-11-21_0230 had official-filled 84384401..84385100 "
        "plus just-published 84385100 through 84385200, and 1h patrol _patrol_2026-11-21_0221 finished 02:30:03; "
        "this first pass overlapped those ticks and inserted the newly published 84385200..84385500 chunks "
        "plus the new freeze gap 84385301..84385599 (except W47N8@84385300 still 404). Not running concurrently with this backfill."
    ),
    "tick_s_printed": 4.236,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 3363,
    "corrective": int(tick.get("ts_realigned_to_later_mean") or 0),
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 2964},
        "W47N8": {"ticks": 600, "new": 5956},
        "W45N8": {"ticks": 700, "new": 1530},
        "W45N7": {"ticks": 700, "new": 1688},
        "W47N7": {"ticks": 700, "new": 1576},
    },
    "per_room_new_window": {
        r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS
    },
    "in_window_404_after_retry2": list(retry2_still or confirm_still or ["W47N8@84385300"]),
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": list(confirm_rec),
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
        f"post-counts actual_sum={actual_sum}{mismatch_s}"
        + (" All five ended 100/100." if jp_all_five else "")
    ),
    "new_box_freeze": {
        "from": "2026-11-21 02:45:59",
        "to": "2026-11-21 03:05:48",
        "sec": 1189,
        "why": "box frozen ~1189s since 2026-11-21 02:45:59 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "03:05:51",
        "listener_pid": 1631943,
        "listener_started": "03:06:00",
        "stats": "84385301..84385599",
        "span": 299,
        "last_stats": "84385300 at 02:45:43",
        "next_stats": "84385600 at 03:06:38",
        "official_fill": {r: gaps["gap_0245_0305"][r]["fill"] for r in ROOMS},
        "official_fill_missing": fill_0245,
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0300",
        "note": "NEW box freeze this window, already healed (listener auto-restarted, live.json fresh). Official-filled four rooms 299/299; W47N8 missing 84385301..84385400 from new official 404 W47N8@84385300. Fold only newer freezes than 02:45:59-03:05:48 after the next 1h patrol tells this one.",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": None,
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
        "filled_by": "1h patrol just-published 84384900 (short_fill 19/19 all five); reconfirmed by this first pass (reconstructed through 84385600).",
        "note": "Already told by the 02:28/02:30 patrol. Fully in window start 84384901. Official-filled 19/19 all five. Fold only newer short gaps than 02:20:54-02:22:17.",
    },
    "already_told_older_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-21 01:47:58",
        "to": "2026-11-21 02:02:50",
        "sec": 884,
        "why": "box frozen ~884s since 2026-11-21 01:47:58 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "02:02:53",
        "stats": "84384461..84384689",
        "span": 229,
        "last_stats": "84384460 at 01:47:24",
        "next_stats": "84384690 at 02:03:19",
        "official_fill": {r: (gaps.get("gap_0147_0202") or {}).get(r, {}).get("fill") for r in ROOMS},
        "official_fill_missing": fill_0147,
        "told": True,
        "told_by": "1h patrol ~02:28/02:30 Asia/Hong_Kong (_patrol_2026-11-21_0221)",
        "aged_out_of_window_start": 84384901,
        "note": "Already healed and already told by the 02:28/02:30 patrol. Ages out of window start 84384901. Official-filled 229/229 all five when last measured in-window.",
    },
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [
        {
            "room": "W47N8",
            "base": 84385300,
            "hole": "84385301..84385400",
            "fill": (lambda h: f"{h.get('distinct', 0)}/100" if isinstance(h, dict) else (h or "0/100"))(holes.get("W47N8@84385300") or {}),
            "confirm": f"{confirm_at} game.time={confirm_gt} still_404",
            "retry2": f"{retry2_at} game.time={retry2_gt} still_404",
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0300",
            "note": "NEW official 404 inside the NEW box-freeze STATS gap 84385301..84385599. Confirm and retry2 still 404. Other four rooms have this chunk. Fold only newer official 404s than W47N8@84385300 after the next 1h patrol tells this one.",
        }
    ],
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
        "aged out of window start 84384901 and were not retried here (already told by 1h patrol _patrol_2026-11-21_0124). "
        "Older already-told leftovers W45N7@84382700 (0/100), W46N8@84382900 (DB 67/100 missing 84382901..84382933), "
        "and W45N8@84382600 (0/100), plus W47N8@84382100, W47N7@84380900, W47N8@84380300, W47N8@84379500, W45N8@84378900, "
        "remain unfilled or listener-filled and were not retried here."
    ),
    "prior_told_box_freeze_aged_out": [
        {
            "from": "2026-11-21 01:47:58",
            "to": "2026-11-21 02:02:50",
            "sec": 884,
            "stats": "84384461..84384689",
            "span": 229,
            "official_fill": {r: (gaps.get("gap_0147_0202") or {}).get(r, {}).get("fill") for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0221",
            "aged_out_of_window_start": 84384901,
            "note": "Official-filled 229/229 all five when last measured in-window.",
        },
        {
            "from": "2026-11-21 01:10:46",
            "to": "2026-11-21 01:24:59",
            "sec": 846,
            "stats": "84383931..84384149",
            "span": 219,
            "official_fill": {r: (gaps.get("gap_0110_0124") or {}).get(r, {}).get("fill") for r in ROOMS},
            "official_fill_missing": fill_0110,
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0124",
            "aged_out_of_window_start": 84384901,
            "note": "W45N7 still missing 84383931..84384000 from official 404 W45N7@84383900; other four rooms 219/219.",
        },
        {
            "from": "2026-11-21 00:50:52",
            "to": "2026-11-21 00:57:30",
            "sec": 393,
            "stats": "84383651..84383759",
            "span": 109,
            "official_fill": "not re-queried this run (aged out of window start 84384901; previously 109/109 all five)",
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0124",
            "aged_out_of_window_start": 84384901,
            "note": "Still 109/109 all five when last measured.",
        },
        {
            "from": "2026-11-21 00:19:22",
            "to": "2026-11-21 00:22:38",
            "sec": 195,
            "stats": "84383131..84383249",
            "span": 119,
            "official_fill": "not re-queried this run (aged out of window start 84384901)",
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0022",
            "aged_out_of_window_start": 84384901,
            "note": "Combined with preceding no-STATS after 00:14:38. Previously 119/119 all five.",
        },
        {
            "from": "2026-11-20 23:50:34",
            "to": "2026-11-20 23:57:00",
            "sec": 385,
            "stats": "84382641..84382889",
            "span": 249,
            "official_fill": "not re-queried this run (aged out of window start 84384901)",
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0022",
            "aged_out_of_window_start": 84384901,
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
        "pid": 1631943,
        "started": "03:06:00",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "03:05:51 after NEW box freeze 02:45:59-03:05:48; listener.py 1631943 started 03:06:00",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "Listener auto-restarted after the NEW 02:45:59-03:05:48 box freeze and has been connected since 03:06:00 (live.json fresh, creep_cpu/path_arrivals ingesting). Single peacetime slot 5:5:1:1, no yield file. This run did not restart the listener or war_cmd/pulse.",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": {
        "id": "_patrol_2026-11-21_0221",
        "finished_at": "2026-11-21 02:30:03",
        "overlap_during_this_run": False,
        "note": "Finished about 35 minutes before this backfill started. Already official-filled 84384201..84384900 (700, missing_chunks=0, inserted=3001) and just-published 84384900 ticks 84384901..84385000 all_five_200=True (short_fill 19/19 all five).",
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
    if key not in gaps:
        return "  (not re-queried this run)"
    return "  " + "  ".join(
        f"{r} {gaps[key][r]['fill']}"
        + (f" missing {gaps[key][r]['missing_range']}" if gaps[key][r]["missing_n"] else "")
        for r in ROOMS
    )

g_0245 = gap_line("gap_0245_0305")
g_0220 = gap_line("gap_0220_0222")
g_0147 = gap_line("gap_0147_0202")
g_0110 = gap_line("gap_0110_0124")

win_lines = "\n".join(
    f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}"
    for r in ROOMS
)

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = "\n"
fill_0245_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0245.items())
    if fill_0245 else "; official-filled all five 299/299"
)
fill_0220_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0220.items())
    if fill_0220 else "; official-filled all five 19/19"
)
jp_all_s = f" All five ended 100/100." if jp_all_five else ""
confirm_txt = (
    f"confirm {confirm_at} game.time={confirm_gt} still_404 {confirm_still or ['W47N8@84385300']} inserted={inserted_confirm}; "
    f"retry2 {retry2_at} game.time={retry2_gt} still_404 {retry2_still or confirm_still} inserted={inserted_retry2}. "
    "Already-told leftover official 404s W45N7@84383500 (hole 84383501..84383600, 0/100) and W45N7@84383900 "
    "(hole 84383901..84384000, 0/100), plus older leftovers W45N7@84382700, W46N8@84382900, W45N8@84382600, "
    "aged out of window start 84384901 and were not retried here."
)
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
{confirm_txt}
tick_s_first={tick_s_first:.5f} printed=4.236 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=3363 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published {JUST_BASE} at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84385601..84385700; script inserted={script_sum}{mismatch_s}{jp_all_s}
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just {JUST_BASE} actual {actual_sum})
NEW box freeze 02:45:59-03:05:48 (~1189s; VM hibernated; listener auto-restart 03:05:51, python 1631943 started 03:06:00). STATS gap 84385301..84385599 (299t; last STATS 84385300 at 02:45:43, next 84385600 at 03:06:38){fill_0245_txt}. NEW official 404 W47N8@84385300 (hole 84385301..84385400, 0/100) remains after confirm and retry2. Already-told short listener gap 02:20:54-02:22:17 (STATS 84384941..84384959, 19t; listener auto-restart 02:22:00, python 1617878 started 02:22:09) is fully in window start 84384901 and remains already told by the 02:28/02:30 patrol{fill_0220_txt}. Already-told freeze 01:47:58-02:02:50 (STATS 84384461..84384689, 229t) aged out of window start 84384901, as did already-told freeze 01:10:46-01:24:59 (STATS 84383931..84384149, 219t; W45N7 still missing 84383931..84384000 from official 404 W45N7@84383900), already-told freeze 00:50:52-00:57:30 (STATS 84383651..84383759, 109t) and already-told 00:14:38 no-STATS + 00:19:22-00:22:38 freeze (STATS 84383131..84383249, 119t). Prior 1h patrol _patrol_2026-11-21_0221 finished 02:30:03 and is not concurrent with this run. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_0300.txt")

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 W47N8@84385300 reconstructed 84384901..84385600 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84385601..84385700 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{nl.join(jp_lines)}
gap_0245_0305 STATS 84385301..84385599 (299) NEW box freeze 02:45:59-03:05:48 (~1189s); listener auto-restart 03:05:51, python 1631943 started 03:06:00
{g_0245}
gap_0220_0222 STATS 84384941..84384959 (19) already-told by 02:28/02:30 patrol (short listener gap 02:20:54-02:22:17)
{g_0220}
gap_0147_0202 STATS 84384461..84384689 (229) already-told by 02:28/02:30 patrol (box freeze 01:47:58-02:02:50); aged out of window start 84384901
{g_0147}
gap_0110_0124 STATS 84383931..84384149 (219) already-told by 01:33 patrol (box freeze 01:10:46-01:24:59); aged out of window start 84384901
{g_0110}
aged-out already-told official 404 W45N7@84383500 0/100, W45N7@84383900 0/100, W45N7@84382700 0/100, W46N8@84382900 67/100, W45N8@84382600 0/100 (not retried)
NEW official 404 W47N8@84385300 0/100 (hole 84385301..84385400) still 404 after confirm and retry2
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.236 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)} ts_realigned_first=3363
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1631943 started=03:06:00 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
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
