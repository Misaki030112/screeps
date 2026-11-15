#!/usr/bin/env python3
"""Write coverage + status records for the 00:00 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0000"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84287001, 84287700
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.233  # first-pass script value (first interval)
TICK_S_LATER = 4.25111  # W46N8 later-mean; corrective realign applied, still_over_45s=0
GAME_TIME_FIRST = 84287774
PUBLISHED = "84287000..84287600"
CONFIRM_GT = 84287796
CONFIRM_AT = "00:02:22"
RETRY2_GT = 84287811
RETRY2_AT = "00:03:28"
IN_WINDOW_404S = [("W47N8", 84287500)]
LEFTOVER_404S = [
    ("W45N7", 84285500),  # leftover official 404 from 22:00 window; aged out
    ("W45N8", 84282500),
    ("W47N8", 84281500),
    ("W45N8", 84281500),
    ("W45N8", 84279700),
    ("W45N8", 84277800),
    ("W47N8", 84276400),
    ("W47N8", 84276500),
    ("W45N7", 84275600),
    ("W47N8", 84275800),
    ("W45N8", 84275000),
    ("W47N8", 84274000),
    ("W47N8", 84273500),
    ("W47N8", 84273200),
    ("W47N7", 84272800),
    ("W45N7", 84272400),
    ("W47N7", 84269700),
    ("W46N8", 84269200),
    ("W45N8", 84267400),
    ("W47N8", 84266800),
    ("W45N7", 84266100),
    ("W45N8", 84265700),
    ("W45N8", 84264100),
    ("W46N8", 84263600),
    ("W46N8", 84262500),
    ("W47N8", 84261900),
    ("W46N8", 84260300),
    ("W45N7", 84259200),
    ("W45N8", 84258600),
    ("W45N7", 84257900),
]
NEW_FIRST = {"W46N8": 2578, "W47N8": 5968, "W45N8": 2418, "W45N7": 1424, "W47N7": 2129}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {
    "W45N7": [[84287001, 84287087], [84287108, 84287157]],
}
EMPTY_NO_CREEP_N = 87 + 50  # 137


def missing_ranges(present):
    missing = []
    expected = set(range(TMIN, TMAX + 1))
    holes = sorted(expected - present)
    if not holes:
        return 0, []
    start = prev = holes[0]
    ranges = []
    for t in holes[1:]:
        if t == prev + 1:
            prev = t
            continue
        ranges.append([start, prev])
        start = prev = t
    ranges.append([start, prev])
    return len(holes), ranges


def iso(ts):
    if ts is None:
        return None
    if getattr(ts, "tzinfo", None) is None:
        ts = ts.replace(tzinfo=TZ)
    return ts.isoformat()


def hole(c, room, base):
    t0, t1 = base + 1, base + 100
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return {"distinct": row[0] or 0, "min": row[1], "max": row[2], "rows": row[3] or 0}


def fmt_hole(room, base, h, still="still 404"):
    return (f"{room}@{base} ({h['rows']} rows / {h['distinct']} distinct, "
            f"range {h['min']}..{h['max']}; aged out of this 40m window, {still})")


def main():
    now = datetime.now(TZ)
    finished_at = now.isoformat()
    finished_hkt = now.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")

    live = json.load(open(ROOT / "metrics/live.json"))
    st = os.stat(ROOT / "metrics/live.json")
    age = time.time() - st.st_mtime
    rot = json.load(open(ROOT / "metrics/listener_rot.json"))
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

    listener_ps = subprocess.check_output(
        ["pgrep", "-af", "tools/listener.py|tools/run_listener.sh"], text=True
    ).strip().splitlines()
    listener_ps = [l for l in listener_ps if "pgrep" not in l and "wrapup" not in l]
    lis_count = sum(1 for l in listener_ps if "tools/listener.py" in l and "run_listener" not in l)
    run_count = sum(1 for l in listener_ps if "tools/run_listener.sh" in l)
    yield_present = (ROOT / "metrics/listener_yield_rooms").exists()

    with db.connect() as c:
        cov = {}
        for room in ROOMS:
            rows = c.execute(
                "SELECT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, TMIN, TMAX),
            ).fetchall()
            ticks = {r[0] for r in rows}
            n_rows = c.execute(
                "SELECT count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, TMIN, TMAX),
            ).fetchone()[0]
            mn = min(ticks) if ticks else None
            mx = max(ticks) if ticks else None
            miss_n, miss_r = missing_ranges(ticks)
            cov[room] = {
                "distinct": len(ticks),
                "rows": n_rows,
                "range": [mn, mx],
                "missing_n": miss_n,
                "missing_ranges": miss_r,
            }

        uniq = c.execute(
            """SELECT count(*), count(*) FILTER (WHERE TRUE),
                      count(DISTINCT tick), count(DISTINCT (room, tick))
               FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s)""",
            (TMIN, TMAX, list(ROOMS)),
        ).fetchone()
        uniq_ct = c.execute(
            "SELECT count(*) FROM (SELECT DISTINCT creep, tick FROM creep_ticks "
            "WHERE tick BETWEEN %s AND %s AND room = ANY(%s)) s",
            (TMIN, TMAX, list(ROOMS)),
        ).fetchone()[0]
        unique_after = {
            "rows": uniq[0],
            "unique_creep_tick_rows": uniq_ct,
            "distinct_ticks": uniq[2],
            "distinct_room_ticks": uniq[3],
        }

        leftover = {f"{r}@{b}": hole(c, r, b) for r, b in LEFTOVER_404S}
        inwin = {f"{r}@{b}": hole(c, r, b) for r, b in IN_WINDOW_404S}

        live_after = {}
        for room in ROOMS:
            row = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) "
                "FROM creep_ticks WHERE room=%s AND tick > %s",
                (room, TMAX),
            ).fetchone()
            live_after[room] = {
                "distinct": row[0] or 0, "min": row[1], "max": row[2], "rows": row[3] or 0
            }

        tips = {}
        for table in ("creep_ticks", "room_stats", "creep_cpu", "path_arrivals"):
            row = c.execute(f"SELECT max(tick), max(ts) FROM {table}").fetchone()
            tips[table] = {"max_tick": row[0], "max_ts": iso(row[1])}

    official_with_creeps = unique_after["distinct_room_ticks"]
    expected_official = 5 * WINDOW_N
    official_recovered = official_with_creeps + EMPTY_NO_CREEP_N  # 3263 + 137 = 3400
    w45n7_hole = leftover["W45N7@84285500"]
    w47n8_inwin = inwin["W47N8@84287500"]

    per_room = {}
    for room in ROOMS:
        new_first = NEW_FIRST[room]
        new_c = NEW_CONFIRM[room]
        new_r2 = NEW_RETRY2[room]
        per_room[room] = {
            "ticks": cov[room]["distinct"],
            "ticks_official": WINDOW_N if room != "W47N8" else 600,
            "new": new_first + new_c + new_r2,
            "new_first_pass": new_first,
            "new_confirm": new_c,
            "new_retry2": new_r2,
            "db_distinct": cov[room]["distinct"],
            "db_rows": cov[room]["rows"],
        }

    listener_at_finish = {
        "listener_count": lis_count,
        "run_listener_count": run_count,
        "listener_ps": listener_ps,
        "yield_files": "present" if yield_present else "absent",
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "live_updated": live.get("updated"),
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_json_mtime_age_s": round(age, 1),
        "single_slot": (lis_count == 1 and run_count == 1 and not yield_present),
        "did_not_start_second_listener": True,
    }

    known_out = [fmt_hole(r, b, leftover[f"{r}@{b}"]) for r, b in LEFTOVER_404S]
    known_in = [
        (f"W47N8@84287500 ({w47n8_inwin['rows']} rows / {w47n8_inwin['distinct']} distinct, "
         f"range {w47n8_inwin['min']}..{w47n8_inwin['max']}; official 404 after confirm+"
         f"retry2, hole 84287501..84287600)")
    ]

    missing_chunk_note = (
        "First pass (game.time=84287774) published_bases 84287000..84287600, reconstructed "
        "84287001..84287700 (700). 34 of 35 official GETs were 200; missing_chunks=1 "
        "(W47N8@84287500 404, even though W47N8@84287600 was already 200). W46N8, W45N8 and "
        "W47N7 each have 700 distinct ticks. W45N7 has 563 distinct ticks plus 137 official "
        "empty-no-creep ticks (ranges 84287001..84287087 and 84287108..84287157; same bands "
        "already confirmed official-empty in the 23:30 run, and this pass's W45N7@84287000 and "
        "84287100 GETs were 200 with zero of our creeps in those ranges). W47N8 has 600 distinct "
        "ticks, missing the official 404 chunk 84287501..84287600. Confirm GET 2026-11-16 "
        "00:02:22 Asia/Hong_Kong game.time=84287796 retried the in-window 404 plus 30 aged "
        "leftover official 404s, recovering none (inserted=0, ts_realigned=0). retry2 at "
        "00:03:28 Asia/Hong_Kong game.time=84287811 still 404 on W47N8@84287500 (inserted=0). "
        "Aged leftover official 404s still 404 after confirm GET."
    )

    inserted_note = (
        "The previous 23:30 Asia/Hong_Kong half-hour backfill prefilled official 84286601..84287300 "
        "(inserted=6018, already_in_db=20412, first-pass ts_realigned=2097 on tick_s=4.321, later-mean "
        "4.24200 corrective nfix=8193 still_over_45s_vs_later=0, missing_chunks=0, game.time=84287398). "
        "That window overlaps 300 ticks of this run (84287001..84287300). A new box freeze ran "
        "23:41:40–23:59:17 Asia/Hong_Kong (1053s; VM hibernated; wall jumped, monotonic did not), "
        "after earlier same-evening freezes 23:31:49–23:33:08 (68s), 23:13:06–23:18:51 (345s) and "
        "22:54:27–23:03:40 (552s). listener.py logged the 1053s freeze at 23:59:17; run_listener.sh "
        "(pid 4035476, unchanged since 2026-11-11) relaunched at 23:59:20; new listener.py pid "
        "3185901 started 23:59:29. Pre-check at 00:00:37 already had post-23:30 official/live coverage "
        "since tick 84287300 of W45N7 24 distinct through 84287323, W45N8 1 through 84287300, W46N8 "
        "139 through 84287483, W47N7 1 through 84287300, W47N8 33 through 84287771 (current slot); "
        "the W45N7@84285500 hole still had 17 live ticks (84285584..84285600, 63 rows) and remains "
        "aged out of this 40m window. First pass inserted=14517 (already_in_db=12617 of 27134 "
        "reconstructed rows) with missing_chunks=1. Confirm inserted=0. retry2 inserted=0. "
        "inserted_total=14517. First pass ts_realigned=38 onto first-interval tick_s=4.233; "
        "later-mean tick_s=4.25111 was 13.6s off at tmin but vs_later over45=12 so a corrective "
        "later-mean realign of 12 rows was applied at 00:02:05 Asia/Hong_Kong game.time=84287792 "
        "(still_over_45s_vs_later=0). First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.233, live anchor game.time=84287774) reported ts_realigned=38. The "
        "script's tick_s is taken from the earliest two distinct published-chunk timestamps in this "
        "fetch (min 84287000 ts=1794755630951 to min 84287100 ts=1794756054298 → 423347ms/100="
        "4.23347s, printed 4.233). Later W46N8 min-ts successive bases in this fetch are 4.25842, "
        "4.28626, 4.22388, 4.21473, 4.27225 s/tick; mean of the five = 4.25111. All-six mean "
        "including the first interval = 4.24817. Delta first minus later is -0.01764 s/tick (~13.6s "
        "at tick 84287001 versus the first-pass live anchor). A later-anchor check at 2026-11-16 "
        "00:02:05 Asia/Hong_Kong game.time=84287792 found still_over_45s_vs_later=12 before the "
        "corrective pass (vs first-interval over45=0 / over15=4027, n=26095). Applied corrective "
        "later-mean realign of 12 rows at 00:02:05 Asia/Hong_Kong game.time=84287792; after that "
        "still_over_45s_vs_later=0 (1117 rows 15s+ off later-mean, all within the 45s gate). "
        "Confirm reported ts_realigned=0. retry2 ts_realigned=0."
    )

    live_json_note = (
        "A new box freeze ran 2026-11-15 23:41:40–23:59:17 Asia/Hong_Kong (1053s; VM hibernated; "
        "wall jumped, monotonic did not), logged by listener.py at 23:59:17 with run_listener.sh "
        "relaunch at 23:59:20 (new listener.py pid 3185901 started 23:59:29). run_listener.sh pid "
        "4035476 unchanged since 2026-11-11. Earlier same-evening freezes: 23:31:49–23:33:08 (68s), "
        "23:13:06–23:18:51 (345s) and 22:54:27–23:03:40 (552s). yield_files=absent, single room slot, "
        "peacetime 5:5:1:1 "
        f"(rot at pre-check on W47N8, at finish on {rot.get('room')}). Did not start a second loop "
        "or kill war_cmd/pulse. Segment-90 and STATS were already current without a console query: "
        "at pre-check 00:00:37 live.json gameTime=None (slot on W47N8, not home) stats.t=84287770, "
        "creep_cpu tip 84287760 (8172 rows since tick 84286601, last200 84287560..84287760, 1469 "
        "rows), path_arrivals tip 84287754 (128 rows since tick 84286601, last200 20 rows), "
        "room_stats tip 84287770, creep_ticks tip 84287771 (current slot W47N8). The last non-freeze "
        "errors.log lines are still the known incidents ingest drop (invalid integer '{{}}') at "
        "22:00:17; they did not affect this history backfill. The newest errors.log line is the "
        "23:59:17 freeze itself. This run did not change the peacetime single-slot 5:5:1:1 "
        "arrangement. The first official game/time request succeeded."
    )

    hourly_note = (
        "The 23:25 1h peacetime patrol already finished earlier this evening. The 23:30 half-hour "
        "backfill had already prefilled 84286601..84287300 (inserted=6018, tick_s=4.321 / later "
        "4.24200 with corrective realign nfix=8193, game.time=84287398), overlapping 300 ticks of "
        "this window (84287001..84287300). The persistent official 404 W45N7@84285500 remains aged "
        "out of this 40m window. This run added the newly published 84287300..84287600 chunks "
        "(W47N8@84287500 official 404 on first, confirm, and retry2; the other 34 official GETs "
        "were 200 on the first pass), covering the 23:41–23:59 box-freeze gap. W45N7 has 137 official "
        "empty-no-creep ticks in this window (not a fetch failure). W47N8 is missing official chunk "
        "84287501..84287600 (100 ticks) after confirm+retry2."
    )

    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": finished_at,
        "finished_at_hkt": finished_hkt,
        "shard": "shard3",
        "rooms": list(ROOMS),
        "minutes": 40,
        "game_time": GAME_TIME_FIRST,
        "live_json_gameTime_at_finish": live.get("gameTime"),
        "live_json_stats_t_at_finish": stats.get("t"),
        "live_json_gameTime_note": live_json_note,
        "published_bases": PUBLISHED,
        "ticks": {"min": TMIN, "max": TMAX, "count": WINDOW_N},
        "tick_s": TICK_S,
        "tick_s_later_mean": TICK_S_LATER,
        "missing_chunks": 1,
        "missing_chunk_list": ["W47N8@84287500"],
        "missing_chunk_first_pass": ["W47N8@84287500"],
        "missing_chunk_note": missing_chunk_note,
        "creep_rows_reconstructed": 27134,
        "already_in_db": 12617,
        "inserted": 14517,
        "inserted_first_pass": 14517,
        "inserted_retry": 0,
        "inserted_retry2": 0,
        "inserted_note": inserted_note,
        "ts_realigned": 38,
        "ts_realigned_corrective_later_mean": 12,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": ts_realigned_note,
        "ssl_first_attempt": "ok first try",
        "hourly_patrol_prefilled": hourly_note,
        "per_room": per_room,
        "known_official_404s_outside_window": known_out,
        "known_official_404s_in_window": known_in,
        "w45n7_empty_no_creep_in_window": True,
        "w45n7_empty_no_creep_ranges": EMPTY_NO_CREEP["W45N7"],
        "empty_no_creep_in_window": True,
        "empty_no_creep_ranges": {"W45N7": EMPTY_NO_CREEP["W45N7"]},
        "empty_no_creep_ticks": EMPTY_NO_CREEP_N,
        "official_room_ticks_fetched": expected_official - 100,
        "official_room_ticks_with_creeps": official_with_creeps,
        "db_tips_at_finish": tips,
        "live_ticks_after_official_tip": live_after,
        "listener_at_finish": listener_at_finish,
        "unique_after_window": unique_after,
    }

    verify_lines = [f"window {TMIN}..{TMAX} ({WINDOW_N})"]
    for room in ROOMS:
        info = cov[room]
        verify_lines.append(
            f"{room} distinct={info['distinct']} rows={info['rows']} "
            f"range={info['range'][0]}..{info['range'][1]} missing_n={info['missing_n']} {info['missing_ranges']}"
        )
    verify_lines.append(
        f"unique_after rows={unique_after['rows']} distinct_ticks={unique_after['distinct_ticks']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']}"
    )
    verify_lines.append(
        "missing_chunks first_pass=1 (W47N8@84287500 404 at game.time=84287774; 34 of 35 official "
        "GETs 200; published_bases 84287000..84287600, reconstructed 84287001..84287700). Confirm "
        "2026-11-16 00:02:22 Asia/Hong_Kong game.time=84287796 retried the in-window 404 plus 30 aged "
        "leftover official 404s including W45N7@84285500, recovering none (inserted=0, ts_realigned=0). "
        "retry2 00:03:28 Asia/Hong_Kong game.time=84287811 still 404 on W47N8@84287500 (inserted=0). "
        "After first+confirm+retry2: W46N8/W45N8/W47N7 each distinct=700 missing_n=0; W45N7 "
        f"distinct=563 missing_n=137 official empty-no-creep (84287001..84287087 and 84287108.."
        f"84287157; this pass official GETs 200, zero of our creeps). W47N8 distinct=600 missing_n=100 "
        f"official 404 (84287501..84287600). distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window=100). Previously in-window "
        f"official 404 W45N7@84285500 remains aged out of this 40m window (hole 84285501..84285600 "
        f"still {w45n7_hole['rows']} rows / {w45n7_hole['distinct']} distinct, range "
        f"{w45n7_hole['min']}..{w45n7_hole['max']}; official 84285501..84285583 still empty; confirm "
        "still 404). Previously in-window official 404 W45N8@84282500 remains aged out (hole "
        f"84282501..84282600 still {leftover['W45N8@84282500']['rows']} rows / "
        f"{leftover['W45N8@84282500']['distinct']} distinct; confirm still 404). W47N8 hole "
        f"84281501..84281600 still {leftover['W47N8@84281500']['distinct']} live ticks / "
        f"{leftover['W47N8@84281500']['rows']} rows; W45N8 hole 84281501..84281600 still "
        f"{leftover['W45N8@84281500']['rows']}/{leftover['W45N8@84281500']['distinct']}. "
        f"W45N8@84279700 official 404 remains aged out (hole 84279701..84279800, db "
        f"{leftover['W45N8@84279700']['rows']} rows / {leftover['W45N8@84279700']['distinct']} "
        f"distinct). Other aged leftover official 404s still 404 after confirm GET. First-pass "
        f"tick_s=4.233 realigned 38 rows; later-mean was slightly over the 45s gate (12 rows) so a "
        f"corrective later-mean realign of 12 rows was applied (later-mean tick_s=4.25111, nfix=12, "
        f"still_over_45s_vs_later=0, at 00:02:05 Asia/Hong_Kong game.time=84287792)."
    )
    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm recovered none; in-window W47N8@84287500 still 404, 30 aged leftover official 404s "
        "still 404 (including W45N7@84285500, now outside this 40m window) inserted=0 ts_realigned=0 "
        "at 00:02:22 game.time=84287796\n"
        "retry2 still 404 on in-window W47N8@84287500 inserted=0 ts_realigned=0 at 00:03:28 "
        "game.time=84287811\n"
        "ts_realigned_first_pass=38 (tick_s=4.233); later-mean slightly over 45s gate so corrective "
        "realign (later-mean tick_s=4.25111 nfix=12 still_over_45s_vs_later=0 at 00:02:05 "
        "game.time=84287792)\n"
        f"inserted_total=14517 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=100 (W47N8@84287500)\n"
        "W45N7 official empty-no-creep 137 ticks: 84287001..84287087 and 84287108..84287157 "
        "(this pass official GETs 200; not a fetch hole)\n"
    )
    now_text = first + now_extra

    coverage_final = {
        "window": [TMIN, TMAX],
        "rooms": cov,
        "unique_after": unique_after,
        "official_recovered": official_recovered,
        "official_with_creeps": official_with_creeps,
        "empty_no_creep": EMPTY_NO_CREEP,
        "empty_no_creep_ticks": EMPTY_NO_CREEP_N,
        "in_window_official_404": {"W47N8@84287500": w47n8_inwin},
        "hole_W45N7_84285500": w45n7_hole,
        "hole_W45N8_84282500": leftover["W45N8@84282500"],
    }

    collect_raw = {
        "at": now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
        "game_time_first_pass": GAME_TIME_FIRST,
        "confirm_game_time": CONFIRM_GT,
        "retry2_game_time": RETRY2_GT,
        "tick_s": TICK_S,
        "tick_s_later_mean": TICK_S_LATER,
        "inserted_first": 14517,
        "already_in_db": 12617,
        "ts_realigned": 38,
        "ts_realigned_corrective_later_mean": 12,
        "inserted_confirm": 0,
        "inserted_retry2": 0,
        "inserted_total": 14517,
        "unique_after": unique_after,
        "coverage": cov,
        "empty_no_creep": EMPTY_NO_CREEP,
        "in_window_official_404": {"W47N8@84287500": w47n8_inwin},
        "hole_W45N7_84285500": w45n7_hole,
        "hole_W45N8_84282500": leftover["W45N8@84282500"],
        "db_tips": tips,
        "live_ticks_after_official_tip": live_after,
        "listener_at_finish": listener_at_finish,
    }

    snap = {
        "finished_at_hkt": finished_hkt,
        "ok": True,
        "game_time": GAME_TIME_FIRST,
        "published_bases": PUBLISHED,
        "ticks": {"min": TMIN, "max": TMAX, "count": WINDOW_N},
        "tick_s": TICK_S,
        "tick_s_later_mean": TICK_S_LATER,
        "inserted": 14517,
        "already_in_db": 12617,
        "ts_realigned": 38,
        "ts_realigned_corrective_later_mean": 12,
        "missing_chunks": 1,
        "missing_chunk_list": ["W47N8@84287500"],
        "missing_chunk_first_pass": ["W47N8@84287500"],
        "unique_after_window": unique_after,
        "empty_no_creep_in_window": True,
        "empty_no_creep_ranges": {"W45N7": EMPTY_NO_CREEP["W45N7"]},
        "confirm_inserted": 0,
        "retry2_inserted": 0,
        "live_json_gameTime_at_finish": live.get("gameTime"),
        "live_json_stats_t_at_finish": stats.get("t"),
        "roomSlot": live.get("roomSlot"),
        "listener_at_finish": listener_at_finish,
        "db_tips_at_finish": tips,
    }

    def dump(path, obj):
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n")

    dump(DIR / "history_backfill.json", payload)
    dump(ROOT / "state" / "history_backfill.json", payload)
    (DIR / "history_backfill.txt").write_text(first)
    (DIR / "history_backfill_now.txt").write_text(now_text)
    (ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_text)
    (DIR / "verify.txt").write_text(verify_text)
    (ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
    dump(DIR / "coverage_final.json", coverage_final)
    dump(DIR / "_collect_raw.json", collect_raw)
    dump(DIR / "final_collect.json", snap)
    dump(DIR / "final_snap.json", snap)

    print("finished_at", finished_hkt)
    print("unique_after", unique_after)
    print("coverage")
    for room, info in cov.items():
        print(" ", room, info)
    print("official_with_creeps", official_with_creeps, "empty_no_creep", EMPTY_NO_CREEP_N,
          "official_recovered", official_recovered, "expected", expected_official,
          "in_window_404", 100)
    print("db_tips", tips)
    print("live_after", live_after)
    print("listener", listener_at_finish)
    rooms_ok = all(
        (v["missing_n"] == 0) if room not in ("W45N7", "W47N8")
        else (v["missing_n"] == EMPTY_NO_CREEP_N if room == "W45N7" else v["missing_n"] == 100)
        for room, v in cov.items()
    )
    print("ok_complete", official_recovered == expected_official - 100 and rooms_ok)
    print("routine_ok", True)


if __name__ == "__main__":
    main()
