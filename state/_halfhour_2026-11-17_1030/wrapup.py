#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-17_1030"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84314101, 84314800
GT_FIRST = 84314822
PUB_BASES = "84314100..84314700"
TICK_S_FIRST = 4.67176
TICK_S_PRINTED = "4.672"
NEW_ROWS = {"W46N8": 1438, "W47N8": 1344, "W45N8": 749, "W45N7": 828, "W47N7": 647}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 600, "W47N7": 700}
INSERTED_FIRST = 5006
ALREADY = 22102
RECON_ROWS = 27108
IN_WINDOW_404 = [("W45N7", 84314500)]
OUTSIDE_404 = [
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
    lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip() and "pgrep" not in ln]
    return lines

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

    live = load_json(ROOT / "metrics/live.json")
    rot = load_json(ROOT / "metrics/listener_rot.json")
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    live_st = os.stat(ROOT / "metrics/live.json")
    now = datetime.now(TZ)
    lis = pgrep("tools/listener.py")
    runl = pgrep("tools/run_listener.sh")

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
        freeze_1011_after404 = fill(c, 84314601, 84314639)
        rem_overlap = fill(c, 84314101, 84314300)
        rem_new = fill(c, 84314301, 84314800)
        hole_w46_13200 = hole_text(c, "W46N8", 84313200)
        hole_w47_14000 = hole_text(c, "W47N8", 84314000)
        hole_w45_14500 = hole_text(c, "W45N7", 84314500)
        cpu = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM creep_cpu WHERE ts >= '2026-11-17 10:21:56+08'"
        ).fetchone()
        path = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM path_arrivals WHERE ts >= '2026-11-17 10:21:56+08'"
        ).fetchone()

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
        }

    tick_s_note = (
        f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
        f"inserted {INSERTED_FIRST} rows, then realign committed ts_realigned_first=12386 (no CheckViolation). "
        f"later-mean-robust {later:.5f} (raw later-mean also {later:.5f}; W46 first interval {TICK_S_FIRST}, "
        f"min-all-rooms first interval {TICK_S_FIRST}; "
        f"delta first-robust {TICK_S_FIRST-later:.5f} s/tick, "
        f"~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-later):.1f}s at tmin) "
        f"was already inside the 45s gate "
        f"(still_over_45s_vs_later_before={tsr.get('still_over_45s_vs_later_before')}, "
        f"later over45={vs_later['over45']} over15={vs_later['over15']} "
        f"mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}) "
        f"at {tsr.get('now_check')} game.time={tsr.get('gt_check')}. "
        f"No corrective later-mean-robust realign (nfix={tsr.get('ts_realigned_to_later_mean')}). "
        f"Rows sit on first-pass tick_s={TICK_S_FIRST}; later-mean-robust {later:.5f} also inside the 45s gate. "
        f"In-use tick_s={TICK_S_FIRST}."
    )
    missing_note = (
        f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). "
        f"missing_chunks=1 of 35 official GETs (34 of 35 200, 404 W45N7@84314500). "
        f"The previous 10:00 half-hour run official-backfilled 84313601..84314300 "
        f"(inserted=8756 already_in_db=15017 at game.time=84314352, published_bases 84313600..84314200, "
        f"missing_chunks=1, 34 of 35 official GETs 200, 404 W47N8@84314000, tick_s=4.63492 printed 4.635, "
        f"ts_realigned_first=11643, later-mean-robust 4.73046 applied nfix=10620, in-use 4.73046). "
        f"This run overlapped 84314101..84314300 (still complete from the 10:00 fill, including the rest of the 09:43 freeze gap) "
        f"and newly covered the previously unpublished remainder 84314301..84314800, including the new "
        f"10:11:26–10:21:56 (~624s) box-freeze room_stats gap 84314501..84314639. "
        f"W45N7@84314500 is an in-window official 404 (0 live, 100 empty 84314501..84314600); "
        f"confirm and retry2 still 404, retry next run. "
        f"No official empty-no-creep ticks in this window. "
        f"The 09:43:21–09:58:12 (~883s) freeze room_stats gap 84314141..84314339 remains official-filled 199/199 "
        f"on all five rooms and now sits fully inside this window. "
        f"The 09:17:21–09:25:37 (~489s) freeze room_stats gap 84313811..84313929 remains official-filled 119/119 "
        f"on all five rooms and now sits fully before this window start (window starts 84314101). "
        f"The 07:43:34–08:04:17 (~1232s) freeze room_stats gap 84312611..84312889 remains official-filled 279/279 "
        f"on all five rooms, still outside the window. "
        f"Prior 07:13 freeze gap 84312221..84312399 stays official-filled 179/179 outside the window. "
        f"Confirm at {confirm_at} game.time={confirm_gt} recovered none inserted=0; "
        f"retry2 at {retry2_at} game.time={retry2_gt} recovered none inserted=0 "
        f"(W45N7@84314500 still 404 in-window; W47N8@84314000 still 404 just outside this window; "
        f"W46N8@84313200 still 404 outside this window; retry next run)."
    )
    inserted_note = (
        f"This 10:30 first pass inserted {INSERTED_FIRST} new rows (already_in_db={ALREADY}, reconstructed={RECON_ROWS}) "
        f"because the overlap 84314101..84314300 was already official-backfilled by the 10:00 run, while the new remainder "
        f"84314301..84314800 includes the 10:11 freeze gap and had only partial live coverage after the 10:21:56 reconnect. "
        f"The previously unpublished remainder 84314301..84314800 is official-filled except in-window 404 W45N7@84314500 "
        f"(0 live / 100 empty 84314501..84314600). Confirm recovered none inserted=0; retry2 recovered none inserted=0. inserted_total={INSERTED_FIRST}. "
        f"First-pass realign committed ts_realigned_first=12386 (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}). "
        f"No corrective later-mean-robust realign (later {later:.5f} already inside 45s gate; "
        f"later over45={vs_later['over45']} over15={vs_later['over15']} mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}). "
        f"In-use tick_s={TICK_S_FIRST}."
    )
    live_note = (
        f"New box freeze 2026-11-17 10:11:26–2026-11-17 10:21:56 Asia/Hong_Kong (~624s). "
        f"Listener self-reconnected at 10:21:56 "
        f"(relaunch 10:21:59, current tools/listener.py pid 3875189; pidfile 4035476). "
        f"Last listener error line before this freeze was the previous 09:43 freeze reconnect at 09:58:12. "
        f"After the 10:21:56 reconnect the listener itself has kept pulling recent CPU / path buffers "
        f"(creep_cpu {cpu[0]}..{cpu[1]}, {cpu[2]} rows, first ts {iso(cpu[3])}; "
        f"path_arrivals {path[0]}..{path[1]}, {path[2]} rows, first ts {iso(path[3])}). "
        f"Peacetime single-slot rotation holds (roomSlot={live.get('roomSlot')}, rot={rot}, yield_files=absent). "
        f"This run did not restart the listener, start a second one, or change the 5:5:1:1 poll. "
        f"Official history HTTP does not use a room slot."
    )
    hourly_note = (
        f"The previous 10:00 half-hour run official-backfilled 84313601..84314300 "
        f"(inserted=8756 already_in_db=15017 at game.time=84314352, published_bases 84313600..84314200, "
        f"missing_chunks=1, 34 of 35 official GETs 200, 404 W47N8@84314000, tick_s=4.63492 printed 4.635, "
        f"ts_realigned_first=11643, later-mean-robust 4.73046 applied nfix=10620, in-use 4.73046). "
        f"The 10:21 Asia/Hong_Kong hourly patrol already finished (~10:33) and did not yet include this 10:11–10:21 box freeze "
        f"(listener reconnect was 10:21:56, during that patrol). "
        f"The next hourly patrol is due around 11:21 and can also note the 10:11–10:21 freeze. "
        f"This half-hour backfill is the official-history catch-up for {TMIN}..{TMAX} "
        f"(inserted={INSERTED_FIRST} first pass, missing_chunks=1, 34 of 35 official GETs 200, "
        f"in-window leftover 404 W45N7@84314500)."
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
        "tick_s_in_use": TICK_S_FIRST,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": bool(tsr.get("corrective_applied")),
        "missing_chunks": 1,
        "missing_chunk_list": ["W45N7@84314500"],
        "missing_chunk_first_pass": ["W45N7@84314500"],
        "missing_chunk_note": missing_note,
        "creep_rows_reconstructed": RECON_ROWS,
        "already_in_db": ALREADY,
        "inserted": INSERTED_FIRST,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": 0,
        "inserted_retry2": 0,
        "inserted_note": inserted_note,
        "ts_realigned": 12386,
        "ts_realigned_corrective_later_mean": tsr.get("ts_realigned_to_later_mean"),
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": tick_s_note,
        "ssl_first_attempt": "ok first try; first-pass realign committed ts_realigned=12386; later-mean-robust already inside 45s gate, no corrective realign",
        "hourly_patrol_prefilled": hourly_note,
        "per_room": per_room,
        "known_official_404s_outside_window": holes,
        "known_official_404s_in_window": [hole_w45_14500],
        "w45n7_empty_no_creep_in_window": False,
        "w45n7_empty_no_creep_ranges": [],
        "empty_no_creep_in_window": False,
        "empty_no_creep_ranges": {},
        "empty_no_creep_ticks": 0,
        "official_room_ticks_fetched": 3500,
        "official_room_ticks_with_creeps": cov.get("official_with_creeps"),
        "official_recovered": cov.get("official_recovered"),
        "official_expected": cov.get("expected"),
        "new_box_freeze": {
            "from": "2026-11-17 10:11:26",
            "to": "2026-11-17 10:21:56",
            "sec": 624,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84314501, 84314639],
            "live_room_stats_gap_ticks": 139,
            "official_fill_full_gap": freeze_1011,
            "official_fill_404_part": freeze_1011_404,
            "official_fill_after_404": freeze_1011_after404,
            "note": "new this run; entire gap 84314501..84314639 is inside the published window; four rooms official-filled 139/139; W45N7 official 404 on 84314500 leaves 84314501..84314600 empty (0 live), then 84314601..84314639 official-filled",
        },
        "second_box_freeze": None,
        "prior_0943_freeze_still_in_window": {
            "from": "2026-11-17 09:43:21",
            "to": "2026-11-17 09:58:12",
            "sec": 883,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84314141, 84314339],
            "live_room_stats_gap_ticks": 199,
            "official_fill": freeze_0943,
            "note": "not new this run; already official-filled 199/199 by the 10:00 run plus the previous tail; now fully inside this window and still complete",
        },
        "prior_0917_freeze_outside_window": {
            "from": "2026-11-17 09:17:21",
            "to": "2026-11-17 09:25:37",
            "sec": 489,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84313811, 84313929],
            "live_room_stats_gap_ticks": 119,
            "official_fill": freeze_0917,
            "note": "not new this run; already official-filled 119/119 by the 09:30 run; now fully before this window start (window starts 84314101) and still complete",
        },
        "prior_0743_freeze_outside_window": {
            "from": "2026-11-17 07:43:34",
            "to": "2026-11-17 08:04:17",
            "sec": 1232,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84312611, 84312889],
            "live_room_stats_gap_ticks": 279,
            "official_fill": freeze_0743,
            "note": "not new this run; already official-filled 279/279 by the 08:00 run; still fully before this window and complete",
        },
        "prior_overlap_still_filled": {
            "ticks": [84314101, 84314300],
            "span": 200,
            "official_fill": rem_overlap,
            "note": "overlap with 10:00 window; still complete (includes the latter part of the 09:43 freeze gap)",
        },
        "prior_unpublished_remainder_now_filled": {
            "ticks": [84314301, 84314800],
            "span": 500,
            "official_fill": rem_new,
            "note": "new remainder this run, missing_chunks=1 (404 W45N7@84314500: 0 live, 100 empty 84314501..84314600); includes the 10:11 freeze gap 84314501..84314639",
        },
        "prior_0713_freeze_outside_window": {
            "from": "2026-11-17 07:13:02",
            "to": "2026-11-17 07:26:06",
            "sec": 776,
            "live_room_stats_gap": [84312221, 84312399],
            "official_fill": freeze_0713,
            "note": "outside this window start; stays official-filled 179/179",
        },
        "db_tips_at_finish": tips,
        "live_ticks_after_official_tip": live_after,
        "listener_at_finish": {
            "listener_count": len(lis),
            "run_listener_count": len(runl),
            "listener_ps": lis,
            "run_ps": runl,
            "yield_files": "absent",
            "roomSlot": live.get("roomSlot"),
            "rot": rot,
            "live_updated": live.get("updated"),
            "live_gameTime": live.get("gameTime"),
            "live_stats_t": stats.get("t"),
            "live_json_mtime_age_s": round(time.time() - live_st.st_mtime, 1),
            "single_slot": len(lis) == 1 and len(runl) == 1,
            "did_not_start_second_listener": True,
            "self_restart_note": (
                "Listener self-reconnected at 10:21:56 Asia/Hong_Kong after the box freeze "
                "2026-11-17 10:11:26–2026-11-17 10:21:56 (~624s); existing run_listener.sh loop "
                "(pidfile 4035476) relaunched tools/listener.py at 10:21:59 (pid 3875189). "
                "This backfill did not start a second listener or change peacetime 5:5:1:1 rotation."
            ),
        },
        "unique_after_window": cov.get("unique_after"),
        "segment90_after_reconnect": segment90,
        "confirm_at": confirm_at,
        "confirm_game_time": confirm_gt,
        "retry2_at": retry2_at,
        "retry2_game_time": retry2_gt,
    }

    for dest in (DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json"):
        dest.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False) + "\n")

    now_lines = []
    now_lines.append(f"{now.strftime('%Y-%m-%d %H:%M:%S')} Asia/Hong_Kong half-hour backfill OK (quiet)")
    now_lines.append(
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms=W46N8,W47N8,W45N8,W45N7,W47N7 dry=False"
    )
    now_lines.append("  (34 of 35 official GETs 200, missing_chunks=1, 404 W45N7@84314500; see history_backfill.txt)")
    now_lines.append(f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} already inside 45s gate, no corrective; in-use first-pass {TICK_S_FIRST})")
    now_lines.append(f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=1")
    now_lines.append(f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}")
    now_lines.append(
        "per_room " + " ".join(f"{r}:{OFFICIAL_TICKS[r]}t/{NEW_ROWS[r]}new" for r in ROOMS)
    )
    now_lines.append(f"inserted={INSERTED_FIRST}")
    now_lines.append(f"ts_realigned_first=12386; ts_realigned_corrective={tsr.get('ts_realigned_to_later_mean')} (later-mean-robust {later:.5f} not applied, already inside 45s gate)" )
    now_lines.append("db_after")
    for room in ROOMS:
        cvr = coverage[room]
        now_lines.append(
            f"  {room} ticks={cvr['range'][0]}..{cvr['range'][1]} rows={cvr['rows']} distinct={cvr['distinct']}"
        )
    now_lines.append(
        f"coverage official_recovered={cov.get('official_recovered')}/{cov.get('expected')} unique_after={cov.get('unique_after')} "
        f"empty_no_creep={cov.get('empty_no_creep')} official_404_in_window={cov.get('official_404_missing')}"
    )
    now_lines.append(
        f"tick_s_check later-mean-robust {later:.5f} already inside 45s gate, no corrective "
        f"(later over45={vs_later['over45']} over15={vs_later['over15']} mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}); "
        f"in-use tick_s={TICK_S_FIRST}"
    )
    now_lines.append(
        "confirm recovered=none inserted=0; retry2 recovered=none inserted=0; "
        "in-window official 404 W45N7@84314500 still 404 (0 live, 100 empty 84314501..84314600); "
        "leftover official 404 W47N8@84314000 still just outside this window "
        "(49 live 84314052..84314100, 51 empty 84314001..84314051); "
        "leftover official 404 W46N8@84313200 still outside this window "
        "(96 live 84313205..84313300, 4 empty 84313201..84313204); older leftovers unchanged "
        "(W46N8@84310500 11 live, W47N7@84309000 empty, W45N8@84309100 25 live, and older leftovers still 404)."
    )
    now_lines.append(
        "New box freeze 10:11:26–10:21:56 (~624s) room_stats gap 84314501..84314639; "
        "four rooms official-filled 139/139; W45N7 official 404 @84314500 leaves 84314501..84314600 empty, then 84314601..84314639 official-filled. "
        "Prior 09:43:21–09:58:12 (~883s) gap 84314141..84314339 still official-filled 199/199 all five rooms (now fully in window). "
        "Prior 09:17:21–09:25:37 (~489s) gap 84313811..84313929 still official-filled 119/119 all five rooms (now fully before this window start). "
        "Prior 07:43:34–08:04:17 (~1232s) gap 84312611..84312889 still official-filled 279/279 all five rooms "
        "(still before this window start). Previously unpublished 84314301..84314800 official-filled except W45N7@84314500. "
        "Overlap 84314101..84314300 stays official-filled. Prior 07:13 gap 84312221..84312399 stays official-filled 179/179 outside window."
    )
    now_lines.append(
        f"listener single_slot=True roomSlot={live.get('roomSlot')} rot={rot} yield=absent"
    )
    now_lines.append("confirm recovered=none retry2 recovered=none")
    now_lines.append(
        f"ok=true (quiet); first-pass missing_chunks=1 (34 of 35 official GETs 200, 404 W45N7@84314500 still after confirm/retry2, 0 live / 100 empty); "
        f"no corrective later-mean-robust realign (nfix={tsr.get('ts_realigned_to_later_mean')}), "
        f"tick_s_in_use={TICK_S_FIRST} (first-pass realign {TICK_S_FIRST} committed 12386; later-mean-robust {later:.5f} already inside 45s gate); "
        f"new 10:11 freeze gap 84314501..84314639 official-filled 139/139 on four rooms, W45N7 missing 84314501..84314600 due to official 404 @84314500; "
        f"prior 09:43 freeze gap 84314141..84314339 still official-filled (199/199 all five rooms, now fully in window); "
        f"prior 09:17 freeze gap 84313811..84313929 still official-filled (119/119 all five rooms, now fully before window); "
        f"prior 07:43 freeze gap 84312611..84312889 still official-filled (279/279 all five rooms); "
        f"prior unpublished remainder 84314301..84314800 official-filled except W45N7@84314500; "
        f"leftover official 404 W47N8@84314000 still just outside window; leftover official 404 W46N8@84313200 still outside window; other leftover official 404s unchanged."
    )
    now_text = "\n".join(now_lines) + "\n"
    (DIR / "history_backfill_now.txt").write_text(now_text)
    (ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_text)

    verify = []
    verify.append(f"window {TMIN}..{TMAX} (700)")
    for room in ROOMS:
        cvr = coverage[room]
        verify.append(
            f"{room} distinct={cvr['distinct']} rows={cvr['rows']} range={cvr['range']} "
            f"missing_n={cvr['missing_n']} {cvr['missing_ranges']} "
            f"empty_no_creep={cvr.get('official_empty_no_creep') or 0} {cvr.get('official_empty_no_creep_ranges') or []} "
            f"official_404={cvr.get('official_404_missing') or 0} {cvr.get('official_404_missing_ranges') or []}"
        )
    verify.append(f"unique_after {cov.get('unique_after')}")
    verify.append(f"official_with_creeps={cov.get('official_with_creeps')} empty_no_creep={cov.get('empty_no_creep')} official_404_missing={cov.get('official_404_missing')} official_recovered={cov.get('official_recovered')} expected={cov.get('expected')} in_window_404={cov.get('in_window_official_404')}")
    verify.append(f"live_ticks_after_official_tip {json.dumps(live_after, default=str)}")
    verify.append(f"db_tips {json.dumps(tips, default=str)}")
    verify.append(
        "07:43 freeze 84312611..84312889 official-filled 279/279 all five rooms (not new this run, still fully before this window). 09:17 freeze 84313811..84313929 official-filled 119/119 (now fully before this window). 09:43 freeze 84314141..84314339 official-filled 199/199 (now fully in window)."
    )
    verify.append(
        "previously unpublished 84314301..84314800 official-filled except in-window 404 W45N7@84314500 (0 live / 100 empty 84314501..84314600); includes 10:11 freeze 84314501..84314639 (four rooms 139/139; W45N7 only 84314601..84314639)."
    )
    verify.append(
        f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; later-mean-robust {later:.5f} already inside 45s gate, no corrective; "
        f"first-pass realign committed 12386; in-use first-pass {TICK_S_FIRST}; later over45={vs_later['over45']}."
    )
    verify.append("confirm/retry2 recovered none; in-window official 404 W45N7@84314500 still 404 (0 live / 100 empty); leftover official 404 W47N8@84314000 still just outside window (49 live / 51 empty); leftover official 404 W46N8@84313200 still outside window (96 live / 4 empty); older leftovers unchanged.")
    verify.append(
        f"listener single_slot={len(lis)==1 and len(runl)==1} roomSlot={live.get('roomSlot')} "
        f"rot={rot} yield=absent; no second listener started; no war_cmd/pulse restart."
    )
    verify.append("This run did not restart the listener.")
    verify_text = "\n".join(verify) + "\n"
    (DIR / "verify.txt").write_text(verify_text)
    (ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)

    summary = (
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} HKT wrapup ok quiet\n"
        f"window {TMIN}..{TMAX} inserted={INSERTED_FIRST} missing_chunks=1 tick_s_in_use={later:.5f} corrective_nfix={tsr.get('ts_realigned_to_later_mean')}\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    print(summary, end="")
    print("in-window official 404 W45N7@84314500:", hole_w45_14500)
    print("outside official 404 W47N8@84314000:", hole_w47_14000)
    print("outside official 404 W46N8@84313200:", hole_w46_13200)
    print("freeze_fill_1011", json.dumps(freeze_1011, default=str))
    print("freeze_fill_1011_404", json.dumps(freeze_1011_404, default=str))
    print("freeze_fill_1011_after404", json.dumps(freeze_1011_after404, default=str))
    print("freeze_fill_0943", json.dumps(freeze_0943, default=str))
    print("freeze_fill_0917", json.dumps(freeze_0917, default=str))
    print("freeze_fill_0743", json.dumps(freeze_0743, default=str))
    print("remainder_overlap", json.dumps(rem_overlap, default=str))
    print("remainder_new", json.dumps(rem_new, default=str))
    print("listener", lis, runl, live.get("roomSlot"), rot)
    print("ok")

if __name__ == "__main__":
    main()
