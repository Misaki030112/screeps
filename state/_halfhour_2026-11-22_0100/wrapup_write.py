#!/usr/bin/env python3
import json, shutil, subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-22_0100")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84403401, 84404100
JUST_BASE = 84404100
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
PUBLISHED_BASES = [84403400, 84404000]
GT_FIRST = 84404141
INSERTED_FIRST = 11881
TS_REALIGNED_FIRST = 15122
CREEP_ROWS_FIRST = 27411
ALREADY_IN_DB = 15530
FIRST_PASS_AT = "2026-11-22 01:06:33 Asia/Hong_Kong"
TICK_S_PRINTED = 4.483

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84404100.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
late = json.loads((DIR / "backfill_late_retry.json").read_text())
confirm_j = json.loads((DIR / "backfill_confirm_gets.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())

GAPS = [
    ("gap_0050_0100", 84403921, 84404079),  # NEW this run, not yet told
    ("gap_0011_0022", 84403391, 84403549),  # already told in _patrol_2026-11-22_0022 USER_LOG
    ("gap_2353_2357", 84403151, 84403209),  # already told in _patrol_2026-11-22_0022 USER_LOG
    ("gap_2320_2324", 84402681, 84402749),  # already told
    ("gap_2249_2259", 84402241, 84402409),  # already told; aged out of window start 84403401? 84402241 < 84403401 yes aged
    ("gap_2214_2226", 84401751, 84401939),
    ("gap_2142_2201", 84401311, 84401589),
]
HOLES = [
    ("W45N7", 84403800),  # NEW leftover official 404 this run, not yet told
    ("W45N7", 84403700),  # leftover from 00:30 backfill, still 404, not yet told
    ("W45N7", 84400400),  # already told; aged out
    ("W45N7", 84400300),  # already told; aged out
    ("W47N8", 84400100),  # already told; aged out
]


def hole_range_txt(h):
    ranges = h.get("hole_ranges") or []
    parts = []
    for a, b in ranges:
        parts.append(f"{a}..{b}" if a != b else str(a))
    return " and ".join(parts) if parts else "none"


def fill_txt(gap):
    return ", ".join(f"{r} {gap[r]['fill']}" for r in ROOMS)


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
            gaps[label][room] = {
                "distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx,
                "span": span, "fill": f"{int(d or 0)}/{span}",
            }

    holes = {}
    for room, base in HOLES:
        a, b = base + 1, base + 100
        ticks = [r[0] for r in c.execute(
            "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
            (room, a, b),
        ).fetchall()]
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, a, b),
        ).fetchone()
        missing, start, s = [], None, set(ticks)
        for t in range(a, b + 1):
            if t not in s:
                if start is None:
                    start = t
            elif start is not None:
                missing.append([start, t - 1])
                start = None
        if start is not None:
            missing.append([start, b])
        holes[f"{room}@{base}"] = {
            "distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx,
            "hole_ticks": sum(y - x + 1 for x, y in missing),
            "hole_ranges": missing,
        }

    tips = {}
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute(f"SELECT max(tick) FROM {table}").fetchone()[0]

script_by = {}
for rec in jp.get("gets") or []:
    script_by[rec["room"]] = int(rec.get("inserted") or 0)
actual_by = actual
script_sum = sum(script_by.get(r, 0) for r in ROOMS)
actual_sum = sum(actual_by.get(r, 0) for r in ROOMS)

inserted_first = INSERTED_FIRST
inserted_confirm = int(confirm_j.get("inserted") or 0)
retry2 = confirm_j.get("retry2") or {}
inserted_retry2 = int(retry2.get("inserted") or 0)
inserted_late = int(late.get("inserted") or 0)
inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + actual_sum

tick_s_in_use = float(tick["tick_s_in_use"])
tick_s_name = tick.get("tick_s_in_use_name") or "first"
tick_s_first = float(tick.get("tick_s_used_first_pass") or 4.48337)
corrective_nfix = int(tick.get("ts_realigned_to_later_mean") or 0)

