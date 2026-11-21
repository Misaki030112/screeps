#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
STATE = ROOT / "state"
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-22_0530")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
NL = chr(10)
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

T0, T1 = 84407301, 84408000
JP_BASE = 84408000
JP_T0, JP_T1 = JP_BASE + 1, JP_BASE + 100

GAPS = [
    ("gap_0517_0523", 84407741, 84407849),
    ("gap_0525_0527", 84407871, 84407899),
    ("gap_0441_0459", 84407211, 84407499),
    ("gap_0418_0422", 84406881, 84406949),
    ("gap_0347_0406", 84406431, 84406719),
    ("gap_0244_0303", 84405501, 84405799),
]

HOLES = [
    ("W47N7", 84407900),
    ("W45N8", 84407700),
    ("W46N8", 84407000),
    ("W45N8", 84406400),
    ("W46N8", 84406600),
    ("W46N8", 84406700),
    ("W45N7", 84403800),
    ("W45N7", 84403700),
    ("W45N7", 84400400),
    ("W45N7", 84400300),
    ("W47N8", 84400100),
]


def hole_meta(row):
    d, mn, mx, n = row
    d = int(d or 0)
    n = int(n or 0)
    return {"distinct": d, "rows": n, "min": mn, "max": mx, "hole_ticks": 100 - d}


def hole_ranges(c, room, base, distinct):
    t0, t1 = base + 1, base + 100
    if distinct == 0:
        return [[t0, t1]]
    ticks = [r[0] for r in c.execute(
        "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick",
        (room, t0, t1),
    ).fetchall()]
    s = set(ticks)
    out, start = [], None
    for t in range(t0, t1 + 1):
        if t not in s:
            if start is None:
                start = t
        elif start is not None:
            out.append([start, t - 1])
            start = None
    if start is not None:
        out.append([start, t1])
    return out


def hole_range_txt(h):
    rs = h.get("hole_ranges") or []
    if not rs:
        return "none"
    parts = []
    for a, b in rs:
        parts.append(f"{a}..{b}" if a != b else str(a))
    return " and ".join(parts)


def fill_txt(by_room):
    return ", ".join(f"{r} {by_room[r]['fill']}" for r in ROOMS)


