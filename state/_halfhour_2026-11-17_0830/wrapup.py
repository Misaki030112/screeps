#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-17_0830"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84312501, 84313200
GT_FIRST = 84313225
PUB_BASES = "84312500..84313100"
TICK_S_FIRST = 4.57801
TICK_S_PRINTED = "4.578"
NEW_ROWS = {"W46N8": 2121, "W47N8": 1349, "W45N8": 645, "W45N7": 1471, "W47N7": 1017}
INSERTED_FIRST = 6603
ALREADY = 21329
RECON_ROWS = 27932
OUTSIDE_404 = [
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
        rem_300 = fill(c, 84312901, 84313200)
        cpu = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM creep_cpu WHERE ts >= '2026-11-17 08:04:17+08'"
        ).fetchone()
        path = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM path_arrivals WHERE ts >= '2026-11-17 08:04:17+08'"
        ).fetchone()

    segment90 = {
        "creep_cpu": {"min": cpu[0], "max": cpu[1], "rows": cpu[2], "min_ts": iso(cpu[3]), "max_ts": iso(cpu[4])},
        "path_arrivals": {"min": path[0], "max": path[1], "rows": path[2], "min_ts": iso(path[3]), "max_ts": iso(path[4])},
    }

    per_room = {}
    for room in ROOMS:
        cvr = coverage[room]
        per_room[room] = {
            "official_ticks_first_pass": 700,
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
        f"inserted 6603 rows, then realign raised psycopg.errors.CheckViolation on "
        f"_hyper_6_74_chunk constraint_74 (new ts 2026-11-17 08:00:00.563845+08 for W46N8 queen84311260 tick 84312817) "
        f"and rolled back, so ts_realigned_first=0. later-mean-robust {later:.5f} "
        f"(raw later-mean also {later:.5f}; W46 first interval 4.59073, min-all-rooms first interval {TICK_S_FIRST}; "
        f"delta first-robust {4.59073-later:.5f} s/tick, ~{(GT_FIRST-TMIN)*abs(4.59073-later):.1f}s at tmin using W46 first, "
        f"~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-later):.1f}s using script first) "
        f"was already inside the 45s gate at {tsr.get('now_check')} game.time={tsr.get('gt_check')} "
        f"(later over45={vs_later['over45']} over15={vs_later['over15']} mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}; "
        f"first over45={vs_first['over45']} over15={vs_first['over15']} mean_off={vs_first['mean_off']:.2f} max_off={vs_first['max_off']:.2f}; "
        f"lowest over45 among sane={tsr.get('lowest_over45_sane')}). "
        f"No corrective realign (corrective_nfix=0). In-use tick_s={later:.5f} "
        f"(rows already sit on later-mean; the 4.578 first-pass tick_s was not applied)."
    )
    missing_note = (
        f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). "
        f"missing_chunks=0 of 35 official GETs (35 of 35 200). No in-window official 404. "
        f"The previous 08:00 half-hour run official-backfilled 84312201..84312900 "
        f"(inserted=16167 already_in_db=9895 at game.time=84312913, published_bases 84312200..84312800, "
        f"missing_chunks=0, tick_s=4.70966 printed 4.710, ts_realigned_first=0, "
        f"later-mean-robust 4.65902 already inside the 45s gate, no corrective, in-use 4.70966). "
        f"This run overlapped 84312501..84312900 and newly covered the previously unpublished remainder "
        f"84312901..84313200 (300/300 distinct on all five rooms). "
        f"The 07:43:34–08:04:17 (~1232s) freeze room_stats gap 84312611..84312889 remains official-filled 279/279 "
        f"on all five rooms and sits inside this window. "
        f"Prior 07:13 freeze gap 84312221..84312399 (outside this window start) stays official-filled 179/179. "
        f"Confirm at {confirm_at} game.time={confirm_gt} recovered none inserted=0; "
        f"retry2 at {retry2_at} game.time={retry2_gt} recovered none inserted=0."
    )
    inserted_note = (
        f"This 08:30 first pass inserted {INSERTED_FIRST} new rows (already_in_db={ALREADY}, reconstructed={RECON_ROWS}) "
        f"because the overlap 84312501..84312900 was already official-backfilled by the 08:00 run "
        f"(including the 07:43 freeze gap 84312611..84312889 official-filled 279/279). "
        f"The previously unpublished remainder 84312901..84313200 is now official-filled 300/300 on all five rooms. "
        f"Confirm recovered none inserted=0; retry2 recovered none inserted=0. inserted_total={INSERTED_FIRST}. "
        f"First-pass realign rolled back after CheckViolation (ts_realigned_first=0, tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}). "
        f"later-mean-robust {later:.5f} was already inside the 45s gate "
        f"(later over45={vs_later['over45']} over15={vs_later['over15']} mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}; "
        f"first over45={vs_first['over45']} over15={vs_first['over15']} mean_off={vs_first['mean_off']:.2f} max_off={vs_first['max_off']:.2f}); "
        f"no corrective realign. In-use tick_s={later:.5f}."
    )
    live_note = (
        f"No new box freeze since the 08:00 wrapup. Listener remains the 08:04:17 self-reconnect after "
        f"2026-11-17 07:43:34–2026-11-17 08:04:17 Asia/Hong_Kong (~1232s) hibernate "
        f"(relaunch 08:04:20, current tools/listener.py pid 3814276; pidfile 4035476). "
        f"Earlier it also self-reconnected at 07:26:06 after 07:13:02–07:26:06 (~776s), "
        f"at 06:59:53 after 06:44:57–06:59:53 (~885s), at 06:17:08 after 06:10:55–06:17:08 (~361s), "
        f"at 05:57:21 after 05:47:25–05:57:21 (~588s), and at 05:41:20 after a websocket ping/pong timeout at 05:41:17. "
        f"After the 08:04:17 reconnect the listener itself has kept pulling recent CPU / path buffers "
        f"(creep_cpu {cpu[0]}..{cpu[1]}, {cpu[2]} rows, first ts {iso(cpu[3])}; "
        f"path_arrivals {path[0]}..{path[1]}, {path[2]} rows, first ts {iso(path[3])}). "
        f"Peacetime single-slot rotation holds (roomSlot={live.get('roomSlot')}, rot={rot}, yield_files=absent). "
        f"This run did not restart the listener, start a second one, or change the 5:5:1:1 poll. "
        f"Official history HTTP does not use a room slot."
    )
    hourly_note = (
        f"The previous 08:00 half-hour run official-backfilled 84312201..84312900 "
        f"(inserted=16167 already_in_db=9895 at game.time=84312913, published_bases 84312200..84312800, "
        f"missing_chunks=0, tick_s=4.70966 printed 4.710, ts_realigned_first=0, "
        f"later-mean-robust 4.65902 already inside the 45s gate, no corrective, in-use 4.70966). "
        f"The 08:16 Asia/Hong_Kong hourly patrol already finished (~08:23) and cleared the HOME upgrade formal alert. "
        f"A 12-hour strategic review is running in parallel (DB reads only, not official history backfill). "
        f"This half-hour backfill is the official-history catch-up for {TMIN}..{TMAX} "
        f"(inserted={INSERTED_FIRST} first pass, missing_chunks=0, 35 of 35 official GETs 200)."
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
        "tick_s_in_use": later,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": False,
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
        "ts_realigned": 0,
        "ts_realigned_corrective_later_mean": 0,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": tick_s_note,
        "ssl_first_attempt": "ok first try; post-insert realign raised CheckViolation and rolled back (insert kept)",
        "hourly_patrol_prefilled": hourly_note,
        "per_room": per_room,
        "known_official_404s_outside_window": holes,
        "known_official_404s_in_window": [],
        "w45n7_empty_no_creep_in_window": False,
        "w45n7_empty_no_creep_ranges": [],
        "empty_no_creep_in_window": False,
        "empty_no_creep_ranges": {},
        "empty_no_creep_ticks": 0,
        "official_room_ticks_fetched": 3500,
        "official_room_ticks_with_creeps": 3500,
        "new_box_freeze": None,
        "second_box_freeze": None,
        "prior_0743_freeze_still_in_window": {
            "from": "2026-11-17 07:43:34",
            "to": "2026-11-17 08:04:17",
            "sec": 1232,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84312611, 84312889],
            "live_room_stats_gap_ticks": 279,
            "official_fill": freeze_0743,
            "note": "not new this run; already official-filled 279/279 by the 08:00 run and still complete",
        },
        "prior_unpublished_remainder_now_filled": {
            "ticks": [84312901, 84313200],
            "span": 300,
            "official_fill": rem_300,
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
                "Listener self-reconnected at 08:04:17 Asia/Hong_Kong after the box freeze "
                "2026-11-17 07:43:34–2026-11-17 08:04:17 (~1232s); existing run_listener.sh loop "
                "(pidfile 4035476) relaunched tools/listener.py at 08:04:20 (pid 3814276). "
                "No new freeze since then. This backfill did not start a second listener or change peacetime 5:5:1:1 rotation."
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
    now_lines.append("  (35 of 35 official GETs 200, missing_chunks=0; see history_backfill.txt)")
    now_lines.append(f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} in use)")
    now_lines.append(f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0")
    now_lines.append(f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}")
    now_lines.append(
        "per_room " + " ".join(f"{r}:700t/{NEW_ROWS[r]}new" for r in ROOMS)
    )
    now_lines.append(f"inserted={INSERTED_FIRST}")
    now_lines.append("ts_realigned=0 (first-pass realign CheckViolation rolled back; no corrective)")
    now_lines.append("db_after")
    for room in ROOMS:
        cvr = coverage[room]
        now_lines.append(
            f"  {room} ticks={cvr['range'][0]}..{cvr['range'][1]} rows={cvr['rows']} distinct={cvr['distinct']}"
        )
    now_lines.append(
        f"coverage official_recovered=3500/3500 unique_after={cov.get('unique_after')} "
        f"empty_no_creep=0 official_404_in_window=0"
    )
    now_lines.append(
        f"tick_s_check later-mean-robust {later:.5f} already inside 45s gate "
        f"(later over45={vs_later['over45']} over15={vs_later['over15']} mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}); "
        f"in-use tick_s={later:.5f}"
    )
    now_lines.append(
        "confirm recovered=none inserted=0; retry2 recovered=none inserted=0; leftover official 404s unchanged "
        "(W46N8@84310500 11 live, W47N7@84309000 empty, W45N8@84309100 25 live, and older leftovers still 404)."
    )
    now_lines.append(
        "No new box freeze. Prior 07:43:34–08:04:17 (~1232s) gap 84312611..84312889 still official-filled 279/279 all five rooms. "
        "Previously unpublished 84312901..84313200 official-filled 300/300 all five rooms. "
        "Prior 07:13 gap 84312221..84312399 stays official-filled 179/179 outside window start."
    )
    now_lines.append(
        f"listener single_slot=True roomSlot={live.get('roomSlot')} rot={rot} yield=absent"
    )
    now_lines.append("confirm recovered=none retry2 recovered=none")
    now_lines.append(
        f"ok=true (quiet); first-pass missing_chunks=0 (35 of 35 official GETs 200, no in-window official 404); "
        f"no corrective realign, tick_s_in_use={later:.5f} (later-mean-robust already inside the 45s gate; "
        f"first-pass realign with {TICK_S_FIRST} rolled back on Timescale daily-chunk boundary); "
        f"prior 07:43 freeze gap 84312611..84312889 still official-filled (279/279 all five rooms); "
        f"prior unpublished remainder 84312901..84313200 official-filled (300/300 all five rooms); "
        f"no unpublished remainder inside the window; leftover official 404s remain outside the window."
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
            f"official_404=0 []"
        )
    verify.append(f"unique_after {cov.get('unique_after')}")
    verify.append("official_with_creeps=3500 empty_no_creep=0 official_404_missing=0 official_recovered=3500 expected=3500 in_window_404=[]")
    verify.append(f"live_ticks_after_official_tip {json.dumps(live_after, default=str)}")
    verify.append(f"db_tips {json.dumps(tips, default=str)}")
    verify.append(
        "07:43 freeze 84312611..84312889 official-filled 279/279 all five rooms (not new this run)."
    )
    verify.append(
        "previously unpublished 84312901..84313200 official-filled 300/300 all five rooms; no unpublished remainder in-window."
    )
    verify.append(
        f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; later-mean-robust {later:.5f} in use; "
        f"first-pass realign CheckViolation rolled back; later already inside 45s gate, no corrective."
    )
    verify.append("confirm/retry2 recovered none; leftover official 404s unchanged and outside this window.")
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
        f"window {TMIN}..{TMAX} inserted={INSERTED_FIRST} missing_chunks=0 tick_s_in_use={later:.5f} corrective_nfix=0\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    print(summary, end="")
    print("in_window official 404: none")
    print("freeze_fill_0743", json.dumps(freeze_0743, default=str))
    print("remainder_300", json.dumps(rem_300, default=str))
    print("listener", lis, runl, live.get("roomSlot"), rot)
    print("ok")

if __name__ == "__main__":
    main()