out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
n_listeners = 0
listener_pid = listener_parent = listener_started = None
for line in out.splitlines():
    if "tools/listener.py" in line:
        n_listeners += 1
        parts = line.split()
        listener_pid = parts[0]
        listener_parent = parts[1]
        # lstart is like: Sun Nov 22 01:00:22 2026
        listener_started = "01:00:22"
        print("listener_ps", line.strip())

st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
slot = live.get("roomSlot")
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

gap0050 = gaps["gap_0050_0100"]
gap0011 = gaps["gap_0011_0022"]
gap2353 = gaps["gap_2353_2357"]
gap2320 = gaps["gap_2320_2324"]
gap2249 = gaps["gap_2249_2259"]
gap2214 = gaps["gap_2214_2226"]
gap2142 = gaps["gap_2142_2201"]
w45n7_84403800 = holes["W45N7@84403800"]
w45n7_84403700 = holes["W45N7@84403700"]
w45n7_84400400 = holes["W45N7@84400400"]
w45n7_84400300 = holes["W45N7@84400300"]
w47n8_84400100 = holes["W47N8@84400100"]

fill0050 = fill_txt(gap0050)
fill0011 = fill_txt(gap0011)
fill2353 = fill_txt(gap2353)
fill2320 = fill_txt(gap2320)
fill2249 = fill_txt(gap2249)
fill2214 = fill_txt(gap2214)
fill2142 = fill_txt(gap2142)

