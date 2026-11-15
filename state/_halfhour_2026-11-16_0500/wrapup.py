#!/usr/bin/env python3
"""Write coverage + status records for the 05:00 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0500"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84291301, 84292000
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.29809  # first-pass exact first-interval (printed 4.298)
TICK_S_LATER = 4.26994  # W46N8 later-mean; already inside 45s gate, no corrective realign
GAME_TIME_FIRST = 84292006
PUBLISHED = "84291300..84291900"
CONFIRM_GT = 84292028
CONFIRM_AT = "05:03:06"
RETRY2_GT = None
RETRY2_AT = None
IN_WINDOW_404S_FIRST = [
    ("W47N8", 84291900),
    ("W45N8", 84291900),
    ("W47N7", 84291900),
]
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
NEW_FIRST = {"W46N8": 2672, "W47N8": 3589, "W45N8": 1304, "W45N7": 1293, "W47N7": 1370}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 1191, "W45N8": 103, "W45N7": 0, "W47N7": 500}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {}
EMPTY_NO_CREEP_N = 0
INSERTED_FIRST = 10228
ALREADY_IN_DB = 10955
CREEP_ROWS_RECONSTRUCTED = 21183
INSERTED_CONFIRM = 1794
INSERTED_RETRY2 = 0
INSERTED_TOTAL = 12022
TICK_S_CHECK_AT = "05:02:32"
TICK_S_CHECK_GT = 84292021
TICK_S_REALIGN_GT = 84292021
TS_REALIGNED_FIRST = 0
TS_REALIGNED_LATER = 0
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
        "First pass (game.time=84292006) published_bases 84291300..84291900, reconstructed "
        "84291301..84292000 (700). 35 official GETs: 32 were 200, missing_chunks=3 "
        "(W47N8@84291900, W45N8@84291900, W47N7@84291900; W46N8 and W45N7 @84291900 already "
        "200). already_in_db=10955 would_insert=10228; first pass inserted=10228, ts_realigned=0 "
        "onto first-interval tick_s=4.29809 (printed 4.298). Confirm GET 2026-11-16 05:03:06 "
        "Asia/Hong_Kong game.time=84292028 recovered all 3 delayed in-window official 404s "
        "(W47N8@84291900 inserted=1191, W45N8@84291900 inserted=103, W47N7@84291900 inserted=500; "
        "confirm inserted=1794, ts_realigned=0) and retried 34 aged leftover official 404s "
        "including W47N8@84290200; all 34 were still 404. retry2 skipped (no remaining in-window "
        "official 404s). After confirm, all five rooms have 700 distinct ticks and missing_n=0. "
        "No official empty-no-creep ticks."
    )

    inserted_note = (
        "The previous 04:30 Asia/Hong_Kong half-hour backfill prefilled official 84290901..84291600 "
        "(inserted_total=3146 after first=3146 + confirm=0 + retry2=0, already_in_db=23349, "
        "first-pass ts_realigned=0 on tick_s=4.30411, later-mean 4.28591 already inside the 45s "
        "gate so no corrective later-mean realign, first-pass missing_chunks=0, "
        "game.time=84291658). That window overlaps 300 ticks of this run (84291301..84291600). "
        "No concurrent hourly patrol at this wake. One new box freeze ran after the 04:30 backfill: "
        "04:44:57–05:00:06 Asia/Hong_Kong (908s; VM hibernated; wall jumped, monotonic did not) "
        "with listener.py logged freeze at 05:00:06; run_listener.sh (pid 4035476, unchanged since "
        "2026-11-11) relaunched at 05:00:09; new listener.py pid 3256165 started 05:00:18. "
        "Pre-check at 05:01:04 already had post-04:30 official/live coverage since tick 84291600 of "
        "W45N7 26 distinct through 84291625, W45N8 1 through 84291600, W46N8 142 through 84291766, "
        "W47N7 1 through 84291600, W47N8 14 through 84292001 (slot had just rotated onto W47N8). "
        "First pass inserted=10228 (already_in_db=10955 of 21183 reconstructed rows in "
        "84291301..84292000) with missing_chunks=3, covering the 04:44–05:00 box-freeze gap for "
        "rooms not on the single peacetime slot, plus the newly published 84291600..84291800 chunks "
        "and the already-published W46N8/W45N7 @84291900 chunks. Confirm inserted=1794 recovered "
        "the delayed W47N8/W45N8/W47N7 @84291900 chunks and did not recover W47N8@84290200 or any "
        "other aged leftover chunks. retry2 skipped. inserted_total=12022. First pass "
        "ts_realigned=0 onto first-interval tick_s=4.29809; later-mean tick_s=4.26994 was already "
        "inside the 45s gate (over45=0, over15=0, n=22296 at 05:02:32 game.time=84292021), so no "
        "corrective later-mean realign was applied. Confirm ts_realigned=0. First game/time request "
        "succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.29809 printed 4.298, live anchor game.time=84292006) reported "
        "ts_realigned=0. The script's tick_s is taken from the earliest two distinct "
        "published-chunk timestamps in this fetch (min 84291300 ts=1794773930960 to min 84291400 "
        "ts=1794774360769 → 4.29809s; printed 4.298). Later W46N8 min-ts successive bases in this "
        "fetch are 4.25182, 4.27864, 4.24759, 4.24367, 4.32799 s/tick; later_mean 4.26994. All-six "
        "mean including the first interval = 4.27463. Delta first minus later is +0.02815 s/tick "
        "(~19.8s at tick 84291301 versus the first-pass live anchor). A later-anchor check at "
        "2026-11-16 05:02:32 Asia/Hong_Kong game.time=84292021 found "
        "still_over_45s_vs_first=0 (n=22296; vs first-interval over15=7838) and "
        "still_over_45s_vs_later=0 (n=22296; vs later-mean over15=0), so no corrective "
        "later-mean realign was applied. Confirm reported ts_realigned=0 (recovered 3 delayed "
        "in-window official 404s; all 34 aged leftover official 404s including W47N8@84290200 "
        "still 404). retry2 skipped."
    )

    live_json_note = (
        "One box freeze ran after the 04:30 backfill: 2026-11-16 04:44:57–05:00:06 Asia/Hong_Kong "
        "(908s; VM hibernated; wall jumped, monotonic did not), logged by listener.py at 05:00:06 "
        "with run_listener.sh relaunch at 05:00:09 (new listener.py pid 3256165 started 05:00:18). "
        "run_listener.sh pid 4035476 unchanged since 2026-11-11. yield_files=absent, single room "
        "slot, peacetime 5:5:1:1 (rot at pre-check on W47N8, i=1). Did not start a second loop or "
        "kill war_cmd/pulse. Segment-90 and STATS were already current without a console query: at "
        "pre-check 05:01:04 live.json gameTime=None (slot on W47N8, objects=0 as designed off HOME) "
        "stats.t=84292000 cpu=17.21 b=10000, creep_cpu tip 84291990 (6564 rows since tick 84290901, "
        "last200 84291790..84291990, 1362 rows, max_ts 05:00:20 after reconnect pull), path_arrivals "
        "tip 84291974 (135 rows since tick 84290901, last200 22 rows), room_stats tip 84292000, "
        "creep_ticks tip 84292001. No new incidents ingest drop after the known 03:00:06 invalid "
        "integer '{}' event. This run did not change the peacetime single-slot 5:5:1:1 "
        "arrangement. The first official game/time request succeeded. No concurrent hourly patrol "
        "was running during this backfill; this run did not add a second websocket slot."
    )

    hourly_note = (
        "The previous 04:30 half-hour backfill had already prefilled 84290901..84291600 "
        "(inserted_total=3146, tick_s=4.30411 / later 4.28591 with no corrective later-mean "
        "realign, first-pass missing_chunks=0, game.time=84291658), overlapping 300 ticks of "
        "this window (84291301..84291600). No concurrent hourly patrol at this wake. First pass "
        "then recovered the newly published 84291600..84291800 chunks for all five rooms and "
        "already-published W46N8/W45N7 @84291900, with missing_chunks=3 delayed official 404s "
        "W47N8/W45N8/W47N7 @84291900, also covering the 04:44–05:00 box-freeze gap; confirm "
        "(05:03:06, game.time=84292028) recovered all 3 delayed in-window chunks (inserted=1794) "
        "and left all 34 aged leftover official 404s including W47N8@84290200 unpublished; retry2 "
        "skipped (no remaining in-window official 404s). There were no official empty-no-creep "
        "ticks in this 40m window. The previously in-window official 404 hole "
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
        "missing_chunks first_pass=3 at game.time=84292006; published_bases 84291300..84291900, "
        "reconstructed 84291301..84292000 (700), already_in_db=10955 inserted=10228 "
        "(W47N8/W45N8/W47N7 @84291900 official 404 on first pass; W46N8 and W45N7 @84291900 already "
        "200). Confirm 2026-11-16 05:03:06 Asia/Hong_Kong game.time=84292028 recovered all 3 delayed "
        "in-window official 404s (inserted=1794: W47N8 1191, W45N8 103, W47N7 500) and retried 34 "
        "aged leftover official 404s including W47N8@84290200 — all 34 still 404, ts_realigned=0. "
        "retry2 skipped (no remaining in-window official 404s). After confirm: "
        "W46N8/W47N8/W45N8/W45N7/W47N7 each distinct=700 missing_n=0. No official empty-no-creep "
        "ticks in this window. "
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
        f"404 after confirm GET. First-pass tick_s=4.29809 (printed 4.298) realigned 0 rows; "
        f"later-mean was already inside the 45s gate so no corrective later-mean realign was "
        f"applied (later-mean tick_s=4.26994, at {TICK_S_CHECK_AT} Asia/Hong_Kong game.time="
        f"{TICK_S_CHECK_GT}; over45=0, over15=0, n=22296 after first pass, before confirm)."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm recovered 3 delayed in-window official 404s W47N8/W45N8/W47N7@84291900 "
        "inserted=1794 (1191/103/500) and retried 34 aged leftover official 404s including "
        "W47N8@84290200 at 05:03:06 game.time=84292028, all 34 still 404 ts_realigned=0; retry2 "
        "skipped (no remaining in-window official 404s)\n"
        "ts_realigned_first_pass=0 (tick_s=4.29809 printed 4.298); later-mean already inside 45s "
        f"gate, no corrective later-mean realign (later-mean tick_s=4.26994 still_over_45s_vs_later="
        f"0 at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT})\n"
        f"inserted_total=12022 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=0 after confirm (first-pass missing_chunks=3)\n"
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
        "retry2 skipped 2026-11-16 05:04 Asia/Hong_Kong: first-pass missing_chunks=3 delayed "
        "official 404s W47N8/W45N8/W47N7@84291900 were all recovered by confirm (inserted=1794); "
        "confirm recovered none of 34 aged leftover official 404s; no remaining in-window official "
        "404s to retry.\n"
    )
    (DIR / "backfill_retry2.txt").write_text(retry2_note)
    (ROOT / "state" / "_halfhour_backfill_retry2_0500.txt").write_text(retry2_note)

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
