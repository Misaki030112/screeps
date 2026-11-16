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
DIR = f"{ROOT}/state/_halfhour_2026-11-16_1800"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84301601, 84302300
SPAN = TMAX - TMIN + 1  # 700
# First-pass official 404 inside this reconstructed window; confirm/retry2 may recover it.
IN_WINDOW_404 = {("W45N8", 84302200)}
GT_FIRST = 84302333
PUB_BASES = "84301600..84302200"
TICK_S_FIRST = 4.78159
TICK_S_PRINTED = "4.782"
TICK_S_LATER = 4.81473
INSERTED_FIRST = 11984
ALREADY = 14216
CREEP_ROWS = 26200
TS_REALIGNED_FIRST = 0
TS_REALIGNED_CORRECTIVE = 2465
FIRST_NEW = {"W46N8": 2891, "W47N8": 4695, "W45N8": 1181, "W45N7": 1535, "W47N7": 1682}
FIRST_OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 600, "W45N7": 700, "W47N7": 700}
MISSING_CHUNKS_FIRST = 1
MISSING_CHUNK_LIST = ["W45N8@84302200"]
TICK_S_CHECK_AT = "18:04:19"
TICK_S_CHECK_GT = 84302359
TICK_S_REALIGN_GT = 84302360
VS_FIRST = "over45=0 over15=3587 mean_off=-0.53 max_off=34.16"
VS_LATER_BEFORE = "over45=1930 over15=5632 mean_off=13.03 max_off=59.27"
VS_LATER_AFTER = "over45=0 over15=5709 mean_off=10.98 max_off=44.96"

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
            "NEW this period: box freeze ~475s from 2026-11-16 17:49:54 to 17:57:59 Asia/Hong_Kong "
            "(listener reconnecting at 17:57:58); existing run_listener.sh relaunched listener.py "
            "at 17:58:02 (pid 3512701 since 17:58:11; previous pid 3496256 from 17:21:33 exited). "
            "Earlier the same afternoon: freeze 17:17:32–17:21:20 (~228s) relaunched at 17:21:23 "
            "(pid 3496256 since 17:21:33). This backfill did not kill or start a listener."
        ),
    }

def fmt_ranges(rr):
    if not rr:
        return ""
    parts = []
    for a, b in rr:
        parts.append(f"{a}..{b}" if a != b else str(a))
    return ", ".join(parts)