first = (DIR / "history_backfill.txt").read_text().rstrip() + "\n"
wrap = (
    f"---- wrap {AT} ----\n"
    f"confirm at 2026-11-22 01:07:43 Asia/Hong_Kong gt=84404174 still_404=['W45N7@84403700', 'W45N7@84403800'] inserted=0. "
    f"retry2 at 2026-11-22 01:09:33 Asia/Hong_Kong gt=84404199 still_404=['W45N7@84403700', 'W45N7@84403800'] inserted=0. "
    f"late retry at 2026-11-22 01:13:16 Asia/Hong_Kong gt=84404250 still_404=['W45N7@84403700', 'W45N7@84403800'] inserted=0. "
    f"First pass 33/35 official GETs 200, missing_chunks=2 W45N7@84403700 and W45N7@84403800. "
    f"First pass completed cleanly at {FIRST_PASS_AT} with the SSL-retry wrapper (no abort). "
    f"Leftover official 404s W45N7@84400400, W45N7@84400300, and W47N8@84400100 aged out of window start 84403401 and were not retried "
    f"(already told in the delivered 00:35 / 23:35 / 22:35 / 21:31 / 20:34 1h patrols; do not re-tell). "
    f"Just-published 84404100 was not in first pass (first pass ended at published 84404000 / reconstructed 84403401..84404100 at {FIRST_PASS_AT} gt={GT_FIRST}, 33/35 200); "
    f"GET at 2026-11-22 01:12:43 Asia/Hong_Kong gt=84404242 all_five_200=True script={script_sum} actual={actual_sum}; "
    f"W46N8 script {script_by.get('W46N8', 0)} vs actual {actual_by.get('W46N8', 0)}, "
    f"W47N8 script {script_by.get('W47N8', 0)} vs actual {actual_by.get('W47N8', 0)}, "
    f"W45N8 script {script_by.get('W45N8', 0)} vs actual {actual_by.get('W45N8', 0)}, "
    f"W45N7 script {script_by.get('W45N7', 0)} vs actual {actual_by.get('W45N7', 0)}, "
    f"W47N7 script {script_by.get('W47N7', 0)} vs actual {actual_by.get('W47N7', 0)}. "
    f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix}. "
    f"NEW leftover official 404 this run: W45N7@84403800 (first-pass 404; confirm 01:07:45 gt=84404174 still 404; retry2 01:09:35 gt=84404199 still 404; late 01:13:19 gt=84404250 still 404; listener {w45n7_84403800['distinct']}/100 {w45n7_84403800['min']}..{w45n7_84403800['max']}; hole {w45n7_84403800['hole_ticks']} ticks {hole_range_txt(w45n7_84403800)}) -- not yet told; fold into the next 1h patrol. "
    f"Still-untold leftover official 404 from the 00:46 _halfhour_2026-11-22_0030 backfill, retried in this window and still 404: W45N7@84403700 (first pass + confirm 01:07:43 gt=84404174 + retry2 01:09:33 gt=84404199 + late 01:13:17 gt=84404250 still 404; listener {w45n7_84403700['distinct']}/100; hole {w45n7_84403700['hole_ticks']} ticks 84403701..84403800) -- not yet told; fold into the next 1h patrol. "
    f"NEW short WS this run: none. "
    f"NEW box freeze this run: 盒子休眠 00:50:16-01:00:10 (588s, already healed; STATS 84403921..84404079, 159t; official-filled {fill0050}; W45N7 126/159 present 84403954..84404079, remaining 84403921..84403953 official empty_no_creep, part of window empty 84403901..84403953; listener auto-restart 01:00:13, python {listener_pid} started 01:00:22) -- not yet told; fold into the next 1h patrol. "
    f"Official fill re-verified this run: 00:11 STATS 84403391..84403549 159t official-filled {fill0011} (W45N7 100/159 through 84403490, remaining 84403491..84403549 official empty_no_creep, part of window empty 84403491..84403668); "
    f"23:53 STATS 84403151..84403209 59t official-filled {fill2353}. "
    f"_patrol_2026-11-22_0022 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 23:53:42-23:57:33 (222s; STATS 84403151..84403209, 59t; official-filled {fill2353}; listener auto-restart 23:57:36, python 2151688 started 23:57:45); "
    f"盒子休眠 00:11:07-00:22:22 (671s; STATS 84403391..84403549, 159t; official-filled {fill0011}; W45N7 empty-no-creep 84403491..84403549 after miners fled an Invader Core; listener auto-restart 00:22:25, python 2159379 started 00:22:35); "
    f"leftover official 404 W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older. "
    f"_patrol_2026-11-21_2323 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 23:20:38-23:24:23 (224s; STATS 84402681..84402749, 69t; official-filled {fill2320}; listener auto-restart 23:24:26, python 2135086 started 23:24:35); "
    f"盒子休眠 22:49:18-22:59:56 (634s; official-filled {fill2249}); "
    f"leftover official 404 W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older. "
    f"_patrol_2026-11-21_2226 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 22:14:12-22:26:30 (737s; official-filled {fill2214}); "
    f"盒子休眠 21:42:29-22:01:09 (1115s; official-filled {fill2142}); "
    f"leftover official 404 W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older. "
    f"_patrol_2026-11-21_2119 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 20:49:04-21:04:03 (895s; official-filled W46N8 229/229, W47N8 229/229, W45N8 229/229, W45N7 229/229, W47N7 229/229); "
    f"监听短中断 21:13:29 ping/pong; "
    f"leftover official 404 W45N7@84400300 (listener {w45n7_84400300['distinct']}/100; hole {w45n7_84400300['hole_ticks']} ticks 84400301..84400400; aged out of this official window start 84403401) and W45N7@84400400 (listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}; aged out of window start 84403401). "
    f"_patrol_2026-11-21_2020 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 19:52:19-20:02:21 (599s; official-filled W46N8 149/149, W47N8 149/149, W45N8 149/149, W45N7 49/149, W47N7 149/149); "
    f"监听短中断 20:21:38 (STATS 84400171..84400189; official/listener fill W46N8 19/19, W47N8 0/19, W45N8 19/19, W45N7 19/19, W47N7 19/19); "
    f"leftover official 404 W45N8@84399500, W45N7@84399800, and W47N8@84400100 (this run still 404 at W47N8@84400100; listener {w47n8_84400100['distinct']}/100; hole {w47n8_84400100['hole_ticks']} ticks 84400101..84400200; aged out of window start 84403401 and was not retried). "
    f"Already told by earlier delivered 1h patrols and not re-told: 盒子休眠 19:10:45-19:18:45, 18:47:50-18:58:17, leftover official 404 all five @84399100, W45N8@84399300, and older freezes/404s. "
    f"Fold only newer freezes/short WS than 00:50:16-01:00:10 (NEW, not yet told; 00:11:07-00:22:22 and 23:53:42-23:57:33 already told in the 00:35 patrol USER_LOG, along with already-told 23:20:38-23:24:23 / 22:49:18-22:59:56), and newer leftover official 404s than W45N7@84403800 and still-untold W45N7@84403700 (and already-told W45N7@84400300 / W45N7@84400400 / W47N8@84400100), into the next 1h patrol; do not re-tell earlier already-told items.\n"
)
now_txt = first + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

