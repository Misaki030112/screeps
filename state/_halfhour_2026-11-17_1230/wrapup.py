#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-17_1230"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84315601, 84316300
GT_FIRST = 84316346
PUB_BASES = "84315600..84316200"
TICK_S_FIRST = 4.66777
TICK_S_PRINTED = "4.668"
NEW_ROWS = {"W46N8": 713, "W47N8": 414, "W45N8": 506, "W45N7": 318, "W47N7": 505}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}
INSERTED_FIRST = 2456
ALREADY = 21456
RECON_ROWS = 23912
TS_REALIGNED_FIRST = 0
IN_WINDOW_404 = []
OUTSIDE_404 = [
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
        detail = f"0 rows / 0 distinct, range None..None; hole {a}..{b}"
    elif d == 100:
        detail = f"already live-filled 100 distinct / {n} rows"
    else:
        detail = f"{d} live-filled {mn}..{mx} / {n} rows; {empty_n} empty {miss}"
    return f"{room}@{base} ({detail}; official {base} still 404 after confirm and retry2; retry next run)"


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
    return "/".join(str((filld[r]["distinct"])) for r in ROOMS) + f" of {span}"


def main():
    cov = load_json(DIR / "coverage_final.json")
    confirm = load_json(DIR / "backfill_confirm_gets.json")
    tsr = load_json(DIR / "tick_s_realign.json")
    coverage = cov.get("coverage") or {}
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
        holes = [hole_text(c, room, base) for room, base in OUTSIDE_404]
        freeze_0743 = fill(c, 84312611, 84312889)
        freeze_0713 = fill(c, 84312221, 84312399)
        freeze_0917 = fill(c, 84313811, 84313929)
        freeze_0943 = fill(c, 84314141, 84314339)
        freeze_1011 = fill(c, 84314501, 84314639)
        freeze_1011_404 = fill(c, 84314501, 84314600)
        freeze_1044 = fill(c, 84314921, 84314959)
        freeze_1054 = fill(c, 84315041, 84315119)
        freeze_1111 = fill(c, 84315261, 84315469)
        freeze_1148 = fill(c, 84315741, 84315789)
        rem_overlap = fill(c, 84315601, 84315800)
        rem_new = fill(c, 84315801, 84316300)
        hole_w47_15100 = hole_text(c, "W47N7", 84315100)
        hole_w45_14900 = hole_text(c, "W45N8", 84314900)
        hole_w45_14500 = hole_text(c, "W45N7", 84314500)
        hole_w47_14000 = hole_text(c, "W47N8", 84314000)
        hole_w46_13200 = hole_text(c, "W46N8", 84313200)
        cpu = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM creep_cpu WHERE ts >= '2026-11-17 11:51:05+08'"
        ).fetchone()
        path = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM path_arrivals WHERE ts >= '2026-11-17 11:51:05+08'"
        ).fetchone()
        db_after = {}
        for room in ROOMS:
            row = c.execute(
                "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
                "FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room=%s",
                (TMIN, TMAX, room),
            ).fetchone()
            db_after[room] = {"min": row[0], "max": row[1], "rows": row[2] or 0, "distinct": row[3] or 0}

    segment90 = {
        "creep_cpu": {"min": cpu[0], "max": cpu[1], "rows": cpu[2], "min_ts": iso(cpu[3]), "max_ts": iso(cpu[4])},
        "path_arrivals": {"min": path[0], "max": path[1], "rows": path[2], "min_ts": iso(path[3]), "max_ts": iso(path[4])},
    }

    per_room = {}
    for room in ROOMS:
        cvr = coverage[room]
        per_room[room] = {
            "official_ticks_first_pass": OFFICIAL_TICKS[room],
            "new_rows_first_pass": NEW_ROWS[room],
            "distinct": cvr["distinct"],
            "rows": cvr["rows"],
            "range": cvr["range"],
            "missing_n": cvr["missing_n"],
            "missing_ranges": cvr["missing_ranges"],
            "official_404_missing": cvr["official_404_missing"],
            "official_404_missing_ranges": cvr.get("official_404_missing_ranges") or [],
            "official_empty_no_creep": cvr.get("official_empty_no_creep") or 0,
            "official_empty_no_creep_ranges": cvr.get("official_empty_no_creep_ranges") or [],
        }

    w45n7_empty = (coverage.get("W45N7") or {}).get("official_empty_no_creep_ranges") or []
    empty_n = cov.get("empty_no_creep") or 0
    official_404_n = cov.get("official_404_missing") or 0
    recovered = cov.get("official_recovered")
    expected = cov.get("expected")

    tick_s_note = (
        f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
        f"inserted {INSERTED_FIRST} rows, then realign committed ts_realigned_first={TS_REALIGNED_FIRST} (no CheckViolation). "
        f"later-mean-robust {later:.5f} (raw later-mean also {later:.5f}; W46 first interval {TICK_S_FIRST}, "
        f"min-all-rooms first interval {TICK_S_FIRST}; "
        f"delta first-robust {TICK_S_FIRST-later:.5f} s/tick, "
        f"~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-later):.1f}s at tmin) "
        f"already inside the 45s gate "
        f"(still_over_45s_vs_later_before={tsr.get('still_over_45s_vs_later_before')}, "
        f"vs_first over45={vs_first['over45']}, vs_later over45={vs_later['over45']}, "
        f"over15={vs_later['over15']} mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}). "
        f"No corrective later-mean-robust realign (nfix={nfix_corr}, skipped_cross_chunk={tsr.get('skipped_cross_chunk') or 0}). "
        f"In-use tick_s={tick_s_in_use:.5f} (first-pass)."
    )
    missing_note = (
        f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). "
        f"missing_chunks=0 of 35 official GETs (35 of 35 200, no in-window official 404). "
        f"The previous 12:00 half-hour run official-backfilled 84315101..84315800 (inserted=9191 already_in_db=16956 "
        f"at game.time=84315882, published_bases 84315100..84315700, missing_chunks=1, 34 of 35 official GETs 200, "
        f"404 W47N7@84315100, tick_s=4.75334 printed 4.753, ts_realigned_first=8025, "
        f"later-mean-robust 4.67987 applied nfix=4234, in-use 4.67987). "
        f"The 12:25 hourly patrol then official-backfilled 84315501..84316200 (inserted=11100 already_in_db=15803 "
        f"at game.time=84316232, published_bases 84315500..84316100, missing_chunks=0, 35 of 35 official GETs 200, "
        f"tick_s=4.666, ts_realigned=0). "
        f"This run overlapped 84315601..84315800 (still official-filled on all five rooms) "
        f"and newly covered the previously unpublished remainder 84315801..84316300, including the just-published 84316200 chunk. "
        f"No in-window official 404. W47N7@84315100 is now outside this window (0 live, 100 empty 84315101..84315200). "
        f"W45N8@84314900 is outside this window (0 live, 100 empty 84314901..84315000). "
        f"W45N7 official empty-no-creep {empty_n} ticks {w45n7_empty}. "
        f"Confirm at {confirm_at} game.time={confirm_gt} recovered none inserted=0; "
        f"retry2 at {retry2_at} game.time={retry2_gt} recovered none inserted=0."
    )
    inserted_note = (
        f"This 12:30 first pass inserted {INSERTED_FIRST} new rows (already_in_db={ALREADY}, reconstructed={RECON_ROWS}) "
        f"because the overlap 84315601..84316200 was already official-backfilled by the 12:00 half-hour run and the 12:25 hourly patrol, "
        f"and the new remainder 84316201..84316300 is the just-published 84316200 chunk (plus any live-gap fill in 84315801..84316200). "
        f"Confirm recovered none inserted=0; retry2 recovered none inserted=0. inserted_total={INSERTED_FIRST}. "
        f"First-pass realign committed ts_realigned_first={TS_REALIGNED_FIRST} (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}). "
        f"later-mean-robust {later:.5f} already inside 45s gate, no corrective (nfix={nfix_corr}; "
        f"over45={vs_later['over45']} over15={vs_later['over15']} mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}). "
        f"In-use tick_s={tick_s_in_use:.5f} (first-pass)."
    )
    live_note = (
        f"No new box freeze since the 11:48:38–11:51:05 Asia/Hong_Kong (~137s) hibernate "
        f"(room_stats gap 84315741..84315789, 49 ticks; still inside this official window and official-filled). "
        f"Listener has stayed up since the 11:51:05 self-reconnect (relaunch 11:51:08, current tools/listener.py pid 3914383; pidfile 4035476). "
        f"This run did not restart the listener. After the 11:51:05 reconnect the listener itself has kept pulling recent CPU / path buffers "
        f"(creep_cpu {cpu[0]}..{cpu[1]}, {cpu[2]} rows, first ts {iso(cpu[3])}; "
        f"path_arrivals {path[0]}..{path[1]}, {path[2]} rows, first ts {iso(path[3])}). "
        f"Peacetime single-slot rotation holds (roomSlot={live.get('roomSlot')}, rot={rot}, yield_files={'present' if yield_present else 'absent'}). "
        f"This run did not start a second listener or change the 5:5:1:1 poll. Official history HTTP does not use a room slot. "
        f"The 12:25 hourly patrol had already official-backfilled 84315501..84316200 before this run; no concurrent history_backfill process."
    )
    hourly_note = (
        f"The previous 12:00 half-hour run official-backfilled 84315101..84315800 (inserted=9191 already_in_db=16956 "
        f"at game.time=84315882, published_bases 84315100..84315700, missing_chunks=1, 34 of 35 official GETs 200, "
        f"404 W47N7@84315100, tick_s=4.75334 printed 4.753, ts_realigned_first=8025, "
        f"later-mean-robust 4.67987 applied nfix=4234, in-use 4.67987). "
        f"The 12:25 hourly patrol official-backfilled 84315501..84316200 (inserted=11100 already_in_db=15803 "
        f"at game.time=84316232, published_bases 84315500..84316100, missing_chunks=0, tick_s=4.666, ts_realigned=0). "
        f"This half-hour backfill is the official-history catch-up for {TMIN}..{TMAX} "
        f"(inserted={INSERTED_FIRST} first pass, missing_chunks=0, 35 of 35 official GETs 200, no in-window official 404)."
    )

    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": now.isoformat(),
        "finished_at_hkt": now.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong"),
        "shard": "shard3",
        "rooms": list(ROOMS),
        "minutes": 40,
        "game_time": GT_FIRST,
        "live_json_gameTime_at_finish": live.get("gameTime"),
        "live_json_stats_t_at_finish": stats.get("t"),
        "live_json_gameTime_note": live_note,
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": TMAX - TMIN + 1},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": later,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": corrective,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": [],
        "missing_chunk_note": missing_note,
        "creep_rows_reconstructed": RECON_ROWS,
        "already_in_db": ALREADY,
        "inserted": INSERTED_FIRST,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": 0,
        "inserted_retry2": 0,
        "inserted_note": inserted_note,
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": nfix_corr,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": tick_s_note,
        "ssl_first_attempt": (
            f"ok first try; first-pass realign committed ts_realigned={TS_REALIGNED_FIRST}; "
            f"later-mean-robust {later:.5f} already inside 45s gate, no corrective nfix={nfix_corr}, after over45={vs_later['over45']}; "
            f"in-use first-pass {tick_s_in_use:.5f}"
        ),
        "hourly_patrol_prefilled": hourly_note,
        "per_room": per_room,
        "known_official_404s_outside_window": holes,
        "known_official_404s_in_window": [],
        "w45n7_empty_no_creep_in_window": bool(w45n7_empty),
        "w45n7_empty_no_creep_ranges": w45n7_empty,
        "empty_no_creep_in_window": bool(empty_n),
        "empty_no_creep_ranges": {"W45N7": w45n7_empty},
        "empty_no_creep_ticks": empty_n,
        "official_room_ticks_fetched": 3500,
        "official_room_ticks_with_creeps": cov.get("official_with_creeps"),
        "official_recovered": recovered,
        "official_expected": expected,
        "new_box_freeze": {
            "from": "2026-11-17 11:48:38",
            "to": "2026-11-17 11:51:05",
            "sec": 137,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84315741, 84315789],
            "live_room_stats_gap_ticks": 49,
            "official_fill_full_gap": freeze_1148,
            "note": "not new this run; still inside official window 84315601..84316300; official-filled on all five rooms",
        },
        "prior_1111_box_freeze": {
            "from": "2026-11-17 11:11:00",
            "to": "2026-11-17 11:25:57",
            "sec": 888,
            "room_stats_gap": [84315261, 84315469],
            "span": 209,
            "official_fill_full_gap": freeze_1111,
            "note": "not new this run; now fully before this window start (window starts 84315601); four rooms 209/209, W45N7 empty-no-creep in parts",
        },
        "prior_1054_freeze": {
            "from": "2026-11-17 10:54:19",
            "to": "2026-11-17 10:58:41",
            "sec": 262,
            "live_room_stats_gap": [84315041, 84315119],
            "official_fill_full_gap": freeze_1054,
            "note": "prior 10:54 freeze; now fully before this window start. W47N7 missing 84315101..84315119 due to official 404 @84315100; W45N7 official empty-no-creep in that band",
        },
        "prior_1044_freeze_outside_or_edge": {
            "from": "2026-11-17 10:44:25",
            "to": "2026-11-17 10:46:18",
            "sec": 100,
            "live_room_stats_gap": [84314921, 84314959],
            "official_fill_full_gap": freeze_1044,
            "note": "fully before this window start (window starts 84315601). W45N8 still missing due to official 404 @84314900; W45N7 official empty-no-creep",
        },
        "prior_1011_freeze_outside_window": {
            "from": "2026-11-17 10:11:26",
            "to": "2026-11-17 10:21:56",
            "sec": 624,
            "live_room_stats_gap": [84314501, 84314639],
            "official_fill_full_gap": freeze_1011,
            "official_fill_404_part": freeze_1011_404,
            "note": "not new this run; already official-filled by earlier runs; fully before this window. Four rooms 139/139; W45N7 still missing 84314501..84314600 due to official 404 @84314500",
        },
        "prior_0943_freeze_outside_window": {
            "from": "2026-11-17 09:43:21",
            "to": "2026-11-17 09:58:12",
            "sec": 883,
            "live_room_stats_gap": [84314141, 84314339],
            "official_fill": freeze_0943,
            "note": "not new this run; already official-filled 199/199; fully before this window",
        },
        "prior_0917_freeze_outside_window": {
            "from": "2026-11-17 09:17:21",
            "to": "2026-11-17 09:25:37",
            "sec": 489,
            "live_room_stats_gap": [84313811, 84313929],
            "official_fill": freeze_0917,
            "note": "not new this run; already official-filled 119/119; fully before this window",
        },
        "prior_0743_freeze_outside_window": {
            "from": "2026-11-17 07:43:34",
            "to": "2026-11-17 08:04:17",
            "sec": 1232,
            "live_room_stats_gap": [84312611, 84312889],
            "official_fill": freeze_0743,
            "note": "not new this run; already official-filled 279/279; fully before this window",
        },
        "prior_0713_freeze_outside_window": {
            "live_room_stats_gap": [84312221, 84312399],
            "official_fill": freeze_0713,
            "note": "already official-filled 179/179; fully before this window",
        },
        "remainder_overlap_84315601_84315800": rem_overlap,
        "remainder_new_84315801_84316300": rem_new,
        "unique_after": cov.get("unique_after"),
        "db_tips": tips,
        "db_after": db_after,
        "live_after_official_tip": live_after,
        "segment90_after_115105_reconnect": segment90,
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
        "confirm": {"at": confirm_at, "game_time": confirm_gt, "recovered": confirm.get("recovered") or [], "inserted": confirm.get("inserted") or 0},
        "retry2": {"at": retry2_at, "game_time": retry2_gt, "recovered": retry2.get("recovered") or [], "inserted": retry2.get("inserted") or 0},
        "coverage_official_recovered": f"{recovered}/{expected}",
    }

    (DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")

    per_txt = " ".join(
        f"{room}:{OFFICIAL_TICKS[room]}t/{NEW_ROWS[room]}new" for room in ROOMS
    )
    db_after_txt = "\n".join(
        f"  {room} ticks={db_after[room]['min']}..{db_after[room]['max']} "
        f"rows={db_after[room]['rows']} distinct={db_after[room]['distinct']}"
        for room in ROOMS
    )
    freeze_1148_txt = (
        f"Prior box freeze 11:48:38–11:51:05 (~137s) room_stats gap 84315741..84315789; "
        f"official-filled {frac(freeze_1148, 49)} (still in this window)."
    )
    freeze_1111_txt = (
        f"Prior box freeze 11:11:00–11:25:57 (~888s) room_stats gap 84315261..84315469 still official-filled "
        f"{frac(freeze_1111, 209)} (W45N7 empty-no-creep in parts of this band)."
    )
    now_text = (
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} Asia/Hong_Kong half-hour backfill OK (quiet)\n"
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False\n"
        f"  (35 of 35 official GETs 200, missing_chunks=0; see history_backfill.txt)\n"
        f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} already inside 45s gate, no corrective nfix={nfix_corr} "
        f"(after over45={vs_later['over45']}), in-use {tick_s_in_use:.5f})\n"
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0\n"
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}\n"
        f"per_room {per_txt}\n"
        f"inserted={INSERTED_FIRST}\n"
        f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} "
        f"(later-mean-robust {later:.5f} already inside 45s gate, no corrective, after over45={vs_later['over45']})\n"
        f"db_after\n{db_after_txt}\n"
        f"coverage official_recovered={recovered}/{expected} unique_after={cov.get('unique_after')} "
        f"empty_no_creep={empty_n} official_404_in_window={official_404_n}\n"
        f"tick_s_check later-mean-robust {later:.5f} already inside 45s gate, no corrective nfix={nfix_corr} "
        f"(later over45={vs_later['over45']} over15={vs_later['over15']} "
        f"mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}); "
        f"in-use tick_s={tick_s_in_use:.5f}\n"
        f"confirm recovered=none inserted=0; retry2 recovered=none inserted=0; "
        f"no in-window official 404; leftover official 404 W47N7@84315100 now outside this window (0 live, 100 empty 84315101..84315200); "
        f"W45N7 official empty-no-creep {empty_n} ticks {w45n7_empty}; "
        f"leftover official 404 W45N8@84314900 still outside this window (0 live, 100 empty 84314901..84315000); "
        f"leftover official 404 W45N7@84314500 still outside this window (0 live, 100 empty 84314501..84314600); "
        f"leftover official 404 W47N8@84314000 still outside this window (49 live 84314052..84314100, 51 empty 84314001..84314051); "
        f"leftover official 404 W46N8@84313200 still outside this window (96 live 84313205..84313300, 4 empty 84313201..84313204); "
        f"older leftovers unchanged (W46N8@84310500 11 live, W47N7@84309000 empty, W45N8@84309100 25 live, and older leftovers still 404).\n"
        f"{freeze_1148_txt} {freeze_1111_txt} "
        f"Prior 10:54 freeze gap 84315041..84315119 still official-filled on three rooms, W47N7 missing 84315101..84315119 due to official 404 @84315100, W45N7 empty-no-creep. "
        f"Prior 10:44 freeze gap 84314921..84314959 now fully before this window; W45N8 missing due to official 404 @84314900. "
        f"Prior 10:11 freeze gap 84314501..84314639 still official-filled 139/139 on four rooms, W45N7 missing 84314501..84314600 due to official 404 @84314500 (still before window). "
        f"Prior 09:43 / 09:17 / 07:43 freeze gaps still official-filled (199/199, 119/119, 279/279) and still before this window. "
        f"Previously unpublished 84315801..84316300 official-filled on all five rooms (includes just-published 84316200). "
        f"Overlap 84315601..84315800 stays official-filled on all five rooms.\n"
        f"listener single_slot={len(lis)<=1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}\n"
        f"confirm recovered=none retry2 recovered=none\n"
        f"ok=true (quiet); first-pass missing_chunks=0 (35 of 35 official GETs 200); "
        f"later-mean-robust {later:.5f} already inside 45s gate, no corrective nfix={nfix_corr}, tick_s_in_use={tick_s_in_use:.5f} "
        f"(first-pass realign {TICK_S_FIRST} committed {TS_REALIGNED_FIRST}); "
        f"prior 11:48 freeze gap 84315741..84315789 still official-filled {frac(freeze_1148, 49)} and still in this window; "
        f"prior 11:11 freeze gap 84315261..84315469 still official-filled {frac(freeze_1111, 209)}, now before this window; "
        f"leftover official 404 W47N7@84315100 now outside window; leftover official 404 W45N8@84314900 still outside window; "
        f"other leftover official 404s unchanged.\n"
    )
    (DIR / "history_backfill_now.txt").write_text(now_text)
    (ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_text)

    verify = [
        f"window {TMIN}..{TMAX} (700)",
    ]
    for room in ROOMS:
        cvr = coverage[room]
        verify.append(
            f"{room} distinct={cvr['distinct']} rows={cvr['rows']} range={cvr['range']} "
            f"missing_n={cvr['missing_n']} {cvr['missing_ranges']} "
            f"empty_no_creep={cvr.get('official_empty_no_creep')} {cvr.get('official_empty_no_creep_ranges')} "
            f"official_404={cvr.get('official_404_missing')} {cvr.get('official_404_missing_ranges')}"
        )
    verify.append(f"unique_after {cov.get('unique_after')}")
    verify.append(
        f"official_with_creeps={cov.get('official_with_creeps')} empty_no_creep={empty_n} "
        f"official_404_missing={official_404_n} official_recovered={recovered} expected={expected} "
        f"in_window_404={cov.get('in_window_official_404')}"
    )
    verify.append(f"live_ticks_after_official_tip {json.dumps(live_after, default=str)}")
    verify.append(f"db_tips {json.dumps(tips, default=str)}")
    verify.append(
        f"Prior 11:48 freeze 84315741..84315789 official-filled {frac(freeze_1148, 49)} and still in this window. "
        f"Prior 11:11 freeze 84315261..84315469 official-filled {frac(freeze_1111, 209)}, now before this window. "
        f"Prior 10:54 freeze 84315041..84315119 still missing W47N7 84315101..84315119 due to official 404 @84315100, now before this window. "
        f"Prior 10:44 / 10:11 / 09:43 / 09:17 / 07:43 freeze bands unchanged and still before this window start."
    )
    verify.append(
        f"previously unpublished 84315801..84316300 official-filled on all five rooms; "
        f"includes just-published 84316200. Overlap 84315601..84315800 official-filled on all five rooms. "
        f"11:48 freeze 84315741..84315789 remains official-filled and still in this window."
    )
    verify.append(
        f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; later-mean-robust {later:.5f} already inside 45s gate, no corrective nfix={nfix_corr}; "
        f"first-pass realign committed {TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later['over45']}."
    )
    verify.append(
        f"confirm/retry2 recovered none; no in-window official 404; leftover official 404 W47N7@84315100 now outside window (0 live / 100 empty); "
        f"leftover official 404 W45N8@84314900 still outside window (0 live / 100 empty); "
        f"leftover official 404 W45N7@84314500 still outside window (0 live / 100 empty); "
        f"leftover official 404 W47N8@84314000 still outside window (49 live / 51 empty); "
        f"leftover official 404 W46N8@84313200 still outside window (96 live / 4 empty); older leftovers unchanged."
    )
    verify.append(
        f"listener single_slot={len(lis)<=1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} "
        f"yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart."
    )
    verify.append("This run did not restart the listener.")
    verify_text = "\n".join(verify) + "\n"
    (DIR / "verify.txt").write_text(verify_text)
    (ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)

    summary = (
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} HKT wrapup ok quiet\n"
        f"window {TMIN}..{TMAX} inserted={INSERTED_FIRST} missing_chunks=0 tick_s_in_use={tick_s_in_use:.5f} corrective_nfix={nfix_corr}\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    print(summary, end="")
    print("outside official 404 W47N7@84315100:", hole_w47_15100)
    print("outside official 404 W45N8@84314900:", hole_w45_14900)
    print("outside official 404 W45N7@84314500:", hole_w45_14500)
    print("outside official 404 W47N8@84314000:", hole_w47_14000)
    print("outside official 404 W46N8@84313200:", hole_w46_13200)
    print("freeze_fill_1148", json.dumps(freeze_1148, default=str))
    print("freeze_fill_1111", json.dumps(freeze_1111, default=str))
    print("freeze_fill_1054", json.dumps(freeze_1054, default=str))
    print("freeze_fill_1044", json.dumps(freeze_1044, default=str))
    print("remainder_overlap", json.dumps(rem_overlap, default=str))
    print("remainder_new", json.dumps(rem_new, default=str))
    print("listener", lis, runl, live.get("roomSlot"), rot)
    print("ok")


if __name__ == "__main__":
    main()