def main():
    conf = load_confirm()
    confirm_at = conf.get("confirm_at") or conf.get("at") or "2026-11-16 18:04:47 Asia/Hong_Kong"
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
    still_404_retry2 = set(conf.get("retry2_still_404") or r2.get("still_404") or [])
    recovered_any = set(confirm_rec or []) | set(retry2_rec or [])
    remaining_404 = set()
    for room, base in IN_WINDOW_404:
        key = f"{room}@{base}"
        if key in recovered_any and key not in still_404_retry2:
            continue
        remaining_404.add((room, base))

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
                    is_404 = (room, chunk_base(t)) in remaining_404 or (room, chunk_base(t)) in IN_WINDOW_404
                    # If this tick is still missing and its base was an official 404 (and not recovered), count as 404.
                    if is_404 and (room, chunk_base(t)) in remaining_404:
                        n404 += 1
                        if cur_404 is None:
                            if cur_empty is not None:
                                miss_empty.append(cur_empty); cur_empty = None
                            cur_404 = [t, t]
                        else:
                            cur_404[1] = t
                    elif is_404 and (room, chunk_base(t)) not in remaining_404:
                        # recovered officially; remaining missing ticks would be empty-no-creep
                        nempty += 1
                        if cur_empty is None:
                            if cur_404 is not None:
                                miss_404.append(cur_404); cur_404 = None
                            cur_empty = [t, t]
                        else:
                            cur_empty[1] = t
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
            ("W45N8", 84302201, 84302300),
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
    official_fetched = 5 * SPAN - 100 * len(IN_WINDOW_404)  # first-pass official 200 room-ticks
    if recovered_any & set(MISSING_CHUNK_LIST):
        # recovered chunk(s) later became official 200; fetched count rises by 100 per recovered base
        official_fetched += 100 * len(recovered_any & set(MISSING_CHUNK_LIST))
    official_recovered = official_with_creeps + empty_ticks
    expected = 5 * SPAN
    in_window_404 = official_404_ticks

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
        "in_window_official_404_bases": sorted(f"{r}@{b}" for r, b in remaining_404),
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

    w45_in = leftovers.get("W45N8@84302200", {})
    w45_in_txt = (
        f"{w45_in.get('rows', 0)} rows / {w45_in.get('distinct', 0)} distinct, "
        f"range {w45_in.get('min')}..{w45_in.get('max')}"
    )
    in_window_still = "W45N8@84302200" in still_404_retry2 or (
        "W45N8@84302200" not in recovered_any and ("W45N8", 84302200) in remaining_404
    )
    known_in = []
    if in_window_still:
        known_in.append(leftover_desc(
            "W45N8@84302200",
            "in-window first-pass official 404, still 404 after confirm and retry2; "
            "not live-filled at wrapup" if (w45_in.get("distinct") or 0) == 0
            else f"in-window first-pass official 404, still 404 after confirm and retry2; partially live-filled; retry next run",
        ))
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
    empty_note_parts = []
    for r in ROOMS:
        if empty_no_creep[r]["n"]:
            empty_note_parts.append(f"{r} {empty_no_creep[r]['n']} ticks ({fmt_ranges(empty_no_creep[r]['ranges'])})")
    empty_note = "; ".join(empty_note_parts) if empty_note_parts else "none"
    inserted_total = INSERTED_FIRST + (confirm_ins or 0) + (retry2_ins or 0)
    confirm_rec_txt = confirm_rec or "none"
    retry2_rec_txt = retry2_rec or "none"
    inwin_404_txt = (
        "in-window official 404 W45N8@84302200 still 404 after confirm and retry2 "
        f"({w45_in_txt}; hole 84302201..84302300; retry next run)"
        if in_window_still else
        f"in-window official 404 W45N8@84302200 recovered ({recovered_any})"
    )
    leftover_short = (
        "leftovers just outside window W47N8@84300900 still 404 "
        "(74 live, holes 84300965..84300983 and 84300994..84301000 / 1008 rows; 26 empty), "
        "W45N8@84300900 still 404 (7 live 84300994..84301000 / 28 rows; 93 empty 84300901..84300993), "
        "W45N8@84300000 still 404 (26 live-filled 84300067..84300092 / 159 rows; 74 empty), "
        "W47N8@84298000 (not live-filled, 0 distinct / 0 rows, hole 84298001..84298100), W47N8@84297200, "
        "W47N7@84296500, W45N8@84295900, W45N7@84295800 still 404"
    )

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
            "Listener had already self-reconnected before this run: NEW box freeze ~475s from "
            "2026-11-16 17:49:54 to 17:57:59 Asia/Hong_Kong, listener reconnecting at 17:57:58, "
            "run_listener.sh relaunched listener.py at 17:58:02 (pid 3512701 since 17:58:11; "
            "previous pid 3496256 from 17:21:33 exited). This 18:00 half-hour backfill did not "
            "kill or restart the listener, war_cmd, or pulse, and did not start a second listener. "
            "yield_files=absent; peacetime single-slot rotation W46N8:W47N8:W45N8:W45N7=5:5:1:1 unchanged. "
            "live.json was fresh at precheck 18:01:55 (age 0.5s, roomSlot W46N8, gameTime=84302329, stats.t=84302320, objects=266). "
            "After reconnect, creep_cpu buffers had already been replayed at 17:58:13 (ticks 84302175..84302280); "
            "room_stats still shows a live dark gap 84302171..84302289 (last pre-freeze 84302170 at 17:49:08, "
            "first post-reconnect 84302290 at 17:58:47). Official history filled that creep_ticks gap for "
            "W46N8, W47N8, W45N7, and W47N7; W45N8 official 84302100 was 200 (through 84302200) but "
            "official 84302200 was 404, so 84302201..84302300 was not officially filled. "
            "The previous 17:30 half-hour backfill had official-backfilled 84301201..84301900 "
            "(inserted=3376, missing_chunks=0, tick_s=4.76419, no corrective realign)."
        ),
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": SPAN},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": TICK_S_LATER,
        "tick_s_in_use": TICK_S_LATER,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": True,
        "missing_chunks": MISSING_CHUNKS_FIRST if in_window_still else 0,
        "missing_chunk_list": MISSING_CHUNK_LIST if in_window_still else [],
        "missing_chunk_first_pass": MISSING_CHUNK_LIST,
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed "
            f"{TMIN}..{TMAX} (700). missing_chunks=1 of 35 official GETs (34 of 35 200; "
            f"404 {', '.join(MISSING_CHUNK_LIST)}). "
            f"confirm at {confirm_at} game.time={confirm_gt} recovered {confirm_rec_txt} "
            f"inserted={confirm_ins} ts_realigned={confirm_nfix}. "
            f"retry2 at {retry2_at} game.time={retry2_gt} recovered {retry2_rec_txt} "
            f"inserted={retry2_ins} ts_realigned={retry2_nfix}. "
            f"{inwin_404_txt}. Leftovers just outside this window: "
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
            "The previous 17:30 Asia/Hong_Kong half-hour backfill prefilled official 84301201..84301900 "
            "(inserted_total=3376, already_in_db=22333, first-pass missing_chunks=0, tick_s=4.76419, "
            "later-mean-robust 4.74546 inside the 45s gate so no corrective realign). "
            f"A later box freeze 17:49:54–17:57:59 (~475s) interrupted live ingest until the listener "
            f"self-reconnected at 17:58:02. This 40-minute official history pull therefore inserted "
            f"{INSERTED_FIRST} new rows (already_in_db={ALREADY} of {CREEP_ROWS} reconstructed) across "
            f"{TMIN}..{TMAX}, mainly the newly published 84301900..84302200 chunks plus the live dark gap "
            f"84302171..84302289. confirm and retry2 inserted {(confirm_ins or 0) + (retry2_ins or 0)}. "
            "W46N8, W47N8, W45N7, and W47N7 have 700 official ticks with creeps. W45N8 official first-pass "
            "covered 600 ticks (84301601..84302200); official 84302200 was 404."
        ),
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": TS_REALIGNED_CORRECTIVE,
        "ts_realigned_confirm": confirm_nfix or 0,
        "ts_realigned_retry2": retry2_nfix or 0,
        "ts_realigned_note": (
            f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) reported "
            f"ts_realigned={TS_REALIGNED_FIRST} (new official rows already on the live-anchor first-interval tick_s). "
            "The script's tick_seconds() uses the first interval between published chunk bases "
            "(min timestamp across rooms, which was W46N8 on every base except 84302000, where W45N7 was 338ms earlier; "
            "the first interval itself was still W46N8=MIN_ALL). later-mean-robust "
            f"of the remaining W46N8 intervals is {TICK_S_LATER} (raw later-mean also {TICK_S_LATER}; delta first-robust "
            "-0.03314 s/tick, ~24.3s at tmin vs gt_first). At 18:04:19 Asia/Hong_Kong game.time=84302359, "
            f"first-interval was inside the 45s gate ({VS_FIRST}) "
            f"but later-mean-robust was over the 45s gate versus first-interval-timestamped rows ({VS_LATER_BEFORE}). "
            f"Applied corrective later-mean-robust realign of {TS_REALIGNED_CORRECTIVE} rows at game.time={TICK_S_REALIGN_GT}; "
            f"after vs later {VS_LATER_AFTER}. First-interval 4.78159 is in the sane 3-6s band; realign was not reverted "
            "(after over45=0, not worse than first). In-use tick_s is later-mean-robust 4.81473."
        ),
        "ssl_first_attempt": "ok first try",
        "hourly_patrol_prefilled": (
            "The previous 17:30 Asia/Hong_Kong half-hour backfill had prefilled 84301201..84301900 "
            "(inserted=3376, missing_chunks=0, tick_s=4.76419 / later 4.74546, no corrective realign). "
            "A NEW box freeze 17:49:54–17:57:59 (~475s) interrupted live ingest until the listener "
            "self-reconnected at 17:58:02. Official history in this window covers 84301600..84302100 "
            "for all five rooms and 84302200 for four rooms (34/35 200; W45N8@84302200 404)."
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
        "new_box_freeze": {
            "from": "2026-11-16 17:49:54",
            "to": "2026-11-16 17:57:59",
            "sec": 475,
            "live_room_stats_gap": [84302171, 84302289],
            "official_fill": (
                "Official history filled creep_ticks across the live dark gap for W46N8, W47N8, W45N7, W47N7. "
                "W45N8 filled through 84302200 (official 84302100 was 200); official 84302200 404 left "
                "84302201..84302300 unfilled, including the latter part of the freeze (84302201..84302289)."
            ),
        },
        "db_tips_at_finish": tips,
        "live_ticks_after_official_tip": live_after,
        "listener_at_finish": listener,
        "unique_after_window": unique_after,
    }
    text_json = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    for dest in (f"{DIR}/history_backfill.json", f"{ROOT}/state/history_backfill.json"):
        with open(dest, "w") as f:
            f.write(text_json)

    first_pass_gets = "34 of 35 official GETs 200; missing_chunks=1 W45N8@84302200"
    now_lines = []
    now_lines.append(
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms=W46N8,W47N8,W45N8,W45N7,W47N7 dry=False"
    )
    now_lines.append(f"  ({first_pass_gets}; see history_backfill.txt)")
    now_lines.append(f"tick_s={TICK_S_PRINTED}")
    now_lines.append(f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={CREEP_ROWS} missing_chunks=1")
    now_lines.append(f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}")
    now_lines.append("per_room W46N8:700t/2891new W47N8:700t/4695new W45N8:600t/1181new W45N7:700t/1535new W47N7:700t/1682new")
    now_lines.append(f"inserted={INSERTED_FIRST}")
    now_lines.append(f"ts_realigned={TS_REALIGNED_FIRST}")
    now_lines.append("db_after")
    for room in sorted(ROOMS):
        cvr = coverage[room]
        rng = cvr["range"]
        now_lines.append(f"  {room} ticks={rng[0]}..{rng[1]} rows={cvr['rows']} distinct={cvr['distinct']}")
    now_lines.append(
        f"confirm recovered {confirm_rec_txt} at 18:04:47 game.time={confirm_gt} inserted={confirm_ins} ts_realigned={confirm_nfix}; "
        f"{inwin_404_txt}; {leftover_short}; retried 35 aged leftover official 404s "
        f"including W46N8@84292000, all still 404; retry2 at {retry2_at} game.time={retry2_gt} recovered {retry2_rec_txt} "
        f"inserted={retry2_ins} ts_realigned={retry2_nfix}; leftovers W47N8@84300900, W45N8@84300900, W45N8@84300000, "
        "W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404"
        + ("; in-window W45N8@84302200 still 404" if in_window_still else "")
    )
    now_lines.append(
        f"ts_realigned_first_pass=0 (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, sane first interval, "
        f"new rows already on the live anchor); later-mean-robust {TICK_S_LATER} was over the 45s gate "
        f"versus first-interval rows at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT} (later {VS_LATER_BEFORE}; "
        f"first {VS_FIRST}), so corrective later-mean-robust realign of {TS_REALIGNED_CORRECTIVE} rows at "
        f"game.time={TICK_S_REALIGN_GT} (after later {VS_LATER_AFTER}; not reverted). "
        f"In-use tick_s={TICK_S_LATER}."
    )
    now_lines.append(
        f"inserted_total={inserted_total} unique_after rows={unique_after['rows']} distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={empty_ticks} official_404_missing={official_404_ticks} "
        f"official_fetched={official_fetched} expected=5*700={expected} in_window_official_404={in_window_404} after retry2 "
        f"(first-pass missing_chunks=1 W45N8@84302200; confirm recovered {0 if not confirm_rec else confirm_rec}, retry2 recovered {0 if not retry2_rec else retry2_rec})"
    )
    now_lines.append(
        f"official empty-no-creep ticks in this window: {empty_note}. "
        "official 84301600/84301700/84301800/84301900/84302000/84302100 were 200 for all five rooms; "
        "official 84302200 was 200 for W46N8, W47N8, W45N7, and W47N7, and 404 for W45N8. "
        + (f"In-window official 404: W45N8 official 404 84302201..84302300 ({w45_in_txt}; official 84302200 still 404 after confirm and retry2; retry next run). " if in_window_still else "In-window official 404 W45N8@84302200 was recovered. ")
        + "Remaining official 404 just outside window: "
        "W47N8 official 404 84300901..84301000 (74 live-filled with holes 84300965..84300983 and 84300994..84301000 "
        "/ 1008 rows; 26 empty; official 84300900 still 404 after confirm and retry2; retry next run); "
        "W45N8 official 404 84300901..84301000 (7 live-filled 84300994..84301000 / 28 rows; 93 empty 84300901..84300993; "
        "official 84300900 still 404 after confirm and retry2; retry next run); "
        "W45N8 official 404 84300001..84300100 (26 live-filled 84300067..84300092 / 159 rows; 74 still empty; official "
        "84300000 still 404 after confirm and retry2; retry next run). Leftover just outside window: W47N8 official 404 "
        "84298001..84298100 (not live-filled, 0 distinct / 0 rows; retry next run); W47N8 official 404 84297201..84297300 "
        "(already live-filled 100 distinct / 1562 rows); W47N7 official 404 84296501..84296600; W45N8 official 404 "
        "84295901..84296000; W45N7 official 404 84295801..84295900. W46N8, W47N8, W45N7, and W47N7 700 distinct with creeps; "
        f"W45N8 {coverage['W45N8']['distinct']} distinct"
        + (f" + {coverage['W45N8']['official_404_missing']} official 404 missing" if coverage['W45N8']['official_404_missing'] else "")
        + (f" + {coverage['W45N8']['official_empty_no_creep']} official empty-no-creep" if coverage['W45N8']['official_empty_no_creep'] else "")
        + ". "
        "A NEW ~475s box freeze 17:49:54–17:57:59 interrupted live ingest (live room_stats gap 84302171..84302289); "
        "run_listener.sh relaunched listener.py at 17:58:02 (pid 3512701 since 17:58:11) after reconnecting at 17:57:58. "
        "Official history filled that creep_ticks dark gap for W46N8, W47N8, W45N7, and W47N7, and for W45N8 through 84302200. "
        "This run did not restart it."
    )
    now_text = "\n".join(now_lines) + "\n"
    for dest in (f"{DIR}/history_backfill_now.txt", f"{ROOT}/state/_halfhour_backfill_now.txt"):
        with open(dest, "w") as f:
            f.write(now_text)

    v = []
    v.append(f"window {TMIN}..{TMAX} ({SPAN})")
    for room in ROOMS:
        cvr = coverage[room]
        rng = cvr["range"]
        v.append(
            f"{room} distinct={cvr['distinct']} rows={cvr['rows']} range={rng[0]}..{rng[1]} "
            f"missing_n={cvr['missing_n']} {cvr['missing_ranges']}"
        )
    v.append(
        f"unique_after rows={unique_after['rows']} distinct_ticks={unique_after['distinct_ticks']} "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']}"
    )
    v.append(
        f"missing_chunks first_pass=1 at game.time={GT_FIRST} (34 of 35 official GETs 200; 404 W45N8@84302200); published_bases {PUB_BASES}, "
        f"reconstructed {TMIN}..{TMAX} (700), already_in_db={ALREADY} inserted={INSERTED_FIRST}, "
        f"ts_realigned=0 on tick_s={TICK_S_FIRST} (printed {TICK_S_PRINTED}, sane first interval; new official rows already "
        f"on the live anchor). later-mean-robust {TICK_S_LATER} was over the 45s gate versus first-interval rows "
        f"at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT} (later {VS_LATER_BEFORE}; first {VS_FIRST}), "
        f"so corrective later-mean-robust realign of {TS_REALIGNED_CORRECTIVE} rows at game.time={TICK_S_REALIGN_GT} "
        f"(after later {VS_LATER_AFTER}; not reverted). In-use tick_s={TICK_S_LATER}. "
        f"Confirm {confirm_at} game.time={confirm_gt} recovered {confirm_rec_txt}; {inwin_404_txt}; "
        "leftovers just outside this window W47N8@84300900 still 404 (74 live-filled with holes 84300965..84300983 "
        "and 84300994..84301000 / 1008 rows; 26 empty) and W45N8@84300900 still 404 (7 live-filled 84300994..84301000 / 28 rows; "
        "93 empty 84300901..84300993); leftovers W45N8@84300000 still 404 (26 live-filled 84300067..84300092 / 159 rows; 74 empty); "
        "leftovers W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900, and W45N7@84295800 still 404; "
        f"retried 35 aged leftover official 404s including W46N8@84292000 — all still 404; confirm ts_realigned={confirm_nfix}. "
        f"retry2 at {retry2_at} game.time={retry2_gt} recovered {retry2_rec_txt}; leftovers W47N8@84300900, W45N8@84300900, "
        "W45N8@84300000, W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404"
        + ("; in-window W45N8@84302200 still 404" if in_window_still else "")
        + ". "
        f"After retry2: W46N8 distinct={coverage['W46N8']['distinct']} missing_n={coverage['W46N8']['missing_n']}; "
        f"W47N8 distinct={coverage['W47N8']['distinct']} missing_n={coverage['W47N8']['missing_n']}; "
        f"W45N8 distinct={coverage['W45N8']['distinct']} missing_n={coverage['W45N8']['missing_n']}"
        + (f" (official 404 {coverage['W45N8']['missing_ranges']})" if coverage['W45N8']['official_404_missing'] else "")
        + (f" (official empty-no-creep {coverage['W45N8']['missing_ranges']})" if coverage['W45N8']['official_empty_no_creep'] and not coverage['W45N8']['official_404_missing'] else "")
        + "; "
        f"W45N7 distinct={coverage['W45N7']['distinct']} missing_n={coverage['W45N7']['missing_n']}"
        + (f" (official empty-no-creep {coverage['W45N7']['missing_ranges']})" if coverage['W45N7']['official_empty_no_creep'] else "")
        + "; "
        f"W47N7 distinct={coverage['W47N7']['distinct']} missing_n={coverage['W47N7']['missing_n']}. "
        f"distinct_room_ticks={unique_after['distinct_room_ticks']} (official room-ticks with creeps={official_with_creeps}; "
        f"official empty-no-creep={empty_ticks}; official 404 missing={official_404_ticks}; official room-ticks fetched={official_fetched}; "
        f"official 404 in window after retry2={in_window_404}). "
        "Previously leftover official 404 W47N8@84300900 is just outside this 40m window (hole 84300901..84301000 still 1008 rows / 74 distinct, range 84300901..84300993; official 84300900 "
        "still 404; confirm and retry2 still 404; partially live-filled; retry next run). Previously leftover official 404 "
        "W45N8@84300900 is just outside this 40m window (hole 84300901..84301000 still 28 rows / 7 distinct, range 84300994..84301000; "
        "official 84300900 still 404; confirm and retry2 still 404; partially live-filled; retry next run). Previously leftover official 404 "
        "W45N8@84300000 is just outside this 40m window (hole 84300001..84300100 still 159 rows / 26 distinct, range 84300067..84300092; official 84300000 "
        "still 404; confirm and retry2 still 404; partially live-filled; retry next run). Previously leftover official 404 "
        "W47N8@84298000 is just outside this 40m window (hole 84298001..84298100 still 0 rows / 0 distinct; official 84298000 "
        "still 404; confirm and retry2 still 404; not live-filled). Previously leftover official 404 W47N8@84297200 is just "
        "outside this 40m window (hole 84297201..84297300 still 1562 rows / 100 distinct, range 84297201..84297300; official "
        "84297200 still 404; confirm and retry2 still 404). Previously leftover official 404 W47N7@84296500 is just outside "
        "this 40m window (hole 84296501..84296600 still 0 rows / 0 distinct; official still empty; confirm and retry2 still 404). "
        "Previously leftover official 404 W45N8@84295900 is just outside this 40m window (hole 84295901..84296000 still 0 rows / "
        "0 distinct; official still empty; confirm and retry2 still 404). Previously leftover official 404 W45N7@84295800 remains "
        "just outside this 40m window (hole 84295801..84295900 still 0 rows / 0 distinct; official still empty; confirm and retry2 "
        f"still 404). First-interval tick_s={TICK_S_FIRST} (printed {TICK_S_PRINTED}) was sane; later-mean-robust {TICK_S_LATER} "
        f"was over the 45s gate so a corrective realign of {TS_REALIGNED_CORRECTIVE} rows was applied; in-use tick_s={TICK_S_LATER}. "
        "The previous 17:30 half-hour backfill had already prefilled 84301601..84301900 overlap; this run added the newly "
        "published 84301900..84302200 chunks and filled the 17:49:54–17:57:59 (~475s) live dark gap (room_stats hole "
        "84302171..84302289) from official history except W45N8@84302200. A NEW ~475s box freeze 17:49:54–17:57:59 interrupted "
        "live ingest until the listener self-reconnected at 17:58:02; this run did not restart it."
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
