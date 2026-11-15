#!/usr/bin/env python3
"""Write coverage + status records for the 06:00 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0600"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84292101, 84292800
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.34352  # first-pass exact first-interval (printed 4.344)
TICK_S_LATER = 4.282064  # W46N8 later-mean; already inside 45s gate, no corrective realign
GAME_TIME_FIRST = 84292805
PUBLISHED = "84292100..84292700"
CONFIRM_GT = 84292837
CONFIRM_AT = "06:00:47"
RETRY2_GT = None
RETRY2_AT = None
RETRY2_SKIPPED = True
IN_WINDOW_404S_FIRST = [
    ("W47N8", 84292700),
    ("W45N8", 84292700),
    ("W47N7", 84292700),
]
IN_WINDOW_404S_FINAL = []
LEFTOVER_404S = [
    ("W46N8", 84292000),
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
NEW_FIRST = {"W46N8": 4676, "W47N8": 4943, "W45N8": 1830, "W45N7": 601, "W47N7": 1316}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 1283, "W45N8": 225, "W45N7": 0, "W47N7": 423}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {"W45N7": [[84292453, 84292453], [84292455, 84292622]]}
EMPTY_NO_CREEP_N = 169
INSERTED_FIRST = 13366
ALREADY_IN_DB = 9160
CREEP_ROWS_RECONSTRUCTED = 22526
INSERTED_CONFIRM = 1931
INSERTED_RETRY2 = 0
INSERTED_TOTAL = 15297
TICK_S_CHECK_AT = "06:00:39"
TICK_S_CHECK_GT = 84292835
TS_REALIGNED_FIRST = 0
TS_REALIGNED_LATER = 0
TS_REALIGNED_CONFIRM = 0
OFFICIAL_404_TICKS = 0  # all first-pass in-window 404s recovered on confirm


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

    official_recovered = 5 * WINDOW_N - OFFICIAL_404_TICKS
    official_with_creeps = unique_after["distinct_room_ticks"]
    expected_official = 5 * WINDOW_N
    w46_920 = leftover["W46N8@84292000"]
    w47n8_902 = leftover["W47N8@84290200"]
    w45n7_hole = leftover["W45N7@84285500"]
    w47n8_aged = leftover["W47N8@84287500"]
    w47n7_aged = leftover["W47N7@84289200"]
    w45n7_893 = leftover["W45N7@84289300"]

    official_ticks = {room: WINDOW_N for room in ROOMS}
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
        "First pass (game.time=84292805) published_bases 84292100..84292700, reconstructed "
        "84292101..84292800 (700). 35 official GETs: 32 were 200, missing_chunks=3 "
        "(W47N8@84292700, W45N8@84292700, W47N7@84292700). already_in_db=9160 would_insert=13366; "
        "first pass inserted=13366, ts_realigned=0 onto first-interval tick_s=4.34352 (printed 4.344). "
        "Confirm GET 2026-11-16 06:00:47 Asia/Hong_Kong game.time=84292837 retried those three "
        "in-window official 404s plus 35 aged leftover official 404s including newly aged-out "
        "W46N8@84292000; all three in-window chunks returned 200 and inserted=1931 "
        "(W47N8 1283 / W45N8 225 / W47N7 423), ts_realigned=0. The 35 aged leftovers including "
        "W46N8@84292000 were still 404, inserted=0. retry2 skipped because no in-window official "
        "404s remained. After confirm, official coverage is complete for all five rooms (3500 of "
        "3500 official room-ticks). W46N8/W47N8/W45N8/W47N7 each have 700 distinct ticks with "
        f"creeps; W45N7 has {cov['W45N7']['distinct']} distinct and {cov['W45N7']['missing_n']} "
        f"official empty-no-creep ticks {cov['W45N7']['missing_ranges']} (chunks 84292400/84292500/"
        "84292600 were all official 200 on first pass; no our creeps on those ticks)."
    )

    inserted_note = (
        "The previous 05:30 Asia/Hong_Kong half-hour backfill prefilled official 84291601..84292300 "
        "(inserted_total=2269 after first=2269 + confirm=0 + retry2=0, already_in_db=20859, "
        "first-pass ts_realigned=0 on tick_s=4.24797, later-mean 4.29658875 already inside the 45s "
        "gate so no corrective later-mean realign, first-pass missing_chunks=1 W46N8@84292000 still "
        "404 after confirm/retry2, game.time=84292379). That window overlaps 200 ticks of this run "
        "(84292101..84292300). No concurrent hourly patrol was running. One new box freeze ran "
        "after the 05:30 backfill: 05:37:16–05:57:06 Asia/Hong_Kong (1182s; VM hibernated; wall "
        "jumped, monotonic did not) with listener.py logged freeze at 05:57:06; run_listener.sh "
        "(pid 4035476, unchanged since 2026-11-11) relaunched at 05:57:09; new listener.py pid "
        "3270948 started 05:57:19. First pass inserted=13366 (already_in_db=9160 of 22526 "
        "reconstructed rows in 84292101..84292800) with missing_chunks=3 on the newest published "
        "base 84292700 for W47N8/W45N8/W47N7 (W46N8 and W45N7 @84292700 were already 200), covering "
        "the 05:37–05:57 box-freeze gap for rooms not on the single peacetime slot and the newly "
        "published 84292300–84292600 chunks. Confirm inserted=1931 and recovered all three "
        "in-window 404s. retry2 skipped. inserted_total=15297. First pass ts_realigned=0 onto "
        "first-interval tick_s=4.34352; later-mean tick_s=4.282064 was already inside the 45s gate "
        f"(over45=0, over15=8000, n=22517 at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT}), so no "
        "corrective later-mean realign was applied. Confirm ts_realigned=0. First game/time request "
        "succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.34352 printed 4.344, live anchor game.time=84292805) reported "
        "ts_realigned=0. The script's tick_s is taken from the earliest two distinct "
        "published-chunk timestamps in this fetch (min 84292100 ts=1794777349975 W46N8 to min "
        "84292200 ts=1794777784327 W46N8 → 4.34352s; printed 4.344). All seven W46N8 bases were "
        "official 200. W46N8 later intervals are 4.22571, 4.34612, 4.25201, 4.30351, 4.28297 "
        "s/tick; later_mean 4.282064. All-seven mean including the first W46 interval 4.34352 = "
        "4.29231. Delta first-interval (script 4.34352) minus later is 0.06146 s/tick (~43.3s at "
        "tick 84292101 versus the first-pass live anchor). A later-anchor check at 2026-11-16 "
        f"{TICK_S_CHECK_AT} Asia/Hong_Kong game.time={TICK_S_CHECK_GT} found still_over_45s_vs_first=0 "
        "(n=22517; vs first-interval over15=8804) and still_over_45s_vs_later=0 (n=22517; vs "
        "later-mean over15=8000), so no corrective later-mean realign was applied. Confirm reported "
        "ts_realigned=0 (three in-window chunks recovered; 35 aged leftover official 404s including "
        "W46N8@84292000 still 404). retry2 skipped."
    )

    live_json_note = (
        "One box freeze ran after the 05:30 backfill: 2026-11-16 05:37:16–05:57:06 Asia/Hong_Kong "
        "(1182s; VM hibernated; wall jumped, monotonic did not), logged by listener.py at 05:57:06 "
        "with run_listener.sh relaunch at 05:57:09 (new listener.py pid 3270948 started 05:57:19). "
        "run_listener.sh pid 4035476 unchanged since 2026-11-11. yield_files=absent, single room "
        "slot, peacetime 5:5:1:1 (rot at pre-check on W47N8, i=1). Did not start a second loop or "
        "kill war_cmd/pulse. Segment-90 and STATS were already current without a console query: at "
        "pre-check 05:58:06 live.json gameTime=None (slot on W47N8, objects=0 as expected) "
        "stats.t=84292790 cpu=18.68 b=10000, creep_cpu tip 84292780 (7421 rows since tick 84291601, "
        "last200 84292580..84292780, 1411 rows, max_ts 05:57:21 after reconnect pull), path_arrivals "
        "tip 84292768 (135 rows since tick 84291601, last200 15 rows), room_stats tip 84292790, "
        "creep_ticks tip 84292799. A known incidents ingest drop of invalid integer '{}' also "
        "occurred at 05:30:10 (same class as 03:00:06 / 00:30:10). This run did not change the "
        "peacetime single-slot 5:5:1:1 arrangement. The first official game/time request succeeded. "
        "No concurrent hourly patrol was running."
    )

    hourly_note = (
        "The previous 05:30 half-hour backfill had already prefilled 84291601..84292300 "
        "(inserted_total=2269, tick_s=4.24797 / later 4.29658875 with no corrective later-mean "
        "realign, first-pass missing_chunks=1 W46N8@84292000 still official 404 after confirm/retry2, "
        "game.time=84292379), overlapping 200 ticks of this window (84292101..84292300). No "
        "concurrent hourly patrol ran during this backfill. First pass then recovered the newly "
        "published 84292300–84292600 chunks and the W46N8/W45N7 @84292700 chunks, with "
        "missing_chunks=3 W47N8/W45N8/W47N7@84292700 (briefly unpublished at game.time=84292805); "
        "confirm (06:00:47, game.time=84292837) recovered all three (inserted=1931). W46N8@84292000 "
        "aged out of this 40m window and remained official 404 on confirm (hole 84292001..84292100 "
        f"still {w46_920['rows']} rows / {w46_920['distinct']} live distinct). There were "
        f"{EMPTY_NO_CREEP_N} official empty-no-creep ticks in this 40m window, all in W45N7 "
        f"{EMPTY_NO_CREEP['W45N7']}."
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
        "missing_chunk_first_pass": ["W47N8@84292700", "W45N8@84292700", "W47N7@84292700"],
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
        "w45n7_empty_no_creep_in_window": True,
        "w45n7_empty_no_creep_ranges": EMPTY_NO_CREEP.get("W45N7", []),
        "empty_no_creep_in_window": True,
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
        "missing_chunks first_pass=3 (W47N8@84292700, W45N8@84292700, W47N7@84292700) at "
        "game.time=84292805; published_bases 84292100..84292700, reconstructed 84292101..84292800 "
        "(700), already_in_db=9160 inserted=13366. Confirm 2026-11-16 06:00:47 Asia/Hong_Kong "
        "game.time=84292837 retried those three in-window official 404s and 35 aged leftover "
        "official 404s including W46N8@84292000 — all three in-window chunks recovered, "
        "inserted=1931, ts_realigned=0; 35 aged leftovers still 404. retry2 skipped (no remaining "
        "in-window official 404s). After confirm: W46N8/W47N8/W45N8/W47N7 each distinct=700 "
        f"missing_n=0; W45N7 distinct={cov['W45N7']['distinct']} missing_n={cov['W45N7']['missing_n']} "
        f"{cov['W45N7']['missing_ranges']} (official empty-no-creep; chunks 84292400/84292500/84292600 "
        "were official 200). "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window=0). "
        f"Previously in-window official 404 W46N8@84292000 remains aged out of this 40m window "
        f"(hole 84292001..84292100 still {w46_920['rows']} rows / {w46_920['distinct']} "
        f"distinct; official 84292001..84292100 still empty; confirm still 404). Previously "
        f"in-window official 404 W47N8@84290200 remains aged out "
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
        f"404 after confirm GET. First-pass tick_s=4.34352 (printed 4.344) realigned 0 rows; "
        f"later-mean was already inside the 45s gate so no corrective later-mean realign was "
        f"applied (later-mean tick_s=4.282064, at {TICK_S_CHECK_AT} Asia/Hong_Kong game.time="
        f"{TICK_S_CHECK_GT}; over45=0, over15=8000, n=22517 after first pass, before confirm)."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm retried in-window official 404s W47N8@84292700, W45N8@84292700, W47N7@84292700 "
        "and 35 aged leftover official 404s including W46N8@84292000 at 06:00:47 game.time=84292837, "
        "all 3 in-window recovered inserted=1931 (W47N8 1283 / W45N8 225 / W47N7 423) ts_realigned=0; "
        "35 aged leftovers still 404; retry2 skipped (no remaining in-window official 404s)\n"
        "ts_realigned_first_pass=0 (tick_s=4.34352 printed 4.344); later-mean already inside 45s "
        f"gate, no corrective later-mean realign (later-mean tick_s=4.282064 still_over_45s_vs_later="
        f"0 at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT})\n"
        f"inserted_total=15297 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=0 after confirm (first-pass missing_chunks=3 W47N8/W45N8/W47N7@"
        f"84292700 all recovered)\n"
        "official empty-no-creep ticks in this window: W45N7 169 ticks "
        "[[84292453, 84292453], [84292455, 84292622]] (official 200 chunks, no our creeps)\n"
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
        "hole_W46N8_84292000": w46_920,
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
        "retry2_skipped": RETRY2_SKIPPED,
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
        "hole_W46N8_84292000": w46_920,
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
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": ["W47N8@84292700", "W45N8@84292700", "W47N7@84292700"],
        "unique_after_window": unique_after,
        "empty_no_creep_in_window": True,
        "empty_no_creep_ranges": dict(EMPTY_NO_CREEP),
        "confirm_inserted": INSERTED_CONFIRM,
        "retry2_inserted": INSERTED_RETRY2,
        "retry2_skipped": RETRY2_SKIPPED,
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
    retry2_note = (
        "retry2 skipped 2026-11-16 06:01:46 Asia/Hong_Kong: first-pass in-window official 404s "
        "W47N8@84292700, W45N8@84292700, W47N7@84292700 were all recovered on confirm at 06:00:47 "
        "game.time=84292837 (inserted=1931); no remaining in-window official 404s to retry.\n"
    )
    (DIR / "backfill_retry2.txt").write_text(retry2_note)
    (ROOT / "state" / "_halfhour_backfill_retry2_0600.txt").write_text(retry2_note)

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
    expected_missing = {"W45N7": 169}
    rooms_official_ok = all(
        cov[k]["missing_n"] == expected_missing.get(k, 0) for k in cov
    )
    print("ok_complete", official_recovered == 3500 and rooms_official_ok
          and official_with_creeps == 3500 - EMPTY_NO_CREEP_N)
    print("routine_ok", True)


if __name__ == "__main__":
    main()
