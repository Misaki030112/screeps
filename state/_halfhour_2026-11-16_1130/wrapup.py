#!/usr/bin/env python3
"""Write coverage + status records for the 11:30 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_1130"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84296601, 84297300
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.42840  # later-mean-robust; applied correctly and left in db
TICK_S_LATER = 4.42840  # later-mean-robust (raw later-mean same); applied
TICK_S_FIRST = 4.29391  # first-interval used by the script (printed 4.294); sane but later applied
GAME_TIME_FIRST = 84297303
PUBLISHED = "84296600..84297200"
CONFIRM_GT = 84297323
CONFIRM_AT = "11:29:14"
RETRY2_GT = 84297338
RETRY2_AT = "11:30:21"
RETRY2_SKIPPED = False
IN_WINDOW_404S_FIRST = [
    ("W47N8", 84297200),
    ("W45N8", 84297200),
    ("W47N7", 84297200),
]
IN_WINDOW_404S_FINAL = [
    ("W47N8", 84297200),  # still official 404; live already filled all 100 ticks
]
LEFTOVER_404S = [
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
NEW_FIRST = {"W46N8": 1120, "W47N8": 1458, "W45N8": 588, "W45N7": 761, "W47N7": 511}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 430, "W45N7": 0, "W47N7": 0}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 484}
EMPTY_NO_CREEP = {}
EMPTY_NO_CREEP_N = 0
INSERTED_FIRST = 4438
ALREADY_IN_DB = 21209
CREEP_ROWS_RECONSTRUCTED = 25647
INSERTED_CONFIRM = 430
INSERTED_RETRY2 = 484
INSERTED_TOTAL = 5352
TICK_S_CHECK_AT = "11:28:57"
TICK_S_CHECK_GT = 84297319
TICK_S_REALIGN_AT = "11:29:01"
TICK_S_REALIGN_GT = 84297319
TS_REALIGNED_FIRST = 248
TS_REALIGNED_LATER = 10078
TS_REALIGNED_CONFIRM = 0
OFFICIAL_404_TICKS = 100  # W47N8@84297200 still official 404 after retry2; live already filled all 100 ticks


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

    official_ticks = {room: WINDOW_N for room in ROOMS}
    official_ticks["W47N8"] = 600  # W47N8@84297200 still official 404; live already filled 100 ticks
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
        "First pass (game.time=84297303) published_bases 84296600..84297200, reconstructed "
        "84296601..84297300 (700). missing_chunks=3 of 35 official GETs: W47N8@84297200, "
        "W45N8@84297200, W47N7@84297200 (the other 32 were 200). already_in_db=21209 "
        "would_insert=4438; first pass inserted=4438 (W46N8 1120 / W47N8 1458 / W45N8 588 / "
        "W45N7 761 / W47N7 511), ts_realigned=248 on first-interval tick_s=4.29391 (printed 4.294), "
        "which is in the sane 3-6s band. later-mean-robust 4.42840 was over the 45s gate versus "
        "those first-pass rows (check at 11:28:57 game.time=84297319: later over45=11138 over15="
        "22212 mean_off~37.37s max_off~82.25s; first over45=28 over15=10032 mean_off~-13.09s "
        "min_off~-45.81s). A corrective later-mean-robust realign of 10078 rows was applied at "
        "11:29:01 game.time=84297319; after over45=0 over15=11489 mean_off~13.36s max_off~44.99s "
        "vs later, and was kept (not reverted). Confirm GET 2026-11-16 11:29:14 Asia/Hong_Kong "
        "game.time=84297323 recovered W45N8@84297200 (100 ticks, ts=1794799736673, inserted=430). "
        "In-window W47N8@84297200 and W47N7@84297200 still 404 at confirm; leftovers W47N7@"
        "84296500, W45N8@84295900 and W45N7@84295800 (just outside this window) still 404. It "
        "also retried 35 aged leftover official 404s including W46N8@84292000, all still 404. "
        "Confirm inserted=430 ts_realigned=0. retry2 at 11:30:21 game.time=84297338 recovered "
        "W47N7@84297200 (100 ticks, ts=1794799780943, inserted=484); W45N8@84297200 already "
        "present (inserted=0); W47N8@84297200 still official 404 (but the live listener already "
        "had all 100 ticks, 1562 rows, range 84297201..84297300). Leftovers W47N7@84296500, "
        "W45N8@84295900 and W45N7@84295800 still 404; retry2 ts_realigned=0. Official coverage "
        "after retry2 is 3400 of 3500 official room-ticks (100 still 404: W47N8@84297200). All "
        "five rooms have 700 distinct ticks with creeps in this window (W47N8's last 100 ticks "
        "came from the live listener). The previous in-window official 404 W47N7@84296500 has "
        "aged just outside this 40m window (hole 84296501..84296600). No official empty-no-creep "
        "ticks in the recovered portion."
    )

    inserted_note = (
        "The previous 11:00 Asia/Hong_Kong half-hour backfill prefilled official 84296301..84297000 "
        "(inserted_total=13951, already_in_db=12903, first-pass ts_realigned=7707 on tick_s=4.37624, "
        "later-mean-robust 4.27102 applied a corrective realign of 8218 rows, first-pass "
        "missing_chunks=1, game.time=84297031). That window overlaps 400 ticks of this run "
        "(84296601..84297000). No new box freeze after the 11:00 backfill; the last freeze was "
        "10:48:46–11:06:00 Asia/Hong_Kong (1023s; VM hibernated; wall jumped, monotonic did not) "
        "with listener.py logged freeze at 11:06:00 and run_listener.sh relaunch at 11:06:03 "
        "(listener.py pid 3361024 since 11:06:12). run_listener.sh (pid 4035476, unchanged since "
        "2026-11-11) stayed up. The listener was already healthy at pre-check (11:27:30), having "
        "pulled segment-90 itself (creep_cpu tip 84297290 / path_arrivals tip 84297289 at "
        "11:26:49). This half-hour first pass (game.time=84297303) had missing_chunks=3, "
        "inserted=4438, already_in_db=21209. Confirm recovered 1 of 3 in-window official 404s "
        "(W45N8@84297200, inserted=430) and left 35 aged leftover official 404s still 404, plus "
        "leftovers W47N7@84296500, W45N8@84295900 and W45N7@84295800 (just outside this window) "
        "still 404. retry2 recovered W47N7@84297200 (inserted=484); W47N8@84297200 remains official "
        "404 in window but is already fully filled by the live listener (100 distinct / 1562 rows). "
        "inserted_total=5352. First-pass ts_realigned=248 on tick_s=4.29391; later-mean-robust "
        "4.42840 applied a corrective realign of 10078 rows at game.time=84297319 (after over45=0). "
        "First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.29391 printed 4.294, live anchor game.time=84297303) reported "
        "ts_realigned=248. The script's tick_s is taken from the earliest two distinct published-"
        "chunk timestamps in this fetch (min 84296600 ts=1794797050233 W46N8 to min 84296700 "
        "ts=1794797479624 W46N8 → 4.29391s; printed 4.294). All six W46N8 / min-all intervals "
        "are in the sane 3-6s band (4.29391, 4.20001, 4.44003, 4.48886, 4.51886, 4.49424). "
        "later_mean_raw = later_mean_robust = 4.42840; all_mean = 4.40599; span_mean = 4.40599. A "
        "later-anchor check at 2026-11-16 11:28:57 Asia/Hong_Kong game.time=84297319 found over45=28 "
        "versus first (over15=10032, mean_off~-13.09s, min_off~-45.81s) and over45=11138 over15="
        "22212 versus later-mean-robust 4.42840 (mean_off~37.37s, max_off~82.25s). Delta first-"
        "robust is -0.13449 s/tick (~94.4s at tmin), over the 45s gate, so a corrective later-mean-"
        "robust realign of 10078 rows was applied at 11:29:01 game.time=84297319; after over45=0 "
        "over15=11489 mean_off~13.36s max_off~44.99s vs later, and was kept. 4.42840 is the tick_s "
        "now in db. Confirm reported ts_realigned=0 (recovered W45N8@84297200, inserted=430; 35 aged "
        "leftover official 404s including W46N8@84292000 still 404). retry2 reported ts_realigned=0 "
        "(recovered W47N7@84297200, inserted=484)."
    )

    live_json_note = (
        "No new box freeze after the 11:00 backfill. The last freeze was 2026-11-16 10:48:46–"
        "11:06:00 Asia/Hong_Kong (1023s; VM hibernated; wall jumped, monotonic did not), logged by "
        "listener.py at 11:06:00 with run_listener.sh relaunch at 11:06:03 (listener.py pid "
        "3361024 since 11:06:12). run_listener.sh pid 4035476 unchanged since 2026-11-11. "
        "yield_files=absent, single room slot, peacetime 5:5:1:1 (rot at pre-check on W47N8, i=1, "
        "left 99.9s). Did not start a second loop or kill war_cmd/pulse. Segment-90 was already "
        "current without a console query: at pre-check 11:27:30 creep_cpu tip 84297290 (last200 "
        "84297090..84297290, 1590 rows; max_ts 11:26:49), path_arrivals tip 84297289 (last200 "
        "84297098..84297289, 27 rows, max_ts 11:26:49). room_stats tip was already current "
        "(84297290 / 11:26:46). live.json at pre-check was on W47N8 (objects=0, gameTime stale "
        "because the slot was not HOME, stats.t=84297290, cpu=18.09, bucket=10000, updated "
        "11:27:26, age 4.1s). No concurrent hourly patrol was running during this backfill, and "
        "this backfill issued no extra console queries. This run did not change the peacetime "
        "single-slot 5:5:1:1 arrangement. The first official game/time request succeeded."
    )

    hourly_note = (
        "The previous 11:00 half-hour backfill had already prefilled 84296301..84297000 "
        "(inserted_total=13951, tick_s first-pass 4.37624 then later-mean-robust 4.27102 applied a "
        "corrective realign of 8218 rows, first-pass missing_chunks=1, game.time=84297031), "
        "overlapping 400 ticks of this window (84296601..84297000), which together with live "
        "listener rows accounts for already_in_db=21209 of 25647 first-pass reconstructed rows. "
        "The previous run's in-window official 404 W47N7@84296500 has aged just outside this 40m "
        "window (hole 84296501..84296600) and remained official 404 on confirm and retry2. The "
        "previous leftovers W45N8@84295900 (hole 84295901..84296000) and W45N7@84295800 (hole "
        "84295801..84295900) remain just outside this 40m window and remained official 404. "
        "W46N8@84292000 remains aged out of this 40m window and remained official 404 on confirm. "
        "No official empty-no-creep ticks in the recovered portion of this window."
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
        "missing_chunks": 3,
        "missing_chunk_list": ["W47N8@84297200"],
        "missing_chunk_first_pass": [
            "W47N8@84297200",
            "W45N8@84297200",
            "W47N7@84297200",
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
        "missing_chunks first_pass=3 at game.time=84297303 (32 of 35 official GETs 200; 404: "
        "W47N8@84297200, W45N8@84297200, W47N7@84297200); "
        "published_bases 84296600..84297200, reconstructed 84296601..84297300 (700), "
        "already_in_db=21209 inserted=4438, ts_realigned=248 on tick_s=4.29391 (printed 4.294, "
        "sane first interval). later-mean-robust 4.42840 was over the 45s gate at 11:28:57 "
        "game.time=84297319 (later over45=11138 over15=22212; first over45=28 over15=10032), so a "
        "corrective later-mean-robust realign of 10078 rows was applied at 11:29:01 "
        "game.time=84297319 (after over45=0 over15=11489 vs later) and kept. Confirm 2026-11-16 "
        "11:29:14 Asia/Hong_Kong game.time=84297323 recovered W45N8@84297200 (inserted=430); "
        "W47N8@84297200 and W47N7@84297200 still 404; leftovers W47N7@84296500, W45N8@84295900, "
        "and W45N7@84295800 still 404; retried 35 aged leftover official "
        "404s including W46N8@84292000 — all still 404; confirm ts_realigned=0. retry2 at "
        "11:30:21 game.time=84297338 recovered W47N7@84297200 (inserted=484); W47N8@84297200 still "
        "official 404 but already live-filled (100 distinct / 1562 rows, 84297201..84297300). "
        "After retry2: all five rooms distinct=700 missing_n=0. "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window after retry2=1 / 100 ticks, "
        f"W47N8@84297200 live-filled). "
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
        "404 after confirm GET. First-pass tick_s=4.29391 (printed 4.294) was sane; later-mean-robust "
        f"4.42840 was applied (check at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT}; "
        f"realign at {TICK_S_REALIGN_AT} game.time={TICK_S_REALIGN_GT}; after over45=0)."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill_now.txt").read_text()
    # strip any previous wrapup append if re-run
    for marker in ("confirm recovered", "confirm retried", "confirm had no", "inserted_total="):
        if marker in first:
            first = first.split(marker)[0].rstrip() + "\n"
            break
    now_extra = (
        "confirm recovered W45N8@84297200 at 11:29:14 game.time=84297323 inserted=430 ts_realigned=0; "
        "W47N8@84297200 and W47N7@84297200 still 404; leftovers W47N7@84296500, W45N8@84295900, "
        "W45N7@84295800 still 404; retried 35 aged leftover official "
        "404s including W46N8@84292000, all still 404; retry2 at 11:30:21 game.time=84297338 "
        "recovered W47N7@84297200 inserted=484 ts_realigned=0; W47N8@84297200 still official 404 "
        "in window but already live-filled (100 distinct / 1562 rows); leftovers W47N7@84296500, "
        "W45N8@84295900 and W45N7@84295800 still 404\n"
        "ts_realigned_first_pass=248 (tick_s=4.29391 printed 4.294, sane first interval); "
        f"later-mean-robust 4.42840 applied corrective realign of 10078 rows "
        f"(check at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT}, realign at {TICK_S_REALIGN_AT} "
        f"game.time={TICK_S_REALIGN_GT}, after over45=0 over15=11489 vs later)\n"
        f"inserted_total=5352 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=1 after retry2 (first-pass missing_chunks=3; confirm recovered 1, "
        "retry2 recovered 1)\n"
        "official empty-no-creep ticks in this window: none in the recovered portion. Remaining "
        "official 404 in window: W47N8@84297200 (live already filled 84297201..84297300). Leftover "
        "just outside window: W47N7 official 404 84296501..84296600; W45N8 official "
        "404 84295901..84296000; W45N7 official 404 84295801..84295900. "
        "All five rooms 700 distinct with creeps\n"
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
        "missing_chunks": 3,
        "missing_chunk_list": ["W47N8@84297200"],
        "missing_chunk_first_pass": [
            "W47N8@84297200",
            "W45N8@84297200",
            "W47N7@84297200",
        ],
        "unique_after_window": unique_after,
        "empty_no_creep_in_window": False,
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
        "retry2 2026-11-16 11:30:21 Asia/Hong_Kong game.time=84297338: first pass missing_chunks=3 "
        "at game.time=84297303 (W47N8@84297200, W45N8@84297200, W47N7@84297200); confirm at "
        "11:29:14 game.time=84297323 recovered W45N8@84297200 (inserted=430) and left W47N8@"
        "84297200 and W47N7@84297200 still 404, plus leftovers W47N7@84296500, W45N8@84295900, "
        "and W45N7@84295800 still 404 (also retried 35 aged leftovers, all still 404). retry2 "
        "recovered W47N7@84297200 (inserted=484); W47N8@84297200 remains official 404 in window "
        "but is already fully filled by the live listener (100 distinct / 1562 rows) and should "
        "still be retried next run. Leftovers W47N7@84296500, W45N8@84295900 and W45N7@84295800 "
        "remain official 404 just outside this window and should be retried next run.\n"
    )
    # keep DIR/backfill_retry2.txt as the actual GET log
    (ROOT / "state" / "_halfhour_backfill_retry2_1130.txt").write_text(retry2_note)

    print("finished_at", finished_hkt)
    print("unique_after", unique_after)
    print("coverage")
    for room, info in cov.items():
        print(" ", room, info)
    print("official_with_creeps", official_with_creeps, "empty_no_creep", EMPTY_NO_CREEP_N,
          "official_recovered", official_recovered, "expected", expected_official,
          "in_window_404", 1)  # W47N8@84297200 official 404, live-filled
    print("db_tips", tips)
    print("live_after", live_after)
    print("listener", listener_at_finish)
    rooms_official_ok = all(
        cov[k]["missing_n"] == 0
        or cov[k]["missing_ranges"] == EMPTY_NO_CREEP.get(k, None)
        for k in cov
    )
    print("ok_complete", official_recovered == 3500 and rooms_official_ok
          and official_with_creeps == 3500 - EMPTY_NO_CREEP_N)  # expected False: 1 official 404
    print("routine_ok", True)


if __name__ == "__main__":
    main()
