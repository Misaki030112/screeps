#!/usr/bin/env python3
"""Write coverage + status records for the 05:30 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0530"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84291601, 84292300
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.24797  # first-pass exact first-interval (printed 4.248)
TICK_S_LATER = 4.29658875  # W46N8 later-mean; already inside 45s gate, no corrective realign
GAME_TIME_FIRST = 84292379
PUBLISHED = "84291600..84292200"
CONFIRM_GT = 84292399
CONFIRM_AT = "05:29:31"
RETRY2_GT = 84292438
RETRY2_AT = "05:32:16"
IN_WINDOW_404S_FIRST = [
    ("W46N8", 84292000),
]
IN_WINDOW_404S_FINAL = [
    ("W46N8", 84292000),
]
LEFTOVER_404S = [
    ("W47N8", 84290200),
    ("W47N7", 84289200),
    ("W45N7", 84289300),
    ("W47N8", 84287500),
    ("W45N7", 84285500),
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
NEW_FIRST = {"W46N8": 118, "W47N8": 996, "W45N8": 408, "W45N7": 408, "W47N7": 339}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {}
EMPTY_NO_CREEP_N = 0
INSERTED_FIRST = 2269
ALREADY_IN_DB = 20859
CREEP_ROWS_RECONSTRUCTED = 23128
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_TOTAL = 2269
TICK_S_CHECK_AT = "05:29:24"
TICK_S_CHECK_GT = 84292398
TS_REALIGNED_FIRST = 0
TS_REALIGNED_LATER = 0
TS_REALIGNED_CONFIRM = 0
OFFICIAL_404_TICKS = 100  # W46N8@84292000 official hole 84292001..84292100


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


def fmt_hole(room, base, h, still="still 404", aged=True):
    aged_s = "aged out of this 40m window, " if aged else "in this 40m window, "
    return (f"{room}@{base} ({h['rows']} rows / {h['distinct']} distinct, "
            f"range {h['min']}..{h['max']}; {aged_s}{still})")


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
            ticks = {r[0] for r in c.execute(
                "SELECT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, TMIN, TMAX),
            ).fetchall()}
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
        in_window_404_first = {f"{r}@{b}": hole(c, r, b) for r, b in IN_WINDOW_404S_FIRST}
        in_window_404 = {f"{r}@{b}": hole(c, r, b) for r, b in IN_WINDOW_404S_FINAL}

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

    w46_in = in_window_404["W46N8@84292000"]
    live_in_hole = w46_in["distinct"]
    official_recovered = 5 * WINDOW_N - OFFICIAL_404_TICKS  # 3400
    official_with_creeps = official_recovered
    expected_official = 5 * WINDOW_N
    w47n8_902 = leftover["W47N8@84290200"]
    w45n7_hole = leftover["W45N7@84285500"]
    w47n8_aged = leftover["W47N8@84287500"]
    w47n7_aged = leftover["W47N7@84289200"]
    w45n7_893 = leftover["W45N7@84289300"]

    official_ticks = {
        "W46N8": WINDOW_N - OFFICIAL_404_TICKS,
        "W47N8": WINDOW_N,
        "W45N8": WINDOW_N,
        "W45N7": WINDOW_N,
        "W47N7": WINDOW_N,
    }
    per_room = {}
    for room in ROOMS:
        new_first = NEW_FIRST[room]
        new_c = NEW_CONFIRM[room]
        new_r2 = NEW_RETRY2[room]
        per_room[room] = {
            "ticks": cov[room]["distinct"],
            "ticks_official": official_ticks[room],
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

    known_out = [fmt_hole(r, b, leftover[f"{r}@{b}"], aged=True) for r, b in LEFTOVER_404S]
    known_in = [fmt_hole(r, b, in_window_404[f"{r}@{b}"], aged=False) for r, b in IN_WINDOW_404S_FINAL]

    missing_chunk_note = (
        "First pass (game.time=84292379) published_bases 84291600..84292200, reconstructed "
        "84291601..84292300 (700). 35 official GETs: 34 were 200, missing_chunks=1 "
        "(W46N8@84292000). already_in_db=20859 would_insert=2269; first pass inserted=2269, "
        "ts_realigned=0 onto first-interval tick_s=4.24797 (printed 4.248). Confirm GET "
        "2026-11-16 05:29:31 Asia/Hong_Kong game.time=84292399 retried in-window official 404 "
        "W46N8@84292000 plus 34 aged leftover official 404s including W47N8@84290200; all 35 "
        "were still 404, inserted=0, ts_realigned=0. retry2 2026-11-16 05:32:16 Asia/Hong_Kong "
        "game.time=84292438: W46N8@84292000 still 404, inserted=0, ts_realigned=0. The concurrent "
        "hourly patrol had already retried W46N8@84292000 twice (still 404 at game.time=84292280 "
        "and 84292357). After confirm/retry2, four rooms have 700 distinct ticks; W46N8 has "
        f"{cov['W46N8']['distinct']} distinct (600 official + {live_in_hole} live in the official "
        "404 hole 84292001..84292100; official 84292001..84292100 still empty). No official "
        "empty-no-creep ticks."
    )

    inserted_note = (
        "The previous 05:00 Asia/Hong_Kong half-hour backfill prefilled official 84291301..84292000 "
        "(inserted_total=12022 after first=10228 + confirm=1794 + retry2 skipped, already_in_db=10955, "
        "first-pass ts_realigned=0 on tick_s=4.29809, later-mean 4.26994 already inside the 45s "
        "gate so no corrective later-mean realign, first-pass missing_chunks=3 all recovered on "
        "confirm, game.time=84292006). That window overlaps 400 ticks of this run "
        "(84291601..84292000). Concurrent hourly patrol _patrol_2026-11-16_0518 also ran a 40m "
        "official first pass at game.time=84292260 for published 84291500..84292100 / reconstructed "
        "84291501..84292200, inserted=5133 already_in_db=18410, missing_chunks=1 W46N8@84292000; "
        "it retried W46N8@84292000 at game.time=84292280 (still 404) and again at game.time=84292357 "
        "(still 404) while inserting 1005 from newly published W46N8@84292200. One new box freeze "
        "ran after the 05:00 backfill: 05:07:22–05:18:57 Asia/Hong_Kong (688s; VM hibernated; wall "
        "jumped, monotonic did not) with listener.py logged freeze at 05:18:57; run_listener.sh "
        "(pid 4035476, unchanged since 2026-11-11) relaunched at 05:19:00; new listener.py pid "
        "3260221 started 05:19:09. First pass inserted=2269 (already_in_db=20859 of 23128 "
        "reconstructed rows in 84291601..84292300) with missing_chunks=1 W46N8@84292000, covering "
        "the newly published 84292200 chunks for rooms not already filled by the patrol and the "
        "05:07–05:18 box-freeze gap for rooms not on the single peacetime slot. Confirm inserted=0 "
        "and did not recover W46N8@84292000 or any aged leftover chunks. retry2 inserted=0, still "
        "404 on W46N8@84292000. inserted_total=2269. First pass ts_realigned=0 onto first-interval "
        "tick_s=4.24797; later-mean tick_s=4.29658875 was already inside the 45s gate (over45=0, "
        f"over15=1682, n=22877 at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT}), so no corrective "
        "later-mean realign was applied. Confirm and retry2 ts_realigned=0. First game/time request "
        "succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.24797 printed 4.248, live anchor game.time=84292379) reported "
        "ts_realigned=0. The script's tick_s is taken from the earliest two distinct "
        "published-chunk timestamps in this fetch (min 84291600 ts=1794775213777 W45N7 to min "
        "84291700 ts=1794775638574 W46N8 → 4.24797s; printed 4.248). W46N8@84292000 was official "
        "404, so W46N8 later intervals are 4.24367, 4.32799, 4.27118 (200-tick 84291900..84292100 "
        "gap), 4.34352 s/tick; later_mean 4.29658875. All-five mean including the first W46 "
        "interval 4.24759 = 4.28679. Delta first-interval (script 4.24797) minus later is "
        "-0.04862 s/tick (~37.8s at tick 84291601 versus the first-pass live anchor). A "
        "later-anchor check at 2026-11-16 05:29:24 Asia/Hong_Kong game.time=84292398 found "
        "still_over_45s_vs_first=0 (n=22877; vs first-interval over15=10517) and "
        "still_over_45s_vs_later=0 (n=22877; vs later-mean over15=1682), so no corrective "
        "later-mean realign was applied. Confirm reported ts_realigned=0 (W46N8@84292000 and all "
        "34 aged leftover official 404s including W47N8@84290200 still 404). retry2 reported "
        "ts_realigned=0 (W46N8@84292000 still 404)."
    )

    live_json_note = (
        "One box freeze ran after the 05:00 backfill: 2026-11-16 05:07:22–05:18:57 Asia/Hong_Kong "
        "(688s; VM hibernated; wall jumped, monotonic did not), logged by listener.py at 05:18:57 "
        "with run_listener.sh relaunch at 05:19:00 (new listener.py pid 3260221 started 05:19:09). "
        "run_listener.sh pid 4035476 unchanged since 2026-11-11. yield_files=absent, single room "
        "slot, peacetime 5:5:1:1 (rot at pre-check on W46N8, i=0). Did not start a second loop or "
        "kill war_cmd/pulse. Segment-90 and STATS were already current without a console query: at "
        "pre-check 05:27:41 live.json gameTime=84292373 (slot on HOME W46N8, objects=265) "
        "stats.t=84292370 cpu=16.88 b=10000, creep_cpu tip 84292360 (7135 rows since tick 84291301, "
        "last200 84292160..84292360, 1489 rows, max_ts 05:27:16 after reconnect pull), path_arrivals "
        "tip 84292359 (132 rows since tick 84291301, last200 34 rows), room_stats tip 84292370, "
        "creep_ticks tip 84292373. No new incidents ingest drop after the known 03:00:06 invalid "
        "integer '{}' event. This run did not change the peacetime single-slot 5:5:1:1 "
        "arrangement. The first official game/time request succeeded. A concurrent hourly patrol "
        "(_patrol_2026-11-16_0518, started ~05:18) was running during this backfill and had already "
        "official-backfilled most of the overlapping window; this run did not add a second "
        "websocket slot."
    )

    hourly_note = (
        "The previous 05:00 half-hour backfill had already prefilled 84291301..84292000 "
        "(inserted_total=12022, tick_s=4.29809 / later 4.26994 with no corrective later-mean "
        "realign, first-pass missing_chunks=3 all recovered on confirm, game.time=84292006), "
        "overlapping 400 ticks of this window (84291601..84292000). Concurrent hourly patrol "
        "_patrol_2026-11-16_0518 also official-backfilled 84291501..84292200 at game.time=84292260 "
        "(inserted=5133, already_in_db=18410, missing_chunks=1 W46N8@84292000) and retried that "
        "chunk twice (still 404 at game.time=84292280 and 84292357), also inserting 1005 from "
        "newly published W46N8@84292200. First pass then recovered the newly published 84292200 "
        "chunks for the other four rooms (and 118 additional W46N8 rows), with missing_chunks=1 "
        "W46N8@84292000 still official 404; confirm (05:29:31, game.time=84292399) and retry2 "
        "(05:32:16, game.time=84292438) left W46N8@84292000 and all 34 aged leftover official "
        "404s including W47N8@84290200 unpublished. There were no official empty-no-creep ticks "
        "in this 40m window. The in-window official 404 hole W46N8 84292001..84292100 still has "
        f"{w46_in['rows']} rows / {w46_in['distinct']} live distinct (official 84292001..84292100 "
        "still empty). Previously in-window official 404 hole "
        f"W47N8 84290201..84290300 still has {w47n8_902['rows']} rows / {w47n8_902['distinct']} "
        f"live distinct, range {w47n8_902['min']}..{w47n8_902['max']}; official 84290201..84290256 "
        "still empty."
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
        "missing_chunk_list": ["W46N8@84292000"],
        "missing_chunk_first_pass": ["W46N8@84292000"],
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
        "official_room_ticks_fetched": official_recovered,
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
        "missing_chunks first_pass=1 (W46N8@84292000) at game.time=84292379; published_bases "
        "84291600..84292200, reconstructed 84291601..84292300 (700), already_in_db=20859 "
        "inserted=2269. Confirm 2026-11-16 05:29:31 Asia/Hong_Kong game.time=84292399 retried "
        "in-window official 404 W46N8@84292000 and 34 aged leftover official 404s including "
        "W47N8@84290200 — all 35 still 404, inserted=0, ts_realigned=0. retry2 2026-11-16 05:32:16 "
        "Asia/Hong_Kong game.time=84292438: W46N8@84292000 still 404, inserted=0. After "
        "confirm/retry2: W47N8/W45N8/W45N7/W47N7 each distinct=700 missing_n=0; W46N8 "
        f"distinct={cov['W46N8']['distinct']} missing_n={cov['W46N8']['missing_n']} "
        f"{cov['W46N8']['missing_ranges']} ({live_in_hole} live ticks in the official 404 hole "
        "84292001..84292100; official 84292001..84292100 still empty). No official empty-no-creep "
        "ticks in this window. "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window=1 W46N8@84292000; live "
        f"ticks inside that official 404 hole={live_in_hole}). "
        f"Previously in-window official 404 W47N8@84290200 remains aged out of this 40m window "
        f"(hole 84290201..84290300 still {w47n8_902['rows']} rows / {w47n8_902['distinct']} "
        f"distinct, range {w47n8_902['min']}..{w47n8_902['max']}; official 84290201..84290256 still "
        f"empty; confirm still 404). Previously in-window official 404 W47N7@84289200 remains aged "
        f"out (hole 84289201..84289300 still {w47n7_aged['rows']} rows / {w47n7_aged['distinct']} "
        f"distinct; confirm still 404). Previously in-window official 404 W45N7@84289300 remains "
        f"aged out (hole 84289301..84289400 still {w45n7_893['rows']} rows / {w45n7_893['distinct']} "
        f"distinct; confirm still 404). Previously in-window official 404 W47N8@84287500 remains "
        f"aged out (hole 84287501..84287600 still {w47n8_aged['rows']} rows / "
        f"{w47n8_aged['distinct']} distinct; confirm still 404). Previously in-window official 404 "
        f"W45N7@84285500 remains aged out (hole 84285501..84285600 still {w45n7_hole['rows']} rows / "
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
        f"404 after confirm GET. First-pass tick_s=4.24797 (printed 4.248) realigned 0 rows; "
        f"later-mean was already inside the 45s gate so no corrective later-mean realign was "
        f"applied (later-mean tick_s=4.29658875, at {TICK_S_CHECK_AT} Asia/Hong_Kong game.time="
        f"{TICK_S_CHECK_GT}; over45=0, over15=1682, n=22877 after first pass, before confirm)."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm retried in-window official 404 W46N8@84292000 and 34 aged leftover official 404s "
        "including W47N8@84290200 at 05:29:31 game.time=84292399, all 35 still 404 inserted=0 "
        "ts_realigned=0; retry2 05:32:16 game.time=84292438 W46N8@84292000 still 404 inserted=0 "
        "ts_realigned=0\n"
        "ts_realigned_first_pass=0 (tick_s=4.24797 printed 4.248); later-mean already inside 45s "
        f"gate, no corrective later-mean realign (later-mean tick_s=4.29658875 still_over_45s_vs_later="
        f"0 at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT})\n"
        f"inserted_total=2269 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=1 W46N8@84292000 after confirm/retry2 (first-pass missing_chunks=1 "
        f"W46N8@84292000; live in W46N8 hole={live_in_hole})\n"
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
        "in_window_official_404": in_window_404,
        "in_window_official_404_first_pass": in_window_404_first,
        "hole_W46N8_84292000": w46_in,
        "hole_W47N8_84290200": w47n8_902,
        "hole_W47N7_84289200": w47n7_aged,
        "hole_W45N7_84289300": w45n7_893,
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
        "in_window_official_404": in_window_404,
        "hole_W46N8_84292000": w46_in,
        "hole_W47N8_84290200": w47n8_902,
        "hole_W47N7_84289200": w47n7_aged,
        "hole_W45N7_84289300": w45n7_893,
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
        "missing_chunks": 1,
        "missing_chunk_list": ["W46N8@84292000"],
        "missing_chunk_first_pass": ["W46N8@84292000"],
        "unique_after_window": unique_after,
        "empty_no_creep_in_window": False,
        "empty_no_creep_ranges": dict(EMPTY_NO_CREEP),
        "confirm_inserted": INSERTED_CONFIRM,
        "retry2_inserted": INSERTED_RETRY2,
        "retry2_skipped": False,
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
    retry2_src = (DIR / "backfill_retry2.txt").read_text()
    (ROOT / "state" / "_halfhour_backfill_retry2_0530.txt").write_text(retry2_src)

    print("finished_at", finished_hkt)
    print("unique_after", unique_after)
    print("coverage")
    for room, info in cov.items():
        print(" ", room, info)
    print("official_with_creeps", official_with_creeps, "empty_no_creep", EMPTY_NO_CREEP_N,
          "official_recovered", official_recovered, "expected", expected_official,
          "in_window_404", 1, "live_in_W46N8_hole", live_in_hole)
    print("db_tips", tips)
    print("live_after", live_after)
    print("listener", listener_at_finish)
    rooms_official_ok = all(
        (v["missing_n"] == 0) if k != "W46N8" else (v["missing_n"] == 100)
        for k, v in cov.items()
    )
    print("ok_complete", official_recovered == 3400 and rooms_official_ok)
    print("routine_ok", True)


if __name__ == "__main__":
    main()