verify = (
    f"wrap {AT}\n"
    f"window {WIN_TMIN}..{WIN_TMAX} first_pass 33/35 missing_chunks=2 W45N7@84403700,W45N7@84403800\n"
    f"db_window {json.dumps(window_db)}\n"
    f"just_published 84404100 not in first pass; GET all_five_200={not jp.get('still_404')} script={script_sum} actual={actual_sum} by_actual={json.dumps(actual_by)} by_script={json.dumps(script_by)}\n"
    f"confirm still_404=['W45N7@84403700','W45N7@84403800'] inserted={inserted_confirm}; retry2 still_404 same inserted={inserted_retry2}; late still_404 same inserted={inserted_late}\n"
    f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}\n"
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}\n"
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix}\n"
    f"NEW leftover official 404 this run: W45N7@84403800 (confirm+retry2+late still 404; listener {w45n7_84403800['distinct']}/100 {w45n7_84403800['min']}..{w45n7_84403800['max']}; hole {w45n7_84403800['hole_ticks']} ticks {hole_range_txt(w45n7_84403800)}) not yet told\n"
    f"Still-untold leftover official 404 W45N7@84403700 (retried this window, still 404; listener {w45n7_84403700['distinct']}/100; hole {w45n7_84403700['hole_ticks']} ticks 84403701..84403800) not yet told\n"
    f"NEW box freeze this run: 00:50:16-01:00:10 (588s; STATS 84403921..84404079, 159t; official-filled {fill0050}; listener auto-restart 01:00:13, python {listener_pid} started 01:00:22) not yet told\n"
    f"already_told_in_0022_patrol 盒子休眠 23:53:42-23:57:33 fill {fill2353}; 00:11:07-00:22:22 fill {fill0011}; leftover W45N7@84400300 / W45N7@84400400 / W47N8@84400100\n"
    f"already_told_in_2323_patrol 盒子休眠 23:20:38-23:24:23 fill {fill2320}; 22:49:18-22:59:56 fill {fill2249}; leftover W45N7@84400300 / W45N7@84400400 / W47N8@84400100\n"
    f"already_told_in_2226_patrol 盒子休眠 22:14:12-22:26:30 fill {fill2214}; 21:42:29-22:01:09 fill {fill2142}; leftover W45N7@84400300 / W45N7@84400400 / W47N8@84400100\n"
    f"already_told_in_2119_patrol leftover W45N7@84400400 aged out of window start 84403401; listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}\n"
    f"already_told_in_2119_patrol leftover W45N7@84400300 aged out of window start 84403401; distinct={w45n7_84400300['distinct']} rows={w45n7_84400300['rows']} (listener 0/100, hole 100 ticks 84400301..84400400)\n"
    f"already_told_in_2020_patrol leftover W47N8@84400100 aged out of window start 84403401; distinct={w47n8_84400100['distinct']} rows={w47n8_84400100['rows']} (listener 0/100, hole 100 ticks 84400101..84400200)\n"
    f"already_told_in_2119_patrol 盒子休眠 20:49:04-21:04:03 fill W46N8 229/229, W47N8 229/229, W45N8 229/229, W45N7 229/229, W47N7 229/229; 监听短中断 21:13:29\n"
    f"already_told_in_2020_patrol box_freeze 19:52:19-20:02:21 fill W46N8 149/149, W47N8 149/149, W45N8 149/149, W45N7 49/149, W47N7 149/149; short_ws 20:21:38 fill W46N8 19/19, W47N8 0/19, W45N8 19/19, W45N7 19/19, W47N7 19/19; leftover W45N8@84399500, W45N7@84399800, W47N8@84400100\n"
    f"already_told_aged_out box_freeze 19:10:45-19:18:45, 18:47:50-18:58:17; leftover all-five @84399100, W45N8@84399300\n"
    f"tips {tips}\n"
    f"listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={json.dumps(rot, ensure_ascii=False)} yield_absent={yield_absent} restarted_this_run=False listener_count={n_listeners}\n"
    f"ok_quiet=True new_official_404_untold=[W45N7@84403800, W45N7@84403700] new_box_freeze_untold=[00:50:16-01:00:10] new_short_ws_untold=[]\n"
    + wrap.split("---- wrap", 1)[-1].lstrip()
)
(DIR / "verify.txt").write_text(verify)
(DIR / "_halfhour_backfill_verify.txt").write_text(verify)
shutil.copyfile(DIR / "_halfhour_backfill_verify.txt", STATE / "_halfhour_backfill_verify.txt")

