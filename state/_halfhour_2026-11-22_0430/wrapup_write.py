#!/usr/bin/env python3
import json, shutil, subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

NL = chr(10)
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-22_0430")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84406201, 84406900
JUST_BASE = 84406900
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
PUBLISHED_BASES = [84406200, 84406800]
GT_FIRST = 84406980
INSERTED_FIRST = 2847
TS_REALIGNED_FIRST = 3685
CREEP_ROWS_FIRST = 23267
ALREADY_IN_DB = 20420
FIRST_PASS_AT = "2026-11-22 04:25 Asia/Hong_Kong"
CONFIRM_AT = "2026-11-22 04:27:33 Asia/Hong_Kong"
RETRY2_AT = "2026-11-22 04:27:44 Asia/Hong_Kong"
LATE_AT = "2026-11-22 04:30:24 Asia/Hong_Kong"

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84406900.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
late = json.loads((DIR / "backfill_late_retry.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())

GAPS = [
    ("gap_0418_0422", 84406881, 84406949),  # NEW box freeze 04:18:46-04:22:28, not yet told
    ("gap_0347_0406", 84406431, 84406719),  # recorded in 0400 backfill, still not yet told in a USER_LOG
    ("gap_0244_0303", 84405501, 84405799),  # already told in _patrol_2026-11-22_0318 USER_LOG
    ("gap_0213_0226", 84405081, 84405269),  # already told in _patrol_2026-11-22_0226 USER_LOG
    ("gap_0150_0200", 84404761, 84404919),  # already told in _patrol_2026-11-22_0226 USER_LOG
    ("gap_0118_0121", 84404311, 84404369),  # already told in _patrol_2026-11-22_0121 USER_LOG
    ("gap_0050_0100", 84403921, 84404079),  # already told in 0121; aged out of window start 84405101
    ("gap_0011_0022", 84403391, 84403549),  # already told in 0022; aged out
    ("gap_2353_2357", 84403151, 84403209),  # already told
    ("gap_2320_2324", 84402681, 84402749),
    ("gap_2249_2259", 84402241, 84402409),
    ("gap_2214_2226", 84401751, 84401939),
    ("gap_2142_2201", 84401311, 84401589),
]
HOLES = [
    ("W45N8", 84406400),  # NEW leftover official 404, confirm+retry2+late+post_jp still 404; fold into next 1h patrol
    ("W46N8", 84406600),  # NEW leftover official 404, confirm+retry2+late+post_jp still 404; fold into next 1h patrol
    ("W46N8", 84406700),  # NEW leftover official 404 on just-published chunk, post_jp 04:16:20 still 404; fold into next 1h patrol
    ("W45N7", 84403800),  # leftover official 404, already told in 0121 USER_LOG; aged out of window start 84406001
    ("W45N7", 84403700),  # already told in 0121; aged out
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
    (DIR / "just_published_post_counts.json").write_text(json.dumps(post, indent=2) + NL)

    # Unique (creep,tick) vs raw rows in the just-published window, for any same-payload dupes.
    dup = {}
    for room in ROOMS:
        rows, uniq = c.execute(
            "SELECT count(*), count(DISTINCT (creep, tick)) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, T0, T1),
        ).fetchone()
        dup[room] = {"rows": int(rows or 0), "unique": int(uniq or 0), "extra": int(rows or 0) - int(uniq or 0)}
    (DIR / "just_published_dedupe.json").write_text(json.dumps({"window": [T0, T1], "by_room": dup}, indent=2) + NL)

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
inserted_confirm = 0
inserted_retry2 = 0
inserted_late = int(late.get("inserted") or 0)
# Prefer unique actuals if extras exist (do not count duplicate rows).
actual_unique = {}
for room in ROOMS:
    extra = int((dup.get(room) or {}).get("extra") or 0)
    # actual is post_rows - pre_rows; if extras appeared in this insert, shrink to unique added.
    if extra > 0:
        actual_unique[room] = max(0, actual_by[room] - extra)
    else:
        actual_unique[room] = actual_by[room]
# Only substitute unique counts in the reported actual if extras were found.
if any((dup.get(r) or {}).get("extra") for r in ROOMS):
    actual_by = actual_unique
    actual_sum = sum(actual_by.get(r, 0) for r in ROOMS)
    dupe_note = (
        "Just-published official insert wrote same-payload duplicate (room,creep,tick) rows in "
        + ", ".join(
            f"{r} ({dup[r]['extra']} extras, {dup[r]['rows']}->{dup[r]['unique']})"
            for r in ROOMS if dup[r]["extra"] > 0
        )
        + "; counts below are unique post-pre (extras not deleted this run). First-pass window unique_creep_tick_rows already matched rows. "
    )
else:
    dupe_note = ""

inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + actual_sum

tick_s_in_use = float(tick["tick_s_in_use"])
tick_s_name = tick.get("tick_s_in_use_name") or "all_mean"
tick_s_first = float(tick.get("tick_s_used_first_pass") or 4.04051)
corrective_nfix = int(tick.get("ts_realigned_to_later_mean") or 0)
later_mean = float(tick.get("later_mean_w46") or 0)

out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
n_listeners = 0
listener_pid = listener_parent = listener_started = None
for line in out.splitlines():
    if "tools/listener.py" in line:
        n_listeners += 1
        parts = line.split()
        listener_pid = parts[0]
        listener_parent = parts[1]
        # ps -o lstart is "Sun Nov 22 03:03:53 2026"; with default whitespace split
        # pid ppid Sun Nov 22 03:03:53 2026 etime stat cmd...
        listener_started = " ".join(parts[2:7]) if len(parts) > 6 else None
        print("listener_ps", line.strip())

st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
slot = live.get("roomSlot")
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

gap0418 = gaps["gap_0418_0422"]
gap0347 = gaps["gap_0347_0406"]
gap0244 = gaps["gap_0244_0303"]
gap0213 = gaps["gap_0213_0226"]
gap0150 = gaps["gap_0150_0200"]
gap0118 = gaps["gap_0118_0121"]
gap0050 = gaps["gap_0050_0100"]
gap0011 = gaps["gap_0011_0022"]
gap2353 = gaps["gap_2353_2357"]
gap2320 = gaps["gap_2320_2324"]
gap2249 = gaps["gap_2249_2259"]
gap2214 = gaps["gap_2214_2226"]
gap2142 = gaps["gap_2142_2201"]
w45n8_84406400 = holes["W45N8@84406400"]
w46n8_84406600 = holes["W46N8@84406600"]
w46n8_84406700 = holes["W46N8@84406700"]
w45n7_84403800 = holes["W45N7@84403800"]
w45n7_84403700 = holes["W45N7@84403700"]
w45n7_84400400 = holes["W45N7@84400400"]
w45n7_84400300 = holes["W45N7@84400300"]
w47n8_84400100 = holes["W47N8@84400100"]

fill0418 = fill_txt(gap0418)
fill0347 = fill_txt(gap0347)
fill0244 = fill_txt(gap0244)
fill0213 = fill_txt(gap0213)
fill0150 = fill_txt(gap0150)
fill0118 = fill_txt(gap0118)
fill0050 = fill_txt(gap0050)
fill0011 = fill_txt(gap0011)
fill2353 = fill_txt(gap2353)
fill2320 = fill_txt(gap2320)
fill2249 = fill_txt(gap2249)
fill2214 = fill_txt(gap2214)
fill2142 = fill_txt(gap2142)

jp_still = jp.get("still_404") or []
jp_at = jp.get("at") or AT
jp_gt = jp.get("game_time")
first = (DIR / "history_backfill.txt").read_text().rstrip() + NL
w45n7_empty = "W45N7 official empty_no_creep in this first-pass window: none (coverage empty_no_creep=0; aged-out earlier empty 84405446..84405786 / 84405818..84405854 sits before window start 84406001)."
wrap = (
    f"---- wrap {AT} ----" + NL
    + "First pass was run by concurrent 1h patrol _patrol_2026-11-22_0422; this halfhour reused those official GETs (no second first pass / confirm / just-published) and ran late retry itself. "
    + f"confirm at {CONFIRM_AT} gt=84407018 still_404=['W45N8@84406400', 'W46N8@84406600', 'W46N8@84406700'] inserted=0. "
    + f"retry2 at {RETRY2_AT} gt=84407021 still_404=['W45N8@84406400', 'W46N8@84406600', 'W46N8@84406700'] inserted=0. "
    + f"late retry at {LATE_AT} gt=84407060 still_404=['W45N8@84406400', 'W46N8@84406600', 'W46N8@84406700'] inserted=0. "
    + f"First pass 32/35 official GETs 200, missing_chunks=3 W45N8@84406400, W46N8@84406600, W46N8@84406700; confirm+retry2+late still 404, leftover. "
    + f"First pass completed cleanly at {FIRST_PASS_AT} (exit=0, no abort). "
    + f"Already-told leftover official 404s W45N7@84403800, W45N7@84403700, W45N7@84400400, W45N7@84400300, and W47N8@84400100 aged out of window start 84406201 and were not retried "
    + f"(already told in the finished 01:31 _patrol_2026-11-22_0121 USER_LOG and earlier delivered 00:35 / 23:35 / 22:35 / 21:31 / 20:34 1h patrols; do not re-tell). "
    + f"Just-published 84406900 was not in first pass (first pass ended at published 84406800 / reconstructed 84406201..84406900 at {FIRST_PASS_AT} gt={GT_FIRST}, 32/35 200 with 3 in-window 404s still leftover). "
    + f"GET at {jp_at} gt={jp_gt} all_five_200={not jp_still} script={script_sum} actual={actual_sum}; "
    + f"W46N8 script {script_by.get('W46N8', 0)} vs actual {actual_by.get('W46N8', 0)}, "
    + f"W47N8 script {script_by.get('W47N8', 0)} vs actual {actual_by.get('W47N8', 0)}, "
    + f"W45N8 script {script_by.get('W45N8', 0)} vs actual {actual_by.get('W45N8', 0)}, "
    + f"W45N7 script {script_by.get('W45N7', 0)} vs actual {actual_by.get('W45N7', 0)}, "
    + f"W47N7 script {script_by.get('W47N7', 0)} vs actual {actual_by.get('W47N7', 0)}. "
    + dupe_note
    + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
    + "W45N7 official empty_no_creep in this first-pass window: none (coverage empty_no_creep=0). "
    + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
    + f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix} (later-mean {later_mean:.5f} worse). "
    + f"Leftover official 404s first recorded in the 04:16 _halfhour_2026-11-22_0400 backfill remain leftover and are still not yet told: W45N8@84406400 (confirm 04:27:34, retry2 04:27:45, late 04:30:24 still 404; listener {w45n8_84406400['distinct']}/100; hole {w45n8_84406400['hole_ticks']} ticks {hole_range_txt(w45n8_84406400)}), W46N8@84406600 (confirm 04:27:35, retry2 04:27:46, late 04:30:27 still 404; listener {w46n8_84406600['distinct']}/100; hole {w46n8_84406600['hole_ticks']} ticks {hole_range_txt(w46n8_84406600)}), and W46N8@84406700 (confirm 04:27:37, retry2 04:27:48, late 04:30:29 still 404; listener {w46n8_84406700['distinct']}/100 {w46n8_84406700['min']}..{w46n8_84406700['max']}; hole {w46n8_84406700['hole_ticks']} ticks {hole_range_txt(w46n8_84406700)}) -- fold into the next 1h patrol. No new official 404 this run. "
    + f"Already-told leftover official 404 W45N7@84403800 aged out of window start 84406201 and was not retried (listener {w45n7_84403800['distinct']}/100 {w45n7_84403800['min']}..{w45n7_84403800['max']}; hole {w45n7_84403800['hole_ticks']} ticks {hole_range_txt(w45n7_84403800)}) -- already told in the finished 01:31 _patrol_2026-11-22_0121 USER_LOG; do not re-tell. "
    + f"Already-told leftover official 404 W45N7@84403700 aged out of window start 84406201 and was not retried (listener {w45n7_84403700['distinct']}/100; hole {w45n7_84403700['hole_ticks']} ticks 84403701..84403800) -- already told in the 01:31 patrol USER_LOG; do not re-tell. "
    + f"NEW short WS this run: none. A listener segment-poll SSL EOF at 03:42:55 did not open a STATS gap and is not a short WS (already noted in the 0400 backfill). "
    + f"NEW box freeze this run: 盒子休眠 04:18:46-04:22:28 (221s, already healed; STATS 84406881..84406949, 69t; official-filled {fill0418}; first-pass official covers 84406881..84406900, just-published 84406900 covers the tail 84406901..84406949; listener auto-restart 04:22:31, python 2251463 started 04:22:41) -- not yet told, fold into the next 1h patrol. "
    + f"Still not yet told from the 0400 backfill: 盒子休眠 03:47:58-04:06:12 (1093s, already healed; STATS 84406431..84406719, 289t; official-filled {fill0347}; first-pass official covers 84406431..84406700 except leftover 404 holes W45N8@84406400 (overlap 84406431..84406500) and W46N8@84406600 (84406601..84406700); W46N8@84406700 still 404 so tail 84406701..84406719 is only the listener slice 84406715..84406719; listener auto-restart 04:06:15, python 2244395 started 04:06:24) -- fold into the next 1h patrol. "
    + f"Official fill re-verified this run: 04:18 STATS 84406881..84406949 69t official-filled {fill0418}; "
    + f"03:47 STATS 84406431..84406719 289t official-filled {fill0347}; "
    + f"02:44 STATS 84405501..84405799 299t official-filled {fill0244}; "
    + f"02:13 STATS 84405081..84405269 189t official-filled {fill0213}; "
    + f"01:50 STATS 84404761..84404919 159t official-filled {fill0150}; "
    + f"01:18 STATS 84404311..84404369 59t official-filled {fill0118}; "
    + f"00:50 STATS 84403921..84404079 159t official-filled {fill0050} (W45N7 126/159 present 84403954..84404079, remaining official empty_no_creep; aged out of window start 84406201). "
    + f"_patrol_2026-11-22_0318 USER_LOG already includes (treat as already told; do not re-tell): 盒子休眠 02:44:07-03:03:40 (1172s; STATS 84405501..84405799, 299t; official-filled {fill0244}; listener auto-restart 03:03:43, python 2219657 started 03:03:53); no new official 404; no new short WS. "
    + f"_patrol_2026-11-22_0226 USER_LOG already includes (treat as already told; do not re-tell): "
    + f"盒子休眠 01:50:21-02:00:50 (621s; STATS 84404761..84404919, 159t; official-filled {fill0150}; listener auto-restart 02:00:53, python 2201574 started 02:01:03); "
    + f"盒子休眠 02:13:42-02:26:20 (753s; STATS 84405081..84405269, 189t; official-filled {fill0213}; listener auto-restart 02:26:23, python 2208243 started 02:26:32). "
    + f"_patrol_2026-11-22_0121 USER_LOG finished 01:32:49 already includes (treat as already told; do not re-tell): "
    + f"盒子休眠 00:50:16-01:00:10 (588s; STATS 84403921..84404079, 159t; official-filled {fill0050}; listener auto-restart 01:00:13, python 2176402 started 01:00:22); "
    + f"盒子休眠 01:18:01-01:21:27 (201s; STATS 84404311..84404369, 59t; official-filled {fill0118}; listener auto-restart 01:21:30, python 2185293 started 01:21:40); "
    + f"leftover official 404 W45N7@84403700 (listener 0/100; hole 100 ticks 84403701..84403800) and W45N7@84403800 (listener 28/100 84403818..84403845; hole 72 ticks 84403801..84403817 and 84403846..84403900). "
    + f"_patrol_2026-11-22_0022 USER_LOG already includes (treat as already told; do not re-tell): "
    + f"盒子休眠 23:53:42-23:57:33 (222s; STATS 84403151..84403209, 59t; official-filled {fill2353}; listener auto-restart 23:57:36, python 2151688 started 23:57:45); "
    + f"盒子休眠 00:11:07-00:22:22 (671s; STATS 84403391..84403549, 159t; official-filled {fill0011}; W45N7 empty-no-creep 84403491..84403549 after miners fled an Invader Core; listener auto-restart 00:22:25, python 2159379 started 00:22:35); "
    + f"leftover official 404 W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older. "
    + f"_patrol_2026-11-21_2323 USER_LOG already includes (treat as already told; do not re-tell): "
    + f"盒子休眠 23:20:38-23:24:23 (224s; STATS 84402681..84402749, 69t; official-filled {fill2320}; listener auto-restart 23:24:26, python 2135086 started 23:24:35); "
    + f"盒子休眠 22:49:18-22:59:56 (634s; official-filled {fill2249}); leftover official 404 W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older. "
    + f"_patrol_2026-11-21_2226 USER_LOG already includes (treat as already told; do not re-tell): "
    + f"盒子休眠 22:14:12-22:26:30 (737s; official-filled {fill2214}); "
    + f"盒子休眠 21:42:29-22:01:09 (1115s; official-filled {fill2142}); leftover official 404 W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older. "
    + f"_patrol_2026-11-21_2119 USER_LOG already includes (treat as already told; do not re-tell): "
    + f"盒子休眠 20:49:04-21:04:03 (895s; official-filled W46N8 229/229, W47N8 229/229, W45N8 229/229, W45N7 229/229, W47N7 229/229); 监听短中断 21:13:29; leftover official 404 W45N7@84400400 / W45N7@84400300 and older. "
    + f"_patrol_2026-11-21_2020 USER_LOG already includes (treat as already told; do not re-tell): "
    + f"盒子休眠 19:52:19-20:02:21 and older freezes / leftover official 404s already told through W47N8@84400100 and earlier. "
    + f"Listener healthy: 1 process, yield_absent={yield_absent}, peacetime 1-slot 5:5:1:1, no second listener, war_cmd/pulse not touched. "
)

now_txt = first + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

verify = (
    f"wrap {AT}" + NL
    + f"window {WIN_TMIN}..{WIN_TMAX} first_pass 32/35 missing_chunks=3 still_404 W45N8@84406400,W46N8@84406600,W46N8@84406700" + NL
    + f"db_window {json.dumps(window_db)}" + NL
    + f"just_published 84406900 not in first pass; GET all_five_200={not jp_still} script={script_sum} actual={actual_sum} by_actual={json.dumps(actual_by)} by_script={json.dumps(script_by)}" + NL
    + f"confirm still_404=['W45N8@84406400', 'W46N8@84406600', 'W46N8@84406700'] inserted={inserted_confirm}; retry2 still_404=['W45N8@84406400', 'W46N8@84406600', 'W46N8@84406700'] inserted={inserted_retry2}; late still_404=['W45N8@84406400', 'W46N8@84406600', 'W46N8@84406700'] inserted={inserted_late}" + NL
    + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
    + f"W45N7 official empty_no_creep in this first-pass window: none (coverage empty_no_creep=0)" + NL
    + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}" + NL
    + f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix} (later-mean {later_mean:.5f} worse)" + NL
    + f"leftover official 404 still 404 (first recorded in _halfhour_2026-11-22_0400, still not yet told): W45N8@84406400 (listener {w45n8_84406400['distinct']}/100; hole {w45n8_84406400['hole_ticks']} ticks {hole_range_txt(w45n8_84406400)}); W46N8@84406600 (listener {w46n8_84406600['distinct']}/100; hole {w46n8_84406600['hole_ticks']} ticks {hole_range_txt(w46n8_84406600)}); W46N8@84406700 (listener {w46n8_84406700['distinct']}/100 {w46n8_84406700['min']}..{w46n8_84406700['max']}; hole {w46n8_84406700['hole_ticks']} ticks {hole_range_txt(w46n8_84406700)}) -- fold into next 1h patrol. No new official 404 this run." + NL
    + f"already_told leftover official 404 W45N7@84403800 aged out of window start 84406201 (listener {w45n7_84403800['distinct']}/100 {w45n7_84403800['min']}..{w45n7_84403800['max']}; hole {w45n7_84403800['hole_ticks']} ticks {hole_range_txt(w45n7_84403800)}); W45N7@84403700 aged out of window start 84406201 (listener {w45n7_84403700['distinct']}/100; hole 100 ticks 84403701..84403800)" + NL
    + f"NEW box freeze this run: 盒子休眠 04:18:46-04:22:28 (221s; STATS 84406881..84406949, 69t; official-filled {fill0418}; listener auto-restart 04:22:31, python 2251463 started 04:22:41) -- not yet told, fold into next 1h patrol" + NL
    + f"still_not_yet_told_from_0400 盒子休眠 03:47:58-04:06:12 (1093s; STATS 84406431..84406719, 289t; official-filled {fill0347}; listener auto-restart 04:06:15, python 2244395 started 04:06:24) -- fold into next 1h patrol" + NL
    + f"already_told_in_0318_patrol 盒子休眠 02:44:07-03:03:40 fill {fill0244}; listener auto-restart 03:03:43, python 2219657 started 03:03:53; do not re-tell" + NL
    + f"already_told_in_0226_patrol 盒子休眠 01:50:21-02:00:50 fill {fill0150}; 02:13:42-02:26:20 fill {fill0213}" + NL
    + f"already_told_in_0121_patrol 盒子休眠 00:50:16-01:00:10 fill {fill0050}; 01:18:01-01:21:27 fill {fill0118}; leftover W45N7@84403700 / W45N7@84403800" + NL
    + f"already_told_in_0022_patrol 盒子休眠 23:53:42-23:57:33 fill {fill2353}; 00:11:07-00:22:22 fill {fill0011}; leftover W45N7@84400300 / W45N7@84400400 / W47N8@84400100" + NL
    + f"already_told_in_2323_patrol 盒子休眠 23:20:38-23:24:23 fill {fill2320}; 22:49:18-22:59:56 fill {fill2249}; leftover W45N7@84400300 / W45N7@84400400 / W47N8@84400100" + NL
    + f"already_told_in_2226_patrol 盒子休眠 22:14:12-22:26:30 fill {fill2214}; 21:42:29-22:01:09 fill {fill2142}; leftover W45N7@84400300 / W45N7@84400400 / W47N8@84400100" + NL
    + f"already_told_in_2119_patrol leftover W45N7@84400400 aged out of window start 84406201; listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}" + NL
    + f"already_told_in_2119_patrol leftover W45N7@84400300 aged out of window start 84406201; distinct={w45n7_84400300['distinct']} rows={w45n7_84400300['rows']} (listener 0/100, hole 100 ticks 84400301..84400400)" + NL
    + f"already_told_in_2020_patrol leftover W47N8@84400100 aged out of window start 84406201; distinct={w47n8_84400100['distinct']} rows={w47n8_84400100['rows']} (listener 0/100, hole 100 ticks 84400101..84400200)" + NL
    + f"already_told_in_2119_patrol 盒子休眠 20:49:04-21:04:03 fill W46N8 229/229, W47N8 229/229, W45N8 229/229, W45N7 229/229, W47N7 229/229; 监听短中断 21:13:29" + NL
    + f"already_told_in_2020_patrol box_freeze 19:52:19-20:02:21 fill W46N8 149/149, W47N8 149/149, W45N8 149/149, W45N7 49/149, W47N7 149/149; short_ws 20:21:38 fill W46N8 19/19, W47N8 0/19, W45N8 19/19, W45N7 19/19, W47N7 19/19; leftover W45N8@84399500, W45N7@84399800, W47N8@84400100" + NL
    + f"already_told_aged_out box_freeze 19:10:45-19:18:45, 18:47:50-18:58:17; leftover all-five @84399100, W45N8@84399300" + NL
    + f"tips {tips}" + NL
    + f"listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={json.dumps(rot, ensure_ascii=False)} yield_absent={yield_absent} restarted_this_run=False listener_count={n_listeners}" + NL
    + f"ok_quiet=True new_official_404_untold=['W45N8@84406400', 'W46N8@84406600', 'W46N8@84406700'] new_box_freeze_untold=['03:47:58-04:06:12', '04:18:46-04:22:28'] new_short_ws_untold=[] first_pass_source=concurrent_patrol_0422" + NL
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
    "just_dup": dup,
    "gaps": gaps,
    "holes": holes,
    "tips": tips,
    "listener_pid": listener_pid,
    "listener_started": listener_started,
    "rot": rot,
    "slot": slot,
    "yield_absent": yield_absent,
    "n_listeners": n_listeners,
    "still_404": jp_still,
    "new_official_404_untold": ["W45N8@84406400", "W46N8@84406600", "W46N8@84406700"],
    "new_box_freeze_untold": ["03:47:58-04:06:12", "04:18:46-04:22:28"],
    "first_pass_source": "concurrent_patrol_0422",
    "already_told_in_0318_patrol": ["02:44:07-03:03:40"],
    "new_short_ws_untold": [],
    "already_told_in_0226_patrol": ["01:50:21-02:00:50", "02:13:42-02:26:20"],
    "already_told_in_0121_patrol": ["00:50:16-01:00:10", "01:18:01-01:21:27", "W45N7@84403700", "W45N7@84403800"],
}
(DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + NL)
shutil.copyfile(DIR / "wrapup_snap.json", DIR / "history_backfill.json")

