#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
STATE = ROOT / "state"
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-22_1930")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
NL = chr(10)
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

T0, T1 = 84419001, 84419700
JP_BASE = 84419700
JP_T0, JP_T1 = JP_BASE + 1, JP_BASE + 100

GAPS = [
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

    inserted_first = 8347
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
    first = tick.get("tick_s_used_first_pass") or 4.1928
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
        "source=this_halfhour_first_pass _halfhour_2026-11-22_1930" + NL
        + first_txt
        + f"---- wrap {now} ----" + NL
        + _pass_txt("confirm", confirm_at, confirm_gt, confirm, inserted_confirm_script) + " "
        + _pass_txt("retry2", retry2_at, retry2_gt, retry2, inserted_retry2_script) + " "
        + _pass_txt("late retry", late_at, late_gt, late, inserted_late) + " "
        + "post-JP leftover retry at 2026-11-22 19:15:02 Asia/Hong_Kong gt=84419875 still_404=['W45N7@84419000', 'W45N7@84419300', 'W45N8@84419600'] recovered=[] inserted=0. "
        + "First pass 32/35 official GETs 200, missing_chunks=3 (W45N7@84419000, W45N7@84419300, W45N8@84419600). "
        + "First pass started 2026-11-22 19:06:32 Asia/Hong_Kong and finished 19:07:14 (exit=0): "
        + "inserted=8347 already_in_db=16465, first-pass realign moved 0 rows ts_realigned_first=0 "
        + "(first-interval tick_s printed 4.193, exact 4.1928). "
        + "No same-payload extra-row collision this first pass. "
        + f"tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use} (later-mean {later}; first {first}); corrective={corrective}; still_over_45s_vs_first={tick.get('still_over_45s_vs_first')} skipped_cross_chunk={tick.get('skipped_cross_chunk', 0)}. "
        + "Last delivered USER_LOG is ~18:38 _patrol_2026-11-22_1822 (finished_at 18:39:45, state-only ed18e0cb); do not re-tell it or write a patrol folder. 12h review already delivered ~08:33; do not re-tell or write its folder. "
        + "18:30 half-hour already official-filled through 84419200 / just-published 84419300 (W45N7@84419300 still 404); 18:38 patrol already official-filled and told leftover 404 all five @84418900 and W45N7@84419000; this run is overlap of those windows plus new official 84419300..84419600 and just-published 84419700. "
        + "Already-told leftover official 404s all five @84418900 (aged out of window start 84419001, not retried this pass), plus W45N8@84415500, W46N8@84414700, W46N8@84413700, W47N7@84412400, W45N7@84411500, W47N8@84409800, W46N8@84408300, W47N8@84408300, W47N7@84407900, W46N8@84407000, W45N8@84407700, W45N8@84406400, W46N8@84406600, W46N8@84406700, "
        + "W45N7@84403800, W45N7@84403700, W45N7@84400400, W45N7@84400300, and W47N8@84400100 also aged out of window start 84419001 "
        + "and were not retried this pass (already told in the 18:38 _patrol_2026-11-22_1822, 14:28 _patrol_2026-11-22_1419, 13:39 _patrol_2026-11-22_1325, or earlier USER_LOG; do not re-tell). "
        + f"Just-published 84419700 was not in first pass (first pass ended at published 84419600 / reconstructed 84419001..84419700 at "
        + f"game.time=84419755, 32/35 200, missing_chunks=3). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} (first +140 at 19:13:23 gt=84419851 recovered all five rooms; no +200/+300 retry needed). "
        + f"script={script_sum} actual={actual_sum}; {script_vs_txt}. "
        + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
        + f"W46N8 official empty_no_creep in this first-pass window: {empty_txt('W46N8')}. "
        + f"W47N8 official empty_no_creep in this first-pass window: {empty_txt('W47N8')}. "
        + f"W45N8 official empty_no_creep in this first-pass window: {empty_txt('W45N8')}. "
        + f"W45N7 official empty_no_creep in this first-pass window: {empty_txt('W45N7')}. "
        + f"W47N7 official empty_no_creep in this first-pass window: {empty_txt('W47N7')}. "
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=0 corrective={corrective} "
        + f"(later-mean {later}; first-pass realign moved 0 rows ts_realigned_first=0; tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use}; no corrective realign, still_over_45s_vs_first={tick.get('still_over_45s_vs_first')}, skipped_cross_chunk=0). "
        + f"Leftover official 404 all five rooms @84418900 already told in the ~18:38 _patrol_2026-11-22_1822 USER_LOG (finished_at 18:39:45); they aged out of window start 84419001 and were not retried this pass. "
        + f"Listener W46N8 {w46n8_84418900['distinct']}/100 range {w46n8_84418900['min']}..{w46n8_84418900['max']}; hole {w46n8_84418900['hole_ticks']} ticks {hole_range_txt(w46n8_84418900)}. W47N8 {w47n8_84418900['distinct']}/100 range {w47n8_84418900['min']}..{w47n8_84418900['max']}; hole {w47n8_84418900['hole_ticks']} ticks {hole_range_txt(w47n8_84418900)}. W45N8 {w45n8_84418900['distinct']}/100 range {w45n8_84418900['min']}..{w45n8_84418900['max']}; hole {w45n8_84418900['hole_ticks']} ticks {hole_range_txt(w45n8_84418900)}. W45N7 {w45n7_84418900['distinct']}/100 range {w45n7_84418900['min']}..{w45n7_84418900['max']}; hole {w45n7_84418900['hole_ticks']} ticks {hole_range_txt(w45n7_84418900)}. W47N7 {w47n7_84418900['distinct']}/100 range {w47n7_84418900['min']}..{w47n7_84418900['max']}; hole {w47n7_84418900['hole_ticks']} ticks {hole_range_txt(w47n7_84418900)}. "
        + f"Already-told leftover official 404 W45N7@84419000 (already told in that 18:38 patrol; this overlap retried it at confirm 19:08:26 gt=84419782, retry2 19:09:03 gt=84419790, late 19:09:19 gt=84419794, and post-JP 19:15:02 gt=84419875, all still 404, inserted=0; listener {w45n7_84419000['distinct']}/100 range {w45n7_84419000['min']}..{w45n7_84419000['max']}; hole {w45n7_84419000['hole_ticks']} ticks {hole_range_txt(w45n7_84419000)}). Do not re-tell. "
        + f"NEW leftover official 404 this run, NOT YET TOLD: W45N7@84419300 (first appeared as just-published 404 in the quiet 18:30 half-hour after the 18:38 patrol; this overlap retried it, still 404 after confirm/retry2/late/post-JP; later official chunks 84419400/84419500/84419700 already 200 including W45N7@84419700, so this is a leftover official-history hole; listener {w45n7_84419300['distinct']}/100 range {w45n7_84419300['min']}..{w45n7_84419300['max']}; hole {w45n7_84419300['hole_ticks']} ticks {hole_range_txt(w45n7_84419300)}) and W45N8@84419600 (first-pass 404; other rooms 200; later just-published 84419700 already 200 for W45N8, so leftover hole not unpublished-latest lag; confirm/retry2/late/post-JP still 404, inserted=0; listener {w45n8_84419600['distinct']}/100 range {w45n8_84419600['min']}..{w45n8_84419600['max']}; hole {w45n8_84419600['hole_ticks']} ticks {hole_range_txt(w45n8_84419600)}). Fold into the next 1h patrol (the next 30-min overlap should retry these leftovers). "
        + f"Already-told leftover official 404 W45N8@84415500 aged out of window start 84419001 and was not retried this pass (listener {w45n8_84415500['distinct']}/100 range {w45n8_84415500['min']}..{w45n8_84415500['max']}; hole {w45n8_84415500['hole_ticks']} ticks {hole_range_txt(w45n8_84415500)}) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG (16:32 patrol also recorded the age-out); do not re-tell. Already-told leftover official 404 W46N8@84414700 aged out of window start 84419001 and was not retried this pass (listener {w46n8_84414700['distinct']}/100 range {w46n8_84414700['min']}..{w46n8_84414700['max']}; hole {w46n8_84414700['hole_ticks']} ticks {hole_range_txt(w46n8_84414700)}) -- already told in the ~13:39 _patrol_2026-11-22_1325 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W46N8@84413700 aged out of window start 84419001 and was not retried this pass (listener {w46n8_84413700['distinct']}/100 range {w46n8_84413700['min']}..{w46n8_84413700['max']}; hole {w46n8_84413700['hole_ticks']} ticks {hole_range_txt(w46n8_84413700)}) -- already told in the 12:33 _patrol_2026-11-22_1222 t508s3627 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W47N7@84412400 aged out of window start 84419001 and was not retried this pass (listener {w47n7_84412400['distinct']}/100 range {w47n7_84412400['min']}..{w47n7_84412400['max']}; hole {w47n7_84412400['hole_ticks']} ticks {hole_range_txt(w47n7_84412400)}) -- already told in the 11:28 _patrol_2026-11-22_1117 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84411500 aged out of window start 84419001 and was not retried this pass (listener {w45n7_84411500['distinct']}/100 range {w45n7_84411500['min']}..{w45n7_84411500['max']}; hole {w45n7_84411500['hole_ticks']} ticks {hole_range_txt(w45n7_84411500)}) -- already told in the 10:37 _patrol_2026-11-22_1022 t508s3620 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W47N8@84409800 aged out of window start 84419001 and was not retried this pass (listener {w47n8_84409800['distinct']}/100 range {w47n8_84409800['min']}..{w47n8_84409800['max']}; hole {w47n8_84409800['hole_ticks']} ticks {hole_range_txt(w47n8_84409800)}) -- already told in the 08:28 _patrol_2026-11-22_0818 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W46N8@84408300 aged out of window start 84419001 and was not retried this pass (listener {w46n8_84408300['distinct']}/100; hole {w46n8_84408300['hole_ticks']} ticks {hole_range_txt(w46n8_84408300)}) -- already told in the 06:44 _patrol_2026-11-22_0625 t508s3614 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W47N8@84408300 aged out of window start 84419001 and was not retried this pass (listener {w47n8_84408300['distinct']}/100; hole {w47n8_84408300['hole_ticks']} ticks {hole_range_txt(w47n8_84408300)}) -- already told in the 06:44 patrol t508s3614 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W47N7@84407900 aged out of window start 84419001 and was not retried this pass (listener {w47n7_84407900['distinct']}/100; hole {w47n7_84407900['hole_ticks']} ticks {hole_range_txt(w47n7_84407900)}) -- already told in the 06:44 patrol t508s3614 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84407700 aged out of window start 84419001 and was not retried this pass (listener {w45n8_84407700['distinct']}/100; hole {w45n8_84407700['hole_ticks']} ticks {hole_range_txt(w45n8_84407700)}) -- already told in the 05:38 _patrol_2026-11-22_0522 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W46N8@84407000 aged out of window start 84419001 and was not retried this pass (listener {w46n8_84407000['distinct']}/100; hole {w46n8_84407000['hole_ticks']} ticks {hole_range_txt(w46n8_84407000)}) -- already told in the 05:38 _patrol_2026-11-22_0522 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404s aged out of window start 84419001 and were not retried: W45N8@84406400 (listener {w45n8_84406400['distinct']}/100; hole {w45n8_84406400['hole_ticks']} ticks {hole_range_txt(w45n8_84406400)}), W46N8@84406600 (listener {w46n8_84406600['distinct']}/100; hole {w46n8_84406600['hole_ticks']} ticks {hole_range_txt(w46n8_84406600)}), W46N8@84406700 (listener {w46n8_84406700['distinct']}/100; hole {w46n8_84406700['hole_ticks']} ticks {hole_range_txt(w46n8_84406700)}) -- already told in the 04:33 _patrol_2026-11-22_0422 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84403800 aged out of window start 84419001 and was not retried (listener {w45n7_84403800['distinct']}/100; hole {w45n7_84403800['hole_ticks']} ticks {hole_range_txt(w45n7_84403800)}) -- already told in the 01:31 _patrol_2026-11-22_0121 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84403700 aged out of window start 84419001 and was not retried (listener {w45n7_84403700['distinct']}/100; hole {w45n7_84403700['hole_ticks']} ticks {hole_range_txt(w45n7_84403700)}) -- already told in the 01:31 patrol USER_LOG; do not re-tell. "
        + f"NEW 盒子休眠 this run: none. NEW 监听短中断 this run: 监听短中断 19:12:43-19:12:57 (WS ping/pong timed out, no box_pauses row; STATS 84419821..84419849, 29t; official-filled {fill1912}; official 84419800 not yet published; listener auto-restart 19:12:48, python 2621093 started 19:12:57, parent 4035476) -- NOT YET TOLD; fold into the next 1h patrol. 盒子休眠 17:41:00-18:04:50 (1424s; STATS 84418531..84418879, 349t; official-filled {fill1741}; listener auto-restart 18:04:53, python 2582266 started 18:05:03, parent 4035476) -- already told in the ~18:38 _patrol_2026-11-22_1822 USER_LOG; do not re-tell. 盒子休眠 17:12:37-17:22:45 (601s; STATS 84418131..84418279, 149t; official-filled {fill1712}; listener auto-restart 17:22:48, python 2569929 started 17:22:57, parent 4035476) -- already told in the ~17:35 _patrol_2026-11-22_1722 USER_LOG; do not re-tell. 盒子休眠 16:44:58-16:59:18 (850s; STATS 84417731..84417949, 219t; official-filled {fill1644}; listener auto-restart 16:59:21, python 2562267 started 16:59:30, parent 4035476) -- already told in the ~17:35 _patrol_2026-11-22_1722 USER_LOG; do not re-tell. 盒子休眠 16:15:02-16:22:09 (423s; STATS 84417291..84417409, 119t; official-filled {fill1615}; listener auto-restart 16:22:13, python 2548139 started 16:22:22, parent 4035476) -- already told in the ~16:32 _patrol_2026-11-22_1621 USER_LOG; do not re-tell. 监听短中断 16:02:42-16:02:55 (WS ping/pong timed out, no box_pauses row; STATS 84417111..84417129, 19t; official-filled {fill1602}; listener auto-restart 16:02:46, python 2540965 started 16:02:55) -- already told in the ~16:32 _patrol_2026-11-22_1621 USER_LOG; do not re-tell. 盒子休眠 14:47:50-15:01:16 (797s; STATS 84416041..84416249, 209t; official-filled {fill1447}; listener auto-restart 15:01:19, python 2507398 started 15:01:28) -- already told in the ~15:32 _patrol_2026-11-22_1521 USER_LOG; do not re-tell. 盒子休眠 14:15:32-14:20:01 (269s; STATS 84415571..84415649, 79t; official-filled {fill1415}; listener auto-restart 14:20:04, python 2490792 started 14:20:14) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. 盒子休眠 13:48:49-13:57:59 (544s; STATS 84415191..84415339, 149t; official-filled {fill1348}; listener auto-restart 13:58:02, python 2481423 started 13:58:12) -- already told in the ~14:28 _patrol_2026-11-22_1419 USER_LOG; do not re-tell. "
        + f"盒子休眠 13:16:57-13:26:20 (563s; STATS 84414731..84414879, 149t; official-filled {fill1316}; listener auto-restart 13:26:23, python 2466379 started 13:26:32) -- already told in the ~13:39 _patrol_2026-11-22_1325 USER_LOG; do not re-tell. "
        + f"盒子休眠 12:51:44-13:03:45 (715s; STATS 84414371..84414559, 189t; official-filled {fill1251}; listener auto-restart 13:03:48, python 2459147 started 13:03:58) -- already told in the ~13:39 _patrol_2026-11-22_1325 USER_LOG; do not re-tell. "
        + f"盒子休眠 12:20:45-12:23:11 (139s; STATS 84413921..84413969, 49t; official-filled {fill1220}; listener auto-restart 12:23:14, python 2442173 started 12:23:23) -- already told in the 12:33 _patrol_2026-11-22_1222 t508s3627 USER_LOG; do not re-tell. "
        + f"监听短中断 12:14:21-12:14:56 (STATS 84413821..84413849, 29t; official-filled {fill1214}; listener auto-restart 12:14:44) -- already told in the 12:33 _patrol_2026-11-22_1222 t508s3627 USER_LOG; do not re-tell. "
        + f"盒子休眠 11:45:08-12:00:47 (931s; STATS 84413411..84413649, 239t; official-filled {fill1145}; listener auto-restart 12:00:50, python 2431743 started 12:00:59) -- already told in the 12:33 _patrol_2026-11-22_1222 t508s3627 USER_LOG; do not re-tell. "
        + f"盒子休眠 10:45:15-11:06:19 (1264s; STATS 84412541..84412859, 319t; official-filled {fill1045}; listener auto-restart 11:06:22, python 2409363 started 11:06:32) -- already told in the 11:28 _patrol_2026-11-22_1117 USER_LOG; do not re-tell. "
        + f"盒子休眠 10:16:39-10:22:23 (338s; STATS 84412131..84412219, 89t; official-filled {fill1016}; listener auto-restart 10:22:26, python 2394456 started 10:22:36) -- already told in the 10:37 _patrol_2026-11-22_1022 t508s3620 USER_LOG; do not re-tell. "
        + f"盒子休眠 09:41:41-09:59:05 (1037s; STATS 84411621..84411889, 269t; official-filled {fill0941}; listener auto-restart 09:59:08, python 2385251 started 09:59:17) -- already told in the 10:37 _patrol_2026-11-22_1022 t508s3620 USER_LOG; do not re-tell. "
        + f"盒子休眠 09:14:15-09:19:05 (283s; STATS 84411221..84411299, 79t; official-filled {fill0914}; listener auto-restart 09:19:08, python 2371673 started 09:19:17) -- already told in the 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. "
        + f"盒子休眠 08:51:14-09:01:02 (581s; STATS 84410881..84411039, 159t; official-filled {fill0851}; listener auto-restart 09:01:06, python 2364487 started 09:01:15) -- already told in the 09:29 _patrol_2026-11-22_0918 USER_LOG; do not re-tell. "
        + "_patrol_2026-11-22_1822 USER_LOG (delivered ~18:38, finished_at 18:39:45, state-only ed18e0cb; treat as already told; do not re-tell): 盒子休眠 17:41:00-18:04:50; leftover official 404 all five rooms @84418900 and W45N7@84419000. _patrol_2026-11-22_1419 USER_LOG (written ~14:28, finished_at 14:30:21; treat as already told; do not re-tell): 盒子休眠 14:15:32-14:20:01 and 13:48:49-13:57:59; leftover official 404 W45N8@84415500. _patrol_2026-11-22_1325 USER_LOG (written ~13:39, finished_at 13:40:38; treat as already told; do not re-tell): 盒子休眠 13:16:57-13:26:20 and 12:51:44-13:03:45; leftover official 404 W46N8@84414700. "
        + "_patrol_2026-11-22_1222 USER_LOG (delivered ~12:33 t508s3627) already includes (treat as already told; do not re-tell): 盒子休眠 12:20:45-12:23:11 and 11:45:08-12:00:47; 监听短中断 12:14:21-12:14:56; leftover official 404 W46N8@84413700. "
        + "_patrol_2026-11-22_1117 USER_LOG (delivered ~11:28) already includes (treat as already told; do not re-tell): 盒子休眠 10:45:15-11:06:19; leftover official 404 W47N7@84412400. "
        + "_patrol_2026-11-22_1022 USER_LOG (delivered ~10:37 t508s3620) already includes (treat as already told; do not re-tell): 盒子休眠 10:16:39-10:22:23 and 09:41:41-09:59:05; leftover official 404 W45N7@84411500. "
        + "_patrol_2026-11-22_0918 USER_LOG (delivered 09:29) already includes (treat as already told; do not re-tell): 盒子休眠 08:51:14-09:01:02 and 09:14:15-09:19:05; W47N7@84411200 first-pass 404 recovered on confirm (no leftover). "
        + "_patrol_2026-11-22_0818 USER_LOG (delivered 08:28) already includes (treat as already told; do not re-tell): 盒子休眠 07:44:22-08:02:42; leftover official 404 W47N8@84409800. "
        + "_patrol_2026-11-22_0725 USER_LOG (delivered 07:35) already includes (treat as already told; do not re-tell): 盒子休眠 07:20:32-07:26:28 and 06:50:03-07:02:08; leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. "
        + "_patrol_2026-11-22_0625 USER_LOG t508s3614 already includes (treat as already told; do not re-tell): 盒子休眠 05:52:44-06:04:12 and 06:21:56-06:26:26. "
        + "_patrol_2026-11-22_0522 USER_LOG already includes (treat as already told; do not re-tell): 盒子休眠 04:41:06-04:59:17 and 05:17:11-05:23:17; 监听短中断 05:25:19-05:27:20; leftover official 404 W46N8@84407000 and W45N8@84407700. "
        + "_patrol_2026-11-22_0422 USER_LOG already includes (treat as already told; do not re-tell): 盒子休眠 03:47:58-04:06:12 and 04:18:46-04:22:28; leftover official 404 W45N8@84406400 / W46N8@84406600 / W46N8@84406700. "
        + "Single listener 2621093 since 19:12:57 after the 19:12:43-19:12:57 WS ping/pong short interrupt auto-restart 19:12:48 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "
        + f"listener_rot {rot} tips {tips}."
        + NL
    )

    (DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
    (DIR / "history_backfill_now.txt").write_text(now_txt)
    shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

    verify = (
        f"wrap {now}" + NL
        + f"ok_quiet=True inserted_total={inserted_total}" + NL
        + f"first_pass game.time=84419755 published_bases=84419000..84419600 reconstructed=84419001..84419700 (700) "
        + f"32/35 200 missing_chunks=3 inserted_first={inserted_first} already_in_db=16465 ts_realigned_first=0; tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_first_nfix=0" + NL
        + f"confirm/retry2/late/postjp still_404 W45N7@84419000 / W45N7@84419300 / W45N8@84419600 inserted=0. Already-told leftover official 404 all five @84418900 aged out of window start 84419001, already told in ~18:38 _patrol_2026-11-22_1822 USER_LOG; not retried this pass. Already-told leftover official 404 W45N7@84419000 retried this overlap, still 404, already told in that 18:38 patrol; do not re-tell. NEW leftover official 404 W45N7@84419300 and W45N8@84419600 (NOT YET TOLD). Already-told leftover official 404s W45N8@84415500 / W46N8@84414700 / W46N8@84413700 / W47N7@84412400 / W45N7@84411500 / W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900 and older aged out of window start 84419001, already told in the 14:28 or earlier patrol, not retried" + NL
        + f"just_published 84419700 at {jp_at} gt={jp_gt} all_five_200={jp_all5} script={script_sum} actual={actual_sum} script_by={script_by} actual_by={actual} still_404={jp_still}" + NL
        + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_applied={bool(tick.get('corrective_applied'))} nfix={corrective}" + NL
        + f"window_db={window_db}" + NL
        + f"dup={dup}" + NL
        + f"tips={tips}" + NL
        + f"listener {listener_lines} rot={rot} yield_absent={yield_absent}" + NL
        + f"gaps 1912={{ { {r: gaps['gap_1912_1913'][r]['fill'] for r in ROOMS} } }} 1741={{ { {r: gaps['gap_1741_1804'][r]['fill'] for r in ROOMS} } }} 1712={{ { {r: gaps['gap_1712_1722'][r]['fill'] for r in ROOMS} } }} 1644={{ { {r: gaps['gap_1644_1659'][r]['fill'] for r in ROOMS} } }} 1615={{ { {r: gaps['gap_1615_1622'][r]['fill'] for r in ROOMS} } }} 1602={{ { {r: gaps['gap_1602_1602'][r]['fill'] for r in ROOMS} } }} 1447={{ { {r: gaps['gap_1447_1501'][r]['fill'] for r in ROOMS} } }} 1415={{ { {r: gaps['gap_1415_1420'][r]['fill'] for r in ROOMS} } }} 1348={{ { {r: gaps['gap_1348_1357'][r]['fill'] for r in ROOMS} } }} 1316={{ { {r: gaps['gap_1316_1326'][r]['fill'] for r in ROOMS} } }} 1251={{ { {r: gaps['gap_1251_1303'][r]['fill'] for r in ROOMS} } }} 1220={{ { {r: gaps['gap_1220_1223'][r]['fill'] for r in ROOMS} } }} 1214={{ { {r: gaps['gap_1214_1214'][r]['fill'] for r in ROOMS} } }} 1145={{ { {r: gaps['gap_1145_1200'][r]['fill'] for r in ROOMS} } }} 1045={{ { {r: gaps['gap_1045_1106'][r]['fill'] for r in ROOMS} } }} 1016={{ { {r: gaps['gap_1016_1022'][r]['fill'] for r in ROOMS} } }} 0941={{ { {r: gaps['gap_0941_0959'][r]['fill'] for r in ROOMS} } }} 0914={{ { {r: gaps['gap_0914_0919'][r]['fill'] for r in ROOMS} } }} 0851={{ { {r: gaps['gap_0851_0901'][r]['fill'] for r in ROOMS} } }} 0744={{ { {r: gaps['gap_0744_0802'][r]['fill'] for r in ROOMS} } }} 0720={{ { {r: gaps['gap_0720_0726'][r]['fill'] for r in ROOMS} } }} 0650={{ { {r: gaps['gap_0650_0702'][r]['fill'] for r in ROOMS} } }} 0621={{ { {r: gaps['gap_0621_0626'][r]['fill'] for r in ROOMS} } }} 0552={{ { {r: gaps['gap_0552_0604'][r]['fill'] for r in ROOMS} } }} 0517={{ { {r: gaps['gap_0517_0523'][r]['fill'] for r in ROOMS} } }} 0525={{ { {r: gaps['gap_0525_0527'][r]['fill'] for r in ROOMS} } }} 0441={{ { {r: gaps['gap_0441_0459'][r]['fill'] for r in ROOMS} } }}" + NL
        + f"holes={holes}" + NL
        + "already_told by _patrol_2026-11-22_1822 USER_LOG ~18:38 finished_at 18:39:45 (do not re-tell): 盒子休眠 17:41:00-18:04:50; leftover official 404 all five @84418900 and W45N7@84419000. already_told by _patrol_2026-11-22_1722 USER_LOG ~17:35 finished_at 17:34:36 t508s3633 (do not re-tell): 盒子休眠 17:12:37-17:22:45 and 16:44:58-16:59:18. already_told by _patrol_2026-11-22_1621 USER_LOG ~16:32 finished_at 16:33:58 (do not re-tell): 盒子休眠 16:15:02-16:22:09; 监听短中断 16:02:42-16:02:55. already_told by _patrol_2026-11-22_1521 USER_LOG ~15:32 finished_at 15:34:21 (do not re-tell): 盒子休眠 14:47:50-15:01:16. already_told by _patrol_2026-11-22_1419 USER_LOG ~14:28 finished_at 14:30:21 (do not re-tell): 盒子休眠 14:15:32-14:20:01 and 13:48:49-13:57:59; leftover official 404 W45N8@84415500. already_told by _patrol_2026-11-22_1325 USER_LOG ~13:39 finished_at 13:40:38 (do not re-tell): 盒子休眠 13:16:57-13:26:20 and 12:51:44-13:03:45; leftover official 404 W46N8@84414700. already_told by _patrol_2026-11-22_1222 USER_LOG t508s3627 (do not re-tell): 盒子休眠 12:20:45-12:23:11 and 11:45:08-12:00:47; 监听短中断 12:14:21-12:14:56; leftover official 404 W46N8@84413700. Already told by _patrol_2026-11-22_1117 USER_LOG (do not re-tell): 盒子休眠 10:45:15-11:06:19; leftover official 404 W47N7@84412400. Already told by _patrol_2026-11-22_1022 USER_LOG t508s3620 (do not re-tell): 盒子休眠 10:16:39-10:22:23 and 09:41:41-09:59:05; leftover official 404 W45N7@84411500. Already told by _patrol_2026-11-22_0918 USER_LOG (do not re-tell): 盒子休眠 08:51:14-09:01:02 and 09:14:15-09:19:05; W47N7@84411200 first-pass 404 recovered on confirm (no leftover). Already told by _patrol_2026-11-22_0818 USER_LOG (do not re-tell): 盒子休眠 07:44:22-08:02:42; leftover official 404 W47N8@84409800. Already told by _patrol_2026-11-22_0725 USER_LOG (do not re-tell): 盒子休眠 07:20:32-07:26:28 and 06:50:03-07:02:08; leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. Already told by _patrol_2026-11-22_0625 USER_LOG t508s3614 (do not re-tell): 盒子休眠 05:52:44-06:04:12 and 06:21:56-06:26:26. Already told by _patrol_2026-11-22_0522 USER_LOG (do not re-tell): 盒子休眠 04:41:06-04:59:17 and 05:17:11-05:23:17; 监听短中断 05:25:19-05:27:20; leftover official 404 W46N8@84407000 and W45N8@84407700. Older already-told freezes through 04:18 / 03:47 / 02:44 and leftover official 404s through W45N8@84406400 / W46N8@84406600 / W46N8@84406700 and earlier." + NL
        + "ok_quiet=True new_official_404_untold=['W45N7@84419300','W45N8@84419600'] still_untold_from_1230=[] still_untold_from_1100=[] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[] still_untold_freeze_from_1230=[] still_untold_freeze_from_1100=[] still_untold_freeze_from_1000=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=['ws_19:12:43-19:12:57 STATS 84419821..84419849'] first_pass_source=this_halfhour_1900 concurrent_patrol=delivered_1822_1839 concurrent_12h_review=already_delivered_0833_do_not_write_its_folder" + NL
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
        "new_official_404_untold": ["W45N7@84419300", "W45N8@84419600"],  # W45N7@84419300 leftover from 18:30 JP after 18:38 patrol; W45N8@84419600 new first-pass leftover this run
        "still_untold_from_1230": [],
        "still_untold_from_1100": [],
        "still_untold_from_1000": [],
        "still_untold_from_0800": [],
        "still_untold_from_0730": [],
        "still_untold_from_0700": [],
        "still_untold_from_0600": [],
        "still_untold_from_0530": [],
        "new_box_freeze_untold": [],
        "still_untold_freeze_from_1230": [],
        "still_untold_freeze_from_1100": [],
        "still_untold_freeze_from_1000": [],
        "still_untold_freeze_from_0800": [],
        "still_untold_freeze_from_0730": [],
        "still_untold_freeze_from_0700": [],
        "still_untold_freeze_from_0600": [],
        "new_short_ws_untold": ["ws_19:12:43-19:12:57 STATS 84419821..84419849"],
        "concurrent_patrol": "delivered_1822_1839",
        "concurrent_12h_review": "already_delivered_0833_do_not_write_its_folder",
        "did_not_write_patrol_folder": True,
        "first_pass_realign": "moved 0 rows ts_realigned_first=0; tick_s_in_use=first 4.19280 after tick_s_check, no corrective, still_over_45s vs first=0",
    }
    (DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + NL)
    (DIR / "wrapup_run.txt").write_text(f"wrap {now} ok_quiet=True inserted_total={inserted_total}{NL}")
    print(f"wrap {now} ok_quiet=True inserted_total={inserted_total}")


if __name__ == "__main__":
    main()
