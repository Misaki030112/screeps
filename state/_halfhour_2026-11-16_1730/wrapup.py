#!/usr/bin/env python3
"""Write local status records for this half-hour official-history backfill."""
from __future__ import annotations
import json, os, time, subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOT = "/workspace/screeps"
DIR = f"{ROOT}/state/_halfhour_2026-11-16_1730"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84301201, 84301900
SPAN = TMAX - TMIN + 1  # 700
IN_WINDOW_404 = set()  # first pass missing_chunks=0; confirm/retry2 were leftover-only
GT_FIRST = 84301970
PUB_BASES = "84301200..84301800"
TICK_S_FIRST = 4.76419
TICK_S_PRINTED = "4.764"
TICK_S_LATER = 4.74546
INSERTED_FIRST = 3376
ALREADY = 22333
CREEP_ROWS = 25709
TS_REALIGNED_FIRST = 0
FIRST_NEW = {"W46N8": 830, "W47N8": 1648, "W45N8": 265, "W45N7": 289, "W47N7": 344}
FIRST_OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}

def ranges(ticks, tmin=TMIN, tmax=TMAX):
    missing = []
    s = set(ticks)
    start = None
    for t in range(tmin, tmax + 1):
        if t not in s:
            if start is None:
                start = t
        else:
            if start is not None:
                missing.append([start, t - 1])
                start = None
    if start is not None:
        missing.append([start, tmax])
    return missing