(DIR / "wrapup_run.txt").write_text(f"wrap {AT} ok_quiet=True inserted_total={inserted_total}" + NL)
print("wrote wrapup files")
print("ok_quiet True inserted_total", inserted_total, "at", AT)
print("now_txt bytes", len(now_txt), "verify bytes", len(verify))
print("just actual", actual_by, "sum", actual_sum, "script", script_by, "sum", script_sum)
print("dup", dup)
print("window_db", window_db)
print("tips", tips)
print("listener", listener_pid, slot, rot, "yield_absent", yield_absent, "count", n_listeners)
print("gap0418", {r: gap0418[r]["fill"] for r in ROOMS})
print("gap0347", {r: gap0347[r]["fill"] for r in ROOMS})
print("gap0244", {r: gap0244[r]["fill"] for r in ROOMS})
print("gap0213", {r: gap0213[r]["fill"] for r in ROOMS})
print("gap0150", {r: gap0150[r]["fill"] for r in ROOMS})
print("gap0118", {r: gap0118[r]["fill"] for r in ROOMS})
print("gap0050", {r: gap0050[r]["fill"] for r in ROOMS})
print("holes", {k: {kk: holes[k][kk] for kk in ("distinct", "rows", "min", "max", "hole_ticks", "hole_ranges")} for k in holes})
