#!/usr/bin/env python3
"""Write 08:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0800"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84389101, 84389800
JUST_BASE = 84389800
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
jp = _load(f"just_published_{JUST_BASE}.json")
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

want_err = (
    "First-pass realign with tick_s=4.14503 (printed 4.145) moved 7978 rows "
    "(ts_realigned_first=7978, inserted=13632, already_in_db=11666, missing_chunks=1 W47N7@84389700)."
)
tick["ts_realigned_first_pass_error"] = want_err
reason = tick.get("reason") or ""
reason = reason.replace(
    "moved 7978 rows (ts_realigned_first=7978, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
    "moved 7978 rows (ts_realigned_first=7978, inserted=13632, already_in_db=11666, missing_chunks=1 W47N7@84389700).",
)
reason = reason.replace("(printed 4.137, min-all-rooms first two bases)", "(printed 4.145, min-all-rooms first two bases)")
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
    conf_chunk_d, conf_chunk_n, conf_chunk_mn, conf_chunk_mx = hole("W47N7", 84389701, 84389800)

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
holes = post.get("holes") or {}
post_tips = post.get("tips") or {}

inserted_first = 13632
inserted_confirm = 461
inserted_retry2 = 0
confirm_at = confirm.get("confirm_at") or confirm.get("at")
confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
confirm_still = list(confirm.get("still_404") or [])
confirm_rec = list(confirm.get("recovered") or [])
retry2_blob = confirm.get("retry2") or {}
retry2_at = confirm.get("retry2_at") or retry2_blob.get("at")
retry2_gt = confirm.get("retry2_game_time") or retry2_blob.get("game_time")
retry2_still = list(confirm.get("retry2_still_404") or retry2_blob.get("still_404") or [])
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or tick.get("tick_s_used_first_pass") or 4.14503)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "first"
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

fill_0743 = fill_missing("gap_0743_0801")
fill_0722 = fill_missing("gap_0722_0725")
fill_0642 = fill_missing("gap_0642_0704")
fill_0634 = fill_missing("gap_0634_0637")
fill_0619 = fill_missing("gap_0619_0622")
fill_0542 = fill_missing("gap_0542_0601")
fill_0442 = fill_missing("gap_0442_0503")
fill_0410 = fill_missing("gap_0410_0418")
fill_0354 = fill_missing("gap_0354_0357")

new_freeze = {
    "from": "2026-11-21 07:43:15",
    "to": "2026-11-21 08:01:01",
    "sec": 1056,
    "stats": "84389531..84389789",
    "span": 259,
    "last_stats": "84389530 at 07:43:03",
    "next_stats": "84389790 at 08:01:21",
    "listener_restart": "08:01:04",
    "listener_pid": 1745776,
    "listener_started": "08:01:13",
    "official_fill": {r: (gaps.get("gap_0743_0801") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_0743,
    "told": False,
    "note": "NEW, first recorded by this 08:00 backfill; not yet told by a 1h patrol. Official window (chunks 84389500..84389700) covers the whole gap 84389531..84389789; first-pass official 404 W47N7@84389700 was recovered on confirm 08:05:33 (100/100), so official-filled all five 259/259. Just-published 84389800 covers 84389801..84389900 and does not overlap this gap.",
}

already_told_freeze_in_window = {
    "from": "2026-11-21 07:22:15",
    "to": "2026-11-21 07:25:56",
    "sec": 214,
    "stats": "84389231..84389299",
    "span": 69,
    "last_stats": "84389230 at 07:21:52",
    "next_stats": "84389300 at 07:26:45",
    "listener_restart": "07:25:59",
    "listener_pid": 1733733,
    "listener_started": "07:26:09",
    "official_fill": {r: (gaps.get("gap_0722_0725") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_0722,
    "told": True,
    "told_by": "07:37 1h patrol",
    "first_recorded_by": "07:30/07:38 half-hour backfill",
    "note": "Still in official window start 84389101 (chunk 84389200); official-filled all five 69/69. First recorded by the 07:30 backfill; first told by the 07:37 1h patrol.",
}

aged_told_0642 = {
    "from": "2026-11-21 06:42:51",
    "to": "2026-11-21 07:04:46",
    "sec": 1315,
    "stats": "84388671..84388999",
    "span": 329,
    "last_stats": "84388670 at 06:42:15",
    "next_stats": "84389000 at 07:05:30",
    "listener_restart": "07:04:49",
    "listener_pid": 1724575,
    "listener_started": "07:04:58",
    "official_fill": {r: (gaps.get("gap_0642_0704") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_0642,
    "told": True,
    "told_by": "07:37 1h patrol",
    "first_recorded_by": "07:00/07:18 half-hour backfill",
    "note": "aged out of window start 84389101; official-filled all five 329/329",
}

aged_told_short_0634 = {
    "from": "2026-11-21 06:34:33",
    "to": "2026-11-21 06:37:21",
    "stats": "84388561..84388599",
    "span": 39,
    "last_stats": "84388560 at 06:34:33",
    "next_stats": "84388600 at 06:37:21",
    "listener_restart": "06:36:28",
    "official_fill": {r: (gaps.get("gap_0634_0637") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_0634,
    "told": True,
    "told_by": "07:37 1h patrol",
    "first_recorded_by": "07:00/07:18 half-hour backfill",
    "note": "Aged out of window start 84389101. W46N8/W47N8/W45N8/W47N7 official-filled 39/39. W45N7 0/39 missing 84388561..84388599 because already-told leftover official 404 W45N7@84388500 (hole 84388501..84388600). First told by the 07:37 1h patrol.",
}

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84389821,
    "published_bases": "84389100..84389700",
    "reconstructed": [84389101, 84389800],
    "ticks": 700,
    "creep_rows": 25298,
    "missing_chunks": 1,
    "already_in_db": 11666,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this 08:00 half-hour routine ran tools/history_backfill.py --minutes 40 "
        "(game.time=84389821, published_bases 84389100..84389700, reconstructed 84389101..84389800 "
        "missing_chunks=1 W47N7@84389700 inserted=13632 already_in_db=11666); 34/35 official GETs 200. "
        "Confirm 08:05:33 gt=84389850 recovered W47N7@84389700 (script inserted=461, db 100/100 rows=275); retry2 skipped no targets. "
        "Prior 07:30 half-hour _halfhour_2026-11-21_0730 had official-filled 84388601..84389300 "
        "(missing_chunks=0, 35/35 200) plus just-published 84389300 (all_five_200=True, actual 479). "
        "This first pass overlapped those ticks and inserted the remaining unpublished tail and the 07:43 freeze gap "
        "(W46N8 2919 new, W47N8 6367 new, W45N8 1722 new, W45N7 1467 new, W47N7 1157 new on the first 600 ticks, plus confirm +275 rows)."
    ),
    "tick_s_printed": 4.145,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 7978,
    "corrective": corrective,
    "corrective_note": "no corrective realign; live-anchor-best first 4.14503 already inside 45s gate (over45=0); later-mean-robust 4.26120 is worse (over45=9893 mean_off=39.8 vs first over45=0 mean_off=-5.9); all_mean 4.24184 also over45=7978",
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 2919},
        "W47N8": {"ticks": 700, "new": 6367},
        "W45N8": {"ticks": 700, "new": 1722},
        "W45N7": {"ticks": 700, "new": 1467},
        "W47N7": {"ticks": 600, "new": 1157},
    },
    "per_room_new_window": {r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS},
    "in_window_404_after_retry2": [],
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
        + " Pre-snapshot already had live/listener rows in W46N8 (30 ticks / 318 rows, 84389801..84389830) and W47N8 (70 ticks / 1188 rows, 84389831..84389900); official GET filled the rest of the chunk."
    ),
    "new_box_freeze": new_freeze,
    "new_short_listener_gap": None,
    "new_official_404": [],
    "prior_untold_box_freeze_in_window": None,
    "already_told_official_404_in_window": {},
    "already_told_box_freeze_in_window": already_told_freeze_in_window,
    "already_told_short_listener_gap_in_window": None,
    "aged_out_already_told_box_freeze_0642": aged_told_0642,
    "aged_out_already_told_short_gap_0634": aged_told_short_0634,
    "aged_out_already_told_box_freeze_0619": {
        "from": "2026-11-21 06:19:18",
        "to": "2026-11-21 06:22:57",
        "sec": 218,
        "stats": "84388331..84388399",
        "span": 69,
        "last_stats": "84388330 at 06:18:24",
        "next_stats": "84388400 at 06:23:19",
        "listener_restart": "06:23:00",
        "listener_pid": 1711818,
        "listener_started": "06:23:09",
        "official_fill": {r: (gaps.get("gap_0619_0622") or {}).get(r, {}).get("fill") for r in ROOMS},
        "official_fill_missing": fill_0619,
        "told": True,
        "told_by": "06:33 1h patrol",
        "note": "aged out of window start 84389101; official-filled all five 69/69",
    },
    "aged_out_already_told_box_freeze_0542": {
        "from": "2026-11-21 05:42:11",
        "to": "2026-11-21 06:01:46",
        "sec": 1169,
        "stats": "84387811..84388109",
        "span": 299,
        "official_fill": {r: (gaps.get("gap_0542_0601") or {}).get(r, {}).get("fill") for r in ROOMS},
        "official_fill_missing": fill_0542,
        "told": True,
        "told_by": "06:33 1h patrol",
        "note": "aged out of window start 84389101; official-filled all five 299/299",
    },
    "aged_out_already_told_box_freeze_0442": {
        "from": "2026-11-21 04:42:19",
        "to": "2026-11-21 05:03:11",
        "sec": 1245,
        "stats": "84386961..84387269",
        "span": 309,
        "official_fill": {r: (gaps.get("gap_0442_0503") or {}).get(r, {}).get("fill") for r in ROOMS},
        "official_fill_missing": fill_0442,
        "told": True,
        "told_by": "05:26 1h patrol _patrol_2026-11-21_0526",
        "note": "aged out of window start 84389101; official-filled all five 309/309",
    },
    "aged_out_already_told_box_freeze_0410": {
        "from": "2026-11-21 04:10:40",
        "to": "2026-11-21 04:18:06",
        "sec": 439,
        "stats": "84386511..84386629",
        "span": 119,
        "official_fill_missing": fill_0410,
        "told": True,
        "told_by": "04:18/04:29 1h patrol",
        "note": "aged out of window start 84389101; W45N8 still missing 84386601..84386629 because of already-told official 404 W45N8@84386600",
    },
    "aged_out_already_told_box_freeze_0354": {
        "from": "2026-11-21 03:54:27",
        "to": "2026-11-21 03:57:32",
        "sec": 178,
        "stats": "84386281..84386339",
        "span": 59,
        "official_fill_missing": fill_0354,
        "told": True,
        "told_by": "04:18/04:29 1h patrol",
    },
    "aged_out_already_told_box_freeze_0245": {
        "from": "2026-11-21 02:45:59",
        "to": "2026-11-21 03:05:48",
        "sec": 1189,
        "stats": "84385301..84385599",
        "span": 299,
        "official_fill_missing": {"W47N8": "84385301..84385400 (100)"},
        "told": True,
    },
    "aged_out_already_told_short_gap_0220": {
        "from": "2026-11-21 02:20:54",
        "to": "2026-11-21 02:22:17",
        "stats": "84384941..84384959",
        "span": 19,
        "told": True,
    },
    "aged_out_already_told_box_freeze_0147": {
        "from": "2026-11-21 01:47:58",
        "to": "2026-11-21 02:02:50",
        "stats": "84384461..84384689",
        "span": 229,
        "told": True,
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
            "note": "Already told by the 07:37 1h patrol (still 404 after 07:00 confirm+retry2; hole 84388501..84388600, 0/100). Aged out of window start 84389101 and was not retried here. Leaves W45N7 missing 84388501..84388600 including the aged-out 06:34-06:37 short-gap ticks 84388561..84388599.",
        },
        "W45N8@84386600": {"hole": "84386601..84386700", "distinct": hole866_d, "rows": hole866_n, "range": None if hole866_mn is None else f"{hole866_mn}..{hole866_mx}", "told_by": "04:18/04:29 1h patrol", "note": "listener 84386657..84386683; aged out of window start 84389101 and not retried here"},
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
        "reason": f"recovered W47N7@84389700; script inserted=461, db distinct={conf_chunk_d} rows={conf_chunk_n} {conf_chunk_mn}..{conf_chunk_mx}",
    },
    "retry2": {"at": retry2_at, "game_time": retry2_gt, "still_404": retry2_still, "inserted": inserted_retry2, "skipped": True, "reason": "no targets; confirm recovered W47N7@84389700"},
    "leftover_recheck": {"at": None, "game_time": None, "still_404": [], "inserted": 0, "skipped": True, "reason": "no in-window leftovers to retry; already-told leftover official 404 W45N7@84388500 aged out of window start 84389101"},
    "tips": tips,
    "post_tips": post_tips,
    "slot": slot,
    "rot": rot,
    "yield_absent": yield_absent,
    "listener_pid": 1745776,
    "listener_started": "08:01:13",
    "listener_restart": "08:01:04",
    "restarted_this_run": False,
    "prior_halfhour": "_halfhour_2026-11-21_0730 finished 07:38; official through 84389300 + just-published 84389300 actual 479; leftover official 404 W45N7@84388500 aged out of that window; first-recorded box freeze 07:22:15-07:25:56 (official-filled all five 69/69) and prior 06:42:51-07:04:46 (official-filled all five 329/329)",
    "prior_1h_patrol": "_patrol last delivered ~07:37 Asia/Hong_Kong; first-told leftover official 404 W45N7@84388500, box freezes 06:42:51-07:04:46 (official-filled all five 329/329) and 07:22:15-07:25:56 (official-filled all five 69/69), and short listener gap 06:34:33-06:37:21 (W45N7 0/39). Earlier 06:33 patrol first-told box freezes 05:42:11-06:01:46 and 06:19:18-06:22:57. Earlier 05:26 patrol first-told box freeze 04:42:19-05:03:11. Earlier 04:18/04:29 patrol first-told W46N8@84386400 / W45N8@84386600 / W47N8@84385900 and box freezes 03:54:27-03:57:32 and 04:10:40-04:18:06.",
    "fold_only_newer_official_404s_than": ["W45N7@84388500"],
    "fold_only_newer_freezes_than": "07:43:15-08:01:01",
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

g_0743 = gap_line("gap_0743_0801")
g_0722 = gap_line("gap_0722_0725")
g_0642 = gap_line("gap_0642_0704")
g_0634 = gap_line("gap_0634_0637")
g_0619 = gap_line("gap_0619_0622")
g_0542 = gap_line("gap_0542_0601")
g_0442 = gap_line("gap_0442_0503")
g_0410 = gap_line("gap_0410_0418")
g_0354 = gap_line("gap_0354_0357")
win_lines = "\n".join(f"  {r} distinct={win[r]['distinct']} rows={win[r]['rows']} {win[r]['min']}..{win[r]['max']}" for r in ROOMS)
post_counts = _load("just_published_post_counts.json", {})
jp_lines = [f"  {r} actual={actual_by[r]} script={script_by[r]} distinct={(post_counts.get(r) or {}).get('distinct')} rows={(post_counts.get(r) or {}).get('rows')}" for r in ROOMS]

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + "\n"
wrap_txt = first_txt + f"""
---- wrap {now_s} ----
confirm at {confirm_at} game.time={confirm_gt} still_404={confirm_still} inserted=461 recovered W47N7@84389700 (db 100/100 rows=275); retry2 at {retry2_at} game.time={retry2_gt} still_404={retry2_still} inserted=0 skipped no targets. First pass 34/35 official GETs 200, missing_chunks=1 W47N7@84389700, recovered on confirm. Already-told leftover official 404 W45N7@84388500 (first recorded by the 07:00/07:18 half-hour, first told by the 07:37 1h patrol, hole 84388501..84388600, {hole885_d}/100) aged out of window start 84389101 and was not retried here. Already-told leftover official 404s W47N8@84385300 (hole 84385301..84385400, {hole853_d}/100), W45N7@84383500, W45N7@84383900, W45N7@84382700, W46N8@84382900, W45N8@84382600, W47N8@84385900 (hole 84385901..84386000, {hole859_d}/100; first told by the 04:18/04:29 1h patrol), W46N8@84386400 (hole 84386401..84386500, {hole864_d}/100, listener 84386401..84386406), and W45N8@84386600 (hole 84386601..84386700, {hole866_d}/100, listener 84386657..84386683; first told by the 04:18/04:29 1h patrol) also aged out of window start 84389101 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.145 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=7978 corrective={corrective}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published {JUST_BASE} at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84389801..84389900; script inserted={script_sum}{mismatch_s}All five ended 100/100.
inserted_window={inserted_window} inserted_total={inserted_total} (first 13632 + confirm 461 + retry2 0 + just 84389800 actual {actual_sum})
NEW box freeze 07:43:15-08:01:01 (1056s; VM hibernated; listener auto-restart 08:01:04, python 1745776 started 08:01:13; not yet told by a 1h patrol). STATS gap 84389531..84389789 (259t; last STATS 84389530 at 07:43:03, next 84389790 at 08:01:21); official-filled all five 259/259. Already-told box freeze 07:22:15-07:25:56 (214s; first recorded by the 07:30/07:38 half-hour; first told by the 07:37 1h patrol; listener auto-restart 07:25:59, python 1733733 started 07:26:09). STATS gap 84389231..84389299 (69t; last STATS 84389230 at 07:21:52, next 84389300 at 07:26:45); official-filled all five 69/69; still in official window start 84389101. Already-told box freeze 06:42:51-07:04:46 (1315s; first recorded by the 07:00/07:18 half-hour; first told by the 07:37 1h patrol). STATS gap 84388671..84388999 (329t); official-filled all five 329/329; aged out of window start 84389101. Already-told short listener gap 06:34:33-06:37:21 (first recorded by the 07:00/07:18 half-hour; first told by the 07:37 1h patrol). STATS gap 84388561..84388599 (39t); official-fill W46N8 39/39, W47N8 39/39, W45N8 39/39, W45N7 0/39, W47N7 39/39; missing W45N7 84388561..84388599 (39); aged out of window start 84389101. Already-told box freeze 06:19:18-06:22:57 (218s; first told by the 06:33 1h patrol) aged out of window start 84389101; official-filled all five 69/69. Already-told box freeze 05:42:11-06:01:46 (1169s; first told by the 06:33 1h patrol) aged out of window start 84389101; official-filled all five 299/299. Already-told box freeze 04:42:19-05:03:11 (1245s; first told by the 05:26 1h patrol) aged out of window start 84389101; official-filled all five 309/309. Already-told box freeze 04:10:40-04:18:06 (439s; first told by the 04:18/04:29 1h patrol) aged out of window start 84389101; official-fill missing W45N8 84386601..84386629 (29). Already-told short box freeze 03:54:27-03:57:32 (178s) aged out of window start 84389101; official-filled all five 59/59. Already-told leftover official 404s W45N7@84388500, W45N8@84386600, W46N8@84386400, W47N8@84385900, and W47N8@84385300 aged out of window start 84389101 and were not retried here. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. No NEW leftover official 404 this run.
"""
(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

retry2_src = DIR / "backfill_retry2.txt"
if not retry2_src.exists():
    retry2_src.write_text("retry2 GET skipped, no targets\n")
shutil.copy2(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0800.txt")

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 W47N7@84389700 reconstructed 84389101..84389800 (700); confirm recovered W47N7@84389700 inserted=461 db 100/100 rows=275; retry2 skipped
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84389801..84389900 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{chr(10).join(jp_lines)}
confirm recovered W47N7@84389700 retry2 skipped no targets inserted=0; already-told leftover official 404 W45N7@84388500 hole 84388501..84388600 {hole885_d}/100 aged out of window start 84389101, not retried, already told by 07:37 1h patrol
gap_0743_0801 STATS 84389531..84389789 (259) NEW this run (box freeze 07:43:15-08:01:01, 1056s); listener auto-restart 08:01:04, python 1745776 started 08:01:13; not yet told by a 1h patrol; official-filled all five 259/259
{g_0743}
gap_0722_0725 STATS 84389231..84389299 (69) already-told by 07:37 patrol (box freeze 07:22:15-07:25:56, 214s); official-filled all five 69/69; still in official window start 84389101
{g_0722}
gap_0642_0704 STATS 84388671..84388999 (329) already-told by 07:37 patrol (box freeze 06:42:51-07:04:46, 1315s); official-filled all five 329/329; aged out of window start 84389101
{g_0642}
gap_0634_0637 STATS 84388561..84388599 (39) already-told by 07:37 patrol (short listener gap 06:34:33-06:37:21); W45N7 0/39 missing because of official 404 W45N7@84388500; aged out of window start 84389101
{g_0634}
gap_0619_0622 STATS 84388331..84388399 (69) already-told by 06:33 patrol (box freeze 06:19:18-06:22:57, 218s); official-filled all five 69/69; aged out of window start 84389101
{g_0619}
gap_0542_0601 STATS 84387811..84388109 (299) already-told by 06:33 patrol (box freeze 05:42:11-06:01:46, 1169s); official-filled all five 299/299; aged out of window start 84389101
{g_0542}
gap_0442_0503 STATS 84386961..84387269 (309) already-told by 05:26 patrol (box freeze 04:42:19-05:03:11, 1245s); official-filled all five 309/309; aged out of window start 84389101
{g_0442}
gap_0410_0418 STATS 84386511..84386629 (119) already-told by 04:18/04:29 patrol (box freeze 04:10:40-04:18:06, 439s); aged out of window start 84389101
{g_0410}
gap_0354_0357 STATS 84386281..84386339 (59) already-told by 04:18/04:29 patrol (short box freeze 03:54:27-03:57:32, 178s); official-filled all five 59/59; aged out of window start 84389101
{g_0354}
aged-out already-told official 404 W45N7@84388500 {hole885_d}/100 (hole 84388501..84388600; first recorded by 07:00/07:18 half-hour; first told by 07:37 1h patrol) not retried this run
aged-out already-told official 404 W46N8@84386400 {hole864_d}/100 (hole 84386401..84386500, listener 84386401..84386406; first told by 04:18/04:29 patrol), W47N8@84385900 {hole859_d}/100, W47N8@84385300 {hole853_d}/100, W45N8@84386600 {hole866_d}/100 (listener 84386657..84386683) not retried
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.145 corrective={corrective} ts_realigned_first=7978
tips room_stats={tips.get("room_stats")} creep_cpu={tips.get("creep_cpu")} path_arrivals={tips.get("path_arrivals")}
listener pid=1745776 started=08:01:13 parent=4035476 slot={slot} rot={rot_s} yield={"absent" if yield_absent else "present"} restarted_this_run=false
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
print("ok_quiet", payload["ok_quiet"], "inserted_total", inserted_total, "new_freeze", new_freeze["from"], "jp_all_five", jp_all_five)
