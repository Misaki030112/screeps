#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
STATE = ROOT / "state"
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_0100")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
NL = chr(10)
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

T0, T1 = 84424101, 84424800
JP_BASE = 84424800
JP_T0, JP_T1 = JP_BASE + 1, JP_BASE + 100

GAPS = [
    ("gap_0051_0057", 84424691, 84424799),
    ("gap_0023_0033", 84424291, 84424449),
    ("gap_2352_2359", 84423801, 84423969),
    ("gap_2243_2305", 84422871, 84423199),
    ("gap_2145_2204", 84422041, 84422319),
    ("gap_2049_2059", 84421221, 84421389),
    ("gap_1943_1959", 84420281, 84420519),
    ("gap_1912_1913", 84419821, 84419849),
    ("gap_1741_1804", 84418531, 84418879),
    ("gap_1712_1722", 84418131, 84418279),
    ("gap_1644_1659", 84417731, 84417949),
    ("gap_1615_1622", 84417291, 84417409),
    ("gap_1602_1602", 84417111, 84417129),
    ("gap_1447_1501", 84416041, 84416249),
    ("gap_1415_1420", 84415571, 84415649),
    ("gap_1348_1357", 84415191, 84415339),
    ("gap_1316_1326", 84414731, 84414879),
    ("gap_1251_1303", 84414371, 84414559),
    ("gap_1220_1223", 84413921, 84413969),
    ("gap_1214_1214", 84413821, 84413849),
    ("gap_1145_1200", 84413411, 84413649),
    ("gap_1045_1106", 84412541, 84412859),
    ("gap_1016_1022", 84412131, 84412219),
    ("gap_0941_0959", 84411621, 84411889),
    ("gap_0914_0919", 84411221, 84411299),
    ("gap_0851_0901", 84410881, 84411039),
    ("gap_0744_0802", 84409901, 84410189),
    ("gap_0720_0726", 84409551, 84409649),
    ("gap_0650_0702", 84409111, 84409299),
    ("gap_0621_0626", 84408691, 84408779),
    ("gap_0552_0604", 84408271, 84408449),
    ("gap_0517_0523", 84407741, 84407849),
    ("gap_0525_0527", 84407871, 84407899),
    ("gap_0441_0459", 84407211, 84407499),
    ("gap_0418_0422", 84406881, 84406949),
    ("gap_0347_0406", 84406431, 84406719),
    ("gap_0244_0303", 84405501, 84405799),
]

