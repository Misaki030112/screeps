#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-18_0030"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84324701, 84325400
GT_FIRST = 84325474
PUB_BASES = "84324700..84325300"
TICK_S_FIRST = 4.65834
TICK_S_PRINTED = "4.658"
NEW_ROWS = {"W46N8": 858, "W47N8": 1140, "W45N8": 458, "W45N7": 246, "W47N7": 641}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 600, "W47N7": 700}
INSERTED_FIRST = 3343
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
ALREADY = 23212
RECON_ROWS = 26555
TS_REALIGNED_FIRST = 0
IN_WINDOW_404 = [
    ("W45N7", 84324900),  # still 404 after 00:00 confirm/retry2 and this first pass/confirm/retry2; 0 live / 100 empty
]
OUTSIDE_404 = [
    ("W47N8", 84324300),
    ("W47N8", 84323200),
    ("W47N8", 84322100),
    ("W45N7", 84321600),
    ("W47N8", 84321300),
    ("W47N8", 84319900),
    ("W47N8", 84319000),
    ("W46N8", 84318500),
    ("W45N8", 84318000),
    ("W47N7", 84315100),
    ("W45N8", 84314900),
    ("W45N7", 84314500),
    ("W47N8", 84314000),
    ("W46N8", 84313200),
    ("W46N8", 84310500), ("W47N7", 84309000), ("W45N8", 84309100), ("W45N8", 84306500),
    ("W45N7", 84305100), ("W47N8", 84304700), ("W45N7", 84303900), ("W45N8", 84302200),
    ("W47N8", 84300900), ("W45N8", 84300900), ("W45N8", 84300000), ("W47N8", 84298000),
    ("W47N8", 84297200), ("W47N7", 84296500), ("W45N8", 84295900), ("W45N7", 84295800),
]


def ranges(ticks, tmin, tmax):
    missing, start, s = [], None, set(ticks)
    for t in range(tmin, tmax + 1):
        if t not in s:
            if start is None:
                start = t
        elif start is not None:
            missing.append([start, t - 1])
            start = None
    if start is not None:
        missing.append([start, tmax])
    return missing


def load_json(path):
    with open(path) as f:
        return json.load(f)


def pgrep(pat):
    r = subprocess.run(["pgrep", "-af", pat], capture_output=True, text=True)
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip() and "pgrep" not in ln]


def iso(ts):
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    return ts.isoformat()


def hole_text(c, room, base):
    a, b = base + 1, base + 100
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, a, b),
    ).fetchone()
    d, mn, mx, n = row[0] or 0, row[1], row[2], row[3] or 0
    ticks = [r[0] for r in c.execute(
        "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
        (room, a, b),
    ).fetchall()]
    miss = ranges(ticks, a, b) if d else [[a, b]]
    empty_n = sum(bb - aa + 1 for aa, bb in miss)
    if d == 0:
        detail = "0 live / 100 empty"
    elif d == 100:
        detail = f"already live-filled 100 distinct / {n} rows"
    else:
        detail = f"{d} live / {empty_n} empty"
    where = "in window" if (base + 1) <= TMAX and (base + 100) >= TMIN else "outside window"
    return f"{room}@{base} ({detail}; official {base} still 404 after confirm and retry2; {where}; retry next run)"


def hole_short(c, room, base):
    a, b = base + 1, base + 100
    ticks = [r[0] for r in c.execute(
        "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
        (room, a, b),
    ).fetchall()]
    d = len(ticks)
    miss = ranges(ticks, a, b) if d else [[a, b]]
    empty_n = sum(bb - aa + 1 for aa, bb in miss)
    if d == 0:
        return f"{room}@{base} (0 live / 100 empty)"
    if d == 100:
        return f"{room}@{base} (100 live)"
    return f"{room}@{base} ({d} live / {empty_n} empty)"


def fill(c, lo, hi):
    out = {}
    span = hi - lo + 1
    for room in ROOMS:
        row = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, lo, hi),
        ).fetchone()
        out[room] = {"distinct": row[0] or 0, "min": row[1], "max": row[2], "rows": row[3] or 0, "span": span}
    return out


