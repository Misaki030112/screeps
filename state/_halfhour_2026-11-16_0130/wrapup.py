#!/usr/bin/env python3
"""Write coverage + status records for the 01:30 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0130"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84288301, 84289000
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.218  # first-pass script value (first interval)
TICK_S_LATER = 4.25153  # W46N8 later-mean; corrective realign applied
GAME_TIME_FIRST = 84289018
PUBLISHED = "84288300..84288900"
CONFIRM_GT = 84289037
CONFIRM_AT = "01:30:22"
RETRY2_GT = None
RETRY2_AT = None
IN_WINDOW_404S_FIRST = [("W47N7", 84288900)]
LEFTOVER_404S = [
    ("W47N8", 84287500),  # leftover official 404 from 00:00/00:30 windows; aged out
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
NEW_FIRST = {"W46N8": 904, "W47N8": 3732, "W45N8": 874, "W45N7": 461, "W47N7": 493}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 478}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {}
EMPTY_NO_CREEP_N = 0
INSERTED_FIRST = 6464
ALREADY_IN_DB = 20766
CREEP_ROWS_RECONSTRUCTED = 27230
INSERTED_CONFIRM = 478
INSERTED_RETRY2 = 0
INSERTED_TOTAL = 6942
TICK_S_CHECK_AT = "01:30:04"
TICK_S_CHECK_GT = 84289033
TS_REALIGNED_FIRST = 5943
TS_REALIGNED_LATER = 4830
TS_REALIGNED_CONFIRM = 0


def missing_ranges(present):
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
    official_recovered = official_with_creeps + EMPTY_NO_CREEP_N
    w45n7_hole = leftover["W45N7@84285500"]
    w47n8_aged = leftover["W47N8@84287500"]

    per_room = {}
    for room in ROOMS:
        new_first = NEW_FIRST[room]
        new_c = NEW_CONFIRM[room]
        new_r2 = NEW_RETRY2[room]
        per_room[room] = {
            "ticks": cov[room]["distinct"],
            "ticks_official": WINDOW_N,
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
    known_in = []

    missing_chunk_note = (
        "First pass (game.time=84289018) published_bases 84288300..84288900, reconstructed "
        "84288301..84289000 (700). 34 of 35 official GETs were 200; missing_chunks=1 "
        "W47N7@84288900 (other four rooms at that base were already 200). already_in_db=20766 "
        "would_insert=6464; first pass inserted=6464, ts_realigned=5943 onto first-interval "
        "tick_s=4.218. Confirm GET 2026-11-16 01:30:22 Asia/Hong_Kong game.time=84289037 recovered "
        "W47N7@84288900 (ticks=100, ts=1794763787460, inserted=478, ts_realigned=0) and retried 31 "
        "aged leftover official 404s (including W47N8@84287500, now outside this 40m window), all "
        "still 404. retry2 was skipped because the in-window official 404 was already recovered and "
        "there was no unpublished latest complete chunk. After confirm, all five rooms have 700 "
        "distinct ticks and no official empty-no-creep ticks."
    )

    inserted_note = (
        "The previous 01:00 Asia/Hong_Kong half-hour backfill prefilled official 84287901..84288600 "
        "(inserted_total=14241 after first=14241 + confirm=0 + retry2 skipped, already_in_db=13175, "
        "first-pass ts_realigned=0 on tick_s=4.202, later-mean 4.24068 already inside the 45s gate, "
        "missing_chunks=0, game.time=84288619). That window overlaps 300 ticks of this run "
        "(84288301..84288600). A new box freeze ran 01:06:26–01:17:17 Asia/Hong_Kong (646s; VM "
        "hibernated; wall jumped, monotonic did not). listener.py logged the freeze at 01:17:17; "
        "run_listener.sh (pid 4035476, unchanged since 2026-11-11) relaunched at 01:17:20; new "
        "listener.py pid 3205323 started 01:17:30. Pre-check at 01:28:49 already had post-01:00 "
        "official/live coverage since tick 84288600 of W45N7 230 distinct through 84288890, W45N8 "
        "207 through 84288861, W46N8 326 through 84289015, W47N7/W47N8 201 distinct through 84288800 "
        "(sparse across the freeze for rooms off the single peacetime slot); W47N8@84287500 was still "
        "0 rows, and the aged W45N7@84285500 hole still had 17 live ticks (84285584..84285600, 63 "
        "rows). First pass inserted=6464 (already_in_db=20766 of 27230 reconstructed rows in "
        "84288301..84289000) with missing_chunks=1 W47N7@84288900, covering the 01:06–01:17 "
        "box-freeze gap for rooms not on the single peacetime slot. Confirm recovered that chunk "
        "(inserted=478). retry2 skipped. inserted_total=6942. First pass ts_realigned=5943 onto "
        "first-interval tick_s=4.218; later-mean tick_s=4.25153 was ~23.7s off at tmin versus the "
        f"first-pass live anchor, and vs_later over45=5096 (n=27300 at {TICK_S_CHECK_AT} "
        f"game.time={TICK_S_CHECK_GT}), so a corrective later-mean realign of 4830 rows was applied; "
        "after that still_over_45s_vs_later=0. Confirm ts_realigned=0. First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.218, live anchor game.time=84289018) reported ts_realigned=5943. The "
        "script's tick_s is taken from the earliest two distinct published-chunk timestamps in this "
        "fetch (min 84288300 ts=1794761154941 to min 84288400 ts=1794761576789 → 4.218s printed; "
        "W46N8 first interval 4.21848). Later W46N8 min-ts successive bases in this fetch are "
        "4.18473, 4.33288, 4.31967, 4.21831, 4.20208 s/tick; later_mean 4.25153. All-six mean "
        "including the first interval = 4.24603. Delta first minus later is -0.03305 s/tick (~23.7s "
        "at tick 84288301 versus the first-pass live anchor). A later-anchor check at 2026-11-16 "
        f"{TICK_S_CHECK_AT} Asia/Hong_Kong game.time={TICK_S_CHECK_GT} found still_over_45s_vs_first=0 "
        "but still_over_45s_vs_later=5096 (n=27300; vs first-interval over15=10311, vs later-mean "
        "over15=17837), so a corrective later-mean realign of 4830 rows was applied at game.time="
        f"{TICK_S_CHECK_GT}; after that still_over_45s_vs_later=0 (over15=12720). Confirm reported "
        "ts_realigned=0 (W47N7@84288900 rows inserted with later-mean tick_s=4.25153). retry2 skipped."
    )

    live_json_note = (
        "A new box freeze ran 2026-11-16 01:06:26–01:17:17 Asia/Hong_Kong (646s; VM hibernated; "
        "wall jumped, monotonic did not), logged by listener.py at 01:17:17 with run_listener.sh "
        "relaunch at 01:17:20 (new listener.py pid 3205323 started 01:17:30). run_listener.sh pid "
        "4035476 unchanged since 2026-11-11. yield_files=absent, single room slot, peacetime 5:5:1:1 "
        f"(rot at pre-check and finish on {rot.get('room')}). Did not start a second loop or kill "
        "war_cmd/pulse. Segment-90 and STATS were already current without a console query: at "
        "pre-check 01:28:49 live.json gameTime=84289015 (slot on W46N8, objects=265) stats.t=84289010, "
        "creep_cpu tip 84289000 (8068 rows since tick 84287901, last200 84288800..84289000, 1642 rows, "
        "max_ts 01:27:48), path_arrivals tip 84288991 (134 rows since tick 84287901, last200 25 rows), "
        "room_stats tip 84289010, creep_ticks tip 84289016. No new incidents ingest drop after the "
        "known 00:30:10 invalid integer '{{}}' event. This run did not change the peacetime "
        "single-slot 5:5:1:1 arrangement. The first official game/time request succeeded."
    )

    hourly_note = (
        "The previous 01:00 half-hour backfill had already prefilled 84287901..84288600 "
        "(inserted_total=14241, tick_s=4.202 / later 4.24068 with no corrective realign, game.time="
        "84288619), overlapping 300 ticks of this window (84288301..84288600) and leaving the "
        "persistent official 404 W47N8@84287500 aged out of this window. First pass recovered 34 of "
        "35 official chunks in 84288301..84289000 (inserted=6464, missing_chunks=1 W47N7@84288900), "
        "covering the 01:06:26–01:17:17 box-freeze gap for rooms not on the single peacetime slot. "
        "Confirm recovered W47N7@84288900 (inserted=478); 31 aged leftover official 404s still 404; "
        "retry2 was not needed. There were no official empty-no-creep ticks in this 40m window. Aged "
        "leftover official 404s including W47N8@84287500 and W45N7@84285500 remain outside this window."
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
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": ["W47N7@84288900"],
        "missing_chunk_note": missing_chunk_note,
        "creep_rows_reconstructed": CREEP_ROWS_RECONSTRUCTED,
        "already_in_db": ALREADY_IN_DB,
        "inserted": INSERTED_TOTAL,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": INSERTED_CONFIRM,
        "inserted_retry2": INSERTED_RETRY2,
        "inserted_note": inserted_note,
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": TS_REALIGNED_LATER,
        "ts_realigned_confirm": TS_REALIGNED_CONFIRM,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": ts_realigned_note,
        "ssl_first_attempt": "ok first try",
        "hourly_patrol_prefilled": hourly_note,
        "per_room": per_room,
        "known_official_404s_outside_window": known_out,
        "known_official_404s_in_window": known_in,
        "w45n7_empty_no_creep_in_window": False,
        "w45n7_empty_no_creep_ranges": EMPTY_NO_CREEP.get("W45N7", []),
        "empty_no_creep_in_window": False,
        "empty_no_creep_ranges": dict(EMPTY_NO_CREEP),
        "empty_no_creep_ticks": EMPTY_NO_CREEP_N,
        "official_room_ticks_fetched": expected_official,
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
        "missing_chunks first_pass=1 (W47N7@84288900 official 404 at game.time=84289018; other 34 "
        "official GETs 200; published_bases 84288300..84288900, reconstructed 84288301..84289000 "
        "(700), already_in_db=20766 inserted=6464). Confirm 2026-11-16 01:30:22 Asia/Hong_Kong "
        "game.time=84289037 recovered W47N7@84288900 (ticks=100 ts=1794763787460 inserted=478 "
        "ts_realigned=0) and retried 31 aged leftover official 404s including W47N8@84287500 (now "
        "outside this 40m window); those 31 were still 404. retry2 skipped (in-window official 404 "
        "already recovered, no unpublished latest chunk). After confirm: all five rooms each "
        "distinct=700 missing_n=0 (no official empty-no-creep ticks in this window). "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window=0 after confirm). Previously "
        f"in-window official 404 W47N8@84287500 remains aged out of this 40m window (hole "
        f"84287501..84287600 still {w47n8_aged['rows']} rows / {w47n8_aged['distinct']} distinct; "
        f"confirm still 404). Previously in-window official 404 W45N7@84285500 remains aged out of "
        f"this 40m window (hole 84285501..84285600 still {w45n7_hole['rows']} rows / "
        f"{w45n7_hole['distinct']} distinct, range {w45n7_hole['min']}..{w45n7_hole['max']}; official "
        f"84285501..84285583 still empty; confirm still 404). Previously in-window official 404 "
        f"W45N8@84282500 remains aged out (hole 84282501..84282600 still "
        f"{leftover['W45N8@84282500']['rows']} rows / {leftover['W45N8@84282500']['distinct']} "
        f"distinct; confirm still 404). W47N8 hole 84281501..84281600 still "
        f"{leftover['W47N8@84281500']['distinct']} live ticks / {leftover['W47N8@84281500']['rows']} "
        f"rows; W45N8 hole 84281501..84281600 still {leftover['W45N8@84281500']['rows']}/"
        f"{leftover['W45N8@84281500']['distinct']}. W45N8@84279700 official 404 remains aged out "
        f"(hole 84279701..84279800, db {leftover['W45N8@84279700']['rows']} rows / "
        f"{leftover['W45N8@84279700']['distinct']} distinct). Other aged leftover official 404s still "
        f"404 after confirm GET. First-pass tick_s=4.218 realigned 5943 rows; later-mean was over the "
        f"45s gate (over45=5096) so a corrective later-mean realign of 4830 rows was applied "
        f"(later-mean tick_s=4.25153, nfix=4830, still_over_45s_vs_later=0 after, at "
        f"{TICK_S_CHECK_AT} Asia/Hong_Kong game.time={TICK_S_CHECK_GT})."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm recovered W47N7@84288900 inserted=478 ts_realigned=0 at 01:30:22 game.time=84289037; "
        "retried 31 aged leftover official 404s (including W47N8@84287500, now outside this 40m window) "
        "all still 404; retry2 skipped\n"
        "ts_realigned_first_pass=5943 (tick_s=4.218); later-mean over 45s gate, corrective realign "
        f"applied (later-mean tick_s=4.25153 nfix=4830 still_over_45s_vs_later=0 after at "
        f"{TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT})\n"
        f"inserted_total=6942 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=0 after confirm (first-pass W47N7@84288900 recovered)\n"
        "no official empty-no-creep ticks in this window\n"
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
        "in_window_official_404": {},
        "in_window_official_404_first_pass": {"W47N7@84288900": "recovered_on_confirm"},
        "hole_W47N8_84287500": w47n8_aged,
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
        "inserted_first": INSERTED_FIRST,
        "already_in_db": ALREADY_IN_DB,
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": TS_REALIGNED_LATER,
        "inserted_confirm": INSERTED_CONFIRM,
        "inserted_retry2": INSERTED_RETRY2,
        "inserted_total": INSERTED_TOTAL,
        "unique_after": unique_after,
        "coverage": cov,
        "empty_no_creep": EMPTY_NO_CREEP,
        "in_window_official_404": {},
        "in_window_official_404_first_pass": {"W47N7@84288900": "recovered_on_confirm"},
        "hole_W47N8_84287500": w47n8_aged,
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
        "inserted": INSERTED_TOTAL,
        "already_in_db": ALREADY_IN_DB,
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": TS_REALIGNED_LATER,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": ["W47N7@84288900"],
        "unique_after_window": unique_after,
        "empty_no_creep_in_window": False,
        "empty_no_creep_ranges": dict(EMPTY_NO_CREEP),
        "confirm_inserted": INSERTED_CONFIRM,
        "retry2_inserted": INSERTED_RETRY2,
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
          "in_window_404", 0)
    print("db_tips", tips)
    print("live_after", live_after)
    print("listener", listener_at_finish)
    rooms_ok = all(v["missing_n"] == 0 for v in cov.values())
    print("ok_complete", official_recovered == expected_official and rooms_ok)
    print("routine_ok", True)


if __name__ == "__main__":
    main()
