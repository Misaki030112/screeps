#!/usr/bin/env python3
import json, shutil, subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_2230")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84401301, 84402000
JUST_BASE = 84402000
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
PUBLISHED_BASES = [84401300, 84401900]
GT_FIRST = 84402070
INSERTED_FIRST = 243
TS_REALIGNED_FIRST = 12847
CREEP_ROWS_FIRST = 25461
ALREADY_IN_DB = 25218

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84402000.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
late = json.loads((DIR / "backfill_late_retry.json").read_text())
confirm_j = json.loads((DIR / "backfill_confirm_gets.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())

GAPS = [
    ("gap_2214_2226", 84401751, 84401939),  # NEW box freeze 22:14:12-22:26:30; not yet told unless 2226 patrol delivers
    ("gap_2142_2201", 84401311, 84401589),  # box freeze 21:42:29-22:01:09; still not delivered by a finished patrol as of this backfill
    ("gap_2049_2104", 84400561, 84400789),  # already told in _patrol_2026-11-21_2119
    ("gap_1952_2002", 84399771, 84399919),  # already told in _patrol_2026-11-21_2020
    ("gap_2021_shortws", 84400171, 84400189),  # already told in _patrol_2026-11-21_2020; aged out of this window start 84401301
]
HOLES = [
    ("W45N7", 84400400),  # already told in 21:31 patrol; aged out of window start 84401301
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
listener_pid, listener_parent, listener_started = 2104047, 4035476, "22:01:21"
if listener_ps:
    parts = listener_ps.split()
    listener_pid = int(parts[0])
    listener_parent = int(parts[1])
    for i, p in enumerate(parts):
        if p.count(":") == 1 and p.split(":")[0].isdigit():
            listener_started = p
            break

yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
slot = live.get("roomSlot")

w45n7_84400400 = holes["W45N7@84400400"]
w45n7_84400300 = holes["W45N7@84400300"]
w47n8_84400100 = holes["W47N8@84400100"]
gap2214 = gaps["gap_2214_2226"]
gap2142 = gaps["gap_2142_2201"]
gap2049 = gaps["gap_2049_2104"]
gap1952 = gaps["gap_1952_2002"]
gap2021 = gaps["gap_2021_shortws"]
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
        "reconstructed": [84401301, 84402000],
        "creep_rows": CREEP_ROWS_FIRST,
        "already_in_db": ALREADY_IN_DB,
        "inserted": inserted_first,
        "ts_realigned": TS_REALIGNED_FIRST,
        "tick_s_printed": 4.327,
        "overlap_compared": None,
        "overlap_match": None,
        "overlap_differ": None,
        "overlap_note": "First-pass output did not print an overlap compared/match/differ summary this run. Backfill does not overwrite existing rows. Concurrent 1h patrol already official-filled 84401201..84402000 (just-published 84401900 at 22:34:58 gt=84402045, inserted 2817) before this first pass.",
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
        "at": retry2.get("at") or confirm_j.get("retry2_at"),
        "skipped": True,
        "game_time": retry2.get("game_time"),
        "still_404": retry2.get("still_404") or [],
        "inserted": inserted_retry2,
        "recovered": retry2.get("recovered") or [],
        "reason": retry2.get("reason") or "no targets",
    },
    "late_retry": {
        "at": late.get("at"),
        "skipped": True,
        "game_time": late.get("game_time"),
        "targets": late.get("targets") or [],
        "still_404": late.get("still_404") or [],
        "inserted": late.get("inserted") or 0,
        "recovered": late.get("recovered") or [],
        "reason": late.get("reason"),
    },
    "just_published": {
        "base": JUST_BASE,
        "included_in_first_pass": False,
        "first_pass_at": "2026-11-21 22:36:25 Asia/Hong_Kong",
        "first_pass_game_time": GT_FIRST,
        "first_pass_all_five_200": True,
        "first_pass_200": ["W46N8@84401900", "W47N8@84401900", "W45N8@84401900", "W45N7@84401900", "W47N7@84401900"],
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
        "note": "live-anchor-best first already inside 45s gate; no corrective realign",
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
        ],
    },
    "new_untold_official_404s": [],
    "new_untold_box_freezes": ["22:14:12-22:26:30", "21:42:29-22:01:09"],
    "new_untold_short_ws": [],
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
    "concurrent_1h_patrol": "_patrol_2026-11-21_2226 running during this backfill; do not write its folder. It already recorded both freezes in freeze_clock. If that patrol delivers, treat both as already told afterwards; otherwise fold into the next 1h patrol after 2226.",
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
    f"Leftover official 404s W45N7@84400400, W45N7@84400300, and W47N8@84400100 aged out of window start 84401301 and were not retried (already told in the delivered 21:31 / 20:34 1h patrols; do not re-tell). "
    f"Just-published 84402000 was not in first pass (first pass ended at published 84401900 / reconstructed 84401301..84402000 at 2026-11-21 22:36:25 Asia/Hong_Kong gt={GT_FIRST}, all five 200); GET at {jp.get('at')} gt={jp.get('game_time')} all_five_200={not jp.get('still_404')} script={script_sum} actual={actual_sum}; "
    f"W46N8 script {script_by['W46N8']} vs actual {actual_by['W46N8']}, W47N8 script {script_by['W47N8']} vs actual {actual_by['W47N8']}, W45N8 script {script_by['W45N8']} vs actual {actual_by['W45N8']}, W45N7 script {script_by['W45N7']} vs actual {actual_by['W45N7']}, W47N7 script {script_by['W47N7']} vs actual {actual_by['W47N7']}. "
    f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix}. "
    f"NEW not yet told — fold into the next 1h patrol after the delivered 21:31 _patrol_2026-11-21_2119, unless the concurrent _patrol_2026-11-21_2226 already delivers this set: "
    f"盒子休眠 22:14:12-22:26:30 (737s, already healed; STATS 84401751..84401939, 189t; official-filled {fill2214}; listener auto-restart 22:26:33, python 2110888 started 22:26:42); "
    f"and still-untold 盒子休眠 21:42:29-22:01:09 (1115s, already healed; STATS 84401311..84401589, 279t; official-filled {fill2142}; listener auto-restart 22:01:12, python 2104047 started 22:01:21). "
    f"No new leftover official 404 and no new short WS this run. "
    f"Concurrent 1h patrol _patrol_2026-11-21_2226 is running (do not write its folder); it already official-filled 84401201..84402000 (just-published 84401900 at 22:34:58 gt=84402045 inserted=2817) and recorded both freezes in freeze_clock. If that patrol delivers, treat both freezes as already told afterwards. "
    f"_patrol_2026-11-21_2119 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 20:49:04-21:04:03 (895s; official-filled {fill2049}); "
    f"监听短中断 21:13:29 ping/pong; "
    f"leftover official 404 W45N7@84400300 (listener {w45n7_84400300['distinct']}/100; hole {w45n7_84400300['hole_ticks']} ticks 84400301..84400400; aged out of this official window start 84401301) and W45N7@84400400 (listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}; aged out of window start 84401301). "
    f"_patrol_2026-11-21_2020 USER_LOG finished 20:35:40 already includes (treat as already told; do not re-tell): "
    f"盒子休眠 19:52:19-20:02:21 (599s; official-filled {fill1952}; aged around/out of this window); "
    f"监听短中断 20:21:38 (STATS 84400171..84400189; official/listener fill {fill2021}; aged out of this official window start 84401301); "
    f"leftover official 404 W45N8@84399500, W45N7@84399800, and W47N8@84400100 (this run still 404 at W47N8@84400100; listener {w47n8_84400100['distinct']}/100; hole {w47n8_84400100['hole_ticks']} ticks 84400101..84400200; aged out of window start 84401301 and was not retried). "
    f"Already told by earlier delivered 1h patrols and not re-told: 盒子休眠 19:10:45-19:18:45, 18:47:50-18:58:17, leftover official 404 all five @84399100, W45N8@84399300, and older freezes/404s. "
    f"Fold only the NEW 盒子休眠 22:14:12-22:26:30 and the still-untold 21:42:29-22:01:09 into the next 1h patrol if 2226 does not deliver them; do not re-tell earlier already-told items.\n"
)

