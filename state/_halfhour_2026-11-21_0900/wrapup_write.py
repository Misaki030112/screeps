#!/usr/bin/env python3
"""Write 09:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0900"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84389901, 84390600
JUST_BASE = 84390600
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")


def _load(name, default=None):
    path = DIR / name
    if path.exists():
        return json.loads(path.read_text())
    if default is not None:
        return default
    raise FileNotFoundError(path)

tick = _load("tick_s_realign.json")
cov = _load("coverage_final.json")
post = _load("just_published_post_summary.json")
confirm = _load("backfill_confirm_gets.json", {"skipped": True, "still_404": [], "inserted": 0, "recovered": [], "at": None, "game_time": None})
retry2j = _load("backfill_retry2_gets.json", {"skipped": True, "still_404": [], "inserted": 0, "recovered": [], "at": None, "game_time": None})
jp = _load(f"just_published_{JUST_BASE}.json")
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

want_err = (
    "First-pass realign with tick_s=4.27697 (printed 4.277) moved 0 rows "
    "(ts_realigned_first=0, inserted=4278, already_in_db=20302, missing_chunks=4 "
    "W46N8@84390400, W47N8@84390500, W45N8@84390500, W47N7@84390500)."
)
tick["ts_realigned_first_pass_error"] = want_err
reason = tick.get("reason") or ""
reason = reason.replace(
    "First-pass realign with tick_s=4.27697 (printed 4.145) moved 0 rows (ts_realigned_first=0, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
    want_err,
)
reason = reason.replace(
    "First-pass realign with tick_s=4.26327 (printed 4.145) moved 0 rows (ts_realigned_first=0, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
    want_err,
)
reason = reason.replace("(printed 4.137, min-all-rooms first two bases)", "(printed 4.277, min-all-rooms first two bases)")
reason = reason.replace("(printed 4.145, min-all-rooms first two bases)", "(printed 4.277, min-all-rooms first two bases)")
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

    def hole(room, a, b):
        row = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, a, b),
        ).fetchone()
        return int(row[0] or 0), int(row[3] or 0), row[1], row[2]

    hole885_d, hole885_n, hole885_mn, hole885_mx = hole("W45N7", 84388501, 84388600)
    hole864_d, hole864_n, hole864_mn, hole864_mx = hole("W46N8", 84386401, 84386500)
    hole866_d, hole866_n, hole866_mn, hole866_mx = hole("W45N8", 84386601, 84386700)
    hole859_d, hole859_n, hole859_mn, hole859_mx = hole("W47N8", 84385901, 84386000)
    hole853_d, hole853_n, hole853_mn, hole853_mx = hole("W47N8", 84385301, 84385400)
    hole904_d, hole904_n, hole904_mn, hole904_mx = hole("W46N8", 84390401, 84390500)
    conf_w47n8_d, conf_w47n8_n, conf_w47n8_mn, conf_w47n8_mx = hole("W47N8", 84390501, 84390600)
    conf_w45n8_d, conf_w45n8_n, conf_w45n8_mn, conf_w45n8_mx = hole("W45N8", 84390501, 84390600)
    conf_w47n7_d, conf_w47n7_n, conf_w47n7_mn, conf_w47n7_mx = hole("W47N7", 84390501, 84390600)

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
holes = post.get("holes") or {}
post_tips = post.get("tips") or {}

inserted_first = 4278
inserted_confirm = int(confirm.get("inserted") or 0)
retry2_blob = retry2j.get("retry2") or {}
inserted_retry2 = int(retry2j.get("retry2_inserted") or retry2_blob.get("inserted") or 0)
confirm_at = confirm.get("confirm_at") or confirm.get("at")
confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
confirm_still = list(confirm.get("still_404") or [])
confirm_rec = list(confirm.get("recovered") or [])
retry2_at = retry2j.get("retry2_at") or retry2_blob.get("at")
retry2_gt = retry2j.get("retry2_game_time") or retry2_blob.get("game_time")
retry2_still = list(retry2j.get("retry2_still_404") or retry2_blob.get("still_404") or [])
retry2_rec = list(retry2j.get("retry2_recovered") or retry2_blob.get("recovered") or [])
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or tick.get("tick_s_used_first_pass") or 4.27697)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "all_mean"
corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
cov_rec = cov.get("official_recovered")
cov_exp = cov.get("expected")
empty_n = cov.get("empty_no_creep")
off404 = cov.get("official_404_missing")

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
script_parts = ", ".join(f"{r} +{script_by[r]}" for r in ROOMS)
mismatch_s = ("; " + ", ".join(script_mismatch) + ". ") if script_mismatch else ". "


def fill_missing(gap_key):
    out = {}
    g = gaps.get(gap_key) or {}
    for r in ROOMS:
        rec = g.get(r) or {}
        if rec.get("missing_n"):
            out[r] = f"{rec.get('missing_range')} ({rec.get('missing_n')})"
    return out

fill_0852 = fill_missing("gap_0852_0856")
fill_0818 = fill_missing("gap_0818_0823")
fill_0743 = fill_missing("gap_0743_0801")
fill_0722 = fill_missing("gap_0722_0725")
fill_0642 = fill_missing("gap_0642_0704")
fill_0634 = fill_missing("gap_0634_0637")
fill_0619 = fill_missing("gap_0619_0622")
fill_0542 = fill_missing("gap_0542_0601")

new_box_freeze = {
    "from": "2026-11-21 08:52:35",
    "to": "2026-11-21 08:56:43",
    "sec": 248,
    "stats": "84390511..84390579",
    "span": 69,
    "last_stats": "84390510 at 08:52:16",
    "next_stats": "84390580 at 08:57:09",
    "listener_restart": "08:56:46",
    "listener_pid": 1772825,
    "listener_started": "08:56:56",
    "official_fill": {r: (gaps.get("gap_0852_0856") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_0852,
    "told": False,
    "first_recorded_by": "09:00 half-hour backfill",
    "note": "NEW box freeze this run, not yet told by a 1h patrol. STATS gap 69t. Official 84390500 first-pass 200 for W46N8/W45N7, 404 for W47N8/W45N8/W47N7 recovered on confirm. Leave telling to the next 1h patrol. Do not restart the listener.",
}

already_told_freeze_0818 = {
    "from": "2026-11-21 08:18:49",
    "to": "2026-11-21 08:23:57",
    "sec": 299,
    "stats": "84390031..84390119",
    "span": 89,
    "last_stats": "84390030 at 08:18:24",
    "next_stats": "84390120 at 08:24:47",
    "listener_restart": "08:24:00",
    "listener_pid": 1755023,
    "listener_started": "08:24:09",
    "official_fill": {r: (gaps.get("gap_0818_0823") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_0818,
    "told": True,
    "told_by": "08:32 1h patrol",
    "note": "Already told by the 08:32 1h patrol. Official-filled all five 89/89 (08:30/08:48 half-hour official 84390100 filled the former unpublished tail). Still in official window start 84389901. Do not re-tell.",
}

new_official_404 = [{
    "chunk": "W46N8@84390400",
    "hole": "84390401..84390441",
    "missing_n": 41,
    "listener": "84390442..84390500",
    "listener_n": 59,
    "distinct": hole904_d,
    "rows": hole904_n,
    "range": None if hole904_mn is None else f"{hole904_mn}..{hole904_mx}",
    "told": False,
    "first_recorded_by": "09:00 half-hour backfill",
    "still_404_after": ["confirm 09:00:36 gt=84390629", "retry2 09:01:07 gt=84390636"],
    "note": "NEW leftover official 404 this run, not yet told by a 1h patrol. First-pass, confirm, and retry2 all 404. Listener already has 59/100 ticks 84390442..84390500; hole 84390401..84390441 (41). Leave telling to the next 1h patrol.",
}]

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84390603,
    "published_bases": "84389900..84390500",
    "reconstructed": [84389901, 84390600],
    "ticks": 700,
    "creep_rows": 24580,
    "missing_chunks": 4,
    "already_in_db": 20302,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this 09:00 half-hour routine ran tools/history_backfill.py --minutes 40 "
        "(game.time=84390603, published_bases 84389900..84390500, reconstructed 84389901..84390600 "
        "missing_chunks=4 W46N8@84390400, W47N8@84390500, W45N8@84390500, W47N7@84390500 "
        "inserted=4278 already_in_db=20302); 31/35 official GETs 200. "
        "Confirm 09:00:35 gt=84390629 recovered W47N8@84390500, W45N8@84390500, W47N7@84390500 "
        f"(script inserted={inserted_confirm}); still_404=['W46N8@84390400']. "
        f"retry2 09:01:06 gt=84390636 still_404=['W46N8@84390400'], inserted={inserted_retry2} "
        "(W45N8 extra on the recovered 84390500 chunk). "
        "Prior 08:30/08:48 half-hour official-filled 84389601..84390300 plus just-published 84390300 actual 2218."
    ),
    "tick_s_printed": 4.277,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 0,
    "corrective": corrective,
    "corrective_note": "no corrective realign; live-anchor-best all_mean 4.23770 already inside 45s gate (over45=0 mean_off=-1.3); later-mean-robust 4.22788 is worse (over45=0 mean_off=-5.4); first-interval 4.27697 over45=0 mean_off=14.8",
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 600, "new": 956},
        "W47N8": {"ticks": 600, "new": 1540},
        "W45N8": {"ticks": 600, "new": 430},
        "W45N7": {"ticks": 700, "new": 706},
        "W47N7": {"ticks": 600, "new": 646},
    },
    "per_room_new_window": {r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS},
    "in_window_404_after_retry2": ["W46N8@84390400"],
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
        + (" All five ended 100/100." if jp_all_five else " Not all five 100/100.")
    ),
    "new_box_freeze": new_box_freeze,
    "new_short_listener_gap": None,
    "new_official_404": new_official_404,
    "prior_untold_box_freeze_in_window": None,
    "already_told_official_404_in_window": {},
    "already_told_box_freeze_in_window": already_told_freeze_0818,
    "already_told_box_freeze_0743_in_window": None,
    "already_told_short_listener_gap_in_window": None,
    "aged_out_already_told_box_freeze_0743": {
        "from": "2026-11-21 07:43:15",
        "to": "2026-11-21 08:01:01",
        "sec": 1056,
        "stats": "84389531..84389789",
        "span": 259,
        "official_fill": {r: (gaps.get("gap_0743_0801") or {}).get(r, {}).get("fill") for r in ROOMS},
        "official_fill_missing": fill_0743,
        "told": True,
        "told_by": "08:32 1h patrol",
        "first_recorded_by": "08:00/08:14 half-hour backfill",
        "note": "aged out of window start 84389901; official-filled all five 259/259",
    },
    "aged_out_already_told_box_freeze_0722": {
        "from": "2026-11-21 07:22:15",
        "to": "2026-11-21 07:25:56",
        "sec": 214,
        "stats": "84389231..84389299",
        "span": 69,
        "official_fill_missing": fill_0722,
        "told": True,
        "told_by": "07:37 1h patrol",
        "note": "aged out of window start 84389901; official-filled all five 69/69",
    },
    "aged_out_already_told_box_freeze_0642": {
        "from": "2026-11-21 06:42:51",
        "to": "2026-11-21 07:04:46",
        "sec": 1315,
        "stats": "84388671..84388999",
        "span": 329,
        "official_fill_missing": fill_0642,
        "told": True,
        "told_by": "07:37 1h patrol",
        "note": "aged out of window start 84389901; official-filled all five 329/329",
    },
    "aged_out_already_told_short_gap_0634": {
        "from": "2026-11-21 06:34:33",
        "to": "2026-11-21 06:37:21",
        "stats": "84388561..84388599",
        "span": 39,
        "official_fill_missing": fill_0634,
        "told": True,
        "told_by": "07:37 1h patrol",
        "note": "Aged out of window start 84389901. W45N7 missing because already-told leftover official 404 W45N7@84388500.",
    },
    "aged_out_already_told_box_freeze_0619": {
        "from": "2026-11-21 06:19:18",
        "to": "2026-11-21 06:22:57",
        "sec": 218,
        "stats": "84388331..84388399",
        "span": 69,
        "official_fill_missing": fill_0619,
        "told": True,
        "told_by": "06:33 1h patrol",
        "note": "aged out of window start 84389901; official-filled all five 69/69",
    },
    "aged_out_already_told_box_freeze_0542": {
        "from": "2026-11-21 05:42:11",
        "to": "2026-11-21 06:01:46",
        "sec": 1169,
        "stats": "84387811..84388109",
        "span": 299,
        "official_fill_missing": fill_0542,
        "told": True,
        "told_by": "06:33 1h patrol",
        "note": "aged out of window start 84389901; official-filled all five 299/299",
    },
    "aged_out_leftover_official_404s": {
        "W45N7@84388500": {
            "hole": "84388501..84388600",
            "distinct": hole885_d,
            "rows": hole885_n,
            "range": None if hole885_mn is None else f"{hole885_mn}..{hole885_mx}",
            "told": True,
            "told_by": "07:37 1h patrol",
            "first_recorded_by": "07:00/07:18 half-hour backfill",
            "note": "Already told by the 07:37 1h patrol (still 404 after later retries; hole 84388501..84388600, 0/100). Aged out of window start 84389901 and was not retried here.",
        },
        "W45N8@84386600": {"hole": "84386601..84386700", "distinct": hole866_d, "rows": hole866_n, "range": None if hole866_mn is None else f"{hole866_mn}..{hole866_mx}", "told_by": "04:18/04:29 1h patrol", "note": "listener 84386657..84386683; aged out of window start 84389901 and not retried here"},
        "W46N8@84386400": {"hole": "84386401..84386500", "distinct": hole864_d, "rows": hole864_n, "range": None if hole864_mn is None else f"{hole864_mn}..{hole864_mx}", "told_by": "04:18/04:29 1h patrol", "note": "listener 84386401..84386406"},
        "W47N8@84385900": {"hole": "84385901..84386000", "distinct": hole859_d, "rows": hole859_n, "told_by": "04:18/04:29 1h patrol"},
        "W47N8@84385300": {"hole": "84385301..84385400", "distinct": hole853_d, "rows": hole853_n, "told": True},
        "W45N7@84383500": {"distinct": (holes.get("W45N7@84383500") or {}).get("distinct"), "told": True},
        "W45N7@84383900": {"distinct": (holes.get("W45N7@84383900") or {}).get("distinct"), "told": True},
        "W45N8@84382600": {"distinct": (holes.get("W45N8@84382600") or {}).get("distinct"), "told": True},
        "W45N7@84382700": {"distinct": (holes.get("W45N7@84382700") or {}).get("distinct"), "told": True},
        "W46N8@84382900": {"distinct": (holes.get("W46N8@84382900") or {}).get("distinct"), "told": True},
    },
    "confirm": {
        "at": confirm_at,
        "game_time": confirm_gt,
        "still_404": confirm_still,
        "inserted": inserted_confirm,
        "recovered": confirm_rec,
        "skipped": False,
        "reason": (
            f"recovered W47N8@84390500, W45N8@84390500, W47N7@84390500; script inserted={inserted_confirm}; "
            f"still_404=['W46N8@84390400']; "
            f"db W47N8 {conf_w47n8_d}/100 rows={conf_w47n8_n} {conf_w47n8_mn}..{conf_w47n8_mx}; "
            f"W45N8 {conf_w45n8_d}/100 rows={conf_w45n8_n} {conf_w45n8_mn}..{conf_w45n8_mx}; "
            f"W47N7 {conf_w47n7_d}/100 rows={conf_w47n7_n} {conf_w47n7_mn}..{conf_w47n7_mx}; "
            f"W46N8@84390400 {hole904_d}/100 rows={hole904_n} {hole904_mn}..{hole904_mx} (listener 59 ticks 84390442..84390500, hole 84390401..84390441)"
        ),
    },
    "retry2": {
        "at": retry2_at,
        "game_time": retry2_gt,
        "still_404": retry2_still,
        "inserted": inserted_retry2,
        "recovered": retry2_rec,
        "skipped": False,
        "reason": f"re-checked confirm recoveries and leftover W46N8@84390400; still_404=['W46N8@84390400']; inserted={inserted_retry2} (W45N8 extra on 84390500); no aged-out leftovers retried",
    },
    "leftover_recheck": {
        "at": retry2_at,
        "game_time": retry2_gt,
        "still_404": ["W46N8@84390400"],
        "inserted": 0,
        "skipped": False,
        "reason": "in-window leftover W46N8@84390400 still 404 after confirm and retry2; already-told leftover official 404 W45N7@84388500 aged out of window start 84389901 and was not retried",
    },
    "tips": tips,
    "post_tips": post_tips,
    "slot": slot,
    "rot": rot,
    "yield_absent": yield_absent,
    "listener_pid": 1772825,
    "listener_started": "08:56:56",
    "listener_restart": "08:56:46",
    "restarted_this_run": False,
    "prior_halfhour": "_halfhour_2026-11-21_0830 finished 08:48; official through 84390300 + just-published 84390300 actual 2218; no NEW leftover official 404; already-told freezes through 08:18:49-08:23:57",
    "prior_1h_patrol": "_patrol_2026-11-21_0825 finished 08:34:10, delivered ~08:32/~08:34 Asia/Hong_Kong; official-filled 84389401..84390100 missing_chunks=0 all five 700/700; first-told box freezes 07:43:15-08:01:01 and 08:18:49-08:23:57; leftover official 404 W45N7@84388500 remains already told. Do not re-tell those freezes or that leftover 404.",
    "fold_only_newer_official_404s_than": ["W46N8@84390400"],
    "fold_only_newer_freezes_than": "08:52:35-08:56:43",
    "fold_only_newer_short_gaps_than": "06:34:33-06:37:21",
}

prev = ROOT / "state" / "history_backfill.json"
if prev.exists():
    shutil.copy2(prev, ROOT / "state" / "history_backfill.prev.json")
(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
shutil.copy2(DIR / "history_backfill.json", prev)


def gap_line(key):
    if key not in gaps:
        return "  (no post_counts for this gap)"
    return "  " + "  ".join(
        f"{r} {(gaps[key].get(r) or {}).get('fill')}" + (
            f" missing {(gaps[key].get(r) or {}).get('missing_range')} ({(gaps[key].get(r) or {}).get('missing_n')})"
            if (gaps[key].get(r) or {}).get("missing_n") else ""
        )
        for r in ROOMS
    )

g_0852 = gap_line("gap_0852_0856")
g_0818 = gap_line("gap_0818_0823")
g_0743 = gap_line("gap_0743_0801")
g_0722 = gap_line("gap_0722_0725")
g_0642 = gap_line("gap_0642_0704")
g_0634 = gap_line("gap_0634_0637")
g_0619 = gap_line("gap_0619_0622")
g_0542 = gap_line("gap_0542_0601")
win_lines = "\n".join(f"  {r} distinct={win[r]['distinct']} rows={win[r]['rows']} {win[r]['min']}..{win[r]['max']}" for r in ROOMS)
post_counts = _load("just_published_post_counts.json", {})
jp_lines = [f"  {r} actual={actual_by[r]} script={script_by[r]} distinct={(post_counts.get(r) or {}).get('distinct')} rows={(post_counts.get(r) or {}).get('rows')}" for r in ROOMS]

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + "\n"
ended = "All five ended 100/100." if jp_all_five else "Not all five 100/100."
wrap_txt = first_txt + f"""
---- wrap {now_s} ----
confirm at {confirm_at} game.time={confirm_gt} still_404={confirm_still} inserted={inserted_confirm} recovered W47N8@84390500, W45N8@84390500, W47N7@84390500; retry2 at {retry2_at} game.time={retry2_gt} still_404={retry2_still} inserted={inserted_retry2} (re-checked recoveries; W45N8 extra on 84390500). First pass 31/35 official GETs 200, missing_chunks=4 W46N8@84390400, W47N8@84390500, W45N8@84390500, W47N7@84390500; the three 84390500 chunks recovered on confirm; W46N8@84390400 still 404 after retry2 (listener 59/100 ticks 84390442..84390500, hole 84390401..84390441, {hole904_d}/100). Already-told leftover official 404 W45N7@84388500 (first recorded by the 07:00/07:18 half-hour, first told by the 07:37 1h patrol, hole 84388501..84388600, {hole885_d}/100) aged out of window start 84389901 and was not retried here. Already-told leftover official 404s W47N8@84385300 (hole 84385301..84385400, {hole853_d}/100), W45N7@84383500, W45N7@84383900, W45N7@84382700, W46N8@84382900, W45N8@84382600, W47N8@84385900 (hole 84385901..84386000, {hole859_d}/100; first told by the 04:18/04:29 1h patrol), W46N8@84386400 (hole 84386401..84386500, {hole864_d}/100, listener 84386401..84386406), and W45N8@84386600 (hole 84386601..84386700, {hole866_d}/100, listener 84386657..84386683; first told by the 04:18/04:29 1h patrol) also aged out of window start 84389901 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.277 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={corrective}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published {JUST_BASE} at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84390601..84390700; script inserted={script_sum}{mismatch_s}{ended}
inserted_window={inserted_window} inserted_total={inserted_total} (first 4278 + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84390600 actual {actual_sum})
NEW box freeze 08:52:35-08:56:43 (248s; not yet told by a 1h patrol; listener auto-restart 08:56:46, python 1772825 started 08:56:56). STATS gap 84390511..84390579 (69t; last STATS 84390510 at 08:52:16, next 84390580 at 08:57:09); official fill after confirm of 84390500: see verify. NEW leftover official 404 W46N8@84390400 (hole 84390401..84390441, 41 ticks; listener 84390442..84390500 59/100; still 404 after confirm 09:00:36 and retry2 09:01:07). Already-told box freeze 08:18:49-08:23:57 (299s; first told by the 08:32 1h patrol; listener auto-restart 08:24:00, python 1755023 started 08:24:09). STATS gap 84390031..84390119 (89t; last STATS 84390030 at 08:18:24, next 84390120 at 08:24:47); official-filled all five 89/89; still in official window start 84389901. Already-told box freeze 07:43:15-08:01:01 (1056s; first recorded by the 08:00/08:14 half-hour; first told by the 08:32 1h patrol) aged out of window start 84389901; official-filled all five 259/259. Already-told box freeze 07:22:15-07:25:56 (214s; first told by the 07:37 1h patrol) aged out of window start 84389901; official-filled all five 69/69. Already-told box freeze 06:42:51-07:04:46 (1315s; first told by the 07:37 1h patrol) aged out of window start 84389901; official-filled all five 329/329. Already-told short listener gap 06:34:33-06:37:21 (first told by the 07:37 1h patrol) aged out of window start 84389901; official-fill W46N8 39/39, W47N8 39/39, W45N8 39/39, W45N7 0/39, W47N7 39/39; missing W45N7 84388561..84388599 (39). Already-told box freeze 06:19:18-06:22:57 (218s; first told by the 06:33 1h patrol) aged out of window start 84389901; official-filled all five 69/69. Already-told box freeze 05:42:11-06:01:46 (1169s; first told by the 06:33 1h patrol) aged out of window start 84389901; official-filled all five 299/299. Already-told leftover official 404s W45N7@84388500, W45N8@84386600, W46N8@84386400, W47N8@84385900, and W47N8@84385300 aged out of window start 84389901 and were not retried here. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file.
"""
(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

retry2_src = DIR / "backfill_retry2.txt"
if not retry2_src.exists():
    retry2_src.write_text("retry2 GET skipped, no targets\n")
shutil.copy2(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0900.txt")

verify = f"""{now_s}
first pass 31/35 official GETs 200 missing_chunks=4 W46N8@84390400, W47N8@84390500, W45N8@84390500, W47N7@84390500 reconstructed 84389901..84390600 (700); confirm recovered the three 84390500 chunks inserted={inserted_confirm} still_404=['W46N8@84390400']; retry2 still_404=['W46N8@84390400'] inserted={inserted_retry2}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84390601..84390700 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{chr(10).join(jp_lines)}
confirm recovered W47N8@84390500, W45N8@84390500, W47N7@84390500; leftover official 404 W46N8@84390400 still 404 after retry2, hole 84390401..84390441 listener 84390442..84390500 {hole904_d}/100, NEW this run not yet told; already-told leftover official 404 W45N7@84388500 hole 84388501..84388600 {hole885_d}/100 aged out of window start 84389901, not retried, already told by 07:37 1h patrol
gap_0852_0856 STATS 84390511..84390579 (69) NEW this run, not yet told (box freeze 08:52:35-08:56:43, 248s); listener auto-restart 08:56:46, python 1772825 started 08:56:56
{g_0852}
gap_0818_0823 STATS 84390031..84390119 (89) already-told by 08:32 patrol (box freeze 08:18:49-08:23:57, 299s); official-filled all five 89/89; still in official window start 84389901
{g_0818}
gap_0743_0801 STATS 84389531..84389789 (259) already-told by 08:32 patrol (box freeze 07:43:15-08:01:01, 1056s); official-filled all five 259/259; aged out of window start 84389901
{g_0743}
gap_0722_0725 STATS 84389231..84389299 (69) already-told by 07:37 patrol (box freeze 07:22:15-07:25:56, 214s); official-filled all five 69/69; aged out of window start 84389901
{g_0722}
gap_0642_0704 STATS 84388671..84388999 (329) already-told by 07:37 patrol (box freeze 06:42:51-07:04:46, 1315s); official-filled all five 329/329; aged out of window start 84389901
{g_0642}
gap_0634_0637 STATS 84388561..84388599 (39) already-told by 07:37 patrol (short listener gap 06:34:33-06:37:21); W45N7 0/39 missing because of official 404 W45N7@84388500; aged out of window start 84389901
{g_0634}
gap_0619_0622 STATS 84388331..84388399 (69) already-told by 06:33 patrol (box freeze 06:19:18-06:22:57, 218s); official-filled all five 69/69; aged out of window start 84389901
{g_0619}
gap_0542_0601 STATS 84387811..84388109 (299) already-told by 06:33 patrol (box freeze 05:42:11-06:01:46, 1169s); official-filled all five 299/299; aged out of window start 84389901
{g_0542}
NEW leftover official 404 W46N8@84390400 {hole904_d}/100 (hole 84390401..84390441, listener 84390442..84390500; first recorded by this 09:00 half-hour; not yet told)
aged-out already-told official 404 W45N7@84388500 {hole885_d}/100 (hole 84388501..84388600; first recorded by 07:00/07:18 half-hour; first told by 07:37 1h patrol) not retried this run
aged-out already-told official 404 W46N8@84386400 {hole864_d}/100 (hole 84386401..84386500, listener 84386401..84386406; first told by 04:18/04:29 patrol), W47N8@84385900 {hole859_d}/100, W47N8@84385300 {hole853_d}/100, W45N8@84386600 {hole866_d}/100 (listener 84386657..84386683) not retried
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.277 corrective={corrective} ts_realigned_first=0
tips room_stats={tips.get("room_stats")} creep_cpu={tips.get("creep_cpu")} path_arrivals={tips.get("path_arrivals")}
listener pid=1772825 started=08:56:56 parent=4035476 slot={slot} rot={rot_s} yield={"absent" if yield_absent else "present"} restarted_this_run=false
ok_quiet=True
"""
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")

summary = f"wrote wrap artifacts at {now_s}; ok_quiet=True coverage={cov_rec}/{cov_exp} inserted_total={inserted_total}\n"
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run.full.txt").write_text(summary)
(DIR / "wrapup_run.console.txt").write_text(summary)
(DIR / "wrapup_run.err").write_text("")
print(summary, end="")
print("ok_quiet", payload["ok_quiet"], "inserted_total", inserted_total, "new_freeze", bool(payload["new_box_freeze"]), "new_404", payload["new_official_404"], "jp_all_five", jp_all_five)
