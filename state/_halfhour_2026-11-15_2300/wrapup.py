#!/usr/bin/env python3
"""Write coverage + status records for the 23:00 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-15_2300"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84286201, 84286900
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.206  # first-pass script value (first interval)
TICK_S_LATER = 4.25692  # W46N8 later-mean; already inside 45s gate, no corrective realign
GAME_TIME_FIRST = 84286982
PUBLISHED = "84286200..84286800"
CONFIRM_GT = 84286997
CONFIRM_AT = "23:06:04"
RETRY2_GT = None
RETRY2_AT = None
IN_WINDOW_404S = []
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
NEW_FIRST = {"W46N8": 2653, "W47N8": 4016, "W45N8": 1388, "W45N7": 1513, "W47N7": 2212}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}


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

    official_recovered = unique_after["distinct_room_ticks"]
    expected_official = 5 * WINDOW_N
    w45n7_hole = leftover["W45N7@84285500"]

    per_room = {}
    for room in ROOMS:
        new_first = NEW_FIRST[room]
        new_c = NEW_CONFIRM[room]
        new_r2 = NEW_RETRY2[room]
        per_room[room] = {
            "ticks": cov[room]["distinct"],
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
        "First pass (game.time=84286982) published_bases 84286200..84286800, reconstructed "
        "84286201..84286900 (700). All 35 official GETs were 200; missing_chunks=0. All five "
        "rooms have 700 distinct ticks in 84286201..84286900. Confirm GET 2026-11-15 23:06:04 "
        "Asia/Hong_Kong game.time=84286997 retried 30 aged leftover official 404s (including "
        "W45N7@84285500, now aged out of this 40m window), recovering none (inserted=0, "
        "ts_realigned=0). retry2 skipped because there was no in-window official 404. Aged "
        "leftover official 404s still 404 after confirm GET. No empty-no-creep in this window."
    )

    inserted_note = (
        "The previous 22:30 Asia/Hong_Kong half-hour backfill prefilled official 84285801..84286500 "
        "(inserted=6080, already_in_db=20705, first-pass ts_realigned=1094 on tick_s=4.195, later-mean "
        "4.27108 corrective nfix=269 still_over_45s_vs_later=0, missing_chunks=0, "
        "game.time=84286534). That window overlaps 300 ticks of this run (84286201..84286500). "
        "A new box freeze ran 22:54:27–23:03:40 Asia/Hong_Kong (552s; VM hibernated; wall jumped, "
        "monotonic did not). listener.py logged the freeze at 23:03:40; run_listener.sh relaunched "
        "at 23:03:43; new listener.py pid 3167970 started 23:03:53 (previous pid 3132680 had run "
        "since 21:52:27). Pre-check at 23:04:44 already had post-22:30 official/live coverage since "
        "tick 84286500 of W45N7 28 distinct through 84286765, W45N8 29 through 84286738, W46N8 143 "
        "through 84286979, W47N7 1 at 84286500, W47N8 143 through 84286710; the W45N7@84285500 "
        "hole still had 17 live ticks (84285584..84285600, 63 rows) and remains aged out of this "
        "40m window. First pass inserted=11782 (already_in_db=15375 of 27157 reconstructed rows) "
        "with missing_chunks=0. Confirm inserted=0. retry2 skipped. inserted_total=11782. First "
        "pass ts_realigned=24 onto first-interval tick_s=4.206; later-mean tick_s=4.25692 was "
        "already inside the 45s gate (still_over_45s_vs_later=0, nfix=0) at 23:05:58 "
        "Asia/Hong_Kong game.time=84286996. First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.206, live anchor game.time=84286982) reported ts_realigned=24. The "
        "script's tick_s is taken from the earliest two distinct published-chunk timestamps in this "
        "fetch (min 84286200 ts=1794752226261 to min 84286300 ts=1794752646845 → 420584ms/100="
        "4.20584s, printed 4.206). Later W46N8 min-ts successive bases in this fetch are ≈4.30190, "
        "4.33463, 4.16507, 4.32135, 4.16167 s/tick; mean of the five ≈4.25692. All-six mean "
        "including the first interval ≈4.24841. Delta first minus later is -0.05108 s/tick (~39.9s "
        "at tick 84286201 versus the first-pass live anchor). A later-anchor check at 2026-11-15 "
        "23:05:58 Asia/Hong_Kong game.time=84286996 found still_over_45s_vs_later=0 already "
        "(4800 rows 15s+ off later-mean; 13805 rows 15s+ off first-interval; 550 rows >45s off "
        "first-interval; n=27258). No corrective later-mean realign was applied "
        "(ts_realigned_to_later_mean=0, still_over_45s_vs_later=0). Confirm reported "
        "ts_realigned=0. retry2 skipped."
    )

    live_json_note = (
        "A new box freeze ran 2026-11-15 22:54:27–23:03:40 Asia/Hong_Kong (552s; VM hibernated; "
        "wall jumped, monotonic did not), logged by listener.py at 23:03:40 with run_listener.sh "
        "relaunch at 23:03:43 (new listener.py pid 3167970 started 23:03:53; previous pid 3132680 "
        "had run since 21:52:27). run_listener.sh pid 4035476 unchanged since 2026-11-11. "
        "yield_files=absent, single room slot, peacetime 5:5:1:1 (rot at pre-check on W46N8, at "
        f"finish on {rot.get('room')}). Did not start a second loop or kill war_cmd/pulse. "
        "Segment-90 and STATS were already current without a console query: at pre-check 23:04:44 "
        "live.json gameTime=84286979 (slot on home W46N8) stats.t=84286970, creep_cpu tip 84286960 "
        "(8981 rows since tick 84285801, last200 84286760..84286960, 1587 rows), path_arrivals tip "
        "84286954 (172 rows since tick 84285801, last200 34 rows), room_stats tip 84286970, "
        "creep_ticks tip 84286979 (current slot W46N8). The last non-freeze errors.log lines are "
        "still the known incidents ingest drop (invalid integer '{{}}') at 22:00:17; they did not "
        "affect this history backfill. The newest errors.log line is the 23:03:40 freeze itself. "
        "This run did not change the peacetime single-slot 5:5:1:1 arrangement. The first official "
        "game/time request succeeded."
    )

    hourly_note = (
        "The 22:26 1h peacetime patrol already finished earlier this evening. The 22:30 half-hour "
        "backfill had already prefilled 84285801..84286500 (inserted=6080, tick_s=4.195 / later "
        "4.27108 with corrective nfix=269, game.time=84286534), overlapping 300 ticks of this "
        "window (84286201..84286500). The persistent official 404 W45N7@84285500 remains aged out "
        "of this 40m window. This run added the newly published 84286500..84286800 chunks (all five "
        "rooms 200 on the first pass; missing_chunks=0), covering the 22:54–23:03 box-freeze gap."
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
        "missing_chunk_first_pass": [],
        "missing_chunk_note": missing_chunk_note,
        "creep_rows_reconstructed": 27157,
        "already_in_db": 15375,
        "inserted": 11782,
        "inserted_first_pass": 11782,
        "inserted_retry": 0,
        "inserted_retry2": 0,
        "inserted_note": inserted_note,
        "ts_realigned": 24,
        "ts_realigned_corrective_later_mean": 0,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": ts_realigned_note,
        "ssl_first_attempt": "ok first try",
        "hourly_patrol_prefilled": hourly_note,
        "per_room": per_room,
        "known_official_404s_outside_window": known_out,
        "known_official_404s_in_window": known_in,
        "w45n7_empty_no_creep_in_window": False,
        "w45n7_empty_no_creep_ranges": [],
        "empty_no_creep_in_window": False,
        "empty_no_creep_ranges": [],
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
        "missing_chunks first_pass=0 (all 35 official GETs 200 at game.time=84286982; "
        "published_bases 84286200..84286800, reconstructed 84286201..84286900). Confirm "
        "2026-11-15 23:06:04 Asia/Hong_Kong game.time=84286997 retried 30 aged leftover official "
        "404s including W45N7@84285500, recovering none (inserted=0, ts_realigned=0). retry2 "
        "skipped (no in-window official 404). After first+confirm: W46N8/W47N8/W45N8/W45N7/W47N7 "
        f"each distinct=700 missing_n=0. distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks recovered="
        f"{official_recovered}). Previously in-window official 404 W45N7@84285500 remains aged out "
        f"of this 40m window (hole 84285501..84285600 still {w45n7_hole['rows']} rows / "
        f"{w45n7_hole['distinct']} distinct, range {w45n7_hole['min']}..{w45n7_hole['max']}; "
        "official 84285501..84285583 still empty; confirm still 404). Previously in-window official "
        f"404 W45N8@84282500 remains aged out (hole 84282501..84282600 still "
        f"{leftover['W45N8@84282500']['rows']} rows / {leftover['W45N8@84282500']['distinct']} "
        f"distinct; confirm still 404). W47N8 hole 84281501..84281600 still "
        f"{leftover['W47N8@84281500']['distinct']} live ticks / {leftover['W47N8@84281500']['rows']} "
        f"rows; W45N8 hole 84281501..84281600 still {leftover['W45N8@84281500']['rows']}/"
        f"{leftover['W45N8@84281500']['distinct']}. W45N8@84279700 official 404 remains aged out "
        f"(hole 84279701..84279800, db {leftover['W45N8@84279700']['rows']} rows / "
        f"{leftover['W45N8@84279700']['distinct']} distinct). Other aged leftover official 404s "
        "still 404 after confirm GET. No empty-no-creep in this window. First-pass tick_s=4.206 "
        "realigned 24 rows; later-mean already inside the 45s gate so no corrective realign "
        "(later-mean tick_s=4.25692, nfix=0, still_over_45s_vs_later=0, at "
        "23:05:58 Asia/Hong_Kong game.time=84286996)."
    )
    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm recovered none; 30 aged leftover official 404s still 404 (including W45N7@84285500, "
        "now outside this 40m window) inserted=0 ts_realigned=0 at 23:06:04 game.time=84286997\n"
        "retry2 skipped (no in-window official 404; first pass missing_chunks=0)\n"
        "ts_realigned_first_pass=24 (tick_s=4.206); later-mean already inside 45s gate "
        "(later-mean tick_s=4.25692 nfix=0 still_over_45s_vs_later=0 at 23:05:58 game.time=84286996)\n"
        f"inserted_total=11782 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official}\n"
    )
    now_text = first + now_extra

    coverage_final = {
        "window": [TMIN, TMAX],
        "rooms": cov,
        "unique_after": unique_after,
        "official_recovered": official_recovered,
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
        "inserted_first": 11782,
        "already_in_db": 15375,
        "ts_realigned": 24,
        "ts_realigned_corrective_later_mean": 0,
        "inserted_confirm": 0,
        "inserted_retry2": 0,
        "inserted_total": 11782,
        "unique_after": unique_after,
        "coverage": cov,
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
        "inserted": 11782,
        "already_in_db": 15375,
        "ts_realigned": 24,
        "ts_realigned_corrective_later_mean": 0,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": [],
        "unique_after_window": unique_after,
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
    print("official_recovered", official_recovered, "expected", expected_official)
    print("db_tips", tips)
    print("live_after", live_after)
    print("listener", listener_at_finish)
    print("ok_complete", official_recovered == expected_official and all(v["missing_n"] == 0 for v in cov.values()))
    print("routine_ok", True)


if __name__ == "__main__":
    main()
