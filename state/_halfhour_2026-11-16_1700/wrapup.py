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
DIR = f"{ROOT}/state/_halfhour_2026-11-16_1700"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84300801, 84301500
SPAN = TMAX - TMIN + 1  # 700
# Official 404 chunks in this window (confirm + retry2 still 404)
IN_WINDOW_404 = {("W47N8", 84300900), ("W45N8", 84300900)}

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
    # official chunk base N covers ticks N+1 .. N+100
    return ((tick - 1) // 100) * 100

def now_hk():
    return datetime.now(TZ)

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
            "Existing run_listener.sh loop relaunched listener.py at 17:01:22 after "
            "'box frozen ~712s since 2026-11-16 16:49:15' (reconnecting at 17:01:18; "
            "old pid 3481079 from 16:38:43 gone; new pid 3488865 since 17:01:31). "
            "This backfill did not kill or start a listener."
        ),
    }

def main():
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
    official_fetched = 5 * SPAN - 200  # two in-window official 404 chunks
    official_recovered = official_with_creeps + empty_ticks
    expected = 5 * SPAN
    in_window_404 = 2

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

    first_new = {"W46N8": 2639, "W47N8": 4665, "W45N8": 1878, "W45N7": 865, "W47N7": 1484}
    first_official_ticks = {"W46N8": 700, "W47N8": 600, "W45N8": 600, "W45N7": 700, "W47N7": 700}
    per_room = {}
    for room in ROOMS:
        c = coverage[room]
        per_room[room] = {
            "ticks": first_official_ticks[room],
            "ticks_official": first_official_ticks[room],
            "new": first_new[room],
            "new_first_pass": first_new[room],
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

    known_in = [
        leftover_desc(
            "W47N8@84300900",
            "official 404 after confirm and retry2; live-filled 74 ticks with holes "
            "84300965..84300983 (19) and 84300994..84301000 (7); 26 official-missing; retry next run)",
        ),
        leftover_desc(
            "W45N8@84300900",
            "official 404 after confirm and retry2; live-filled 7 ticks 84300994..84301000 / 28 rows; "
            "93 empty 84300901..84300993; retry next run)",
        ),
    ]
    known_out = [
        leftover_desc(
            "W45N8@84300000",
            "just outside this 40m window, still 404, partially live-filled "
            "(26 live 84300067..84300092 / 159 rows; 74 empty); retry next run)",
        ),
        leftover_desc(
            "W47N8@84298000",
            "just outside this 40m window, still 404, not live-filled; retry next run)",
        ),
        leftover_desc(
            "W47N8@84297200",
            "just outside this 40m window, still 404, already live-filled 100 distinct; retry next run)",
        ),
        leftover_desc(
            "W47N7@84296500",
            "just outside this 40m window, still 404, not live-filled; retry next run)",
        ),
        leftover_desc(
            "W45N8@84295900",
            "just outside this 40m window, still 404, not live-filled; retry next run)",
        ),
        leftover_desc(
            "W45N7@84295800",
            "just outside this 40m window, still 404, not live-filled; retry next run)",
        ),
    ]

    empty_ranges = {r: empty_no_creep[r]["ranges"] for r in ROOMS if empty_no_creep[r]["n"]}
    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": finished.isoformat(),
        "finished_at_hkt": finished_hkt,
        "shard": "shard3",
        "rooms": list(ROOMS),
        "minutes": 40,
        "game_time": 84301585,
        "live_json_gameTime_at_finish": listener.get("live_gameTime"),
        "live_json_stats_t_at_finish": listener.get("live_stats_t"),
        "live_json_gameTime_note": (
            "Listener had already self-reconnected before this run: box freeze ~712s from "
            "2026-11-16 16:49:15 to 17:01:19 Asia/Hong_Kong, listener reconnecting at 17:01:18, "
            "run_listener.sh relaunched listener.py at 17:01:22 (pid 3488865 since 17:01:31; "
            "previous pid 3481079 from 16:38:43 exited). This 17:00 half-hour backfill did not "
            "kill or restart the listener, war_cmd, or pulse, and did not start a second listener. "
            "yield_files=absent; peacetime single-slot rotation W46N8:W47N8:W45N8:W45N7=5:5:1:1 unchanged. "
            "live.json was fresh at precheck (age 1.5s, roomSlot W46N8, gameTime=84301580, stats.t=84301580, objects=261). "
            "After reconnect, creep_cpu/path_arrivals buffers were already current "
            "(precheck last200ticks 84301370..84301570 / 84301342..84301530). "
            "The previous 16:30 half-hour backfill had official-backfilled 84300401..84301100 "
            "(inserted=2877, missing_chunks=2 W47N8@84300900 and W45N8@84300900). "
            "No concurrent hourly patrol was running during this backfill."
        ),
        "published_bases": "84300800..84301400",
        "ticks": {"min": TMIN, "max": TMAX, "count": SPAN},
        "tick_s": 4.85064,
        "tick_s_later_mean": 4.75978,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "missing_chunks": 2,
        "missing_chunk_list": ["W47N8@84300900", "W45N8@84300900"],
        "missing_chunk_first_pass": ["W47N8@84300900", "W45N8@84300900"],
        "missing_chunk_note": (
            "First pass (game.time=84301585) published_bases 84300800..84301400, reconstructed "
            "84300801..84301500 (700). missing_chunks=2 (33 of 35 official GETs 200; 404 W47N8@84300900 "
            "and W45N8@84300900). confirm at 2026-11-16 17:04:30 Asia/Hong_Kong game.time=84301610 and "
            "retry2 at 2026-11-16 17:10:36 Asia/Hong_Kong game.time=84301687 recovered none. "
            "In-window official 404s remain W47N8@84300900 and W45N8@84300900. Leftovers just outside "
            "this window: W45N8@84300000 (26 live + 74 empty), W47N8@84298000 (still empty), "
            "W47N8@84297200 (already live-filled), W47N7@84296500, W45N8@84295900, and W45N7@84295800 "
            "still 404; retried 35 aged leftover official 404s including W46N8@84292000, all still 404."
        ),
        "creep_rows_reconstructed": 24131,
        "already_in_db": 12600,
        "inserted": 11531,
        "inserted_first_pass": 11531,
        "inserted_retry": 0,
        "inserted_retry2": 0,
        "inserted_note": (
            "The previous 16:30 Asia/Hong_Kong half-hour backfill prefilled official 84300401..84301100 "
            "(inserted_total=2877, already_in_db=21516, first-pass missing_chunks=2 W47N8@84300900 and "
            "W45N8@84300900, tick_s=4.83409, ts_realigned=0). A later box freeze 16:49:15–17:01:19 (~712s) "
            "interrupted live ingest until the listener self-reconnected at 17:01:22. This 40-minute official "
            "history pull therefore inserted 11531 new rows (already_in_db=12600 of 24131 reconstructed) "
            "across 84300801..84301500, mainly the newly published 84301100..84301400 chunks plus rooms that "
            "were off-slot and the period covered by the box freeze. confirm and retry2 inserted 0. "
            "W46N8 and W47N7 have 700 official ticks with creeps. W45N7 official 700 ticks include 175 "
            "empty-no-creep (84300847, 84300849..84301016, 84301233..84301236, and 84301249..84301250). "
            "W47N8/W45N8 official 84300900 remain 404 (partially live-filled)."
        ),
        "ts_realigned": 12275,
        "ts_realigned_corrective_later_mean": 11082,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": (
            "First pass (tick_s=4.85064 printed 4.851, live anchor game.time=84301585) reported "
            "ts_realigned=12275 (new official rows realigned onto the live-anchor first-interval tick_s). "
            "The script's tick_seconds() uses the first interval between published chunk bases "
            "(min timestamp across rooms, which was W46N8 on every base this window). later-mean-robust "
            "of the remaining W46N8 intervals is 4.75978 (raw later-mean 4.75978; delta first-robust "
            "0.09086 s/tick, ~71.2s at tmin vs gt_first). At 17:03:53 Asia/Hong_Kong game.time=84301602, "
            "first-interval was just outside the 45s gate (over45=258, over15=1794, mean_off=4.01, max_off=46.58) "
            "and later-mean-robust was over the 45s gate versus the then-current first-interval rows "
            "(over45=10254, over15=20792, mean_off=-36.99). First-interval 4.85064 is in the sane 3-6s band; "
            "a corrective later-mean-robust realign of 11082 rows was applied at game.time=84301602; "
            "after that, still_over_45s_vs_later=0 (over15=10481, mean_off=-13.24, min_off=-44.97) and "
            "was kept (not reverted; after over45=0 was not worse than first). prev_later 4.83768 also had "
            "over45=0 at the pre-corrective check (over15=1794, mean_off=-1.84) but the standing procedure "
            "applies later-mean-robust when first-pass rows are over the 45s gate versus later-mean. "
            "In-use tick_s after corrective is later-mean-robust 4.75978."
        ),
        "ssl_first_attempt": "ok first try",
        "hourly_patrol_prefilled": (
            "No concurrent hourly patrol ran during this backfill (last 1h patrol was the 16:20 Asia/Hong_Kong run). "
            "The previous 16:30 half-hour backfill had prefilled 84300401..84301100 (inserted=2877, tick_s=4.83409, "
            "ts_realigned=0, first-pass missing_chunks=2 W47N8@84300900 and W45N8@84300900). A box freeze "
            "16:49:15–17:01:19 (~712s) interrupted live ingest until the listener self-reconnected at 17:01:22. "
            "Official history in this window covers 84300800..84301400 except the two still-unpublished 84300900 "
            "chunks for W47N8 and W45N8."
        ),
        "per_room": per_room,
        "known_official_404s_outside_window": known_out,
        "known_official_404s_in_window": known_in,
        "w45n7_empty_no_creep_in_window": True,
        "w45n7_empty_no_creep_ranges": empty_no_creep["W45N7"]["ranges"],
        "empty_no_creep_in_window": True,
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

    # history_backfill_now.txt (brief status for the next hourly patrol)
    now_lines = []
    now_lines.append(
        "game.time=84301585 published_bases=84300800..84301400 rooms=W46N8,W47N8,W45N8,W45N7,W47N7 dry=False"
    )
    now_lines.append(
        "  (33 of 35 official GETs 200; 404 W47N8@84300900 and W45N8@84300900; see history_backfill.txt)"
    )
    now_lines.append("tick_s=4.851")
    now_lines.append("reconstructed ticks=84300801..84301500 (700) creep_rows=24131 missing_chunks=2")
    now_lines.append("already_in_db=12600 would_insert=11531")
    now_lines.append("per_room W46N8:700t/2639new W47N8:600t/4665new W45N8:600t/1878new W45N7:700t/865new W47N7:700t/1484new")
    now_lines.append("inserted=11531")
    now_lines.append("ts_realigned=12275")
    now_lines.append("db_after")
    for room in sorted(ROOMS):
        c = coverage[room]
        rng = c["range"]
        now_lines.append(
            f"  {room} ticks={rng[0]}..{rng[1]} rows={c['rows']} distinct={c['distinct']}"
        )
    now_lines.append(
        "confirm recovered none at 17:04:30 game.time=84301610 inserted=0 ts_realigned=0; "
        "in-window official 404 W47N8@84300900 (74 live, holes 84300965..84300983 and 84300994..84301000) "
        "and W45N8@84300900 (7 live 84300994..84301000 / 28 rows; 93 empty 84300901..84300993) still 404; "
        "leftovers just outside window W45N8@84300000 still 404 (26 live-filled 84300067..84300092 / 159 rows; 74 empty), "
        "W47N8@84298000 (not live-filled, 0 distinct / 0 rows, hole 84298001..84298100), W47N8@84297200, "
        "W47N7@84296500, W45N8@84295900, W45N7@84295800 still 404; retried 35 aged leftover official 404s "
        "including W46N8@84292000, all still 404; retry2 at 17:10:36 game.time=84301687 recovered none "
        "inserted=0 ts_realigned=0; leftovers W47N8@84300900, W45N8@84300900, W45N8@84300000, "
        "W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404"
    )
    now_lines.append(
        "ts_realigned_first_pass=12275 (tick_s=4.85064 printed 4.851, sane first interval, new rows realigned "
        "onto the live anchor); later-mean-robust 4.75978 was over the 45s gate versus first-interval rows "
        "at 17:03:53 game.time=84301602 (later over45=10254 over15=20792 mean_off=-36.99; first over45=258 "
        "over15=1794 mean_off=4.01 max_off=46.58), so a corrective later-mean-robust realign of 11082 rows "
        "was applied (after over45=0 over15=10481 mean_off=-13.24; not reverted). In-use tick_s=4.75978."
    )
    now_lines.append(
        f"inserted_total=11531 unique_after rows={unique_after['rows']} distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={empty_ticks} official_404_missing={official_404_ticks} "
        f"official_fetched={official_fetched} expected=5*700={expected} in_window_official_404={in_window_404} after retry2 "
        "(first-pass missing_chunks=2 W47N8@84300900 and W45N8@84300900; confirm recovered 0, retry2 recovered 0)"
    )
    now_lines.append(
        "official empty-no-creep ticks in this window: W45N7 175 ticks (84300847, 84300849..84301016, "
        "84301233..84301236, and 84301249..84301250); official 84300800/84300900/84301000/84301200/84301300 were 200. "
        "In-window official 404: W47N8 official 404 84300901..84301000 (74 live-filled with holes 84300965..84300983 "
        "and 84300994..84301000 / 1008 rows; 26 empty; official 84300900 still 404 after confirm and retry2; retry next run); "
        "W45N8 official 404 84300901..84301000 (7 live-filled 84300994..84301000 / 28 rows; 93 empty 84300901..84300993; "
        "official 84300900 still 404 after confirm and retry2; retry next run). Remaining official 404 just outside window: "
        "W45N8 official 404 84300001..84300100 (26 live-filled 84300067..84300092 / 159 rows; 74 still empty; official "
        "84300000 still 404 after confirm and retry2; retry next run). Leftover just outside window: W47N8 official 404 "
        "84298001..84298100 (not live-filled, 0 distinct / 0 rows; retry next run); W47N8 official 404 84297201..84297300 "
        "(already live-filled 100 distinct / 1562 rows); W47N7 official 404 84296501..84296600; W45N8 official 404 "
        "84295901..84296000; W45N7 official 404 84295801..84295900. W46N8 and W47N7 700 distinct with creeps; "
        "W45N7 525 distinct + 175 official empty-no-creep."
    )
    now_text = "\n".join(now_lines) + "\n"
    for dest in (f"{DIR}/history_backfill_now.txt", f"{ROOT}/state/_halfhour_backfill_now.txt"):
        with open(dest, "w") as f:
            f.write(now_text)

    # verify.txt
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
        "missing_chunks first_pass=2 at game.time=84301585 (33 of 35 official GETs 200; 404 W47N8@84300900 and "
        "W45N8@84300900); published_bases 84300800..84301400, reconstructed 84300801..84301500 (700), "
        "already_in_db=12600 inserted=11531, ts_realigned=12275 on tick_s=4.85064 (printed 4.851, sane first interval; "
        "new official rows realigned onto the live anchor). later-mean-robust 4.75978 was over the 45s gate versus "
        "first-interval rows at 17:03:53 game.time=84301602 (later over45=10254 over15=20792 mean_off=-36.99; "
        "first over45=258 over15=1794 mean_off=4.01 max_off=46.58), so a corrective later-mean-robust realign of "
        "11082 rows was applied (after over45=0 over15=10481 mean_off=-13.24; not reverted). In-use tick_s=4.75978. "
        "Confirm 2026-11-16 17:04:30 Asia/Hong_Kong game.time=84301610 recovered none; in-window official 404 "
        "W47N8@84300900 still 404 (74 live-filled with holes 84300965..84300983 and 84300994..84301000 / 1008 rows; "
        "26 empty) and W45N8@84300900 still 404 (7 live-filled 84300994..84301000 / 28 rows; 93 empty 84300901..84300993); "
        "leftovers just outside this window W45N8@84300000 still 404 (26 live-filled 84300067..84300092 / 159 rows; 74 empty); "
        "leftovers W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900, and W45N7@84295800 still 404; "
        "retried 35 aged leftover official 404s including W46N8@84292000 — all still 404; confirm ts_realigned=0. "
        "retry2 at 17:10:36 game.time=84301687 recovered none; leftovers W47N8@84300900, W45N8@84300900, "
        "W45N8@84300000, W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404. "
        f"After retry2: W46N8 distinct=700 missing_n=0; W47N7 distinct=700 missing_n=0; W47N8 distinct=674 missing_n=26 "
        f"(official 404 hole); W45N8 distinct=607 missing_n=93 (official 404 hole); W45N7 distinct=525 missing_n=175 "
        f"(official empty-no-creep 84300847, 84300849..84301016, 84301233..84301236, and 84301249..84301250). "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} (official room-ticks with creeps={official_with_creeps}; "
        f"official empty-no-creep={empty_ticks}; official 404 missing={official_404_ticks}; official room-ticks fetched={official_fetched}; "
        f"official 404 in window after retry2={in_window_404}). In-window official 404 W47N8@84300900 remains "
        "(hole 84300901..84301000, 74 live with two holes, official still 404 after confirm and retry2; retry next run). "
        "In-window official 404 W45N8@84300900 remains (hole 84300901..84301000, 7 live 84300994..84301000, official still "
        "404 after confirm and retry2; retry next run). Previously in-window official 404 W45N8@84300000 is just outside "
        "this 40m window (hole 84300001..84300100 still 159 rows / 26 distinct, range 84300067..84300092; official 84300000 "
        "still 404; confirm and retry2 still 404; partially live-filled; retry next run). Previously in-window official 404 "
        "W47N8@84298000 is just outside this 40m window (hole 84298001..84298100 still 0 rows / 0 distinct; official 84298000 "
        "still 404; confirm and retry2 still 404; not live-filled). Previously in-window official 404 W47N8@84297200 is just "
        "outside this 40m window (hole 84297201..84297300 still 1562 rows / 100 distinct, range 84297201..84297300; official "
        "84297200 still 404; confirm and retry2 still 404). Previously in-window official 404 W47N7@84296500 is just outside "
        "this 40m window (hole 84296501..84296600 still 0 rows / 0 distinct; official still empty; confirm and retry2 still 404). "
        "Previously in-window official 404 W45N8@84295900 is just outside this 40m window (hole 84295901..84296000 still 0 rows / "
        "0 distinct; official still empty; confirm and retry2 still 404). Previously in-window official 404 W45N7@84295800 remains "
        "just outside this 40m window (hole 84295801..84295900 still 0 rows / 0 distinct; official still empty; confirm and retry2 "
        "still 404). First-interval tick_s=4.85064 (printed 4.851) was sane; later-mean-robust 4.75978 was over the 45s gate "
        "versus first-interval rows so a corrective realign of 11082 rows was applied and kept. The previous 16:30 half-hour "
        "backfill had already prefilled 84300801..84301100 overlap (plus earlier live/patrol rows); this run added the newly "
        "published 84301100..84301400 chunks and off-slot / box-freeze gaps. A ~712s box freeze 16:49:15–17:01:19 interrupted "
        "live ingest until the listener self-reconnected at 17:01:22; this run did not restart it."
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
