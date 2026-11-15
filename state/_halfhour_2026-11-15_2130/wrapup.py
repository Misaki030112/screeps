#!/usr/bin/env python3
"""Write coverage + status records for the 21:30 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-15_2130"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84284901, 84285600
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.256  # first-pass script value (first interval)
TICK_S_LATER = 4.24563  # W46N8 later-mean; no corrective (already inside 45s gate)
GAME_TIME_FIRST = 84285677
PUBLISHED = "84284900..84285500"
CONFIRM_GT = 84285695
CONFIRM_AT = "21:33:30"
RETRY2_GT = 84285712
RETRY2_AT = "21:34:45"
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
NEW_FIRST = {"W46N8": 882, "W47N8": 1515, "W45N8": 371, "W45N7": 0, "W47N7": 353}
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
        "First pass (game.time=84285677) published_bases 84284900..84285500, reconstructed "
        "84284901..84285600 (700). 34 of 35 official GETs were 200; missing_chunks=1 "
        "W45N7@84285500 (the tip published base; the other four rooms returned 200 for that "
        "base). W45N7 first-pass reconstruction was 600 ticks (84284901..84285500). Confirm GET "
        "2026-11-15 21:33:30 Asia/Hong_Kong game.time=84285695 retried that in-window 404 plus "
        "29 aged leftover official 404s, recovering none (inserted=0, ts_realigned=0). retry2 "
        "2026-11-15 21:34:45 Asia/Hong_Kong game.time=84285712 retried only W45N7@84285500, "
        "still 404 (inserted=0, ts_realigned=0). After first+confirm+retry2, W46N8/W47N8/W45N8/"
        "W47N7 each have 700 distinct ticks in 84284901..84285600; W45N7 has "
        f"{cov['W45N7']['distinct']} distinct, missing_n={cov['W45N7']['missing_n']} "
        f"{cov['W45N7']['missing_ranges']}. The in-window hole 84285501..84285600 has "
        f"{w45n7_hole['rows']} live rows / {w45n7_hole['distinct']} distinct "
        f"(range {w45n7_hole['min']}..{w45n7_hole['max']}); official ticks in "
        "84285501..84285583 remain empty. Aged leftover official 404s still 404 after confirm "
        "GET. No empty-no-creep in this window."
    )

    inserted_note = (
        "The previous 21:00 Asia/Hong_Kong half-hour backfill prefilled official 84284501..84285200 "
        "(inserted=14110, already_in_db=13889, first-pass ts_realigned=0, later-mean already inside "
        "the 45s gate so nfix=0, tick_s=4.165 / later 4.20342, missing_chunks=0, "
        "game.time=84285249). That window overlaps 300 ticks of this run (84284901..84285200). One "
        "box freeze since then dropped the live listener: 21:08:30–21:23:46 Asia/Hong_Kong (916s; "
        "relaunch 21:23:50; listener.py pid 3121287 started 21:23:59, still the live process at "
        "pre-check 21:32:02 and at finish). Pre-check at 21:32:02 already had post-21:00 "
        "official/live coverage since tick 84285200 of W45N7 330 distinct through 84285612, W45N8 "
        "324 through 84285583, W46N8 363 through 84285674, W47N7 301 through 84285500, W47N8 301 "
        "through 84285500; the W45N8@84282500 hole was still 0/0 and aged out of the new window. "
        "First pass inserted=3121 (already_in_db=23761 of 26882 reconstructed rows) with "
        "missing_chunks=1 (W45N7@84285500). Confirm inserted=0. retry2 inserted=0. "
        "inserted_total=3121. First pass ts_realigned=1496 onto first-interval tick_s=4.256; "
        "later-mean tick_s=4.24563 was already inside the 45s gate at 21:33:13 (game.time=84285691, "
        "still_over_45s_vs_later=0), so no corrective realign. First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.256, live anchor game.time=84285677) reported ts_realigned=1496. The "
        "script's tick_s is taken from the earliest two distinct published-chunk timestamps in this "
        "fetch (min 84284900 ts=1794746694719 to min 84285000 ts=1794747120321 → 425602ms/100="
        "4.25602s, printed 4.256). Later W46N8 min-ts successive bases in this fetch are ≈4.16940, "
        "4.24942, 4.30362, 4.30281, 4.20289 s/tick; mean of the five ≈4.24563. All-six mean "
        "including the first interval ≈4.24736. Delta first minus later is +0.01039 s/tick (~8.1s "
        "at tick 84284901), inside the 45s gate. A later-anchor check at 2026-11-15 21:33:13 "
        "Asia/Hong_Kong game.time=84285691 found still_over_45s_vs_later=0 (12504 rows 15s+ off) "
        "and 0 rows >45s off the first-interval rate at that later anchor. No corrective realign "
        "was applied. Confirm reported ts_realigned=0. retry2 reported ts_realigned=0."
    )

    live_json_note = (
        "One new box freeze since the previous 21:00 Asia/Hong_Kong half-hour: 2026-11-15 "
        "21:08:30–21:23:46 Asia/Hong_Kong (916s; VM hibernated; wall jumped, monotonic did not), "
        "logged by listener.py at 21:23:46 with run_listener.sh relaunch at 21:23:50 (listener.py "
        "pid 3121287 started 21:23:59, still the live listener at pre-check 21:32:02 and at finish). "
        "run_listener.sh pid 4035476 unchanged since 2026-11-11. yield_files=absent, single room "
        f"slot, peacetime 5:5:1:1 (rot at pre-check on W46N8, at finish on {rot.get('room')}). "
        "Did not start a second loop or kill war_cmd/pulse. Segment-90 and STATS came back without "
        "a console query: at pre-check 21:32:02 (about 8 min after the 21:23:50 relaunch) live.json "
        "gameTime=84285674 (slot on home W46N8) stats.t=84285670, creep_cpu tip 84285660 (7938 rows "
        "since tick 84284501, last200 84285460..84285660, 1388 rows), path_arrivals tip 84285658 "
        "(150 rows since tick 84284501, last200 26 rows), room_stats tip 84285670, creep_ticks tip "
        "84285674 (current slot W46N8). This run did not change the peacetime single-slot 5:5:1:1 "
        "arrangement. The first official game/time request succeeded."
    )

    hourly_note = (
        "The 21:23 1h peacetime patrol already finished earlier this evening. The 21:00 half-hour "
        "backfill had already prefilled 84284501..84285200 (inserted=14110, tick_s=4.165 / later "
        "4.20342, game.time=84285249), overlapping 300 ticks of this window (84284901..84285200). "
        "The aged W45N8@84282500 official 404 sits outside this window. This run added the newly "
        "published 84285200..84285500 chunks (all five rooms 200 on the first pass except "
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
        "creep_rows_reconstructed": 26882,
        "already_in_db": 23761,
        "inserted": 3121,
        "inserted_first_pass": 3121,
        "inserted_retry": 0,
        "inserted_retry2": 0,
        "inserted_note": inserted_note,
        "ts_realigned": 1496,
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
        "game.time=84285677; published_bases 84284900..84285500, reconstructed 84284901..84285600; "
        "W45N7 first-pass 600t through 84285500). Confirm 2026-11-15 21:33:30 Asia/Hong_Kong "
        "game.time=84285695 retried that in-window 404 plus 29 aged leftover official 404s, "
        "recovering none (inserted=0, ts_realigned=0). retry2 2026-11-15 21:34:45 Asia/Hong_Kong "
        "game.time=84285712 retried only W45N7@84285500, still 404 (inserted=0, ts_realigned=0). "
        f"After first+confirm+retry2: W46N8/W47N8/W45N8/W47N7 distinct=700 missing_n=0; W45N7 "
        f"distinct={cov['W45N7']['distinct']} missing_n={cov['W45N7']['missing_n']} "
        f"{cov['W45N7']['missing_ranges']}. distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks recovered="
        f"{official_recovered}). In-window official 404 W45N7@84285500 hole 84285501..84285600 has "
        f"{w45n7_hole['rows']} live rows / {w45n7_hole['distinct']} distinct "
        f"(range {w45n7_hole['min']}..{w45n7_hole['max']}); official 84285501..84285583 still empty. "
        f"Previously in-window official 404 W45N8@84282500 has aged out of this 40m window "
        f"(hole 84282501..84282600 still {leftover['W45N8@84282500']['rows']} rows / "
        f"{leftover['W45N8@84282500']['distinct']} distinct; confirm still 404). "
        f"W47N8 hole 84281501..84281600 still {leftover['W47N8@84281500']['distinct']} live ticks / "
        f"{leftover['W47N8@84281500']['rows']} rows; W45N8 hole 84281501..84281600 still "
        f"{leftover['W45N8@84281500']['rows']}/{leftover['W45N8@84281500']['distinct']}. "
        f"W45N8@84279700 official 404 remains aged out (hole 84279701..84279800, db "
        f"{leftover['W45N8@84279700']['rows']} rows / {leftover['W45N8@84279700']['distinct']} distinct). "
        "Other aged leftover official 404s still 404 after confirm GET. No empty-no-creep in this "
        "window. First-pass tick_s=4.256 realigned 1496 rows; later-mean already inside 45s gate "
        "(later-mean tick_s=4.24563, still_over_45s_vs_later=0, no corrective realign at 21:33:13 "
        "Asia/Hong_Kong game.time=84285691)."
    )
    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm recovered none; in-window official 404 W45N7@84285500 still 404; 29 aged leftover "
        "official 404s still 404 inserted=0 ts_realigned=0 at 21:33:30 game.time=84285695\n"
        "retry2 W45N7@84285500 still 404 inserted=0 ts_realigned=0 at 21:34:45 game.time=84285712\n"
        "ts_realigned_first_pass=1496 (tick_s=4.256); no corrective later-mean realign "
        "(later-mean tick_s=4.24563 nfix=0 still_over_45s_vs_later=0 at 21:33:13 game.time=84285691)\n"
        f"inserted_total=3121 unique_after rows={unique_after['rows']} "
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
        "inserted_first": 3121,
        "already_in_db": 23761,
        "ts_realigned": 1496,
        "ts_realigned_corrective_later_mean": 0,
        "inserted_confirm": 0,
        "inserted_retry2": 0,
        "inserted_total": 3121,
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
        "inserted": 3121,
        "already_in_db": 23761,
        "ts_realigned": 1496,
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
