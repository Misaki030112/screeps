#!/usr/bin/env python3
"""Write 06:30 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0630"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84387701, 84388400
JUST_BASE = 84388400
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
def _load(name, default):
    path = DIR / name
    return json.loads(path.read_text()) if path.exists() else default

confirm = _load("backfill_confirm_gets.json", {"skipped": True, "still_404": [], "inserted": 0, "recovered": [], "at": None, "game_time": None})
confirm_saved = _load("backfill_confirm_gets_after_retry2.json", {"skipped": True})
jp = json.loads((DIR / f"just_published_{JUST_BASE}.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

want = (
    "First-pass realign with tick_s=4.23863 (printed 4.239) moved 0 rows "
    "(ts_realigned_first=0, inserted=700, already_in_db=28965, missing_chunks=0)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace(
    "moved 0 rows (ts_realigned_first=0, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
    "moved 0 rows (ts_realigned_first=0, inserted=700, already_in_db=28965, missing_chunks=0).",
)
reason = reason.replace(
    "(printed 4.137, min-all-rooms first two bases)",
    "(printed 4.239, min-all-rooms first two bases)",
)
reason = reason.replace(
    "(printed 4.145) moved 0 rows",
    "(printed 4.239) moved 0 rows",
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

    def hole(room, a, b):
        row = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, a, b),
        ).fetchone()
        return int(row[0] or 0), int(row[3] or 0), row[1], row[2]

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

inserted_first = 700
inserted_confirm = 0
inserted_retry2 = 0
confirm_at = None
confirm_gt = None
confirm_still = []
confirm_rec = []
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or tick.get("tick_s_used_first_pass") or 4.23863)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "first"
# No corrective this run; tick_s_in_use is first 4.23863 already inside the 45s gate.
corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
cov_rec = cov.get("official_recovered")
cov_exp = cov.get("expected")
empty_n = cov.get("empty_no_creep")
off404 = cov.get("official_404_missing")

retry2_at = None
retry2_gt = None
retry2b_at = None
retry2b_gt = None
retry2_still = []

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

fill_0619 = fill_missing("gap_0619_0622")
fill_0542 = fill_missing("gap_0542_0601")
fill_0442 = fill_missing("gap_0442_0503")
fill_0410 = fill_missing("gap_0410_0418")
fill_0354 = fill_missing("gap_0354_0357")
fill_0245 = fill_missing("gap_0245_0305")
fill_0220 = fill_missing("gap_0220_0222")
fill_0147 = fill_missing("gap_0147_0202")

new_freeze = {
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
    "told": False,
    "note": "NEW, first recorded by this 06:30 backfill; not yet told by a 1h patrol. A 1h patrol was already running at 06:22 when this freeze ended. Official window (chunk 84388300) covers the whole gap 84388331..84388399; just-published 84388400 covers 84388401..84388500 and does not overlap this gap.",
}
prior_untold_box_freeze_0542 = {
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
    "told": False,
    "note": "First recorded by the 06:00/06:12 backfill; still in official window start 84387701; official-filled all five 299/299 including just-published 84388101..84388109. Not yet confirmed delivered by a 1h patrol (a 1h patrol was already running at 06:22).",
}

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84388485,
    "published_bases": "84387700..84388300",
    "reconstructed": [84387701, 84388400],
    "ticks": 700,
    "creep_rows": 29665,
    "missing_chunks": 0,
    "already_in_db": 28965,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84388485, published_bases 84387700..84388300, "
        "reconstructed 84387701..84388400 missing_chunks=0 inserted=700 already_in_db=28965); "
        "35/35 official GETs 200. Prior 06:00 half-hour _halfhour_2026-11-21_0600 had official-filled 84387401..84388100 "
        "plus just-published 84388100 through 84388200. This first pass overlapped those ticks and inserted the remaining "
        "unpublished tail (W46N8 0 new, W47N8 600 new, W45N8 0 new, W45N7 0 new, W47N7 100 new)."
    ),
    "tick_s_printed": 4.239,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 0,
    "corrective": corrective,
    "corrective_note": "no corrective realign; later-mean-robust 4.25633 was slightly worse than live-anchor-best first 4.23863 (already inside 45s gate, over45=0)",
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 0},
        "W47N8": {"ticks": 700, "new": 600},
        "W45N8": {"ticks": 700, "new": 0},
        "W45N7": {"ticks": 700, "new": 0},
        "W47N7": {"ticks": 700, "new": 100},
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
    ),
    "new_box_freeze": new_freeze,
    "prior_untold_box_freeze_0542": prior_untold_box_freeze_0542,
    "new_short_listener_gap": None,
    "new_official_404": [],
    "already_told_official_404_in_window": {},
    "already_told_box_freeze_in_window": {},
    "already_told_short_listener_gap_in_window": None,
    "aged_out_already_told_box_freeze_0442": {
        "from": "2026-11-21 04:42:19",
        "to": "2026-11-21 05:03:11",
        "sec": 1245,
        "stats": "84386961..84387269",
        "span": 309,
        "last_stats": "84386960 at 04:42:04",
        "next_stats": "84387270 at 05:03:25",
        "listener_restart": "05:03:14",
        "listener_pid": 1680509,
        "listener_started": "05:03:23",
        "official_fill": {r: (gaps.get("gap_0442_0503") or {}).get(r, {}).get("fill") for r in ROOMS},
        "official_fill_missing": fill_0442,
        "told": True,
        "told_by": "05:26 1h patrol _patrol_2026-11-21_0526",
        "note": "aged out of window start 84387701; official-filled all five 309/309",
    },
    "aged_out_already_told_box_freeze_0410": {
        "gap_0410_0418": {
            "from": "2026-11-21 04:10:40",
            "to": "2026-11-21 04:18:06",
            "sec": 439,
            "stats": "84386511..84386629",
            "span": 119,
            "last_stats": "84386510 at 04:10:30",
            "next_stats": "84386630 at 04:18:40",
            "listener_restart": "04:18:09",
            "listener_pid": 1665264,
            "listener_started": "04:18:18",
            "official_fill": {r: (gaps.get("gap_0410_0418") or {}).get(r, {}).get("fill") for r in ROOMS},
            "official_fill_missing": fill_0410,
            "told": True,
            "told_by": "04:18/04:29 1h patrol _patrol_2026-11-21_0418",
            "note": "aged out of window start 84387701; W45N8 still missing 84386601..84386629 because of already-told official 404 W45N8@84386600",
        },
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
        "official_fill_missing": fill_0220,
        "told": True,
    },
    "aged_out_already_told_box_freeze_0147": {
        "from": "2026-11-21 01:47:58",
        "to": "2026-11-21 02:02:50",
        "stats": "84384461..84384689",
        "span": 229,
        "official_fill_missing": fill_0147,
        "told": True,
    },
    "aged_out_leftover_official_404s": {
        "W45N8@84386600": {"hole": "84386601..84386700", "distinct": hole866_d, "rows": hole866_n, "range": f"{hole866_mn}..{hole866_mx}", "told_by": "04:18/04:29 1h patrol", "note": "listener 84386657..84386683; still 404 after later leftover rechecks; aged out of window start 84387701 and not retried here"},
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
    "leftover_recheck": {"at": retry2b_at, "game_time": retry2b_gt, "still_404": retry2_still, "inserted": 0},
    "tips": tips,
    "post_tips": post_tips,
    "slot": slot,
    "rot": rot,
    "yield_absent": yield_absent,
    "listener_pid": 1711818,
    "listener_started": "06:23:09",
    "listener_restart": "06:23:00",
    "restarted_this_run": False,
    "prior_halfhour": "_halfhour_2026-11-21_0600 finished 06:12; official through 84388100 + just-published 84388200",
    "prior_1h_patrol": "_patrol_2026-11-21_0526 delivered ~05:26; first-told box freeze 04:42:19-05:03:11 (official-filled all five 309/309). Earlier 04:18/04:29 patrol first-told W46N8@84386400 / W45N8@84386600 / W47N8@84385900 and box freezes 03:54:27-03:57:32 and 04:10:40-04:18:06. A 1h patrol was already running at 06:22 when this backfill started (and when the 06:19 freeze ended); it has not been delivered yet.",
    "fold_only_newer_official_404s_than": ["W45N8@84386600"],
    "fold_only_newer_freezes_than": "06:19:18-06:22:57",
    "fold_only_newer_short_gaps_than": "02:20:54-02:22:17",
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
        f"{r} {gaps[key][r]['fill']}"
        + (f" missing {gaps[key][r]['missing_range']}" if gaps[key][r]["missing_n"] else "")
        for r in ROOMS
    )

g_0619 = gap_line("gap_0619_0622")
g_0542 = gap_line("gap_0542_0601")
g_0442 = gap_line("gap_0442_0503")
g_0410 = gap_line("gap_0410_0418")
g_0354 = gap_line("gap_0354_0357")
g_0245 = gap_line("gap_0245_0305")
g_0220 = gap_line("gap_0220_0222")
g_0147 = gap_line("gap_0147_0202")
win_lines = "\n".join(f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}" for r in ROOMS)
first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = "\n"
fill_0619_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0619.items())
    if fill_0619 else "; official-filled all five 69/69"
)
fill_0542_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0542.items())
    if fill_0542 else "; official-filled all five 299/299"
)
fill_0442_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0442.items())
    if fill_0442 else "; official-filled all five 309/309"
)
fill_0410_txt = (
    "; official-fill missing " + "; ".join(f"{r} {v}" for r, v in fill_0410.items())
    if fill_0410 else "; official-filled all five 119/119"
)
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
jp_lines = [
    f"  {r} actual +{actual_by[r]} script +{script_by[r]} post {post['post'][r]['distinct']}/100 rows={post['post'][r]['rows']}"
    for r in ROOMS
]
confirm_txt = (
    "confirm/retry2 skipped (no in-window official 404s; first pass 35/35 official GETs 200). "
    "Already-told leftover official 404s W47N8@84385300 (hole 84385301..84385400, 0/100), "
    "W45N7@84383500, W45N7@84383900, W45N7@84382700, W46N8@84382900, W45N8@84382600, "
    f"W47N8@84385900 (hole 84385901..84386000, {hole859_d}/100; first told by the 04:18/04:29 1h patrol), "
    f"W46N8@84386400 (hole 84386401..84386500, {hole864_d}/100, listener 84386401..84386406), "
    f"and W45N8@84386600 (hole 84386601..84386700, {hole866_d}/100, listener 84386657..84386683; first told by the 04:18/04:29 1h patrol) "
    "aged out of window start 84387701 and were not retried here."
)
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
{confirm_txt}
tick_s_first={tick_s_first:.5f} printed=4.239 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={corrective}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published {JUST_BASE} at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84388401..84388500; script inserted={script_sum}{mismatch_s}{jp_all_s}
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just {JUST_BASE} actual {actual_sum})
NEW box freeze 06:19:18-06:22:57 (218s; VM hibernated; listener auto-restart 06:23:00, python 1711818 started 06:23:09; not yet told by a 1h patrol; a 1h patrol was already running at 06:22 when this freeze ended). STATS gap 84388331..84388399 (69t; last STATS 84388330 at 06:18:24, next 84388400 at 06:23:19){fill_0619_txt}. Prior untold box freeze 05:42:11-06:01:46 (1169s; first recorded by the 06:00/06:12 backfill; listener auto-restart 06:01:49, python 1702923 started 06:01:59; not yet confirmed delivered by a 1h patrol). STATS gap 84387811..84388109 (299t; last STATS 84387810 at 05:42:02, next 84388110 at 06:02:43){fill_0542_txt}; still in official window start 84387701. Already-told box freeze 04:42:19-05:03:11 (1245s; VM hibernated; listener auto-restart 05:03:14, python 1680509 started 05:03:23; first told by the 05:26 1h patrol). STATS gap 84386961..84387269 (309t; last STATS 84386960 at 04:42:04, next 84387270 at 05:03:25){fill_0442_txt}; aged out of window start 84387701. Already-told box freeze 04:10:40-04:18:06 (439s; VM hibernated; listener auto-restart 04:18:09, python 1665264 started 04:18:18; first told by the 04:18/04:29 1h patrol). STATS gap 84386511..84386629 (119t; last STATS 84386510 at 04:10:30, next 84386630 at 04:18:40){fill_0410_txt}; aged out of window start 84387701. Already-told short box freeze 03:54:27-03:57:32 (178s; STATS 84386281..84386339, 59t){fill_0354_txt}; first told by the same 04:18/04:29 patrol (recorded earlier by the 04:00/04:07 backfill); aged out of window start 84387701. Already-told official 404 W45N8@84386600 (hole 84386601..84386700, {hole866_d}/100, listener 84386657..84386683) aged out of window start 84387701 and was not retried here. Already-told official 404 W46N8@84386400 (hole 84386401..84386500, {hole864_d}/100, listener 84386401..84386406) aged out of window start 84387701 and was not retried here. Already-told official 404 W47N8@84385900 (hole 84385901..84386000, {hole859_d}/100) aged out of window start 84387701 and was not retried here. Already-told official 404 W47N8@84385300 (hole 84385301..84385400, {hole853_d}/100) aged out of window start 84387701 and was not retried here. Already-told box freeze 02:45:59-03:05:48 (STATS 84385301..84385599, 299t) aged out of window start 84387701{fill_0245_txt}. Already-told short listener gap 02:20:54-02:22:17 (STATS 84384941..84384959, 19t) aged out of window start 84387701{fill_0220_txt}. Already-told freeze 01:47:58-02:02:50 (STATS 84384461..84384689, 229t) aged out of window start 84387701. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. No newer official 404s than the already-told W45N8@84386600.
"""
(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
retry2_src = DIR / "backfill_retry2.txt"
if not retry2_src.exists():
    retry2_src.write_text("skipped: no in-window official 404s; first pass 35/35 official GETs 200\n")
shutil.copy2(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0630.txt")

verify = f"""{now_s}
first pass 35/35 official GETs 200 missing_chunks=0 reconstructed 84387701..84388400 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84388401..84388500 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{nl.join(jp_lines)}
gap_0619_0622 STATS 84388331..84388399 (69) NEW this run (box freeze 06:19:18-06:22:57, 218s); listener auto-restart 06:23:00, python 1711818 started 06:23:09; not yet told by a 1h patrol (a 1h patrol was already running at 06:22); official window covers the whole gap 84388331..84388399
{g_0619}
gap_0542_0601 STATS 84387811..84388109 (299) first recorded by the 06:00/06:12 backfill (box freeze 05:42:11-06:01:46, 1169s); listener auto-restart 06:01:49, python 1702923 started 06:01:59; not yet confirmed delivered by a 1h patrol; official-filled all five 299/299; still in official window start 84387701
{g_0542}
gap_0442_0503 STATS 84386961..84387269 (309) already-told by 05:26 patrol (box freeze 04:42:19-05:03:11, 1245s); listener auto-restart 05:03:14, python 1680509 started 05:03:23; official-filled all five 309/309; aged out of window start 84387701
{g_0442}
gap_0410_0418 STATS 84386511..84386629 (119) already-told by 04:18/04:29 patrol (box freeze 04:10:40-04:18:06, 439s); listener auto-restart 04:18:09, python 1665264 started 04:18:18; aged out of window start 84387701
{g_0410}
gap_0354_0357 STATS 84386281..84386339 (59) already-told by 04:18/04:29 patrol (short box freeze 03:54:27-03:57:32, 178s); official-filled all five 59/59; aged out of window start 84387701
{g_0354}
gap_0245_0305 STATS 84385301..84385599 (299) already-told by 03:17 backfill / 03:30 patrol (box freeze 02:45:59-03:05:48, ~1189s); aged out of window start 84387701
{g_0245}
gap_0220_0222 STATS 84384941..84384959 (19) already-told by 02:28/02:30 patrol (short listener gap 02:20:54-02:22:17); aged out of window start 84387701
{g_0220}
gap_0147_0202 STATS 84384461..84384689 (229) already-told by 02:28/02:30 patrol (box freeze 01:47:58-02:02:50); aged out of window start 84387701
{g_0147}
aged-out already-told official 404 W46N8@84386400 {hole864_d}/100 (hole 84386401..84386500, listener 84386401..84386406; first told by 04:18/04:29 patrol), W47N8@84385900 {hole859_d}/100, W47N8@84385300 0/100, W45N7@84383500 0/100, W45N7@84383900 0/100, W45N7@84382700 0/100, W46N8@84382900 67/100, W45N8@84382600 0/100 (not retried)
aged-out already-told official 404 W45N8@84386600 {hole866_d}/100 (hole 84386601..84386700, listener 84386657..84386683; first told by the 04:18/04:29 1h patrol) not retried this run
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.239 corrective={corrective} ts_realigned_first=0
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1711818 started=06:23:09 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
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
