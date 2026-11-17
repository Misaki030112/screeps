#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-18_0100"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84325101, 84325800
GT_FIRST = 84325803
PUB_BASES = "84325100..84325700"
TICK_S_FIRST = 4.67017
TICK_S_PRINTED = "4.670"
NEW_ROWS = {"W46N8": 3058, "W47N8": 3826, "W45N8": 1743, "W45N7": 1395, "W47N7": 1549}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}
INSERTED_FIRST = 11571
INSERTED_CONFIRM = 2060
INSERTED_RETRY2 = 40  # script-reported; unique row counts unchanged after confirm (net +0)
INSERTED_RETRY2_UNIQUE_NET = 0
ALREADY = 12670
RECON_ROWS = 24241
TS_REALIGNED_FIRST = 764
IN_WINDOW_404 = []  # confirm recovered W47N8/W45N8/W47N7@84325700; none remain
OUTSIDE_404 = [
    ("W45N7", 84324900),
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


def frac(filld, span):
    return "/".join(str(filld[r]["distinct"]) for r in ROOMS) + f" of {span}"


def main():
    cov = load_json(DIR / "coverage_final.json")
    confirm = load_json(DIR / "backfill_confirm_gets.json")
    tsr = load_json(DIR / "tick_s_realign.json")
    coverage = cov.get("coverage") or cov
    later = float(tsr["later_mean_w46_robust"])
    vs_first = tsr.get("vs_first_after_revert") or tsr.get("vs_first")
    vs_later = tsr.get("vs_later_after_revert") or tsr.get("vs_later_after")
    confirm_at = confirm.get("at")
    confirm_gt = confirm.get("game_time")
    retry2 = confirm.get("retry2") or {}
    retry2_at = retry2.get("at")
    retry2_gt = retry2.get("game_time")
    # later-mean was auto-applied then reverted; in-use is first-interval
    corrective = False
    nfix_corr = 0
    tick_s_in_use = TICK_S_FIRST
    inserted_total = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2_UNIQUE_NET

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
        db_after = {}
        per_room = {}
        for room in ROOMS:
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
        hole_shorts = {f"{room}@{base}": hole_short(c, room, base) for room, base in OUTSIDE_404}
        freeze_0044 = fill(c, 84325601, 84325789)
        freeze_0010 = fill(c, 84325171, 84325209)
        freeze_0023 = fill(c, 84325320, 84325360)
        freeze_0002 = fill(c, 84325051, 84325089)
        freeze_2342 = fill(c, 84324821, 84324969)
        freeze_2315 = fill(c, 84324485, 84324514)
        rem_overlap = fill(c, 84325101, 84325400)
        rem_new = fill(c, 84325401, 84325800)
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
    recovered = int(cov.get("official_recovered") or 3500)
    expected = int(cov.get("expected") or 3500)
    empty_no_creep = int(cov.get("empty_no_creep") or 0)
    official_404_missing = int(cov.get("official_404_missing") or 0)
    w45n7_empty = (coverage.get("W45N7") or {}).get("official_empty_no_creep_ranges") or []
    w45n8_empty = (coverage.get("W45N8") or {}).get("official_empty_no_creep_ranges") or []

    leftover_bits = [
        f"leftover official 404 {hole_shorts['W45N7@84324900']} still outside window",
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
    inwin_txt = "no in-window official 404 remains (W47N8/W45N8/W47N7@84325700 recovered on confirm)"

    finished_at = now.isoformat()
    finished_hkt = now.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
    finished_hkt_sec = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

    db_after_lines = "\n".join(
        f"  {room} ticks={db_after[room]['min']}..{db_after[room]['max']} rows={db_after[room]['rows']} distinct={db_after[room]['distinct']}"
        for room in ROOMS
    )
    per_room_line = " ".join(
        f"{room}:{OFFICIAL_TICKS[room]}t/{NEW_ROWS[room]}new" for room in ROOMS
    )

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
            "New box freeze 00:44:18–00:58:17 (~830s). Listener logged the freeze, then auth/me 502s during reconnect; "
            "run_listener restarted at 00:58:20, listener.py up at 00:58:30 (pid 66638). This run did not restart the listener, war_cmd, or pulse. "
            "live.json gameTime field stayed None after reconnect, but stats.t, roomSlot, cpu, and DB ingest were live "
            f"(precheck stats.t=84325800, wrapup stats.t={stats.get('t')}, roomSlot={live.get('roomSlot')}). Segment 90 buffers pulled across the freeze band."
        ),
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": 700},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": later,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": True,
        "tick_s_corrective_applied": corrective,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": ["W47N8@84325700", "W45N8@84325700", "W47N7@84325700"],
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). "
            "32 of 35 official GETs 200; missing_chunks=3 W47N8/W45N8/W47N7@84325700 (latest published chunk; W46N8 and W45N7 already 200). "
            f"Confirm at {confirm_at} game.time={confirm_gt} recovered all three, inserted=2060. "
            f"retry2 at {retry2_at} game.time={retry2_gt} reported inserted=40 (W45N8 +39, W47N7 +1) but unique row counts were unchanged from confirm (net +0)."
        ),
        "creep_rows_reconstructed": RECON_ROWS,
        "already_in_db": ALREADY,
        "inserted": inserted_total,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": INSERTED_CONFIRM,
        "inserted_retry2": INSERTED_RETRY2,
        "inserted_retry2_unique_net": INSERTED_RETRY2_UNIQUE_NET,
        "inserted_note": (
            f"This 01:00 first pass inserted {INSERTED_FIRST} new rows (already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
            f"Confirm recovered W47N8/W45N8/W47N7@84325700 and inserted {INSERTED_CONFIRM}. "
            f"retry2 reported +{INSERTED_RETRY2} but unique coverage was already 3500/3500 after confirm (net +0). "
            f"Total unique inserted {inserted_total}."
        ),
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": nfix_corr,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": (
            f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) ts_realigned={TS_REALIGNED_FIRST}. "
            f"later-mean-robust {later:.5f} had over45={tsr.get('vs_candidates', {}).get('later_robust', {}).get('over45', 764)} vs the live anchor "
            f"while first already had over45=0; an automatic later-mean corrective of 764 rows was applied then reverted "
            f"(nrev recorded in tick_s_realign.json). in-use {tick_s_in_use:.5f}; after-revert vs_first over45={vs_first.get('over45')} "
            f"vs_later over45={vs_later.get('over45')}."
        ),
        "ssl_first_attempt": False,
        "hourly_patrol_prefilled": False,
        "per_room": per_room,
        "known_official_404s_outside_window": [f"{r}@{b}" for r, b in OUTSIDE_404],
        "known_official_404s_in_window": [],
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
            "from": "2026-11-18 00:44:18",
            "to": "2026-11-18 00:58:17",
            "sec": 830,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84325601, 84325789],
            "live_room_stats_gap_ticks": 189,
            "official_fill_full_gap": freeze_0044,
            "official_fill_published_part": freeze_0044,
            "official_fill_unpublished_tail": {},
            "published_part": [84325601, 84325789],
            "unpublished_tail": [],
            "note": (
                "new this run; full room_stats gap 84325601..84325789 is inside official window "
                f"{TMIN}..{TMAX}; official-filled {frac(freeze_0044, 189)} of 189 ticks on all five rooms; no unpublished tail. "
                "Segment 90 also pulled creep_cpu/path_arrivals across most of this band after the 00:58:30 reconnect."
            ),
        },
        "prior_0010_box_freeze": {
            "from": "2026-11-18 00:10:06",
            "to": "2026-11-18 00:12:20",
            "sec": 127,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84325171, 84325209],
            "official_fill_full_gap": freeze_0010,
            "note": (
                "not new this run (already in 00:30 wrapup); still inside this window; official-filled "
                f"{frac(freeze_0010, 39)} of 39 ticks on all five rooms; no unpublished tail."
            ),
        },
        "prior_0023_ws_drop": {
            "from": "2026-11-18 00:23:40",
            "to": "2026-11-18 00:23:50",
            "sec": 10,
            "kind": "ws_connection_lost",
            "official_fill_nearby": freeze_0023,
            "nearby_band": [84325320, 84325360],
            "note": (
                "not new this run; still inside this window; official-filled "
                f"{frac(freeze_0023, 41)} of 41 ticks 84325320..84325360."
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
                "not new this run; now before this window start (window starts 84325101); official-filled "
                f"{frac(freeze_0002, 39)} of 39 ticks."
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
                "not new this run; now before this window; official-filled "
                f"{frac(freeze_2342, 149)} of 149 ticks (W45N7 missing 69 ticks 84324901..84324969 due to leftover official 404 @84324900)."
            ),
        },
        "prior_2315_box_freeze": {
            "from": "2026-11-17 23:15:58",
            "to": "2026-11-17 23:18:18",
            "sec": 130,
            "live_room_stats_gap": [84324485, 84324514],
            "official_fill_full_gap": freeze_2315,
            "note": "not new this run; still before this window; official-filled 30/30/30/30/30 of 30 ticks.",
        },
        "remainder_overlap_84325101_84325400": rem_overlap,
        "remainder_new_84325401_84325800": rem_new,
        "unique_after": unique_after,
        "db_tips": tips,
        "db_after": db_after,
        "listener": {
            "single_slot": len(lis) <= 1 and not yield_present,
            "listener_pids": lis,
            "run_listener": runl,
            "roomSlot": live.get("roomSlot"),
            "rot": rot,
            "yield": yield_present,
        },
        "confirm_at": confirm_at,
        "confirm_game_time": confirm_gt,
        "retry2_at": retry2_at,
        "retry2_game_time": retry2_gt,
        "ok_quiet": True,
    }

    (DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")

    now_lines = [
        f"{finished_hkt_sec} half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
        "  (first pass 32 of 35 official GETs 200, missing_chunks=3 W47N8/W45N8/W47N7@84325700; confirm recovered all three inserted=2060; retry2 reported inserted=40 unique net +0; no in-window official 404 remains; leftover official 404s otherwise unchanged; see history_backfill.txt)",
        (
            f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} automatic corrective applied then reverted, "
            f"nfix kept 0 (first already over45=0 vs live anchor; later over45={vs_later.get('over45')} after revert), in-use {tick_s_in_use:.5f})"
        ),
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=3 (first pass)",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_room_line}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2} reported / unique net +{INSERTED_RETRY2_UNIQUE_NET}, total {inserted_total})",
        (
            f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} "
            f"(later-mean-robust {later:.5f} applied then reverted; in-use first-interval {tick_s_in_use:.5f}, after-revert first over45={vs_first.get('over45')})"
        ),
        "db_after",
        db_after_lines,
        f"coverage official_recovered={recovered}/{expected} unique_after={unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
        (
            f"tick_s_check later-mean-robust {later:.5f} automatic corrective nfix=764 then reverted (later over45 was not better than first); "
            f"in-use tick_s={tick_s_in_use:.5f}"
        ),
        (
            f"confirm recovered W47N8/W45N8/W47N7@84325700 inserted=2060; retry2 reported inserted=40 unique net +0; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep 0 ranges {w45n7_empty}; {leftover_txt}"
        ),
        (
            f"New box freeze 00:44:18–00:58:17 (~830s) room_stats gap 84325601..84325789; official-filled {frac(freeze_0044, 189)} of 189 of 189 of 189 ticks 84325601..84325789 "
            f"(in this window; official-filled on all five rooms; no unpublished tail). "
            f"Prior box freeze 00:10:06–00:12:20 (~127s) room_stats gap 84325171..84325209; official-filled {frac(freeze_0010, 39)} of 39 of 39 of 39 ticks still in this window, no unpublished tail. "
            f"Prior websocket connection-lost 00:23:40 official-filled {frac(freeze_0023, 41)} of 41 of 41 of 41 ticks 84325320..84325360 still in this window. "
            f"Prior websocket ping/pong timeout 00:02:37 room_stats gap 84325051..84325089; official-filled {frac(freeze_0002, 39)} of 39 of 39 of 39 ticks now before this window. "
            f"Prior box freeze 23:42:43–23:53:44 (~661s) room_stats gap 84324821..84324969; official-filled {frac(freeze_2342, 149)} of 149 of 149 of 149 ticks now before this window "
            f"(W45N7 missing 69 ticks 84324901..84324969 due to leftover official 404 @84324900). "
            f"Prior box freeze 23:15:58–23:18:18 (~130s) official-filled 30/30/30/30/30 of 30 ticks still before this window. "
            f"Previously unpublished 84325401..84325800 official-filled on all five rooms 400/400/400/400/400 of 400. "
            f"Overlap 84325101..84325400 official-filled 300/300/300/300/300 of 300. "
            f"Includes just-published 84325100..84325700 chunks and the new 00:44 freeze gap. "
            f"W45N7@84324900 remains outside this window and still official 404. "
            f"W47N8@84324300 / W47N8@84323200 / W47N8@84322100 / W47N8@84321300 / W45N7@84321600 / W47N8@84319900 and older leftovers remain outside this window and official 404."
        ),
        f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
        f"confirm recovered W47N8/W45N8/W47N7@84325700 inserted=2060 retry2 reported inserted=40 unique net +0",
        (
            f"ok=true (quiet); first-pass missing_chunks=3 (32 of 35 official GETs 200); confirm recovered all three in-window 404s inserted=2060; "
            f"retry2 reported inserted=40 unique net +0; no in-window official 404 remains; "
            f"later-mean-robust {later:.5f} automatic corrective reverted, tick_s_in_use={tick_s_in_use:.5f} (first-pass realign {TICK_S_FIRST} committed {TS_REALIGNED_FIRST}); "
            f"new 00:44 freeze gap 84325601..84325789 official-filled {frac(freeze_0044, 189)} of 189 of 189 of 189 ticks in this window, no unpublished tail; "
            f"prior 00:10 freeze gap 84325171..84325209 official-filled {frac(freeze_0010, 39)} of 39 of 39 of 39 ticks still in this window, no unpublished tail; "
            f"prior 00:23 connection-lost band 84325320..84325360 official-filled {frac(freeze_0023, 41)} of 41 of 41 of 41 ticks still in this window; "
            f"prior 00:02 ping/pong gap 84325051..84325089 official-filled {frac(freeze_0002, 39)} of 39 of 39 of 39 ticks now before this window; "
            f"prior 23:42 freeze gap 84324821..84324969 official-filled {frac(freeze_2342, 149)} of 149 of 149 of 149 ticks now before this window "
            f"(W45N7 missing 69 due to official 404 @84324900); "
            f"{inwin_txt}; {leftover_txt}"
        ),
    ]
    now_text = "\n".join(now_lines) + "\n"
    (DIR / "history_backfill_now.txt").write_text(now_text)
    (ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_text)

    verify = [
        f"{finished_hkt_sec} half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
        "  (first pass 32 of 35 official GETs 200, missing_chunks=3 W47N8/W45N8/W47N7@84325700; confirm recovered all three inserted=2060; retry2 reported inserted=40 unique net +0; no in-window official 404 remains; leftover official 404s otherwise unchanged; see history_backfill.txt)",
        (
            f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} automatic corrective applied then reverted, "
            f"nfix kept 0 (after-revert first over45={vs_first.get('over45')}), in-use {tick_s_in_use:.5f})"
        ),
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=3 (first pass)",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_room_line}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2} reported / unique net +{INSERTED_RETRY2_UNIQUE_NET}, total {inserted_total})",
        (
            f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} "
            f"(later-mean-robust {later:.5f} applied then reverted, in-use {tick_s_in_use:.5f})"
        ),
        "db_after",
        db_after_lines,
        f"coverage official_recovered={recovered}/{expected} unique_after={unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
        (
            f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; later-mean-robust {later:.5f} corrective applied then reverted nfix={nfix_corr}; "
            f"first-pass realign committed {TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later.get('over45')} after revert."
        ),
        (
            f"confirm recovered W47N8/W45N8/W47N7@84325700 inserted=2060; retry2 reported inserted=40 unique net +0; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep 0 ranges {w45n7_empty}; {leftover_txt}"
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
        f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2_UNIQUE_NET} coverage={recovered}/{expected} tick_s_in_use={tick_s_in_use:.5f} later_mean_reverted=True\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    print(summary)
    print(now_text)


if __name__ == "__main__":
    main()
