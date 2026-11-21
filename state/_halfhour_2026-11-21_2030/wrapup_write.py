#!/usr/bin/env python3
import json, shutil, subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_2030")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84399701, 84400400
JUST_BASE = 84400300
T0, T1 = JUST_BASE + 1, JUST_BASE + 100

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84400300.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
late = json.loads((DIR / "backfill_late_retry.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())

# post counts and holes / gaps / tips
GAPS = [
    ("gap_1952_2002", 84399771, 84399919),  # already in _patrol_2026-11-21_2020 USER_LOG (finished 20:35:40): box freeze 19:52:19-20:02:21, 599s, already healed; STATS 149t; listener auto-restart 20:02:25, python 2055432 started 20:02:34.
    ("gap_2021_shortws", 84400171, 84400189),  # already in _patrol_2026-11-21_2020 USER_LOG: 监听短中断 20:21:38 ping/pong (not a box freeze; no box_pauses row); restart 20:21:41, python 2064860 started 20:21:51; STATS 19t; W47N8 0/19 because leftover official 404 W47N8@84400100.
    ("gap_1910_1918", 84399191, 84399309),  # already told by the delivered 19:18/19:28 1h patrol (and 2020 patrol will not re-tell); ages partly out of official window start 84399701.
]
HOLES = [
    ("W45N7", 84399800),
    ("W47N8", 84400100),
    ("W45N7", 84400300),
    ("W45N8", 84399500),
    ("W45N8", 84399300),
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
        holes[f"{room}@{base}"] = {
            "distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx,
            "hole_ticks": len(miss),
            "hole_ranges": None if not miss else (
                [[miss[0], miss[-1]]] if miss[-1]-miss[0]+1 == len(miss)
                else None
            ),
            "missing": None if not miss else f"{miss[0]}..{miss[-1]}" if miss[-1]-miss[0]+1 == len(miss) else miss,
        }
        # compute contiguous ranges
        if miss:
            ranges = []
            s = miss[0]
            prev = miss[0]
            for t in miss[1:]:
                if t != prev + 1:
                    ranges.append([s, prev])
                    s = t
                prev = t
            ranges.append([s, prev])
            holes[f"{room}@{base}"]["hole_ranges"] = ranges

    tips = {}
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute(f"select max(tick) from {table}").fetchone()[0]

script_by = {g["room"]: int(g.get("inserted") or 0) for g in (jp.get("gets") or [])}
for r in ROOMS:
    script_by.setdefault(r, 0)
actual_by = actual
actual_sum = sum(actual_by.values())
script_sum = sum(script_by.values())

inserted_first = 2482
inserted_confirm = 0
inserted_retry2 = 0
inserted_late = int(late.get("inserted") or 0)
inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + actual_sum

tick_s_in_use = float(tick["tick_s_in_use"])
tick_s_first = float(tick["tick_s_used_first_pass"])
tick_s_name = tick.get("tick_s_in_use_name") or "all_mean"

# listener process
out = subprocess.check_output(["ps","-o","pid,ppid,lstart,etime,stat,cmd","-C","python"], text=True)
listener_ps = None
for line in out.splitlines():
    if "tools/listener.py" in line:
        listener_ps = line.strip()
        break
# parse pid/start
listener_pid = 2064860
listener_started = "20:21:51"
listener_parent = 4035476
if listener_ps:
    parts = listener_ps.split()
    listener_pid = int(parts[0])
    listener_parent = int(parts[1])

yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
slot = live.get("roomSlot")

w45n8_84399500 = holes["W45N8@84399500"]
w45n7_84399800 = holes["W45N7@84399800"]
w47n8_84400100 = holes["W47N8@84400100"]
w45n7_84400300 = holes["W45N7@84400300"]
gap1952 = gaps["gap_1952_2002"]
gap2021 = gaps["gap_2021_shortws"]

new_404 = {
    "room": "W45N7",
    "base": 84400300,
    "ticks": [84400301, 84400400],
    "listener": {"distinct": w45n7_84400300["distinct"], "rows": w45n7_84400300["rows"], "min": w45n7_84400300["min"], "max": w45n7_84400300["max"]},
    "hole_ticks": w45n7_84400300["hole_ticks"],
    "hole_ranges": w45n7_84400300["hole_ranges"],
    "first_seen": "first-pass 2026-11-21 20:38:16 Asia/Hong_Kong gt=84400419 still 404 (just-published 84400300 included in first pass, before typical base+140=84400440)",
    "confirm": {"at": "2026-11-21 20:40:15 Asia/Hong_Kong", "game_time": 84400446, "still_404": True, "inserted": 0},
    "retry2": {"at": "2026-11-21 20:42:08 Asia/Hong_Kong", "game_time": 84400473, "still_404": True, "inserted": 0},
    "just_published": {"at": "2026-11-21 20:42:22 Asia/Hong_Kong", "game_time": 84400476, "still_404": True, "inserted": 0},
    "late_retry": {"at": late["at"], "game_time": late["game_time"], "still_404": True, "inserted": 0},
    "not_yet_told": True,
}

payload = {
    "ok_quiet": True,
    "at": AT,
    "window": [WIN_TMIN, WIN_TMAX],
    "published_bases": [84399700, 84400300],
    "game_time_first": 84400419,
    "first_pass": {
        "gets_200": 32,
        "gets_total": 35,
        "missing_chunks": ["W45N7@84399800", "W47N8@84400100", "W45N7@84400300"],
        "reconstructed": [84399701, 84400400],
        "creep_rows": 25360,
        "already_in_db": 22878,
        "inserted": 2482,
        "ts_realigned": 56,
        "tick_s_printed": 4.210,
        "overlap_compared": 22399,
        "overlap_match": 22397,
        "overlap_differ": 2,
        "overlap_note": "Backfill does not overwrite existing rows. First-pass overlap 22397/22399 match; 2 W47N8 diffs at 84400267 (w8rhauler84399119) and 84400296 (w8rminer84400063) during evac (listener vs official).",
    },
    "confirm": {
        "at": "2026-11-21 20:40:15 Asia/Hong_Kong",
        "skipped": False,
        "game_time": 84400446,
        "still_404": ["W45N7@84399800", "W47N8@84400100", "W45N7@84400300"],
        "inserted": 0,
        "recovered": [],
        "ssl_note": "W47N8@84400100 confirm attempt 1 transient URLError SSL EOF; subsequent attempt returned official 404 (not an aborted retry).",
    },
    "retry2": {
        "at": "2026-11-21 20:42:08 Asia/Hong_Kong",
        "skipped": False,
        "game_time": 84400473,
        "still_404": ["W45N7@84399800", "W47N8@84400100", "W45N7@84400300"],
        "inserted": 0,
        "recovered": [],
    },
    "late_retry": {
        "at": late["at"],
        "game_time": late["game_time"],
        "targets": late["targets"],
        "still_404": late["still_404"],
        "inserted": late["inserted"],
        "recovered": late["recovered"],
    },
    "just_published": {
        "base": 84400300,
        "included_in_first_pass": True,
        "first_pass_at": "2026-11-21 20:38:16 Asia/Hong_Kong",
        "first_pass_game_time": 84400419,
        "reget_at": jp["at"],
        "game_time": jp["game_time"],
        "all_five_200": False,
        "script_sum": script_sum,
        "actual_sum": actual_sum,
        "script_by_room": script_by,
        "actual_by_room": actual_by,
        "still_404": jp.get("still_404") or [],
        "w46n8_note": "W46N8 script 3 vs actual 0 (insert WHERE NOT EXISTS on creep+tick; db already 1223/100 at GET time, post still 1223).",
        "w47n7_note": "W47N7 official 200 empty 0/100 ticks 84400301..84400400 (evac; our creeps gone; not a 404). Combined with official-200 empty 84400296..84400300 in chunk 84400200 = 105t.",
        "w45n7_note": "W45N7@84400300 still 404 on first pass, confirm, retry2, just-published re-GET, and late retry; listener 0/100; hole 100 ticks 84400301..84400400.",
    },
    "coverage": {
        "official_recovered": cov["official_recovered"],
        "expected": cov["expected"],
        "empty_no_creep": cov["empty_no_creep"],
        "official_404_missing": cov["official_404_missing"],
        "w47n7_empty": "official 200 evac empty 84400296..84400300 (5t) in official-200 chunk 84400200 and 84400301..84400400 (100t) in official-200 chunk 84400300; 105t total, not 404s.",
    },
    "inserted_total": inserted_total,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_name,
    "tick_s_first": tick_s_first,
    "ts_realigned_first": 56,
    "corrective": bool(tick.get("corrective_applied")),
    "tips": tips,
    "window_db": window_db,
    "just_published_post": post,
    "gaps": gaps,
    "holes": holes,
    "listener": {
        "pid": listener_pid,
        "started": listener_started,
        "parent": listener_parent,
        "ps": listener_ps,
        "slot": slot,
        "rot": rot,
        "yield_absent": yield_absent,
        "restarted_this_run": False,
        "auto_restart_before_this_run": "2026-11-21 20:21:41 after short WS 20:21:38 (already in _patrol_2026-11-21_2020 USER_LOG); python 2064860 started 20:21:51",
        "count": 1,
    },
    "written_in_2020_patrol_user_log": {
        "patrol_dir": "_patrol_2026-11-21_2020",
        "finished_at": "2026-11-21 20:35:40 CST",
        "treat_as_already_told_after_delivery": True,
        "box_freezes": ["19:52:19-20:02:21"],
        "short_ws": ["20:21:38"],
        "official_404s": ["W45N8@84399500", "W45N7@84399800", "W47N8@84400100"],
        "note": "Do not re-tell these after the 20:20/20:35 patrol delivery. Official fill for 19:52 freeze is now W46N8/W47N8/W45N8/W47N7 149/149, W45N7 49/149 (30 ticks 84399771..84399800 plus 19 ticks 84399901..84399919 later filled; still missing leftover official 404 W45N7@84399800 100t).",
    },
    "already_told_by_1918_patrol": {
        "box_freezes_aged_or_out": ["19:10:45-19:18:45", "18:47:50-18:58:17", "17:51:07-17:58:33"],
        "official_404s_aged_out": ["W45N8@84399300", "W46N8@84399100", "W47N8@84399100", "W45N8@84399100", "W45N7@84399100", "W47N7@84399100"],
    },
    "new_untold_box_freezes": [],
    "new_untold_official_404s": [new_404],
    "new_untold_short_ws": [],
    "concurrent_patrol": "finished _patrol_2026-11-21_2020 at 20:35:40 CST before this run; _review12h_2026-11-21_20 was also in progress; did not write a patrol or 12h folder",
    "did_not_write_patrol_folder": True,
}

(DIR / "just_published_post_summary.json").write_text(json.dumps({
    "at": AT,
    "just_published_skipped": False,
    "included_in_first_pass": True,
    "post": post,
    "pre": pre,
    "actual_by_room": actual_by,
    "actual_sum": actual_sum,
    "script_by_room": script_by,
    "script_sum": script_sum,
    "gaps": gaps,
    "holes": holes,
    "tips": tips,
    "window_db": window_db,
    "first_pass_window": [WIN_TMIN, WIN_TMAX],
}, indent=2, default=str) + "\n")

(DIR / "wrapup_snap.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

# now.txt = first pass + wrap paragraph
first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + "\n"

w45n7_1952 = gap1952["W45N7"]
fill1952 = ", ".join(f"{r} {gap1952[r]['fill']}" for r in ROOMS)
fill2021 = ", ".join(f"{r} {gap2021[r]['fill']}" for r in ROOMS)

wrap = (
    f"---- wrap {AT} ----\n"
    f"confirm at 2026-11-21 20:40:15 Asia/Hong_Kong gt=84400446 still_404 W45N7@84399800, W47N8@84400100, W45N7@84400300 inserted=0 "
    f"(W47N8@84400100 confirm attempt 1 transient SSL EOF, then official 404); "
    f"retry2 at 2026-11-21 20:42:08 Asia/Hong_Kong gt=84400473 still_404 same three inserted=0. "
    f"First pass 32/35 official GETs 200, missing_chunks=3 (W45N7@84399800 and W47N8@84400100 already written in _patrol_2026-11-21_2020 USER_LOG finished 20:35:40; W45N7@84400300 new first-pass 404 on just-published 84400300). "
    f"Leftover official 404 W45N8@84399500 and older (W45N8@84399300 / all-five @84399100) aged out of window start 84399701 and were not retried. "
    f"W47N7 official-200 evac empty in this window: 84400296..84400300 (5t) in official-200 chunk 84400200 and 84400301..84400400 (100t) in official-200 chunk 84400300, 105t total, not 404s. "
    f"Just-published 84400300 was included in first pass at 2026-11-21 20:38:16 Asia/Hong_Kong gt=84400419 (4/5 official 200, W45N7 404, W47N7 official 200 empty); "
    f"re-GET at 2026-11-21 20:42:22 Asia/Hong_Kong gt=84400476 all_five_200=False script={script_sum} actual={actual_sum}; "
    f"W46N8 script {script_by.get('W46N8',0)} vs actual {actual_by.get('W46N8',0)}, "
    f"W47N8 script {script_by.get('W47N8',0)} vs actual {actual_by.get('W47N8',0)}, "
    f"W45N8 script {script_by.get('W45N8',0)} vs actual {actual_by.get('W45N8',0)}, "
    f"W45N7 script {script_by.get('W45N7',0)} vs actual {actual_by.get('W45N7',0)}, "
    f"W47N7 script {script_by.get('W47N7',0)} vs actual {actual_by.get('W47N7',0)}. "
    f"W46N8 script 3 vs actual 0 (insert WHERE NOT EXISTS on creep+tick; db already 1223/100 at GET time). "
    f"W47N7 official 200 empty 0/100, not a 404. W45N7@84400300 still 404. "
    f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
    f"inserted_first={inserted_first} confirm=0 retry2=0 late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
    f"tick_s_printed=4.210 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_name}) ts_realigned_first=56 corrective=0. "
    f"First-pass overlap compared=22399 match=22397 differ=2 (not overwritten). "
    f"Listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={json.dumps(rot, ensure_ascii=False)} yield=absent restarted_this_run=False "
    f"(auto-restart 20:21:41 after short WS 20:21:38, already in the 20:20 patrol USER_LOG). "
    f"No new box freeze or short WS this run. "
    f"NEW not-yet-told leftover official 404 W45N7@84400300 (first-pass + confirm 20:40:15 gt=84400446 + retry2 20:42:08 gt=84400473 + just-published re-GET 20:42:22/20:42:35 gt=84400476 + late retry {late['at']} gt={late['game_time']} still 404; listener {w45n7_84400300['distinct']}/100; hole {w45n7_84400300['hole_ticks']} ticks 84400301..84400400). "
    f"_patrol_2026-11-21_2020 USER_LOG finished 20:35:40 already includes (treat as already told after that delivery; do not re-tell): "
    f"盒子休眠 19:52:19-20:02:21 (599s, already healed; STATS 84399771..84399919, 149t; official-filled {fill1952}; W45N7 now {w45n7_1952['fill']} only 84399771..84399800 plus later-filled 84399901..84399919, still missing leftover official 404 W45N7@84399800; listener auto-restart 20:02:25, python 2055432 started 20:02:34); "
    f"监听短中断 20:21:38 ping/pong (not a box freeze; no box_pauses row; restart 20:21:41, python 2064860 started 20:21:51; STATS 84400171..84400189, 19t; official/listener fill {fill2021}; W47N8 0/19 because leftover official 404 W47N8@84400100); "
    f"leftover official 404 W45N8@84399500 (listener {w45n8_84399500['distinct']}/100 {w45n8_84399500['min']}..{w45n8_84399500['max']}; hole {w45n8_84399500['hole_ticks']} ticks; aged out of this official window start 84399701 and was not retried); "
    f"leftover official 404 W45N7@84399800 (confirm+retry2+late this run still 404; listener {w45n7_84399800['distinct']}/100; hole {w45n7_84399800['hole_ticks']} ticks 84399801..84399900); "
    f"leftover official 404 W47N8@84400100 (confirm+retry2+late this run still 404; listener {w47n8_84400100['distinct']}/100; hole {w47n8_84400100['hole_ticks']} ticks 84400101..84400200). "
    f"Already told by the delivered 19:18/19:28 1h patrol and not re-told: 盒子休眠 19:10:45-19:18:45, 18:47:50-18:58:17, leftover official 404 all five @84399100, W45N8@84399300, and older freezes/404s (now aged out of window start 84399701). "
    f"Fold only newer freezes, short WS gaps, or leftover official 404s than the 2020 patrol set (19:52:19-20:02:21, 20:21:38, W45N8@84399500, W45N7@84399800, W47N8@84400100) plus this NEW W45N7@84400300 once it is told; do not re-tell those 2020 items or earlier already-told items.\n"
)

now_txt = first + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

verify = (
    f"wrap {AT}\n"
    f"window {WIN_TMIN}..{WIN_TMAX} first_pass 32/35 missing_chunks=3 W45N7@84399800 W47N8@84400100 W45N7@84400300\n"
    f"db_window {json.dumps(window_db)}\n"
    f"W47N7 official-200 evac empty 84400296..84400300 (5t) and 84400301..84400400 (100t), 105t total, not a 404\n"
    f"already-in-2020-patrol leftover W45N7@84399800 still 404 after confirm+retry2+late distinct={w45n7_84399800['distinct']} rows={w45n7_84399800['rows']} (listener {w45n7_84399800['distinct']}/100, hole {w45n7_84399800['hole_ticks']} ticks 84399801..84399900)\n"
    f"already-in-2020-patrol leftover W47N8@84400100 still 404 after confirm+retry2+late distinct={w47n8_84400100['distinct']} rows={w47n8_84400100['rows']} (listener {w47n8_84400100['distinct']}/100, hole {w47n8_84400100['hole_ticks']} ticks 84400101..84400200)\n"
    f"NEW leftover W45N7@84400300 still 404 after confirm+retry2+just-pub+late {late['at']} gt={late['game_time']}; listener {w45n7_84400300['distinct']}/100; hole {w45n7_84400300['hole_ticks']} ticks 84400301..84400400\n"
    f"W45N8@84399500 leftover aged out of window start 84399701 and was not retried (listener {w45n8_84399500['distinct']}/100 {w45n8_84399500['min']}..{w45n8_84399500['max']}, hole {w45n8_84399500['hole_ticks']}; already in 2020 patrol USER_LOG)\n"
    f"just_published 84400300 included_in_first_pass all_five_200=False script={script_sum} actual={actual_sum} by_actual={json.dumps(actual_by)} by_script={json.dumps(script_by)} still_404={jp.get('still_404')} W46N8 script 3 vs actual 0; W47N7 official 200 empty 0/100 not a 404; W45N7 still 404\n"
    f"late_retry three leftovers {late['at']} gt={late['game_time']} still 404 inserted=0\n"
    f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}\n"
    f"inserted_first={inserted_first} confirm=0 retry2=0 late={inserted_late} just_actual={actual_sum} total={inserted_total}\n"
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first=56 corrective=0\n"
    f"NEW_untold leftover official 404 W45N7@84400300 first-pass+confirm+retry2+just-pub+late still 404 listener {w45n7_84400300['distinct']}/100 hole 100\n"
    f"written_in_2020_patrol_user_log (treat as already told after 20:35:40 delivery; do not re-tell): box_freeze 19:52:19-20:02:21 fill {fill1952}; short_ws 20:21:38 fill {fill2021}; leftover W45N8@84399500, W45N7@84399800, W47N8@84400100\n"
    f"already_told_aged_out box_freeze 19:10:45-19:18:45, 18:47:50-18:58:17, 17:51:07-17:58:33; leftover all-five @84399100, W45N8@84399300\n"
    f"overlap_differ=2 not overwritten\n"
    f"tips {tips}\n"
    f"listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={json.dumps(rot, ensure_ascii=False)} yield_absent={yield_absent} restarted_this_run=False\n"
    f"ok_quiet=True new_official_404_untold=['W45N7@84400300'] new_box_freeze_untold=[] new_short_ws_untold=[]\n"
    + wrap.split("---- wrap",1)[-1].lstrip()
)
(DIR / "verify.txt").write_text(verify)
(DIR / "_halfhour_backfill_verify.txt").write_text(verify)
shutil.copyfile(DIR / "_halfhour_backfill_verify.txt", STATE / "_halfhour_backfill_verify.txt")

(DIR / "wrapup_run.txt").write_text(f"wrap {AT} ok_quiet=True inserted_total={inserted_total}\n")
print("wrote wrapup files")
print("ok_quiet True inserted_total", inserted_total, "at", AT)
print("now_txt bytes", len(now_txt), "verify bytes", len(verify))
print("just actual", actual_by, "sum", actual_sum, "script", script_by, "sum", script_sum)
print("new_untold_404", [new_404["room"]+"@"+str(new_404["base"])])
print("window_db", window_db)
print("tips", tips)
print("listener", listener_pid, slot, rot, "yield_absent", yield_absent)
print("gap1952", {r: gap1952[r]["fill"] for r in ROOMS})
print("gap2021", {r: gap2021[r]["fill"] for r in ROOMS})
print("holes", {k: {kk: holes[k][kk] for kk in ("distinct","rows","min","max","hole_ticks","hole_ranges")} for k in holes})