now_txt = first + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

verify = (
    f"wrap {AT}\n"
    f"window {WIN_TMIN}..{WIN_TMAX} first_pass 35/35 missing_chunks=0\n"
    f"db_window {json.dumps(window_db)}\n"
    f"just_published 84402000 not in first pass; GET all_five_200={not jp.get('still_404')} script={script_sum} actual={actual_sum} by_actual={json.dumps(actual_by)} by_script={json.dumps(script_by)}\n"
    f"confirm skipped no targets inserted={inserted_confirm}; retry2 skipped; late skipped\n"
    f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}\n"
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}\n"
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix}\n"
    f"NEW leftover official 404 / short WS: none\n"
    f"NEW 盒子休眠 22:14:12-22:26:30 (737s; STATS 84401751..84401939 189t; official-filled {fill2214}; listener auto-restart 22:26:33 pid=2110888 started=22:26:42) not yet told — fold into next 1h patrol unless concurrent _patrol_2026-11-21_2226 delivers\n"
    f"still-untold 盒子休眠 21:42:29-22:01:09 (1115s; STATS 84401311..84401589 279t; official-filled {fill2142}; listener auto-restart 22:01:12 pid=2104047 started=22:01:21) — same: fold unless 2226 delivers\n"
    f"already_told_in_2119_patrol leftover W45N7@84400400 aged out of window start 84401301; listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}\n"
    f"already_told_in_2119_patrol leftover W45N7@84400300 aged out of window start 84401301; distinct={w45n7_84400300['distinct']} rows={w45n7_84400300['rows']} (listener 0/100, hole 100 ticks 84400301..84400400)\n"
    f"already_told_in_2020_patrol leftover W47N8@84400100 aged out of window start 84401301; distinct={w47n8_84400100['distinct']} rows={w47n8_84400100['rows']} (listener 0/100, hole 100 ticks 84400101..84400200)\n"
    f"already_told_in_2119_patrol 盒子休眠 20:49:04-21:04:03 fill {fill2049}; 监听短中断 21:13:29\n"
    f"already_told_in_2020_patrol box_freeze 19:52:19-20:02:21 fill {fill1952}; short_ws 20:21:38 fill {fill2021}; leftover W45N8@84399500, W45N7@84399800, W47N8@84400100\n"
    f"already_told_aged_out box_freeze 19:10:45-19:18:45, 18:47:50-18:58:17; leftover all-five @84399100, W45N8@84399300\n"
    f"tips {tips}\n"
    f"listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={json.dumps(rot, ensure_ascii=False)} yield_absent={yield_absent} restarted_this_run=False listener_count={n_listeners}\n"
    f"ok_quiet=True new_official_404_untold=[] new_box_freeze_untold=['22:14:12-22:26:30', '21:42:29-22:01:09'] new_short_ws_untold=[]\n"
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
print("gap2142", {r: gap2142[r]["fill"] for r in ROOMS})
print("gap2049", {r: gap2049[r]["fill"] for r in ROOMS})
print("holes", {k: {kk: holes[k][kk] for kk in ("distinct", "rows", "min", "max", "hole_ticks", "hole_ranges")} for k in holes})
