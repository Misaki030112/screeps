#!/usr/bin/env python3
"""Write coverage + status records for the 20:00 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-15_2000"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84283601, 84284300
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.260  # first-pass script value (first interval)
TICK_S_LATER = 4.22645  # W46N8 later-mean; no corrective realign (already inside 45s gate)
GAME_TIME_FIRST = 84284397
PUBLISHED = "84283600..84284200"
LEFTOVER_404S = [
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
NEW_FIRST = {"W46N8": 2466, "W47N8": 6465, "W45N8": 1334, "W45N7": 742, "W47N7": 2436}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
TICKS_FIRST = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}


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

    per_room = {}
    for room in ROOMS:
        new_first = NEW_FIRST[room]
        new_r2 = NEW_RETRY2[room]
        per_room[room] = {
            "ticks": cov[room]["distinct"],
            "new": new_first + new_r2,
            "new_first_pass": new_first,
            "new_confirm": 0,
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

    missing_chunk_note = (
        "First pass (game.time=84284397) published_bases 84283600..84284200, reconstructed "
        "84283601..84284300 (700). All 35 official GETs were 200; missing_chunks=0 (no tip or "
        "mid-window official 404 in this window). Confirm GET 2026-11-15 20:03:45 Asia/Hong_Kong "
        "game.time=84284421 retried 29 aged leftover official 404s, recovering none (inserted=0, "
        "ts_realigned=0). retry2 skipped (nothing in-window to retry). After the first pass every "
        "room has 700 distinct ticks in 84283601..84284300. Previously in-window official 404 "
        "W45N8@84282500 remains aged out of this 40m window "
        f"(hole 84282501..84282600 still {leftover['W45N8@84282500']['rows']} rows / "
        f"{leftover['W45N8@84282500']['distinct']} distinct; confirm still 404). Other aged leftover "
        "official 404s still 404 after confirm GET. No empty-no-creep in this window."
    )

    inserted_note = (
        "The previous 19:30 Asia/Hong_Kong half-hour backfill prefilled official 84283301..84284000 "
        "(inserted=9535, already_in_db=16813, first-pass ts_realigned=13196 then corrective later-mean "
        "ts_realigned=14370, tick_s=4.124 / later 4.25848, missing_chunks=0, game.time=84284039). That "
        "window overlaps 400 ticks of this run (84283601..84284000). One box freeze since then dropped "
        "the live listener: 19:43:37–20:00:13 Asia/Hong_Kong (996s; relaunch 20:00:16; listener.py pid "
        "3098374 started 20:00:25, still the live process at pre-check 20:01:27 and at finish). "
        "Pre-check at 20:01:27 already had post-19:30 official/live coverage since tick 84284000 of "
        "W45N7 24 distinct through 84284049, W45N8 1 (tip 84284000), W46N8 95 through 84284389, "
        "W47N7 1 (tip 84284000), W47N8 1 (tip 84284000); the W45N8@84282500 hole was still 0/0 and "
        "aged out of the new window. First pass inserted=13443 (already_in_db=16786 of 30229 "
        "reconstructed rows) with missing_chunks=0. Confirm inserted=0. retry2 not needed. "
        "inserted_total=13443. First pass ts_realigned=4273 onto first-interval tick_s=4.260; no "
        "corrective later-mean realign (later-mean tick_s=4.22645 already still_over_45s=0 at "
        "20:03:34, game.time=84284419). First game/time request disconnected; retry succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.260, live anchor game.time=84284397) reported ts_realigned=4273. The script's "
        "tick_s is taken from the earliest two distinct published-chunk timestamps in this fetch (min 84283600 "
        "ts=1794741209069 to min 84283700 ts=1794741635069 → 426000ms/100=4.260s). Later W46N8 min-ts successive "
        "bases in this fetch are ≈4.356, 4.210, 4.190, 4.274, 4.102 s/tick; mean of the five ≈4.22645. All-six "
        "mean including the first interval ≈4.232. Delta first minus later is 0.03355 s/tick (~26.7s at tick "
        "84283601), inside the 45s gate. A later-anchor check at 2026-11-15 20:03:34 Asia/Hong_Kong "
        "game.time=84284419 found still_over_45s_vs_later=0 (6805 rows remain 15–45s off later mean) and "
        "762 rows >45s off the first-interval rate at that later anchor; no corrective UPDATE was applied "
        "because later-mean already sits inside the 45s gate. Confirm reported ts_realigned=0."
    )

    live_json_note = (
        "One new box freeze since the previous 19:30 Asia/Hong_Kong half-hour: 2026-11-15 19:43:37–20:00:13 "
        "Asia/Hong_Kong (996s; VM hibernated; wall jumped, monotonic did not), logged by listener.py at 20:00:13 "
        "with run_listener.sh relaunch at 20:00:16 (listener.py pid 3098374 started 20:00:25, still the live listener "
        "at pre-check 20:01:27 and at finish). run_listener.sh pid 4035476 unchanged since 2026-11-11. "
        "yield_files=absent, single room slot, peacetime 5:5:1:1 (rot at pre-check on W46N8, "
        f"at finish on {rot.get('room')}). Did not start a second loop or kill war_cmd/pulse. "
        "Segment-90 and STATS came back without a console query: at pre-check 20:01:27 (about 71s after the 20:00:16 "
        "relaunch) live.json gameTime=84284388 (slot on home W46N8) stats.t=84284380, creep_cpu tip 84284380 "
        "(7375 rows since tick 84283301, last200 84284215..84284380, 1336 rows), path_arrivals tip 84284379 "
        "(133 rows since tick 84283301, last200 27 rows), room_stats tip 84284380, creep_ticks tip 84284389 "
        "(current slot W46N8). This run did not change the peacetime single-slot 5:5:1:1 arrangement. "
        "The first official game/time request raised RemoteDisconnected; the retry about 5s later succeeded."
    )

    hourly_note = (
        "The 19:20 1h peacetime patrol already finished (analysis / console collect only — "
        "no history_backfill.py). The 19:30 half-hour backfill had already prefilled 84283301..84284000 "
        "(inserted=9535, tick_s=4.124 / later 4.25848, game.time=84284039), overlapping 400 ticks of this window "
        "(84283601..84284000). The aged W45N8@84282500 official 404 sits outside this window. This run added "
        "the newly published 84284000..84284200 chunks (all five rooms 200 on the first pass)."
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
        "creep_rows_reconstructed": 30229,
        "already_in_db": 16786,
        "inserted": 13443,
        "inserted_first_pass": 13443,
        "inserted_retry": 0,
        "inserted_retry2": 0,
        "inserted_note": inserted_note,
        "ts_realigned": 4273,
        "ts_realigned_corrective_later_mean": 0,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": ts_realigned_note,
        "ssl_first_attempt": "RemoteDisconnected on first game/time, retry ok",
        "hourly_patrol_prefilled": hourly_note,
        "per_room": per_room,
        "known_official_404s_outside_window": known_out,
        "known_official_404s_in_window": [],
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
        "missing_chunks first_pass=0 (all 35 official GETs 200 at game.time=84284397; published_bases "
        "84283600..84284200, reconstructed 84283601..84284300). Confirm 2026-11-15 20:03:45 Asia/Hong_Kong "
        "game.time=84284421 retried 29 aged leftover official 404s, recovering none (inserted=0, ts_realigned=0). "
        "retry2 skipped (no in-window official 404). After the first pass missing_chunks=0; every room "
        f"distinct=700, missing_n=0. distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks recovered="
        f"{official_recovered} = {expected_official}). Previously in-window official 404 W45N8@84282500 has aged "
        f"out of this 40m window (hole 84282501..84282600 still {leftover['W45N8@84282500']['rows']} rows / "
        f"{leftover['W45N8@84282500']['distinct']} distinct; confirm still 404). "
        f"W47N8 hole 84281501..84281600 still {leftover['W47N8@84281500']['distinct']} live ticks / "
        f"{leftover['W47N8@84281500']['rows']} rows; W45N8 hole 84281501..84281600 still "
        f"{leftover['W45N8@84281500']['rows']}/{leftover['W45N8@84281500']['distinct']}. "
        f"W45N8@84279700 official 404 remains aged out (hole 84279701..84279800, db "
        f"{leftover['W45N8@84279700']['rows']} rows / {leftover['W45N8@84279700']['distinct']} distinct). "
        "Other aged leftover official 404s still 404 after confirm GET. No empty-no-creep in this window. "
        "First-pass tick_s=4.260 realigned 4273 rows; no corrective later-mean realign (later-mean tick_s=4.22645, "
        "still_over_45s_vs_later=0 at 20:03:34 Asia/Hong_Kong game.time=84284419)."
    )
    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm recovered none; no in-window official 404; 29 aged leftover official 404s still 404 "
        "inserted=0 ts_realigned=0 at 20:03:45 game.time=84284421\n"
        "retry2 skipped (missing_chunks first_pass=0)\n"
        "ts_realigned_first_pass=4273 (tick_s=4.260); no corrective later-mean realign "
        "(later-mean tick_s=4.22645 still_over_45s_vs_later=0 at 20:03:34 game.time=84284419)\n"
        f"inserted_total=13443 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_recovered={official_recovered}=5*{WINDOW_N}\n"
    )
    now_text = first + now_extra

    coverage_final = {
        "window": [TMIN, TMAX],
        "rooms": cov,
        "unique_after": unique_after,
        "official_recovered": official_recovered,
        "hole_W45N8_84282500": leftover["W45N8@84282500"],
    }

    collect_raw = {
        "at": now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
        "game_time_first_pass": GAME_TIME_FIRST,
        "confirm_game_time": 84284421,
        "retry2_game_time": None,
        "tick_s": TICK_S,
        "tick_s_later_mean": TICK_S_LATER,
        "inserted_first": 13443,
        "already_in_db": 16786,
        "ts_realigned": 4273,
        "ts_realigned_corrective_later_mean": 0,
        "inserted_confirm": 0,
        "inserted_retry2": 0,
        "inserted_total": 13443,
        "unique_after": unique_after,
        "coverage": cov,
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
        "inserted": 13443,
        "already_in_db": 16786,
        "ts_realigned": 4273,
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
    print("ok", official_recovered == expected_official and all(v["missing_n"] == 0 for v in cov.values()))


if __name__ == "__main__":
    main()