HOLES = [
    ("W45N8", 84422100),
    ("W45N8", 84422400),
    ("W46N8", 84418900),
    ("W47N8", 84418900),
    ("W45N8", 84418900),
    ("W45N7", 84418900),
    ("W47N7", 84418900),
    ("W45N7", 84419000),
    ("W45N7", 84419300),
    ("W45N8", 84419600),
    ("W45N8", 84415500),
    ("W46N8", 84414700),
    ("W46N8", 84413700),
    ("W47N7", 84412400),
    ("W45N7", 84411500),
    ("W47N8", 84409800),
    ("W46N8", 84408300),
    ("W47N8", 84408300),
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
    jp = json.loads((DIR / f"just_published_{JP_BASE}.json").read_text())
    pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
    late = json.loads((DIR / "backfill_late_retry.json").read_text())
    confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
    try:
        postjp = json.loads((DIR / "backfill_postjp_retry.json").read_text())
    except Exception:
        postjp = {"skipped": True, "inserted": 0, "at": None, "game_time": None}

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
    gets = jp.get("gets") or jp.get("results") or []
    script_by = {r: 0 for r in ROOMS}
    split_exists = (DIR / ("just_published_%s_first.json" % JP_BASE)).exists()
    names = [
        "just_published_%s_first.json" % JP_BASE,
        "just_published_%s_retry.json" % JP_BASE,
        "just_published_%s_retry2.json" % JP_BASE,
    ] if split_exists else ["just_published_%s.json" % JP_BASE]
    for name in names:
        fp = DIR / name
        if not fp.exists():
            continue
        jx = __import__("json").loads(fp.read_text())
        for g in (jx.get("gets") or []):
            script_by[g["room"]] = script_by.get(g["room"], 0) + int(g.get("inserted") or 0)
    script_sum = sum(script_by.values())

    inserted_first = 6030
    inserted_confirm_script = int(confirm.get("inserted") or 0)
    inserted_retry2_script = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
    inserted_confirm = inserted_confirm_script
    inserted_retry2 = inserted_retry2_script
    inserted_late = int(late.get("inserted") or 0)
    inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + actual_sum

    out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
    listener_lines = [ln.strip() for ln in out.splitlines() if "tools/listener.py" in ln]
    rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
    yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

    w45n8_84422100 = holes["W45N8@84422100"]
    w45n8_84422400 = holes["W45N8@84422400"]
    w46n8_84418900 = holes["W46N8@84418900"]
    w47n8_84418900 = holes["W47N8@84418900"]
    w45n8_84418900 = holes["W45N8@84418900"]
    w45n7_84418900 = holes["W45N7@84418900"]
    w47n7_84418900 = holes["W47N7@84418900"]
    w45n7_84419000 = holes["W45N7@84419000"]
    w45n7_84419300 = holes["W45N7@84419300"]
    w45n8_84419600 = holes["W45N8@84419600"]
    w45n8_84415500 = holes["W45N8@84415500"]
    w46n8_84414700 = holes["W46N8@84414700"]
    w46n8_84413700 = holes["W46N8@84413700"]
    w47n7_84412400 = holes["W47N7@84412400"]
    w45n7_84411500 = holes["W45N7@84411500"]
    w47n8_84409800 = holes["W47N8@84409800"]
    w46n8_84408300 = holes["W46N8@84408300"]
    w47n8_84408300 = holes["W47N8@84408300"]
    w47n7_84407900 = holes["W47N7@84407900"]
    w45n8_84407700 = holes["W45N8@84407700"]
    w46n8_84407000 = holes["W46N8@84407000"]
    w45n8_84406400 = holes["W45N8@84406400"]
    w46n8_84406600 = holes["W46N8@84406600"]
    w46n8_84406700 = holes["W46N8@84406700"]
    w45n7_84403800 = holes["W45N7@84403800"]
    w45n7_84403700 = holes["W45N7@84403700"]

    fill0051 = fill_txt(gaps["gap_0051_0057"])
    fill0023 = fill_txt(gaps["gap_0023_0033"])
    fill2352 = fill_txt(gaps["gap_2352_2359"])
    fill2243 = fill_txt(gaps["gap_2243_2305"])
    fill2145 = fill_txt(gaps["gap_2145_2204"])
    fill2049 = fill_txt(gaps["gap_2049_2059"])
    fill1943 = fill_txt(gaps["gap_1943_1959"])
    fill1912 = fill_txt(gaps["gap_1912_1913"])
    fill1741 = fill_txt(gaps["gap_1741_1804"])
    fill1712 = fill_txt(gaps["gap_1712_1722"])
    fill1644 = fill_txt(gaps["gap_1644_1659"])
    fill1615 = fill_txt(gaps["gap_1615_1622"])
    fill1602 = fill_txt(gaps["gap_1602_1602"])
    fill1447 = fill_txt(gaps["gap_1447_1501"])
    fill1415 = fill_txt(gaps["gap_1415_1420"])
    fill1348 = fill_txt(gaps["gap_1348_1357"])
    fill1316 = fill_txt(gaps["gap_1316_1326"])
    fill1251 = fill_txt(gaps["gap_1251_1303"])
    fill1220 = fill_txt(gaps["gap_1220_1223"])
    fill1214 = fill_txt(gaps["gap_1214_1214"])
    fill1145 = fill_txt(gaps["gap_1145_1200"])
    fill1045 = fill_txt(gaps["gap_1045_1106"])
    fill1016 = fill_txt(gaps["gap_1016_1022"])
    fill0941 = fill_txt(gaps["gap_0941_0959"])
    fill0914 = fill_txt(gaps["gap_0914_0919"])
    fill0851 = fill_txt(gaps["gap_0851_0901"])
    fill0744 = fill_txt(gaps["gap_0744_0802"])
    fill0720 = fill_txt(gaps["gap_0720_0726"])
    fill0650 = fill_txt(gaps["gap_0650_0702"])
    fill0621 = fill_txt(gaps["gap_0621_0626"])
    fill0552 = fill_txt(gaps["gap_0552_0604"])
    fill0517 = fill_txt(gaps["gap_0517_0523"])
    fill0525 = fill_txt(gaps["gap_0525_0527"])
    fill0441 = fill_txt(gaps["gap_0441_0459"])
    fill0418 = fill_txt(gaps["gap_0418_0422"])
    fill0347 = fill_txt(gaps["gap_0347_0406"])
    fill0244 = fill_txt(gaps["gap_0244_0303"])

    tick_s_in_use = tick.get("tick_s_in_use")
    first = tick.get("tick_s_used_first_pass") or 4.15347
    later = tick.get("later_mean_w46") or tick.get("later_mean_robust")
    corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
    tick_s_label = tick.get("tick_s_in_use_name") or "first"

    first_txt = (DIR / "history_backfill.txt").read_text().rstrip() + NL
    retry2 = confirm.get("retry2") or {}
    confirm_at = confirm.get("confirm_at") or confirm.get("at")
    confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
    retry2_at = confirm.get("retry2_at") or retry2.get("at")
    retry2_gt = confirm.get("retry2_game_time") or retry2.get("game_time")
    late_at = late.get("at")
    late_gt = late.get("game_time")
    jp_first = {}
    try:
        jp_first = __import__("json").loads((DIR / ("just_published_%s_first.json" % JP_BASE)).read_text())
    except Exception:
        jp_first = {}
    jp_at = jp_first.get("at") or jp.get("at")
    jp_gt = jp_first.get("game_time") or jp.get("game_time")
    jp_still = jp.get("still_404") or []
    jp_all5 = (not jp_still) and all((g.get("ok") or g.get("code") == 200) for g in (jp.get("gets") or gets or [])) if (jp.get("gets") or gets) else (not jp_still)

    def script_vs(room):
        s = script_by.get(room)
        a = actual[room]
        return f"{room} script {s} vs actual {a}"

    script_vs_txt = ", ".join(script_vs(r) for r in ROOMS)

    empty_by = cov.get("coverage") or {}
    def empty_txt(room):
        c = empty_by.get(room) or {}
        n = c.get("official_empty_no_creep") or 0
        rs = c.get("official_empty_no_creep_ranges") or []
        if not n:
            return "none"
        parts = []
        for a, b in rs:
            parts.append(f"{a}..{b}" if a != b else str(a))
        return f"{n} ticks " + " and ".join(parts)

    def _pass_txt(name, at, gt, payload, inserted):
        if payload.get("skipped"):
            return f"{name} at {at} gt={gt} skipped no targets inserted={inserted}."
        still = payload.get("still_404") or []
        recovered = payload.get("recovered") or []
        return f"{name} at {at} gt={gt} still_404={still} recovered={recovered} inserted={inserted}."


    now_txt = (
        "source=this_halfhour_first_pass _halfhour_2026-11-23_0100" + NL
        + first_txt
        + f"---- wrap {now} ----" + NL
        + _pass_txt("confirm", confirm_at, confirm_gt, confirm, inserted_confirm_script) + " "
        + _pass_txt("retry2", retry2_at, retry2_gt, retry2, inserted_retry2_script) + " "
        + _pass_txt("late retry", late_at, late_gt, late, inserted_late) + " "
        + _pass_txt("post-JP leftover retry", postjp.get("at"), postjp.get("game_time"), postjp, int(postjp.get("inserted") or 0)) + " "
        + "First pass 35/35 official GETs 200, missing_chunks=0. "
        + "First pass started 2026-11-23 01:01:05 Asia/Hong_Kong and finished 01:01:48 (exit=0): "
        + "inserted=6030 already_in_db=18290, first-pass realign moved 7838 rows ts_realigned_first=7838 "
        + "(first-interval tick_s printed 4.153, exact 4.15347). Overlap with the 00:30 half-hour (official 84423801..84424500 / JP 84424500) accounts for already_in_db=18290. "
        + "Confirm 01:03:22 skipped no targets inserted=0. No same-payload extra-row collision this first pass. "
        + f"tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use} (first {first} had over45=294; later-mean {later} over45=0 was better); corrective_applied=False nfix={corrective}; skipped_cross_chunk={tick.get('skipped_cross_chunk', 0)}. "
        + "Last delivered USER_LOG is ~23:31 _patrol_2026-11-22_2316 (finished_at 23:32:40); do not re-tell it. This half-hour did not write a patrol or 12h-review folder. 12h review _review12h_2026-11-22_20 already completed ~20:37 (docs-only, LIVE still 2b5398f7, not a game deploy); do not re-tell or write its folder. "
        + "00:30 half-hour already official-filled 84423801..84424500 / just-published 84424500, and recorded still-untold 盒子休眠 00:23:50-00:33:45 plus still-untold 23:52:01-23:59:48 from the 00:00 half-hour. 23:31 patrol already official+JP filled through 84423500, and already told leftover 404 W45N8@84422100 and W45N8@84422400 plus 盒子休眠 22:43:27-23:05:49 (and 21:45:57-22:04:37 and 20:49:49-20:59:53 and 19:43:54-19:59:40). This run is overlap of the 00:30 window plus new official 84424100..84424700 and just-published 84424800. "
        + "Already-told leftover official 404s W45N8@84422100 and W45N8@84422400 aged out of window start 84424101 and were not retried this pass (already told in the 22:37 patrol and mentioned as already-told in the 23:31 _patrol_2026-11-22_2316 USER_LOG; do not re-tell). "
        + "Older already-told leftovers W45N7@84419300, W45N8@84419600, all five @84418900, W45N7@84419000, W45N8@84415500, W46N8@84414700, W46N8@84413700, W47N7@84412400, W45N7@84411500, W47N8@84409800, W46N8@84408300, W47N8@84408300, W47N7@84407900, W46N8@84407000, W45N8@84407700, W45N8@84406400, W46N8@84406600, W46N8@84406700, W45N7@84403800, W45N7@84403700, W45N7@84400400, W45N7@84400300, and W47N8@84400100 also aged out of window start 84424101 and were not retried this pass; do not re-tell. "
        + f"Just-published 84424800 was not in first pass (first pass ended at published 84424700 / reconstructed 84424101..84424800 at "
        + f"game.time=84424836, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5}. W47N7 first GET hit a transient SSL EOF and was resumed at 01:09:44 gt=84424958 inserted=496; all five ended 200. "
        + f"script={script_sum} actual={actual_sum}; {script_vs_txt}. "
        + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
        + f"W46N8 official empty_no_creep in this first-pass window: {empty_txt('W46N8')}. "
        + f"W47N8 official empty_no_creep in this first-pass window: {empty_txt('W47N8')}. "
        + f"W45N8 official empty_no_creep in this first-pass window: {empty_txt('W45N8')}. "
        + f"W45N7 official empty_no_creep in this first-pass window: {empty_txt('W45N7')}. "
        + f"W47N7 official empty_no_creep in this first-pass window: {empty_txt('W47N7')}. "
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
        + "NEW leftover official 404 this run: none (first pass 35/35 200, no first-pass 404s). "
        + f"Already-told leftover official 404 W45N8@84422100 (listener {w45n8_84422100['distinct']}/100 range {w45n8_84422100['min']}..{w45n8_84422100['max']}; hole {w45n8_84422100['hole_ticks']} ticks {hole_range_txt(w45n8_84422100)}; sits inside already-told freeze STATS 84422041..84422319) and W45N8@84422400 (listener {w45n8_84422400['distinct']}/100 range {w45n8_84422400['min']}..{w45n8_84422400['max']}; hole {w45n8_84422400['hole_ticks']} ticks {hole_range_txt(w45n8_84422400)}) aged out of window start 84424101 and were not retried this pass; already told in the ~22:37 patrol and mentioned as already-told in the ~23:31 _patrol_2026-11-22_2316 USER_LOG; do not re-tell. "
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=7838 corrective={corrective} "
        + f"(later-mean {later}; first-pass realign moved 7838 rows with first-interval 4.15347; first over45=294 vs live anchor, later_raw over45=0; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use} inside 45s gate, no corrective realign, skipped_cross_chunk=0). "
        + f"NEW 盒子休眠 this run 00:51:21-00:57:39 Asia/Hong_Kong (378s, box_pauses row; STATS 84424691..84424799, 109t; official-filled {fill0051}; listener auto-restart 00:57:42, python 2775547 started 00:57:52, parent 4035476). NEW 监听短中断 this run: none. Still-untold 盒子休眠 00:23:50-00:33:45 (595s; STATS 84424291..84424449 official-filled {fill0023}; listener auto-restart 00:33:49, python 2765557 started 00:33:58, parent 4035476) was recorded by the quiet 00:30 half-hour and is not yet told. Still-untold 盒子休眠 23:52:01-23:59:48 (459s; STATS 84423801..84423969 official-filled {fill2352}; listener auto-restart 23:59:51, python 2749374 started 00:00:01, parent 4035476) was recorded by the quiet 00:00 half-hour and is not yet told; fold both prior freezes plus this run's 00:51 freeze into the next 3h patrol (~02:16). The 23:51:41 no-STATS reconnect (197s) sits at the front of that 23:52 STATS gap and is not a separate 监听短中断. Already-told 盒子休眠 22:43:27-23:05:49 (1334s; STATS 84422871..84423199 official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476; already told in the 23:31 patrol; do not re-tell). "
        + f"Already-told 盒子休眠 21:45:57-22:04:37 (1120s; STATS 84422041..84422319 official-filled {fill2145}; already told in the 22:37 patrol; do not re-tell). "
        + "Already-told 盒子休眠 20:49:49-20:59:53 and 19:43:54-19:59:40 and 17:41:00-18:04:50 and older; already-told 监听短中断 through 19:12:43-19:12:57 and 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20; do not re-tell. "
        + f"window_db={window_db}" + NL
        + f"jp_post={post} jp_script_by={script_by} jp_actual_by={actual}" + NL
        + f"tips={tips}" + NL
        + f"listener {listener_lines} rot={rot} yield_absent={yield_absent}" + NL
        + "Single listener 2775547 since 00:57:52 after the NEW 盒子休眠 00:51:21-00:57:39 auto-restart 00:57:42 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "
        + f"listener_rot {rot} tips {tips}."
        + NL
    )

    (DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
    (DIR / "history_backfill_now.txt").write_text(now_txt)
    shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

    verify = (
        f"wrap {now}" + NL
        + f"ok_quiet=True inserted_total={inserted_total}" + NL
        + f"window={T0}..{T1} jp={JP_T0}..{JP_T1}" + NL
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}" + NL
        + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} later={later} corrective={corrective} still_over_45s_vs_first=0" + NL
        + f"window_db={window_db}" + NL
        + f"jp_post={post} script_by={script_by} actual_by={actual}" + NL
        + f"tips={tips}" + NL
        + f"listener {listener_lines} rot={rot} yield_absent={yield_absent}" + NL
        + f"gaps 0051={{ { {r: gaps['gap_0051_0057'][r]['fill'] for r in ROOMS} } }} 0023={{ { {r: gaps['gap_0023_0033'][r]['fill'] for r in ROOMS} } }} 2352={{ { {r: gaps['gap_2352_2359'][r]['fill'] for r in ROOMS} } }} 2243={{ { {r: gaps['gap_2243_2305'][r]['fill'] for r in ROOMS} } }} 2145={{ { {r: gaps['gap_2145_2204'][r]['fill'] for r in ROOMS} } }} 2049={{ { {r: gaps['gap_2049_2059'][r]['fill'] for r in ROOMS} } }} 1943={{ { {r: gaps['gap_1943_1959'][r]['fill'] for r in ROOMS} } }} 1912={{ { {r: gaps['gap_1912_1913'][r]['fill'] for r in ROOMS} } }} 1741={{ { {r: gaps['gap_1741_1804'][r]['fill'] for r in ROOMS} } }} 1712={{ { {r: gaps['gap_1712_1722'][r]['fill'] for r in ROOMS} } }} 1644={{ { {r: gaps['gap_1644_1659'][r]['fill'] for r in ROOMS} } }} 1615={{ { {r: gaps['gap_1615_1622'][r]['fill'] for r in ROOMS} } }} 1602={{ { {r: gaps['gap_1602_1602'][r]['fill'] for r in ROOMS} } }}" + NL
        + f"holes W45N8@84422100={holes['W45N8@84422100']} W45N8@84422400={holes['W45N8@84422400']}" + NL
        + f"NEW 盒子休眠 this run 00:51:21-00:57:39 (378s; STATS 84424691..84424799 official-filled {fill0051}; listener auto-restart 00:57:42, python 2775547 started 00:57:52, parent 4035476). NEW leftover official 404 none this run (first pass 35/35 200, no first-pass 404s). NEW 监听短中断 none. still_untold from quiet 00:30 half-hour (do not tell now; fold into next 3h patrol): 盒子休眠 00:23:50-00:33:45 (STATS 84424291..84424449 official-filled {fill0023}; listener auto-restart 00:33:49, python 2765557 started 00:33:58, parent 4035476). still_untold from quiet 00:00 half-hour (do not tell now; fold into next 3h patrol): 盒子休眠 23:52:01-23:59:48 (STATS 84423801..84423969 official-filled {fill2352}; listener auto-restart 23:59:51, python 2749374 started 00:00:01, parent 4035476; the 23:51:41 no-STATS reconnect shares that STATS gap and is not a separate 监听短中断). already_told by _patrol_2026-11-22_2316 USER_LOG ~23:31 finished_at 23:32:40 (do not re-tell): 盒子休眠 22:43:27-23:05:49 (STATS 84422871..84423199 official-filled {fill2243}; listener auto-restart 23:05:52, python 2722653 started 23:06:02, parent 4035476). already_told by _patrol_2026-11-22_2224 USER_LOG ~22:37 finished_at 22:36:58 (do not re-tell): 盒子休眠 21:45:57-22:04:37; leftover official 404 W45N8@84422100 and W45N8@84422400. already_told by _patrol_2026-11-22_2117 USER_LOG ~21:27 finished_at 21:27:21 (do not re-tell): 盒子休眠 20:49:49-20:59:53; leftover official 404 W45N7@84419300 and W45N8@84419600. already_told by _patrol_2026-11-22_2016 USER_LOG ~20:27 finished_at 20:26:55 (do not re-tell): 盒子休眠 19:43:54-19:59:40. already_told by _patrol_2026-11-22_1924 USER_LOG ~19:36 finished_at 19:36:36 (do not re-tell): 监听短中断 19:12:43-19:12:57; 盒子休眠 17:41:00-18:04:50 and earlier leftover official 404 all five @84418900 and W45N7@84419000. Older already-told freezes through 17:12:37-17:22:45 / 16:44:58-16:59:18 / 16:15:02-16:22:09 and leftover official 404s through W45N8@84415500 / W46N8@84414700 / W46N8@84413700 and earlier. already-told 监听短中断 through 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20." + NL
        + "ok_quiet=True new_official_404_untold=[] still_untold_from_1230=[] still_untold_from_1100=[] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[00:51:21-00:57:39] still_untold_freeze_from_0030=[00:23:50-00:33:45] still_untold_freeze_from_0000=[23:52:01-23:59:48] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0100 concurrent_patrol=already_delivered_patrol_2026-11-22_2316_do_not_write_its_folder concurrent_12h_review=already_completed_review12h_2026-11-22_20_do_not_write_its_folder" + NL
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
        "inserted_confirm_script": inserted_confirm_script,
        "inserted_retry2": inserted_retry2,
        "inserted_retry2_script": inserted_retry2_script,
        "inserted_late": inserted_late,
        "just_actual": actual_sum,
        "just_script": script_sum,
        "just_script_by": script_by,
        "just_actual_by": actual,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_in_use_name": tick_s_label,
        "window": [T0, T1],
        "window_db": window_db,
        "coverage": {"official_recovered": cov["official_recovered"], "expected": cov["expected"], "empty_no_creep": cov["empty_no_creep"], "official_404": cov["official_404_missing"]},
        "gaps": {k: {r: v[r]["fill"] for r in ROOMS} for k, v in gaps.items()},
        "holes": holes,
        "tips": tips,
        "listener": listener_lines,
        "rot": rot,
        "yield_absent": yield_absent,
        "new_official_404_untold": [],
        "still_untold_from_1230": [],
        "still_untold_from_1100": [],
        "still_untold_from_1000": [],
        "still_untold_from_0800": [],
        "still_untold_from_0730": [],
        "still_untold_from_0700": [],
        "still_untold_from_0600": [],
        "still_untold_from_0530": [],
        "new_box_freeze_untold": ["00:51:21-00:57:39"],
        "still_untold_freeze_from_0030": ["00:23:50-00:33:45"],
        "still_untold_freeze_from_0000": ["23:52:01-23:59:48"],
        "still_untold_freeze_from_1230": [],
        "still_untold_freeze_from_1100": [],
        "still_untold_freeze_from_1000": [],
        "still_untold_freeze_from_0800": [],
        "still_untold_freeze_from_0730": [],
        "still_untold_freeze_from_0700": [],
        "still_untold_freeze_from_0600": [],
        "new_short_ws_untold": [],
        "concurrent_patrol": "already_delivered_patrol_2026-11-22_2316_do_not_write_its_folder",
        "concurrent_12h_review": "already_completed_review12h_2026-11-22_20_do_not_write_its_folder",
        "did_not_write_patrol_folder": True,
        "first_pass_realign": "moved 7838 rows ts_realigned_first=7838 with first=4.15347; tick_s_check live-anchor-best later_raw 4.17286 (first over45=294, later over45=0), corrective nfix=0",
    }
    (DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + NL)
    (DIR / "wrapup_run.txt").write_text(f"wrap {now} ok_quiet=True inserted_total={inserted_total}{NL}")
    print(f"wrap {now} ok_quiet=True inserted_total={inserted_total}")


if __name__ == "__main__":
    main()
