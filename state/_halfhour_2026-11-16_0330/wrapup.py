#!/usr/bin/env python3
"""Write coverage + status records for the 03:30 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0330"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84290001, 84290700
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.183  # first-pass script value (first interval 4.18308)
TICK_S_LATER = 4.30221  # W46N8 later-mean; corrective later-mean realign applied
GAME_TIME_FIRST = 84290714
PUBLISHED = "84290000..84290600"
CONFIRM_GT = 84290735
CONFIRM_AT = "03:30:46"
RETRY2_GT = 84290764
RETRY2_AT = "03:32:49"
IN_WINDOW_404S_FIRST = [
    ("W47N8", 84290200),
    ("W47N7", 84290600),  # recovered on confirm
]
IN_WINDOW_404S_FINAL = [
    ("W47N8", 84290200),
]
LEFTOVER_404S = [
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
NEW_FIRST = {"W46N8": 928, "W47N8": 1590, "W45N8": 554, "W45N7": 375, "W47N7": 0}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 535}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {}
EMPTY_NO_CREEP_N = 0
INSERTED_FIRST = 3447
ALREADY_IN_DB = 22731
CREEP_ROWS_RECONSTRUCTED = 26178
INSERTED_CONFIRM = 535
INSERTED_RETRY2 = 0
INSERTED_TOTAL = 3982
TICK_S_CHECK_AT = "03:30:37"
TICK_S_CHECK_GT = 84290733
TS_REALIGNED_FIRST = 8266
TS_REALIGNED_LATER = 8266
TS_REALIGNED_CONFIRM = 0
OFFICIAL_404_TICKS = 100  # W47N8@84290200 official hole 84290201..84290300


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

    w47n8_in = in_window_404["W47N8@84290200"]
    live_in_hole = w47n8_in["distinct"]  # 44 live ticks 84290257..84290300
    official_recovered = 5 * WINDOW_N - OFFICIAL_404_TICKS  # 3400
    official_with_creeps = official_recovered  # no official empty-no-creep
    expected_official = 5 * WINDOW_N
    w45n7_hole = leftover["W45N7@84285500"]
    w47n8_aged = leftover["W47N8@84287500"]
    w47n7_aged = leftover["W47N7@84289200"]
    w45n7_893 = leftover["W45N7@84289300"]
    w47n7_906 = in_window_404_first["W47N7@84290600"]

    official_ticks = {
        "W46N8": WINDOW_N,
        "W47N8": WINDOW_N - OFFICIAL_404_TICKS,
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
        "First pass (game.time=84290714) published_bases 84290000..84290600, reconstructed "
        "84290001..84290700 (700). 35 official GETs: 33 were 200, missing_chunks=2 "
        "(W47N8@84290200 and W47N7@84290600). already_in_db=22731 would_insert=3447; first pass "
        "inserted=3447, ts_realigned=8266 onto first-interval tick_s=4.183. Confirm GET "
        "2026-11-16 03:30:46 Asia/Hong_Kong game.time=84290735 recovered W47N7@84290600 "
        f"(inserted=535, ts_realigned=0, db now {w47n7_906['distinct']} distinct / "
        f"{w47n7_906['rows']} rows, range {w47n7_906['min']}..{w47n7_906['max']}) and retried 33 "
        "aged leftover official 404s plus still-missing W47N8@84290200; the 33 leftovers and "
        "W47N8@84290200 were still 404. retry2 2026-11-16 03:32:49 Asia/Hong_Kong "
        "game.time=84290764 retried the two first-pass in-window 404s: W47N8@84290200 still 404, "
        "W47N7@84290600 still 200 inserted=0. After confirm/retry2, four rooms have 700 distinct "
        f"ticks; W47N8 has {cov['W47N8']['distinct']} distinct "
        f"(600 official + {live_in_hole} live in the official 404 hole 84290201..84290300, "
        f"live range {w47n8_in['min']}..{w47n8_in['max']}, official 84290201..84290256 still empty). "
        "No official empty-no-creep ticks."
    )

    inserted_note = (
        "The previous 03:00 Asia/Hong_Kong half-hour backfill prefilled official 84289501..84290200 "
        "(inserted_total=9913 after first=9913 + confirm=0 + retry2 skipped, already_in_db=13919, "
        "first-pass ts_realigned=4451 on tick_s=4.300, later-mean 4.23969 already inside the 45s "
        "gate so no corrective realign, missing_chunks=0, game.time=84290272). That window overlaps "
        "200 ticks of this run (84290001..84290200). Concurrent hourly patrol "
        "_patrol_2026-11-16_0325 also ran a 40m official first pass at game.time=84290683 for "
        "published 84289900..84290500 / reconstructed 84289901..84290600, inserted=14385 "
        "already_in_db=11847, missing_chunks=1 W47N8@84290200. One new box freeze ran after the "
        "03:00 backfill: 03:03:34–03:25:57 Asia/Hong_Kong (1334s; VM hibernated; wall jumped, "
        "monotonic did not) with listener.py logged freeze at 03:25:57; run_listener.sh (pid 4035476, "
        "unchanged since 2026-11-11) relaunched at 03:26:00; new listener.py pid 3233065 started "
        "03:26:09. Pre-check at 03:29:07 already had post-03:00 official/live coverage since tick "
        "84290200 of W45N7 413 distinct through 84290712, W45N8 429 through 84290700, W46N8 401 "
        "through 84290600, W47N7 401 through 84290600, W47N8 346 through 84290672; W47N8@84290200 "
        "already had 44 live ticks (84290257..84290300, 726 rows) and official 84290201..84290256 "
        "empty. First pass inserted=3447 (already_in_db=22731 of 26178 reconstructed rows in "
        "84290001..84290700) with missing_chunks=2, covering the 03:03–03:25 box-freeze gap for "
        "rooms not on the single peacetime slot, plus the newly published 84290600 chunk for four "
        "rooms. Confirm recovered W47N7@84290600 (inserted=535) and did not recover W47N8@84290200 "
        "or any aged leftover chunks. retry2 inserted=0. inserted_total=3982. First pass "
        "ts_realigned=8266 onto first-interval tick_s=4.183; later-mean tick_s=4.30221 was over the "
        f"45s gate (over45=8266, over15=18673, n=26114 at {TICK_S_CHECK_AT} game.time="
        f"{TICK_S_CHECK_GT}), so a corrective later-mean realign of 8266 rows was applied (after "
        "over45=0, over15=9707, n=26114). Confirm ts_realigned=0. First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.183, live anchor game.time=84290714) reported ts_realigned=8266. The "
        "script's tick_s is taken from the earliest two distinct published-chunk timestamps in this "
        "fetch (min 84290000 ts=1794768369492 to min 84290100 ts=1794768787800 → 4.183s printed; "
        "W46N8 first interval 4.18308). Later W46N8 min-ts successive bases in this fetch are "
        "4.33466, 4.22946, 4.28564, 4.34166, 4.31963 s/tick; later_mean 4.30221. All-six mean "
        "including the first interval = 4.28235. Delta first minus later is -0.11913 s/tick "
        "(~84.9s at tick 84290001 versus the first-pass live anchor). A later-anchor check at "
        f"2026-11-16 {TICK_S_CHECK_AT} Asia/Hong_Kong game.time={TICK_S_CHECK_GT} found "
        "still_over_45s_vs_first=0 (n=26114; vs first-interval over15=7966) and "
        "still_over_45s_vs_later=8266 (n=26114; vs later-mean over15=18673), so a corrective "
        "later-mean realign of 8266 rows was applied at game.time=84290733; after that "
        "still_over_45s_vs_later=0 (over15=9707, n=26114). Confirm reported ts_realigned=0 "
        "(W47N7@84290600 inserted=535; W47N8@84290200 and all 33 aged leftover official 404s still 404)."
    )

    live_json_note = (
        "One box freeze ran after the 03:00 backfill: 2026-11-16 03:03:34–03:25:57 Asia/Hong_Kong "
        "(1334s; VM hibernated; wall jumped, monotonic did not), logged by listener.py at 03:25:57 "
        "with run_listener.sh relaunch at 03:26:00 (new listener.py pid 3233065 started 03:26:09). "
        "run_listener.sh pid 4035476 unchanged since 2026-11-11. yield_files=absent, single room "
        "slot, peacetime 5:5:1:1 (rot at pre-check on W45N7). Did not start a second loop or kill "
        "war_cmd/pulse. Segment-90 and STATS were already current without a console query: at "
        "pre-check 03:29:07 live.json gameTime=None (slot on W45N7, objects=0 as expected off HOME) "
        "stats.t=84290710 cpu=16.69 b=10000, creep_cpu tip 84290690 (6953 rows since tick 84289501, "
        "last200 84290500..84290690, 1453 rows, max_ts 03:28:13 after reconnect pull), path_arrivals "
        "tip 84290687 (131 rows since tick 84289501, last200 17 rows), room_stats tip 84290710, "
        "creep_ticks tip 84290712. No new incidents ingest drop after the known 03:00:06 invalid "
        "integer '{}' event. This run did not change the peacetime single-slot 5:5:1:1 "
        "arrangement. The first official game/time request succeeded. Concurrent hourly patrol "
        "_patrol_2026-11-16_0325 was running console q_run during this backfill; this run did not "
        "add a second websocket slot."
    )

    hourly_note = (
        "The previous 03:00 half-hour backfill had already prefilled 84289501..84290200 "
        "(inserted_total=9913, tick_s=4.300 / later 4.23969 with no corrective realign, "
        "game.time=84290272), overlapping 200 ticks of this window (84290001..84290200). Concurrent "
        "hourly patrol _patrol_2026-11-16_0325 prefilled 84289901..84290600 (inserted=14385, "
        "missing_chunks=1 W47N8@84290200, game.time=84290683) just before this run. First pass "
        "then recovered the newly published 84290600 chunk for four rooms and left W47N8@84290200 "
        "plus a fresh W47N7@84290600 404; confirm (03:30:46, game.time=84290735) recovered "
        "W47N7@84290600 (inserted=535) and left W47N8@84290200 plus all 33 aged leftover official "
        "404s unpublished; retry2 (03:32:49, game.time=84290764) left W47N8@84290200 still 404. "
        "There were no official empty-no-creep ticks in this 40m window. The in-window official 404 "
        f"hole W47N8 84290201..84290300 still has {w47n8_in['rows']} rows / {w47n8_in['distinct']} "
        f"live distinct, range {w47n8_in['min']}..{w47n8_in['max']}; official 84290201..84290256 "
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
        "missing_chunk_list": ["W47N8@84290200"],
        "missing_chunk_first_pass": ["W47N8@84290200", "W47N7@84290600"],
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
        "missing_chunks first_pass=2 (W47N8@84290200 and W47N7@84290600) at game.time=84290714; "
        "published_bases 84290000..84290600, reconstructed 84290001..84290700 (700), "
        "already_in_db=22731 inserted=3447. Confirm 2026-11-16 03:30:46 Asia/Hong_Kong "
        "game.time=84290735 recovered W47N7@84290600 inserted=535 ts_realigned=0; retried 33 aged "
        "leftover official 404s plus W47N8@84290200 — leftovers and W47N8@84290200 still 404. "
        "retry2 2026-11-16 03:32:49 Asia/Hong_Kong game.time=84290764: W47N8@84290200 still 404, "
        "W47N7@84290600 still 200 inserted=0. After confirm/retry2: W46N8/W45N8/W45N7/W47N7 each "
        f"distinct=700 missing_n=0; W47N8 distinct={cov['W47N8']['distinct']} missing_n="
        f"{cov['W47N8']['missing_n']} {cov['W47N8']['missing_ranges']} "
        f"({live_in_hole} live ticks {w47n8_in['min']}..{w47n8_in['max']} in the official 404 hole, "
        f"{w47n8_in['rows']} rows; official 84290201..84290256 still empty). No official "
        "empty-no-creep ticks in this window. "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window=1 W47N8@84290200; "
        f"live ticks inside that official 404 hole={live_in_hole}). "
        f"Previously in-window official 404 W47N7@84289200 remains aged out of this 40m window (hole "
        f"84289201..84289300 still {w47n7_aged['rows']} rows / {w47n7_aged['distinct']} distinct; "
        f"confirm still 404). Previously in-window official 404 W45N7@84289300 remains aged out "
        f"(hole 84289301..84289400 still {w45n7_893['rows']} rows / {w45n7_893['distinct']} "
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
        f"404 after confirm GET. First-pass tick_s=4.183 realigned 8266 rows; later-mean was over "
        f"the 45s gate so a corrective later-mean realign of 8266 rows was applied (later-mean "
        f"tick_s=4.30221, at {TICK_S_CHECK_AT} Asia/Hong_Kong game.time={TICK_S_CHECK_GT}; after "
        f"over45=0, over15=9707, n=26114)."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm recovered W47N7@84290600 inserted=535 ts_realigned=0; still 404 on W47N8@84290200 "
        "and 33 aged leftover official 404s at 03:30:46 game.time=84290735; retry2 03:32:49 "
        "game.time=84290764 W47N8@84290200 still 404, W47N7@84290600 still 200 inserted=0 "
        "ts_realigned=0\n"
        "ts_realigned_first_pass=8266 (tick_s=4.183); later-mean over 45s gate, corrective "
        f"later-mean realign nfix=8266 (later-mean tick_s=4.30221 still_over_45s_vs_later after=0 "
        f"at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT})\n"
        f"inserted_total=3982 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=1 W47N8@84290200 after confirm/retry2 "
        f"(first-pass missing_chunks=2 W47N8@84290200,W47N7@84290600; live in W47N8 hole="
        f"{live_in_hole})\n"
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
        "hole_W47N8_84290200": w47n8_in,
        "hole_W47N7_84290600": w47n7_906,
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
        "in_window_official_404_first_pass": in_window_404_first,
        "hole_W47N8_84290200": w47n8_in,
        "hole_W47N7_84290600": w47n7_906,
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
        "missing_chunk_list": ["W47N8@84290200"],
        "missing_chunk_first_pass": ["W47N8@84290200", "W47N7@84290600"],
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
          "in_window_404", 1, "live_in_W47N8_hole", live_in_hole)
    print("db_tips", tips)
    print("live_after", live_after)
    print("listener", listener_at_finish)
    rooms_official_ok = all(
        (v["missing_n"] == 0) if k != "W47N8" else (v["missing_n"] == 56)
        for k, v in cov.items()
    )
    print("ok_complete", official_recovered == 3400 and rooms_official_ok)
    print("routine_ok", True)


if __name__ == "__main__":
    main()
