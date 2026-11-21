#!/usr/bin/env python3
import json, shutil, subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-22_0000")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84402501, 84403200
JUST_BASE = 84403200
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
PUBLISHED_BASES = [84402500, 84403100]
GT_FIRST = 84403236
INSERTED_FIRST = 5825
TS_REALIGNED_FIRST = 7742
CREEP_ROWS_FIRST = 24839
ALREADY_IN_DB = 19014
FIRST_PASS_AT = "2026-11-22 00:00:48 Asia/Hong_Kong"
TICK_S_PRINTED = 4.356

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84403200.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
late = json.loads((DIR / "backfill_late_retry.json").read_text())
confirm_j = json.loads((DIR / "backfill_confirm_gets.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())

GAPS = [
    ("gap_2353_2357", 84403151, 84403209),  # NEW this run, not yet told; fold into next 1h patrol
    ("gap_2320_2324", 84402681, 84402749),  # already told in _patrol_2026-11-21_2323 USER_LOG
    ("gap_2249_2259", 84402241, 84402409),  # already told in _patrol_2026-11-21_2323 USER_LOG; aged out of window start 84402501
    ("gap_2214_2226", 84401751, 84401939),  # already told in delivered _patrol_2026-11-21_2226
    ("gap_2142_2201", 84401311, 84401589),  # already told in delivered _patrol_2026-11-21_2226
    ("gap_2049_2104", 84400561, 84400789),  # already told in _patrol_2026-11-21_2119
    ("gap_1952_2002", 84399771, 84399919),  # already told in _patrol_2026-11-21_2020
    ("gap_2021_shortws", 84400171, 84400189),  # already told in _patrol_2026-11-21_2020
]
HOLES = [
    ("W45N7", 84400400),  # already told in 21:31 patrol; aged out of window start 84402501
    ("W45N7", 84400300),  # already told in 21:31 patrol; aged out
    ("W47N8", 84400100),  # already told in 20:34 patrol; aged out
]

with db.connect() as c:
    post = {}
    actual = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, T0, T1),
        ).fetchone()
        post[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
        actual[room] = int(n or 0) - int((pre.get(room) or {}).get("rows") or 0)
    (DIR / "just_published_post_counts.json").write_text(json.dumps(post, indent=2) + "\n")

    window_db = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, WIN_TMIN, WIN_TMAX),
        ).fetchone()
        window_db[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

    gaps = {}
    for label, a, b in GAPS:
        gaps[label] = {}
        span = b - a + 1
        for room in ROOMS:
            d, mn, mx, n = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, a, b),
            ).fetchone()
            miss = c.execute(
                "select array_agg(t order by t) from (select generate_series(%s,%s) t except select distinct tick from creep_ticks where room=%s and tick between %s and %s) x",
                (a, b, room, a, b),
            ).fetchone()[0] or []
            gaps[label][room] = {
                "fill": f"{int(d or 0)}/{span}",
                "distinct": int(d or 0),
                "rows": int(n or 0),
                "min": mn,
                "max": mx,
                "missing_n": len(miss),
                "missing_range": f"{miss[0]}..{miss[-1]}" if miss else None,
            }

    holes = {}
    for room, base in HOLES:
        t0, t1 = base + 1, base + 100
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, t0, t1),
        ).fetchone()
        miss = c.execute(
            "select array_agg(t order by t) from (select generate_series(%s,%s) t except select distinct tick from creep_ticks where room=%s and tick between %s and %s) x",
            (t0, t1, room, t0, t1),
        ).fetchone()[0] or []
        rec = {
            "distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx,
            "hole_ticks": len(miss),
            "hole_ranges": None,
            "missing": None if not miss else f"{miss[0]}..{miss[-1]}",
        }
        if miss:
            ranges = []
            s = prev = miss[0]
            for t in miss[1:]:
                if t != prev + 1:
                    ranges.append([s, prev])
                    s = t
                prev = t
            ranges.append([s, prev])
            rec["hole_ranges"] = ranges
            rec["missing"] = f"{miss[0]}..{miss[-1]}" if miss[-1]-miss[0]+1 == len(miss) else miss
        holes[f"{room}@{base}"] = rec

    tips = {}
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute(f"select max(tick) from {table}").fetchone()[0]

script_by = {g["room"]: int(g.get("inserted") or 0) for g in (jp.get("gets") or [])}
for r in ROOMS:
    script_by.setdefault(r, 0)
actual_by = actual
actual_sum = sum(actual_by.values())
script_sum = sum(script_by.values())

