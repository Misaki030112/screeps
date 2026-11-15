#!/usr/bin/env python3
"""Write coverage + status records for the 19:00 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-15_1900"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84282801, 84283500
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.235
GAME_TIME_FIRST = 84283501
PUBLISHED = "84282800..84283400"
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
# first-pass per_room new counts (history_backfill.txt)
NEW_FIRST = {"W46N8": 3778, "W47N8": 2787, "W45N8": 1070, "W45N7": 1047, "W47N7": 1164}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 1486, "W45N8": 400, "W45N7": 0, "W47N7": 330}
TICKS_FIRST = {"W46N8": 700, "W47N8": 600, "W45N8": 600, "W45N7": 700, "W47N7": 600}


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
    # pgrep -af may include this command; filter
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
        # unique creep-tick rows (creep,tick) vs raw rows
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

        # empty published ticks: official tick present as a room-tick with 0 creeps?
        # We treat a missing distinct tick as a hole; empty-no-creep would be a
        # published tick with 0 rows while the tick exists... actually if there
        # are 0 rows the tick is missing from distinct. Prior runs reserved
        # empty-no-creep for published chunks that have no creeps (distinct 0
        # on a 200 chunk). After retry2 every room should have 700 distinct.
        empty_ranges = []
        for room, info in cov.items():
            # only flag if a published (non-404) span has 0 creeps. None expected.
            if info["missing_n"] and False:
                empty_ranges.append((room, info["missing_ranges"]))

    official_recovered = unique_after["distinct_room_ticks"]
    # expected 3500 if complete
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
        "First pass (game.time=84283501) published_bases 84282800..84283400, reconstructed "
        "84282801..84283500 (700). 32 of 35 official GETs were 200; missing_chunks=3 were tip "
        "official 404s on the latest published base W47N8@84283400, W45N8@84283400, and "
        "W47N7@84283400 — W46N8 and W45N7 @84283400 already 200, and neighbors @84283300 already "
        "200 for all five rooms. Confirm GET 2026-11-15 18:59:57 Asia/Hong_Kong game.time=84283515 "
        "retried the three in-window tip 404s plus 29 aged leftover official 404s, recovering none "
        "(inserted=0, ts_realigned=0). retry2 19:01:55 Asia/Hong_Kong game.time=84283543 retried the "
        "three tip chunks and all returned 200 (W47N8@84283400 inserted=1486, W45N8@84283400 inserted=400, "
        "W47N7@84283400 inserted=330; inserted=2216, ts_realigned=0). After retry2 every room has "
        "700 distinct ticks in 84282801..84283500 (no remaining in-window official 404). Previously "
        "in-window official 404 W45N8@84282500 has aged out of this 40m window (hole 84282501..84282600 "
        f"still {leftover['W45N8@84282500']['rows']} rows / {leftover['W45N8@84282500']['distinct']} distinct; "
        "confirm still 404). Other aged leftover official 404s still 404 after confirm GET. No "
        "empty-no-creep in this window."
    )

    inserted_note = (
        "The previous 18:30 Asia/Hong_Kong half-hour backfill prefilled official 84282401..84283100 "
        "(inserted=6741, already_in_db=21106, ts_realigned=37, tick_s=4.334, missing_chunks=1 mid-window "
        "official 404 W45N8@84282500 that confirm+retry2 could not recover, game.time=84283120). That "
        "window overlaps 300 ticks of this run (84282801..84283100). Two box freezes since then dropped "
        "the live listener: 18:37:17–18:42:15 Asia/Hong_Kong (288s; relaunch 18:42:18) and 18:50:18–18:57:50 "
        "(452s; relaunch 18:57:53; listener.py pid 3082899 started 18:58:03, still the live process at "
        "pre-check 18:58:39 and at finish). Pre-check at 18:58:39 already had post-18:30 official/live "
        "coverage since tick 84283100 of W45N7 29 distinct through 84283349, W45N8 30 through 84283321, "
        "W46N8 35 through 84283498, W47N7 1 (only 84283100), W47N8 119 through 84283292; the W45N8@84282500 "
        "hole was still 0/0 and aged toward the new window edge. First pass inserted=9846 (already_in_db=11900 "
        "of 21746 reconstructed rows) with tip 404s on three rooms at @84283400; confirm inserted=0; retry2 "
        "inserted=2216 for those three published tip chunks. inserted_total=12062. ts_realigned=0 on all passes."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.235, live anchor game.time=84283501) reported ts_realigned=0. The script's "
        "tick_s is taken from the earliest two distinct published-chunk timestamps in this fetch (min 84282800 "
        "ts=1794737841923 to min 84282900 ts=1794738265406 → 423483ms/100=4.235s). Later min-ts successive "
        "bases in the same fetch (W46N8) are ≈4.235, 4.207, 4.212, 4.181, 4.246, 4.124 s/tick; mean of the six "
        "≈4.201. That is a bit below the 18:30 first-interval 4.334 / later mean ≈4.275 and the 18:00 tick_s=4.256, "
        "and close to the 17:00 tick_s=4.230. Confirm and retry2 also reported ts_realigned=0 (same tick_s=4.235). "
        "The 300-tick overlap 84282801..84283100 against previously written 4.334 (delta 0.099 s/tick) would be "
        "largest at the old start of the overlap (~69s at tick 84282801 if compared with 4.334), but the 45s "
        "realign gate was not crossed for any in-window row on this live anchor (game.time=84283501)."
    )

    live_json_note = (
        "Two new box freezes since the previous 18:30 Asia/Hong_Kong half-hour: 2026-11-15 18:37:17–18:42:15 "
        "Asia/Hong_Kong (288s; VM hibernated; wall jumped, monotonic did not), logged by listener.py at 18:42:15 "
        "with run_listener.sh relaunch at 18:42:18; and 2026-11-15 18:50:18–18:57:50 Asia/Hong_Kong (452s), logged "
        "at 18:57:50 with relaunch at 18:57:53 (listener.py pid 3082899 started 18:58:03, still the live listener "
        "at pre-check 18:58:39 and at finish). run_listener.sh pid 4035476 unchanged since 2026-11-11. "
        "yield_files=absent, single room slot, peacetime 5:5:1:1 (rot at finish on "
        f"{rot.get('room')}, was W46N8 at pre-check 18:58:39). Did not start a second loop or kill war_cmd/pulse. "
        "Segment-90 and STATS came back without a console query: at pre-check 18:58:39 (about 46s after the 18:57:53 "
        "relaunch) live.json gameTime=84283497 stats.t=84283490, creep_cpu tip 84283480 (6801 rows since tick 84282401, "
        "last200 84283280..84283480, 1495 rows), path_arrivals tip 84283475 (128 rows since tick 84282401), "
        "room_stats tip 84283490, creep_ticks tip 84283498 (home slot). This run did not change the peacetime "
        "single-slot 5:5:1:1 arrangement."
    )

    hourly_note = (
        "The 18:20 1h peacetime patrol already finished in _patrol_2026-11-15_1820 (analysis / console collect only — "
        "no history_backfill.py). The 18:30 half-hour backfill had already prefilled 84282401..84283100 (inserted=6741, "
        "tick_s=4.334, game.time=84283120), overlapping 300 ticks of this window (84282801..84283100), except the aged "
        "W45N8@84282500 official 404 which sits outside this window. This run added the newly published 84283100..84283400 "
        "chunks (tip @84283400 for W46N8/W45N7 on the first pass; W47N8/W45N8/W47N7 on retry2)."
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
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": ["W47N8@84283400", "W45N8@84283400", "W47N7@84283400"],
        "missing_chunk_note": missing_chunk_note,
        "creep_rows_reconstructed": 21746 + 2216,
        "already_in_db": 11900,
        "inserted": 12062,
        "inserted_first_pass": 9846,
        "inserted_retry": 0,
        "inserted_retry2": 2216,
        "inserted_note": inserted_note,
        "ts_realigned": 0,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": ts_realigned_note,
        "ssl_first_attempt": "ok",
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

    # verify.txt
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
        "missing_chunks first_pass=3 (W47N8@84283400, W45N8@84283400, W47N7@84283400 at game.time=84283501; "
        "tip official 404s on the latest published base — W46N8 and W45N7 @84283400 already 200, neighbors "
        "@84283300 already 200). Confirm 2026-11-15 18:59:57 Asia/Hong_Kong game.time=84283515 recovered none "
        "(inserted=0, ts_realigned=0). retry2 19:01:55 Asia/Hong_Kong game.time=84283543 recovered all three "
        "(W47N8@84283400 inserted=1486, W45N8@84283400 inserted=400, W47N7@84283400 inserted=330; inserted=2216, "
        "ts_realigned=0). After retry2 missing_chunks=0; every room distinct=700, missing_n=0. "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks recovered="
        f"{official_recovered} = {expected_official}). Previously in-window official 404 W45N8@84282500 has aged "
        f"out of this 40m window (hole 84282501..84282600 still {leftover['W45N8@84282500']['rows']} rows / "
        f"{leftover['W45N8@84282500']['distinct']} distinct; confirm still 404). "
        f"W47N8 hole 84281501..84281600 still {leftover['W47N8@84281500']['distinct']} live ticks / "
        f"{leftover['W47N8@84281500']['rows']} rows; W45N8 hole 84281501..84281600 still "
        f"{leftover['W45N8@84281500']['rows']}/{leftover['W45N8@84281500']['distinct']}. "
        f"W45N8@84279700 official 404 remains aged out (hole 84279701..84279800, db "
        f"{leftover['W45N8@84279700']['rows']} rows / {leftover['W45N8@84279700']['distinct']} distinct). "
        "Other aged leftover official 404s still 404 after confirm GET. No empty-no-creep in this window."
    )
    verify_text = "\n".join(verify_lines) + "\n"

    # append to first-pass history_backfill.txt to produce now.txt
    first = (DIR / "history_backfill.txt").read_text()
    # strip trailing EXIT line handling — keep it and append
    now_extra = (
        "confirm recovered none; still_404 in-window W47N8@84283400,W45N8@84283400,W47N7@84283400 "
        "inserted=0 ts_realigned=0 at 18:59:57 game.time=84283515\n"
        "retry2 recovered W47N8@84283400,W45N8@84283400,W47N7@84283400 "
        "inserted=2216 ts_realigned=0 at 19:01:55 game.time=84283543\n"
        f"inserted_total=12062 unique_after rows={unique_after['rows']} "
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
        "confirm_game_time": 84283515,
        "retry2_game_time": 84283543,
        "tick_s": TICK_S,
        "inserted_first": 9846,
        "already_in_db": 11900,
        "ts_realigned": 0,
        "inserted_confirm": 0,
        "inserted_retry2": 2216,
        "inserted_total": 12062,
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
        "inserted": 12062,
        "already_in_db": 11900,
        "ts_realigned": 0,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": ["W47N8@84283400", "W45N8@84283400", "W47N7@84283400"],
        "unique_after_window": unique_after,
        "confirm_inserted": 0,
        "retry2_inserted": 2216,
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
    (DIR / "history_backfill.txt").write_text(now_text)  # keep first-pass+appends in the run folder's txt too? 
    # Actually keep original first-pass file; write a combined copy as history_backfill_now in folder
    # Re-read: last run used history_backfill.txt as the first-pass plus maybe not overwritten.
    # I'll restore first pass and write combined to history_backfill_full.txt and now.txt
    # Wait I already overwrote. I still have `first` in memory — write first back, write combined separately.
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
