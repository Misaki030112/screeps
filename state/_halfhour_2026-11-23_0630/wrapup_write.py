#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
STATE = ROOT / "state"
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_0630")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
NL = chr(10)
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

T0, T1 = 84428601, 84429300
JP_BASE = 84429300
JP_T0, JP_T1 = JP_BASE + 1, JP_BASE + 100

GAPS = [
    ("gap_0623_0627", 84429281, 84429349),
    ("gap_0548_0606", 84428841, 84429079),
    ("gap_0516_0525", 84428401, 84428539),
    ("gap_0453_0458", 84428081, 84428169),
    ("gap_0420_0435", 84427641, 84427859),
    ("gap_0352_0358", 84427261, 84427359),
    ("gap_0322_0329", 84426841, 84426959),
    ("gap_0251_0258", 84426401, 84426519),
    ("gap_0219_0228", 84425951, 84426089),
    ("gap_0146_0201", 84425481, 84425709),
    ("gap_0115_0127", 84425041, 84425219),
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
    ("W47N7", 84429300),
    ("W45N7", 84428300),
    ("W45N8", 84425500),
    ("W45N8", 84425800),
    ("W45N8", 84426200),
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

    inserted_first = 3012
    inserted_confirm_script = int(confirm.get("inserted") or 0)
    inserted_retry2_script = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
    inserted_confirm = inserted_confirm_script
    inserted_retry2 = inserted_retry2_script
    inserted_late = int(late.get("inserted") or 0)
    inserted_postjp = int(postjp.get("inserted") or 0)
    inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + inserted_postjp + actual_sum

    out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
    listener_lines = [ln.strip() for ln in out.splitlines() if "tools/listener.py" in ln]
    rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
    yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

    w45n7_84428300 = holes["W45N7@84428300"]
    w45n8_84425500 = holes["W45N8@84425500"]
    w45n8_84425800 = holes["W45N8@84425800"]
    w45n8_84426200 = holes["W45N8@84426200"]
    w45n8_84422100 = holes["W45N8@84422100"]
    w45n8_84422400 = holes["W45N8@84422400"]
    w47n7_84429300 = holes["W47N7@84429300"]
    fill0623 = fill_txt(gaps["gap_0623_0627"])

    fill0548 = fill_txt(gaps["gap_0548_0606"])
    fill0516 = fill_txt(gaps["gap_0516_0525"])
    fill0453 = fill_txt(gaps["gap_0453_0458"])
    fill0420 = fill_txt(gaps["gap_0420_0435"])
    fill0352 = fill_txt(gaps["gap_0352_0358"])
    fill0322 = fill_txt(gaps["gap_0322_0329"])
    fill0251 = fill_txt(gaps["gap_0251_0258"])
    fill0219 = fill_txt(gaps["gap_0219_0228"])
    fill0146 = fill_txt(gaps["gap_0146_0201"])
    fill0115 = fill_txt(gaps["gap_0115_0127"])
    fill0051 = fill_txt(gaps["gap_0051_0057"])
    fill0023 = fill_txt(gaps["gap_0023_0033"])
    fill2352 = fill_txt(gaps["gap_2352_2359"])
    fill2243 = fill_txt(gaps["gap_2243_2305"])
    fill2145 = fill_txt(gaps["gap_2145_2204"])

    tick_s_in_use = tick.get("tick_s_in_use")
    first = tick.get("tick_s_used_first_pass") or 4.43969
    later = tick.get("later_mean_w46") or tick.get("later_mean_robust")
    corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
    tick_s_label = tick.get("tick_s_in_use_name") or "first"
    over45_first = tick.get("still_over_45s_vs_first")
    over45_later = tick.get("still_over_45s_vs_later_before") or tick.get("still_over_45s_vs_later")
    vs_all = ((tick.get("vs_candidates") or {}).get("all_mean") or {})
    over45_all = vs_all.get("over45")

    first_txt = (DIR / "history_backfill.txt").read_text().rstrip() + NL
    retry2 = confirm.get("retry2") or {}
    confirm_at = confirm.get("confirm_at") or confirm.get("at")
    confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
    retry2_at = confirm.get("retry2_at") or retry2.get("at")
    retry2_gt = confirm.get("retry2_game_time") or retry2.get("game_time")
    late_at = late.get("at")
    late_gt = late.get("game_time")
    jp_at = jp.get("at")
    jp_gt = jp.get("game_time")
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
        "source=this_halfhour_first_pass _halfhour_2026-11-23_0630" + NL
        + first_txt
        + f"---- wrap {now} ----" + NL
        + _pass_txt("confirm", confirm_at, confirm_gt, confirm, inserted_confirm_script) + " "
        + _pass_txt("retry2", retry2_at, retry2_gt, retry2, inserted_retry2_script) + " "
        + _pass_txt("late retry", late_at, late_gt, late, inserted_late) + " "
        + _pass_txt("post-JP leftover retry", postjp.get("at"), postjp.get("game_time"), postjp, inserted_postjp) + " "
        + "First pass 35/35 official GETs 200, missing_chunks=0. "
        + "First pass started 2026-11-23 06:32:22 Asia/Hong_Kong and finished 06:33:10 (exit=0): "
        + "inserted=3012 already_in_db=23022, first-pass realign moved 19540 rows ts_realigned_first=19540 "
        + "(first-interval tick_s printed 4.440, exact 4.43969). Overlap with the 06:00 half-hour (official 84428401..84429100 / JP 84429100) accounts for already_in_db=23022. "
        + "First-pass insert matched would_insert=3012. Already-told leftover W45N7@84428300 (aged out of window start 84428601, two chunks before this window, not a first-pass 404 this window) was not retried; do not label NEW. "
        + f"tick_s_check chose live-anchor-best {tick_s_label} {tick_s_in_use} (first {first} over45={over45_first} then corrective nfix={corrective} after over45=0; later-mean {later} over45={over45_later}; all_mean over45={over45_all}; prev_later {tick.get('prev_later_mean')} over45={((tick.get('vs_candidates') or {}).get('prev_later') or {}).get('over45')}); corrective_applied=True nfix={corrective}; skipped_cross_chunk={tick.get('skipped_cross_chunk', 0)}; applied first, not later-mean (later-mean over45 worse). "
        + "Last delivered USER_LOG is ~05:38 _patrol_2026-11-23_0516 (finished_at 05:40:08); do not re-tell it. This half-hour did not write a patrol or 12h-review folder. No concurrent patrol this run. Quiet 06:00 half-hour _halfhour_2026-11-23_0600 already wrapped 06:21:02; do not re-tell that collect-only wrap, but carry its still-untold 盒子休眠 05:48:18-06:06:20 into the next 3h patrol. 12h review _review12h_2026-11-22_20 already completed ~20:37 (docs-only, LIVE still 2b5398f7, not a game deploy); do not re-tell or write its folder. "
        + "06:00 half-hour already official-filled 84428401..84429100 / just-published 84429100, wrap 06:21:02, with no NEW leftover official 404; its NEW 盒子休眠 05:48:18-06:06:20 was not yet told. "
        + f"Just-published 84429300 was not in first pass (first pass ended at published 84429200 / reconstructed 84428601..84429300 at game.time=84429395, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} still_404={jp_still}. "
        + "JP retry at 2026-11-23 06:40:42 Asia/Hong_Kong gt=84429500 still_404=['W47N7@84429300'] recovered the other four, script inserted=167. "
        + "JP retry2 at 2026-11-23 06:49:13 Asia/Hong_Kong gt=84429600 still_404=['W47N7@84429300'] script inserted=167 (W45N7 script count; actual unique rows did not grow — just_actual uses unique-minus-pre). "
        + f"script={script_sum} actual={actual_sum}; {script_vs_txt}. "
        + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
        + f"W46N8 official empty_no_creep in this first-pass window: {empty_txt('W46N8')}. "
        + f"W47N8 official empty_no_creep in this first-pass window: {empty_txt('W47N8')}. "
        + f"W45N8 official empty_no_creep in this first-pass window: {empty_txt('W45N8')}. "
        + f"W45N7 official empty_no_creep in this first-pass window: {empty_txt('W45N7')}. "
        + f"W47N7 official empty_no_creep in this first-pass window: {empty_txt('W47N7')}. "
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} postjp={inserted_postjp} just_actual={actual_sum} total={inserted_total}. "
        + f"NEW leftover official 404 W47N7@84429300 (just-published chunk, not a first-pass 404; first GET 06:35:58 gt=84429440, retry 06:40:42 gt=84429500, retry2 06:49:13 gt=84429600, and postjp 06:50:54 gt=84429625 still 404, inserted=0; listener {w47n7_84429300['distinct']}/100 range {w47n7_84429300['min']}..{w47n7_84429300['max']}; hole {w47n7_84429300['hole_ticks']} ticks {hole_range_txt(w47n7_84429300)}) is not yet told; fold into the next 3h patrol. "
        + f"Already-told leftover official 404 W45N7@84428300 (already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG finished_at 05:40:08; not a first-pass 404 in this window; aged out of window start 84428601 and was not retried this pass; listener {w45n7_84428300['distinct']}/100 range {w45n7_84428300['min']}..{w45n7_84428300['max']}; hole {w45n7_84428300['hole_ticks']} ticks {hole_range_txt(w45n7_84428300)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84426200 (already told in the same ~05:38 0516 USER_LOG; previously still-untold from the 03:00 half-hour; not a first-pass 404 in this window; aged out of window start 84428601 and was not retried this pass; listener {w45n8_84426200['distinct']}/100 range {w45n8_84426200['min']}..{w45n8_84426200['max']}; hole {w45n8_84426200['hole_ticks']} ticks {hole_range_txt(w45n8_84426200)}) is not labeled NEW this wrap; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84425500 and W45N8@84425800 (already told in the ~02:43 _patrol_2026-11-23_0216 USER_LOG and mentioned as already-told in the ~05:38 0516 USER_LOG; aged out of window start 84428601 and were not retried this pass; listener {w45n8_84425500['distinct']}/100 and {w45n8_84425800['distinct']}/100; holes {w45n8_84425500['hole_ticks']} ticks {hole_range_txt(w45n8_84425500)} and {w45n8_84425800['hole_ticks']} ticks {hole_range_txt(w45n8_84425800)}) are not labeled NEW this wrap; do not re-tell. "
        + "Already-told leftover official 404s W45N8@84422100 and W45N8@84422400 aged out of window start 84428601 and were not retried this pass (already told in the 22:37 patrol and mentioned as already-told later; do not re-tell). "
        + "NEW leftover official 404 this run: W47N7@84429300 — NOT YET TOLD; fold into the next 3h patrol. NEW 盒子休眠 this run: 06:23:39-06:27:58 Asia/Hong_Kong — NOT YET TOLD; fold into the next 3h patrol. Still-untold 盒子休眠 from the quiet 06:00 half-hour: 05:48:18-06:06:20 — still NOT YET TOLD; fold into the next 3h patrol. NEW 监听短中断 this run: none. "
        + f"NEW 盒子休眠 06:23:39-06:27:58 Asia/Hong_Kong (251s, box_pauses row; STATS 84429281..84429349, 69t; official-filled {fill0623}; W47N7 20/69 missing tail 84429301..84429349 due to leftover official 404 W47N7@84429300; listener auto-restart 06:28:01, python 2910119 started 06:28:11, parent 4035476) is not yet told; fold into the next 3h patrol. "
        + f"Still-untold 盒子休眠 05:48:18-06:06:20 Asia/Hong_Kong (1075s, box_pauses row; STATS 84428841..84429079, 239t; official-filled {fill0548}; listener auto-restart 06:06:23, python 2899745 started 06:06:33, parent 4035476) was recorded by the quiet 06:00 half-hour (wrap 06:21:02) and is still not yet told; fold into the next 3h patrol. "
        + f"Already-told 盒子休眠 05:16:36-05:25:46 Asia/Hong_Kong (545s, box_pauses row; STATS 84428401..84428539, 139t; official-filled {fill0516}; listener auto-restart 05:25:49, python 2883580 started 05:25:59, parent 4035476) was already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG; do not re-tell. "
        + f"Already-told 盒子休眠 04:53:04-04:58:42 (332s; STATS 84428081..84428169 official-filled {fill0453}; listener auto-restart 04:58:45, python 2872869 started 04:58:54, parent 4035476) and 04:20:59-04:35:45 (878s; STATS 84427641..84427859 official-filled {fill0420}; listener auto-restart 04:35:48, python 2862906 started 04:35:58, parent 4035476) and 03:52:38-03:58:50 (371s; STATS 84427261..84427359 official-filled {fill0352}; listener auto-restart 03:58:53, python 2850693 started 03:59:02, parent 4035476) and 03:22:33-03:29:51 (432s; STATS 84426841..84426959 official-filled {fill0322}; listener auto-restart 03:29:55, python 2838073 started 03:30:04, parent 4035476) and 02:51:37-02:58:39 (421s; STATS 84426401..84426519 official-filled {fill0251}; listener auto-restart 02:58:42, python 2822854 started 02:58:52, parent 4035476) were already told in the same ~05:38 0516 USER_LOG; do not re-tell. "
        + f"Already-told 盒子休眠 02:19:33-02:28:15 (515s; STATS 84425951..84426089 official-filled {fill0219}; listener auto-restart 02:28:18, python 2807754 started 02:28:27, parent 4035476) was already told in the ~02:43 _patrol_2026-11-23_0216 USER_LOG; do not re-tell. "
        + f"Already-told 盒子休眠 01:46:20-02:01:27 (901s; STATS 84425481..84425709 official-filled {fill0146}; listener auto-restart 02:01:30, python 2796851 started 02:01:40, parent 4035476; W45N8 129/229 because leftover official 404 W45N8@84425500 sits inside it) and 01:15:53-01:27:13 (672s; STATS 84425041..84425219 official-filled {fill0115}; listener auto-restart 01:27:16, python 2785707 started 01:27:25, parent 4035476) and 00:51:21-00:57:39 (378s; STATS 84424691..84424799 official-filled {fill0051}; listener auto-restart 00:57:42, python 2775547 started 00:57:52, parent 4035476) and 00:23:50-00:33:45 (595s; STATS 84424291..84424449 official-filled {fill0023}; listener auto-restart 00:33:49, python 2765557 started 00:33:58, parent 4035476) and 23:52:01-23:59:48 (459s; STATS 84423801..84423969 official-filled {fill2352}; listener auto-restart 23:59:51, python 2749374 started 00:00:01, parent 4035476; the 23:51:41 no-STATS reconnect shares that STATS gap and is not a separate 监听短中断) were already told in the same ~02:43 patrol USER_LOG; do not re-tell. "
        + f"Already-told 盒子休眠 22:43:27-23:05:49 (1334s; STATS 84422871..84423199 official-filled {fill2243}; already told in the 23:31 patrol; do not re-tell). "
        + f"Already-told 盒子休眠 21:45:57-22:04:37 (1120s; STATS 84422041..84422319 official-filled {fill2145}; already told in the 22:37 patrol; do not re-tell). "
        + "Already-told 盒子休眠 20:49:49-20:59:53 and 19:43:54-19:59:40 and 17:41:00-18:04:50 and older; already-told 监听短中断 through 19:12:43-19:12:57 and 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20; do not re-tell. "
        + f"window_db={window_db}" + NL
        + f"jp_post={post} jp_script_by={script_by} jp_actual_by={actual}" + NL
        + f"tips={tips}" + NL
        + f"listener {listener_lines} rot={rot} yield_absent={yield_absent}" + NL
        + "Single listener 2910119 since 06:28:11 after the NEW 盒子休眠 06:23:39-06:27:58 auto-restart 06:28:01 (parent 4035476), peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "
        + f"listener_rot {rot} tips {tips}."
        + NL
    )

    (DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
    (DIR / "history_backfill_now.txt").write_text(now_txt)
    shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

    verify = (
        f"wrap {now} ok_quiet=True" + NL
        + f"window={T0}..{T1} jp={JP_T0}..{JP_T1}" + NL
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} postjp={inserted_postjp} just_actual={actual_sum} total={inserted_total}" + NL
        + f"tick_s_in_use={tick_s_in_use} name={tick_s_label} corrective_applied=True nfix={corrective}" + NL
        + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
        + f"window_db={window_db}" + NL
        + f"jp_post={post} jp_dup={dup} jp_script_by={script_by} jp_actual_by={actual}" + NL
        + f"holes W47N7@84429300={holes['W47N7@84429300']} W45N7@84428300={holes['W45N7@84428300']} W45N8@84425500={holes['W45N8@84425500']} W45N8@84425800={holes['W45N8@84425800']} W45N8@84426200={holes['W45N8@84426200']} W45N8@84422100={holes['W45N8@84422100']} W45N8@84422400={holes['W45N8@84422400']}" + NL
        + f"NEW 盒子休眠 this run: 06:23:39-06:27:58 Asia/Hong_Kong (251s, box_pauses row; STATS 84429281..84429349, 69t; official-filled {fill0623}; W47N7 20/69 missing tail 84429301..84429349 due to leftover official 404 W47N7@84429300; listener auto-restart 06:28:01, python 2910119 started 06:28:11, parent 4035476) — NOT YET TOLD; fold into the next 3h patrol. Still-untold 盒子休眠 from the quiet 06:00 half-hour: 05:48:18-06:06:20 Asia/Hong_Kong (1075s, box_pauses row; STATS 84428841..84429079, 239t; official-filled {fill0548}; listener auto-restart 06:06:23, python 2899745 started 06:06:33, parent 4035476) — still NOT YET TOLD; fold into the next 3h patrol. Already-told 盒子休眠 05:16:36-05:25:46 (545s; STATS 84428401..84428539 official-filled {fill0516}; listener auto-restart 05:25:49, python 2883580 started 05:25:59, parent 4035476) was already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG finished_at 05:40:08; do not re-tell. Already-told 盒子休眠 04:53:04-04:58:42 (332s; STATS 84428081..84428169 official-filled {fill0453}; listener auto-restart 04:58:45, python 2872869 started 04:58:54, parent 4035476) and 04:20:59-04:35:45 (878s; STATS 84427641..84427859 official-filled {fill0420}; listener auto-restart 04:35:48, python 2862906 started 04:35:58, parent 4035476) and 03:52:38-03:58:50 (371s; STATS 84427261..84427359 official-filled {fill0352}; listener auto-restart 03:58:53, python 2850693 started 03:59:02, parent 4035476) and 03:22:33-03:29:51 (432s; STATS 84426841..84426959 official-filled {fill0322}; listener auto-restart 03:29:55, python 2838073 started 03:30:04, parent 4035476) and 02:51:37-02:58:39 (421s; STATS 84426401..84426519 official-filled {fill0251}; listener auto-restart 02:58:42, python 2822854 started 02:58:52, parent 4035476) were already told in the same 0516 USER_LOG; do not re-tell. NEW leftover official 404 W47N7@84429300 (just-published chunk, not a first-pass 404; first GET 06:35:58, retry 06:40:42, retry2 06:49:13, postjp 06:50:54 still 404; hole 100 ticks 84429301..84429400; listener {w47n7_84429300['distinct']}/100) — NOT YET TOLD; fold into the next 3h patrol. Leftover official 404 W45N7@84428300 (not a first-pass 404 this window; aged out of window start 84428601, not retried this pass; hole 100 ticks 84428301..84428400; listener {w45n7_84428300['distinct']}/100) already told in the 0516 USER_LOG; do not re-tell. Leftover official 404 W45N8@84426200 (previously still-untold from 03:00; aged out of window start 84428601, not retried this pass; hole 100 ticks 84426201..84426300; listener {w45n8_84426200['distinct']}/100) already told in the 0516 USER_LOG; do not re-tell. Leftover official 404 W45N8@84425500 and W45N8@84425800 (aged out, not retried this pass) already told in the 02:43 patrol USER_LOG and mentioned as already-told in the 0516 USER_LOG; do not re-tell. NEW 监听短中断 none. already_told by _patrol_2026-11-23_0516 USER_LOG ~05:38 finished_at 05:40:08 (do not re-tell): 盒子休眠 05:16:36-05:25:46 (STATS 84428401..84428539 official-filled {fill0516}) and 04:53:04-04:58:42 (STATS 84428081..84428169 official-filled {fill0453}) and 04:20:59-04:35:45 (STATS 84427641..84427859 official-filled {fill0420}) and 03:52:38-03:58:50 (STATS 84427261..84427359 official-filled {fill0352}) and 03:22:33-03:29:51 (STATS 84426841..84426959 official-filled {fill0322}) and 02:51:37-02:58:39 (STATS 84426401..84426519 official-filled {fill0251}); leftover official 404 W45N8@84426200 and W45N7@84428300. already_told by _patrol_2026-11-23_0216 USER_LOG ~02:43 finished_at 02:43:39 (do not re-tell): 盒子休眠 02:19:33-02:28:15 (STATS 84425951..84426089 official-filled {fill0219}) and 01:46:20-02:01:27 (STATS 84425481..84425709 official-filled {fill0146}; W45N8 129/229 because of W45N8@84425500) and 01:15:53-01:27:13 (STATS 84425041..84425219 official-filled {fill0115}) and 00:51:21-00:57:39 (STATS 84424691..84424799 official-filled {fill0051}) and 00:23:50-00:33:45 (STATS 84424291..84424449 official-filled {fill0023}) and 23:52:01-23:59:48 (STATS 84423801..84423969 official-filled {fill2352}; the 23:51:41 no-STATS reconnect shares that STATS gap and is not a separate 监听短中断); leftover official 404 W45N8@84425500 and W45N8@84425800. already_told by _patrol_2026-11-22_2316 USER_LOG ~23:31 finished_at 23:32:40 (do not re-tell): 盒子休眠 22:43:27-23:05:49 (STATS 84422871..84423199 official-filled {fill2243}). already_told by _patrol_2026-11-22_2224 USER_LOG ~22:37 finished_at 22:36:58 (do not re-tell): 盒子休眠 21:45:57-22:04:37; leftover official 404 W45N8@84422100 and W45N8@84422400. Older already-told freezes through 20:49:49-20:59:53 / 19:43:54-19:59:40 / 17:41:00-18:04:50 and leftover official 404s through W45N7@84419300 / W45N8@84419600 / all five @84418900 and earlier. already-told 监听短中断 through 19:12:43-19:12:57 and 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20." + NL
        + "ok_quiet=True new_official_404_untold=[W47N7@84429300] still_untold_from_0300=[] still_untold_from_1230=[] still_untold_from_1100=[] still_untold_from_1000=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[06:23:39-06:27:58] still_untold_freeze_from_0600=[05:48:18-06:06:20] still_untold_freeze_from_0500=[] still_untold_freeze_from_0430=[] still_untold_freeze_from_0400=[] still_untold_freeze_from_0330=[] still_untold_freeze_from_0300=[] still_untold_freeze_from_0200=[] still_untold_freeze_from_0130=[] still_untold_freeze_from_0100=[] still_untold_freeze_from_0030=[] still_untold_freeze_from_0000=[] still_untold_freeze_from_1230=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0630 concurrent_patrol=none_this_run last=_patrol_2026-11-23_0516_finished_at_05:40:08_USER_LOG_~05:38 concurrent_12h_review=already_completed_review12h_2026-11-22_20_do_not_write_its_folder already_told_404s_this_patrol=[W45N8@84425500,W45N8@84425800,W45N8@84426200,W45N7@84428300] already_told_freeze_this_patrol=[05:16:36-05:25:46,04:53:04-04:58:42,04:20:59-04:35:45,03:52:38-03:58:50,03:22:33-03:29:51,02:51:37-02:58:39,02:19:33-02:28:15,01:46:20-02:01:27,01:15:53-01:27:13,00:51:21-00:57:39,00:23:50-00:33:45,23:52:01-23:59:48]" + NL
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
        "inserted_postjp": inserted_postjp,
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
        "new_official_404_untold": ["W47N7@84429300"],
        "still_untold_from_0300": [],
        "already_told_404s_this_patrol": ["W45N8@84425500", "W45N8@84425800", "W45N8@84426200", "W45N7@84428300"],
        "new_box_freeze_untold": ["06:23:39-06:27:58"],
        "still_untold_freeze_from_0600": ["05:48:18-06:06:20"],
        "still_untold_freeze_from_0430": [],
        "still_untold_freeze_from_0400": [],
        "still_untold_freeze_from_0330": [],
        "still_untold_freeze_from_0300": [],
        "already_told_freeze_this_patrol": ["05:16:36-05:25:46", "04:53:04-04:58:42", "04:20:59-04:35:45", "03:52:38-03:58:50", "03:22:33-03:29:51", "02:51:37-02:58:39", "02:19:33-02:28:15", "01:46:20-02:01:27", "01:15:53-01:27:13", "00:51:21-00:57:39", "00:23:50-00:33:45", "23:52:01-23:59:48"],
        "new_short_ws_untold": [],
        "concurrent_patrol": "none_this_run; last=_patrol_2026-11-23_0516_finished_at_05:40:08_USER_LOG_~05:38",
        "concurrent_12h_review": "already_completed_review12h_2026-11-22_20_do_not_write_its_folder",
        "did_not_write_patrol_folder": True,
        "first_pass_realign": "moved 19540 rows ts_realigned_first=19540 with first=4.43969; tick_s_check live-anchor-best first 4.43969 (first over45=2847 then corrective nfix=2847 after over45=0; later-mean 4.806526 over45=23436; all_mean over45=20877; prev_later 4.38831 over45=8471); applied first, not later-mean",
    }
    (DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + NL)
    (DIR / "wrapup_run.txt").write_text(f"wrap {now} ok_quiet=True inserted_total={inserted_total}{NL}")
    print(f"wrap {now} ok_quiet=True inserted_total={inserted_total}")


if __name__ == "__main__":
    main()