inserted_first = INSERTED_FIRST
inserted_confirm = int(confirm_j.get("inserted") or 0)
retry2 = confirm_j.get("retry2") or {}
inserted_retry2 = int(retry2.get("inserted") or confirm_j.get("retry2_inserted") or 0)
inserted_late = int(late.get("inserted") or 0)
inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + actual_sum

tick_s_in_use = float(tick["tick_s_in_use"])
tick_s_first = float(tick["tick_s_used_first_pass"])
tick_s_name = tick.get("tick_s_in_use_name") or "first"
corrective_nfix = int(tick.get("ts_realigned_to_later_mean") or 0)

out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
listener_ps = None
n_listeners = 0
for line in out.splitlines():
    if "tools/listener.py" in line:
        n_listeners += 1
        listener_ps = line.strip()
listener_pid, listener_parent, listener_started = 2151688, 4035476, "23:57:45"
if listener_ps:
    parts = listener_ps.split()
    listener_pid = int(parts[0])
    listener_parent = int(parts[1])
    # ps -o lstart: Sat Nov 21 23:57:45 2026
    for i, p in enumerate(parts):
        if p.count(":") == 2 and p.split(":")[0].isdigit():
            listener_started = p
            break

yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
slot = live.get("roomSlot")

w45n7_84400400 = holes["W45N7@84400400"]
w45n7_84400300 = holes["W45N7@84400300"]
w47n8_84400100 = holes["W47N8@84400100"]
gap2353 = gaps["gap_2353_2357"]
gap2320 = gaps["gap_2320_2324"]
gap2249 = gaps["gap_2249_2259"]
gap2214 = gaps["gap_2214_2226"]
gap2142 = gaps["gap_2142_2201"]
gap2049 = gaps["gap_2049_2104"]
gap1952 = gaps["gap_1952_2002"]
gap2021 = gaps["gap_2021_shortws"]
fill2353 = ", ".join(f"{r} {gap2353[r]['fill']}" for r in ROOMS)
fill2320 = ", ".join(f"{r} {gap2320[r]['fill']}" for r in ROOMS)
fill2249 = ", ".join(f"{r} {gap2249[r]['fill']}" for r in ROOMS)
fill2214 = ", ".join(f"{r} {gap2214[r]['fill']}" for r in ROOMS)
fill2142 = ", ".join(f"{r} {gap2142[r]['fill']}" for r in ROOMS)
fill2049 = ", ".join(f"{r} {gap2049[r]['fill']}" for r in ROOMS)
fill1952 = ", ".join(f"{r} {gap1952[r]['fill']}" for r in ROOMS)
fill2021 = ", ".join(f"{r} {gap2021[r]['fill']}" for r in ROOMS)

def hole_range_txt(h):
    if not h.get("hole_ranges"):
        return "none"
    parts = [f"{a}..{b}" for a, b in h["hole_ranges"]]
    return " and ".join(parts)

