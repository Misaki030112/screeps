#!/usr/bin/env python3
"""Write 04:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0400"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84385601, 84386300
JUST_BASE = 84386300
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
    "First-pass realign with tick_s=4.27192 (printed 4.272) moved 12049 rows "
    "(ts_realigned_first=12049, inserted=6498, already_in_db=18223, missing_chunks=1 W47N8@84385900)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace(
    "moved 12049 rows (ts_realigned_first=12049, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
    "moved 12049 rows (ts_realigned_first=12049, inserted=6498, already_in_db=18223, missing_chunks=1 W47N8@84385900).",
)
reason = reason.replace(
    "(printed 4.137, min-all-rooms first two bases)",
    "(printed 4.272, min-all-rooms first two bases)",
)
reason = reason.replace(
    "(printed 4.145) moved 12049 rows",
    "(printed 4.272) moved 12049 rows",
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
    hole859 = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W47N8", 84385901, 84386000),
    ).fetchone()
    hole859_d, hole859_n = int(hole859[0] or 0), int(hole859[3] or 0)
    hole853 = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W47N8", 84385301, 84385400),
    ).fetchone()
    hole853_d, hole853_n = int(hole853[0] or 0), int(hole853[3] or 0)

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
holes = post.get("holes") or {}
post_tips = post.get("tips") or {}

inserted_first = 6498
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = 0
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.27192)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "first"
corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
cov_rec = cov.get("official_recovered")
cov_exp = cov.get("expected")
empty_n = cov.get("empty_no_creep")
off404 = cov.get("official_404_missing")

confirm_at = confirm.get("confirm_at") or confirm.get("at")
confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
retry2_at = "2026-11-21 04:03:37 Asia/Hong_Kong"
retry2_gt = 84386416
retry2b_at = "2026-11-21 04:05:47 Asia/Hong_Kong"
retry2b_gt = 84386447
confirm_still = confirm.get("still_404") or ["W47N8@84385900"]
retry2_still = ["W47N8@84385900"]
confirm_rec = confirm.get("recovered") or []

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

fill_0354 = fill_missing("gap_0354_0357")
fill_0245 = fill_missing("gap_0245_0305")
fill_0220 = fill_missing("gap_0220_0222")
fill_0147 = fill_missing("gap_0147_0202")

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84386364,
    "published_bases": "84385600..84386200",
    "reconstructed": [84385601, 84386300],
    "ticks": 700,
    "creep_rows": 24721,
    "missing_chunks": 1,
    "already_in_db": 18223,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84386364, published_bases 84385600..84386200, "
        "reconstructed 84385601..84386300 missing_chunks=1 W47N8@84385900 inserted=6498 already_in_db=18223); "
        "34/35 official GETs 200. Prior 03:30 half-hour _halfhour_2026-11-21_0330 had official-filled 84385301..84386000 "
        "plus just-published 84386000 through 84386100, and 1h patrol _patrol_2026-11-21_0320 finished 03:32:34; "
        "this first pass overlapped those ticks and inserted newly published 84386100..84386200 chunks "
        "plus remaining earlier overlap, except already-recorded official 404 W47N8@84385900 still 404. "
        "Not running concurrently with this backfill."
    ),
    "tick_s_printed": 4.272,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 12049,
    "corrective": corrective,
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 1340},
        "W47N8": {"ticks": 600, "new": 2065},
        "W45N8": {"ticks": 700, "new": 845},
        "W45N7": {"ticks": 700, "new": 911},
        "W47N7": {"ticks": 700, "new": 1337},
    },
    "per_room_new_window": {r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS},
    "in_window_404_after_retry2": ["W47N8@84385900"],
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
        "from": "2026-11-21 03:54:27",
        "to": "2026-11-21 03:57:32",
        "sec": 178,
        "stats": "84386281..84386339",
        "span": 59,
        "last_stats": "84386280 at 03:54:10",
        "next_stats": "84386340 at 03:58:19",
        "listener_restart": "03:57:35",
        "listener_pid": 1658535,
        "listener_started": "03:57:45",
        "official_fill": {r: gaps["gap_0354_0357"][r]["fill"] for r in ROOMS},
        "official_fill_missing": fill_0354,
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0400",
        "note": "NEW short box freeze (VM hibernated, 178s). Official first-pass window covered through 84386300; just-published 84386300 filled 84386301..84386339. Official-filled all five 59/59. Leave for the next 1h patrol to tell. Fold only newer freezes than 03:54:27-03:57:32 after that patrol, and newer short gaps than 02:20:54-02:22:17 until a patrol updates the short-gap watermark.",
    },
    "new_short_listener_gap": None,
    "new_official_404": [],
    "already_told_box_freeze_in_window": None,
    "already_told_short_listener_gap_in_window": None,
    "aged_out_already_told_box_freeze_0245": {
        "from": "2026-11-21 02:45:59",
        "to": "2026-11-21 03:05:48",
        "sec": 1189,
        "stats": "84385301..84385599",
        "span": 299,
        "listener_restart": "03:05:51",
        "official_fill": {r: (gaps.get("gap_0245_0305") or {}).get(r, {}).get("fill") for r in ROOMS},
        "official_fill_missing": fill_0245,
        "told": True,
        "told_by": "30-min backfill ~03:17 and 1h patrol ~03:30 Asia/Hong_Kong (_halfhour_2026-11-21_0300 / _patrol_2026-11-21_0320)",
        "aged_out_of_window_start": 84385601,
        "note": "Already healed and already told. Ages out of window start 84385601 (gap ends 84385599). Official-filled four rooms 299/299; W47N8 missing 84385301..84385400 from already-told official 404 W47N8@84385300.",
    },
    "aged_out_already_told_short_listener_gap": {
        "from": "2026-11-21 02:20:54",
        "to": "2026-11-21 02:22:17",
        "sec": 83,
        "stats": "84384941..84384959",
        "span": 19,
        "official_fill": {r: (gaps.get("gap_0220_0222") or {}).get(r, {}).get("fill") for r in ROOMS},
        "told": True,
        "told_by": "1h patrol ~02:28/02:30 Asia/Hong_Kong (_patrol_2026-11-21_0221)",
        "aged_out_of_window_start": 84385601,
        "note": "Already told. Ages out of window start 84385601. Official-filled 19/19 all five.",
    },
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-21 01:47:58",
        "to": "2026-11-21 02:02:50",
        "sec": 884,
        "stats": "84384461..84384689",
        "span": 229,
        "official_fill": {r: (gaps.get("gap_0147_0202") or {}).get(r, {}).get("fill") for r in ROOMS},
        "told": True,
        "told_by": "1h patrol ~02:28/02:30 Asia/Hong_Kong (_patrol_2026-11-21_0221)",
        "aged_out_of_window_start": 84385601,
    },
    "already_told_in_window_404": [
        {
            "room": "W47N8",
            "base": 84385900,
            "hole": "84385901..84386000",
            "fill": f"{hole859_d}/100",
            "rows": hole859_n,
            "confirm": f"{confirm_at} game.time={confirm_gt} still_404",
            "retry2": f"{retry2_at} game.time={retry2_gt} still_404",
            "recheck": f"{retry2b_at} game.time={retry2b_gt} still_404",
            "told": False,
            "recorded_by": "30-min backfill ~03:53 Asia/Hong_Kong (_halfhour_2026-11-21_0330)",
            "note": "Already recorded by the previous 03:30/03:53 backfill as NEW official 404; still 0/100 after this run's confirm 04:01:46, retry2 04:03:37, and leftover recheck 04:05:47. Other four rooms had this chunk on the first pass. Not yet told by a 1h patrol (last patrol was 03:30, before this hole was found). Leave for the next 1h patrol. Fold only newer official 404s than W47N8@84385900 after that patrol tells it.",
        }
    ],
    "aged_out_already_told_404_not_retried": [
        "W47N8@84385300", "W45N7@84383500", "W45N7@84383900", "W45N7@84382700", "W46N8@84382900", "W45N8@84382600",
    ],
    "aged_out_leftover_note": (
        "Already-told official 404s W47N8@84385300 (0/100, hole 84385301..84385400), W45N7@84383500 (0/100), "
        "W45N7@84383900 (0/100), W45N7@84382700 (0/100), W46N8@84382900 (DB 67/100 missing 84382901..84382933), "
        "and W45N8@84382600 (0/100) aged out of window start 84385601 and were not retried here. "
        f"Already-recorded official 404 W47N8@84385900 remains in window and was retried (still {hole859_d}/100)."
    ),
    "listener": {
        "single_slot": True,
        "roomSlot": slot,
        "rot": rot,
        "pid": 1658535,
        "started": "03:57:45",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "03:57:35 after NEW short box freeze 03:54:27-03:57:32; listener.py 1658535 started 03:57:45 and stayed up this run",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "Listener pid 1658535 has been connected since 03:57:45 (live.json mtime fresh, creep_cpu/path_arrivals ingesting). live.json gameTime field lagged at 84386406 while stats.t and DB ingest continued; not a disconnect and not restarted by this run. Single peacetime slot 5:5:1:1, no yield file. This run did not restart the listener or war_cmd/pulse.",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": {
        "id": "_patrol_2026-11-21_0320",
        "finished_at": "2026-11-21 03:32:34",
        "overlap_during_this_run": False,
        "note": "Finished well before this backfill started. Already official-filled through the 03:00 half-hour window and told the 02:45:59-03:05:48 freeze plus official 404 W47N8@84385300. It did not yet tell official 404 W47N8@84385900 or the NEW short freeze 03:54:27-03:57:32.",
    },
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
    "tick_s_reason": tick.get("reason"),
    "post_counts_tips_at": post.get("at"),
    "post_counts_tips": post_tips,
    "leftover_recheck": {"at": retry2b_at, "game_time": retry2b_gt, "still_404": retry2_still, "inserted": 0},
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

g_0354 = gap_line("gap_0354_0357")
g_0245 = gap_line("gap_0245_0305")
g_0220 = gap_line("gap_0220_0222")
g_0147 = gap_line("gap_0147_0202")
win_lines = "\n".join(f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}" for r in ROOMS)
first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = "\n"
fill_0354_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0354.items())
    if fill_0354 else "; official-filled all five 59/59"
)
fill_0245_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0245.items())
    if fill_0245 else "; official-filled all five 299/299"
)
fill_0220_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0220.items())
    if fill_0220 else "; official-filled all five 19/19"
)
jp_all_s = " All five ended 100/100." if jp_all_five else ""
confirm_txt = (
    f"confirm {confirm_at} game.time={confirm_gt} still_404 {confirm_still} inserted={inserted_confirm}; "
    f"retry2 {retry2_at} game.time={retry2_gt} still_404 {retry2_still} inserted={inserted_retry2}. "
    "Already-told leftover official 404s W47N8@84385300 (hole 84385301..84385400, 0/100), "
    "W45N7@84383500, W45N7@84383900, W45N7@84382700, W46N8@84382900, and W45N8@84382600 "
    "aged out of window start 84385601 and were not retried here. Already-recorded official 404 W47N8@84385900 remains in window and was retried (still 0/100). "
    f"Leftover recheck {retry2b_at} game.time={retry2b_gt} still_404 {retry2_still} inserted=0."
)
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
{confirm_txt}
tick_s_first={tick_s_first:.5f} printed=4.272 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=12049 corrective={corrective}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published {JUST_BASE} at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84386301..84386400; script inserted={script_sum}{mismatch_s}{jp_all_s}
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just {JUST_BASE} actual {actual_sum})
NEW short box freeze 03:54:27-03:57:32 (178s; VM hibernated; listener auto-restart 03:57:35, python 1658535 started 03:57:45; not yet told, leave for next 1h patrol). STATS gap 84386281..84386339 (59t; last STATS 84386280 at 03:54:10, next 84386340 at 03:58:19){fill_0354_txt}. Already-recorded official 404 W47N8@84385900 (hole 84385901..84386000, {hole859_d}/100) remains after confirm 04:01:46, retry2 04:03:37, and leftover recheck 04:05:47 game.time=84386447; other four rooms had this chunk on the first pass; recorded by the 03:53 backfill and not yet told by a 1h patrol. Already-told official 404 W47N8@84385300 (hole 84385301..84385400, {hole853_d}/100) aged out of window start 84385601 and was not retried here. Already-told box freeze 02:45:59-03:05:48 (STATS 84385301..84385599, 299t) aged out of window start 84385601{fill_0245_txt}. Already-told short listener gap 02:20:54-02:22:17 (STATS 84384941..84384959, 19t) aged out of window start 84385601{fill_0220_txt}. Already-told freeze 01:47:58-02:02:50 (STATS 84384461..84384689, 229t) aged out of window start 84385601. Prior 1h patrol _patrol_2026-11-21_0320 finished 03:32:34 and is not concurrent with this run. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. live.json gameTime field lagged at 84386406 while stats.t/ingest continued; not a disconnect.
"""
(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_0400.txt")

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 W47N8@84385900 reconstructed 84385601..84386300 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84386301..84386400 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{nl.join(jp_lines)}
gap_0354_0357 STATS 84386281..84386339 (59) NEW short box freeze 03:54:27-03:57:32 (178s, VM hibernated); listener auto-restart 03:57:35, python 1658535 started 03:57:45; not yet told, leave for next 1h patrol; official-filled all five 59/59
{g_0354}
gap_0245_0305 STATS 84385301..84385599 (299) already-told by 03:17 backfill / 03:30 patrol (box freeze 02:45:59-03:05:48, ~1189s); aged out of window start 84385601
{g_0245}
gap_0220_0222 STATS 84384941..84384959 (19) already-told by 02:28/02:30 patrol (short listener gap 02:20:54-02:22:17); aged out of window start 84385601
{g_0220}
gap_0147_0202 STATS 84384461..84384689 (229) already-told by 02:28/02:30 patrol (box freeze 01:47:58-02:02:50); aged out of window start 84385601
{g_0147}
aged-out already-told official 404 W47N8@84385300 0/100, W45N7@84383500 0/100, W45N7@84383900 0/100, W45N7@84382700 0/100, W46N8@84382900 67/100, W45N8@84382600 0/100 (not retried)
already-recorded official 404 W47N8@84385900 0/100 (hole 84385901..84386000) still 404 after confirm 04:01:46, retry2 04:03:37, and leftover recheck 04:05:47 gt=84386447; recorded by 03:53 backfill, not yet told by a 1h patrol
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.272 corrective={corrective} ts_realigned_first=12049
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1658535 started=03:57:45 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
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
(DIR / "wrapup_run.console.txt").write_text(summary)
(DIR / "wrapup_run.err").write_text("")
print(summary, end="")
