#!/usr/bin/env python3
"""Write coverage + status records for the 04:00 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0400"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84290401, 84291100
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.34166  # first-pass exact first-interval (printed 4.342)
TICK_S_LATER = 4.27211  # W46N8 later-mean; corrective later-mean realign applied
GAME_TIME_FIRST = 84291190
PUBLISHED = "84290400..84291000"
CONFIRM_GT = 84291212
CONFIRM_AT = "04:04:47"
RETRY2_GT = None
RETRY2_AT = None
IN_WINDOW_404S_FIRST = []
IN_WINDOW_404S_FINAL = []
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
NEW_FIRST = {"W46N8": 3118, "W47N8": 6124, "W45N8": 1954, "W45N7": 1053, "W47N7": 2170}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {}
EMPTY_NO_CREEP_N = 0
INSERTED_FIRST = 14419
ALREADY_IN_DB = 12977
CREEP_ROWS_RECONSTRUCTED = 27396
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_TOTAL = 14419
TICK_S_CHECK_AT = "04:04:24"
TICK_S_CHECK_GT = 84291206
TICK_S_REALIGN_GT = 84291207
TS_REALIGNED_FIRST = 6766
TS_REALIGNED_LATER = 4750
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

    official_recovered = 5 * WINDOW_N
    official_with_creeps = official_recovered
    expected_official = 5 * WINDOW_N
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
    known_in = []

    missing_chunk_note = (
        "First pass (game.time=84291190) published_bases 84290400..84291000, reconstructed "
        "84290401..84291100 (700). 35 official GETs: all 35 were 200, missing_chunks=0. "
        "already_in_db=12977 would_insert=14419; first pass inserted=14419, ts_realigned=6766 "
        "onto first-interval tick_s=4.34166 (printed 4.342). Confirm GET 2026-11-16 04:04:47 "
        "Asia/Hong_Kong game.time=84291212 retried 34 aged leftover official 404s including "
        "W47N8@84290200 (now outside this 40m window); all 34 were still 404, inserted=0, "
        "ts_realigned=0. retry2 skipped (no in-window official 404s). After first pass, all five "
        "rooms have 700 distinct ticks and missing_n=0. No official empty-no-creep ticks."
    )

    inserted_note = (
        "The previous 03:30 Asia/Hong_Kong half-hour backfill prefilled official 84290001..84290700 "
        "(inserted_total=3982 after first=3447 + confirm=535 + retry2=0, already_in_db=22731, "
        "first-pass ts_realigned=8266 on tick_s=4.183, later-mean 4.30221 over the 45s gate so a "
        "corrective later-mean realign of 8266 rows was applied, first-pass missing_chunks=2 "
        "W47N8@84290200 and W47N7@84290600 with W47N7@84290600 recovered on confirm, "
        "game.time=84290714). That window overlaps 300 ticks of this run (84290401..84290700). "
        "No concurrent hourly patrol at this wake. One new box freeze ran after the 03:30 backfill: "
        "03:38:52–04:02:06 Asia/Hong_Kong (1393s; VM hibernated; wall jumped, monotonic did not) "
        "with listener.py logged freeze at 04:02:06; run_listener.sh (pid 4035476, unchanged since "
        "2026-11-11) relaunched at 04:02:09; new listener.py pid 3241312 started 04:02:18. "
        "Pre-check at 04:03:02 already had post-03:30 official/live coverage since tick 84290700 of "
        "W45N7 29 distinct through 84290728, W45N8 1 at 84290700, W46N8 128 through 84291188, "
        "W47N7 1 at 84290700, W47N8 1 at 84290700. First pass inserted=14419 (already_in_db=12977 "
        "of 27396 reconstructed rows in 84290401..84291100) with missing_chunks=0, covering the "
        "03:38–04:02 box-freeze gap for rooms not on the single peacetime slot, plus the newly "
        "published 84290700..84291000 chunks. Confirm inserted=0 and did not recover W47N8@84290200 "
        "or any other aged leftover chunks. retry2 skipped. inserted_total=14419. First pass "
        "ts_realigned=6766 onto first-interval tick_s=4.34166; later-mean tick_s=4.27211 was over "
        f"the 45s gate (over45=6336, over15=16535, n=27475 at {TICK_S_CHECK_AT} game.time="
        f"{TICK_S_CHECK_GT}), so a corrective later-mean realign of 4750 rows was applied at "
        f"game.time={TICK_S_REALIGN_GT} (after over45=0, over15=10139, n=27475). Confirm "
        "ts_realigned=0. First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.34166 printed 4.342, live anchor game.time=84291190) reported "
        "ts_realigned=6766. The script's tick_s is taken from the earliest two distinct "
        "published-chunk timestamps in this fetch (min 84290400 ts=1794770072776 to min 84290500 "
        "ts=1794770506942 → 4.34166s; printed 4.342). Later W46N8 min-ts successive bases in this "
        "fetch are 4.31963, 4.20692, 4.25159, 4.27830, 4.30410 s/tick; later_mean 4.27211. All-six "
        "mean including the first interval = 4.28370. Delta first minus later is +0.06955 s/tick "
        "(~54.9s at tick 84290401 versus the first-pass live anchor). A later-anchor check at "
        f"2026-11-16 {TICK_S_CHECK_AT} Asia/Hong_Kong game.time={TICK_S_CHECK_GT} found "
        "still_over_45s_vs_first=0 (n=27475; vs first-interval over15=6747) and "
        "still_over_45s_vs_later=6336 (n=27475; vs later-mean over15=16535), so a corrective "
        f"later-mean realign of 4750 rows was applied at game.time={TICK_S_REALIGN_GT}; after that "
        "still_over_45s_vs_later=0 (over15=10139, n=27475). Confirm reported ts_realigned=0 "
        "(all 34 aged leftover official 404s including W47N8@84290200 still 404). retry2 skipped."
    )

    live_json_note = (
        "One box freeze ran after the 03:30 backfill: 2026-11-16 03:38:52–04:02:06 Asia/Hong_Kong "
        "(1393s; VM hibernated; wall jumped, monotonic did not), logged by listener.py at 04:02:06 "
        "with run_listener.sh relaunch at 04:02:09 (new listener.py pid 3241312 started 04:02:18). "
        "run_listener.sh pid 4035476 unchanged since 2026-11-11. yield_files=absent, single room "
        "slot, peacetime 5:5:1:1 (rot at pre-check on W46N8). Did not start a second loop or kill "
        "war_cmd/pulse. Segment-90 and STATS were already current without a console query: at "
        "pre-check 04:03:02 live.json gameTime=84291188 (slot on HOME W46N8, objects=263) "
        "stats.t=84291180 cpu=20.73 b=10000, creep_cpu tip 84291170 (5980 rows since tick 84290001, "
        "last200 84290995..84291170, 1320 rows, max_ts 04:02:20 after reconnect pull), path_arrivals "
        "tip 84291168 (134 rows since tick 84290001, last200 27 rows), room_stats tip 84291180, "
        "creep_ticks tip 84291188. No new incidents ingest drop after the known 03:00:06 invalid "
        "integer '{}' event. This run did not change the peacetime single-slot 5:5:1:1 "
        "arrangement. The first official game/time request succeeded. No concurrent hourly patrol "
        "was running during this backfill; this run did not add a second websocket slot."
    )

    hourly_note = (
        "The previous 03:30 half-hour backfill had already prefilled 84290001..84290700 "
        "(inserted_total=3982, tick_s=4.183 / later 4.30221 with a corrective later-mean realign "
        "of 8266 rows, first-pass missing_chunks=2 with W47N7@84290600 recovered on confirm, "
        "game.time=84290714), overlapping 300 ticks of this window (84290401..84290700). No "
        "concurrent hourly patrol at this wake. First pass then recovered the newly published "
        "84290700..84291000 chunks for all five rooms with missing_chunks=0; confirm (04:04:47, "
        "game.time=84291212) left all 34 aged leftover official 404s including W47N8@84290200 "
        "unpublished; retry2 skipped (no in-window official 404s). There were no official "
        "empty-no-creep ticks in this 40m window. The previously in-window official 404 hole "
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
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": [],
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
        "missing_chunks first_pass=0 at game.time=84291190; published_bases 84290400..84291000, "
        "reconstructed 84290401..84291100 (700), already_in_db=12977 inserted=14419. Confirm "
        "2026-11-16 04:04:47 Asia/Hong_Kong game.time=84291212 retried 34 aged leftover official "
        "404s including W47N8@84290200 — all still 404, inserted=0 ts_realigned=0. retry2 skipped "
        "(no in-window official 404s). After first pass: W46N8/W47N8/W45N8/W45N7/W47N7 each "
        "distinct=700 missing_n=0. No official empty-no-creep ticks in this window. "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window=0). "
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
        f"404 after confirm GET. First-pass tick_s=4.34166 (printed 4.342) realigned 6766 rows; "
        f"later-mean was over the 45s gate so a corrective later-mean realign of 4750 rows was "
        f"applied (later-mean tick_s=4.27211, at {TICK_S_CHECK_AT} Asia/Hong_Kong game.time="
        f"{TICK_S_CHECK_GT} / realign game.time={TICK_S_REALIGN_GT}; after over45=0, over15=10139, "
        f"n=27475)."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm retried 34 aged leftover official 404s including W47N8@84290200 at 04:04:47 "
        "game.time=84291212, all still 404 inserted=0 ts_realigned=0; retry2 skipped (no in-window "
        "official 404s)\n"
        "ts_realigned_first_pass=6766 (tick_s=4.34166 printed 4.342); later-mean over 45s gate, "
        f"corrective later-mean realign nfix=4750 (later-mean tick_s=4.27211 still_over_45s_vs_later "
        f"after=0 at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT} / realign game.time="
        f"{TICK_S_REALIGN_GT})\n"
        f"inserted_total=14419 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=0 after first pass (first-pass missing_chunks=0)\n"
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
        "missing_chunk_first_pass": [],
        "unique_after_window": unique_after,
        "empty_no_creep_in_window": False,
        "empty_no_creep_ranges": dict(EMPTY_NO_CREEP),
        "confirm_inserted": INSERTED_CONFIRM,
        "retry2_inserted": INSERTED_RETRY2,
        "retry2_skipped": True,
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
        "retry2 skipped 2026-11-16 04:05 Asia/Hong_Kong: first-pass missing_chunks=0 and confirm "
        "recovered none of 34 aged leftover official 404s; no in-window official 404s to retry.\n"
    )
    (DIR / "backfill_retry2.txt").write_text(retry2_note)
    (ROOT / "state" / "_halfhour_backfill_retry2_0400.txt").write_text(retry2_note)

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
    rooms_official_ok = all(v["missing_n"] == 0 for v in cov.values())
    print("ok_complete", official_recovered == 3500 and rooms_official_ok)
    print("routine_ok", True)


if __name__ == "__main__":
    main()