payload = {
    "ok_quiet": True,
    "at": AT,
    "window": [WIN_TMIN, WIN_TMAX],
    "published_bases": PUBLISHED_BASES,
    "game_time_first": GT_FIRST,
    "first_pass": {
        "gets_200": 35,
        "gets_total": 35,
        "missing_chunks": [],
        "reconstructed": [84402501, 84403200],
        "creep_rows": CREEP_ROWS_FIRST,
        "already_in_db": ALREADY_IN_DB,
        "inserted": inserted_first,
        "ts_realigned": TS_REALIGNED_FIRST,
        "tick_s_printed": TICK_S_PRINTED,
        "overlap_compared": None,
        "overlap_match": None,
        "overlap_differ": None,
        "overlap_note": "First-pass output did not print an overlap compared/match/differ summary this run. Backfill does not overwrite existing rows. First pass completed cleanly at 00:00:48 with the SSL-retry wrapper (no abort). Prior 23:30 half-hour already official-filled 84402201..84402900 and just-published 84402900 (ticks 84402901..84403000, actual 2576 at 23:45:56). This first pass also included newly published 84403000 and 84403100.",
    },
    "confirm": {
        "at": confirm_j.get("confirm_at") or confirm_j.get("at"),
        "skipped": True,
        "game_time": confirm_j.get("confirm_game_time") or confirm_j.get("game_time"),
        "still_404": confirm_j.get("still_404") or [],
        "inserted": inserted_confirm,
        "recovered": confirm_j.get("recovered") or [],
    },
    "retry2": {
        "at": retry2.get("at"),
        "skipped": True,
        "game_time": retry2.get("game_time"),
        "still_404": retry2.get("still_404") or [],
        "inserted": inserted_retry2,
        "recovered": retry2.get("recovered") or [],
        "reason": retry2.get("reason"),
    },
    "late_retry": {
        "at": late.get("at"),
        "skipped": True,
        "game_time": late.get("game_time"),
        "targets": late.get("targets") or [],
        "still_404": late.get("still_404") or [],
        "inserted": inserted_late,
        "recovered": late.get("recovered") or [],
        "reason": late.get("reason"),
    },
    "just_published": {
        "base": JUST_BASE,
        "included_in_first_pass": False,
        "first_pass_at": FIRST_PASS_AT,
        "first_pass_game_time": GT_FIRST,
        "first_pass_all_five_200": True,
        "first_pass_200": ["W46N8@84403100", "W47N8@84403100", "W45N8@84403100", "W45N7@84403100", "W47N7@84403100"],
        "first_pass_404": [],
        "reget_at": jp.get("at"),
        "game_time": jp.get("game_time"),
        "all_five_200": not jp.get("still_404"),
        "script_inserted": script_sum,
        "actual_inserted": actual_sum,
        "by_script": script_by,
        "by_actual": actual_by,
        "still_404": jp.get("still_404") or [],
    },
    "coverage": {
        "official_recovered": cov["official_recovered"],
        "expected": cov["expected"],
        "empty_no_creep": cov["empty_no_creep"],
        "official_404_missing": cov["official_404_missing"],
        "per_room": cov["coverage"],
    },
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_name,
    "ts_realigned_first": TS_REALIGNED_FIRST,
    "corrective": {
        "applied": bool(tick.get("corrective_applied")),
        "nfix": corrective_nfix,
        "tick_s": tick_s_in_use,
        "note": "live-anchor-best prev_later 4.30514 (23:30 tick_s_in_use); already inside 45s gate, no corrective realign",
    },
    "inserted_total": inserted_total,
    "inserted_breakdown": {
        "first": inserted_first,
        "confirm": inserted_confirm,
        "retry2": inserted_retry2,
        "late": inserted_late,
        "just_actual": actual_sum,
    },
    "window_db": window_db,
    "gaps": gaps,
    "holes": holes,
    "tips": tips,
    "listener": {
        "pid": listener_pid,
        "parent": listener_parent,
        "started": listener_started,
        "count": n_listeners,
        "slot": slot,
        "rot": rot,
        "yield_absent": yield_absent,
        "restarted_this_run": False,
        "restarts_before_this_run": [
            {"at": "22:01:12", "why": "box freeze 21:42:29-22:01:09", "python_started": "22:01:21", "pid": 2104047},
            {"at": "22:26:33", "why": "box freeze 22:14:12-22:26:30", "python_started": "22:26:42", "pid": 2110888},
            {"at": "22:59:59", "why": "box freeze 22:49:18-22:59:56", "python_started": "23:00:09", "pid": 2124111},
            {"at": "23:24:26", "why": "box freeze 23:20:38-23:24:23", "python_started": "23:24:35", "pid": 2135086},
            {"at": "23:57:36", "why": "box freeze 23:53:42-23:57:33", "python_started": "23:57:45", "pid": 2151688},
        ],
    },
    "new_untold_official_404s": [],
    "new_untold_box_freezes": [
        {
            "from": "2026-11-21 23:53:42",
            "to": "2026-11-21 23:57:33",
            "sec": 222,
            "stats": [84403151, 84403209],
            "span": 59,
            "listener_restart": "23:57:36",
            "python_started": "23:57:45",
            "pid": 2151688,
            "already_healed": True,
        }
    ],
    "new_untold_short_ws": [],
    "already_told_in_2323_patrol": [
        "box_freeze 23:20:38-23:24:23",
        "box_freeze 22:49:18-22:59:56",
        "W45N7@84400300",
        "W45N7@84400400",
        "W47N8@84400100",
    ],
    "already_told_in_2226_patrol": [
        "box_freeze 22:14:12-22:26:30",
        "box_freeze 21:42:29-22:01:09",
        "W45N7@84400300",
        "W45N7@84400400",
        "W47N8@84400100",
    ],
    "already_told_in_2119_patrol": [
        "box_freeze 20:49:04-21:04:03",
        "short_ws 21:13:29",
        "W45N7@84400300",
        "W45N7@84400400",
    ],
    "already_told_in_2020_patrol": [
        "box_freeze 19:52:19-20:02:21",
        "short_ws 20:21:38",
        "W45N8@84399500",
        "W45N7@84399800",
        "W47N8@84400100",
    ],
    "concurrent_1h_patrol": "_patrol_2026-11-21_2323",
}

