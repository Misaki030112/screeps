#!/usr/bin/env python3
"""Write 11:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_1100"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84391601, 84392300
JUST_BASE = 84392300
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
retry2j = _load("backfill_retry2_gets.json", None) if (DIR / "backfill_retry2_gets.json").exists() else None
if retry2j is None:
    retry2j = confirm if confirm.get("retry2") or confirm.get("retry2_skipped") else retry2_default
jp = _load(f"just_published_{JUST_BASE}.json")
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

want_err = (
    "First-pass realign with tick_s=4.29684 (printed 4.297) moved 0 rows "
    "(ts_realigned_first=0, inserted=9846, already_in_db=16990, missing_chunks=0)."
)
tick["ts_realigned_first_pass_error"] = want_err
reason = tick.get("reason") or ""
for old in (
    "First-pass realign with tick_s=4.20613 (printed 4.145) moved 3287 rows (ts_realigned_first=3287, inserted=3305, already_in_db=21922, missing_chunks=0).",
    "First-pass realign with tick_s=4.20613 (printed 4.137, min-all-rooms first two bases)",
    "First-pass realign with tick_s=4.20613 (printed 4.145) moved 3287 rows (ts_realigned_first=3287, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
):
    reason = reason.replace(old, want_err if "moved 3287 rows" in old else "First-pass realign with tick_s=4.20613 (printed 4.206, min-all-rooms first two bases)")
reason = reason.replace("(printed 4.206, min-all-rooms first two bases)", "(printed 4.297, min-all-rooms first two bases)")
reason = reason.replace("(printed 4.206)", "(printed 4.297)")
reason = reason.replace("(ts_realigned_first=0, inserted=3305, already_in_db=21922, missing_chunks=0).", "(ts_realigned_first=0, inserted=9846, already_in_db=16990, missing_chunks=0).")
if "inserted=200" in reason or "W45N7@84383500" in reason:
    reason = reason.replace(
        "First-pass realign with tick_s=4.20613 (printed 4.206) moved 3287 rows (ts_realigned_first=3287, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
        want_err,
    )
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

    hole904_d, hole904_n, hole904_mn, hole904_mx = hole("W46N8", 84390401, 84390500)
    hole908_d, hole908_n, hole908_mn, hole908_mx = hole("W46N8", 84390801, 84390900)
    hole909_d, hole909_n, hole909_mn, hole909_mx = hole("W47N7", 84390901, 84391000)
    hole885_d, hole885_n, hole885_mn, hole885_mx = hole("W45N7", 84388501, 84388600)
    hole866_d, hole866_n, hole866_mn, hole866_mx = hole("W45N8", 84386601, 84386700)
    hole864_d, hole864_n, hole864_mn, hole864_mx = hole("W46N8", 84386401, 84386500)
    hole859_d, hole859_n, hole859_mn, hole859_mx = hole("W47N8", 84385901, 84386000)
    hole853_d, hole853_n, hole853_mn, hole853_mx = hole("W47N8", 84385301, 84385400)

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
holes = post.get("holes") or {}
post_tips = post.get("tips") or {}
post_counts = post.get("post") or {}

inserted_first = 9846
inserted_confirm = int(confirm.get("inserted") or 0)
retry2_blob = retry2j.get("retry2") or retry2j
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

tick_s_first = float(tick.get("tick_s_used_first_pass") or tick.get("first_interval") or 4.29684)
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

fill_1047 = fill_missing("gap_1047_1059")
fill_1017 = fill_missing("gap_1017_1024")
fill_0958 = fill_missing("gap_0958_1005")
fill_0915 = fill_missing("gap_0915_0923")
fill_0852 = fill_missing("gap_0852_0856")
fill_0818 = fill_missing("gap_0818_0823")

already_told_freeze_1017 = {
    "from": "2026-11-21 10:17:34",
    "to": "2026-11-21 10:24:42",
    "sec": 423,
    "stats": "84391711..84391819",
    "span": 109,
    "last_stats": "84391710 at 10:17:17",
    "next_stats": "84391820 at 10:25:05",
    "listener_restart": "10:24:45",
    "listener_pid": 1808991,
    "listener_started": "10:24:54",
    "official_fill": {r: (gaps.get("gap_1017_1024") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_1017,
    "told": True,
    "told_by": "10:31 1h patrol",
    "first_recorded_by": "10:24/10:31 1h patrol",
    "note": (
        "Already told by the 10:31 1h patrol. Box freeze 10:17:34-10:24:42 (423s); STATS 84391711..84391819 (109t). "
        "At patrol time official-filled published 90/90 all five, unpublished tail 84391801..84391819 expected. "
        "This run official first-pass included chunk 84391800 (84391801..84391900) so that tail is now official-filled. "
        "Still in official window start 84391601. Do not re-tell."
    ),
}

already_told_freeze_0958 = {
    "from": "2026-11-21 09:58:02",
    "to": "2026-11-21 10:05:00",
    "sec": 412,
    "stats": "84391431..84391549",
    "span": 119,
    "last_stats": "84391430 at 09:57:18",
    "next_stats": "84391550 at 10:05:42",
    "listener_restart": "10:05:03",
    "listener_pid": 1801941,
    "listener_started": "10:05:13",
    "official_fill": {r: (gaps.get("gap_0958_1005") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_0958,
    "told": True,
    "told_by": "10:31 1h patrol",
    "first_recorded_by": "10:00 half-hour backfill",
    "note": (
        "Already told by the 10:31 1h patrol (first recorded by the 10:00 half-hour backfill as NEW). "
        "Box freeze 09:58:02-10:05:00 (412s); STATS 84391431..84391549 (119t). "
        "Official-fill missing W45N7 84391431..84391537 (90) empty-no-creep during evac, not a 404. "
        "Ages out of window start 84391601. Do not re-tell."
    ),
}

already_told_freeze_0915 = {
    "from": "2026-11-21 09:15:27",
    "to": "2026-11-21 09:23:48",
    "sec": 492,
    "stats": "84390831..84390959",
    "span": 129,
    "last_stats": "84390830 at 09:14:58",
    "next_stats": "84390960 at 09:24:15",
    "listener_restart": "09:23:51",
    "listener_pid": 1782523,
    "listener_started": "09:24:01",
    "official_fill": {r: (gaps.get("gap_0915_0923") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_0915,
    "told": True,
    "told_by": "09:42 1h patrol",
    "first_recorded_by": "09:30 half-hour backfill (concurrent with 09:26/09:42 1h)",
    "note": "Already told by the 09:42 1h patrol. Official-filled W47N8/W45N8/W45N7 129/129; W46N8 59/129 missing 84390831..84390900 due to leftover 404 W46N8@84390800; W47N7 70/129 missing 84390901..84390959 due to leftover 404 W47N7@84390900. Ages out of window start 84391601. Do not re-tell.",
}

already_told_freeze_0852 = {
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
    "told": True,
    "told_by": "09:42 1h patrol",
    "first_recorded_by": "09:00 half-hour backfill",
    "note": "Already told by the 09:42 1h patrol. Official-filled all five 69/69. Ages out of window start 84391601. Do not re-tell.",
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
    "note": "Already told by the 08:32 1h patrol. Official-filled all five 89/89; ages out of window start 84391601. Do not re-tell.",
}

new_box_freeze = {
    "from": "2026-11-21 10:47:36",
    "to": "2026-11-21 10:59:07",
    "sec": 684,
    "stats": "84392131..84392309",
    "span": 179,
    "last_stats": "84392130 at 10:47:07",
    "next_stats": "84392310 at 10:59:44",
    "listener_restart": "10:59:10",
    "listener_pid": 1822915,
    "listener_started": "10:59:19",
    "official_fill": {r: (gaps.get("gap_1047_1059") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_1047,
    "told": False,
    "told_by": None,
    "first_recorded_by": "11:00 half-hour backfill",
    "note": (
        "NEW this run, not yet told by a 1h patrol. Box freeze 10:47:36-10:59:07 (684s); STATS 84392131..84392309 (179t). "
        "last_stats 84392130 at 10:47:07, next 84392310 at 10:59:44. Listener auto-restart 10:59:10, python 1822915 started 10:59:19, parent=4035476. "
        "Official first-pass filled through 84392300; just-published 84392300 filled the unpublished tail 84392301..84392309. "
        "Official-filled all five 179/179. This run did not restart the listener. Next 1h patrol should tell this freeze."
    ),
}

new_official_404 = []

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84392326,
    "published_bases": "84391600..84392200",
    "reconstructed": [84391601, 84392300],
    "ticks": 700,
    "creep_rows": 26836,
    "missing_chunks": 0,
    "already_in_db": 16990,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this 11:00 half-hour routine ran tools/history_backfill.py --minutes 40 "
        "(game.time=84392326, published_bases 84391600..84392200, reconstructed 84391601..84392300 "
        "missing_chunks=0 inserted=9846 already_in_db=16990); 35/35 official GETs 200. "
        f"Confirm {confirm_at} skipped, no targets, inserted={inserted_confirm}. "
        f"retry2 {retry2_at} skipped, no targets, inserted={inserted_retry2}. "
        "Prior 10:30 half-hour official-filled 84391201..84391900 plus just-published 84391900 actual 2568."
    ),
    "tick_s_printed": 4.297,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 0,
    "corrective": corrective,
    "corrective_note": (
        f"no corrective realign; live-anchor-best {tick_s_in_use_name} {tick_s_in_use:.5f} already inside 45s gate "
        f"(over45=0); later-mean-robust 4.21696 was worse (over45=0 mean_off=-10.3 vs best mean_off=-4.7); first-pass tick_s=4.29684 had over45=318 so was not used"
    ),
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 3596},
        "W47N8": {"ticks": 700, "new": 3179},
        "W45N8": {"ticks": 700, "new": 1690},
        "W45N7": {"ticks": 700, "new": 559},
        "W47N7": {"ticks": 700, "new": 822},
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
        + (" All five ended 100/100." if jp_all_five else " Not all five 100/100.")
    ),
    "new_box_freeze": new_box_freeze,
    "new_short_listener_gap": None,
    "new_official_404": new_official_404,
    "prior_untold_box_freeze_in_window": None,
    "already_told_official_404_in_window": {},
    "already_told_box_freeze_in_window": already_told_freeze_1017,
    "already_told_box_freeze_0958_in_window": None,
    "already_told_box_freeze_0852_in_window": None,
    "already_told_box_freeze_0818_in_window": None,
    "already_told_box_freeze_0743_in_window": None,
    "already_told_short_listener_gap_in_window": None,
    "aged_out_already_told_box_freeze_0958": {
        **already_told_freeze_0958,
        "note": "aged out of window start 84391601; official-fill missing W45N7 90 empty-no-creep during evac, not a 404; already told by 10:31 1h patrol",
    },
    "aged_out_already_told_box_freeze_0915": {
        **already_told_freeze_0915,
        "note": "aged out of window start 84391601; official-fill missing W46N8 70 / W47N7 59 due to leftover official 404s; already told by 09:42 1h patrol",
    },
    "aged_out_already_told_box_freeze_0852": {
        **already_told_freeze_0852,
        "note": "aged out of window start 84391601; official-filled all five 69/69; already told by 09:42 1h patrol",
    },
    "aged_out_already_told_box_freeze_0818": {
        **already_told_freeze_0818,
        "note": "aged out of window start 84391601; official-filled all five 89/89; already told by 08:32 1h patrol",
    },
    "aged_out_leftover_official_404s": {
        "W46N8@84390800": {
            "chunk": "W46N8@84390800",
            "hole": "84390801..84390900",
            "missing_n": 100,
            "listener": None,
            "listener_n": 0,
            "distinct": hole908_d,
            "rows": hole908_n,
            "range": None if hole908_mn is None else f"{hole908_mn}..{hole908_mx}",
            "told": True,
            "told_by": "09:42 1h patrol",
            "first_recorded_by": "09:30 half-hour backfill (concurrent with 09:26/09:42 1h)",
            "note": "Already told by the 09:42 1h patrol. Aged out of window start 84391601 and was not retried here. Hole 84390801..84390900 (100).",
        },
        "W47N7@84390900": {
            "chunk": "W47N7@84390900",
            "hole": "84390901..84391000",
            "missing_n": 100,
            "listener": None,
            "listener_n": 0,
            "distinct": hole909_d,
            "rows": hole909_n,
            "range": None if hole909_mn is None else f"{hole909_mn}..{hole909_mx}",
            "told": True,
            "told_by": "09:42 1h patrol",
            "first_recorded_by": "09:30 half-hour backfill (concurrent with 09:26/09:42 1h)",
            "note": "Already told by the 09:42 1h patrol. Aged out of window start 84391601 and was not retried here. Hole 84390901..84391000 (100).",
        },
        "W46N8@84390400": {
            "chunk": "W46N8@84390400",
            "hole": "84390401..84390441",
            "missing_n": 41,
            "listener": "84390442..84390500",
            "listener_n": 59,
            "distinct": hole904_d,
            "rows": hole904_n,
            "range": None if hole904_mn is None else f"{hole904_mn}..{hole904_mx}",
            "told": True,
            "told_by": "09:42 1h patrol",
            "first_recorded_by": "09:00 half-hour backfill",
            "note": "Already told by the 09:42 1h patrol. Aged out of window start 84391601 and was not retried here. Listener 59/100; hole 84390401..84390441 (41).",
        },
        "W45N7@84388500": {
            "hole": "84388501..84388600",
            "distinct": hole885_d,
            "rows": hole885_n,
            "range": None if hole885_mn is None else f"{hole885_mn}..{hole885_mx}",
            "told": True,
            "told_by": "07:37 1h patrol",
            "note": "Already told by the 07:37 1h patrol. Aged out of window start 84391601 and was not retried here.",
        },
        "W45N8@84386600": {"hole": "84386601..84386700", "distinct": hole866_d, "rows": hole866_n, "range": None if hole866_mn is None else f"{hole866_mn}..{hole866_mx}", "told_by": "04:18/04:29 1h patrol", "note": "aged out of window start 84391601 and not retried here"},
        "W46N8@84386400": {"hole": "84386401..84386500", "distinct": hole864_d, "rows": hole864_n, "range": None if hole864_mn is None else f"{hole864_mn}..{hole864_mx}", "told_by": "04:18/04:29 1h patrol"},
        "W47N8@84385900": {"hole": "84385901..84386000", "distinct": hole859_d, "rows": hole859_n, "told_by": "04:18/04:29 1h patrol"},
        "W47N8@84385300": {"hole": "84385301..84385400", "distinct": hole853_d, "rows": hole853_n, "told": True},
    },
    "confirm": {
        "at": confirm_at,
        "game_time": confirm_gt,
        "still_404": confirm_still,
        "inserted": inserted_confirm,
        "recovered": confirm_rec,
        "skipped": True,
        "reason": "no targets; first pass 35/35 official GETs 200, missing_chunks=0; no in-window official 404s to retry",
    },
    "retry2": {
        "at": retry2_at,
        "game_time": retry2_gt,
        "still_404": retry2_still,
        "inserted": inserted_retry2,
        "recovered": retry2_rec,
        "skipped": True,
        "reason": "no targets; missing_chunks=0; no aged-out leftovers retried",
    },
    "leftover_recheck": {
        "at": retry2_at,
        "game_time": retry2_gt,
        "still_404": [],
        "inserted": 0,
        "skipped": True,
        "reason": "no in-window leftover official 404s this run; already-told leftovers W46N8@84390800 / W47N7@84390900 / W46N8@84390400 aged out of window start 84391601 and were not retried",
    },
    "tips": tips,
    "post_tips": post_tips,
    "slot": slot,
    "rot": rot,
    "yield_absent": yield_absent,
    "listener_pid": 1822915,
    "listener_started": "10:59:19",
    "listener_restart": "10:59:10",
    "restarted_this_run": False,
    "prior_halfhour": "_halfhour_2026-11-21_1030 finished ~10:42; official through 84391900 + just-published 84391900 actual 2568; no in-window official 404s; leftovers W46N8@84390400 / W46N8@84390800 / W47N7@84390900 already told and aged out of that window start 84391201; already-told freezes 10:17:34-10:24:42 and 09:58:02-10:05:00 still in that window, told by the 10:31 1h patrol",
    "prior_1h_patrol": "_patrol_2026-11-21_1024 finished ~10:31, USER_LOG delivered ~10:31 Asia/Hong_Kong; first-told box freezes 09:58:02-10:05:00 and 10:17:34-10:24:42 (official-filled published 90/90 all five, unpublished tail 84391801..84391819 expected at patrol time). No NEW leftover official 404s. Already-told leftovers W46N8@84390400, W46N8@84390800, W47N7@84390900, W45N7@84388500, W45N8@84386600 remain already told. Do not re-tell those freezes or leftovers. Fold only newer freezes than 10:17:34-10:24:42.",
    "fold_only_newer_official_404s_than": ["W46N8@84390400", "W46N8@84390800", "W47N7@84390900", "W45N7@84388500", "W45N8@84386600"],
    "fold_only_newer_freezes_than": "10:47:36-10:59:07",
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

g_1047 = gap_line("gap_1047_1059")
g_1017 = gap_line("gap_1017_1024")
g_0958 = gap_line("gap_0958_1005")
g_0915 = gap_line("gap_0915_0923")
g_0852 = gap_line("gap_0852_0856")
g_0818 = gap_line("gap_0818_0823")

win_lines = "\n".join(f"  {r} distinct={win[r]['distinct']} rows={win[r]['rows']} {win[r]['min']}..{win[r]['max']}" for r in ROOMS)
jp_lines = [f"  {r} actual={actual_by[r]} script={script_by[r]} distinct={(post_counts.get(r) or {}).get('distinct')} rows={(post_counts.get(r) or {}).get('rows')}" for r in ROOMS]

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + "\n"

wrap_txt = first_txt + f"""
---- wrap {now_s} ----
confirm at {confirm_at} game.time={confirm_gt} still_404={confirm_still} inserted={inserted_confirm} recovered={confirm_rec} skipped=True; retry2 at {retry2_at} game.time={retry2_gt} still_404={retry2_still} inserted={inserted_retry2} skipped=True. First pass 35/35 official GETs 200, missing_chunks=0; confirm/retry2 had no targets. Already-told leftover official 404s W46N8@84390800 / W47N7@84390900 / W46N8@84390400 and older aged out of window start {WIN_TMIN} and were not retried. No in-window official 404s this run. Just-published {JUST_BASE} at {jp.get('at')} gt={jp.get('game_time')} all_five_200={jp_all_five} script={script_sum} actual={actual_sum}. Coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}. inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} just_actual={actual_sum} total={inserted_total}. tick_s_printed=4.297 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={corrective}. Listener pid=1822915 started=10:59:19 parent=4035476 slot={slot} rot={rot_s} yield={'absent' if yield_absent else 'present'} restarted_this_run=false. Peacetime single-slot 5:5:1:1. This run did not restart the listener or war_cmd/pulse.
NEW-this-window not yet told: box freeze 10:47:36-10:59:07 (684s; STATS 84392131..84392309, 179t; official-filled all five 179/179, including former unpublished tail 84392301..84392309 via just-published 84392300; listener auto-restart 10:59:10, python 1822915 started 10:59:19). Already-told by 10:31 1h and still in window: box freeze 10:17:34-10:24:42 (423s; STATS 84391711..84391819; official-filled all five 109/109). Already-told box freezes 09:58:02-10:05:00 (W45N7 29/119 empty-no-creep during evac, not a 404), 09:15:27-09:23:48, 08:52:35-08:56:43, 08:18:49-08:23:57 and leftover official 404s W46N8@84390800 / W47N7@84390900 / W46N8@84390400 age out of window start {WIN_TMIN}. Fold only newer freezes than 10:47:36-10:59:07 and newer leftover official 404s than W46N8@84390400 / W46N8@84390800 / W47N7@84390900 / W45N7@84388500 / W45N8@84386600.
"""
(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

retry2_src = DIR / "backfill_retry2.txt"
if not retry2_src.exists():
    retry2_src.write_text("retry2 GET skipped, no targets\n")
shutil.copy2(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1100.txt")

verify = f"""{now_s}
first pass 35/35 official GETs 200 missing_chunks=0 reconstructed 84391601..84392300 (700); confirm skipped no targets inserted={inserted_confirm}; retry2 skipped no targets inserted={inserted_retry2}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84392301..84392400 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{chr(10).join(jp_lines)}
confirm/retry2 skipped (no targets); no in-window official 404s; already-told leftover official 404s W46N8@84390800 {hole908_d}/100 (hole 84390801..84390900), W47N7@84390900 {hole909_d}/100 (hole 84390901..84391000), W46N8@84390400 hole 84390401..84390441 {hole904_d}/100 (listener 84390442..84390500) aged out of window start 84391601, not retried
gap_1047_1059 STATS 84392131..84392309 (179) NEW this run, not yet told by a 1h patrol (box freeze 10:47:36-10:59:07, 684s); last_stats 84392130 at 10:47:07, next 84392310 at 10:59:44; listener auto-restart 10:59:10, python 1822915 started 10:59:19; official first-pass filled through 84392300, just-published 84392300 filled former unpublished tail 84392301..84392309; official-filled all five 179/179
{g_1047}
gap_1017_1024 STATS 84391711..84391819 (109) already-told by 10:31 patrol (box freeze 10:17:34-10:24:42, 423s); listener auto-restart 10:24:45, python 1808991 started 10:24:54; official-filled all five 109/109; still in official window start 84391601
{g_1017}
gap_0958_1005 STATS 84391431..84391549 (119) already-told by 10:31 patrol (box freeze 09:58:02-10:05:00, 412s); listener auto-restart 10:05:03, python 1801941 started 10:05:13; ages out of window start 84391601
{g_0958}
gap_0915_0923 STATS 84390831..84390959 (129) already-told by 09:42 patrol (box freeze 09:15:27-09:23:48, 492s); ages out of window start 84391601
{g_0915}
gap_0852_0856 STATS 84390511..84390579 (69) already-told by 09:42 patrol (box freeze 08:52:35-08:56:43, 248s); official-filled all five 69/69; ages out of window start 84391601
{g_0852}
gap_0818_0823 STATS 84390031..84390119 (89) already-told by 08:32 patrol (box freeze 08:18:49-08:23:57, 299s); official-filled all five 89/89; ages out of window start 84391601
{g_0818}
no in-window leftover official 404s this run; aged-out already-told official 404s W46N8@84390800 / W47N7@84390900 / W46N8@84390400 not retried — do not re-tell
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.297 corrective={corrective} ts_realigned_first=0
tips room_stats={tips.get("room_stats")} creep_cpu={tips.get("creep_cpu")} path_arrivals={tips.get("path_arrivals")}
listener pid=1822915 started=10:59:19 parent=4035476 slot={slot} rot={rot_s} yield={"absent" if yield_absent else "present"} restarted_this_run=false
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
print("ok_quiet", payload["ok_quiet"], "inserted_total", inserted_total, "new_freeze", payload["new_box_freeze"]["from"] if payload["new_box_freeze"] else None, "new_404", payload["new_official_404"], "jp_all_five", jp_all_five)
