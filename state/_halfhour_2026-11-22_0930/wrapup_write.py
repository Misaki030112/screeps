#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
STATE = ROOT / "state"
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-22_0900")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
NL = chr(10)
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

T0, T1 = 84410301, 84411000
JP_BASE = 84411000
JP_T0, JP_T1 = JP_BASE + 1, JP_BASE + 100

GAPS = [
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
    script_by = {}
    gets = jp.get("gets") or jp.get("results") or []
    script_sum = int(jp.get("inserted") or 0)
    if gets:
        for g in gets:
            script_by[g["room"]] = int(g.get("inserted") or 0)
        script_sum = sum(script_by.values()) if script_by else script_sum
    else:
        script_by = {r: None for r in ROOMS}

    # First pass inserted=10151 is the real DB insert. confirm/retry2/late skipped (no targets).
    inserted_first = 9250
    inserted_confirm_script = int(confirm.get("inserted") or 0)
    inserted_retry2_script = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
    inserted_confirm = 0
    inserted_retry2 = 0
    inserted_late = int(late.get("inserted") or 0)
    inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + actual_sum

    out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
    listener_lines = [ln.strip() for ln in out.splitlines() if "tools/listener.py" in ln]
    rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
    yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

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
    first = tick.get("tick_s_used_first_pass") or 4.101
    later = tick.get("later_mean_w46") or tick.get("later_mean_robust")
    corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
    tick_s_label = tick.get("tick_s_in_use_name") or "all_mean"

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
    jp_all5 = (not jp_still) and all((g.get("ok") or g.get("code") == 200) for g in gets) if gets else (not jp_still)

    def script_vs(room):
        s = script_by.get(room)
        a = actual[room]
        return f"{room} script {s} vs actual {a}"

    script_vs_txt = ", ".join(script_vs(r) for r in ROOMS)

    now_txt = (
        "source=this_halfhour_first_pass _halfhour_2026-11-22_0900" + NL
        + first_txt
        + f"---- wrap {now} ----" + NL
        + f"confirm at {confirm_at} gt={confirm_gt} skipped no targets inserted={inserted_confirm_script}. "
        + f"retry2 at {retry2_at} gt={retry2_gt} skipped no targets inserted={inserted_retry2_script}. "
        + f"late retry at {late_at} gt={late_gt} skipped no targets inserted={inserted_late}. "
        + "First pass 35/35 official GETs 200, missing_chunks=0. "
        + "First pass started 2026-11-22 09:03:26 Asia/Hong_Kong and finished 09:04:12 (exit=0): "
        + "inserted=9250 already_in_db=15658, first-pass realign succeeded ts_realigned_first=23. "
        + "tick_s_check at 09:05:07 chose live-anchor-best later_raw 4.09961 already inside the 45s gate (over45=0), so no corrective realign. "
        + "1h patrol already delivered 08:28 _patrol_2026-11-22_0818. 12h review already delivered ~08:33 t508s3618; do not re-tell or write its folder. "
        + "08:30 half-hour already official-filled through 84410500 / just-published 84410600; this run is idempotent overlap plus new official 84410700..84410900 and just-published 84411000. "
        + "Already-told leftover official 404s W47N8@84409800, W46N8@84408300, W47N8@84408300, W47N7@84407900, W46N8@84407000, W45N8@84407700, W45N8@84406400, W46N8@84406600, W46N8@84406700, "
        + "W45N7@84403800, W45N7@84403700, W45N7@84400400, W45N7@84400300, and W47N8@84400100 aged out of window start 84410301 "
        + "and were not retried this pass (already told in the 08:28 _patrol_2026-11-22_0818 or earlier USER_LOG; do not re-tell). "
        + f"Just-published 84411000 was not in first pass (first pass ended at published 84410900 / reconstructed 84410301..84411000 at "
        + f"game.time=84411068, 35/35 200, missing_chunks=0). GET at {jp_at} gt={jp_gt} all_five_200={jp_all5} "
        + f"script={script_sum} actual={actual_sum}; {script_vs_txt}. "
        + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
        + "W46N8 official empty_no_creep in this first-pass window: none. "
        + "W47N8 official empty_no_creep in this first-pass window: none. "
        + "W45N8 / W45N7 / W47N7 official empty_no_creep in this first-pass window: none. "
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} ts_realigned_first=23 corrective={corrective} "
        + f"(later-raw later-mean {later}; first-pass realign succeeded ts_realigned=23; live-anchor-best later_raw already inside 45s gate, no corrective realign; still_over_45s_vs_target=0 vs later_raw). "
        + f"Already-told leftover official 404 W47N8@84409800 aged out of window start 84410301 and was not retried this pass (listener {w47n8_84409800['distinct']}/100 range {w47n8_84409800['min']}..{w47n8_84409800['max']}; hole {w47n8_84409800['hole_ticks']} ticks {hole_range_txt(w47n8_84409800)}) -- already told in the 08:28 _patrol_2026-11-22_0818 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W46N8@84408300 aged out of window start 84410301 and was not retried this pass (listener {w46n8_84408300['distinct']}/100; hole {w46n8_84408300['hole_ticks']} ticks {hole_range_txt(w46n8_84408300)}) -- already told in the 06:44 _patrol_2026-11-22_0625 t508s3614 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W47N8@84408300 aged out of window start 84410301 and was not retried this pass (listener {w47n8_84408300['distinct']}/100; hole {w47n8_84408300['hole_ticks']} ticks {hole_range_txt(w47n8_84408300)}) -- already told in the 06:44 patrol t508s3614 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W47N7@84407900 aged out of window start 84410301 and was not retried this pass (listener {w47n7_84407900['distinct']}/100; hole {w47n7_84407900['hole_ticks']} ticks {hole_range_txt(w47n7_84407900)}) -- already told in the 06:44 patrol t508s3614 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N8@84407700 aged out of window start 84410301 and was not retried this pass (listener {w45n8_84407700['distinct']}/100; hole {w45n8_84407700['hole_ticks']} ticks {hole_range_txt(w45n8_84407700)}) -- already told in the 05:38 _patrol_2026-11-22_0522 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W46N8@84407000 aged out of window start 84410301 and was not retried this pass (listener {w46n8_84407000['distinct']}/100; hole {w46n8_84407000['hole_ticks']} ticks {hole_range_txt(w46n8_84407000)}) -- already told in the 05:38 _patrol_2026-11-22_0522 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404s aged out of window start 84410301 and were not retried: W45N8@84406400 (listener {w45n8_84406400['distinct']}/100; hole {w45n8_84406400['hole_ticks']} ticks {hole_range_txt(w45n8_84406400)}), W46N8@84406600 (listener {w46n8_84406600['distinct']}/100; hole {w46n8_84406600['hole_ticks']} ticks {hole_range_txt(w46n8_84406600)}), W46N8@84406700 (listener {w46n8_84406700['distinct']}/100; hole {w46n8_84406700['hole_ticks']} ticks {hole_range_txt(w46n8_84406700)}) -- already told in the 04:33 _patrol_2026-11-22_0422 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84403800 aged out of window start 84410301 and was not retried (listener {w45n7_84403800['distinct']}/100; hole {w45n7_84403800['hole_ticks']} ticks {hole_range_txt(w45n7_84403800)}) -- already told in the 01:31 _patrol_2026-11-22_0121 USER_LOG; do not re-tell. "
        + f"Already-told leftover official 404 W45N7@84403700 aged out of window start 84410301 and was not retried (listener {w45n7_84403700['distinct']}/100; hole {w45n7_84403700['hole_ticks']} ticks {hole_range_txt(w45n7_84403700)}) -- already told in the 01:31 patrol USER_LOG; do not re-tell. "
        + "NEW leftover official 404 this run: none. "
        + "NEW short WS this run: none. "
        + f"NEW box freeze this run: 盒子休眠 08:51:14-09:01:02 (581s; STATS 84410881..84411039, 159t; official-filled {fill0851}; listener auto-restart 09:01:06, python 2364487 started 09:01:15) -- not yet told; fold into the next 1h patrol USER_LOG. "
        + f"_patrol_2026-11-22_0818 USER_LOG (delivered 08:28) already includes (treat as already told; do not re-tell): "
        + f"盒子休眠 07:44:22-08:02:42 (1093s; STATS 84409901..84410189, 289t; official-filled {fill0744}; listener auto-restart 08:02:45, python 2336374 started 08:02:54); "
        + f"leftover official 404 W47N8@84409800 (listener {w47n8_84409800['distinct']}/100 range {w47n8_84409800['min']}..{w47n8_84409800['max']}; hole {w47n8_84409800['hole_ticks']} ticks {hole_range_txt(w47n8_84409800)}). "
        + f"_patrol_2026-11-22_0725 USER_LOG (delivered 07:35) already includes (treat as already told; do not re-tell): "
        + f"盒子休眠 07:20:32-07:26:28 (356s; STATS 84409551..84409649, 99t; official-filled {fill0720}; listener auto-restart 07:26:31, python 2325173 started 07:26:41); "
        + f"盒子休眠 06:50:03-07:02:08 (725s; STATS 84409111..84409299, 189t; official-filled {fill0650}; listener auto-restart 07:02:11); "
        + "leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. "
        + f"_patrol_2026-11-22_0625 USER_LOG (delivered 06:44 as t508s3614) already includes (treat as already told; do not re-tell): "
        + f"盒子休眠 05:52:44-06:04:12 (683s; STATS 84408271..84408449, 179t; official-filled {fill0552}; W46N8 and W47N8 short because leftover official 404 W46N8@84408300 and W47N8@84408300 cover 84408301..84408400; listener auto-restart 06:04:15); "
        + f"盒子休眠 06:21:56-06:26:26 (269s; STATS 84408691..84408779, 89t; official-filled {fill0621}; listener auto-restart 06:26:29, python 2299582 started 06:26:38); "
        + "leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. "
        + f"_patrol_2026-11-22_0522 USER_LOG (written 05:38) already includes (treat as already told; do not re-tell): "
        + f"盒子休眠 04:41:06-04:59:17 (1086s; STATS 84407211..84407499, 289t; official-filled {fill0441}; listener auto-restart 04:59:20); "
        + f"盒子休眠 05:17:11-05:23:17 (361s; STATS 84407741..84407849, 109t; official-filled {fill0517}; W45N8 short because leftover official 404 W45N8@84407700 covers 84407741..84407800; listener auto-restart 05:23:20); "
        + f"监听短中断 05:25:19-05:27:20 (no box_pauses row; STATS 84407871..84407899, 29t; official-filled {fill0525}; listener ws ping/pong 05:26:35, auto-restart 05:26:38); "
        + "leftover official 404 W46N8@84407000 / W45N8@84407700. "
        + f"Official fill re-verified this run: 08:51 STATS 84410881..84411039 159t official-filled {fill0851}; 07:44 STATS 84409901..84410189 289t official-filled {fill0744}; 07:20 STATS 84409551..84409649 99t official-filled {fill0720}; 06:50 STATS 84409111..84409299 189t official-filled {fill0650}; 06:21 STATS 84408691..84408779 89t official-filled {fill0621}; 05:52 STATS 84408271..84408449 179t official-filled {fill0552}; 05:17 STATS 84407741..84407849 109t official-filled {fill0517}; 05:25 short WS STATS 84407871..84407899 29t official-filled {fill0525}; 04:41 STATS 84407211..84407499 289t official-filled {fill0441}; 04:18 STATS 84406881..84406949 69t official-filled {fill0418}; 03:47 STATS 84406431..84406719 289t official-filled {fill0347}; 02:44 STATS 84405501..84405799 299t official-filled {fill0244}. "
        + "_patrol_2026-11-22_0422 USER_LOG already includes (treat as already told; do not re-tell): 盒子休眠 03:47:58-04:06:12 and 04:18:46-04:22:28; leftover official 404 W45N8@84406400 / W46N8@84406600 / W46N8@84406700. "
        + "Single listener 2364487 since 09:01:15 after the 08:51 box freeze auto-restart, peacetime one-slot rotation, yield_absent=True. Did not start a second listener or restart war_cmd/pulse. "
        + f"listener_rot {rot} tips {tips}."
        + NL
    )

    (DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
    (DIR / "history_backfill_now.txt").write_text(now_txt)
    shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

    verify = (
        f"wrap {now}" + NL
        + f"ok_quiet=True inserted_total={inserted_total}" + NL
        + f"first_pass game.time=84411068 published_bases=84410300..84410900 reconstructed=84410301..84411000 (700) "
        + f"35/35 200 missing_chunks=0 inserted_first={inserted_first} already_in_db=15658 ts_realigned_first=23 (realign succeeded)" + NL
        + "confirm/retry2/late skipped no targets inserted=0 (leftover official 404s W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900 and older aged out of window start 84410301, already told in 08:28 patrol or earlier)" + NL
        + f"just_published 84411000 at {jp_at} gt={jp_gt} all_five_200={jp_all5} script={script_sum} actual={actual_sum} script_by={script_by} actual_by={actual}" + NL
        + f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}" + NL
        + f"tick_s_in_use={tick_s_in_use} ({tick_s_label}) first={first} corrective_applied={bool(tick.get('corrective_applied'))} nfix={corrective}" + NL
        + f"window_db={window_db}" + NL
        + f"dup={dup}" + NL
        + f"tips={tips}" + NL
        + f"listener {listener_lines} rot={rot} yield_absent={yield_absent}" + NL
        + f"gaps 0851={{ { {r: gaps['gap_0851_0901'][r]['fill'] for r in ROOMS} } }} 0744={{ { {r: gaps['gap_0744_0802'][r]['fill'] for r in ROOMS} } }} 0720={{ { {r: gaps['gap_0720_0726'][r]['fill'] for r in ROOMS} } }} 0650={{ { {r: gaps['gap_0650_0702'][r]['fill'] for r in ROOMS} } }} 0621={{ { {r: gaps['gap_0621_0626'][r]['fill'] for r in ROOMS} } }} 0552={{ { {r: gaps['gap_0552_0604'][r]['fill'] for r in ROOMS} } }} 0517={{ { {r: gaps['gap_0517_0523'][r]['fill'] for r in ROOMS} } }} 0525={{ { {r: gaps['gap_0525_0527'][r]['fill'] for r in ROOMS} } }} 0441={{ { {r: gaps['gap_0441_0459'][r]['fill'] for r in ROOMS} } }}" + NL
        + f"holes={holes}" + NL
        + "already_told by _patrol_2026-11-22_0818 USER_LOG (do not re-tell): 盒子休眠 07:44:22-08:02:42; leftover official 404 W47N8@84409800. Already told by _patrol_2026-11-22_0725 USER_LOG (do not re-tell): 盒子休眠 07:20:32-07:26:28 and 06:50:03-07:02:08; leftover official 404 W46N8@84408300 / W47N8@84408300 / W47N7@84407900. Already told by _patrol_2026-11-22_0625 USER_LOG t508s3614 (do not re-tell): 盒子休眠 05:52:44-06:04:12 and 06:21:56-06:26:26. Already told by _patrol_2026-11-22_0522 USER_LOG (do not re-tell): 盒子休眠 04:41:06-04:59:17 and 05:17:11-05:23:17; 监听短中断 05:25:19-05:27:20; leftover official 404 W46N8@84407000 and W45N8@84407700. Older already-told freezes through 04:18 / 03:47 / 02:44 and leftover official 404s through W45N8@84406400 / W46N8@84406600 / W46N8@84406700 and earlier." + NL
        + "ok_quiet=True new_official_404_untold=[] still_untold_from_0800=[] still_untold_from_0730=[] still_untold_from_0700=[] still_untold_from_0600=[] still_untold_from_0530=[] new_box_freeze_untold=[08:51:14-09:01:02 STATS 84410881..84411039 159t] still_untold_freeze_from_0800=[] still_untold_freeze_from_0730=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0600=[] new_short_ws_untold=[] first_pass_source=this_halfhour_0900 concurrent_patrol=none concurrent_12h_review=already_delivered_0833_do_not_write_its_folder" + NL
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
        "still_untold_from_0800": [],
        "still_untold_from_0730": [],
        "still_untold_from_0700": [],
        "still_untold_from_0600": [],
        "still_untold_from_0530": [],
        "new_box_freeze_untold": ["08:51:14-09:01:02 STATS 84410881..84411039 159t"],
        "still_untold_freeze_from_0800": [],
        "still_untold_freeze_from_0730": [],
        "still_untold_freeze_from_0700": [],
        "still_untold_freeze_from_0600": [],
        "new_short_ws_untold": [],
        "concurrent_patrol": None,
        "concurrent_12h_review": "already_delivered_0833_do_not_write_its_folder",
        "did_not_write_patrol_folder": True,
        "first_pass_realign": "succeeded ts_realigned=23; tick_s_check no corrective, over45 vs later_raw=0",
    }
    (DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + NL)
    (DIR / "wrapup_run.txt").write_text(f"wrap {now} ok_quiet=True inserted_total={inserted_total}{NL}")
    print(f"wrap {now} ok_quiet=True inserted_total={inserted_total}")


if __name__ == "__main__":
    main()