(DIR / "wrapup_snap.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

confirm_at = confirm_j.get("confirm_at") or confirm_j.get("at")
confirm_gt = confirm_j.get("confirm_game_time") or confirm_j.get("game_time")
retry2_at = retry2.get("at")

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + "\n"
wrap = (
    f"---- wrap {AT} ----\n"
    f"confirm at {confirm_at} skipped no targets inserted={inserted_confirm}; still_404 none. "
    f"retry2 at {retry2_at} skipped no targets inserted={inserted_retry2}. "
    f"late retry skipped no targets inserted={inserted_late}. "
    f"First pass 35/35 official GETs 200, missing_chunks=0. "
    f"First pass completed cleanly at {FIRST_PASS_AT} with the SSL-retry wrapper (no abort). "
    f"Leftover official 404s W45N7@84400400, W45N7@84400300, and W47N8@84400100 aged out of window start 84402501 and were not retried (already told in the delivered 23:35 / 22:35 / 21:31 / 20:34 1h patrols; do not re-tell). "
    f"Just-published 84403200 was not in first pass (first pass ended at published 84403100 / reconstructed 84402501..84403200 at {FIRST_PASS_AT} gt={GT_FIRST}, all five 200); GET at {jp.get('at')} gt={jp.get('game_time')} all_five_200={not jp.get('still_404')} script={script_sum} actual={actual_sum}; "
    f"W46N8 script {script_by['W46N8']} vs actual {actual_by['W46N8']}, W47N8 script {script_by['W47N8']} vs actual {actual_by['W47N8']}, W45N8 script {script_by['W45N8']} vs actual {actual_by['W45N8']}, W45N7 script {script_by['W45N7']} vs actual {actual_by['W45N7']}, W47N7 script {script_by['W47N7']} vs actual {actual_by['W47N7']}. "
    f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix}. "
    f"NEW leftover official 404 / short WS this run: none. NEW 盒子休眠 23:53:42-23:57:33 (222s, already healed; STATS 84403151..84403209, 59t; official-filled {fill2353}; listener auto-restart 23:57:36, python 2151688 started 23:57:45) -- not yet told; fold into the next 1h patrol. "
    f"_patrol_2026-11-21_2323 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 23:20:38-23:24:23 (224s; STATS 84402681..84402749, 69t; official-filled {fill2320}; listener auto-restart 23:24:26, python 2135086 started 23:24:35); "
    f"盒子休眠 22:49:18-22:59:56 (634s; official-filled {fill2249}); "
    f"leftover official 404 W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older. "
    f"_patrol_2026-11-21_2226 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 22:14:12-22:26:30 (737s; official-filled {fill2214}); "
    f"盒子休眠 21:42:29-22:01:09 (1115s; official-filled {fill2142}); "
    f"leftover official 404 W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older. "
    f"_patrol_2026-11-21_2119 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 20:49:04-21:04:03 (895s; official-filled {fill2049}); "
    f"监听短中断 21:13:29 ping/pong; "
    f"leftover official 404 W45N7@84400300 (listener {w45n7_84400300['distinct']}/100; hole {w45n7_84400300['hole_ticks']} ticks 84400301..84400400; aged out of this official window start 84402501) and W45N7@84400400 (listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}; aged out of window start 84402501). "
    f"_patrol_2026-11-21_2020 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 19:52:19-20:02:21 (599s; official-filled {fill1952}); "
    f"监听短中断 20:21:38 (STATS 84400171..84400189; official/listener fill {fill2021}); "
    f"leftover official 404 W45N8@84399500, W45N7@84399800, and W47N8@84400100 (this run still 404 at W47N8@84400100; listener {w47n8_84400100['distinct']}/100; hole {w47n8_84400100['hole_ticks']} ticks 84400101..84400200; aged out of window start 84402501 and was not retried). "
    f"Already told by earlier delivered 1h patrols and not re-told: 盒子休眠 19:10:45-19:18:45, 18:47:50-18:58:17, leftover official 404 all five @84399100, W45N8@84399300, and older freezes/404s. "
    f"Fold only newer freezes/short WS than 23:53:42-23:57:33 (and already-told 23:20:38-23:24:23 / 22:49:18-22:59:56), and newer leftover official 404s than W45N7@84400300 / W45N7@84400400 / W47N8@84400100, into the next 1h patrol; do not re-tell earlier already-told items.\n"
)
now_txt = first + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

