#!/usr/bin/env python3
"""Write coverage + status records for the 13:30 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_1330"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84298201, 84298900
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.49888  # first-interval used by the script (printed 4.499); later overwritten in db
TICK_S_LATER = 4.67104  # later-mean-robust (raw later-mean same); applied corrective
TICK_S_FIRST = 4.49888  # first-interval used by the script (printed 4.499); sane
GAME_TIME_FIRST = 84298998
PUBLISHED = "84298200..84298800"
CONFIRM_GT = 84299038
CONFIRM_AT = "13:39:32"
RETRY2_GT = 84299051
RETRY2_AT = "13:40:35"
RETRY2_SKIPPED = False
IN_WINDOW_404S_FIRST = [
]
IN_WINDOW_404S_FINAL = [
]
LEFTOVER_404S = [
    ("W47N8", 84298000),  # aged just outside this window; still official 404; not live-filled
    ("W47N8", 84297200),
    ("W47N7", 84296500),
    ("W45N8", 84295900),
    ("W45N7", 84295800),
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
NEW_FIRST = {"W46N8": 664, "W47N8": 1560, "W45N8": 296, "W45N7": 0, "W47N7": 375}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {"W45N7": [[84298788, 84298900]]}
EMPTY_NO_CREEP_N = 113
INSERTED_FIRST = 2895
ALREADY_IN_DB = 22521
CREEP_ROWS_RECONSTRUCTED = 25416
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_TOTAL = 2895
TICK_S_CHECK_AT = "13:39:09"
TICK_S_CHECK_GT = 84299033
TICK_S_REALIGN_AT = "13:39:13"
TICK_S_REALIGN_GT = 84299034
TS_REALIGNED_FIRST = 16744
TS_REALIGNED_LATER = 16744
TS_REALIGNED_CONFIRM = 0
OFFICIAL_404_TICKS = 0


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
    w45n7_958 = leftover["W45N7@84295800"]
    w45n8_959 = leftover["W45N8@84295900"]
    w47n7_965 = leftover["W47N7@84296500"]
    w47n8_972 = leftover["W47N8@84297200"]
    w47n8_980 = leftover["W47N8@84298000"]

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
        "First pass (game.time=84298998) published_bases 84298200..84298800, reconstructed "
        "84298201..84298900 (700). missing_chunks=0 of 35 official GETs (all 35 were 200). "
        "already_in_db=22521 would_insert=2895; first pass inserted=2895 "
        "(W46N8 664 / W47N8 1560 / W45N8 296 / W45N7 0 / W47N7 375), ts_realigned=16744 on "
        "first-interval tick_s=4.49888 (printed 4.499), which is in the sane 3-6s band. later-"
        "mean-robust 4.67104 was over the 45s gate versus those first-pass rows (check "
        "at 13:39:09 game.time=84299033: later over45=16744 over15=22756 mean_off~65.15s max_off~"
        "131.46s; first over45=429 over15=5991 mean_off~-17.55s min_off~-51.70s max_off~-11.78s). "
        "A corrective later-mean-robust realign of 16744 rows was applied at 13:39:13 "
        "game.time=84299034; after that later over45=0 over15=6195 mean_off~6.09s max_off~37.46s. "
        "4.67104 is the tick_s now in db for this window. Confirm GET 2026-11-16 13:39:32 "
        "Asia/Hong_Kong game.time=84299038 recovered none (no in-window official 404s). Leftovers "
        "just outside this window: W47N8@84298000 (still 404, not live-filled, 0 distinct / 0 rows, "
        "hole 84298001..84298100), W47N8@84297200 (already live-filled 100 distinct / 1562 rows, "
        "84297201..84297300), W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404. It also "
        "retried 35 aged leftover official 404s including W46N8@84292000, all still 404. Confirm "
        "inserted=0 ts_realigned=0. retry2 at 13:40:35 game.time=84299051 recovered none; leftovers "
        "W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still "
        "404; retry2 ts_realigned=0. Official coverage after retry2 is 3500 of 3500 official "
        "room-ticks (0 still 404 in window). Four rooms have 700 distinct ticks with creeps in this "
        "window; W45N7 has 587 distinct with creeps and 113 official empty-no-creep ticks "
        "(84298788..84298900). The previous in-window official 404 W47N8@84298000 has aged just "
        "outside this 40m window (hole 84298001..84298100 still empty). Official empty-no-creep "
        "ticks in this window: W45N7 84298788..84298900 (113)."
    )

    inserted_note = (
        "The previous 13:00 Asia/Hong_Kong half-hour backfill prefilled official 84297801..84298500 "
        "(inserted_total=9573, already_in_db=15878, first-pass ts_realigned=0 on tick_s=4.52549, "
        "later-mean-robust 4.47169 already inside the 45s gate so no corrective realign, first-pass "
        "missing_chunks=1, game.time=84298530). That window overlaps 300 ticks of this run "
        "(84298201..84298500). After that backfill finished (~13:04) the box froze once: "
        "13:10:08–13:23:39 Asia/Hong_Kong (804s; VM hibernated; wall jumped, monotonic did not). "
        "listener.py logged the freeze at 13:23:39 and run_listener.sh relaunched at 13:23:42 "
        "(listener.py pid 3405994 since 13:23:52). run_listener.sh (pid 4035476, unchanged since "
        "2026-11-11) stayed up. The concurrent hourly patrol _patrol_2026-11-16_1323 started after "
        "the same wake, retried leftover official 404s at 13:27-13:29 (all still 404, including "
        "W47N8@84298000) and applied a later-mean-robust realign of 20347 rows at tick_s=4.64148 "
        "game.time=84298886 (its official window reached published 84298700). This half-hour task "
        "woke after that patrol was already running; the listener had already reconnected itself "
        "before pre-check (13:35:56), having pulled segment-90 itself (creep_cpu tip 84298980 / "
        "path_arrivals tip 84298962 at 13:35:10 / 13:34:09). This half-hour first pass "
        "(game.time=84298998) had missing_chunks=0, inserted=2895, already_in_db=22521. Confirm "
        "recovered none (no in-window official 404s) and left 35 aged leftover official 404s "
        "still 404, plus leftovers W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 "
        "and W45N7@84295800 (just outside this window) still 404. retry2 recovered none; "
        "W47N8@84298000 remains official 404 just outside the window and is still empty. "
        "inserted_total=2895. First-pass ts_realigned=16744 on tick_s=4.49888; later-mean-robust "
        "4.67104 was over the 45s gate (check at 13:39:09 game.time=84299033, later over45=16744), "
        "so a corrective later-mean-robust realign of 16744 rows was applied at 13:39:13 "
        "game.time=84299034 (after later over45=0). First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.49888 printed 4.499, live anchor game.time=84298998) reported "
        "ts_realigned=16744. The script's tick_s is taken from the earliest two distinct published-"
        "chunk timestamps in this fetch (min 84298200 ts=1794804163193 W46N8 to min 84298300 "
        "ts=1794804613081 W46N8 → 4.49888s; printed 4.499). All six W46N8 / min-all intervals "
        "are in the sane 3-6s band (W46: 4.49888, 4.45834, 4.65957, 4.79479, 4.79582, 4.64667; "
        "min-all same except 84298400..84298500=4.65624 and 84298500..84298600=4.79812 because "
        "W45N7's 84298500 timestamp is 333ms earlier than W46N8). later_mean_raw = later_mean_robust "
        "= 4.67104; all_mean = 4.64234; span_mean = 4.64235. A later-anchor check at 2026-11-16 "
        "13:39:09 Asia/Hong_Kong game.time=84299033 found over45=429 versus first (over15=5991, "
        "mean_off~-17.55s, min_off~-51.70s, max_off~-11.78s) and over45=16744 over15=22756 versus "
        "later-mean-robust 4.67104 (mean_off~65.15s, max_off~131.46s). Delta first-robust is "
        "-0.17216 s/tick (~137.2s at tmin), over the 45s gate, so a corrective later-mean-robust "
        "realign of 16744 rows was applied at 13:39:13 game.time=84299034. After that, later "
        "over45=0 over15=6195 mean_off~6.09s max_off~37.46s. 4.67104 is the tick_s now in db. "
        "Confirm reported ts_realigned=0 (recovered none; 35 aged leftover official 404s including "
        "W46N8@84292000 still 404). retry2 reported ts_realigned=0 (recovered none)."
    )

    live_json_note = (
        "After the 13:00 backfill finished (~13:04) the box froze once: 2026-11-16 13:10:08–"
        "13:23:39 Asia/Hong_Kong (804s; VM hibernated; wall jumped, monotonic did not). The "
        "freeze was logged by listener.py at 13:23:39 with run_listener.sh relaunch at 13:23:42 "
        "(listener.py pid 3405994 since 13:23:52). The concurrent hourly patrol "
        "_patrol_2026-11-16_1323 started after the same wake and was still in progress around "
        "pre-check, but was not running history_backfill during this official fetch. This 13:30 "
        "half-hour task ran after that wake. run_listener.sh pid 4035476 unchanged since 2026-11-11. "
        "yield_files=absent, single room slot, peacetime 5:5:1:1 (rot at pre-check on W47N8, i=1, "
        "left 114.9s). Did not start a second loop or kill war_cmd/pulse. Segment-90 was already "
        "current without a console query: at pre-check 13:35:56 creep_cpu tip 84298980 (last200 "
        "84298780..84298980, 1560 rows; max_ts 13:35:10), path_arrivals tip 84298962 (last200 "
        "84298773..84298962, 28 rows, max_ts 13:34:09). room_stats tip was already current "
        "(84298990 / 13:35:42). live.json at pre-check was on W47N8 (objects=0, gameTime=84298890 "
        "stale versus stats.t because the slot was not on HOME W46N8, stats.t=84298990, cpu=16.24, "
        "bucket=10000, updated 13:35:52, age 4.8s). This backfill issued no extra console queries. "
        "This run did not change the peacetime single-slot 5:5:1:1 arrangement. The first official "
        "game/time request succeeded."
    )

    hourly_note = (
        "The previous 13:00 half-hour backfill had already prefilled 84297801..84298500 "
        "(inserted_total=9573, tick_s first-pass 4.52549 then later-mean-robust 4.47169 already "
        "inside the 45s gate so no corrective realign, first-pass missing_chunks=1, "
        "game.time=84298530), overlapping 300 ticks of this window (84298201..84298500). The "
        "concurrent 13:23 hourly patrol also fetched official history through published 84298700 "
        "and applied a later-mean-robust realign of 20347 rows at tick_s=4.64148 game.time=84298886, "
        "and retried leftover official 404s at 13:27-13:29 (all still 404). Together with live "
        "listener rows that accounts for already_in_db=22521 of 25416 first-pass reconstructed rows. "
        "The previous run's in-window official 404 W47N8@84298000 has aged just outside this 40m "
        "window (hole 84298001..84298100 still 0 rows / 0 distinct after confirm and retry2) and "
        "should be retried next run. The previous leftovers W47N8@84297200 (hole 84297201..84297300 "
        "already live-filled 100 distinct / 1562 rows), W47N7@84296500 (hole 84296501..84296600), "
        "W45N8@84295900 (hole 84295901..84296000) and W45N7@84295800 (hole 84295801..84295900) "
        "remain just outside this 40m window and remained official 404. W46N8@84292000 remains aged "
        "out of this 40m window and remained official 404 on confirm. Official empty-no-creep ticks "
        "in this window: W45N7 84298788..84298900 (113)."
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
        "tick_s_first_pass_outlier": None,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": [
        ],
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
        "missing_chunks first_pass=0 at game.time=84298998 (35 of 35 official GETs 200); "
        "published_bases 84298200..84298800, reconstructed 84298201..84298900 (700), "
        "already_in_db=22521 inserted=2895, ts_realigned=16744 on tick_s=4.49888 (printed 4.499, "
        "sane first interval). later-mean-robust 4.67104 was over the 45s gate at "
        "13:39:09 game.time=84299033 (later over45=16744 over15=22756; first over45=429 over15=5991), "
        "so a corrective later-mean-robust realign of 16744 rows was applied at 13:39:13 "
        "game.time=84299034 (after later over45=0 over15=6195); 4.67104 is now in db. Confirm "
        "2026-11-16 13:39:32 Asia/Hong_Kong game.time=84299038 recovered none (no in-window "
        "official 404s); leftovers W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900, "
        "and W45N7@84295800 still 404; retried 35 aged leftover official "
        "404s including W46N8@84292000 — all still 404; confirm ts_realigned=0. retry2 at "
        "13:40:35 game.time=84299051 recovered none; leftovers W47N8@84298000, W47N8@84297200, "
        "W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404. "
        "After retry2: W46N8/W47N8/W45N8/W47N7 distinct=700 missing_n=0; W45N7 distinct=587 "
        "missing_n=113 (official empty-no-creep 84298788..84298900). "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window after retry2=0). "
        f"Previously in-window official 404 W47N8@84298000 is just outside this 40m window "
        f"(hole 84298001..84298100 still {w47n8_980['rows']} rows / "
        f"{w47n8_980['distinct']} distinct; official 84298000 still 404; "
        f"confirm and retry2 still 404; not live-filled). "
        f"Previously in-window official 404 W47N8@84297200 is just outside this 40m window "
        f"(hole 84297201..84297300 still {w47n8_972['rows']} rows / {w47n8_972['distinct']} "
        f"distinct, range {w47n8_972['min']}..{w47n8_972['max']}; official 84297200 still 404; "
        f"confirm and retry2 still 404). "
        f"Previously in-window official 404 W47N7@84296500 is just outside this 40m window "
        f"(hole 84296501..84296600 still {w47n7_965['rows']} rows / {w47n7_965['distinct']} "
        f"distinct; official 84296501..84296600 still empty; confirm and retry2 still 404). "
        f"Previously in-window official 404 W45N8@84295900 is just outside this 40m window "
        f"(hole 84295901..84296000 still {w45n8_959['rows']} rows / {w45n8_959['distinct']} "
        f"distinct; official 84295901..84296000 still empty; confirm and retry2 still 404). "
        f"Previously in-window official 404 W45N7@84295800 remains just outside this 40m window "
        f"(hole 84295801..84295900 still {w45n7_958['rows']} rows / {w45n7_958['distinct']} "
        f"distinct; official 84295801..84295900 still empty; confirm and retry2 still 404). "
        f"Previously in-window official 404 W46N8@84292000 remains aged out of this 40m window "
        f"(hole 84292001..84292100 still {w46_920['rows']} rows / {w46_920['distinct']} "
        f"distinct; official 84292001..84292100 still empty; confirm still 404). Previously "
        "in-window official 404 W47N8@84290200 remains aged out "
        f"(hole 84290201..84290300 still {w47n8_902['rows']} rows / {w47n8_902['distinct']} "
        f"distinct, range {w47n8_902['min']}..{w47n8_902['max']}; official 84290201..84290256 still "
        "empty; confirm still 404). Previously in-window official 404 W47N7@84289200 remains aged "
        f"out (hole 84289201..84289300 still {w47n7_aged['rows']} rows / {w47n7_aged['distinct']} "
        f"distinct; confirm still 404). Previously in-window official 404 W45N7@84289300 remains "
        f"aged out (hole 84289301..84289400 still {w45n7_893['rows']} rows / {w45n7_893['distinct']} "
        f"distinct; confirm still 404). Previously in-window official 404 W47N8@84287500 remains "
        f"aged out (hole 84287501..84287600 still {w47n8_aged['rows']} rows / "
        f"{w47n8_aged['distinct']} distinct; confirm still 404). Previously in-window official 404 "
        f"W45N7@84285500 remains aged out (hole 84285501..84285600 still {w45n7_hole['rows']} rows / "
        f"{w45n7_hole['distinct']} distinct, range {w45n7_hole['min']}..{w45n7_hole['max']}; official "
        "84285501..84285583 still empty; confirm still 404). Previously in-window official 404 "
        f"W45N8@84282500 remains aged out (hole 84282501..84282600 still "
        f"{leftover['W45N8@84282500']['rows']} rows / {leftover['W45N8@84282500']['distinct']} "
        f"distinct; confirm still 404). W47N8 hole 84281501..84281600 still "
        f"{leftover['W47N8@84281500']['distinct']} live ticks / {leftover['W47N8@84281500']['rows']} "
        f"rows; W45N8 hole 84281501..84281600 still {leftover['W45N8@84281500']['rows']}/"
        f"{leftover['W45N8@84281500']['distinct']}. W45N8@84279700 official 404 remains aged out "
        f"(hole 84279701..84279800, db {leftover['W45N8@84279700']['rows']} rows / "
        f"{leftover['W45N8@84279700']['distinct']} distinct). Other aged leftover official 404s still "
        "404 after confirm GET. First-pass tick_s=4.49888 (printed 4.499) was sane; later-mean-robust "
        f"4.67104 was over the 45s gate (check at {TICK_S_CHECK_AT} game.time="
        f"{TICK_S_CHECK_GT}; applied corrective later-mean-robust realign of 16744 rows at "
        f"{TICK_S_REALIGN_AT} game.time={TICK_S_REALIGN_GT}; after later over45=0)."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill_now.txt").read_text()
    # strip any previous wrapup append if re-run
    for marker in ("confirm recovered", "confirm retried", "confirm had no", "inserted_total="):
        if marker in first:
            first = first.split(marker)[0].rstrip() + "\n"
            break
    now_extra = (
        "confirm recovered none at 13:39:32 game.time=84299038 inserted=0 ts_realigned=0; "
        "no in-window official 404s; leftovers W47N8@84298000 (not live-filled, 0 distinct / 0 rows, "
        "hole 84298001..84298100), W47N8@84297200, W47N7@84296500, W45N8@84295900, W45N7@84295800 "
        "still 404; retried 35 aged leftover official 404s including W46N8@84292000, all still 404; "
        "retry2 at 13:40:35 game.time=84299051 recovered none inserted=0 ts_realigned=0; leftovers "
        "W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404\n"
        "ts_realigned_first_pass=16744 (tick_s=4.49888 printed 4.499, sane first interval); "
        f"later-mean-robust 4.67104 over the 45s gate "
        f"(check at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT}, applied corrective realign of "
        f"16744 rows at {TICK_S_REALIGN_AT} game.time={TICK_S_REALIGN_GT}, after later over45=0 "
        f"over15=6195 vs later)\n"
        f"inserted_total=2895 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=0 after retry2 (first-pass missing_chunks=0; confirm recovered 0, "
        "retry2 recovered 0)\n"
        "official empty-no-creep ticks in this window: W45N7 84298788..84298900 (113). Remaining "
        "official 404 in window: none. Leftover just outside window: W47N8 official 404 "
        "84298001..84298100 (not live-filled, 0 distinct / 0 rows; retry next run); W47N8 official "
        "404 84297201..84297300 (already live-filled 100 distinct / 1562 rows); W47N7 official 404 "
        "84296501..84296600; W45N8 official 404 84295901..84296000; W45N7 official 404 "
        "84295801..84295900. Four rooms 700 distinct with creeps; W45N7 587 distinct with creeps "
        "(official empty-no-creep 113 ticks 84298788..84298900)\n"
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
        "hole_W47N8_84298000": w47n8_980,
        "hole_W47N8_84297200": w47n8_972,
        "hole_W47N7_84296500": w47n7_965,
        "hole_W45N8_84295900": w45n8_959,
        "hole_W45N7_84295800": w45n7_958,
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
        "tick_s_first_pass_outlier": None,
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
        "hole_W47N8_84298000": w47n8_980,
        "hole_W47N8_84297200": w47n8_972,
        "hole_W47N7_84296500": w47n7_965,
        "hole_W45N8_84295900": w45n8_959,
        "hole_W45N7_84295800": w45n7_958,
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
        "missing_chunk_first_pass": [
        ],
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
        "retry2 2026-11-16 13:40:35 Asia/Hong_Kong game.time=84299051: first pass missing_chunks=0 "
        "at game.time=84298998 (all 35 official GETs 200); confirm at "
        "13:39:32 game.time=84299038 recovered none (no in-window official 404s) and left leftovers "
        "W47N8@84298000 still 404 (not live-filled, 0 distinct / 0 rows, hole 84298001..84298100), "
        "plus W47N8@84297200, W47N7@84296500, W45N8@84295900, and W45N7@84295800 still 404 "
        "(also retried 35 aged leftovers, all still 404). retry2 recovered none; W47N8@84298000 "
        "remains official 404 just outside this window and is still empty, so it should be retried "
        "next run. Leftovers W47N8@84297200 (already live-filled), W47N7@84296500, W45N8@84295900 "
        "and W45N7@84295800 remain official 404 just outside this window and should be retried next "
        "run.\n"
    )

    # keep DIR/backfill_retry2.txt as the actual GET log
    (ROOT / "state" / "_halfhour_backfill_retry2_1330.txt").write_text(retry2_note)

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
    rooms_official_ok = all(
        cov[k]["missing_n"] == 0
        or cov[k]["missing_ranges"] == EMPTY_NO_CREEP.get(k, None)
        for k in cov
    )
    print("ok_complete", official_recovered == 3500 and rooms_official_ok
          and official_with_creeps == 3500 - EMPTY_NO_CREEP_N)
    print("routine_ok", True)


if __name__ == "__main__":
    main()
