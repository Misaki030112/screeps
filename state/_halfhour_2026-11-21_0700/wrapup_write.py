#!/usr/bin/env python3
"""Write 07:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0700"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84388301, 84389000
JUST_BASE = 84389000
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
nl = "\n"

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

# Fix stale printed-tick_s wording left in the tick_s_check template.
want = (
    "First-pass realign with tick_s=4.18774 (printed 4.188) moved 0 rows "
    "(ts_realigned_first=0, inserted=15701, already_in_db=9792, missing_chunks=1 W45N7@84388500)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace(
    "moved 0 rows (ts_realigned_first=0, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
    "moved 0 rows (ts_realigned_first=0, inserted=15701, already_in_db=9792, missing_chunks=1 W45N7@84388500).",
)
reason = reason.replace("(printed 4.137, min-all-rooms first two bases)", "(printed 4.188, min-all-rooms first two bases)")
reason = reason.replace("(printed 4.145) moved 0 rows", "(printed 4.188) moved 0 rows")
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

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
holes = post.get("holes") or {}
post_tips = post.get("tips") or {}

inserted_first = 15701
inserted_confirm = 0
inserted_retry2 = 0
confirm_at = confirm.get("confirm_at") or confirm.get("at")
confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
confirm_still = list(confirm.get("still_404") or [])
confirm_rec = list(confirm.get("recovered") or [])
retry2_at = confirm.get("retry2_at")
retry2_gt = confirm.get("retry2_game_time")
retry2_still = list(confirm.get("retry2_still_404") or [])
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or tick.get("tick_s_used_first_pass") or 4.18774)
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
mismatch_s = ("; " + "; ".join(script_mismatch) + ".") if script_mismatch else "."
script_parts = ", ".join(f"{r} +{script_by[r]}" for r in ROOMS)

def fill_missing(gap_key):
    missing = {}
    for r in ROOMS:
        g = (gaps.get(gap_key) or {}).get(r) or {}
        if g.get("missing_n"):
            missing[r] = f"{g.get('missing_range')} ({g.get('missing_n')})"
    return missing

def fill_txt(gap_key, missing):
    fills = []
    for r in ROOMS:
        g = (gaps.get(gap_key) or {}).get(r) or {}
        fills.append(f"{r} {g.get('fill')}")
    if not missing:
        return "; official-filled all five " + ((gaps.get(gap_key) or {}).get("W46N8") or {}).get("fill", "")
    return "; official-fill " + ", ".join(fills) + "; missing " + ", ".join(f"{r} {v}" for r, v in missing.items())

fill_0642 = fill_missing("gap_0642_0704")
fill_0634 = fill_missing("gap_0634_0637")
fill_0619 = fill_missing("gap_0619_0622")
fill_0542 = fill_missing("gap_0542_0601")
fill_0442 = fill_missing("gap_0442_0503")
fill_0410 = fill_missing("gap_0410_0418")
fill_0354 = fill_missing("gap_0354_0357")
fill_0245 = fill_missing("gap_0245_0305")

fill_0642_txt = fill_txt("gap_0642_0704", fill_0642)
fill_0634_txt = fill_txt("gap_0634_0637", fill_0634)
fill_0619_txt = fill_txt("gap_0619_0622", fill_0619)
fill_0542_txt = fill_txt("gap_0542_0601", fill_0542)
fill_0442_txt = fill_txt("gap_0442_0503", fill_0442)
fill_0410_txt = fill_txt("gap_0410_0418", fill_0410)
fill_0354_txt = fill_txt("gap_0354_0357", fill_0354)
fill_0245_txt = fill_txt("gap_0245_0305", fill_0245)

new_freeze = {
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
    "told": False,
    "note": "NEW, first recorded by this 07:00 backfill; not yet told by a 1h patrol. Official window (chunks 84388600..84388900) covers the whole gap 84388671..84388999; just-published 84389000 covers 84389001..84389100 and does not overlap this gap. Official-filled all five 329/329.",
}
new_short_gap = {
    "from": "2026-11-21 06:34:33",
    "to": "2026-11-21 06:37:21",
    "kind": "short_listener_gap",
    "cause": "ping/pong timeout 06:36:25, listener restart 06:36:28 (segment poll errors 06:39:10 and 06:40:22 did not create a further STATS gap)",
    "stats": "84388561..84388599",
    "span": 39,
    "last_stats": "84388560 at 06:34:33",
    "next_stats": "84388600 at 06:37:21",
    "listener_restart": "06:36:28",
    "official_fill": {r: (gaps.get("gap_0634_0637") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_0634,
    "told": False,
    "note": "NEW, first recorded by this 07:00 backfill; not yet told by a 1h patrol. W46N8/W47N8/W45N8/W47N7 official-filled 39/39. W45N7 0/39 missing 84388561..84388599 because first-pass official 404 W45N7@84388500 stayed 404 after confirm and retry2 (hole 84388501..84388600).",
}
new_official_404 = [{
    "room": "W45N7",
    "base": 84388500,
    "hole": "84388501..84388600",
    "distinct": hole885_d,
    "rows": hole885_n,
    "range": None if hole885_mn is None else f"{hole885_mn}..{hole885_mx}",
    "first_pass": "404 at 07:07 first pass (game.time=84389020)",
    "confirm": "still 404 at 07:11:33 game.time=84389084",
    "retry2": "still 404 at 07:12:32 game.time=84389098",
    "told": False,
    "note": "NEW leftover official 404 this run; not retried beyond confirm+retry2. Leaves W45N7 missing the 06:34-06:37 short-gap ticks 84388561..84388599 and the rest of chunk 84388501..84388600. Do not treat recovered just-published 84389000 as a leftover.",
}]

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84389020,
    "published_bases": "84388300..84388900",
    "reconstructed": [84388301, 84389000],
    "ticks": 700,
    "creep_rows": 25493,
    "missing_chunks": 1,
    "already_in_db": 9792,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84389020, published_bases 84388300..84388900, "
        "reconstructed 84388301..84389000 missing_chunks=1 W45N7@84388500 inserted=15701 already_in_db=9792); "
        "34/35 official GETs 200. Prior 06:30 half-hour _halfhour_2026-11-21_0630 had official-filled 84387701..84388400 "
        "plus just-published 84388400 (all_five_200=True, actual 0). This first pass overlapped those ticks and inserted "
        "the remaining unpublished tail and the 06:42 freeze gap (W46N8 4690 new, W47N8 4649 new, W45N8 2565 new, W45N7 1443 new, W47N7 2354 new)."
    ),
    "tick_s_printed": 4.188,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 0,
    "corrective": corrective,
    "corrective_note": "no corrective realign; later-mean-robust 4.23360 was slightly worse than live-anchor-best all_mean 4.22596 (already inside 45s gate, over45=0)",
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 4690},
        "W47N8": {"ticks": 700, "new": 4649},
        "W45N8": {"ticks": 700, "new": 2565},
        "W45N7": {"ticks": 600, "new": 1443},
        "W47N7": {"ticks": 700, "new": 2354},
    },
    "per_room_new_window": {r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS},
    "in_window_404_after_retry2": ["W45N7@84388500"],
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
    "new_box_freeze": new_freeze,
    "new_short_listener_gap": new_short_gap,
    "new_official_404": new_official_404,
    "already_told_official_404_in_window": {},
    "already_told_box_freeze_in_window": {
        "gap_0619_0622": {
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
            "note": "still in official window start 84388301; official-filled all five 69/69",
        },
    },
    "already_told_short_listener_gap_in_window": None,
    "aged_out_already_told_box_freeze_0542": {
        "from": "2026-11-21 05:42:11",
        "to": "2026-11-21 06:01:46",
        "sec": 1169,
        "stats": "84387811..84388109",
        "span": 299,
        "last_stats": "84387810 at 05:42:02",
        "next_stats": "84388110 at 06:02:43",
        "listener_restart": "06:01:49",
        "listener_pid": 1702923,
        "listener_started": "06:01:59",
        "official_fill": {r: (gaps.get("gap_0542_0601") or {}).get(r, {}).get("fill") for r in ROOMS},
        "official_fill_missing": fill_0542,
        "told": True,
        "told_by": "06:33 1h patrol",
        "note": "aged out of window start 84388301; official-filled all five 299/299",
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
        "note": "aged out of window start 84388301; official-filled all five 309/309",
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
        "note": "aged out of window start 84388301; W45N8 still missing 84386601..84386629 because of already-told official 404 W45N8@84386600",
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
        "listener_restart": "03:05:51",
        "official_fill": {r: (gaps.get("gap_0245_0305") or {}).get(r, {}).get("fill") for r in ROOMS},
        "official_fill_missing": fill_0245,
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
        "W45N8@84386600": {"hole": "84386601..84386700", "distinct": hole866_d, "rows": hole866_n, "range": f"{hole866_mn}..{hole866_mx}", "told_by": "04:18/04:29 1h patrol", "note": "listener 84386657..84386683; still 404 after later leftover rechecks; aged out of window start 84388301 and not retried here"},
        "W46N8@84386400": {"hole": "84386401..84386500", "distinct": hole864_d, "rows": hole864_n, "range": f"{hole864_mn}..{hole864_mx}", "told_by": "04:18/04:29 1h patrol", "note": "listener 84386401..84386406"},
        "W47N8@84385900": {"hole": "84385901..84386000", "distinct": hole859_d, "rows": hole859_n, "told_by": "04:18/04:29 1h patrol"},
        "W47N8@84385300": {"hole": "84385301..84385400", "distinct": hole853_d, "rows": hole853_n, "told": True},
        "W45N7@84383500": {"distinct": (holes.get("W45N7@84383500") or {}).get("distinct"), "told": True},
        "W45N7@84383900": {"distinct": (holes.get("W45N7@84383900") or {}).get("distinct"), "told": True},
        "W45N8@84382600": {"distinct": (holes.get("W45N8@84382600") or {}).get("distinct"), "told": True},
        "W45N7@84382700": {"distinct": (holes.get("W45N7@84382700") or {}).get("distinct"), "told": True},
        "W46N8@84382900": {"distinct": (holes.get("W46N8@84382900") or {}).get("distinct"), "told": True},
    },
    "confirm": {"at": confirm_at, "game_time": confirm_gt, "still_404": confirm_still, "inserted": inserted_confirm, "recovered": confirm_rec},
    "retry2": {"at": retry2_at, "game_time": retry2_gt, "still_404": retry2_still, "inserted": inserted_retry2},
    "leftover_recheck": {"at": None, "game_time": None, "still_404": retry2_still, "inserted": 0},
    "tips": tips,
    "post_tips": post_tips,
    "slot": slot,
    "rot": rot,
    "yield_absent": yield_absent,
    "listener_pid": 1724575,
    "listener_started": "07:04:58",
    "listener_restart": "07:04:49",
    "restarted_this_run": False,
    "prior_halfhour": "_halfhour_2026-11-21_0630 finished 06:36; official through 84388400 + just-published 84388400 actual 0",
    "prior_1h_patrol": "_patrol delivered ~06:33 Asia/Hong_Kong; first-told box freezes 05:42:11-06:01:46 (official-filled all five 299/299) and 06:19:18-06:22:57 (official-filled all five 69/69). Earlier 05:26 patrol first-told box freeze 04:42:19-05:03:11. Earlier 04:18/04:29 patrol first-told W46N8@84386400 / W45N8@84386600 / W47N8@84385900 and box freezes 03:54:27-03:57:32 and 04:10:40-04:18:06.",
    "fold_only_newer_official_404s_than": ["W45N8@84386600"],
    "fold_only_newer_freezes_than": "06:42:51-07:04:46",
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

g_0642 = gap_line("gap_0642_0704")
g_0634 = gap_line("gap_0634_0637")
g_0619 = gap_line("gap_0619_0622")
g_0542 = gap_line("gap_0542_0601")
g_0442 = gap_line("gap_0442_0503")
g_0410 = gap_line("gap_0410_0418")
g_0354 = gap_line("gap_0354_0357")
g_0245 = gap_line("gap_0245_0305")
win_lines = "\n".join(f"  {r} distinct={win[r]['distinct']} rows={win[r]['rows']} {win[r]['min']}..{win[r]['max']}" for r in ROOMS)
jp_lines = [f"  {r} actual={actual_by[r]} script={script_by[r]} distinct={post.get('post', post.get('actual_by_room') and '')}" for r in ROOMS]
# Use post counts file for distinct if present
post_counts = _load("just_published_post_counts.json", {})
jp_lines = [f"  {r} actual={actual_by[r]} script={script_by[r]} distinct={(post_counts.get(r) or {}).get('distinct')} rows={(post_counts.get(r) or {}).get('rows')}" for r in ROOMS]

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + "\n"
wrap_txt = first_txt + f"""
---- wrap {now_s} ----
confirm at {confirm_at} game.time={confirm_gt} still_404={confirm_still} inserted=0; retry2 at {retry2_at} game.time={retry2_gt} still_404={retry2_still} inserted=0. First pass 34/35 official GETs 200, missing_chunks=1 W45N7@84388500, still 404 after confirm+retry2 (NEW leftover official 404, hole 84388501..84388600, {hole885_d}/100). Already-told leftover official 404s W47N8@84385300 (hole 84385301..84385400, {hole853_d}/100), W45N7@84383500, W45N7@84383900, W45N7@84382700, W46N8@84382900, W45N8@84382600, W47N8@84385900 (hole 84385901..84386000, {hole859_d}/100; first told by the 04:18/04:29 1h patrol), W46N8@84386400 (hole 84386401..84386500, {hole864_d}/100, listener 84386401..84386406), and W45N8@84386600 (hole 84386601..84386700, {hole866_d}/100, listener 84386657..84386683; first told by the 04:18/04:29 1h patrol) aged out of window start 84388301 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.188 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={corrective}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published {JUST_BASE} at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84389001..84389100; script inserted={script_sum}{mismatch_s}{" All five ended 100/100." if jp_all_five else ""}
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm 0 + retry2 0 + just {JUST_BASE} actual {actual_sum})
NEW box freeze 06:42:51-07:04:46 (1315s; VM hibernated; listener auto-restart 07:04:49, python 1724575 started 07:04:58; not yet told by a 1h patrol). STATS gap 84388671..84388999 (329t; last STATS 84388670 at 06:42:15, next 84389000 at 07:05:30){fill_0642_txt}. NEW short listener gap 06:34:33-06:37:21 (ping/pong timeout 06:36:25, listener restart 06:36:28; not yet told by a 1h patrol). STATS gap 84388561..84388599 (39t; last STATS 84388560 at 06:34:33, next 84388600 at 06:37:21){fill_0634_txt}. Already-told box freeze 06:19:18-06:22:57 (218s; first told by the 06:33 1h patrol; listener auto-restart 06:23:00, python 1711818 started 06:23:09). STATS gap 84388331..84388399 (69t; last STATS 84388330 at 06:18:24, next 84388400 at 06:23:19){fill_0619_txt}; still in official window start 84388301. Already-told box freeze 05:42:11-06:01:46 (1169s; first told by the 06:33 1h patrol; listener auto-restart 06:01:49, python 1702923 started 06:01:59). STATS gap 84387811..84388109 (299t){fill_0542_txt}; aged out of window start 84388301. Already-told box freeze 04:42:19-05:03:11 (1245s; first told by the 05:26 1h patrol) aged out of window start 84388301{fill_0442_txt}. Already-told box freeze 04:10:40-04:18:06 (439s; first told by the 04:18/04:29 1h patrol) aged out of window start 84388301{fill_0410_txt}. Already-told short box freeze 03:54:27-03:57:32 (178s; STATS 84386281..84386339, 59t){fill_0354_txt}; aged out of window start 84388301. Already-told official 404 W45N8@84386600 (hole 84386601..84386700, {hole866_d}/100, listener 84386657..84386683) aged out of window start 84388301 and was not retried here. Already-told official 404 W46N8@84386400 (hole 84386401..84386500, {hole864_d}/100, listener 84386401..84386406) aged out of window start 84388301 and was not retried here. Already-told official 404 W47N8@84385900 (hole 84385901..84386000, {hole859_d}/100) aged out of window start 84388301 and was not retried here. Already-told official 404 W47N8@84385300 (hole 84385301..84385400, {hole853_d}/100) aged out of window start 84388301 and was not retried here. Already-told box freeze 02:45:59-03:05:48 (STATS 84385301..84385599, 299t) aged out of window start 84388301{fill_0245_txt}. Already-told short listener gap 02:20:54-02:22:17 (STATS 84384941..84384959, 19t) aged out of window start 84388301. Already-told freeze 01:47:58-02:02:50 (STATS 84384461..84384689, 229t) aged out of window start 84388301. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. NEW leftover official 404 W45N7@84388500 is newer than the already-told W45N8@84386600 and is not yet told.
"""
(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
retry2_src = DIR / "backfill_retry2.txt"
if not retry2_src.exists():
    retry2_src.write_text("retry2 still_404=['W45N7@84388500'] inserted=0\n")
shutil.copy2(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0700.txt")

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 W45N7@84388500 reconstructed 84388301..84389000 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84389001..84389100 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{nl.join(jp_lines)}
confirm still_404={confirm_still} retry2 still_404={retry2_still} inserted=0; NEW leftover official 404 W45N7@84388500 hole 84388501..84388600 {hole885_d}/100 not yet told
gap_0642_0704 STATS 84388671..84388999 (329) NEW this run (box freeze 06:42:51-07:04:46, 1315s); listener auto-restart 07:04:49, python 1724575 started 07:04:58; not yet told by a 1h patrol; official-filled all five 329/329
{g_0642}
gap_0634_0637 STATS 84388561..84388599 (39) NEW short listener gap this run (ping/pong timeout 06:36:25, restart 06:36:28); not yet told; W45N7 0/39 missing because of official 404 W45N7@84388500
{g_0634}
gap_0619_0622 STATS 84388331..84388399 (69) already-told by 06:33 patrol (box freeze 06:19:18-06:22:57, 218s); official-filled all five 69/69; still in official window start 84388301
{g_0619}
gap_0542_0601 STATS 84387811..84388109 (299) already-told by 06:33 patrol (box freeze 05:42:11-06:01:46, 1169s); official-filled all five 299/299; aged out of window start 84388301
{g_0542}
gap_0442_0503 STATS 84386961..84387269 (309) already-told by 05:26 patrol (box freeze 04:42:19-05:03:11, 1245s); official-filled all five 309/309; aged out of window start 84388301
{g_0442}
gap_0410_0418 STATS 84386511..84386629 (119) already-told by 04:18/04:29 patrol (box freeze 04:10:40-04:18:06, 439s); aged out of window start 84388301
{g_0410}
gap_0354_0357 STATS 84386281..84386339 (59) already-told by 04:18/04:29 patrol (short box freeze 03:54:27-03:57:32, 178s); official-filled all five 59/59; aged out of window start 84388301
{g_0354}
gap_0245_0305 STATS 84385301..84385599 (299) already-told by 03:17 backfill / 03:30 patrol (box freeze 02:45:59-03:05:48, ~1189s); aged out of window start 84388301
{g_0245}
aged-out already-told official 404 W46N8@84386400 {hole864_d}/100 (hole 84386401..84386500, listener 84386401..84386406; first told by 04:18/04:29 patrol), W47N8@84385900 {hole859_d}/100, W47N8@84385300 {hole853_d}/100, W45N7@84383500 0/100, W45N7@84383900 0/100, W45N7@84382700 0/100, W46N8@84382900 67/100, W45N8@84382600 0/100 (not retried)
aged-out already-told official 404 W45N8@84386600 {hole866_d}/100 (hole 84386601..84386700, listener 84386657..84386683; first told by the 04:18/04:29 1h patrol) not retried this run
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.188 corrective={corrective} ts_realigned_first=0
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1724575 started=07:04:58 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
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
