#!/usr/bin/env python3
"""Write coverage + status records for the 02:30 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0230"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84289201, 84289900
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.113  # first-pass script value (first interval)
TICK_S_LATER = 4.25528  # W46N8 later-mean; corrective realign applied
GAME_TIME_FIRST = 84289927
PUBLISHED = "84289200..84289800"
CONFIRM_GT = 84289951
CONFIRM_AT = "02:34:58"
RETRY2_GT = 84289967
RETRY2_AT = "02:36:04"
IN_WINDOW_404S_FIRST = [("W47N7", 84289200), ("W45N7", 84289300)]
LEFTOVER_404S = [
    ("W47N8", 84287500),  # leftover official 404 from 00:00/00:30 windows; aged out
    ("W45N7", 84285500),  # leftover official 404 from 22:00 window; aged out
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
NEW_FIRST = {"W46N8": 1193, "W47N8": 3413, "W45N8": 619, "W45N7": 582, "W47N7": 768}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {}
EMPTY_NO_CREEP_N = 0
INSERTED_FIRST = 6575
ALREADY_IN_DB = 17760
CREEP_ROWS_RECONSTRUCTED = 24335
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_TOTAL = 6575
TICK_S_CHECK_AT = "02:34:51"
TICK_S_CHECK_GT = 84289950
TS_REALIGNED_FIRST = 11749
TS_REALIGNED_LATER = 11733
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
        in_window_404 = {f"{r}@{b}": hole(c, r, b) for r, b in IN_WINDOW_404S_FIRST}

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

    official_with_creeps = unique_after["distinct_room_ticks"]
    expected_official = 5 * WINDOW_N
    official_recovered = official_with_creeps + EMPTY_NO_CREEP_N
    w45n7_hole = leftover["W45N7@84285500"]
    w47n8_aged = leftover["W47N8@84287500"]

    per_room = {}
    for room in ROOMS:
        new_first = NEW_FIRST[room]
        new_c = NEW_CONFIRM[room]
        new_r2 = NEW_RETRY2[room]
        per_room[room] = {
            "ticks": cov[room]["distinct"],
            "ticks_official": WINDOW_N,
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
    known_in = []
    for r, b in IN_WINDOW_404S_FIRST:
        h = in_window_404[f"{r}@{b}"]
        known_in.append(
            f"{r}@{b} ({h['rows']} rows / {h['distinct']} distinct, "
            f"range {h['min']}..{h['max']}; still 404 after confirm and retry2)"
        )

    missing_chunk_note = (
        "First pass (game.time=84289927) published_bases 84289200..84289800, reconstructed "
        "84289201..84289900 (700). 33 of 35 official GETs were 200; missing_chunks=2 "
        "W47N7@84289200 and W45N7@84289300 (later chunks for both rooms in this window were already "
        "200, so these are mid-window official holes, not unpublished latest; same two chunks were "
        "already official 404 in the 02:00 run and still 404 then after confirm/retry2). "
        "already_in_db=17760 would_insert=6575; first pass inserted=6575, ts_realigned=11749 onto "
        "first-interval tick_s=4.113. Confirm GET 2026-11-16 02:34:58 Asia/Hong_Kong "
        "game.time=84289951 retried both in-window 404s plus 31 aged leftover official 404s "
        "(including W47N8@84287500, now outside this 40m window); all 33 were still 404, inserted=0. "
        "retry2 2026-11-16 02:36:04 Asia/Hong_Kong game.time=84289967 retried the two in-window 404s; "
        "both still 404, inserted=0. After confirm/retry2, W46N8/W47N8/W45N8 have 700 distinct ticks; "
        "W47N7 is missing 84289201..84289300 and W45N7 is missing 84289301..84289400. No official "
        "empty-no-creep ticks."
    )

    inserted_note = (
        "The previous 02:00 Asia/Hong_Kong half-hour backfill prefilled official 84288801..84289500 "
        "(inserted_total=17708 after first=17708 + confirm=0 + retry2=0, already_in_db=9668, "
        "first-pass ts_realigned=0 on tick_s=4.202, later-mean 4.20189 already inside the 45s gate "
        "with no corrective realign, missing_chunks=2 W47N7@84289200 and W45N7@84289300 still 404 "
        "after confirm/retry2, game.time=84289525). That window overlaps 300 ticks of this run "
        "(84289201..84289500), including the same two official 404 holes. Two new box freezes ran "
        "after that backfill: 02:11:11–02:22:56 Asia/Hong_Kong (705s; VM hibernated; wall jumped, "
        "monotonic did not) with listener.py restart at 02:22:59, and 02:30:14–02:32:31 (136s) with "
        "listener.py logged freeze at 02:32:31; run_listener.sh (pid 4035476, unchanged since "
        "2026-11-11) relaunched at 02:32:34; new listener.py pid 3224969 started 02:32:43. Pre-check "
        "at 02:32:57 already had post-02:00 official/live coverage since tick 84289500 of W45N7 225 "
        "distinct through 84289809, W45N8 201 through 84289700, W46N8 276 through 84289923, W47N7 201 "
        "through 84289700, W47N8 201 through 84289700; W47N7@84289200 and W45N7@84289300 were still "
        "0 rows, and the aged W45N7@84285500 hole still had 17 live ticks (84285584..84285600, 63 "
        "rows). First pass inserted=6575 (already_in_db=17760 of 24335 reconstructed rows in "
        "84289201..84289900) with missing_chunks=2 W47N7@84289200 and W45N7@84289300, covering the "
        "02:11–02:22 and 02:30–02:32 box-freeze gaps for rooms not on the single peacetime slot. "
        "Confirm and retry2 did not recover those two chunks (inserted=0 each). inserted_total=6575. "
        "First pass ts_realigned=11749 onto first-interval tick_s=4.113; later-mean tick_s=4.25528 "
        "was over the 45s gate (over45=11749, over15=19702, n=25693 at 02:34:51 game.time=84289950), "
        "so a corrective later-mean realign of 11733 rows was applied (after over45=0, over15=7241, "
        "n=25693). Confirm/retry2 ts_realigned=0. First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.113, live anchor game.time=84289927) reported ts_realigned=11749. The "
        "script's tick_s is taken from the earliest two distinct published-chunk timestamps in this "
        "fetch (min 84289200 ts=1794764972891 to min 84289300 ts=1794765384164 → 4.113s printed; "
        "W46N8 first interval 4.11273). Later W46N8 min-ts successive bases in this fetch are "
        "4.19336, 4.34490, 4.29966, 4.20483, 4.23365 s/tick; later_mean 4.25528. All-six mean "
        "including the first interval = 4.23152. Delta first minus later is -0.14255 s/tick "
        "(~-103.5s at tick 84289201 versus the first-pass live anchor). A later-anchor check at "
        "2026-11-16 02:34:51 Asia/Hong_Kong game.time=84289950 found still_over_45s_vs_first=0 "
        "(rows already realigned onto 4.113; vs first-interval over15=7149) and "
        "still_over_45s_vs_later=11749 (n=25693; vs later-mean over15=19702 before corrective), so "
        "a corrective later-mean realign of 11733 rows was applied at game.time=84289950; after "
        "that still_over_45s_vs_later=0 and still_over_15s_vs_later=7241 (n=25693). Confirm and "
        "retry2 reported ts_realigned=0 (no new rows inserted; both in-window official 404s still "
        "404)."
    )

    live_json_note = (
        "Two box freezes ran after the 02:00 backfill: 2026-11-16 02:11:11–02:22:56 Asia/Hong_Kong "
        "(705s; VM hibernated; wall jumped, monotonic did not), logged by listener.py with "
        "run_listener.sh relaunch at 02:22:59; and 02:30:14–02:32:31 (136s), logged at 02:32:31 "
        "with run_listener.sh relaunch at 02:32:34 (new listener.py pid 3224969 started 02:32:43). "
        "run_listener.sh pid 4035476 unchanged since 2026-11-11. yield_files=absent, single room "
        "slot, peacetime 5:5:1:1 (rot at pre-check on W46N8). Did not start a second loop or kill "
        "war_cmd/pulse. Segment-90 and STATS were already current without a console query: at "
        "pre-check 02:32:57 live.json gameTime=84289923 (slot on HOME W46N8, objects=264) "
        "stats.t=84289920 cpu=19.43 b=10000, creep_cpu tip 84289910 (6446 rows since tick 84288801, "
        "last200 84289710..84289910, 1428 rows, max_ts 02:32:31), path_arrivals tip 84289902 (142 "
        "rows since tick 84288801, last200 23 rows), room_stats tip 84289920, creep_ticks tip "
        "84289923. No new incidents ingest drop after the known 00:30:10 invalid integer '{{}}' "
        "event. This run did not change the peacetime single-slot 5:5:1:1 arrangement. The first "
        "official game/time request succeeded."
    )

    hourly_note = (
        "The previous 02:00 half-hour backfill had already prefilled 84288801..84289500 "
        "(inserted_total=17708, tick_s=4.202 / later 4.20189 with no corrective realign, "
        "game.time=84289525), overlapping 300 ticks of this window (84289201..84289500) and leaving "
        "the persistent official 404s W47N7@84289200 and W45N7@84289300 inside this window, plus "
        "W47N8@84287500 aged out. First pass recovered 33 of 35 official chunks in "
        "84289201..84289900 (inserted=6575, missing_chunks=2 W47N7@84289200 and W45N7@84289300), "
        "covering the 02:11:11–02:22:56 and 02:30:14–02:32:31 box-freeze gaps for rooms not on the "
        "single peacetime slot. Confirm (02:34:58, game.time=84289951) and retry2 (02:36:04, "
        "game.time=84289967) left both in-window official 404s unpublished; 31 aged leftover official "
        "404s still 404. There were no official empty-no-creep ticks in this 40m window. Aged leftover "
        "official 404s including W47N8@84287500 and W45N7@84285500 remain outside this window."
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
        "missing_chunks": 2,
        "missing_chunk_list": ["W47N7@84289200", "W45N7@84289300"],
        "missing_chunk_first_pass": ["W47N7@84289200", "W45N7@84289300"],
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
        "missing_chunks first_pass=2 (W47N7@84289200 and W45N7@84289300 official 404 at "
        "game.time=84289927; other 33 official GETs 200; published_bases 84289200..84289800, "
        "reconstructed 84289201..84289900 (700), already_in_db=17760 inserted=6575). Confirm "
        "2026-11-16 02:34:58 Asia/Hong_Kong game.time=84289951 still 404 on both in-window chunks "
        "(inserted=0 ts_realigned=0) and retried 31 aged leftover official 404s including "
        "W47N8@84287500 (now outside this 40m window); those 31 were still 404. retry2 2026-11-16 "
        "02:36:04 Asia/Hong_Kong game.time=84289967 still 404 on W47N7@84289200 and W45N7@84289300 "
        "(later chunks for both rooms in this window were already 200, so these are mid-window "
        "official holes, also still 404 in the 02:00 run). After confirm/retry2: "
        "W46N8/W47N8/W45N8 each distinct=700 missing_n=0; "
        "W47N7 missing 84289201..84289300; W45N7 missing 84289301..84289400 (no official "
        "empty-no-creep ticks in this window). "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window=2 after confirm/retry2). "
        f"Previously in-window official 404 W47N8@84287500 remains aged out of this 40m window (hole "
        f"84287501..84287600 still {w47n8_aged['rows']} rows / {w47n8_aged['distinct']} distinct; "
        f"confirm still 404). Previously in-window official 404 W45N7@84285500 remains aged out of "
        f"this 40m window (hole 84285501..84285600 still {w45n7_hole['rows']} rows / "
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
        f"404 after confirm GET. First-pass tick_s=4.113 realigned 11749 rows; later-mean was over "
        f"the 45s gate (over45=11749, over15=19702, n=25693) so a corrective later-mean realign of "
        f"11733 rows was applied (later-mean tick_s=4.25528, at {TICK_S_CHECK_AT} Asia/Hong_Kong "
        f"game.time={TICK_S_CHECK_GT}; after over45=0, over15=7241, n=25693)."
    )

    verify_text = "\n".join(verify_lines) + "\n"

    first = (DIR / "history_backfill.txt").read_text()
    now_extra = (
        "confirm still 404 W47N7@84289200 and W45N7@84289300 inserted=0 ts_realigned=0 at 02:34:58 "
        "game.time=84289951; retried 31 aged leftover official 404s (including W47N8@84287500, now "
        "outside this 40m window) all still 404; retry2 02:36:04 game.time=84289967 also still 404 "
        "on both in-window chunks\n"
        "ts_realigned_first_pass=11749 (tick_s=4.113); later-mean over 45s gate, corrective realign "
        f"applied (later-mean tick_s=4.25528 nfix=11733 still_over_45s_vs_later=0 at "
        f"{TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT})\n"
        f"inserted_total=6575 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=2 after confirm/retry2 (first-pass W47N7@84289200 and "
        f"W45N7@84289300 still 404)\n"
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
        "in_window_official_404_first_pass": {"W47N7@84289200": "still_404_after_retry2", "W45N7@84289300": "still_404_after_retry2"},
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
        "in_window_official_404_first_pass": {"W47N7@84289200": "still_404_after_retry2", "W45N7@84289300": "still_404_after_retry2"},
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
        "missing_chunks": 2,
        "missing_chunk_list": ["W47N7@84289200", "W45N7@84289300"],
        "missing_chunk_first_pass": ["W47N7@84289200", "W45N7@84289300"],
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
          "in_window_404", 2)
    print("db_tips", tips)
    print("live_after", live_after)
    print("listener", listener_at_finish)
    rooms_ok = all(v["missing_n"] == 0 for v in cov.values())
    print("ok_complete", official_recovered == expected_official and rooms_ok)
    print("routine_ok", True)  # official mid-window 404s documented; DB write and API otherwise succeeded


if __name__ == "__main__":
    main()