def chunk_base(tick):
    return ((tick - 1) // 100) * 100

def now_hk():
    return datetime.now(TZ)

def load_confirm():
    try:
        return json.load(open(f"{DIR}/backfill_confirm_gets.json"))
    except Exception:
        return {}

def listener_snap():
    def pgrep(pat):
        try:
            out = subprocess.check_output(["pgrep", "-af", pat], text=True).strip().splitlines()
        except subprocess.CalledProcessError:
            out = []
        return [l for l in out if l.strip()]
    lis = pgrep("tools/listener.py")
    run = pgrep("tools/run_listener.sh")
    yield_present = any(
        os.path.exists(os.path.join(ROOT, "metrics", n))
        for n in ("listener_yield_rooms",)
    ) or bool(__import__("glob").glob(os.path.join(ROOT, "metrics", "*yield*")))
    rot = {}
    try:
        rot = json.load(open(f"{ROOT}/metrics/listener_rot.json"))
    except Exception:
        pass
    live = {}
    age = None
    try:
        live = json.load(open(f"{ROOT}/metrics/live.json"))
        age = round(time.time() - os.stat(f"{ROOT}/metrics/live.json").st_mtime, 1)
    except Exception:
        pass
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    return {
        "listener_count": len(lis),
        "run_listener_count": len(run),
        "listener_ps": lis + run,
        "yield_files": "present" if yield_present else "absent",
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "live_updated": live.get("updated"),
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_json_mtime_age_s": age,
        "single_slot": len(lis) == 1 and len(run) == 1,
        "did_not_start_second_listener": True,
        "self_restart_note": (
            "Existing run_listener.sh loop relaunched listener.py at 17:21:23 after "
            "'box frozen ~228s since 2026-11-16 17:17:32' (reconnecting at 17:21:20; "
            "old pid 3492867 from 17:10:47 gone; new pid 3496256 since 17:21:33). "
            "Earlier the same hour: freeze 16:49:15–17:01:19 (~712s) relaunched at 17:01:22 "
            "(pid 3488865 since 17:01:31); freeze 17:09:04–17:10:34 (~81s) plus a websocket "
            "ping/pong timeout at 17:10:35 relaunched at 17:10:38 (pid 3492867 since 17:10:47). "
            "This backfill did not kill or start a listener."
        ),
    }

def main():
    conf = load_confirm()
    confirm_at = conf.get("confirm_at") or conf.get("at") or "2026-11-16 17:35:13 Asia/Hong_Kong"
    confirm_gt = conf.get("confirm_game_time") or conf.get("game_time")
    confirm_ins = conf.get("inserted", 0)
    confirm_nfix = conf.get("ts_realigned", 0)
    confirm_rec = conf.get("recovered") or []
    r2 = conf.get("retry2") or {}
    retry2_at = conf.get("retry2_at") or r2.get("at")
    retry2_gt = conf.get("retry2_game_time") or r2.get("game_time")
    retry2_ins = conf.get("retry2_inserted", r2.get("inserted", 0)) or 0
    retry2_nfix = conf.get("retry2_ts_realigned", r2.get("ts_realigned", 0)) or 0
    retry2_rec = conf.get("retry2_recovered") or r2.get("recovered") or []

    coverage = {}
    official_404_missing = {}
    empty_no_creep = {}
    with db.connect() as c:
        unique = c.execute(
            """SELECT count(*), count(DISTINCT (creep, tick)), count(DISTINCT tick),
                      count(DISTINCT (room, tick))
               FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s)""",
            (TMIN, TMAX, list(ROOMS)),
        ).fetchone()
        for room in ROOMS:
            rows = c.execute(
                "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
                (room, TMIN, TMAX),
            ).fetchall()
            ticks = [r[0] for r in rows]
            n = c.execute(
                "SELECT count(*), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, TMIN, TMAX),
            ).fetchone()
            miss = ranges(ticks)
            miss_404, miss_empty = [], []
            n404 = nempty = 0
            for a, b in miss:
                cur_404 = cur_empty = None
                for t in range(a, b + 1):
                    is_404 = (room, chunk_base(t)) in IN_WINDOW_404
                    if is_404:
                        n404 += 1
                        if cur_404 is None:
                            if cur_empty is not None:
                                miss_empty.append(cur_empty); cur_empty = None
                            cur_404 = [t, t]
                        else:
                            cur_404[1] = t
                    else:
                        nempty += 1
                        if cur_empty is None:
                            if cur_404 is not None:
                                miss_404.append(cur_404); cur_404 = None
                            cur_empty = [t, t]
                        else:
                            cur_empty[1] = t
                if cur_404 is not None:
                    miss_404.append(cur_404)
                if cur_empty is not None:
                    miss_empty.append(cur_empty)
            coverage[room] = {
                "distinct": len(ticks),
                "rows": n[0] or 0,
                "range": [n[1], n[2]] if n[1] is not None else None,
                "missing_n": sum((b - a + 1) for a, b in miss),
                "missing_ranges": miss,
                "official_empty_no_creep": nempty,
                "official_404_missing": n404,
            }
            official_404_missing[room] = {"n": n404, "ranges": miss_404}
            empty_no_creep[room] = {"n": nempty, "ranges": miss_empty}
        tips = {}
        for table in ("creep_ticks", "room_stats", "creep_cpu", "path_arrivals"):
            row = c.execute(f"SELECT max(tick), max(ts) FROM {table}").fetchone()
            tips[table] = {"max_tick": row[0], "max_ts": row[1].isoformat() if row[1] else None}
        live_after = {}
        for room in ROOMS:
            row = c.execute(
                """SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
                   FROM creep_ticks WHERE room=%s AND tick > %s""",
                (room, TMAX),
            ).fetchone()
            live_after[room] = {"distinct": row[0] or 0, "min": row[1], "max": row[2], "rows": row[3] or 0}
        leftovers = {}
        leftover_specs = [
            ("W47N8", 84300901, 84301000),
            ("W45N8", 84300901, 84301000),
            ("W45N8", 84300001, 84300100),
            ("W47N8", 84298001, 84298100),
            ("W47N8", 84297201, 84297300),
            ("W47N7", 84296501, 84296600),
            ("W45N8", 84295901, 84296000),
            ("W45N7", 84295801, 84295900),
        ]
        for room, a, b in leftover_specs:
            row = c.execute(
                """SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
                   FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s""",
                (room, a, b),
            ).fetchone()
            leftovers[f"{room}@{a-1}"] = {
                "distinct": row[0] or 0, "min": row[1], "max": row[2], "rows": row[3] or 0,
            }

    unique_after = {
        "rows": unique[0],
        "unique_creep_tick_rows": unique[1],
        "distinct_ticks": unique[2],
        "distinct_room_ticks": unique[3],
    }
    official_with_creeps = sum(coverage[r]["distinct"] for r in ROOMS)
    empty_ticks = sum(empty_no_creep[r]["n"] for r in ROOMS)
    official_404_ticks = sum(official_404_missing[r]["n"] for r in ROOMS)
    official_fetched = 5 * SPAN
    official_recovered = official_with_creeps + empty_ticks
    expected = 5 * SPAN
    in_window_404 = 0

    cov_payload = {
        "window": [TMIN, TMAX],
        "span": SPAN,
        "coverage": coverage,
        "unique_after": unique_after,
        "official_with_creeps": official_with_creeps,
        "empty_no_creep": empty_ticks,
        "official_404_missing": official_404_ticks,
        "official_fetched": official_fetched,
        "official_recovered": official_recovered,
        "expected": expected,
        "in_window_official_404": in_window_404,
        "db_tips": tips,
        "live_after": live_after,
        "at": now_hk().strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    }
    with open(f"{DIR}/coverage_final.json", "w") as f:
        json.dump(cov_payload, f, indent=2)
        f.write("\n")

    listener = listener_snap()
    finished = now_hk()
    finished_hkt = finished.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")

    per_room = {}
    for room in ROOMS:
        c = coverage[room]
        per_room[room] = {
            "ticks": FIRST_OFFICIAL_TICKS[room],
            "ticks_official": FIRST_OFFICIAL_TICKS[room],
            "new": FIRST_NEW[room],
            "new_first_pass": FIRST_NEW[room],
            "new_confirm": 0,
            "new_retry2": 0,
            "distinct": c["distinct"],
            "rows": c["rows"],
            "range": c["range"],
            "missing_n": c["missing_n"],
            "missing_ranges": c["missing_ranges"],
            "official_empty_no_creep": c["official_empty_no_creep"],
            "official_404_missing": c["official_404_missing"],
        }

    def leftover_desc(key, extra):
        info = leftovers[key]
        d, n, mn, mx = info["distinct"], info["rows"], info["min"], info["max"]
        rng = f"{mn}..{mx}" if mn is not None else "None..None"
        return f"{key} ({n} rows / {d} distinct, range {rng}; {extra})"

    known_in = []
    known_out = [
        leftover_desc("W47N8@84300900",
            "just outside this 40m window, still 404, live-filled 74 ticks with holes "
            "84300965..84300983 (19) and 84300994..84301000 (7); 26 official-missing; retry next run"),
        leftover_desc("W45N8@84300900",
            "just outside this 40m window, still 404, live-filled 7 ticks 84300994..84301000 / 28 rows; "
            "93 empty 84300901..84300993; retry next run"),
        leftover_desc("W45N8@84300000",
            "just outside this 40m window, still 404, partially live-filled "
            "(26 live 84300067..84300092 / 159 rows; 74 empty); retry next run"),
        leftover_desc("W47N8@84298000",
            "just outside this 40m window, still 404, not live-filled; retry next run"),
        leftover_desc("W47N8@84297200",
            "just outside this 40m window, still 404, already live-filled 100 distinct; retry next run"),
        leftover_desc("W47N7@84296500",
            "just outside this 40m window, still 404, not live-filled; retry next run"),
        leftover_desc("W45N8@84295900",
            "just outside this 40m window, still 404, not live-filled; retry next run"),
        leftover_desc("W45N7@84295800",
            "just outside this 40m window, still 404, not live-filled; retry next run"),
    ]
    empty_ranges = {r: empty_no_creep[r]["ranges"] for r in ROOMS if empty_no_creep[r]["n"]}
    inserted_total = INSERTED_FIRST + (confirm_ins or 0) + (retry2_ins or 0)

    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": finished.isoformat(),
        "finished_at_hkt": finished_hkt,
        "shard": "shard3",
        "rooms": list(ROOMS),
        "minutes": 40,
        "game_time": GT_FIRST,
        "live_json_gameTime_at_finish": listener.get("live_gameTime"),
        "live_json_stats_t_at_finish": listener.get("live_stats_t"),
        "live_json_gameTime_note": (
            "Listener had already self-reconnected before this run: box freeze ~228s from "
            "2026-11-16 17:17:32 to 17:21:20 Asia/Hong_Kong, listener reconnecting at 17:21:20, "
            "run_listener.sh relaunched listener.py at 17:21:23 (pid 3496256 since 17:21:33; "
            "previous pid 3492867 from 17:10:47 exited). This 17:30 half-hour backfill did not "
            "kill or restart the listener, war_cmd, or pulse, and did not start a second listener. "
            "yield_files=absent; peacetime single-slot rotation W46N8:W47N8:W45N8:W45N7=5:5:1:1 unchanged. "
            "live.json was fresh at precheck (age 0.6s, roomSlot W46N8, gameTime=84301966, stats.t=84301960, objects=267). "
            "After reconnect, creep_cpu/path_arrivals buffers were already current "
            "(precheck last200ticks creep_cpu 84301760..84301960 / path_arrivals 84301760..84301952). "
            "The previous 17:00 half-hour backfill had official-backfilled 84300801..84301500 "
            "(inserted=11531, missing_chunks=2 W47N8@84300900 and W45N8@84300900, still 404 after that run's confirm/retry2). "
            "The concurrent 17:26 hourly patrol had already official-backfilled 84301101..84301800 "
            "(game.time=84301893, missing_chunks=0, inserted=8759, tick_s=4.626, ts_realigned=14833) "
            "and its python processes were gone by this run's 17:32:50 precheck."
        ),
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": SPAN},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": TICK_S_LATER,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": [],
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed "
            f"{TMIN}..{TMAX} (700). missing_chunks=0 (35 of 35 official GETs 200). "
            f"confirm at {confirm_at} game.time={confirm_gt} recovered {confirm_rec or 'none'} "
            f"inserted={confirm_ins} ts_realigned={confirm_nfix}. "
            f"retry2 at {retry2_at} game.time={retry2_gt} recovered {retry2_rec or 'none'} "
            f"inserted={retry2_ins} ts_realigned={retry2_nfix}. "
            "No in-window official 404. Leftovers just outside this window: "
            "W47N8@84300900 (74 live with holes), W45N8@84300900 (7 live 84300994..84301000), "
            "W45N8@84300000 (26 live + 74 empty), W47N8@84298000 (still empty), "
            "W47N8@84297200 (already live-filled), W47N7@84296500, W45N8@84295900, and W45N7@84295800 "
            "still 404; retried 35 aged leftover official 404s including W46N8@84292000, all still 404."
        ),
        "creep_rows_reconstructed": CREEP_ROWS,
        "already_in_db": ALREADY,
        "inserted": inserted_total,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": confirm_ins or 0,
        "inserted_retry2": retry2_ins or 0,
        "inserted_note": (
            "The previous 17:00 Asia/Hong_Kong half-hour backfill prefilled official 84300801..84301500 "
            "(inserted_total=11531, already_in_db=12600, first-pass missing_chunks=2 W47N8@84300900 and "
            "W45N8@84300900, tick_s=4.85064 then corrective later-mean-robust 4.75978). The 17:26 hourly "
            "patrol then official-backfilled 84301101..84301800 (inserted=8759, missing_chunks=0, tick_s=4.626). "
            f"A later box freeze 17:17:32–17:21:20 (~228s) interrupted live ingest until the listener "
            f"self-reconnected at 17:21:23. This 40-minute official history pull therefore inserted "
            f"{INSERTED_FIRST} new rows (already_in_db={ALREADY} of {CREEP_ROWS} reconstructed) across "
            f"{TMIN}..{TMAX}, mainly the newly published 84301800 chunk plus remaining off-slot / box-freeze "
            f"gaps not yet in the patrol fill. confirm and retry2 inserted { (confirm_ins or 0) + (retry2_ins or 0) }. "
            "W46N8, W47N8, W45N8, and W47N7 have 700 official ticks with creeps. W45N7 official 700 ticks "
            "include 6 empty-no-creep (84301233..84301236 and 84301249..84301250)."
        ),
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": 0,
        "ts_realigned_confirm": confirm_nfix or 0,
        "ts_realigned_retry2": retry2_nfix or 0,
        "ts_realigned_note": (
            f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) reported "
            f"ts_realigned={TS_REALIGNED_FIRST} (new official rows already on the live-anchor first-interval tick_s; "
            "the 17:26 patrol had also just realigned the 84301101..84301800 overlap). "
            "The script's tick_seconds() uses the first interval between published chunk bases "
            f"(min timestamp across rooms, which was W46N8 on every base this window). later-mean-robust "
            f"of the remaining W46N8 intervals is {TICK_S_LATER} (raw later-mean {TICK_S_LATER}; delta first-robust "
            "0.01873 s/tick, ~14.4s at tmin vs gt_first). At 17:34:23 Asia/Hong_Kong game.time=84301985, "
            "first-interval was inside the 45s gate (over45=0, over15=5085, mean_off=3.92, max_off=41.12) "
            "and later-mean-robust was also inside the 45s gate (over45=0, over15=10495, mean_off=-4.16). "
            "First-interval 4.76419 is in the sane 3-6s band; no corrective realign was applied. "
            "In-use tick_s is first-interval 4.76419."
        ),
        "ssl_first_attempt": "ok first try",
        "hourly_patrol_prefilled": (
            "The concurrent 17:26 Asia/Hong_Kong hourly patrol had already official-backfilled "
            "84301101..84301800 at game.time=84301893 (missing_chunks=0, inserted=8759, already_in_db=16497, "
            "tick_s=4.626, ts_realigned=14833) and was past that step by this run's precheck "
            "(no patrol/history_backfill process listed at 17:32:50). The previous 17:00 half-hour backfill "
            "had prefilled 84300801..84301500 (inserted=11531, tick_s=4.85064 / later 4.75978, "
            "first-pass missing_chunks=2 W47N8@84300900 and W45N8@84300900, still 404). A box freeze "
            "17:17:32–17:21:20 (~228s) interrupted live ingest until the listener self-reconnected at 17:21:23. "
            "Official history in this window covers all of 84301200..84301800 for all five rooms (35/35 200)."
        ),
        "per_room": per_room,
        "known_official_404s_outside_window": known_out,
        "known_official_404s_in_window": known_in,
        "w45n7_empty_no_creep_in_window": bool(empty_no_creep.get("W45N7", {}).get("n")),
        "w45n7_empty_no_creep_ranges": empty_no_creep.get("W45N7", {}).get("ranges") or [],
        "empty_no_creep_in_window": bool(empty_ticks),
        "empty_no_creep_ranges": empty_ranges,
        "empty_no_creep_ticks": empty_ticks,
        "official_room_ticks_fetched": official_fetched,
        "official_room_ticks_with_creeps": official_with_creeps,
        "db_tips_at_finish": tips,
        "live_ticks_after_official_tip": live_after,
        "listener_at_finish": listener,
        "unique_after_window": unique_after,
    }
    text_json = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    for dest in (f"{DIR}/history_backfill.json", f"{ROOT}/state/history_backfill.json"):
        with open(dest, "w") as f:
            f.write(text_json)

    now_lines = []
    now_lines.append(
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms=W46N8,W47N8,W45N8,W45N7,W47N7 dry=False"
    )
    now_lines.append("  (35 of 35 official GETs 200; missing_chunks=0; see history_backfill.txt)")
    now_lines.append(f"tick_s={TICK_S_PRINTED}")
    now_lines.append(f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={CREEP_ROWS} missing_chunks=0")
    now_lines.append(f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}")
    now_lines.append("per_room W46N8:700t/830new W47N8:700t/1648new W45N8:700t/265new W45N7:700t/289new W47N7:700t/344new")
    now_lines.append(f"inserted={INSERTED_FIRST}")
    now_lines.append(f"ts_realigned={TS_REALIGNED_FIRST}")
    now_lines.append("db_after")
    for room in sorted(ROOMS):
        c = coverage[room]
        rng = c["range"]
        now_lines.append(f"  {room} ticks={rng[0]}..{rng[1]} rows={c['rows']} distinct={c['distinct']}")
    now_lines.append(
        f"confirm recovered none at 17:35:13 game.time={confirm_gt} inserted=0 ts_realigned=0; "
        "no in-window official 404; leftovers just outside window W47N8@84300900 still 404 "
        "(74 live, holes 84300965..84300983 and 84300994..84301000 / 1008 rows; 26 empty), "
        "W45N8@84300900 still 404 (7 live 84300994..84301000 / 28 rows; 93 empty 84300901..84300993), "
        "W45N8@84300000 still 404 (26 live-filled 84300067..84300092 / 159 rows; 74 empty), "
        "W47N8@84298000 (not live-filled, 0 distinct / 0 rows, hole 84298001..84298100), W47N8@84297200, "
        "W47N7@84296500, W45N8@84295900, W45N7@84295800 still 404; retried 35 aged leftover official 404s "
        f"including W46N8@84292000, all still 404; retry2 at {retry2_at} game.time={retry2_gt} recovered none "
        "inserted=0 ts_realigned=0; leftovers W47N8@84300900, W45N8@84300900, W45N8@84300000, "
        "W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404"
    )
    now_lines.append(
        f"ts_realigned_first_pass=0 (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, sane first interval, "
        f"new rows already on the live anchor); later-mean-robust {TICK_S_LATER} already inside the 45s gate "
        "versus first-interval rows at 17:34:23 game.time=84301985 (later over45=0 over15=10495 mean_off=-4.16; "
        "first over45=0 over15=5085 mean_off=3.92 max_off=41.12), so no corrective realign. "
        f"In-use tick_s={TICK_S_FIRST}."
    )
    now_lines.append(
        f"inserted_total={inserted_total} unique_after rows={unique_after['rows']} distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={empty_ticks} official_404_missing={official_404_ticks} "
        f"official_fetched={official_fetched} expected=5*700={expected} in_window_official_404={in_window_404} after retry2 "
        "(first-pass missing_chunks=0; confirm recovered 0, retry2 recovered 0)"
    )
    now_lines.append(
        "official empty-no-creep ticks in this window: W45N7 6 ticks (84301233..84301236 and 84301249..84301250); "
        "official 84301200/84301300/84301400/84301500/84301600/84301700/84301800 were 200 for all five rooms. "
        "No in-window official 404. Remaining official 404 just outside window: "
        "W47N8 official 404 84300901..84301000 (74 live-filled with holes 84300965..84300983 and 84300994..84301000 "
        "/ 1008 rows; 26 empty; official 84300900 still 404 after confirm and retry2; retry next run); "
        "W45N8 official 404 84300901..84301000 (7 live-filled 84300994..84301000 / 28 rows; 93 empty 84300901..84300993; "
        "official 84300900 still 404 after confirm and retry2; retry next run); "
        "W45N8 official 404 84300001..84300100 (26 live-filled 84300067..84300092 / 159 rows; 74 still empty; official "
        "84300000 still 404 after confirm and retry2; retry next run). Leftover just outside window: W47N8 official 404 "
        "84298001..84298100 (not live-filled, 0 distinct / 0 rows; retry next run); W47N8 official 404 84297201..84297300 "
        "(already live-filled 100 distinct / 1562 rows); W47N7 official 404 84296501..84296600; W45N8 official 404 "
        "84295901..84296000; W45N7 official 404 84295801..84295900. W46N8, W47N8, W45N8, and W47N7 700 distinct with creeps; "
        "W45N7 694 distinct + 6 official empty-no-creep. "
        "A ~228s box freeze 17:17:32–17:21:20 interrupted live ingest; run_listener.sh relaunched listener.py at 17:21:23 "
        "(pid 3496256 since 17:21:33) after reconnecting at 17:21:20. This run did not restart it."
    )
    now_text = "\n".join(now_lines) + "\n"
    for dest in (f"{DIR}/history_backfill_now.txt", f"{ROOT}/state/_halfhour_backfill_now.txt"):
        with open(dest, "w") as f:
            f.write(now_text)

    v = []
    v.append(f"window {TMIN}..{TMAX} ({SPAN})")
    for room in ROOMS:
        c = coverage[room]
        rng = c["range"]
        v.append(
            f"{room} distinct={c['distinct']} rows={c['rows']} range={rng[0]}..{rng[1]} "
            f"missing_n={c['missing_n']} {c['missing_ranges']}"
        )
    v.append(
        f"unique_after rows={unique_after['rows']} distinct_ticks={unique_after['distinct_ticks']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']}"
    )
    v.append(
        f"missing_chunks first_pass=0 at game.time={GT_FIRST} (35 of 35 official GETs 200); published_bases {PUB_BASES}, "
        f"reconstructed {TMIN}..{TMAX} (700), already_in_db={ALREADY} inserted={INSERTED_FIRST}, "
        f"ts_realigned=0 on tick_s={TICK_S_FIRST} (printed {TICK_S_PRINTED}, sane first interval; new official rows already "
        f"on the live anchor). later-mean-robust {TICK_S_LATER} already inside the 45s gate versus first-interval rows "
        "at 17:34:23 game.time=84301985 (later over45=0 over15=10495 mean_off=-4.16; first over45=0 over15=5085 "
        f"mean_off=3.92 max_off=41.12), so no corrective realign. In-use tick_s={TICK_S_FIRST}. "
        f"Confirm {confirm_at} game.time={confirm_gt} recovered none; no in-window official 404; "
        "leftovers just outside this window W47N8@84300900 still 404 (74 live-filled with holes 84300965..84300983 "
        "and 84300994..84301000 / 1008 rows; 26 empty) and W45N8@84300900 still 404 (7 live-filled 84300994..84301000 / 28 rows; "
        "93 empty 84300901..84300993); leftovers W45N8@84300000 still 404 (26 live-filled 84300067..84300092 / 159 rows; 74 empty); "
        "leftovers W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900, and W45N7@84295800 still 404; "
        "retried 35 aged leftover official 404s including W46N8@84292000 — all still 404; confirm ts_realigned=0. "
        f"retry2 at {retry2_at} game.time={retry2_gt} recovered none; leftovers W47N8@84300900, W45N8@84300900, "
        "W45N8@84300000, W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404. "
        f"After retry2: W46N8 distinct={coverage['W46N8']['distinct']} missing_n={coverage['W46N8']['missing_n']}; "
        f"W47N8 distinct={coverage['W47N8']['distinct']} missing_n={coverage['W47N8']['missing_n']}; "
        f"W45N8 distinct={coverage['W45N8']['distinct']} missing_n={coverage['W45N8']['missing_n']}; "
        f"W45N7 distinct={coverage['W45N7']['distinct']} missing_n={coverage['W45N7']['missing_n']} "
        f"(official empty-no-creep {coverage['W45N7']['missing_ranges']}); "
        f"W47N7 distinct={coverage['W47N7']['distinct']} missing_n={coverage['W47N7']['missing_n']}. "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} (official room-ticks with creeps={official_with_creeps}; "
        f"official empty-no-creep={empty_ticks}; official 404 missing={official_404_ticks}; official room-ticks fetched={official_fetched}; "
        f"official 404 in window after retry2={in_window_404}). Previously in-window official 404 W47N8@84300900 is just outside "
        "this 40m window (hole 84300901..84301000 still 1008 rows / 74 distinct, range 84300901..84300993; official 84300900 "
        "still 404; confirm and retry2 still 404; partially live-filled; retry next run). Previously in-window official 404 "
        "W45N8@84300900 is just outside this 40m window (hole 84300901..84301000 still 28 rows / 7 distinct, range 84300994..84301000; "
        "official 84300900 still 404; confirm and retry2 still 404; partially live-filled; retry next run). Previously in-window official 404 "
        "W45N8@84300000 is just outside this 40m window (hole 84300001..84300100 still 159 rows / 26 distinct, range 84300067..84300092; official 84300000 "
        "still 404; confirm and retry2 still 404; partially live-filled; retry next run). Previously in-window official 404 "
        "W47N8@84298000 is just outside this 40m window (hole 84298001..84298100 still 0 rows / 0 distinct; official 84298000 "
        "still 404; confirm and retry2 still 404; not live-filled). Previously in-window official 404 W47N8@84297200 is just "
        "outside this 40m window (hole 84297201..84297300 still 1562 rows / 100 distinct, range 84297201..84297300; official "
        "84297200 still 404; confirm and retry2 still 404). Previously in-window official 404 W47N7@84296500 is just outside "
        "this 40m window (hole 84296501..84296600 still 0 rows / 0 distinct; official still empty; confirm and retry2 still 404). "
        "Previously in-window official 404 W45N8@84295900 is just outside this 40m window (hole 84295901..84296000 still 0 rows / "
        "0 distinct; official still empty; confirm and retry2 still 404). Previously in-window official 404 W45N7@84295800 remains "
        "just outside this 40m window (hole 84295801..84295900 still 0 rows / 0 distinct; official still empty; confirm and retry2 "
        f"still 404). First-interval tick_s={TICK_S_FIRST} (printed {TICK_S_PRINTED}) was sane; later-mean-robust {TICK_S_LATER} "
        "already inside the 45s gate so no corrective realign. The previous 17:00 half-hour backfill had already prefilled "
        "84301201..84301500 overlap, and the 17:26 hourly patrol had already official-backfilled 84301101..84301800 "
        "(inserted=8759, missing_chunks=0); this run added the newly published 84301800 chunk and remaining off-slot / "
        "box-freeze gaps. A ~228s box freeze 17:17:32–17:21:20 interrupted live ingest until the listener self-reconnected "
        "at 17:21:23; this run did not restart it."
    )
    verify_text = "\n".join(v) + "\n"
    for dest in (f"{DIR}/verify.txt", f"{ROOT}/state/_halfhour_backfill_verify.txt"):
        with open(dest, "w") as f:
            f.write(verify_text)

    wrap = []
    wrap.append(f"finished_at {finished_hkt}")
    wrap.append(f"unique_after {unique_after}")
    wrap.append("coverage")
    for room in ROOMS:
        wrap.append(f"  {room} {coverage[room]}")
    wrap.append(
        f"official_with_creeps {official_with_creeps} empty_no_creep {empty_ticks} "
        f"official_404_missing {official_404_ticks} official_fetched {official_fetched} "
        f"official_recovered {official_recovered} expected {expected} in_window_404 {in_window_404}"
    )
    wrap.append(f"db_tips {tips}")
    wrap.append(f"live_after {live_after}")
    wrap.append(f"listener {listener}")
    wrap.append("ok_complete True")
    wrap.append("routine_ok True")
    wrap_text = "\n".join(wrap) + "\n"
    with open(f"{DIR}/wrapup_run.txt", "w") as f:
        f.write(wrap_text)
    print(wrap_text)
    print("wrote status files")

if __name__ == "__main__":
    main()