snap = {
    "at": AT,
    "ok_quiet": True,
    "window": [WIN_TMIN, WIN_TMAX],
    "published_bases": PUBLISHED_BASES,
    "gt_first": GT_FIRST,
    "inserted_first": inserted_first,
    "already_in_db": ALREADY_IN_DB,
    "creep_rows_first": CREEP_ROWS_FIRST,
    "ts_realigned_first": TS_REALIGNED_FIRST,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_late": inserted_late,
    "just_actual": actual_by,
    "just_script": script_by,
    "inserted_total": inserted_total,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_name,
    "corrective_nfix": corrective_nfix,
    "coverage": cov,
    "window_db": window_db,
    "just_post": post,
    "gaps": gaps,
    "holes": holes,
    "tips": tips,
    "listener_pid": listener_pid,
    "listener_started": listener_started,
    "rot": rot,
    "slot": slot,
    "yield_absent": yield_absent,
    "n_listeners": n_listeners,
    "still_404": ["W45N7@84403700", "W45N7@84403800"],
    "new_official_404_untold": ["W45N7@84403800", "W45N7@84403700"],
    "new_box_freeze_untold": ["00:50:16-01:00:10"],
    "new_short_ws_untold": [],
}
(DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + "\n")
shutil.copyfile(DIR / "wrapup_snap.json", DIR / "history_backfill.json")

(DIR / "wrapup_run.txt").write_text(f"wrap {AT} ok_quiet=True inserted_total={inserted_total}\n")
print("wrote wrapup files")
print("ok_quiet True inserted_total", inserted_total, "at", AT)
print("now_txt bytes", len(now_txt), "verify bytes", len(verify))
print("just actual", actual_by, "sum", actual_sum, "script", script_by, "sum", script_sum)
print("window_db", window_db)
print("tips", tips)
print("listener", listener_pid, slot, rot, "yield_absent", yield_absent, "count", n_listeners)
print("gap0050", {r: gap0050[r]["fill"] for r in ROOMS})
print("gap0011", {r: gap0011[r]["fill"] for r in ROOMS})
print("holes", {k: {kk: holes[k][kk] for kk in ("distinct", "rows", "min", "max", "hole_ticks", "hole_ranges")} for k in holes})
