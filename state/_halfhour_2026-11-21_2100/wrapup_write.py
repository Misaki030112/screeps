#!/usr/bin/env python3
import json, shutil, subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_2100")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84400101, 84400800
JUST_BASE = 84400700
T0, T1 = JUST_BASE + 1, JUST_BASE + 100

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84400700.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
late = json.loads((DIR / "backfill_late_retry.json").read_text())
confirm_j = json.loads((DIR / "backfill_confirm_gets.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())

GAPS = [
    ("gap_2049_2104", 84400561, 84400789),  # NEW this run: box freeze 20:49:04-21:04:03, 895s; STATS 229t; listener auto-restart 21:04:06, python 2082229 started 21:04:16. Official-filled all five 229/229.
    ("gap_1952_2002", 84399771, 84399919),  # already in _patrol_2026-11-21_2020 USER_LOG (finished 20:35:40)
    ("gap_2021_shortws", 84400171, 84400189),  # already in _patrol_2026-11-21_2020 USER_LOG
]
HOLES = [
    ("W47N8", 84400100),
    ("W45N7", 84400300),
    ("W45N7", 84400400),
    ("W45N7", 84399800),
    ("W45N8", 84399500),
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

inserted_first = 11936
inserted_confirm = int(confirm_j.get("inserted") or 0)
inserted_retry2 = int(confirm_j.get("retry2_inserted") or 0)
inserted_late = int(late.get("inserted") or 0)
inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + actual_sum

tick_s_in_use = float(tick["tick_s_in_use"])
tick_s_first = float(tick["tick_s_used_first_pass"])
tick_s_name = tick.get("tick_s_in_use_name") or "all_mean"

out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
listener_ps = None
n_listeners = 0
for line in out.splitlines():
    if "tools/listener.py" in line:
        n_listeners += 1
        listener_ps = line.strip()
listener_pid, listener_parent, listener_started = 2086972, 4035476, "21:13:43"
if listener_ps:
    parts = listener_ps.split()
    listener_pid = int(parts[0])
    listener_parent = int(parts[1])
    # lstart is like: Sat Nov 21 21:13:43 2026
    if "21:" in listener_ps:
        for i, p in enumerate(parts):
            if p.count(":") == 1 and p.split(":")[0].isdigit():
                listener_started = p
                break

yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
slot = live.get("roomSlot")

w47n8_84400100 = holes["W47N8@84400100"]
w45n7_84400300 = holes["W45N7@84400300"]
w45n7_84400400 = holes["W45N7@84400400"]
w45n7_84399800 = holes["W45N7@84399800"]
w45n8_84399500 = holes["W45N8@84399500"]
gap2049 = gaps["gap_2049_2104"]
gap1952 = gaps["gap_1952_2002"]
gap2021 = gaps["gap_2021_shortws"]
fill2049 = ", ".join(f"{r} {gap2049[r]['fill']}" for r in ROOMS)
fill1952 = ", ".join(f"{r} {gap1952[r]['fill']}" for r in ROOMS)
fill2021 = ", ".join(f"{r} {gap2021[r]['fill']}" for r in ROOMS)

def hole_range_txt(h):
    if not h.get("hole_ranges"):
        return "none"
    parts = [f"{a}..{b}" for a, b in h["hole_ranges"]]
    return " and ".join(parts)

new_404 = {
    "room": "W45N7",
    "base": 84400400,
    "ticks": [84400401, 84400500],
    "listener": {"distinct": w45n7_84400400["distinct"], "rows": w45n7_84400400["rows"], "min": w45n7_84400400["min"], "max": w45n7_84400400["max"]},
    "hole_ticks": w45n7_84400400["hole_ticks"],
    "hole_ranges": w45n7_84400400["hole_ranges"],
    "first_seen": "first-pass 2026-11-21 21:06:04 Asia/Hong_Kong gt=84400810 still 404",
    "confirm": {"at": confirm_j.get("confirm_at") or confirm_j.get("at"), "game_time": confirm_j.get("confirm_game_time") or confirm_j.get("game_time"), "still_404": True, "inserted": 0},
    "retry2": {"at": confirm_j.get("retry2_at"), "game_time": confirm_j.get("retry2_game_time"), "still_404": True, "inserted": 0},
    "late_retry": {"at": late["at"], "game_time": late["game_time"], "still_404": True, "inserted": 0},
    "not_yet_told": True,
}

still_untold_84400300 = {
    "room": "W45N7",
    "base": 84400300,
    "from_run": "_halfhour_2026-11-21_2030",
    "still_404_this_run": True,
    "listener": {"distinct": w45n7_84400300["distinct"], "rows": w45n7_84400300["rows"]},
    "hole_ticks": w45n7_84400300["hole_ticks"],
    "hole_ranges": w45n7_84400300["hole_ranges"],
    "not_yet_told": True,
}

payload = {
    "ok_quiet": True,
    "at": AT,
    "window": [WIN_TMIN, WIN_TMAX],
    "published_bases": [84400100, 84400700],
    "game_time_first": 84400810,
    "first_pass": {
        "gets_200": 31,
        "gets_total": 35,
        "missing_chunks": ["W47N8@84400100", "W45N7@84400300", "W45N7@84400400", "W47N7@84400700"],
        "reconstructed": [84400101, 84400800],
        "creep_rows": 22715,
        "already_in_db": 10779,
        "inserted": 11936,
        "ts_realigned": 2945,
        "tick_s_printed": 4.336,
        "overlap_compared": 10674,
        "overlap_match": 10605,
        "overlap_differ": 69,
        "overlap_note": "Backfill does not overwrite existing rows. First-pass overlap 10605/10674 match; 69 diffs sampled at W47N8 84400786-84400787 (live listener just after 21:04 reconnect vs official history).",
    },
    "confirm": {
        "at": confirm_j.get("confirm_at") or confirm_j.get("at"),
        "skipped": False,
        "game_time": confirm_j.get("confirm_game_time") or confirm_j.get("game_time"),
        "still_404": ["W47N8@84400100", "W45N7@84400300", "W45N7@84400400"],
        "inserted": inserted_confirm,
        "recovered": confirm_j.get("recovered") or [],
    },
    "retry2": {
        "at": confirm_j.get("retry2_at"),
        "skipped": False,
        "game_time": confirm_j.get("retry2_game_time"),
        "still_404": confirm_j.get("retry2_still_404"),
        "inserted": inserted_retry2,
        "recovered": confirm_j.get("retry2_recovered") or [],
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
        "base": JUST_BASE,
        "included_in_first_pass": True,
        "first_pass_at": "2026-11-21 21:06:04 Asia/Hong_Kong",
        "first_pass_game_time": 84400810,
        "first_pass_w47n7_404": True,
        "reget_at": jp.get("at"),
        "game_time": jp.get("game_time"),
        "all_five_200": not jp.get("still_404"),
        "script_inserted": script_sum,
        "actual_inserted": actual_sum,
        "by_script": script_by,
        "by_actual": actual_by,
        "still_404": jp.get("still_404"),
    },
    "coverage": {
        "official_recovered": cov["official_recovered"],
        "expected": cov["expected"],
        "empty_no_creep": cov["empty_no_creep"],
        "official_404_missing": cov["official_404_missing"],
        "per_room": cov["coverage"],
        "w47n7_official_200_evac_empty": [[84400296, 84400496]],
        "w47n7_empty_ticks": 201,
    },
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_name,
    "ts_realigned_first": 2945,
    "corrective": {"applied": bool(tick.get("corrective_applied")), "nfix": int(tick.get("ts_realigned_to_later_mean") or 0)},
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
        "restarted_this_run": True,
        "restarts": [
            {"at": "21:04:06", "why": "box freeze 20:49:04-21:04:03", "python_started": "21:04:16", "pid": 2082229},
            {"at": "21:13:33", "why": "ws ping/pong timed out 21:13:29", "python_started": "21:13:43", "pid": 2086972},
        ],
    },
    "new_untold_official_404s": ["W45N7@84400400"],
    "still_untold_from_2030": ["W45N7@84400300"],
    "new_untold_box_freezes": [{
        "from": "2026-11-21 20:49:04",
        "to": "2026-11-21 21:04:03",
        "sec": 895,
        "stats": [84400561, 84400789],
        "stats_ticks": 229,
        "official_fill": {r: gap2049[r]["fill"] for r in ROOMS},
        "already_healed": True,
    }],
    "new_untold_short_ws": [{
        "at": "2026-11-21 21:13:29",
        "kind": "ping/pong",
        "box_pause_row": False,
        "restart": "21:13:33",
        "python_started": "21:13:43",
        "pid": 2086972,
        "stats_note": "no extra missing room_stats decile around 84400900..84400950 after reconnect; outside official history window end 84400800",
    }],
    "new_404_detail": new_404,
    "still_untold_84400300": still_untold_84400300,
    "written_in_2020_patrol_user_log": [
        "box_freeze 19:52:19-20:02:21",
        "short_ws 20:21:38",
        "W45N8@84399500",
        "W45N7@84399800",
        "W47N8@84400100",
    ],
}

(DIR / "wrapup_snap.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

confirm_at = confirm_j.get("confirm_at") or confirm_j.get("at")
confirm_gt = confirm_j.get("confirm_game_time") or confirm_j.get("game_time")
retry2_at = confirm_j.get("retry2_at")
retry2_gt = confirm_j.get("retry2_game_time")

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + "\n"
wrap = (
    f"---- wrap {AT} ----\n"
    f"confirm at {confirm_at} gt={confirm_gt} recovered W47N7@84400700 inserted={inserted_confirm}; still_404 W47N8@84400100, W45N7@84400300, W45N7@84400400. "
    f"retry2 at {retry2_at} gt={retry2_gt} still_404 same three leftovers inserted={inserted_retry2} (W47N7@84400700 already recovered, script {inserted_retry2}). "
    f"First pass 31/35 official GETs 200, missing_chunks=4 (W47N8@84400100 already written in _patrol_2026-11-21_2020 USER_LOG finished 20:35:40; W45N7@84400300 leftover not yet told from _halfhour_2026-11-21_2030; W45N7@84400400 new first-pass 404; W47N7@84400700 just-published first-pass 404, recovered on confirm). "
    f"Leftover official 404 W45N7@84399800 and W45N8@84399500 aged out of window start 84400101 and were not retried. "
    f"W47N7 official-200 evac empty in this window: 84400296..84400496 (201t), not 404s. "
    f"Just-published 84400700 was included in first pass at 2026-11-21 21:06:04 Asia/Hong_Kong gt=84400810 (4/5 official 200, W47N7 404); confirm recovered W47N7 at {confirm_at} gt={confirm_gt}; re-GET at {jp.get('at')} gt={jp.get('game_time')} all_five_200=True script={script_sum} actual={actual_sum}; "
    f"W46N8 script {script_by['W46N8']} vs actual {actual_by['W46N8']}, W47N8 script {script_by['W47N8']} vs actual {actual_by['W47N8']}, W45N8 script {script_by['W45N8']} vs actual {actual_by['W45N8']}, W45N7 script {script_by['W45N7']} vs actual {actual_by['W45N7']}, W47N7 script {script_by['W47N7']} vs actual {actual_by['W47N7']}. "
    f"just_actual=0 (insert WHERE NOT EXISTS on creep+tick; db already 100/100 all five at GET time). "
    f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
    f"tick_s_printed=4.336 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_name}) ts_realigned_first=2945 corrective=0. "
    f"First-pass overlap compared=10674 match=10605 differ=69 (not overwritten; W47N8 live reconnect edge 84400786-84400787). "
    f"Listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={json.dumps(rot, ensure_ascii=False)} yield_absent={yield_absent} listener_count={n_listeners} restarted_this_run=True "
    f"(auto-restart 21:04:06 after box freeze 20:49:04-21:04:03, python 2082229 started 21:04:16; then auto-restart 21:13:33 after short WS ping/pong 21:13:29, python 2086972 started 21:13:43). "
    f"NEW not-yet-told 盒子休眠 20:49:04-21:04:03 (895s, already healed; STATS 84400561..84400789, 229t; official-filled {fill2049}; listener auto-restart 21:04:06). "
    f"NEW not-yet-told 监听短中断 21:13:29 ping/pong (not a box freeze; no box_pauses row; restart 21:13:33, python 2086972 started 21:13:43; no extra missing room_stats decile around 84400900..84400950; sits after official window end 84400800). "
    f"NEW not-yet-told leftover official 404 W45N7@84400400 (first-pass 21:06:04 gt=84400810 + confirm {confirm_at} gt={confirm_gt} + retry2 {retry2_at} gt={retry2_gt} + late retry {late['at']} gt={late['game_time']} still 404; listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}). "
    f"Still not yet told from _halfhour_2026-11-21_2030: leftover official 404 W45N7@84400300 (confirm+retry2+late this run still 404; listener {w45n7_84400300['distinct']}/100; hole {w45n7_84400300['hole_ticks']} ticks 84400301..84400400). "
    f"_patrol_2026-11-21_2020 USER_LOG finished 20:35:40 already includes (treat as already told after that delivery; do not re-tell): "
    f"盒子休眠 19:52:19-20:02:21 (599s, already healed; STATS 84399771..84399919, 149t; official-filled {fill1952}; W45N7 still missing leftover official 404 W45N7@84399800; listener auto-restart 20:02:25); "
    f"监听短中断 20:21:38 ping/pong (not a box freeze; no box_pauses row; restart 20:21:41, python 2064860 started 20:21:51; STATS 84400171..84400189, 19t; official/listener fill {fill2021}; W47N8 0/19 because leftover official 404 W47N8@84400100); "
    f"leftover official 404 W45N8@84399500 (listener {w45n8_84399500['distinct']}/100 {w45n8_84399500['min']}..{w45n8_84399500['max']}; hole {w45n8_84399500['hole_ticks']} ticks; aged out of this official window start 84400101 and was not retried); "
    f"leftover official 404 W45N7@84399800 (aged out of this official window start 84400101 and was not retried; listener {w45n7_84399800['distinct']}/100; hole {w45n7_84399800['hole_ticks']} ticks 84399801..84399900); "
    f"leftover official 404 W47N8@84400100 (confirm+retry2+late this run still 404; listener {w47n8_84400100['distinct']}/100; hole {w47n8_84400100['hole_ticks']} ticks 84400101..84400200). "
    f"Already told by the delivered 19:18/19:28 1h patrol and not re-told: 盒子休眠 19:10:45-19:18:45, 18:47:50-18:58:17, leftover official 404 all five @84399100, W45N8@84399300, and older freezes/404s. "
    f"Fold only newer freezes, short WS gaps, or leftover official 404s than the 2020 patrol set (19:52:19-20:02:21, 20:21:38, W45N8@84399500, W45N7@84399800, W47N8@84400100) plus the still-untold W45N7@84400300 from the 20:30 backfill and this run's NEW W45N7@84400400 / 盒子休眠 20:49:04-21:04:03 / 监听短中断 21:13:29 once they are told; do not re-tell those 2020 items or earlier already-told items.\n"
)

now_txt = first + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

verify = (
    f"wrap {AT}\n"
    f"window {WIN_TMIN}..{WIN_TMAX} first_pass 31/35 missing_chunks=4 W47N8@84400100 W45N7@84400300 W45N7@84400400 W47N7@84400700(recovered_on_confirm)\n"
    f"db_window {json.dumps(window_db)}\n"
    f"W47N7 official-200 evac empty 84400296..84400496 (201t), not a 404\n"
    f"already-in-2020-patrol leftover W47N8@84400100 still 404 after confirm+retry2+late distinct={w47n8_84400100['distinct']} rows={w47n8_84400100['rows']} (listener 0/100, hole 100 ticks 84400101..84400200)\n"
    f"still-untold-from-2030 leftover W45N7@84400300 still 404 after confirm+retry2+late distinct={w45n7_84400300['distinct']} rows={w45n7_84400300['rows']} (listener 0/100, hole 100 ticks 84400301..84400400)\n"
    f"NEW leftover W45N7@84400400 still 404 after confirm+retry2+late {late['at']} gt={late['game_time']}; listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}\n"
    f"W45N7@84399800 and W45N8@84399500 leftovers aged out of window start 84400101 and were not retried\n"
    f"just_published 84400700 included_in_first_pass W47N7 first-pass 404 recovered on confirm; re-GET all_five_200=True script={script_sum} actual={actual_sum} by_actual={json.dumps(actual_by)} by_script={json.dumps(script_by)}\n"
    f"late_retry three leftovers {late['at']} gt={late['game_time']} still 404 inserted=0\n"
    f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}\n"
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}\n"
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first=2945 corrective=0\n"
    f"NEW_untold leftover official 404 W45N7@84400400; still-untold W45N7@84400300 from 20:30\n"
    f"NEW_untold 盒子休眠 20:49:04-21:04:03 fill {fill2049}\n"
    f"NEW_untold 监听短中断 21:13:29 ping/pong restart 21:13:33 pid={listener_pid} started={listener_started}\n"
    f"written_in_2020_patrol_user_log (treat as already told after 20:35:40 delivery; do not re-tell): box_freeze 19:52:19-20:02:21 fill {fill1952}; short_ws 20:21:38 fill {fill2021}; leftover W45N8@84399500, W45N7@84399800, W47N8@84400100\n"
    f"already_told_aged_out box_freeze 19:10:45-19:18:45, 18:47:50-18:58:17; leftover all-five @84399100, W45N8@84399300\n"
    f"overlap_differ=69 not overwritten\n"
    f"tips {tips}\n"
    f"listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={json.dumps(rot, ensure_ascii=False)} yield_absent={yield_absent} restarted_this_run=True listener_count={n_listeners}\n"
    f"ok_quiet=True new_official_404_untold=['W45N7@84400400'] still_untold_from_2030=['W45N7@84400300'] new_box_freeze_untold=['20:49:04-21:04:03'] new_short_ws_untold=['21:13:29']\n"
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
print("new_untold_404", ["W45N7@84400400"], "still_untold", ["W45N7@84400300"])
print("window_db", window_db)
print("tips", tips)
print("listener", listener_pid, slot, rot, "yield_absent", yield_absent, "count", n_listeners)
print("gap2049", {r: gap2049[r]["fill"] for r in ROOMS})
print("holes", {k: {kk: holes[k][kk] for kk in ("distinct", "rows", "min", "max", "hole_ticks", "hole_ranges")} for k in holes})