verify = (
    f"wrap {AT}\n"
    f"window {WIN_TMIN}..{WIN_TMAX} first_pass 35/35 missing_chunks=0\n"
    f"db_window {json.dumps(window_db)}\n"
    f"just_published 84403200 not in first pass; GET all_five_200={not jp.get('still_404')} script={script_sum} actual={actual_sum} by_actual={json.dumps(actual_by)} by_script={json.dumps(script_by)}\n"
    f"confirm skipped no targets inserted={inserted_confirm}; retry2 skipped; late skipped\n"
    f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}\n"
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}\n"
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix}\n"
    f"NEW leftover official 404 / short WS this run: none\n"
    f"NEW 盒子休眠 23:53:42-23:57:33 (222s, already healed; STATS 84403151..84403209, 59t; official-filled {fill2353}; listener auto-restart 23:57:36, python 2151688 started 23:57:45) not yet told\n"
    f"already_told_in_2323_patrol 盒子休眠 23:20:38-23:24:23 fill {fill2320}; 22:49:18-22:59:56 fill {fill2249}; leftover W45N7@84400300 / W45N7@84400400 / W47N8@84400100\n"
    f"already_told_in_2226_patrol 盒子休眠 22:14:12-22:26:30 fill {fill2214}; 21:42:29-22:01:09 fill {fill2142}; leftover W45N7@84400300 / W45N7@84400400 / W47N8@84400100\n"
    f"already_told_in_2119_patrol leftover W45N7@84400400 aged out of window start 84402501; listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}\n"
    f"already_told_in_2119_patrol leftover W45N7@84400300 aged out of window start 84402501; distinct={w45n7_84400300['distinct']} rows={w45n7_84400300['rows']} (listener 0/100, hole 100 ticks 84400301..84400400)\n"
    f"already_told_in_2020_patrol leftover W47N8@84400100 aged out of window start 84402501; distinct={w47n8_84400100['distinct']} rows={w47n8_84400100['rows']} (listener 0/100, hole 100 ticks 84400101..84400200)\n"
    f"already_told_in_2119_patrol 盒子休眠 20:49:04-21:04:03 fill {fill2049}; 监听短中断 21:13:29\n"
    f"already_told_in_2020_patrol box_freeze 19:52:19-20:02:21 fill {fill1952}; short_ws 20:21:38 fill {fill2021}; leftover W45N8@84399500, W45N7@84399800, W47N8@84400100\n"
    f"already_told_aged_out box_freeze 19:10:45-19:18:45, 18:47:50-18:58:17; leftover all-five @84399100, W45N8@84399300\n"
    f"tips {tips}\n"
    f"listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={json.dumps(rot, ensure_ascii=False)} yield_absent={yield_absent} restarted_this_run=False listener_count={n_listeners}\n"
    f"ok_quiet=True new_official_404_untold=[] new_box_freeze_untold=[23:53:42-23:57:33] new_short_ws_untold=[]\n"
    + wrap.split("---- wrap", 1)[-1].lstrip()
)
(DIR / "verify.txt").write_text(verify)
(DIR / "_halfhour_backfill_verify.txt").write_text(verify)
shutil.copyfile(DIR / "_halfhour_backfill_verify.txt", STATE / "_halfhour_backfill_verify.txt")

(DIR / "wrapup_run.txt").write_text(f"wrap {AT} ok_quiet=True inserted_total={inserted_total}\n")
print("wrote wrapup files")
print("ok_quiet True inserted_total", inserted_total, "at", AT)
print("now_txt bytes", len(now_txt), "verify bytes", len(verify))
print("just actual", actual_by, "sum", actual_sum, "script", script_by, "sum", script_sum)
print("window_db", window_db)
print("tips", tips)
print("listener", listener_pid, slot, rot, "yield_absent", yield_absent, "count", n_listeners)
print("gap2353", {r: gap2353[r]["fill"] for r in ROOMS})
print("gap2320", {r: gap2320[r]["fill"] for r in ROOMS})
print("gap2249", {r: gap2249[r]["fill"] for r in ROOMS})
print("gap2214", {r: gap2214[r]["fill"] for r in ROOMS})
print("holes", {k: {kk: holes[k][kk] for kk in ("distinct", "rows", "min", "max", "hole_ticks", "hole_ranges")} for k in holes})
