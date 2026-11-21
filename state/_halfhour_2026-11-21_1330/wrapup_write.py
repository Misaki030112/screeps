#!/usr/bin/env python3
"""Write 13:30 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_1330"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84393701, 84394400
JUST_BASE = 84394400
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
retry2_default = {"skipped": True, "still_404": [], "inserted": 0, "recovered": [], "at": None, "game_time": None}
retry2j = confirm if confirm.get("retry2") or confirm.get("retry2_skipped") else retry2_default
jp = _load(f"just_published_{JUST_BASE}.json")
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

want_err = (
    "First-pass realign with tick_s=4.23635 (printed 4.236) moved 0 rows "
    "(ts_realigned_first=0, inserted=531, already_in_db=26099, missing_chunks=1)."
)
tick["ts_realigned_first_pass_error"] = want_err
reason = tick.get("reason") or ""
reason = reason.replace("(printed 4.206, min-all-rooms first two bases)", "(printed 4.236, min-all-rooms first two bases)")
reason = reason.replace("(printed 4.206)", "(printed 4.236)")
reason = reason.replace("(printed 4.224)", "(printed 4.236)")
reason = reason.replace(
    "(ts_realigned_first=0, inserted=3305, already_in_db=21922, missing_chunks=0).",
    "(ts_realigned_first=0, inserted=531, already_in_db=26099, missing_chunks=1).",
)
reason = reason.replace(
    "First-pass realign with tick_s=4.23635 (printed 4.236) moved 0 rows (ts_realigned_first=0, inserted=3305, already_in_db=21922, missing_chunks=0).",
    want_err,
)
if "inserted=531" not in reason:
    reason = reason + " " + want_err
tick["reason"] = reason
(DIR / "tick_s_realign.json").write_text(json.dumps(tick, indent=2) + chr(10))

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

    hole926_d, hole926_n, hole926_mn, hole926_mx = hole("W45N8", 84392601, 84392700)
    hole904_d, hole904_n, hole904_mn, hole904_mx = hole("W46N8", 84390401, 84390500)
    hole908_d, hole908_n, hole908_mn, hole908_mx = hole("W46N8", 84390801, 84390900)
    hole909_d, hole909_n, hole909_mn, hole909_mx = hole("W47N7", 84390901, 84391000)
    hole885_d, hole885_n, hole885_mn, hole885_mx = hole("W45N7", 84388501, 84388600)
    hole866_d, hole866_n, hole866_mn, hole866_mx = hole("W45N8", 84386601, 84386700)
    hole943_d, hole943_n, hole943_mn, hole943_mx = hole("W46N8", 84394301, 84394400)

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]

inserted_first = 531
inserted_confirm = int(confirm.get("inserted") or 0)
retry2_blob = retry2j.get("retry2") or retry2j
inserted_retry2 = int(retry2j.get("retry2_inserted") or retry2_blob.get("inserted") or 0)
confirm_at = confirm.get("confirm_at") or confirm.get("at")
confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
confirm_still = list(confirm.get("still_404") or [])
confirm_rec = list(confirm.get("recovered") or [])
confirm_skipped = bool(confirm.get("skipped"))
retry2_at = retry2j.get("retry2_at") or retry2_blob.get("at")
retry2_gt = retry2j.get("retry2_game_time") or retry2_blob.get("game_time")
retry2_still = list(retry2j.get("retry2_still_404") or retry2_blob.get("still_404") or [])
retry2_rec = list(retry2j.get("retry2_recovered") or retry2_blob.get("recovered") or [])
retry2_skipped = bool(retry2j.get("retry2_skipped") or retry2_blob.get("skipped"))
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("tick_s_used_first_pass") or tick.get("first_interval") or 4.23635)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "all_mean"
corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
cov_rec = cov.get("official_recovered")
cov_exp = cov.get("expected")
empty_n = cov.get("empty_no_creep")
off404 = cov.get("official_404_missing")

slot = live.get("roomSlot")
rot_s = json.dumps(rot, ensure_ascii=False)
jp_still = jp.get("still_404") or []
jp_rec = jp.get("recovered") or []
jp_all_five = (not jp_still) and len(jp_rec) >= 5

script_mismatch = [f"{r} script {script_by[r]} vs actual {actual_by[r]}" for r in ROOMS if actual_by[r] != script_by[r]]
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


def gap_lines(gap_key):
    g = gaps.get(gap_key) or {}
    lines = []
    for r in ROOMS:
        rec = g.get(r) or {}
        miss = rec.get("missing_range")
        extra = f" missing {miss} ({rec.get('missing_n')})" if rec.get("missing_n") else ""
        lines.append(f"  {r} fill={rec.get('fill')} rows={rec.get('rows')}{extra}")
    return "\n".join(lines)


new_box_freeze = {
    "from": "2026-11-21 13:09:46",
    "to": "2026-11-21 13:21:14",
    "sec": 680,
    "stats": "84394131..84394299",
    "span": 169,
    "last_stats": "84394130 at 13:09:20",
    "next_stats": "84394300 at 13:21:31",
    "listener_restart": "13:21:17",
    "listener_pid": 1883231,
    "listener_started": "13:21:26",
    "official_fill": {r: (gaps.get("gap_1309_1321") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1309_1321"),
    "told": False,
    "told_by": None,
    "first_recorded_by": "13:30 half-hour backfill",
    "note": (
        "NEW this run, not yet told. Box freeze 13:09:46-13:21:14 (680s); STATS 84394131..84394299 (169t). "
        "last_stats 84394130 at 13:09:20, next 84394300 at 13:21:31. Listener auto-restart 13:21:17, python 1883231 started 13:21:26, parent=4035476. "
        "This backfill official-filled all five 169/169 (chunks 84394100 and 84394200 cover the whole 169t inside official window start 84393701). "
        "Next 1h patrol should tell this freeze together with the still-untold 12:48 and 12:30 freezes."
    ),
}

prior_untold_freeze_1248 = {
    "from": "2026-11-21 12:48:14",
    "to": "2026-11-21 12:57:17",
    "sec": 534,
    "stats": "84393831..84393969",
    "span": 139,
    "last_stats": "84393830 at 12:48:02",
    "next_stats": "84393970 at 12:57:57",
    "listener_restart": "12:57:20",
    "listener_pid": 1876378,
    "listener_started": "12:57:29",
    "official_fill": {r: (gaps.get("gap_1248_1257") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1248_1257"),
    "told": False,
    "told_by": None,
    "first_recorded_by": "13:00 half-hour backfill",
    "note": (
        "Still not yet told (first recorded by the 13:00 half-hour backfill). Box freeze 12:48:14-12:57:17 (534s); STATS 84393831..84393969 (139t). "
        "Official-filled all five 139/139 at the 13:00 run; still in official window start 84393701. "
        "Next 1h patrol should tell this freeze together with the newer 13:09 freeze and the still-untold 12:30 freeze. Do not treat as already told."
    ),
}

prior_untold_freeze_1230 = {
    "from": "2026-11-21 12:30:42",
    "to": "2026-11-21 12:35:35",
    "sec": 283,
    "stats": "84393581..84393659",
    "span": 79,
    "last_stats": "84393580 at 12:30:15",
    "next_stats": "84393660 at 12:36:02",
    "listener_restart": "12:35:38",
    "listener_pid": 1869380,
    "listener_started": "12:35:48",
    "official_fill": {r: (gaps.get("gap_1230_1235") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1230_1235"),
    "told": False,
    "told_by": None,
    "first_recorded_by": "12:30 half-hour backfill",
    "note": (
        "Still not yet told (first recorded by the 12:30 half-hour backfill). Box freeze 12:30:42-12:35:35 (283s); STATS 84393581..84393659 (79t). "
        "Official-filled all five 79/79 at the 12:30 run; ages out of official window start 84393701. "
        "Next 1h patrol should still tell this freeze together with 13:09 and 12:48. Do not treat as already told."
    ),
}

already_told_freeze_1149 = {
    "from": "2026-11-21 11:49:12",
    "to": "2026-11-21 11:57:31",
    "sec": 494,
    "stats": "84393001..84393129",
    "span": 129,
    "official_fill": {r: (gaps.get("gap_1149_1157") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1149_1157"),
    "told": True,
    "told_by": "12:26 1h patrol t508s3573",
    "note": "Already told by the 12:26 1h patrol. Box freeze 11:49:12-11:57:31 (494s); official-filled all five 129/129. Ages out of window start 84393701. Do not re-tell.",
}

already_told_gap_1210 = {
    "from": "2026-11-21 12:10:56",
    "to": "2026-11-21 12:10:59",
    "kind": "ws_ping_pong_timeout",
    "not_a_box_freeze": True,
    "stats": "84393291..84393319",
    "span": 29,
    "official_fill": {r: (gaps.get("gap_1210") or {}).get(r, {}).get("fill") for r in ROOMS},
    "told": True,
    "told_by": "12:26 1h patrol t508s3573",
    "note": "Already told by the 12:26 1h patrol. Short listener WS ping/pong, not a box freeze; official-filled all five 29/29. Ages out of official window start 84393701. Do not re-tell.",
}

already_told_gap_1218 = {
    "from": "2026-11-21 12:18:13",
    "to": "2026-11-21 12:18:17",
    "kind": "ws_ping_pong_timeout",
    "not_a_box_freeze": True,
    "stats": "84393391..84393419",
    "span": 29,
    "official_fill": {r: (gaps.get("gap_1218") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1218"),
    "told": True,
    "told_by": "12:26 1h patrol t508s3573",
    "note": (
        "Already told by the 12:26 1h patrol. Short listener WS ping/pong, not a box freeze. "
        "Four rooms official-filled 29/29; W45N7 21/29 missing 84393411 and 84393413..84393419 is official empty-no-creep after invader-core evac, not a 404. "
        "Ages out of official window start 84393701. Do not re-tell."
    ),
}

already_told_leftover_926 = {
    "chunk": "W45N8@84392600",
    "hole": "84392601..84392663 and 84392693..84392700",
    "missing_n": 71,
    "listener": "84392664..84392692",
    "listener_n": 29,
    "distinct": hole926_d,
    "rows": hole926_n,
    "range": None if hole926_mn is None else f"{hole926_mn}..{hole926_mx}",
    "told": True,
    "told_by": "12:26 1h patrol t508s3573",
    "note": (
        "Already told by the 12:26 1h patrol (confirm+retry2 12:08 and patrol retry 12:25 still 404). "
        "Ages out of window start 84393701 and was not retried here. Listener 29/100; hole 71 ticks."
    ),
}

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84394426,
    "published_bases": "84393700..84394300",
    "reconstructed": [84393701, 84394400],
    "ticks": 700,
    "creep_rows": 26630,
    "missing_chunks": 1,
    "already_in_db": 26099,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this 13:30 half-hour routine ran tools/history_backfill.py --minutes 40 "
        "(game.time=84394426, published_bases 84393700..84394300, reconstructed 84393701..84394400 "
        "missing_chunks=1 W46N8@84394300 inserted=531 already_in_db=26099); 34/35 official GETs 200. "
        f"Confirm {confirm_at} skipped={confirm_skipped} still_404={confirm_still} inserted={inserted_confirm}. "
        f"retry2 {retry2_at} skipped={retry2_skipped} still_404={retry2_still} inserted={inserted_retry2}. "
        "Late retry 13:39:21 gt=84394550 still 404 W46N8@84394300 inserted=0. "
        "Prior 13:00 half-hour official-filled 84393201..84393900 plus just-published 84393900 actual 3109; "
        "that run also recorded still-untold box freeze 12:48:14-12:57:17 (official-filled all five 139/139) "
        "and carried still-untold 12:30:42-12:35:35 (official-filled all five 79/79)."
    ),
    "tick_s_printed": 4.236,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 0,
    "corrective": corrective,
    "corrective_note": (
        f"no corrective realign; live-anchor-best span_mean {tick_s_in_use:.5f} already inside 45s gate "
        "(over45=0 mean_off=-0.5) at game.time=84394465; first-pass tick_s=4.23635 (printed 4.236) realigned 0 rows"
    ),
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "empty_no_creep_note": (
        "W45N7 official empty-no-creep 9 ticks: 84393793..84393798 and 84393817..84393819 "
        "(same official empty-no-creep pattern after the earlier W45N7 Invader-core evac; not a 404). "
        "The older evac empty range 84393411 / 84393413..84393580 now sits before official window start 84393701."
    ),
    "per_room_new_first": {
        "W46N8": {"ticks": 600, "new": 0},
        "W47N8": {"ticks": 700, "new": 300},
        "W45N8": {"ticks": 700, "new": 0},
        "W45N7": {"ticks": 700, "new": 0},
        "W47N7": {"ticks": 700, "new": 231},
    },
    "per_room_new_window": {r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS},
    "in_window_404_after_retry2": ["W46N8@84394300"],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": JUST_BASE,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": jp_all_five,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp_still,
    "just_published_actual_note": (
        f"script inserted={script_sum} ({script_parts}). "
        f"post-counts actual_sum={actual_sum}{mismatch_s}"
        + (" All five ended 100/100." if jp_all_five else " Not all five 100/100.")
    ),
    "new_box_freeze": new_box_freeze,
    "new_short_listener_gap": None,
    "new_official_404": [{
        "chunk": "W46N8@84394300",
        "hole": "84394380..84394400",
        "missing_n": 21,
        "listener": "84394301..84394379",
        "listener_n": 79,
        "distinct": hole943_d,
        "rows": hole943_n,
        "range": None if hole943_mn is None else f"{hole943_mn}..{hole943_mx}",
        "told": False,
        "told_by": None,
        "first_recorded_by": "13:30 half-hour backfill",
        "note": (
            "NEW leftover official 404 this run, not yet told. First pass 404 at game.time=84394426; "
            "confirm 13:33:07 gt=84394463, retry2 13:33:42 gt=84394471, and late retry 13:39:21 gt=84394550 still 404. "
            "Other four rooms at base 84394300 returned 200 on the first pass. "
            "Listener already has 79/100 ticks 84394301..84394379; hole 21 ticks 84394380..84394400. "
            "Next 1h patrol should tell this leftover together with the new 13:09 freeze."
        ),
    }],
    "prior_untold_box_freeze_in_window": prior_untold_freeze_1248,
    "prior_untold_box_freeze_aged_out": prior_untold_freeze_1230,
    "prior_untold_short_listener_gap_in_window": None,
    "already_told_official_404_in_window": {},
    "already_told_box_freeze_in_window": None,  # 11:49 freeze ages out of window start 84393701
    "already_told_box_freeze_aged_out": already_told_freeze_1149,
    "already_told_short_listener_gap_1210": already_told_gap_1210,
    "already_told_short_listener_gap_1218": already_told_gap_1218,
    "aged_out_leftover_official_404s": {
        "W45N8@84392600": already_told_leftover_926,
        "W46N8@84390800": {
            "chunk": "W46N8@84390800",
            "distinct": hole908_d,
            "rows": hole908_n,
            "told": True,
            "told_by": "09:42 1h patrol",
            "note": "Already told. Aged out of window start 84393701 and was not retried here.",
        },
        "W47N7@84390900": {
            "chunk": "W47N7@84390900",
            "distinct": hole909_d,
            "rows": hole909_n,
            "told": True,
            "told_by": "09:42 1h patrol",
            "note": "Already told. Aged out of window start 84393701 and was not retried here.",
        },
        "W46N8@84390400": {
            "chunk": "W46N8@84390400",
            "distinct": hole904_d,
            "rows": hole904_n,
            "told": True,
            "told_by": "09:42 1h patrol",
            "note": "Already told. Aged out of window start 84393701 and was not retried here.",
        },
        "W45N7@84388500": {
            "chunk": "W45N7@84388500",
            "distinct": hole885_d,
            "rows": hole885_n,
            "told": True,
            "told_by": "07:37 1h patrol",
            "note": "Already told. Aged out of window start 84393701 and was not retried here.",
        },
        "W45N8@84386600": {
            "chunk": "W45N8@84386600",
            "distinct": hole866_d,
            "rows": hole866_n,
            "told": True,
            "told_by": "04:18/04:29 1h patrol",
            "note": "Already told. Aged out of window start 84393701 and was not retried here.",
        },
    },
    "confirm": {
        "at": confirm_at,
        "game_time": confirm_gt,
        "still_404": confirm_still,
        "inserted": inserted_confirm,
        "recovered": confirm_rec,
        "skipped": confirm_skipped,
        "reason": "first pass 34/35 official GETs 200, missing_chunks=1 W46N8@84394300; confirm still 404, inserted=0",
    },
    "retry2": {
        "at": retry2_at,
        "game_time": retry2_gt,
        "still_404": retry2_still,
        "inserted": inserted_retry2,
        "recovered": retry2_rec,
        "skipped": retry2_skipped,
        "reason": "W46N8@84394300 still 404 at 13:33:42 gt=84394471; late retry 13:39:21 gt=84394550 also 404",
    },
    "listener": {
        "pid": 1883231,
        "started": "13:21:26",
        "parent": 4035476,
        "slot": slot,
        "rot": rot,
        "yield": "absent" if yield_absent else "present",
        "restarted_this_run": False,
        "last_auto_restart": "13:21:17 after box freeze 13:09:46-13:21:14; existing run_listener.sh parent 4035476 relaunched listener.py; this run did not restart the listener or war_cmd/pulse",
        "peacetime_single_slot": "W46N8:W47N8:W45N8:W45N7=5:5:1:1",
    },
    "prior_halfhour": (
        "_halfhour_2026-11-21_1300 finished ~13:07; official through 84393900 + just-published 84393900 actual 3109; "
        "recorded still-untold box freeze 12:48:14-12:57:17 (official-filled all five 139/139) and carried still-untold 12:30:42-12:35:35 (official-filled all five 79/79); "
        "leftover official 404 W45N8@84392600 already told by the 12:26 1h patrol and aged out"
    ),
    "prior_1h_patrol": (
        "_patrol_2026-11-21_1217 finished ~12:27, USER_LOG delivered ~12:26 Asia/Hong_Kong t508s3573. "
        "Told box freeze 11:49:12-11:57:31 (official-filled all five 129/129), leftover official 404 W45N8@84392600 "
        "(listener 29/100, hole 71), and short listener WS gaps 11:12:51-11:12:54, 12:10:59, and 12:18:17. "
        "Older already-told freezes through 11:19:06-11:20:43 and 10:47:36-10:59:07 remain already told. "
        "Do not re-tell those. Fold the new 13:09:46-13:21:14 freeze, the still-untold 12:48:14-12:57:17 and 12:30:42-12:35:35 freezes, and the new leftover official 404 W46N8@84394300."
    ),
    "tips": tips,
    "ok_quiet": True,
}

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + "\n"
wrap_body = f"""---- wrap {now_s} ----
confirm at {confirm_at} game.time={confirm_gt} still_404={confirm_still} inserted={inserted_confirm} recovered={confirm_rec} skipped={confirm_skipped}; retry2 at {retry2_at} game.time={retry2_gt} still_404={retry2_still} inserted={inserted_retry2} recovered={retry2_rec} skipped={retry2_skipped}. First pass 34/35 official GETs 200, missing_chunks=1 W46N8@84394300. Confirm 13:33:07 and retry2 13:33:42 still 404; late retry 13:39:21 gt=84394550 also still 404, inserted=0. Already-told leftover official 404s W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 and older aged out of window start {WIN_TMIN} and were not retried. Just-published {JUST_BASE} at {jp.get('at')} gt={jp.get('game_time')} all_five_200={jp_all_five} script={script_sum} actual={actual_sum}. Coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404} (W45N7 9 empty-no-creep 84393793..84393798 and 84393817..84393819, not a 404; W46N8 leftover official 404 hole 84394380..84394400, listener 79/100 84394301..84394379). inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} just_actual={actual_sum} total={inserted_total}. tick_s_printed=4.236 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={corrective}. Listener pid=1883231 started=13:21:26 parent=4035476 slot={slot} rot={rot_s} yield={'absent' if yield_absent else 'present'} restarted_this_run=false. Peacetime single-slot 5:5:1:1. This run did not restart the listener or war_cmd/pulse.
NEW-this-window not yet told: box freeze 13:09:46-13:21:14 (680s; STATS 84394131..84394299, 169t; official-filled all five 169/169; listener auto-restart 13:21:17, python 1883231 started 13:21:26). NEW leftover official 404 W46N8@84394300 not yet told (confirm+retry2+late_retry still 404; listener 79/100 84394301..84394379; hole 21 ticks 84394380..84394400). Still not yet told from the 13:00 backfill and still in window: box freeze 12:48:14-12:57:17 (534s; STATS 84393831..84393969, 139t; official-filled all five 139/139; listener auto-restart 12:57:20, python 1876378 started 12:57:29). Still not yet told from the 12:30 backfill but ages out of window start {WIN_TMIN}: box freeze 12:30:42-12:35:35 (283s; STATS 84393581..84393659, 79t; official-filled all five 79/79; listener auto-restart 12:35:38, python 1869380 started 12:35:48). Already told by the 12:26 1h patrol t508s3573 and now age out of window start {WIN_TMIN}: short listener WS gaps 12:10:56-12:10:59 and 12:18:13-12:18:17, leftover official 404 W45N8@84392600 and older leftovers W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600, already-told freeze 11:49:12-11:57:31 and freezes through 11:19:06-11:20:43 and short WS gap 11:12:51-11:12:54. Fold the new freeze 13:09:46-13:21:14, the still-untold 12:48:14-12:57:17 and 12:30:42-12:35:35, and the new leftover official 404 W46N8@84394300; do not re-tell already-told freezes through 11:49:12-11:57:31 or leftover official 404 W45N8@84392600.
"""
wrap_txt = first + "\n" + wrap_body
(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

prev = ROOT / "state" / "history_backfill.json"
if prev.exists():
    shutil.copy2(prev, ROOT / "state" / "history_backfill.prev.json")
(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
shutil.copy2(DIR / "history_backfill.json", prev)

retry2_src = DIR / "backfill_retry2.txt"
if not retry2_src.exists():
    retry2_src.write_text("retry2 GET skipped, no targets\n")
shutil.copy2(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1330.txt")

win_lines = "\n".join(
    f"  {r} ticks={win[r]['min']}..{win[r]['max']} rows={win[r]['rows']} distinct={win[r]['distinct']}"
    for r in ROOMS
)
jp_lines = [f"  {r} actual=+{actual_by[r]} script=+{script_by[r]} post_distinct={post['post'][r]['distinct']} post_rows={post['post'][r]['rows']}" for r in ROOMS]

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 W46N8@84394300 reconstructed 84393701..84394400 (700); confirm still 404 inserted={inserted_confirm}; retry2 still 404 inserted={inserted_retry2}; late retry 13:39:21 gt=84394550 still 404 inserted=0
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84394401..84394500 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{chr(10).join(jp_lines)}
NEW leftover official 404 W46N8@84394300 {hole943_d}/100 (listener 84394301..84394379, 79; hole 21 ticks 84394380..84394400) not yet told; confirm+retry2+late_retry still 404. Already-told leftover official 404 W45N8@84392600 {hole926_d}/100 (listener 84392664..84392692, 29; hole 71) aged out of window start 84393701, not retried (already told by 12:26 1h patrol). Already-told leftovers W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600 also aged out, not retried
gap_1309_1321 STATS 84394131..84394299 (169) NEW this run, not yet told (box freeze 13:09:46-13:21:14, 680s); last_stats 84394130 at 13:09:20, next 84394300 at 13:21:31; listener auto-restart 13:21:17, python 1883231 started 13:21:26; official-filled all five 169/169; whole gap sits in official window start 84393701 (chunks 84394100 and 84394200)
{gap_lines("gap_1309_1321")}
gap_1248_1257 STATS 84393831..84393969 (139) still not yet told (recorded by 13:00 half-hour backfill; box freeze 12:48:14-12:57:17, 534s); official-filled all five 139/139; still in official window start 84393701
{gap_lines("gap_1248_1257")}
gap_1230_1235 STATS 84393581..84393659 (79) still not yet told (recorded by 12:30 half-hour backfill; box freeze 12:30:42-12:35:35, 283s); official-filled all five 79/79; ages out of official window start 84393701
{gap_lines("gap_1230_1235")}
gap_1218 STATS 84393391..84393419 (29) already-told by 12:26 patrol (short listener WS ping/pong 12:18:13, restart 12:18:17, not a box freeze); four rooms 29/29; W45N7 21/29 missing 84393411..84393419 official empty-no-creep after evac, not a 404; ages out of official window start 84393701
{gap_lines("gap_1218")}
gap_1210 STATS 84393291..84393319 (29) already-told by 12:26 patrol (short listener WS ping/pong 12:10:56, restart 12:10:59, not a box freeze); official-filled all five 29/29; ages out of official window start 84393701
{gap_lines("gap_1210")}
gap_1149_1157 STATS 84393001..84393129 (129) already-told by 12:26 patrol (box freeze 11:49:12-11:57:31, 494s); official-filled all five 129/129; ages out of official window start 84393701
{gap_lines("gap_1149_1157")}
NEW box freeze 13:09:46-13:21:14 not yet told (official-filled all five 169/169). NEW leftover official 404 W46N8@84394300 not yet told (listener 79/100, hole 21). Still-untold 12:48:14-12:57:17 also not yet told (official-filled all five 139/139). Still-untold 12:30:42-12:35:35 also not yet told (official-filled all five 79/79; ages out of this official window). Do not re-tell already-told freeze 11:49:12-11:57:31, short WS gaps 12:10/12:18/11:12, or leftover official 404 W45N8@84392600 and older leftovers.
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.236 corrective={corrective} ts_realigned_first=0
tips room_stats={tips.get("room_stats")} creep_cpu={tips.get("creep_cpu")} path_arrivals={tips.get("path_arrivals")}
listener pid=1883231 started=13:21:26 parent=4035476 slot={slot} rot={rot_s} yield={"absent" if yield_absent else "present"} restarted_this_run=false
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
print(
    "ok_quiet", payload["ok_quiet"],
    "inserted_total", inserted_total,
    "new_freeze", payload["new_box_freeze"]["from"],
    "new_404", payload["new_official_404"],
    "jp_all_five", jp_all_five,
    "empty_no_creep", empty_n,
)
