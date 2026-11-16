#!/usr/bin/env python3
"""Write coverage + status records for the 10:30 half-hour history backfill."""
from __future__ import annotations
import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_1030"
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84295901, 84296600
WINDOW_N = TMAX - TMIN + 1  # 700
TICK_S = 4.28517  # later-mean-robust; applied correctly and left in db
TICK_S_LATER = 4.28517  # later-mean-robust (raw later-mean same); applied
TICK_S_FIRST = 4.20627  # first-interval used by the script (printed 4.206); sane but later applied
GAME_TIME_FIRST = 84296605
PUBLISHED = "84295900..84296500"
CONFIRM_GT = 84296627
CONFIRM_AT = "10:38:34"
RETRY2_GT = 84296661
RETRY2_AT = "10:40:57"
RETRY2_SKIPPED = False
IN_WINDOW_404S_FIRST = [
    ("W45N8", 84295900),
    ("W47N8", 84296500),
    ("W45N8", 84296500),
    ("W47N7", 84296500),
]
IN_WINDOW_404S_FINAL = [
    ("W45N8", 84295900),
    ("W47N7", 84296500),
]
LEFTOVER_404S = [
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
NEW_FIRST = {"W46N8": 929, "W47N8": 1291, "W45N8": 325, "W45N7": 593, "W47N7": 375}
NEW_CONFIRM = {"W46N8": 0, "W47N8": 1384, "W45N8": 410, "W45N7": 0, "W47N7": 0}
NEW_RETRY2 = {"W46N8": 0, "W47N8": 0, "W45N8": 124, "W45N7": 0, "W47N7": 0}
EMPTY_NO_CREEP = {}
EMPTY_NO_CREEP_N = 0
INSERTED_FIRST = 3513
ALREADY_IN_DB = 18664
CREEP_ROWS_RECONSTRUCTED = 22177
INSERTED_CONFIRM = 1794
INSERTED_RETRY2 = 124
INSERTED_TOTAL = 5431
TICK_S_CHECK_AT = "10:38:11"
TICK_S_CHECK_GT = 84296622
TICK_S_REALIGN_AT = "10:38:16"
TICK_S_REALIGN_GT = 84296622
TS_REALIGNED_FIRST = 8357
TS_REALIGNED_LATER = 4379
TS_REALIGNED_CONFIRM = 0
OFFICIAL_404_TICKS = 200  # W45N8@84295900 + W47N7@84296500 still 404 after retry2


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

    official_ticks = {room: WINDOW_N for room in ROOMS}
    official_ticks["W45N8"] = 600  # W45N8@84295900 still official 404
    official_ticks["W47N7"] = 600  # W47N7@84296500 still official 404
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
        "First pass (game.time=84296605) published_bases 84295900..84296500, reconstructed "
        "84295901..84296600 (700). missing_chunks=4 of 35 official GETs: W45N8@84295900, "
        "W47N8@84296500, W45N8@84296500, W47N7@84296500 (the other 31 were 200). "
        "already_in_db=18664 would_insert=3513; first pass inserted=3513 (W46N8 929 / W47N8 1291 / "
        "W45N8 325 / W45N7 593 / W47N7 375), ts_realigned=8357 on first-interval tick_s=4.20627 "
        "(printed 4.206), which is in the sane 3-6s band. later-mean-robust 4.28517 was over the "
        "45s gate versus those first-pass rows (check at 10:38:11 game.time=84296622: later "
        "over45=5547 over15=9816 mean_off~18.94s max_off~57.87s; first over45=0 over15=9392 "
        "mean_off~-12.29s max_off~0.98s). A corrective later-mean-robust realign of 4379 rows was "
        "applied at 10:38:16 game.time=84296622; after over45=0 over15=4408 mean_off~6.71s "
        "max_off~44.99s vs later, and was kept (not reverted). Confirm GET 2026-11-16 10:38:34 "
        "Asia/Hong_Kong game.time=84296627 recovered W47N8@84296500 (inserted=1384, 100 distinct "
        "84296501..84296600) and W45N8@84296500 (inserted=410); W45N8@84295900, W47N7@84296500 and "
        "leftover W45N7@84295800 (just outside this window) still 404. It also retried 35 aged "
        "leftover official 404s including W46N8@84292000, all still 404. Confirm inserted=1794 "
        "ts_realigned=0. retry2 at 10:40:57 game.time=84296661 recovered additional W45N8@84296500 "
        "rows (inserted=124; 100 distinct already present) and re-fetched W47N8@84296500 "
        "(inserted=0). W45N8@84295900 and W47N7@84296500 remain official 404 in window; "
        "W45N7@84295800 remains official 404 just outside this window. Official coverage after "
        "retry2 is 3300 of 3500 official room-ticks (200 still 404). W46N8, W47N8 and W45N7 each "
        "have 700 distinct ticks with creeps in this window; W45N8 has 600 distinct (hole "
        "84295901..84296000 official 404); W47N7 has 600 distinct (hole 84296501..84296600 official "
        "404). The previous 10:00 unseeded W45N8 gap 84296001..84296089 was already filled by "
        "pre-check (100 distinct). No official empty-no-creep ticks in the recovered portion."
    )

    inserted_note = (
        "The previous 10:00 Asia/Hong_Kong half-hour backfill prefilled official 84295401..84296100 "
        "(inserted_total=12435 after first=10648 + confirm=1402 + retry2=385, already_in_db=11462, "
        "first-pass ts_realigned=0 on tick_s=4.24957, later-mean-robust 4.23879 already inside the "
        "45s gate with no corrective realign, first-pass missing_chunks=5, game.time=84296102). That "
        "window overlaps 200 ticks of this run (84295901..84296100). After the 10:00 backfill there "
        "was one box freeze: 10:12:14–10:22:56 Asia/Hong_Kong (634s; VM hibernated; wall jumped, "
        "monotonic did not) with listener.py logged freeze at 10:22:56 (also ws ping/pong timed out) "
        "and run_listener.sh relaunch at 10:22:59. A later ws ping/pong timeout at 10:36:22 caused "
        "another listener.py restart at 10:36:25 (new listener.py pid 3354234 at 10:36:35). "
        "run_listener.sh (pid 4035476, unchanged since 2026-11-11) stayed up. The listener was "
        "already healthy at pre-check (10:36:40), having pulled segment-90 itself (creep_cpu tip "
        "84296590 / path_arrivals tip 84296580 at 10:36:36 and 10:35:53). A 10:25 hourly patrol had "
        "already run after the freeze and before this backfill. This half-hour first pass "
        "(game.time=84296605) had missing_chunks=4, inserted=3513, already_in_db=18664. Confirm "
        "recovered 2 of 4 in-window official 404s (inserted=1794) and left 35 aged leftover official "
        "404s still 404, plus leftover W45N7@84295800 (just outside this window) still 404. retry2 "
        "added 124 more W45N8@84296500 rows (inserted=124); W45N8@84295900 and W47N7@84296500 remain "
        "official 404 in window. inserted_total=5431. First-pass ts_realigned=8357 on tick_s=4.20627; "
        "later-mean-robust 4.28517 applied a corrective realign of 4379 rows at game.time=84296622 "
        "(after over45=0). First game/time request succeeded."
    )

    ts_realigned_note = (
        "First pass (tick_s=4.20627 printed 4.206, live anchor game.time=84296605) reported "
        "ts_realigned=8357. The script's tick_s is taken from the earliest two distinct published-chunk "
        "timestamps in this fetch (min 84295900 ts=1794794064546 W46N8 to min 84296000 "
        "ts=1794794485173 W46N8 → 4.20627s; printed 4.206). All six W46N8 / min-all intervals "
        "are in the sane 3-6s band (4.20627, 4.24904, 4.28137, 4.32279, 4.37624, 4.19640). "
        "later_mean_raw = later_mean_robust = 4.28517; all_mean = 4.27202; span_mean = 4.27202. A "
        "later-anchor check at 2026-11-16 10:38:11 Asia/Hong_Kong game.time=84296622 found over45=0 "
        "versus first (over15=9392, mean_off~-12.29s, max_off~0.98s) and over45=5547 over15=9816 versus "
        "later-mean-robust 4.28517 (mean_off~18.94s, max_off~57.87s). Delta first-robust is -0.07890 "
        "s/tick (~55.5s at tmin), over the 45s gate, so a corrective later-mean-robust realign of "
        "4379 rows was applied at 10:38:16 game.time=84296622; after over45=0 over15=4408 "
        "mean_off~6.71s max_off~44.99s vs later, and was kept. 4.28517 is the tick_s now in db. "
        "Confirm reported ts_realigned=0 (recovered W47N8@84296500 and W45N8@84296500, inserted=1794; "
        "35 aged leftover official 404s including W46N8@84292000 still 404). retry2 reported "
        "ts_realigned=0 (additional W45N8@84296500 inserted=124)."
    )

    live_json_note = (
        "After the 10:00 backfill there was one box freeze: 2026-11-16 10:12:14–10:22:56 "
        "Asia/Hong_Kong (634s; VM hibernated; wall jumped, monotonic did not), logged by "
        "listener.py at 10:22:56 (also ws ping/pong timed out) with run_listener.sh relaunch at "
        "10:22:59. A later ws ping/pong timeout at 10:36:22 caused another listener.py restart at "
        "10:36:25 (new listener.py pid 3354234 at 10:36:35). run_listener.sh pid 4035476 unchanged "
        "since 2026-11-11. yield_files=absent, single room slot, peacetime 5:5:1:1 (rot at pre-check "
        "on W46N8, i=0, left 74.4s). Did not start a second loop or kill war_cmd/pulse. Segment-90 "
        "was already current without a console query: at pre-check 10:36:40 creep_cpu tip 84296590 "
        "(last200 84296390..84296590, 1432 rows; max_ts 10:36:36 after reconnect pull), "
        "path_arrivals tip 84296580 (last200 24 rows, max_ts 10:35:53). room_stats tip was already "
        "current (84296600 / 10:36:38). live.json at pre-check was on HOME W46N8 (objects=266, "
        "gameTime=84296600, stats.t=84296600, cpu=17.49, bucket=10000, updated 10:36:38, age 2.9s). "
        "A 10:25 hourly patrol had already finished after the 10:12–10:22 freeze; no concurrent "
        "hourly patrol was running during this backfill, and this backfill issued no extra console "
        "queries. No new incidents-ingest drop was logged after the 05:30:10 invalid-integer '{}' "
        "event. This run did not change the peacetime single-slot 5:5:1:1 arrangement. The first "
        "official game/time request succeeded."
    )

    hourly_note = (
        "The previous 10:00 half-hour backfill had already prefilled 84295401..84296100 "
        "(inserted_total=12435, tick_s first-pass 4.24957 then later-mean-robust 4.23879 already "
        "inside the 45s gate with no corrective realign, first-pass missing_chunks=5, "
        "game.time=84296102), overlapping 200 ticks of this window (84295901..84296100), which "
        "together with live listener rows accounts for already_in_db=18664 of 22177 first-pass "
        "reconstructed rows. The previous run's in-window official 404 W45N7@84295800 has aged just "
        "outside this 40m window (hole 84295801..84295900) and remained official 404 on confirm and "
        "retry2. The previous unseeded W45N8 gap 84296001..84296089 was already filled by pre-check "
        "(100 distinct). Two in-window official 404s remain after retry2: W45N8@84295900 (hole "
        "84295901..84296000, 0 rows) and W47N7@84296500 (hole 84296501..84296600, 0 rows). W46N8@"
        "84292000 remains aged out of this 40m window and remained official 404 on confirm. No "
        "official empty-no-creep ticks in the recovered portion of this window."
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
        "missing_chunks": 2,
        "missing_chunk_list": ["W45N8@84295900", "W47N7@84296500"],
        "missing_chunk_first_pass": [
            "W45N8@84295900", "W47N8@84296500",
            "W45N8@84296500", "W47N7@84296500",
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
        "missing_chunks first_pass=4 at game.time=84296605 (31 of 35 official GETs 200; 404: "
        "W45N8@84295900, W47N8@84296500, W45N8@84296500, W47N7@84296500); "
        "published_bases 84295900..84296500, reconstructed 84295901..84296600 (700), "
        "already_in_db=18664 inserted=3513, ts_realigned=8357 on tick_s=4.20627 (printed 4.206, "
        "sane first interval). later-mean-robust 4.28517 was over the 45s gate at 10:38:11 "
        "game.time=84296622 (later over45=5547 over15=9816; first over45=0 over15=9392), so a "
        "corrective later-mean-robust realign of 4379 rows was applied at 10:38:16 "
        "game.time=84296622 (after over45=0 over15=4408 vs later) and kept. Confirm 2026-11-16 "
        "10:38:34 Asia/Hong_Kong game.time=84296627 recovered W47N8@84296500 (inserted=1384, 100 "
        "distinct) and W45N8@84296500 (inserted=410); W45N8@84295900, W47N7@84296500, and leftover "
        "W45N7@84295800 still 404; retried 35 aged leftover official 404s including W46N8@84292000 "
        "— all still 404; inserted=1794 ts_realigned=0. retry2 at 10:40:57 game.time=84296661 "
        "added 124 more W45N8@84296500 rows (100 distinct already present); W45N8@84295900 and "
        "W47N7@84296500 still 404; leftover W45N7@84295800 still 404. After retry2: "
        "W46N8/W47N8/W45N7 each distinct=700 missing_n=0; W45N8 distinct=600 missing_n=100 official "
        "404 (84295901..84296000); W47N7 distinct=600 missing_n=100 official 404 "
        "(84296501..84296600). "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"(5*{WINDOW_N} would be {expected_official}; official room-ticks with creeps="
        f"{official_with_creeps}; official empty-no-creep={EMPTY_NO_CREEP_N}; official room-ticks "
        f"fetched/recovered={official_recovered}; official 404 in window after retry2=2 / 200 ticks). "
        f"Previously in-window official 404 W45N7@84295800 is just outside this 40m window "
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
        "404 after confirm GET. First-pass tick_s=4.20627 (printed 4.206) was sane; later-mean-robust "
        f"4.28517 was applied (check at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT}; "
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
        "confirm recovered W47N8@84296500 and W45N8@84296500 at 10:38:34 game.time=84296627 "
        "inserted=1794 ts_realigned=0; W45N8@84295900, W47N7@84296500, W45N7@84295800 still 404; "
        "retried 35 aged leftover official 404s including W46N8@84292000, all still 404; retry2 at "
        "10:40:57 game.time=84296661 recovered additional W45N8@84296500 inserted=124 "
        "ts_realigned=0; W45N8@84295900 and W47N7@84296500 still 404 in window; leftover "
        "W45N7@84295800 still 404\n"
        "ts_realigned_first_pass=8357 (tick_s=4.20627 printed 4.206, sane first interval); "
        f"later-mean-robust 4.28517 applied corrective realign of 4379 rows "
        f"(check at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT}, realign at {TICK_S_REALIGN_AT} "
        f"game.time={TICK_S_REALIGN_GT}, after over45=0 over15=4408 vs later)\n"
        f"inserted_total=5431 unique_after rows={unique_after['rows']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={EMPTY_NO_CREEP_N} "
        f"official_recovered={official_recovered} expected=5*{WINDOW_N}={expected_official} "
        f"in_window_official_404=2 after retry2 (first-pass missing_chunks=4; confirm recovered 2, "
        "retry2 added more rows on an already-recovered chunk)\n"
        "official empty-no-creep ticks in this window: none in the recovered portion. Remaining "
        "holes: W45N8 official 404 84295901..84296000; W47N7 official 404 84296501..84296600. "
        "Leftover just outside window: W45N7 official 404 84295801..84295900. "
        "W46N8/W47N8/W45N7 each 700 distinct with creeps\n"
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
        "missing_chunks": 2,
        "missing_chunk_list": ["W45N8@84295900", "W47N7@84296500"],
        "missing_chunk_first_pass": [
            "W45N8@84295900", "W47N8@84296500",
            "W45N8@84296500", "W47N7@84296500",
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
        "retry2 2026-11-16 10:40:57 Asia/Hong_Kong game.time=84296661: first pass missing_chunks=4 "
        "at game.time=84296605; confirm at 10:38:34 game.time=84296627 recovered W47N8@84296500 "
        "(inserted=1384) and W45N8@84296500 (inserted=410) and left W45N8@84295900, "
        "W47N7@84296500, and leftover W45N7@84295800 still 404 (also retried 35 aged leftovers, "
        "all still 404, confirm inserted=1794). retry2 added 124 more W45N8@84296500 rows (100 "
        "distinct already present) and re-fetched W47N8@84296500 (inserted=0). W45N8@84295900 and "
        "W47N7@84296500 remain official 404 in window; leftover W45N7@84295800 remains official "
        "404 just outside this window; all three should be retried next run.\n"
    )
    # keep DIR/backfill_retry2.txt as the actual GET log
    (ROOT / "state" / "_halfhour_backfill_retry2_1030.txt").write_text(retry2_note)

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
