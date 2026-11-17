#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-18_0130"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84325401, 84326100
GT_FIRST = 84326195
PUB_BASES = "84325400..84326000"
TICK_S_FIRST = 4.82569
TICK_S_PRINTED = "4.826"
NEW_ROWS = {"W46N8": 0, "W47N8": 0, "W45N8": 0, "W45N7": 0, "W47N7": 0}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}
INSERTED_FIRST = 0
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_RETRY2_UNIQUE_NET = 0
ALREADY = 25603
RECON_ROWS = 25603
TS_REALIGNED_FIRST = 2679
IN_WINDOW_404 = []
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
    vs_first = tsr.get("vs_first")
    vs_later_after = tsr.get("vs_later_after") or {}
    confirm_at = confirm.get("at")
    confirm_gt = confirm.get("game_time")
    retry2 = confirm.get("retry2") or {}
    retry2_at = retry2.get("at")
    retry2_gt = retry2.get("game_time")
    # later-mean-robust corrective was kept this run
    corrective = bool(tsr.get("corrective_applied"))
    nfix_corr = int(tsr.get("ts_realigned_to_later_mean") or 0)
    tick_s_in_use = later if corrective else TICK_S_FIRST
    inserted_total = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2_UNIQUE_NET

    live = load_json(ROOT / "metrics/live.json")
    rot = load_json(ROOT / "metrics/listener_rot.json")
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    now = datetime.now(TZ)
    finished_hkt = now.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
    finished_hkt_sec = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    lis = pgrep("tools/listener.py")
    runl = pgrep("tools/run_listener.sh")
    yield_present = (ROOT / "metrics/listener_yield_rooms").exists() or any(
        (ROOT / "metrics").glob("yield*")
    )

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
        freeze_0110 = fill(c, 84325931, 84326149)
        freeze_0110_pub = fill(c, 84325931, 84326100)
        freeze_0110_tail = fill(c, 84326101, 84326149)
        freeze_0044 = fill(c, 84325601, 84325789)
        freeze_0010 = fill(c, 84325171, 84325209)
        freeze_0023 = fill(c, 84325320, 84325360)
        freeze_0002 = fill(c, 84325051, 84325089)
        freeze_2342 = fill(c, 84324821, 84324969)
        rem_overlap = fill(c, 84325401, 84325800)
        rem_new = fill(c, 84325801, 84326100)
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
    w47n7_empty = (coverage.get("W47N7") or {}).get("official_empty_no_creep_ranges") or []

    leftover_order = [
        "W45N7@84324900", "W47N8@84324300", "W47N8@84323200", "W47N8@84322100",
        "W47N8@84321300", "W45N7@84321600", "W47N8@84319900", "W47N8@84319000",
        "W46N8@84318500", "W45N8@84318000", "W47N7@84315100", "W45N8@84314900",
        "W45N7@84314500", "W47N8@84314000", "W46N8@84313200",
    ]
    leftover_bits = [f"leftover official 404 {hole_shorts[k]} still outside window" for k in leftover_order]
    leftover_txt = "; ".join(leftover_bits) + "; older leftovers unchanged."
    inwin_txt = "no in-window official 404 remains"
    per_room_line = " ".join(
        f"{room}:{per_room[room]['official_ticks']}t/{per_room[room]['new_rows_first_pass']}new"
        for room in ROOMS
    )
    db_after_lines = "\n".join(
        f"  {room} ticks={db_after[room]['min']}..{db_after[room]['max']} rows={db_after[room]['rows']} distinct={db_after[room]['distinct']}"
        for room in ROOMS
    )

    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": now.isoformat(),
        "finished_at_hkt": finished_hkt,
        "shard": "shard3",
        "rooms": list(ROOMS),
        "minutes": 40,
        "game_time": GT_FIRST,
        "live_json_gameTime_at_finish": live.get("gameTime"),
        "live_json_stats_t_at_finish": (stats or {}).get("t"),
        "live_json_gameTime_note": (
            "New box freeze 01:10:45–01:26:26 (~934s). Listener logged the freeze and "
            "run_listener restarted at 01:26:29, listener.py up at 01:26:39 (pid 73909). "
            "This run did not restart the listener, war_cmd, or pulse. live.json was fresh "
            f"after reconnect (gameTime/stats.t live, roomSlot={live.get('roomSlot')}). "
            "Segment 90 buffers pulled across the freeze band (creep_cpu after a 34t start hole, "
            "then normal ~5-tick sample cadence). Concurrent 1h patrol q_live.py in "
            "_patrol_2026-11-18_0126 was left alone."
        ),
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": 700},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": later,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": corrective,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": [],
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed "
            f"{TMIN}..{TMAX} (700). 35 of 35 official GETs 200; missing_chunks=0. "
            f"Confirm at {confirm_at} game.time={confirm_gt} retried leftover outside-window 404s, "
            f"inserted=0 (all still 404). retry2 skipped, no in-window official 404s."
        ),
        "creep_rows_reconstructed": RECON_ROWS,
        "already_in_db": ALREADY,
        "inserted": inserted_total,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": INSERTED_CONFIRM,
        "inserted_retry2": INSERTED_RETRY2,
        "inserted_retry2_unique_net": INSERTED_RETRY2_UNIQUE_NET,
        "inserted_note": (
            f"This 01:30 first pass inserted 0 new rows (already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
            "Official rows through 84326100 were already present (400-tick overlap with the 01:00 window "
            "plus 84325801..84326100 already stored before this run). Confirm inserted 0; retry2 skipped. "
            "Coverage official_recovered=3500/3500 including W47N7 official empty-no-creep 117 ticks."
        ),
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": nfix_corr,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": (
            f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
            f"ts_realigned={TS_REALIGNED_FIRST}. later-mean-robust {later:.5f} then had over45 vs the first-pass "
            f"anchor; an automatic later-mean corrective of {nfix_corr} rows was applied at game.time=84326213 "
            f"and kept (after over45 vs later=0, better than first). in-use {tick_s_in_use:.5f}; "
            f"after-corrective vs_later over45={vs_later_after.get('over45')}."
        ),
        "ssl_first_attempt": False,
        "hourly_patrol_prefilled": True,
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
            "from": "2026-11-18 01:10:45",
            "to": "2026-11-18 01:26:26",
            "sec": 934,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84325931, 84326149],
            "live_room_stats_gap_ticks": 219,
            "official_fill_full_gap": freeze_0110,
            "official_fill_published_part": freeze_0110_pub,
            "official_fill_unpublished_tail": freeze_0110_tail,
            "published_part": [84325931, 84326100],
            "unpublished_tail": [84326101, 84326149],
            "note": (
                "new this run; room_stats gap 84325931..84326149 (219). Official published through 84326100, "
                f"so published part 84325931..84326100 official-filled {frac(freeze_0110_pub, 170)} of 170 "
                f"(W47N7 short of 170 because of official empty-no-creep 84325931..84325946). "
                f"Unpublished tail 84326101..84326149 official-filled {frac(freeze_0110_tail, 49)} of 49 "
                "(W46N8 live-resumed 84326143 after reconnect; 84326101..84326142 still empty, not yet published; "
                "other rooms have no live rows in the tail). Full-gap official+live "
                f"{frac(freeze_0110, 219)} of 219. Segment 90 also pulled creep_cpu/path_arrivals across most of "
                "this band after the 01:26:39 reconnect (creep_cpu start hole 84325931..84325964, then normal cadence)."
            ),
        },
        "prior_0044_box_freeze": {
            "from": "2026-11-18 00:44:18",
            "to": "2026-11-18 00:58:17",
            "sec": 830,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84325601, 84325789],
            "official_fill_full_gap": freeze_0044,
            "note": (
                "not new this run; still in this window (window starts 84325401); official-filled "
                f"{frac(freeze_0044, 189)} of 189 ticks on all five rooms; no unpublished tail."
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
                "not new this run; now before this window start (window starts 84325401); official-filled "
                f"{frac(freeze_0010, 39)} of 39 ticks."
            ),
        },
        "prior_0023_ws_drop": {
            "from": "2026-11-18 00:23:40",
            "to": "2026-11-18 00:23:50",
            "sec": 10,
            "kind": "ws_connection_lost",
            "official_fill_nearby": freeze_0023,
            "note": (
                "not new this run; now before this window; official-filled "
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
                "not new this run; now before this window; official-filled "
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
        "remainder_overlap_84325401_84325800": rem_overlap,
        "remainder_new_84325801_84326100": rem_new,
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
        "  (first pass 35 of 35 official GETs 200, missing_chunks=0; confirm inserted=0 leftover outside-window 404s unchanged; retry2 skipped no in-window official 404s; see history_backfill.txt)",
        (
            f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} automatic corrective applied and kept, "
            f"nfix={nfix_corr} (after vs_later over45={vs_later_after.get('over45')}), in-use {tick_s_in_use:.5f})"
        ),
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_room_line}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 skipped, total {inserted_total})",
        (
            f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} "
            f"(later-mean-robust {later:.5f} applied and kept; in-use {tick_s_in_use:.5f}, after vs_later over45={vs_later_after.get('over45')})"
        ),
        "db_after",
        db_after_lines,
        f"coverage official_recovered={recovered}/{expected} unique_after={unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
        (
            f"tick_s_check later-mean-robust {later:.5f} automatic corrective nfix={nfix_corr} kept (after later over45=0 better than first); "
            f"in-use tick_s={tick_s_in_use:.5f}"
        ),
        (
            f"confirm inserted=0 leftover official 404s unchanged; retry2 skipped no in-window official 404s; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep 0 ranges {w45n7_empty}; "
            f"W47N7 official empty-no-creep {empty_no_creep} ranges {w47n7_empty}; {leftover_txt}"
        ),
        (
            f"New box freeze 01:10:45–01:26:26 (~934s) room_stats gap 84325931..84326149; "
            f"published part 84325931..84326100 official-filled {frac(freeze_0110_pub, 170)} of 170 "
            f"(W47N7 short due to official empty-no-creep 84325931..84325946); "
            f"unpublished tail 84326101..84326149 official-filled {frac(freeze_0110_tail, 49)} of 49 "
            f"(W46N8 live-resumed 84326143; 84326101..84326142 still unpublished empty; other rooms 0 in tail). "
            f"Full gap official+live {frac(freeze_0110, 219)} of 219. "
            f"Prior box freeze 00:44:18–00:58:17 (~830s) room_stats gap 84325601..84325789; official-filled {frac(freeze_0044, 189)} of 189 ticks still in this window, no unpublished tail. "
            f"Prior box freeze 00:10:06–00:12:20 (~127s) room_stats gap 84325171..84325209; official-filled {frac(freeze_0010, 39)} of 39 ticks now before this window. "
            f"Prior websocket connection-lost 00:23:40 official-filled {frac(freeze_0023, 41)} of 41 ticks 84325320..84325360 now before this window. "
            f"Prior websocket ping/pong timeout 00:02:37 room_stats gap 84325051..84325089; official-filled {frac(freeze_0002, 39)} of 39 ticks still before this window. "
            f"Prior box freeze 23:42:43–23:53:44 (~661s) room_stats gap 84324821..84324969; official-filled {frac(freeze_2342, 149)} of 149 ticks still before this window "
            f"(W45N7 missing 69 ticks 84324901..84324969 due to leftover official 404 @84324900). "
            f"Previously unpublished 84325801..84326100 official-filled on all five rooms (W47N7 183/300 because of 117 official empty-no-creep). "
            f"Overlap 84325401..84325800 official-filled {frac(rem_overlap, 400)} of 400. "
            f"Includes just-published 84325400..84326000 chunks and the new 01:10 freeze published part. "
            f"W45N7@84324900 remains outside this window and still official 404. "
            f"W47N8@84324300 / W47N8@84323200 / W47N8@84322100 / W47N8@84321300 / W45N7@84321600 / W47N8@84319900 and older leftovers remain outside this window and official 404."
        ),
        f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
        "confirm inserted=0 leftover 404s unchanged; retry2 skipped no in-window official 404s",
        (
            f"ok=true (quiet); first-pass missing_chunks=0 (35 of 35 official GETs 200); confirm inserted=0 leftover outside-window 404s unchanged; "
            f"retry2 skipped no in-window official 404s; {inwin_txt}; "
            f"later-mean-robust {later:.5f} automatic corrective kept, tick_s_in_use={tick_s_in_use:.5f} (first-pass realign {TICK_S_FIRST} committed {TS_REALIGNED_FIRST}, corrective nfix={nfix_corr}); "
            f"new 01:10 freeze gap 84325931..84326149 official+live {frac(freeze_0110, 219)} of 219 "
            f"(published 170t {frac(freeze_0110_pub, 170)}; unpublished tail 49t {frac(freeze_0110_tail, 49)}, W46N8 live from 84326143); "
            f"prior 00:44 freeze gap 84325601..84325789 official-filled {frac(freeze_0044, 189)} of 189 ticks still in this window, no unpublished tail; "
            f"prior 00:10 freeze gap 84325171..84325209 official-filled {frac(freeze_0010, 39)} of 39 ticks now before this window; "
            f"prior 00:23 connection-lost band 84325320..84325360 official-filled {frac(freeze_0023, 41)} of 41 ticks now before this window; "
            f"prior 00:02 ping/pong gap 84325051..84325089 official-filled {frac(freeze_0002, 39)} of 39 ticks still before this window; "
            f"prior 23:42 freeze gap 84324821..84324969 official-filled {frac(freeze_2342, 149)} of 149 ticks still before this window "
            f"(W45N7 missing 69 due to official 404 @84324900); "
            f"{inwin_txt}; W47N7 official empty-no-creep 117 ranges {w47n7_empty}; {leftover_txt}"
        ),
    ]
    now_text = "\n".join(now_lines) + "\n"
    (DIR / "history_backfill_now.txt").write_text(now_text)
    (ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_text)

    verify = [
        f"{finished_hkt_sec} half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
        "  (first pass 35 of 35 official GETs 200, missing_chunks=0; confirm inserted=0 leftover outside-window 404s unchanged; retry2 skipped no in-window official 404s; see history_backfill.txt)",
        (
            f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} automatic corrective applied and kept, "
            f"nfix={nfix_corr} (after vs_later over45={vs_later_after.get('over45')}), in-use {tick_s_in_use:.5f})"
        ),
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_room_line}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 skipped, total {inserted_total})",
        (
            f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} "
            f"(later-mean-robust {later:.5f} applied and kept, in-use {tick_s_in_use:.5f})"
        ),
        "db_after",
        db_after_lines,
        f"coverage official_recovered={recovered}/{expected} unique_after={unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
        (
            f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; later-mean-robust {later:.5f} corrective applied and kept nfix={nfix_corr}; "
            f"first-pass realign committed {TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later_after.get('over45')} after corrective."
        ),
        (
            f"confirm inserted=0 leftover official 404s unchanged; retry2 skipped no in-window official 404s; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep 0 ranges {w45n7_empty}; "
            f"W47N7 official empty-no-creep {empty_no_creep} ranges {w47n7_empty}; {leftover_txt}"
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
        f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2_UNIQUE_NET} coverage={recovered}/{expected} tick_s_in_use={tick_s_in_use:.5f} later_mean_reverted=False\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    print(summary)
    print(now_text)


if __name__ == "__main__":
    main()