def main():
    now = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    tick = json.loads((DIR / "tick_s_realign.json").read_text())
    cov = json.loads((DIR / "coverage_final.json").read_text())
    jp = json.loads((DIR / "just_published_84408000.json").read_text())
    pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
    late = json.loads((DIR / "backfill_late_retry.json").read_text())
    confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())

    post = {}
    window_db = {}
    dup = {}
    holes = {}
    gaps = {}
    tips = {}
    with db.connect() as c:
        for room in ROOMS:
            d, mn, mx, n = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks "
                "WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, JP_T0, JP_T1),
            ).fetchone()
            post[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
            r, u = c.execute(
                "SELECT count(*), count(DISTINCT (creep, tick)) FROM creep_ticks "
                "WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, JP_T0, JP_T1),
            ).fetchone()
            dup[room] = {"rows": int(r or 0), "unique": int(u or 0), "extra": int(r or 0) - int(u or 0)}
            d2, mn2, mx2, n2 = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks "
                "WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, T0, T1),
            ).fetchone()
            window_db[room] = {"distinct": int(d2 or 0), "rows": int(n2 or 0), "min": mn2, "max": mx2}

        for room, base in HOLES:
            row = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks "
                "WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, base + 1, base + 100),
            ).fetchone()
            h = hole_meta(row)
            h["hole_ranges"] = hole_ranges(c, room, base, h["distinct"])
            holes[f"{room}@{base}"] = h

        for label, a, b in GAPS:
            span = b - a + 1
            by = {}
            for room in ROOMS:
                d, mn, mx, n = c.execute(
                    "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks "
                    "WHERE room=%s AND tick BETWEEN %s AND %s",
                    (room, a, b),
                ).fetchone()
                by[room] = {
                    "fill": f"{int(d or 0)}/{span}",
                    "distinct": int(d or 0), "rows": int(n or 0),
                    "min": mn, "max": mx, "span": span,
                }
            gaps[label] = by

        for table in ("room_stats", "creep_cpu", "path_arrivals"):
            tips[table] = c.execute(f"SELECT max(tick) FROM {table}").fetchone()[0]

    (DIR / "just_published_post_counts.json").write_text(json.dumps(post, indent=2) + NL)
    (DIR / "just_published_dedupe.json").write_text(json.dumps({"window": [JP_T0, JP_T1], "by_room": dup}, indent=2) + NL)

    actual = {}
    for room in ROOMS:
        actual[room] = max(0, dup[room]["unique"] - int((pre.get(room) or {}).get("rows") or 0))
    actual_sum = sum(actual.values())
    script_by = {}
    gets = jp.get("gets") or jp.get("results") or []
    script_sum = int(jp.get("inserted") or 0)
    if gets:
        for g in gets:
            script_by[g["room"]] = int(g.get("inserted") or 0)
        script_sum = sum(script_by.values()) if script_by else script_sum
    else:
        script_by = {r: None for r in ROOMS}

    inserted_first = 2881
    inserted_confirm = int(confirm.get("inserted") or 0)
    inserted_retry2 = int(confirm.get("retry2_inserted") or 0)
    inserted_late = int(late.get("inserted") or 0)
    inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + actual_sum

    out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
    listener_lines = [ln.strip() for ln in out.splitlines() if "tools/listener.py" in ln]
    rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
    yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

    w45n8_84407700 = holes["W45N8@84407700"]
    w47n7_84407900 = holes["W47N7@84407900"]
    w46n8_84407000 = holes["W46N8@84407000"]
    w45n8_84406400 = holes["W45N8@84406400"]
    w46n8_84406600 = holes["W46N8@84406600"]
    w46n8_84406700 = holes["W46N8@84406700"]
    w45n7_84403800 = holes["W45N7@84403800"]
    w45n7_84403700 = holes["W45N7@84403700"]

    fill0517 = fill_txt(gaps["gap_0517_0523"])
    fill0525 = fill_txt(gaps["gap_0525_0527"])
    fill0441 = fill_txt(gaps["gap_0441_0459"])
    fill0418 = fill_txt(gaps["gap_0418_0422"])
    fill0347 = fill_txt(gaps["gap_0347_0406"])
    fill0244 = fill_txt(gaps["gap_0244_0303"])

    tick_s_in_use = tick.get("tick_s_in_use")
    first = tick.get("tick_s_used_first_pass") or 4.03086
    later = tick.get("later_mean_w46") or tick.get("later_mean_robust")
    corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
    tick_s_label = tick.get("tick_s_in_use_source") or "span_mean"

    first_txt = (DIR / "history_backfill.txt").read_text().rstrip() + NL
    confirm_at = confirm.get("confirm_at") or confirm.get("at")
    confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
    retry2_at = confirm.get("retry2_at")
    retry2_gt = confirm.get("retry2_game_time")
    late_at = late.get("at")
    late_gt = late.get("game_time")
    jp_at = "2026-11-22 05:43:43 Asia/Hong_Kong"
    jp_gt = jp.get("game_time") or 84408141

    def script_vs(room):
        s = script_by.get(room)
        a = actual[room]
        return f"{room} script {s} vs actual {a}"

    script_vs_txt = ", ".join(script_vs(r) for r in ROOMS)

    now_txt = (
        "source=this_halfhour_first_pass _halfhour_2026-11-22_0530" + NL
        + first_txt
        + f"---- wrap {now} ----" + NL
        + f"confirm at {confirm_at} gt={confirm_gt} still_404={confirm.get('still_404')} inserted={inserted_confirm}. "
        + f"retry2 at {retry2_at} gt={retry2_gt} still_404={confirm.get('retry2_still_404')} inserted={inserted_retry2}. "
        + f"late retry at {late_at} gt={late_gt} still_404={late.get('still_404')} inserted={inserted_late}. "
        + "First pass 33/35 official GETs 200, missing_chunks=2 W45N8@84407700 and W47N7@84407900; confirm+retry2+late still 404, leftover. "
        + "First pass completed cleanly at 2026-11-22 05:35:41 Asia/Hong_Kong onward (exit=0, no abort). "
        + "Already-told leftover official 404s W46N8@84407000, W45N8@84406400, W46N8@84406600, W46N8@84406700, "
        + "W45N7@84403800, W45N7@84403700, W45N7@84400400, W45N7@84400300, and W47N8@84400100 aged out of window start 84407301 "
        + "and were not retried as new aged leftovers "
        + "(W45N8@84407700 was in this first pass and was retried confirm+retry2+late; W46N8@84407000 was reconfirmed by concurrent "
        + "_patrol_2026-11-22_0522 at 05:32:10 still 404 and was not retried again). "
        + "Just-published 84408000 was not in first pass (first pass ended at published 84407900 / reconstructed 84407301..84408000 at "
        + f"game.time=84408023, 33/35 200 with 2 in-window 404s still leftover). GET at {jp_at} gt={jp_gt} all_five_200=True "
        + f"script={script_sum} actual={actual_sum}; {script_vs_txt}. "
        + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
        + "W47N7 official empty_no_creep in this first-pass window: none (the 100-tick gap 84407901..84408000 is leftover official 404 W47N7@84407900, not empty). "
        + "W45N8 official empty_no_creep in this first-pass window: none (the 100-tick gap 84407701..84407800 is leftover official 404 W45N8@84407700, not empty). "
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=2871 corrective={corrective} "
        + f"(later-mean {later} worse than live-anchor-best {tick_s_label}; first already realigned 2871; live-anchor-best already inside 45s gate, no corrective). "
        + f"NEW leftover official 404 this run: W47N7@84407900 (confirm 05:37:39, retry2 05:37:50, late 05:44:33 still 404; listener {w47n7_84407900['distinct']}/100; hole {w47n7_84407900['hole_ticks']} ticks {hole_range_txt(w47n7_84407900)}) -- not yet told, fold into the next 1h patrol. "
        + f"Already-told leftover official 404 W45N8@84407700 was retried this run and still 404 (confirm 05:37:37, retry2 05:37:49, late 05:44:31 still 404; listener {w45n8_84407700['distinct']}/100; hole {w45n8_84407700['hole_ticks']} ticks {hole_range_txt(w45n8_84407700)}) -- already told in the 05:22 _patrol_2026-11-22_0522 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W46N8@84407000 aged out of window start 84407301 and was not retried this pass (patrol reconfirm 05:32:10 still 404; listener {w46n8_84407000['distinct']}/100 {w46n8_84407000['min']}..{w46n8_84407000['max']}; hole {w46n8_84407000['hole_ticks']} ticks {hole_range_txt(w46n8_84407000)}) -- already told in the 05:22 _patrol_2026-11-22_0522 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404s aged out of window start 84407301 and were not retried: W45N8@84406400 (listener {w45n8_84406400['distinct']}/100; hole {w45n8_84406400['hole_ticks']} ticks {hole_range_txt(w45n8_84406400)}), W46N8@84406600 (listener {w46n8_84406600['distinct']}/100; hole {w46n8_84406600['hole_ticks']} ticks {hole_range_txt(w46n8_84406600)}), W46N8@84406700 (listener {w46n8_84406700['distinct']}/100 {w46n8_84406700['min']}..{w46n8_84406700['max']}; hole {w46n8_84406700['hole_ticks']} ticks {hole_range_txt(w46n8_84406700)}) -- already told in the 04:33 _patrol_2026-11-22_0422 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84403800 aged out of window start 84407301 and was not retried (listener {w45n7_84403800['distinct']}/100 {w45n7_84403800['min']}..{w45n7_84403800['max']}; hole {w45n7_84403800['hole_ticks']} ticks {hole_range_txt(w45n7_84403800)}) -- already told in the finished 01:31 _patrol_2026-11-22_0121 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84403700 aged out of window start 84407301 and was not retried (listener {w45n7_84403700['distinct']}/100; hole {w45n7_84403700['hole_ticks']} ticks {hole_range_txt(w45n7_84403700)}) -- already told in the 01:31 patrol USER_LOG; do not re-tell. "
        + "NEW short WS this run: none. "
        + "NEW box freeze this run: none. "
        + f"_patrol_2026-11-22_0522 USER_LOG (written 05:38) already includes (treat as already told; do not re-tell): "
        + f"盒子休眠 04:41:06-04:59:17 (1086s; STATS 84407211..84407499, 289t; official-filled {fill0441}; listener auto-restart 04:59:20, python 2264003 started 04:59:30); "
        + f"盒子休眠 05:17:11-05:23:17 (361s; STATS 84407741..84407849, 109t; official-filled {fill0517}; W45N8 short because leftover official 404 W45N8@84407700 covers 84407741..84407800; listener auto-restart 05:23:20); "
        + f"监听短中断 05:25:19-05:27:20 (no box_pauses row; STATS 84407871..84407899, 29t; official-filled {fill0525}; listener ws ping/pong 05:26:35, auto-restart 05:26:38, python 2274875 started 05:26:47); "
        + "leftover official 404 W46N8@84407000 / W45N8@84407700. "
        + f"Official fill re-verified this run: 05:17 STATS 84407741..84407849 109t official-filled {fill0517}; 05:25 short WS STATS 84407871..84407899 29t official-filled {fill0525}; 04:41 STATS 84407211..84407499 289t official-filled {fill0441}; 04:18 STATS 84406881..84406949 69t official-filled {fill0418}; 03:47 STATS 84406431..84406719 289t official-filled {fill0347}; 02:44 STATS 84405501..84405799 299t official-filled {fill0244}. "
        + "_patrol_2026-11-22_0422 USER_LOG already includes (treat as already told; do not re-tell): 盒子休眠 03:47:58-04:06:12 and 04:18:46-04:22:28; leftover official 404 W45N8@84406400 / W46N8@84406600 / W46N8@84406700. "
        + "Single listener still 2274875 since 05:26:47, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "
        + f"listener_rot {rot} tips {tips}."
        + NL
    )

    (DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
    (DIR / "history_backfill_now.txt").write_text(now_txt)
    shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

    verify = (
        f"wrap {now}" + NL
        + f"ok_quiet=True inserted_total={inserted_total}" + NL
        + f"first_pass game.time=84408023 published_bases=84407300..84407900 reconstructed=84407301..84408000 (700) "
        + f"33/35 200 missing_chunks=2 W45N8@84407700 W47N7@84407900 inserted_first={inserted_first} already_in_db=24681 ts_realigned_first=2871" + NL
        + "confirm+retry2+late still_404=['W45N8@84407700','W47N7@84407900'] inserted=0" + NL
        + f"just_published 84408000 at {jp_at} gt={jp_gt} all_five_200=True script={script_sum} actual={actual_sum} script_by={script_by} actual_by={actual}" + NL
        + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_applied=False nfix={corrective}" + NL
        + f"window_db={window_db}" + NL
        + f"dup={dup}" + NL
        + f"tips={tips}" + NL
        + f"listener {listener_lines} rot={rot} yield_absent={yield_absent}" + NL
        + f"gaps 0517={ {r: gaps['gap_0517_0523'][r]['fill'] for r in ROOMS} } 0525={ {r: gaps['gap_0525_0527'][r]['fill'] for r in ROOMS} } 0441={ {r: gaps['gap_0441_0459'][r]['fill'] for r in ROOMS} }" + NL
        + f"holes={holes}" + NL
        + "already_told by _patrol_2026-11-22_0522 USER_LOG (do not re-tell): 盒子休眠 04:41:06-04:59:17 and 05:17:11-05:23:17; 监听短中断 05:25:19-05:27:20; leftover official 404 W46N8@84407000 and W45N8@84407700. Older already-told freezes through 04:18 / 03:47 / 02:44 and leftover official 404s through W45N8@84406400 / W46N8@84406600 / W46N8@84406700 and earlier." + NL
        + "ok_quiet=True new_official_404_untold=['W47N7@84407900'] new_box_freeze_untold=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0530" + NL
    )
    (DIR / "verify.txt").write_text(verify)
    (DIR / "_halfhour_backfill_verify.txt").write_text(verify)
    shutil.copyfile(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")

    snap = {
        "at": now,
        "ok_quiet": True,
        "inserted_total": inserted_total,
        "inserted_first": inserted_first,
        "inserted_confirm": inserted_confirm,
        "inserted_retry2": inserted_retry2,
        "inserted_late": inserted_late,
        "just_script": script_sum,
        "just_actual": actual_sum,
        "just_script_by": script_by,
        "just_actual_by": actual,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_label": tick_s_label,
        "window": [T0, T1],
        "window_db": window_db,
        "dup": dup,
        "tips": tips,
        "gaps": {k: {r: v[r]["fill"] for r in ROOMS} for k, v in gaps.items()},
        "holes": holes,
        "new_official_404_untold": ["W47N7@84407900"],
        "new_box_freeze_untold": [],
        "new_short_ws_untold": [],
        "listener": listener_lines,
        "rot": rot,
        "yield_absent": yield_absent,
    }
    (DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + NL)
    (DIR / "wrapup_run.txt").write_text(f"wrap {now} ok_quiet=True inserted_total={inserted_total}{NL}")

    print("listener_ps", " | ".join(listener_lines))
    print("wrote wrapup files")
    print("ok_quiet True inserted_total", inserted_total, "at", now)
    print("now_txt bytes", len(now_txt.encode()), "verify bytes", len(verify.encode()))
    print("just actual", actual, "sum", actual_sum, "script", script_by, "sum", script_sum)
    print("dup", dup)
    print("window_db", window_db)
    print("tips", tips)
    print("listener", listener_lines, "rot", rot, "yield_absent", yield_absent)
    for label in ("gap_0517_0523", "gap_0525_0527", "gap_0441_0459"):
        print(label, {r: gaps[label][r]["fill"] for r in ROOMS})
    print("new hole W47N7@84407900", holes["W47N7@84407900"])
    print("W45N8@84407700", holes["W45N8@84407700"])
    print("W46N8@84407000", holes["W46N8@84407000"])


if __name__ == "__main__":
    main()
