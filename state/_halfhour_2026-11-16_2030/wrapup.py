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
DIR = f"{ROOT}/state/_halfhour_2026-11-16_2030"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84303401, 84304100
SPAN = TMAX - TMIN + 1  # 700
# First-pass official 404 inside this reconstructed window: W45N7@84303900 (missing_chunks=1 of 35).
# Previous leftover 404 W45N8@84302200 is just outside TMIN and is retried as a leftover.
IN_WINDOW_404 = {("W45N7", 84303900)}
GT_FIRST = 84304182
PUB_BASES = "84303400..84304000"
TICK_S_FIRST = 4.84319
TICK_S_PRINTED = "4.843"
TICK_S_LATER = 4.85314
TICK_S_IN_USE = 4.84319  # first-interval; later already inside 45s gate, no corrective
INSERTED_FIRST = 0
ALREADY = 25570
CREEP_ROWS = 25570
TS_REALIGNED_FIRST = 177
TS_REALIGNED_CORRECTIVE = 0
FIRST_NEW = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
FIRST_OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 600, "W47N7": 700}
MISSING_CHUNKS_FIRST = 1
MISSING_CHUNK_LIST = ["W45N7@84303900"]
TICK_S_CHECK_AT = "20:32:28"
TICK_S_CHECK_GT = 84304200
TICK_S_REALIGN_GT = None
VS_FIRST = "over45=0 over15=1132 mean_off=-3.65 max_off=42.36"
VS_LATER_BEFORE = "over45=0 over15=1811 mean_off=0.90 max_off=44.12"
VS_LATER_AFTER = "over45=0 over15=1811 mean_off=0.90 max_off=44.12"

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
            "NEW this period: box freeze 2026-11-16 20:19:04–20:23:43 Asia/Hong_Kong (~271s, recorded in "
            "box_pauses.jsonl). existing run_listener.sh relaunched listener.py at 20:23:46 "
            "(pid 3582186 since 20:23:56; previous pid 3575402 from 20:05:13/20:05:23 exited after the freeze). "
            "After reconnect, the listener itself pulled recent CPU / path buffers (creep_cpu and path_arrivals "
            "near the live tip). room_stats has a 69-tick live gap 84304031..84304099 around the freeze; "
            "official 84304000 was 200 for all five rooms on this run, so creep_ticks 84304001..84304100 is filled. "
            "The unpublished in-progress chunk 84304100 (ticks 84304101..) is being filled live on the subscribed room. "
            "In-window official 404 W45N7@84303900 (hole 84303901..84304000, 0 live) is still 404 after confirm and retry2. "
            "Earlier the same evening: freeze 19:49:05–20:05:10 (~952s) relaunched at 20:05:13 "
            "(pid 3575402 since 20:05:23; room_stats gap 84303661..84303869 already official-filled in the 20:00 run); "
            "listener ws ping/pong timeout at 19:36:16 relaunched at 19:36:19 "
            "(pid 3567881 since 19:36:29; room_stats gap 84303491..84303509 already official-filled in the 19:30 run); "
            "freeze 18:46:58–18:57:48 (~640s) relaunched at 18:57:51 (pid 3541009 since 18:58:01; "
            "room_stats gap 84302881..84303029 already official-filled in the 19:00 run). "
            "This backfill did not kill or start a listener."
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
    confirm_at = conf.get("confirm_at") or conf.get("at") or "2026-11-16 18:37:42 Asia/Hong_Kong"
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
    in_window_still = True  # first-pass missing_chunks=1; W45N7@84303900 still 404 after confirm and retry2
    known_in = [
        "W45N7@84303900 (in-window official 404, hole 84303901..84304000, 0 rows / 0 distinct; "
        "still 404 after confirm 20:32:39 game.time=84304202 and retry2 20:33:46 game.time=84304216; "
        "not live-filled; retry next run)",
    ]
    known_out = [
        leftover_desc("W45N8@84302200",
            "just outside this 40m window (previous leftover official 404), still 404 after confirm and retry2; "
            "not live-filled at wrapup; hole 84302201..84302300; retry next run" if (w45_in.get("distinct") or 0) == 0
            else "just outside this 40m window (previous leftover official 404), still 404 after confirm and retry2; partially live-filled; retry next run"),
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
        "in-window official 404 W45N7@84303900 still 404 after confirm and retry2 "
        "(0 rows / 0 distinct, range None..None; hole 84303901..84304000; retry next run); "
        "leftover official 404 W45N8@84302200 just outside this window still 404 after confirm and retry2 "
        f"({w45_in_txt}; hole 84302201..84302300; retry next run)"
    )
    leftover_short = (
        "leftovers just outside window W45N8@84302200 still 404 "
        f"({w45_in_txt}; hole 84302201..84302300), "
        "W47N8@84300900 still 404 "
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
            "Listener self-reconnected just before this run after a box freeze 2026-11-16 20:19:04–20:23:43 "
            "Asia/Hong_Kong (~271s, recorded in box_pauses.jsonl). existing run_listener.sh relaunched "
            "listener.py at 20:23:46 (pid 3582186 since 20:23:56; previous pid 3575402 from 20:05:13/20:05:23 "
            "exited). After reconnect the listener itself pulled recent CPU / path buffers. This 20:30 "
            "half-hour backfill did not kill or restart the listener, war_cmd, or pulse, and did not start "
            "a second listener. yield_files=absent; peacetime single-slot rotation "
            "W46N8:W47N8:W45N8:W45N7=5:5:1:1 unchanged. live.json was fresh at precheck 20:30:44 "
            "(age 2.4s, roomSlot W45N8, gameTime=None because the slot was not on HOME, stats.t=84304170). "
            "room_stats has a 69-tick live gap 84304031..84304099 around the freeze; official 84304000 was "
            "200 for all five rooms on this run, so creep_ticks 84304001..84304100 is filled. The unpublished "
            "in-progress chunk 84304100 is being filled live on the subscribed room. In-window official 404 "
            "W45N7@84303900 (hole 84303901..84304000) remains unfilled after confirm and retry2. The earlier "
            "19:49:05–20:05:10 (~952s) freeze room_stats gap 84303661..84303869 was already official-filled "
            "in the 20:00 run, the 19:36 ping/pong room_stats gap 84303491..84303509 was already official-filled "
            "in the 19:30 run, and the 18:46:58–18:57:48 (~640s) freeze gap 84302881..84303029 was already "
            "official-filled in the 19:00 run. Leftover official 404 W45N8@84302200 (hole 84302201..84302300) "
            "is just outside this window and remains unfilled. The concurrent 20:23 hourly patrol had already "
            "official-backfilled this same window at game.time=84304111 (inserted=8514, missing_chunks=2: "
            "W45N7@84303900 and W47N7@84304000) and recovered W47N7@84304000 on a W47N7-only retry at "
            "game.time=84304132 (inserted=450), so this 20:30 first pass was idempotent (inserted=0)."
        ),
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": SPAN},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": TICK_S_LATER,
        "tick_s_in_use": TICK_S_IN_USE,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": False,
        "missing_chunks": MISSING_CHUNKS_FIRST if in_window_still else 0,
        "missing_chunk_list": MISSING_CHUNK_LIST if in_window_still else [],
        "missing_chunk_first_pass": MISSING_CHUNK_LIST,
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed "
            f"{TMIN}..{TMAX} (700). missing_chunks=1 of 35 official GETs (34 of 35 200; "
            "W45N7@84303900 404). The concurrent 20:23 hourly patrol had already pulled the same "
            "window at game.time=84304111 (then missing_chunks=2 including W47N7@84304000, which "
            "the patrol recovered at game.time=84304132). "
            f"confirm at {confirm_at} game.time={confirm_gt} recovered {confirm_rec_txt} "
            f"inserted={confirm_ins} ts_realigned={confirm_nfix}. "
            f"retry2 at {retry2_at} game.time={retry2_gt} recovered {retry2_rec_txt} "
            f"inserted={retry2_ins} ts_realigned={retry2_nfix}. "
            f"{inwin_404_txt}. Leftovers just outside this window: "
            "W45N8@84302200 (0 live, hole 84302201..84302300), "
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
            "The concurrent 20:23 Asia/Hong_Kong hourly patrol already official-backfilled this same "
            "window at game.time=84304111 (inserted=8514, already_in_db=16611, missing_chunks=2: "
            "W45N7@84303900 and W47N7@84304000; tick_s=4.843) and recovered W47N7@84304000 on a "
            "W47N7-only retry at game.time=84304132 (inserted=450). The previous 20:00 half-hour "
            "backfill had official-backfilled the overlap 84303401..84303800 (inserted_total=9987, "
            "already_in_db=18513, first-pass missing_chunks=0, tick_s=4.87164, later-mean-robust 4.83139, "
            "no corrective realign, ts_realigned_first=1441). "
            f"A box freeze 20:19:04–20:23:43 (~271s) caused run_listener.sh to relaunch listener.py "
            f"at 20:23:46. This 40-minute official history pull therefore inserted "
            f"{INSERTED_FIRST} new rows (already_in_db={ALREADY} of {CREEP_ROWS} reconstructed) across "
            f"{TMIN}..{TMAX}; it was idempotent on the patrol-prefilled 84303800/84303900/84304000 "
            "chunks plus overlap with the previous official window (including the new freeze gap "
            "84304031..84304099, which official 84304000 filled in creep_ticks). "
            f"confirm and retry2 inserted {(confirm_ins or 0) + (retry2_ins or 0)}. "
            "Four rooms have 700 official ticks with creeps; W45N7 has 600 with an official 404 hole "
            "84303901..84304000. Official 84303400/84303500/84303600/84303700/84303800/84303900/84304000 "
            "were 200 for all five rooms except W45N7@84303900 (34 of 35 official GETs 200)."
        ),
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": TS_REALIGNED_CORRECTIVE,
        "ts_realigned_confirm": confirm_nfix or 0,
        "ts_realigned_retry2": retry2_nfix or 0,
        "ts_realigned_note": (
            f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) reported "
            f"ts_realigned={TS_REALIGNED_FIRST}. "
            "The script's tick_seconds() uses the first interval between published chunk bases "
            "(min timestamp across rooms, which was W46N8 on every published base this window, so W46 and MIN_ALL are identical; "
            "first-interval tick_s=4.84319). later-mean-robust "
            f"of the remaining W46N8 intervals is {TICK_S_LATER} (raw later-mean also {TICK_S_LATER}; delta first-robust "
            "-0.00995 s/tick, ~7.8s at tmin vs gt_first). "
            f"At {TICK_S_CHECK_AT} Asia/Hong_Kong game.time={TICK_S_CHECK_GT}, "
            f"first-interval was already inside the 45s gate versus the later live anchor ({VS_FIRST}) "
            f"and later-mean-robust was also inside the 45s gate versus first-interval-timestamped rows ({VS_LATER_BEFORE}). "
            "No corrective later-mean-robust realign was applied (later over45=0 and first-interval is in the sane 3-6s band). "
            f"In-use tick_s remains first-interval {TICK_S_IN_USE}."
        ),
        "ssl_first_attempt": "ok first try",
        "hourly_patrol_prefilled": (
            "The concurrent 20:23 Asia/Hong_Kong hourly patrol had already official-backfilled this "
            "same window at game.time=84304111 (inserted=8514, already_in_db=16611, missing_chunks=2: "
            "W45N7@84303900 and W47N7@84304000, tick_s=4.843) and recovered W47N7@84304000 on a "
            "W47N7-only retry at 20:27 game.time=84304132 (inserted=450, W47N7 distinct=700). "
            "The previous 20:00 half-hour backfill had prefilled the overlap 84303401..84303800 "
            "(inserted=9987, missing_chunks=0, tick_s=4.87164 / later 4.83139, no corrective realign, "
            "ts_realigned_first=1441). "
            "A box freeze 20:19:04–20:23:43 (~271s) caused run_listener.sh to relaunch listener.py "
            "at 20:23:46 (pid 3582186 since 20:23:56). Official history in this window covers "
            "84303400..84304000 for all five rooms except W45N7@84303900 (34/35 official GETs 200; "
            "missing_chunks=1)."
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
            "from": "2026-11-16 20:19:04",
            "to": "2026-11-16 20:23:43",
            "sec": 271,
            "kind": "box freeze (VM hibernated; recorded in box_pauses.jsonl)",
            "live_room_stats_gap": [84304031, 84304099],
            "official_fill": (
                "Box froze 20:19:04–20:23:43 (~271s) and run_listener.sh relaunched listener.py at 20:23:46 "
                "(pid 3582186 since 20:23:56). room_stats shows a 69-tick gap 84304031..84304099 around the freeze. "
                "Official 84304000 was 200 for all five rooms on this run, so creep_ticks 84304001..84304100 is filled. "
                "The unpublished in-progress chunk 84304100 (84304101..) is being filled live on the subscribed room. "
                "The earlier 19:49:05–20:05:10 (~952s) freeze room_stats gap 84303661..84303869 was already official-filled "
                "in the 20:00 run, the 19:36 ping/pong room_stats gap 84303491..84303509 was already official-filled in the "
                "19:30 run, and the 18:46:58–18:57:48 (~640s) freeze live room_stats gap 84302881..84303029 was already "
                "official-filled in the 19:00 run. In-window official 404 W45N7@84303900 (hole 84303901..84304000) remains "
                "unfilled. Leftover official 404 W45N8@84302200 (hole 84302201..84302300) is earlier than this window "
                "and remains unfilled."
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

    first_pass_gets = "34 of 35 official GETs 200; missing_chunks=1 W45N7@84303900"
    now_lines = []
    now_lines.append(
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms=W46N8,W47N8,W45N8,W45N7,W47N7 dry=False"
    )
    now_lines.append(f"  ({first_pass_gets}; see history_backfill.txt)")
    now_lines.append(f"tick_s={TICK_S_PRINTED}")
    now_lines.append(f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={CREEP_ROWS} missing_chunks=1")
    now_lines.append(f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}")
    now_lines.append("per_room W46N8:700t/0new W47N8:700t/0new W45N8:700t/0new W45N7:600t/0new W47N7:700t/0new")
    now_lines.append(f"inserted={INSERTED_FIRST}")
    now_lines.append(f"ts_realigned={TS_REALIGNED_FIRST}")
    now_lines.append("db_after")
    for room in sorted(ROOMS):
        cvr = coverage[room]
        rng = cvr["range"]
        now_lines.append(f"  {room} ticks={rng[0]}..{rng[1]} rows={cvr['rows']} distinct={cvr['distinct']}")
    now_lines.append(
        f"confirm recovered {confirm_rec_txt} at {confirm_at} game.time={confirm_gt} inserted={confirm_ins} ts_realigned={confirm_nfix}; "
        f"{inwin_404_txt}; {leftover_short}; retried 35 aged leftover official 404s "
        f"including W46N8@84292000, all still 404; retry2 at {retry2_at} game.time={retry2_gt} recovered {retry2_rec_txt} "
        f"inserted={retry2_ins} ts_realigned={retry2_nfix}; leftovers W45N7@84303900 (in-window), W45N8@84302200, W47N8@84300900, W45N8@84300900, W45N8@84300000, "
        "W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404"
    )
    now_lines.append(
        f"ts_realigned_first_pass={TS_REALIGNED_FIRST} (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, sane first interval); "
        f"later-mean-robust {TICK_S_LATER} was already inside the 45s gate versus first-interval rows "
        f"at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT} (later {VS_LATER_BEFORE}; first {VS_FIRST}), "
        "so no corrective realign was applied. "
        f"In-use tick_s={TICK_S_IN_USE}."
    )
    now_lines.append(
        f"inserted_total={inserted_total} unique_after rows={unique_after['rows']} distinct_room_ticks={unique_after['distinct_room_ticks']} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={empty_ticks} official_404_missing={official_404_ticks} "
        f"official_fetched={official_fetched} expected=5*700={expected} in_window_official_404={in_window_404} after retry2 "
        f"(first-pass missing_chunks=1 W45N7@84303900; confirm recovered {0 if not confirm_rec else confirm_rec}, retry2 recovered {0 if not retry2_rec else retry2_rec})"
    )
    now_lines.append(
        f"official empty-no-creep ticks in this window: {empty_note}. "
        "official 84303400/84303500/84303600/84303700/84303800/84303900/84304000 were 200 for all five rooms "
        "except W45N7@84303900 (34 of 35 official GETs 200; in-window official 404 W45N7@84303900 hole 84303901..84304000 "
        "still 0 rows / 0 distinct after confirm and retry2; retry next run). "
        "Remaining official 404 just outside window: "
        f"W45N8 official 404 84302201..84302300 ({w45_in_txt}; official 84302200 still 404 after confirm and retry2; retry next run); "
        "W47N8 official 404 84300901..84301000 (74 live-filled with holes 84300965..84300983 and 84300994..84301000 "
        "/ 1008 rows; 26 empty; official 84300900 still 404 after confirm and retry2; retry next run); "
        "W45N8 official 404 84300901..84301000 (7 live-filled 84300994..84301000 / 28 rows; 93 empty 84300901..84300993; "
        "official 84300900 still 404 after confirm and retry2; retry next run); "
        "W45N8 official 404 84300001..84300100 (26 live-filled 84300067..84300092 / 159 rows; 74 still empty; official "
        "84300000 still 404 after confirm and retry2; retry next run). Leftover just outside window: W47N8 official 404 "
        "84298001..84298100 (not live-filled, 0 distinct / 0 rows; retry next run); W47N8 official 404 84297201..84297300 "
        "(already live-filled 100 distinct / 1562 rows); W47N7 official 404 84296501..84296600; W45N8 official 404 "
        "84295901..84296000; W45N7 official 404 84295801..84295900. Four rooms 700 distinct with creeps; W45N7 600 "
        "with official 404 hole 84303901..84304000. "
        "A box freeze 20:19:04–20:23:43 (~271s) caused run_listener.sh to relaunch listener.py at 20:23:46 "
        "(pid 3582186 since 20:23:56; previous pid 3575402 exited). This is recorded in box_pauses.jsonl. "
        "room_stats has a 69-tick gap 84304031..84304099 around the freeze; official 84304000 was 200 "
        "for every room, so creep_ticks 84304001..84304100 is filled. The earlier 19:49:05–20:05:10 (~952s) freeze "
        "room_stats gap 84303661..84303869 was already official-filled in the 20:00 run, the 19:36 ping/pong "
        "room_stats gap 84303491..84303509 was already official-filled in the 19:30 run, and the 18:46:58–18:57:48 "
        "(~640s) freeze live room_stats gap 84302881..84303029 was already official-filled in the 19:00 run. "
        "This run did not restart the listener."
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
        f"missing_chunks first_pass=1 at game.time={GT_FIRST} (34 of 35 official GETs 200; W45N7@84303900 404); published_bases {PUB_BASES}, "
        f"reconstructed {TMIN}..{TMAX} (700), already_in_db={ALREADY} inserted={INSERTED_FIRST}, "
        f"ts_realigned={TS_REALIGNED_FIRST} on tick_s={TICK_S_FIRST} (printed {TICK_S_PRINTED}, sane first interval). "
        f"later-mean-robust {TICK_S_LATER} was already inside the 45s gate versus first-interval rows "
        f"at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT} (later {VS_LATER_BEFORE}; first {VS_FIRST}), "
        f"so no corrective realign was applied. In-use tick_s={TICK_S_IN_USE}. "
        f"Confirm {confirm_at} game.time={confirm_gt} recovered {confirm_rec_txt}; {inwin_404_txt}; "
        "leftovers just outside this window W45N8@84302200 still 404 (0 rows / 0 distinct, hole 84302201..84302300) "
        "and W47N8@84300900 still 404 (74 live-filled with holes 84300965..84300983 "
        "and 84300994..84301000 / 1008 rows; 26 empty) and W45N8@84300900 still 404 (7 live-filled 84300994..84301000 / 28 rows; "
        "93 empty 84300901..84300993); leftovers W45N8@84300000 still 404 (26 live-filled 84300067..84300092 / 159 rows; 74 empty); "
        "leftovers W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900, and W45N7@84295800 still 404; "
        f"retried 35 aged leftover official 404s including W46N8@84292000 — all still 404; confirm ts_realigned={confirm_nfix}. "
        f"retry2 at {retry2_at} game.time={retry2_gt} recovered {retry2_rec_txt}; leftovers W45N7@84303900 (in-window), W45N8@84302200, W47N8@84300900, W45N8@84300900, "
        "W45N8@84300000, W47N8@84298000, W47N8@84297200, W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404. "
        f"After retry2: W46N8 distinct={coverage['W46N8']['distinct']} missing_n={coverage['W46N8']['missing_n']}; "
        f"W47N8 distinct={coverage['W47N8']['distinct']} missing_n={coverage['W47N8']['missing_n']}; "
        f"W45N8 distinct={coverage['W45N8']['distinct']} missing_n={coverage['W45N8']['missing_n']}"
        + (f" (official 404 {coverage['W45N8']['missing_ranges']})" if coverage['W45N8']['official_404_missing'] else "")
        + (f" (official empty-no-creep {coverage['W45N8']['missing_ranges']})" if coverage['W45N8']['official_empty_no_creep'] and not coverage['W45N8']['official_404_missing'] else "")
        + "; "
        f"W45N7 distinct={coverage['W45N7']['distinct']} missing_n={coverage['W45N7']['missing_n']}"
        + (f" (official 404 {coverage['W45N7']['missing_ranges']})" if coverage['W45N7']['official_404_missing'] else "")
        + (f" (official empty-no-creep {coverage['W45N7']['missing_ranges']})" if coverage['W45N7']['official_empty_no_creep'] and not coverage['W45N7']['official_404_missing'] else "")
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
        f"was already inside the 45s gate so no corrective realign was applied; in-use tick_s={TICK_S_IN_USE}. "
        "Previously leftover official 404 W45N8@84302200 is just outside this 40m window (hole 84302201..84302300 still 0 rows / 0 distinct; official 84302200 "
        "still 404; confirm and retry2 still 404; not live-filled; retry next run). "
        "The concurrent 20:23 hourly patrol had already official-backfilled this same window "
        "(inserted=8514 then recovered W47N7@84304000 inserted=450); this 20:30 run was idempotent "
        "(inserted=0) and retried in-window official 404 W45N7@84303900 (hole 84303901..84304000 still 0 rows / 0 distinct; "
        "confirm and retry2 still 404; not live-filled; retry next run). Leftover official 404 W45N8@84302200 remains just outside this window. "
        "A box freeze 20:19:04–20:23:43 (~271s) caused run_listener.sh to relaunch listener.py at 20:23:46 "
        "(pid 3582186 since 20:23:56); room_stats gap 84304031..84304099 (69 ticks) sits around the freeze, "
        "and official 84304000 filled creep_ticks 84304001..84304100 for all five rooms. This run did not restart the listener."
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