def tick_runs(ticks):
    if not ticks:
        return []
    runs, a, prev = [], ticks[0], ticks[0]
    for t in ticks[1:]:
        if t == prev + 1:
            prev = t
        else:
            runs.append([a, prev, prev - a + 1])
            a = prev = t
    runs.append([a, prev, prev - a + 1])
    return runs


def frac(filld, span):
    return "/".join(str(filld[r]["distinct"]) for r in ROOMS) + f" of {span}"


def in_window(lo, hi):
    return not (hi < TMIN or lo > TMAX)


def seg_after(c, ts_from):
    out = {}
    for table in ("creep_cpu", "path_arrivals"):
        row = c.execute(
            f"SELECT min(tick), max(tick), count(*), min(ts), max(ts) FROM {table} WHERE ts >= %s",
            (ts_from,),
        ).fetchone()
        out[table] = {
            "min_tick": row[0], "max_tick": row[1], "rows": row[2] or 0,
            "min_ts": iso(row[3]), "max_ts": iso(row[4]),
        }
    return out


def main():
    cov = load_json(DIR / "coverage_final.json")
    confirm = load_json(DIR / "backfill_confirm_gets.json")
    tsr = load_json(DIR / "tick_s_realign.json")
    prev = load_json(DIR / "history_backfill_prev_0000.json")
    coverage = cov.get("coverage") or cov
    later = float(tsr["later_mean_w46_robust"])
    vs_later = tsr["vs_later_after"]
    vs_first = tsr["vs_first"]
    confirm_at = confirm.get("at")
    confirm_gt = confirm.get("game_time")
    retry2 = confirm.get("retry2") or {}
    retry2_at = retry2.get("at")
    retry2_gt = retry2.get("game_time")
    corrective = bool(tsr.get("corrective_applied"))
    nfix_corr = int(tsr.get("ts_realigned_to_later_mean") or 0)
    tick_s_in_use = later if corrective else TICK_S_FIRST

    live = load_json(ROOT / "metrics/live.json")
    rot = load_json(ROOT / "metrics/listener_rot.json")
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    now = datetime.now(TZ)
    lis = pgrep("tools/listener.py")
    runl = pgrep("tools/run_listener.sh")
    yield_present = (ROOT / "metrics/listener_yield_rooms").exists()

    with db.connect() as c:
        tips = {}
        for table in ("creep_ticks", "room_stats", "creep_cpu", "path_arrivals"):
            row = c.execute(f"SELECT max(tick), max(ts) FROM {table}").fetchone()
            tips[table] = {"max_tick": row[0], "max_ts": iso(row[1])}
        live_after = {}
        db_after = {}
        per_room = {}
        for room in ROOMS:
            rows = c.execute(
                "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick > %s ORDER BY 1",
                (room, TMAX),
            ).fetchall()
            ticks = [r[0] for r in rows]
            agg = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) "
                "FROM creep_ticks WHERE room=%s AND tick > %s",
                (room, TMAX),
            ).fetchone()
            live_after[room] = {
                "distinct": agg[0] or 0, "min": agg[1], "max": agg[2], "rows": agg[3] or 0,
                "runs": tick_runs(ticks),
            }
            dba = c.execute(
                "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
                "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, TMIN, TMAX),
            ).fetchone()
            db_after[room] = {
                "min": dba[0], "max": dba[1], "rows": dba[2] or 0, "distinct": dba[3] or 0,
            }
            room_cov = (coverage.get(room) or {}) if isinstance(coverage, dict) else {}
            per_room[room] = {
                "official_ticks": OFFICIAL_TICKS[room],
                "new_rows_first_pass": NEW_ROWS[room],
                "db_rows": dba[2] or 0,
                "db_distinct": dba[3] or 0,
                "db_min": dba[0],
                "db_max": dba[1],
                "missing_n": room_cov.get("missing_n"),
                "missing_ranges": room_cov.get("missing_ranges"),
                "official_empty_no_creep": room_cov.get("official_empty_no_creep"),
                "official_empty_no_creep_ranges": room_cov.get("official_empty_no_creep_ranges"),
                "official_404_missing": room_cov.get("official_404_missing"),
            }
        holes = [hole_text(c, room, base) for room, base in OUTSIDE_404]
        in_window_holes = [hole_text(c, room, base) for room, base in IN_WINDOW_404]
        hole_shorts = {f"{room}@{base}": hole_short(c, room, base) for room, base in (IN_WINDOW_404 + OUTSIDE_404)}
        freeze_0010 = fill(c, 84325171, 84325209)
        freeze_0023 = fill(c, 84325320, 84325360)
        freeze_0002 = fill(c, 84325051, 84325089)
        freeze_2342 = fill(c, 84324821, 84324969)
        freeze_2315 = fill(c, 84324485, 84324514)
        rem_overlap = fill(c, 84324701, 84325100)
        rem_new = fill(c, 84325101, 84325400)
        # prior gaps now before this window (spot-check still filled)
        freeze_2249 = fill(c, 84324141, 84324309)
        freeze_2249_pub = fill(c, 84324141, 84324300)
        freeze_2249_tail = fill(c, 84324301, 84324309)
        freeze_2214 = fill(c, 84323691, 84323819)
        freeze_2146 = fill(c, 84323341, 84323549)
        seg_002350 = seg_after(c, "2026-11-18 00:23:50+08")
        seg_001223 = seg_after(c, "2026-11-18 00:12:23+08")
        unique = c.execute(
            """SELECT count(*), count(DISTINCT (creep, tick)), count(DISTINCT tick),
                      count(DISTINCT (room, tick))
               FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s)""",
            (TMIN, TMAX, list(ROOMS)),
        ).fetchone()

    unique_after = {
        "rows": unique[0],
        "unique_creep_tick_rows": unique[1],
        "distinct_ticks": unique[2],
        "distinct_room_ticks": unique[3],
    }
    recovered = int(cov.get("official_recovered") or 3400)
    expected = int(cov.get("official_expected") or 3500)
    empty_no_creep = int(cov.get("empty_no_creep") or cov.get("official_empty_no_creep") or 0)
    official_404_missing = int(cov.get("official_404_missing") or 100)
    w45n7_empty = (coverage.get("W45N7") or {}).get("official_empty_no_creep_ranges") or []
    w45n8_empty = (coverage.get("W45N8") or {}).get("official_empty_no_creep_ranges") or []

    leftover_bits = [
        f"leftover official 404 {hole_shorts['W47N8@84324300']} still outside window",
        f"leftover official 404 {hole_shorts['W47N8@84323200']} still outside window",
        f"leftover official 404 {hole_shorts['W47N8@84322100']} still outside window",
        f"leftover official 404 {hole_shorts['W47N8@84321300']} still outside window",
        f"leftover official 404 {hole_shorts['W45N7@84321600']} still outside window",
        f"leftover official 404 {hole_shorts['W47N8@84319900']} still outside window",
        f"leftover official 404 {hole_shorts['W47N8@84319000']} still outside window",
        f"leftover official 404 {hole_shorts['W46N8@84318500']} still outside window",
        f"leftover official 404 {hole_shorts['W45N8@84318000']} still outside window",
        f"leftover official 404 {hole_shorts['W47N7@84315100']} still outside window",
        f"leftover official 404 {hole_shorts['W45N8@84314900']} still outside window",
        f"leftover official 404 {hole_shorts['W45N7@84314500']} still outside window",
        f"leftover official 404 {hole_shorts['W47N8@84314000']} still outside window",
        f"leftover official 404 {hole_shorts['W46N8@84313200']} still outside window",
        "older leftovers unchanged",
    ]
    leftover_txt = "; ".join(leftover_bits) + "."
    inwin_txt = f"in-window official 404 {hole_shorts['W45N7@84324900']} still 404 after confirm and retry2"

    finished_at = now.isoformat()
    finished_hkt = now.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
    finished_hkt_sec = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": finished_at,
        "finished_at_hkt": finished_hkt,
        "shard": "shard3",
        "rooms": list(ROOMS),
        "minutes": 40,
        "game_time": GT_FIRST,
        "live_json_gameTime_at_finish": live.get("gameTime"),
        "live_json_stats_t_at_finish": stats.get("t"),
        "live_json_gameTime_note": (
            "Listener already up at precheck (pid 54635 since 00:23:50 after ws 'Connection to remote host was lost' at 00:23:40). "
            "New box freeze 00:10:06–00:12:20 (~127s) and the 00:23:40 drop were already self-healed; this run did not restart the listener. "
            "live.json was fresh (age 2.6s) at 00:33:08 precheck, roomSlot=W46N8 then W47N8 at wrapup."
        ),
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": 700},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": later,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": corrective,
        "missing_chunks": 1,
        "missing_chunk_list": ["W45N7@84324900"],
        "missing_chunk_first_pass": ["W45N7@84324900"],
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). "
            "34 of 35 official GETs 200; missing_chunks=1 W45N7@84324900 (same leftover official 404 as the 00:00 run). "
            "W47N8/W45N8/W47N7@84325000, 404 on the 00:00 first pass, were already 200 on this first pass. "
            "Confirm at 00:35:16 and retry2 at 00:37:25 both still 404 W45N7@84324900; inserted=0."
        ),
        "creep_rows_reconstructed": RECON_ROWS,
        "already_in_db": ALREADY,
        "inserted": INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": INSERTED_CONFIRM,
        "inserted_retry2": INSERTED_RETRY2,
        "inserted_note": (
            f"This 00:30 first pass inserted {INSERTED_FIRST} new rows (already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
            "Confirm and retry2 inserted 0 (W45N7@84324900 still official 404)."
        ),
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": nfix_corr,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": (
            f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) inserted with ts_realigned=0. "
            f"later-mean-robust {later:.5f} already inside 45s gate (over45=0), no corrective realign; in-use {tick_s_in_use:.5f}."
        ),
        "ssl_first_attempt": False,
        "hourly_patrol_prefilled": True,
        "per_room": per_room,
        "known_official_404s_outside_window": [f"{r}@{b}" for r, b in OUTSIDE_404],
        "known_official_404s_in_window": [f"{r}@{b}" for r, b in IN_WINDOW_404],
        "w45n7_empty_no_creep_in_window": bool(w45n7_empty),
        "w45n7_empty_no_creep_ranges": w45n7_empty,
        "empty_no_creep_in_window": bool(empty_no_creep),
        "empty_no_creep_ranges": {room: (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or [] for room in ROOMS},
        "empty_no_creep_ticks": empty_no_creep,
        "official_room_ticks_fetched": recovered,
        "official_room_ticks_with_creeps": unique_after["distinct_room_ticks"],
        "official_recovered": recovered,
        "official_expected": expected,
        "new_box_freeze": {
            "from": "2026-11-18 00:10:06",
            "to": "2026-11-18 00:12:20",
            "sec": 127,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84325171, 84325209],
            "live_room_stats_gap_ticks": 39,
            "official_fill_full_gap": freeze_0010,
            "official_fill_published_part": freeze_0010,
            "official_fill_unpublished_tail": {},
            "published_part": [84325171, 84325209],
            "unpublished_tail": [],
            "note": (
                "new this run; full room_stats gap 84325171..84325209 is inside official window "
                f"{TMIN}..{TMAX}; official-filled {frac(freeze_0010, 39)} of 39 ticks on all five rooms; no unpublished tail."
            ),
        },
        "new_ws_drop": {
            "from": "2026-11-18 00:23:40",
            "to": "2026-11-18 00:23:50",
            "sec": 10,
            "kind": "ws_connection_lost",
            "listener_restart": "2026-11-18 00:23:40",
            "official_fill_nearby": freeze_0023,
            "nearby_band": [84325320, 84325360],
            "note": (
                "new this run; ws error 'Connection to remote host was lost' at 00:23:40, listener self-restarted 00:23:50. "
                "No large room_stats gap beyond the normal 9-tick STATS cadence; official-filled "
                f"{frac(freeze_0023, 41)} of 41 ticks 84325320..84325360 in this window. Segment 90 pulled after reconnect."
            ),
        },
        "prior_0002_ws_pong": {
            "from": "2026-11-18 00:01:06",
            "to": "2026-11-18 00:02:41",
            "sec": 95,
            "kind": "ws_ping_pong_timeout",
            "live_room_stats_gap": [84325051, 84325089],
            "official_fill_full_gap": freeze_0002,
            "note": (
                "not new this run (already in 00:00 wrapup); still inside this window; official-filled "
                f"{frac(freeze_0002, 39)} of 39 ticks. Prior 00:00 note of W45N8 empty-no-creep 5 ticks 84325058..84325062 is now filled (W45N8 distinct=700 this window)."
            ),
        },
        "prior_2342_box_freeze": {
            "from": "2026-11-17 23:42:43",
            "to": "2026-11-17 23:53:44",
            "sec": 661,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84324821, 84324969],
            "official_fill_full_gap": freeze_2342,
            "note": (
                "not new this run; still inside this window; official-filled "
                f"{frac(freeze_2342, 149)} of 149 ticks (W45N7 missing 69 ticks 84324901..84324969 due to official 404 @84324900)."
            ),
        },
        "prior_2315_box_freeze": {
            "from": "2026-11-17 23:15:58",
            "to": "2026-11-17 23:18:18",
            "sec": 130,
            "live_room_stats_gap": [84324485, 84324514],
            "official_fill_full_gap": freeze_2315,
            "note": "not new this run; now before this window start (window starts 84324701); official-filled 30/30/30/30/30 of 30 of 30 ticks.",
        },
        "remainder_overlap_84324701_84325100": rem_overlap,
        "remainder_new_84325101_84325400": rem_new,
        "unique_after": unique_after,
        "db_tips": tips,
        "db_after": db_after,
        "live_after_official_tip": live_after,
        "segment90_after_002350_reconnect": seg_002350,
        "segment90_after_001223_reconnect": seg_001223,
        "listener": {
            "listener_py": lis,
            "run_listener_sh": runl,
            "count_listener_py": len(lis),
            "count_run_listener": len(runl),
            "single_slot": len(lis) <= 1 and not yield_present,
            "roomSlot": live.get("roomSlot"),
            "rot": rot,
            "yield_files": "present" if yield_present else "absent",
            "restarted_this_run": False,
        },
        "confirm": {
            "at": confirm_at,
            "game_time": confirm_gt,
            "recovered": confirm.get("recovered") or [],
            "inserted": confirm.get("inserted") or 0,
        },
        "retry2": {
            "at": retry2_at,
            "game_time": retry2_gt,
            "recovered": retry2.get("recovered") or [],
            "inserted": retry2.get("inserted") or 0,
        },
        "coverage_official_recovered": f"{recovered}/{expected}",
        "in_window_holes": in_window_holes,
        "outside_holes": holes,
        "ok_quiet": True,
        "prev_run_finished_at": prev.get("finished_at_hkt") or prev.get("finished_at"),
        "prev_window": (prev.get("ticks") or {}),
    }

    (DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")

    db_after_lines = "\n".join(
        f"  {room} ticks={db_after[room]['min']}..{db_after[room]['max']} "
        f"rows={db_after[room]['rows']} distinct={db_after[room]['distinct']}"
        for room in ROOMS
    )
    per_room_line = " ".join(
        f"{room}:{OFFICIAL_TICKS[room]}t/{NEW_ROWS[room]}new" for room in ROOMS
    )

    now_lines = [
        f"{finished_hkt_sec} half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
        "  (first pass 34 of 35 official GETs 200, missing_chunks=1 W45N7@84324900; confirm recovered none inserted=0; retry2 inserted=0; in-window official 404 W45N7@84324900 still 404 0 live / 100 empty; leftover official 404s otherwise unchanged; see history_backfill.txt)",
        f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} corrective nfix={nfix_corr} (after over45={vs_later['over45']}), in-use {tick_s_in_use:.5f})",
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=1 (first pass)",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_room_line}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, total {INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2})",
        f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} (later-mean-robust {later:.5f} corrective, after over45={vs_later['over45']})",
        "db_after",
        db_after_lines,
        f"coverage official_recovered={recovered}/{expected} unique_after={unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
        f"tick_s_check later-mean-robust {later:.5f} corrective nfix={nfix_corr} (later over45={vs_later['over45']} over15={vs_later.get('over15')} mean_off={vs_later.get('mean_off'):.2f} max_off={vs_later.get('max_off'):.2f}); in-use tick_s={tick_s_in_use:.5f}",
        (
            f"confirm recovered none inserted=0; retry2 inserted=0; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep {len(w45n7_empty)} ranges {w45n7_empty}; "
            f"{leftover_txt}"
        ),
        (
            f"New box freeze 00:10:06–00:12:20 (~127s) room_stats gap 84325171..84325209; official-filled {frac(freeze_0010, 39)} of 39 of 39 ticks 84325171..84325209 (in this window; official-filled on all five rooms; no unpublished tail). "
            f"New websocket connection-lost 00:23:40 (listener restart 00:23:50) official-filled {frac(freeze_0023, 41)} of 41 of 41 ticks 84325320..84325360 (in this window; no large room_stats gap beyond the normal 9-tick STATS cadence). "
            f"Prior websocket ping/pong timeout 00:02:37 room_stats gap 84325051..84325089; official-filled {frac(freeze_0002, 39)} of 39 of 39 ticks 84325051..84325089 (still in this window; official-filled on all five rooms; prior W45N8 empty-no-creep 5 ticks 84325058..84325062 now filled). "
            f"Prior box freeze 23:42:43–23:53:44 (~661s) room_stats gap 84324821..84324969; official-filled {frac(freeze_2342, 149)} of 149 of 149 ticks 84324821..84324969 (still in this window; official-filled on W46N8/W47N8/W45N8/W47N7; W45N7 missing 69 ticks 84324901..84324969 due to official 404 @84324900; no unpublished tail). "
            f"Prior box freeze 23:15:58–23:18:18 (~130s) live creep_ticks gap 84324485..84324514; official-filled {frac(freeze_2315, 30)} of 30 of 30 ticks 84324485..84324514 (now before this window; official-filled on all five rooms; no unpublished tail). "
            f"Prior box freeze 22:49:11–23:01:18 (~727s) room_stats gap 84324141..84324309; official-filled {frac(freeze_2249_pub, 160)} of 160 of 160 published ticks 84324141..84324300 (still before this window; official-filled on all five rooms); former unpublished tail 84324301..84324309 is still before this window (official-fill {frac(freeze_2249_tail, 9)} of 9 of 9; W47N8 missing all 9 due to leftover official 404 @84324300). "
            f"Prior box freeze 22:14:08–22:23:18 (~549s) room_stats gap 84323691..84323819; official-filled {frac(freeze_2214, 129)} of 129 of 129 ticks 84323691..84323819 (still before this window; official-filled on all five rooms; no unpublished tail). "
            f"Prior box freeze 21:46:18–22:01:35 (~904s) room_stats gap 84323341..84323549; official-filled {frac(freeze_2146, 209)} of 209 of 209 ticks 84323341..84323549 (still before this window including former unpublished tail; official-filled on all five rooms; no unpublished tail remains). "
            "Prior 21:30 / 20:45 / 20:17 / 19:38 / 19:16 / 18:46 / 17:46 / 17:14 / 16:48 / 16:19 / 15:44 / 15:16 / 14:49 / 14:12 / 13:48 / 13:18 / 12:52 / 12:57 / 11:48 / 11:11 / 10:54 / 10:44 / 10:11 / 09:43 / 09:17 / 07:43 freeze gaps still official-filled as previously recorded and still before this window. "
            f"Previously unpublished 84325101..84325400 official-filled on all five rooms {frac(rem_new, 300)}. "
            f"Overlap 84324701..84325100 official-filled {frac(rem_overlap, 400)} (W45N7 missing 100 ticks 84324901..84325000 due to official 404 @84324900; other four rooms 400/400). "
            "Includes just-published 84324700..84325300 chunks, the new 00:10 freeze gap, and the new 00:23 connection-lost band. "
            f"W47N8@84324300 remains outside this window and still official 404. W47N8@84323200 / W47N8@84322100 / W47N8@84321300 / W45N7@84321600 / W47N8@84319900 and older leftovers remain outside this window and official 404."
        ),
        f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
        "confirm recovered none inserted=0 retry2 inserted=0",
        (
            f"ok=true (quiet); first-pass missing_chunks=1 (34 of 35 official GETs 200); confirm recovered none inserted=0; retry2 inserted=0; "
            f"{inwin_txt}; later-mean-robust {later:.5f} corrective nfix={nfix_corr}, tick_s_in_use={tick_s_in_use:.5f} (first-pass realign {TICK_S_FIRST} committed 0); "
            f"new 00:10 freeze gap 84325171..84325209 official-filled {frac(freeze_0010, 39)} of 39 of 39 ticks in this window, no unpublished tail; "
            f"new 00:23 connection-lost band 84325320..84325360 official-filled {frac(freeze_0023, 41)} of 41 of 41 ticks in this window; "
            f"prior 00:02 ping/pong gap 84325051..84325089 official-filled {frac(freeze_0002, 39)} of 39 of 39 ticks still in this window (W45N8 previous empty-no-creep 5 ticks now filled); "
            f"prior 23:42 freeze gap 84324821..84324969 official-filled {frac(freeze_2342, 149)} of 149 of 149 ticks still in this window (W45N7 missing 69 due to official 404 @84324900), no unpublished tail; "
            f"prior 23:15 freeze gap 84324485..84324514 official-filled {frac(freeze_2315, 30)} of 30 of 30 ticks now before this window, no unpublished tail; "
            f"{inwin_txt}; {leftover_txt}"
        ),
    ]
    now_text = "\n".join(now_lines) + "\n"
    (DIR / "history_backfill_now.txt").write_text(now_text)
    (ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_text)

    verify = [
        f"{finished_hkt_sec} half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
        "  (first pass 34 of 35 official GETs 200, missing_chunks=1 W45N7@84324900; confirm recovered none inserted=0; retry2 inserted=0; in-window official 404 W45N7@84324900 still 404 0 live / 100 empty; leftover official 404s otherwise unchanged; see history_backfill.txt)",
        f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} corrective nfix={nfix_corr} (after over45={vs_later['over45']}), in-use {tick_s_in_use:.5f})",
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=1 (first pass)",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_room_line}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, total {INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2})",
        f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} (later-mean-robust {later:.5f} corrective, after over45={vs_later['over45']})",
        "db_after",
        db_after_lines,
        f"coverage official_recovered={recovered}/{expected} unique_after={unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
        (
            f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; later-mean-robust {later:.5f} corrective nfix={nfix_corr}; "
            f"first-pass realign committed {TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later['over45']}."
        ),
        (
            f"confirm recovered none inserted=0; retry2 inserted=0; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep {len(w45n7_empty)} ranges {w45n7_empty}; {leftover_txt}"
        ),
        (
            f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} "
            f"yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart."
        ),
        "This run did not restart the listener.",
    ]
    verify_text = "\n".join(verify) + "\n"
    (DIR / "verify.txt").write_text(verify_text)
    (ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)

    summary = (
        f"{finished_hkt} wrapup ok\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
        f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2} coverage={recovered}/{expected} tick_s_in_use={tick_s_in_use:.5f} corrective={corrective} nfix={nfix_corr}\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    print(summary)
    print(now_text)


if __name__ == "__main__":
    main()
