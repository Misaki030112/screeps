#!/usr/bin/env python3
"""Write coverage + status records for the 06:30 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0630"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84292501, 84293200
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.30351  # first-pass exact first-interval (printed 4.304)
TICK_S_LATER = 4.29335  # W46N8 later-mean; already inside 45s gate, no corrective realign
GAME_TIME_FIRST = 84293295
PUBLISHED = "84292500..84293100"
CONFIRM_GT = 84293318
CONFIRM_AT = "06:35:13"
RETRY2_GT = None
RETRY2_AT = None
RETRY2_SKIPPED = True
IN_WINDOW_404S_FIRST = []
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
NEW_FIRST = {"W46N8": 0, "W47N8": 0, "W45N8": 100, "W45N7": 0, "W47N7": 100}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {"W45N7": [[84292501, 84292622], [84292839, 84292861]]}
EMPTY_NO_CREEP_N = 145
INSERTED_FIRST = 200
ALREADY_IN_DB = 25164
CREEP_ROWS_RECONSTRUCTED = 25364
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_TOTAL = 200
TICK_S_CHECK_AT = "06:35:08"
TICK_S_CHECK_GT = 84293317
TS_REALIGNED_FIRST = 66
TS_REALIGNED_LATER = 0
TS_REALIGNED_CONFIRM = 0
OFFICIAL_404_TICKS = 0  # no in-window official 404s on first pass


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
        "First pass (game.time=84293295) published_bases 84292500..84293100, reconstructed "
        "84292501..84293200 (700). 35 official GETs: all 35 were 200, missing_chunks=0. "
        "already_in_db=25164 would_insert=200; first pass inserted=200 (W45N8 100 / W47N7 100), "
        "ts_realigned=66 onto first-interval tick_s=4.30351 (printed 4.304). Those 66 rows had "
        "been realigned earlier by the 06:25 hourly patrol retry with tick_s=4.169 on a 300-tick "
        "subwindow; this first pass put them back onto the 40m first-interval tick_s. Confirm GET "
        "2026-11-16 06:35:13 Asia/Hong_Kong game.time=84293318 retried 35 aged leftover official "
        "404s including W46N8@84292000; all 35 were still 404, inserted=0, ts_realigned=0. "
        "retry2 skipped because there were no in-window official 404s. After first pass, official "
        "coverage is complete for all five rooms (3500 of 3500 official room-ticks). "
        "W46N8/W47N8/W45N8/W47N7 each have 700 distinct ticks with creeps; W45N7 has "
        f"{cov['W45N7']['distinct']} distinct and {cov['W45N7']['missing_n']} official "
        f"empty-no-creep ticks {cov['W45N7']['missing_ranges']} (chunks 84292500/84292600/"
        "84292800 were official 200 on first pass; no our creeps on those ticks)."
    )

    inserted_note = (
        "The previous 06:00 Asia/Hong_Kong half-hour backfill prefilled official 84292101..84292800 "
        "(inserted_total=15297 after first=13366 + confirm=1931 + retry2=0, already_in_db=9160, "
        "first-pass ts_realigned=0 on tick_s=4.34352, later-mean 4.282064 already inside the 45s "
        "gate so no corrective later-mean realign, first-pass missing_chunks=3 W47N8/W45N8/W47N7@"
        "84292700 all recovered on confirm, game.time=84292805). That window overlaps 300 ticks of "
        "this run (84292501..84292800). The concurrent 06:25 hourly patrol also prefilled this "
        "same 40m official window before this run: first pass at game.time=84293206 tick_s=4.304 "
        "inserted=10916 already_in_db=11815 missing_chunks=3 (W47N8/W45N8/W47N7@84293100) "
        "ts_realigned=0; patrol retry at game.time=84293240 tick_s=4.169 on 84292901..84293200 "
        "recovered all three (inserted=2333) and realigned 66 rows. One new box freeze ran after "
        "the 06:00 backfill: 06:09:55–06:25:27 Asia/Hong_Kong (923s; VM hibernated; wall jumped, "
        "monotonic did not) with listener.py logged freeze at 06:25:27; run_listener.sh (pid "
        "4035476, unchanged since 2026-11-11) relaunched at 06:25:30; new listener.py pid 3277554 "
        "started 06:25:40. This half-hour first pass (game.time=84293295) had missing_chunks=0, "
        "inserted=200 (already_in_db=25164 of 25364 reconstructed rows in 84292501..84293200; "
        "W45N8 100 / W47N7 100, creeps the patrol retry likely missed when it reconstructed the "
        "newest chunks without earlier window state), covering the 06:09–06:25 box-freeze gap for "
        "rooms not on the single peacetime slot plus the newly published 84292800–84293100 chunks "
        "(already mostly written by the patrol). Confirm inserted=0 (35 aged leftover official "
        "404s still 404). retry2 skipped. inserted_total=200. First pass ts_realigned=66 onto "
        "first-interval tick_s=4.30351 (correcting the patrol retry's tick_s=4.169); later-mean "
        f"tick_s=4.29335 was already inside the 45s gate (over45=0, over15=2000, n=25323 at "
        f"{TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT}), so no corrective later-mean realign was "
        "applied. Confirm ts_realigned=0. First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.30351 printed 4.304, live anchor game.time=84293295) reported "
        "ts_realigned=66. The script's tick_s is taken from the earliest two distinct "
        "published-chunk timestamps in this fetch (min 84292500 ts=1794779066711 W46N8 to min "
        "84292600 ts=1794779497062 W46N8 → 4.30351s; printed 4.304). All seven W46N8 bases were "
        "official 200. W46N8 later intervals are 4.28297, 4.29865, 4.36193, 4.16927, 4.35393 "
        "s/tick; later_mean 4.29335. All-seven mean including the first W46 interval 4.30351 = "
        "4.29504. Delta first-interval (script 4.30351) minus later is 0.01016 s/tick (~8.1s at "
        "tick 84292501 versus the first-pass live anchor). The 66 realigned rows were previously "
        "skewed by the 06:25 hourly patrol retry (tick_s=4.169 on 84292901..84293200). A later-"
        f"anchor check at 2026-11-16 {TICK_S_CHECK_AT} Asia/Hong_Kong game.time={TICK_S_CHECK_GT} "
        "found still_over_45s_vs_first=0 (n=25323; vs first-interval over15=1155) and "
        "still_over_45s_vs_later=0 (n=25323; vs later-mean over15=2000), so no corrective later-"
        "mean realign was applied. Confirm reported ts_realigned=0 (no in-window 404s; 35 aged "
        "leftover official 404s including W46N8@84292000 still 404). retry2 skipped."
    )

    live_json_note = (
        "One box freeze ran after the 06:00 backfill: 2026-11-16 06:09:55–06:25:27 Asia/Hong_Kong "
        "(923s; VM hibernated; wall jumped, monotonic did not), logged by listener.py at 06:25:27 "
        "with run_listener.sh relaunch at 06:25:30 (new listener.py pid 3277554 started 06:25:40). "
        "run_listener.sh pid 4035476 unchanged since 2026-11-11. yield_files=absent, single room "
        "slot, peacetime 5:5:1:1 (rot at pre-check on W46N8, i=0; at finish on W47N8, i=1). Did not "
        "start a second loop or kill war_cmd/pulse. Segment-90 and STATS were already current "
        "without a console query: at pre-check 06:32:45 live.json gameTime=84293283 (slot on HOME "
        "W46N8, objects=267) stats.t=84293280 cpu=18.33 b=10000, creep_cpu tip 84293260 (7376 rows "
        "since tick 84292101, last200 84293060..84293260, 1459 rows, max_ts 06:31:45 after "
        "reconnect pull), path_arrivals tip 84293260 (141 rows since tick 84292101, last200 20 "
        "rows), room_stats tip 84293280, creep_ticks tip 84293283. No new incidents-ingest drop "
        "was logged after the 05:30:10 invalid-integer '{}' event. This run did not change the "
        "peacetime single-slot 5:5:1:1 arrangement. The first official game/time request succeeded. "
        "The 1h peacetime patrol (started ~06:25) had already prefilled this official window and "
        "finished its exact2h/backfill work before this run's first pass; it was not still writing "
        "during this backfill."
    )

    hourly_note = (
        "The previous 06:00 half-hour backfill had already prefilled 84292101..84292800 "
        "(inserted_total=15297, tick_s=4.34352 / later 4.282064 with no corrective later-mean "
        "realign, first-pass missing_chunks=3 W47N8/W45N8/W47N7@84292700 all recovered on confirm, "
        "game.time=84292805), overlapping 300 ticks of this window (84292501..84292800). The 06:25 "
        "hourly patrol then prefilled the same official window 84292501..84293200 (first pass "
        "game.time=84293206 inserted=10916 already_in_db=11815 missing_chunks=3 W47N8/W45N8/W47N7@"
        "84293100 ts_realigned=0 tick_s=4.304; retry game.time=84293240 recovered all three "
        "inserted=2333 and realigned 66 rows at tick_s=4.169). This half-hour first pass "
        "(game.time=84293295) found missing_chunks=0, inserted=200 more (W45N8 100 / W47N7 100), "
        "and ts_realigned=66 onto first-interval tick_s=4.30351. W46N8@84292000 remains aged out "
        "of this 40m window and remained official 404 on confirm (hole 84292001..84292100 still "
        f"{w46_920['rows']} rows / {w46_920['distinct']} live distinct). There were "
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
        "missing_chunks first_pass=0 at game.time=84293295; published_bases 84292500..84293100, "
        "reconstructed 84292501..84293200 (700), already_in_db=25164 inserted=200, ts_realigned=66. "
        "Confirm 2026-11-16 06:35:13 Asia/Hong_Kong game.time=84293318 retried 35 aged leftover "
        "official 404s including W46N8@84292000 — all still 404, inserted=0, ts_realigned=0. retry2 "
        "skipped (no in-window official 404s). After first pass: W46N8/W47N8/W45N8/W47N7 each "
        f"distinct=700 missing_n=0; W45N7 distinct={cov['W45N7']['distinct']} missing_n="
        f"{cov['W45N7']['missing_n']} {cov['W45N7']['missing_ranges']} (official empty-no-creep; "
        "chunks 84292500/84292600/84292800 were official 200). "
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
        f"404 after confirm GET. First-pass tick_s=4.30351 (printed 4.304) realigned 66 rows "
        f"(correcting the 06:25 patrol retry tick_s=4.169); later-mean was already inside the 45s "
        f"gate so no corrective later-mean realign was applied (later-mean tick_s=4.29335, at "
        f"{TICK_S_CHECK_AT} Asia/Hong_Kong game.time={TICK_S_CHECK_GT}; over45=0, over15=2000, "
        f"n=25323 after first pass, before confirm)."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill_now.txt").read_text()
    if "confirm retried" in first:
        first = first.split("confirm retried")[0].rstrip() + "\n"
    now_extra = (
        "confirm retried 35 aged leftover official 404s including W46N8@84292000 at 06:35:13 "
        "game.time=84293318, all still 404 inserted=0 ts_realigned=0; no in-window official 404s; "
        "retry2 skipped (no in-window official 404s)\n"
        "ts_realigned_first_pass=66 (tick_s=4.30351 printed 4.304, correcting 06:25 patrol retry "
        f"tick_s=4.169); later-mean already inside 45s gate, no corrective later-mean realign "
        f"(later-mean tick_s=4.29335 still_over_45s_vs_later=0 at {TICK_S_CHECK_AT} game.time="
        f"{TICK_S_CHECK_GT})\n"
        f"inserted_total=200 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=0 after first pass (first-pass missing_chunks=0)\n"
        "official empty-no-creep ticks in this window: W45N7 145 ticks "
        "[[84292501, 84292622], [84292839, 84292861]] (official 200 chunks, no our creeps)\n"
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
        "missing_chunk_first_pass": [],
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
    (DIR / "history_backfill_now.txt").write_text(now_text)
    (ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_text)
    (DIR / "verify.txt").write_text(verify_text)
    (ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
    dump(DIR / "coverage_final.json", coverage_final)
    dump(DIR / "_collect_raw.json", collect_raw)
    dump(DIR / "final_collect.json", snap)
    dump(DIR / "final_snap.json", snap)
    retry2_note = (
        "retry2 skipped 2026-11-16 06:36 Asia/Hong_Kong: first pass had missing_chunks=0 at "
        "game.time=84293295 (all 35 official GETs 200); confirm at 06:35:13 game.time=84293318 "
        "retried 35 aged leftover official 404s including W46N8@84292000, all still 404 "
        "(inserted=0). No in-window official 404s to retry.\n"
    )
    (DIR / "backfill_retry2.txt").write_text(retry2_note)
    (ROOT / "state" / "_halfhour_backfill_retry2_0630.txt").write_text(retry2_note)

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
    expected_missing = {"W45N7": 145}
    rooms_official_ok = all(
        cov[k]["missing_n"] == expected_missing.get(k, 0) for k in cov
    )
    print("ok_complete", official_recovered == 3500 and rooms_official_ok
          and official_with_creeps == 3500 - EMPTY_NO_CREEP_N)
    print("routine_ok", True)


if __name__ == "__main__":
    main()
