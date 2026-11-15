#!/usr/bin/env python3
"""Write coverage + status records for the 22:00 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-15_2200"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84285401, 84286100
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.203  # first-pass script value (first interval)
TICK_S_LATER = 4.26563  # W46N8 later-mean; no corrective (already inside 45s gate)
GAME_TIME_FIRST = 84286158
PUBLISHED = "84285400..84286000"
CONFIRM_GT = 84286178
CONFIRM_AT = "22:07:53"
RETRY2_GT = 84286197
RETRY2_AT = "22:09:13"
IN_WINDOW_404S = [
    ("W45N7", 84285500),  # official 404 after first pass, confirm, and retry2
]
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
NEW_FIRST = {"W46N8": 3344, "W47N8": 6457, "W45N8": 2532, "W45N7": 1923, "W47N7": 1708}
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


def fmt_in_window(room, base, h, still="still 404 after confirm+retry2"):
    return (f"{room}@{base} ({h['rows']} rows / {h['distinct']} distinct, "
            f"range {h['min']}..{h['max']}; in-window official 404, {still})")


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

    official_recovered = unique_after["distinct_room_ticks"]
    expected_official = 5 * WINDOW_N
    w45n7_hole = inwin["W45N7@84285500"]

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
    known_in = [fmt_in_window(r, b, inwin[f"{r}@{b}"]) for r, b in IN_WINDOW_404S]

    missing_chunk_note = (
        "First pass (game.time=84286158) published_bases 84285400..84286000, reconstructed "
        "84285401..84286100 (700). 34 of 35 official GETs were 200; missing_chunks=1 "
        "W45N7@84285500 (same persistent official 404 as the 21:30 run; the other four rooms "
        "returned 200 for that base). W45N7 first-pass reconstruction was 600 ticks (gap at "
        "84285501..84285600). Confirm GET 2026-11-15 22:07:53 Asia/Hong_Kong game.time=84286178 "
        "retried that in-window 404 plus 29 aged leftover official 404s, recovering none "
        "(inserted=0, ts_realigned=0). retry2 2026-11-15 22:09:13 Asia/Hong_Kong "
        "game.time=84286197 retried only W45N7@84285500, still 404 (inserted=0, ts_realigned=0). "
        "After first+confirm+retry2, W46N8/W47N8/W45N8/W47N7 each have 700 distinct ticks in "
        f"84285401..84286100; W45N7 has {cov['W45N7']['distinct']} distinct, "
        f"missing_n={cov['W45N7']['missing_n']} {cov['W45N7']['missing_ranges']}. The in-window "
        f"hole 84285501..84285600 has {w45n7_hole['rows']} live rows / {w45n7_hole['distinct']} "
        f"distinct (range {w45n7_hole['min']}..{w45n7_hole['max']}); official ticks in "
        "84285501..84285583 remain empty. Aged leftover official 404s still 404 after confirm "
        "GET. No empty-no-creep in this window."
    )

    inserted_note = (
        "The previous 21:30 Asia/Hong_Kong half-hour backfill prefilled official 84284901..84285600 "
        "(inserted=3121, already_in_db=23761, first-pass ts_realigned=1496 on tick_s=4.256, "
        "later-mean 4.24563 already inside the 45s gate so nfix=0, missing_chunks=1 "
        "W45N7@84285500, game.time=84285677). That window overlaps 200 ticks of this run "
        "(84285401..84285600). One box freeze since then dropped the live listener: "
        "21:42:27–21:52:14 Asia/Hong_Kong (587s; relaunch 21:52:17; listener.py pid 3132680 "
        "started 21:52:27, still the live process at pre-check 22:06:07 and at finish). Pre-check "
        "at 22:06:07 already had post-21:30 official/live coverage since tick 84285600 of W45N7 "
        "41 distinct through 84286091, W45N8 29 through 84286063, W46N8 205 through 84286154, "
        "W47N7 1 through 84285600, W47N8 138 through 84286035; the W45N7@84285500 hole already "
        "had 17 live ticks (84285584..84285600, 63 rows) and stayed in this new 40m window. "
        "First pass inserted=15964 (already_in_db=9874 of 25838 reconstructed rows) with "
        "missing_chunks=1 (W45N7@84285500). Confirm inserted=0. retry2 inserted=0. "
        "inserted_total=15964. First pass ts_realigned=0 onto first-interval tick_s=4.203; "
        "later-mean tick_s=4.26563 was already inside the 45s gate at 22:07:37 (game.time=84286175, "
        "still_over_45s_vs_later=0), so no corrective realign. First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.203, live anchor game.time=84286158) reported ts_realigned=0. The "
        "script's tick_s is taken from the earliest two distinct published-chunk timestamps in this "
        "fetch (min 84285400 ts=1794748822846 to min 84285500 ts=1794749243135 → 420289ms/100="
        "4.20289s, printed 4.203). Later W46N8 min-ts successive bases in this fetch are ≈4.25681, "
        "4.20499, 4.32717, 4.19464, 4.34455 s/tick; mean of the five ≈4.26563. All-six mean "
        "including the first interval ≈4.25518. Delta first minus later is -0.06274 s/tick (~47.5s "
        "at tick 84285401 versus the first-pass live anchor), but a later-anchor check at "
        "2026-11-15 22:07:37 Asia/Hong_Kong game.time=84286175 found still_over_45s_vs_later=0 "
        "(12819 rows 15s+ off later-mean; 9372 rows 15s+ off first-interval; 0 rows >45s off "
        "either rate; n=25454). No corrective realign was applied. Confirm reported "
        "ts_realigned=0. retry2 reported ts_realigned=0."
    )

    live_json_note = (
        "One new box freeze since the previous 21:30 Asia/Hong_Kong half-hour: 2026-11-15 "
        "21:42:27–21:52:14 Asia/Hong_Kong (587s; VM hibernated; wall jumped, monotonic did not), "
        "logged by listener.py at 21:52:14 with run_listener.sh relaunch at 21:52:17 (listener.py "
        "pid 3132680 started 21:52:27, still the live listener at pre-check 22:06:07 and at finish). "
        "run_listener.sh pid 4035476 unchanged since 2026-11-11. yield_files=absent, single room "
        f"slot, peacetime 5:5:1:1 (rot at pre-check on W46N8, at finish on {rot.get('room')}). "
        "Did not start a second loop or kill war_cmd/pulse. Segment-90 and STATS came back without "
        "a console query: at pre-check 22:06:07 (about 14 min after the 21:52:17 relaunch) live.json "
        "gameTime=84286153 (slot on home W46N8) stats.t=84286150, creep_cpu tip 84286140 (8327 rows "
        "since tick 84284901, last200 84285940..84286140, 1585 rows), path_arrivals tip 84286122 "
        "(154 rows since tick 84284901, last200 28 rows), room_stats tip 84286150, creep_ticks tip "
        "84286154 (current slot W46N8). A known incidents ingest drop (invalid integer '{{}}') "
        "logged at 22:00:17; it did not affect this history backfill. This run did not change the "
        "peacetime single-slot 5:5:1:1 arrangement. The first official game/time request succeeded."
    )

    hourly_note = (
        "The 21:25 1h peacetime patrol already finished earlier this evening. The 21:30 half-hour "
        "backfill had already prefilled 84284901..84285600 (inserted=3121, tick_s=4.256 / later "
        "4.24563, game.time=84285677), overlapping 200 ticks of this window (84285401..84285600). "
        "The persistent official 404 W45N7@84285500 remains in this window. This run added the newly "
        "published 84285600..84286000 chunks (all five rooms 200 on the first pass except "
        "W45N7@84285500, still official 404 after confirm and retry2)."
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
        "missing_chunk_list": ["W45N7@84285500"],
        "missing_chunk_first_pass": ["W45N7@84285500"],
        "missing_chunk_note": missing_chunk_note,
        "creep_rows_reconstructed": 25838,
        "already_in_db": 9874,
        "inserted": 15964,
        "inserted_first_pass": 15964,
        "inserted_retry": 0,
        "inserted_retry2": 0,
        "inserted_note": inserted_note,
        "ts_realigned": 0,
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
        "missing_chunks first_pass=1 W45N7@84285500 (34 of 35 official GETs 200 at "
        "game.time=84286158; published_bases 84285400..84286000, reconstructed 84285401..84286100; "
        "W45N7 first-pass 600t with a gap at 84285501..84285600). Confirm 2026-11-15 22:07:53 "
        "Asia/Hong_Kong game.time=84286178 retried that in-window 404 plus 29 aged leftover official "
        "404s, recovering none (inserted=0, ts_realigned=0). retry2 2026-11-15 22:09:13 "
        "Asia/Hong_Kong game.time=84286197 retried only W45N7@84285500, still 404 (inserted=0, "
        f"ts_realigned=0). After first+confirm+retry2: W46N8/W47N8/W45N8/W47N7 distinct=700 "
        f"missing_n=0; W45N7 distinct={cov['W45N7']['distinct']} missing_n={cov['W45N7']['missing_n']} "
        f"{cov['W45N7']['missing_ranges']}. distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks recovered="
        f"{official_recovered}). In-window official 404 W45N7@84285500 hole 84285501..84285600 has "
        f"{w45n7_hole['rows']} live rows / {w45n7_hole['distinct']} distinct "
        f"(range {w45n7_hole['min']}..{w45n7_hole['max']}); official 84285501..84285583 still empty. "
        f"Previously in-window official 404 W45N8@84282500 remains aged out of this 40m window "
        f"(hole 84282501..84282600 still {leftover['W45N8@84282500']['rows']} rows / "
        f"{leftover['W45N8@84282500']['distinct']} distinct; confirm still 404). "
        f"W47N8 hole 84281501..84281600 still {leftover['W47N8@84281500']['distinct']} live ticks / "
        f"{leftover['W47N8@84281500']['rows']} rows; W45N8 hole 84281501..84281600 still "
        f"{leftover['W45N8@84281500']['rows']}/{leftover['W45N8@84281500']['distinct']}. "
        f"W45N8@84279700 official 404 remains aged out (hole 84279701..84279800, db "
        f"{leftover['W45N8@84279700']['rows']} rows / {leftover['W45N8@84279700']['distinct']} distinct). "
        "Other aged leftover official 404s still 404 after confirm GET. No empty-no-creep in this "
        "window. First-pass tick_s=4.203 realigned 0 rows; later-mean already inside 45s gate "
        "(later-mean tick_s=4.26563, still_over_45s_vs_later=0, no corrective realign at 22:07:37 "
        "Asia/Hong_Kong game.time=84286175)."
    )
    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm recovered none; in-window official 404 W45N7@84285500 still 404; 29 aged leftover "
        "official 404s still 404 inserted=0 ts_realigned=0 at 22:07:53 game.time=84286178\n"
        "retry2 W45N7@84285500 still 404 inserted=0 ts_realigned=0 at 22:09:13 game.time=84286197\n"
        "ts_realigned_first_pass=0 (tick_s=4.203); no corrective later-mean realign "
        "(later-mean tick_s=4.26563 nfix=0 still_over_45s_vs_later=0 at 22:07:37 game.time=84286175)\n"
        f"inserted_total=15964 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"W45N7 missing_n={cov['W45N7']['missing_n']} {cov['W45N7']['missing_ranges']}\n"
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
        "inserted_first": 15964,
        "already_in_db": 9874,
        "ts_realigned": 0,
        "ts_realigned_corrective_later_mean": 0,
        "inserted_confirm": 0,
        "inserted_retry2": 0,
        "inserted_total": 15964,
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
        "inserted": 15964,
        "already_in_db": 9874,
        "ts_realigned": 0,
        "ts_realigned_corrective_later_mean": 0,
        "missing_chunks": 1,
        "missing_chunk_list": ["W45N7@84285500"],
        "missing_chunk_first_pass": ["W45N7@84285500"],
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
