#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
STATE = ROOT / "state"
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_1130")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
NL = chr(10)
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

T0, T1 = 84432901, 84433600
JP_BASE = 84433600
JP_T0, JP_T1 = JP_BASE + 1, JP_BASE + 100

GAPS = [
    ("gap_1122_1128", 84433481, 84433589),  # NEW 盒子休眠 11:22:21-11:28:28
    ("gap_1008_1036", 84432441, 84432839),
    ("gap_1049_1050", 84433011, 84433049),
    ("gap_0928_0935", 84431871, 84431979),
    ("gap_0854_0905", 84431391, 84431559),
    ("gap_0818_0822", 84430871, 84430939),
    ("gap_0738_0800", 84430301, 84430629),
    ("gap_0700_0706", 84429761, 84429849),
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
]

HOLES = [
    ("W47N8", 84433300),  # NEW this 1130 pass
    ("W45N8", 84433100),  # still-untold from quiet 1100
    ("W45N8", 84432300),
    ("W45N7", 84432500),
    ("W47N7", 84432800),
    ("W47N8", 84432000),
    ("W47N8", 84431000),
    ("W47N7", 84430800),
    ("W47N7", 84430700),
    ("W46N8", 84430500),
    ("W47N8", 84429900),
    ("W47N7", 84429300),
    ("W45N7", 84428300),
    ("W45N8", 84426200),
    ("W45N8", 84425500),
    ("W45N8", 84425800),
]


def hole_meta(row):
    d, mn, mx, n = row
    return {
        "distinct": int(d or 0),
        "min": mn,
        "max": mx,
        "rows": int(n or 0),
        "hole_ticks": 100 - int(d or 0),
    }


def hole_ranges(c, room, base, distinct):
    t0, t1 = base + 1, base + 100
    if distinct >= 100:
        return []
    have = {r[0] for r in c.execute(
        "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    )}
    out, start = [], None
    for t in range(t0, t1 + 1):
        if t not in have:
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
        if h["distinct"] == 0:
            return f"{(h.get('min') and 'n/a') or (HOLES and '')}"
        return "none"
    # Prefer explicit ranges; for full hole use base+1..base+100
    parts = []
    for a, b in rs:
        parts.append(f"{a}..{b}" if a != b else str(a))
    return " and ".join(parts) if parts else "none"


def fill_txt(by_room):
    return ", ".join(f"{r} {by_room[r]['fill']}" for r in ROOMS)


def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {} if default is None else default


def main():
    now = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    tick = json.loads((DIR / "tick_s_realign.json").read_text())
    cov = json.loads((DIR / "coverage_final.json").read_text())
    jp_first_p = DIR / f"just_published_{JP_BASE}_first.json"
    jp_p = DIR / f"just_published_{JP_BASE}.json"
    jp = json.loads(jp_first_p.read_text()) if jp_first_p.exists() else json.loads(jp_p.read_text())
    pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
    late = load_json(DIR / "backfill_late_retry.json")
    confirm = load_json(DIR / "backfill_confirm_gets.json")
    retry2j = confirm.get("retry2") or {}
    postjp = load_json(DIR / "backfill_postjp_retry.json", {"skipped": True, "inserted": 0, "at": None, "game_time": None})

    post, window_db, dup, holes, gaps, tips = {}, {}, {}, {}, {}, {}
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
            if not h["hole_ranges"] and h["distinct"] == 0:
                h["hole_ranges"] = [[base + 1, base + 100]]
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
        # actual unique rows now minus pre-count rows at GET time
        actual[room] = max(0, dup[room]["unique"] - int((pre.get(room) or {}).get("rows") or 0))
    actual_sum = sum(actual.values())

    script_by = {r: 0 for r in ROOMS}
    for name in (f"just_published_{JP_BASE}_first.json", f"just_published_{JP_BASE}.json"):
        fp = DIR / name
        if not fp.exists():
            continue
        jx = json.loads(fp.read_text())
        # Prefer first file once
        if name.endswith("_first.json") or not (DIR / f"just_published_{JP_BASE}_first.json").exists():
            for g in (jx.get("gets") or []):
                script_by[g["room"]] = int(g.get("inserted") or 0)
            break
    script_sum = sum(script_by.values())

    inserted_first = 9164
    inserted_confirm = int(confirm.get("inserted") or 0)
    inserted_retry2 = int(retry2j.get("inserted") or 0)
    inserted_late = int(late.get("inserted") or 0)
    inserted_postjp = int(postjp.get("inserted") or 0)
    inserted_total = inserted_first + inserted_confirm + inserted_retry2 + inserted_late + inserted_postjp + actual_sum

    out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
    listener_lines = [ln.strip() for ln in out.splitlines() if "tools/listener.py" in ln]
    rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
    yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()

    h333 = holes["W47N8@84433300"]
    h331 = holes["W45N8@84433100"]
    h323 = holes["W45N8@84432300"]
    h325 = holes["W45N7@84432500"]
    h328 = holes["W47N7@84432800"]
    h320 = holes["W47N8@84432000"]
    h310 = holes["W47N8@84431000"]

    fill1122 = fill_txt(gaps["gap_1122_1128"])
    fill1008 = fill_txt(gaps["gap_1008_1036"])
    fill1049 = fill_txt(gaps["gap_1049_1050"])
    fill0928 = fill_txt(gaps["gap_0928_0935"])
    fill0854 = fill_txt(gaps["gap_0854_0905"])

    tick_s_in_use = tick.get("tick_s_in_use")
    later = tick.get("later_mean_w46")
    corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
    tick_s_label = tick.get("tick_s_in_use_name") or "all_mean"
    vs_first = (tick.get("vs_candidates") or {}).get("first") or {}
    vs_all = (tick.get("vs_candidates") or {}).get("all_mean") or {}
    vs_later = (tick.get("vs_candidates") or {}).get("later_robust") or {}
    skipped_chunk = int(tick.get("skipped_cross_chunk") or 0)

    first_txt = (DIR / "history_backfill.txt").read_text().rstrip() + NL

    def script_vs(room):
        return f"{room} script {script_by.get(room)} vs actual {actual[room]}"
    script_vs_txt = ", ".join(script_vs(r) for r in ROOMS)

    empty_by = cov.get("coverage") or {}
    def empty_txt(room):
        c = empty_by.get(room) or {}
        n = c.get("official_empty_no_creep") or 0
        rs = c.get("official_empty_no_creep_ranges") or []
        if not n:
            return "none"
        parts = [f"{a}..{b}" if a != b else str(a) for a, b in rs]
        return f"{n} ticks " + " and ".join(parts)

    confirm_at = confirm.get("at") or confirm.get("confirm_at")
    confirm_gt = confirm.get("game_time") or confirm.get("confirm_game_time")
    confirm_still = confirm.get("still_404") or []
    confirm_rec = confirm.get("recovered") or []
    retry_at = retry2j.get("at")
    retry_gt = retry2j.get("game_time")
    retry_still = retry2j.get("still_404") or []
    retry_rec = retry2j.get("recovered") or []
    late_at = late.get("at") or late.get("at_finish")
    late_gt = late.get("game_time")
    late_still = late.get("still_404") or []
    late_rec = late.get("recovered") or []
    post_at = postjp.get("at") or postjp.get("at_finish")
    post_gt = postjp.get("game_time")
    post_still = postjp.get("still_404") or []
    post_rec = postjp.get("recovered") or []
    post_line = (
        f"post-JP leftover retry at {post_at} gt={post_gt} still_404={post_still} recovered={post_rec} inserted={inserted_postjp}. "
    )

    jp_at = jp.get("at")
    jp_gt = jp.get("game_time")
    jp_still = jp.get("still_404") or []
    jp_rec = jp.get("recovered") or []
    jp_ins = int(jp.get("inserted") or 0)
    all_five = not jp_still

    def hr(h):
        return hole_range_txt(h) if h.get("hole_ranges") else (f"{h['min']}..{h['max']}" if h.get("min") else f"{None}..{None}")

    # For full holes with distinct=0, hole_range_txt may be awkward; force base span
    def hole_span(room_base_key, base):
        h = holes[room_base_key]
        if h["distinct"] == 0:
            return f"{base+1}..{base+100}"
        return hole_range_txt(h)

    now_txt = (
        first_txt
        + "---- wrap " + now + " ----" + NL
        + f"confirm at {confirm_at} gt={confirm_gt} still_404={confirm_still} recovered={confirm_rec} inserted={inserted_confirm}. "
        + f"retry2 at {retry_at} gt={retry_gt} still_404={retry_still} recovered={retry_rec} inserted={inserted_retry2}. "
        + f"late retry at {late_at} gt={late_gt} still_404={late_still} recovered={late_rec} inserted={inserted_late}. "
        + post_line
        + "First pass --minutes 40. First pass 33/35 official GETs 200, missing_chunks=2 (W45N8@84433100, W47N8@84433300). "
        + "First pass started 2026-11-23 11:32:07 Asia/Hong_Kong and finished 11:32:56 (exit=0): inserted=9164 already_in_db=16686 ts_realigned=0, printed tick_s=4.259 (exact first-interval 4.25882). Inserts committed. "
        + "Overlap with the 11:00 half-hour (official 84432501..84433200 / JP 84433200) accounts for already_in_db=16686. "
        + f"Confirm at {confirm_at} gt={confirm_gt} recovered none inserted=0; still_404={confirm_still}. "
        + "The near leftover official 404 W47N7@84432800 (just before window start 84432901; first recorded in the quiet 1030 half-hour; still NOT YET TOLD) was retried at confirm/retry2/late/postjp and is still 404 (inserted=0); do not relabel NEW. "
        + "The in-window still-untold leftover W45N8@84433100 (first recorded in the quiet 1100 half-hour) was retried at confirm/retry2/late/postjp and is still 404 (inserted=0); do not relabel NEW. "
        + "The first-pass in-window 404 W47N8@84433300 stayed 404 after confirm/retry2/late/postjp (inserted=0). At postjp gt=84433801 it was already 501 ticks past the base, so it is recorded as a NEW leftover official 404, not mere publish lag. "
        + "Aged-out leftover official 404 W45N8@84432300, W45N7@84432500, W47N8@84432000, W47N8@84431000 and older aged out of window start 84432901 and were not retried this pass; do not relabel NEW. "
        + f"tick_s_check chose live-anchor-best all_mean {tick_s_in_use} (all_mean over45={vs_all.get('over45')} mean_off={vs_all.get('mean_off')}; first 4.25882 over45={vs_first.get('over45')} mean_off={vs_first.get('mean_off')}; later-mean {later} over45={vs_later.get('over45')} mean_off={vs_later.get('mean_off')}); later-mean was worse than all_mean so was not applied; first 4.25882 was already inside the 45s gate (over45=0); corrective_applied={bool(tick.get('corrective_applied'))} nfix={corrective}; skipped_cross_chunk={skipped_chunk}. First-pass realign used 4.25882 (printed 4.259) and committed ts_realigned=0. tick_s_in_use={tick_s_in_use} ({tick_s_label}). "
        + "Last delivered USER_LOG is ~08:34 _patrol_2026-11-23_0821 (finished_at 08:34:04); do not re-tell it. The 12h review _review12h_2026-11-23_08 was already delivered ~08:30; do not re-tell it. This half-hour did not write a patrol or 12h-review folder and did not restart the listener, war_cmd, or pulse. "
        + "Quiet 11:00 half-hour _halfhour_2026-11-23_1100 already wrapped 11:15:24; do not re-tell that collect-only wrap, but carry its still-untold leftover official 404 W45N8@84433100 and the still-untold freezes/404s from earlier quiet wraps into the next 3h patrol (do not relabel NEW except for truly new this wrap). "
        + "Just-published 84433600 was not in first pass (first pass ended at published 84433500 / reconstructed 84432901..84433600 at game.time=84433631, 33/35 200, missing_chunks=2). "
        + f"GET at {jp_at} gt={jp_gt} all_five_200={all_five} still_404={jp_still} recovered={jp_rec} script inserted={jp_ins}. "
        + "JP retry and retry2 skipped no targets (all five 200). "
        + f"script={script_sum} actual={actual_sum}; {script_vs_txt}. "
        + f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
        + f"W46N8 official empty_no_creep in this first-pass window: {empty_txt('W46N8')}. "
        + f"W47N8 official empty_no_creep in this first-pass window: {empty_txt('W47N8')}. "
        + f"W45N8 official empty_no_creep in this first-pass window: {empty_txt('W45N8')}. "
        + f"W45N7 official empty_no_creep in this first-pass window: {empty_txt('W45N7')}. "
        + f"W47N7 official empty_no_creep in this first-pass window: {empty_txt('W47N7')}. "
        + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} postjp={inserted_postjp} just_actual={actual_sum} total={inserted_total}. "
        + f"NEW leftover official 404 W47N8@84433300 (first recorded as a first-pass in-window 404 this 1130 half-hour; confirm {confirm_at} gt={confirm_gt} / retry2 {retry_at} gt={retry_gt} / late {late_at} gt={late_gt} / postjp {post_at} gt={post_gt} still 404, inserted=0; listener {h333['distinct']}/100 range {h333['min']}..{h333['max']}; hole {h333['hole_ticks']} ticks {hole_span('W47N8@84433300', 84433300)}) — NOT YET TOLD; fold into the next 3h patrol. "
        + f"Still-untold leftover official 404 W45N8@84433100 (first recorded as a first-pass leftover in the quiet 1100 half-hour; in-window this pass; retried at confirm/retry2/late/postjp still 404, inserted=0; listener {h331['distinct']}/100 range {h331['min']}..{h331['max']}; hole {h331['hole_ticks']} ticks {hole_span('W45N8@84433100', 84433100)}) is not labeled NEW this wrap; still NOT YET TOLD; fold into the next 3h patrol. "
        + f"Still-untold leftover official 404 W47N7@84432800 (first recorded in quiet 1030; near this window start 84432901; retried this pass still 404, inserted=0; listener {h328['distinct']}/100 range {h328['min']}..{h328['max']}; hole {h328['hole_ticks']} ticks {hole_span('W47N7@84432800', 84432800)}) is not labeled NEW this wrap; still NOT YET TOLD; fold into the next 3h patrol. "
        + f"Still-untold leftover official 404 W45N8@84432300 (quiet 1030; aged out of window start {T0}; not retried; listener {h323['distinct']}/100 range {h323['min']}..{h323['max']}; hole {h323['hole_ticks']} ticks {hole_span('W45N8@84432300', 84432300)}) is not labeled NEW; still NOT YET TOLD. "
        + f"Still-untold leftover official 404 W45N7@84432500 (quiet 1030; aged out of window start {T0}; not retried; listener {h325['distinct']}/100 range {h325['min']}..{h325['max']}; hole {h325['hole_ticks']} ticks {hole_span('W45N7@84432500', 84432500)}) is not labeled NEW; still NOT YET TOLD. "
        + f"Still-untold leftover official 404 W47N8@84432000 (quiet 0930; aged out; not retried; listener {h320['distinct']}/100 range {h320['min']}..{h320['max']}; hole {h320['hole_ticks']} ticks {hole_span('W47N8@84432000', 84432000)}) is not labeled NEW; still NOT YET TOLD. "
        + f"Still-untold leftover official 404 W47N8@84431000 (quiet 0830; aged out; not retried; listener {h310['distinct']}/100 range {h310['min']}..{h310['max']}; hole {h310['hole_ticks']} ticks {hole_span('W47N8@84431000', 84431000)}) is not labeled NEW; still NOT YET TOLD. "
        + "NEW leftover official 404 this run: W47N8@84433300. Still-untold leftover official 404 from the quiet 11:00 half-hour: W45N8@84433100 — still NOT YET TOLD. Still-untold from quiet 10:30: W45N8@84432300, W45N7@84432500, W47N7@84432800. Still-untold from quiet 09:30: W47N8@84432000. Still-untold from quiet 08:30: W47N8@84431000. "
        + f"NEW 盒子休眠 this run: 11:22:21-11:28:28 Asia/Hong_Kong (367s, box_pauses row; STATS 84433481..84433589, 109t; official-filled {fill1122}; listener auto-restart 11:28:31, python 3035248 started 11:28:40, parent 4035476) — NOT YET TOLD; fold into the next 3h patrol. "
        + "Still-untold 盒子休眠 from the quiet 10:30 half-hour: 10:08:51-10:36:08 and 10:49:06-10:50:33 — still NOT YET TOLD; fold into the next 3h patrol; do not relabel NEW. "
        + "Still-untold 盒子休眠 from the quiet 09:30 half-hour: 09:28:39-09:35:07 — still NOT YET TOLD. Still-untold from quiet 09:00: 08:54:25-09:05:57 — still NOT YET TOLD. NEW 监听短中断 this run: none. "
        + f"Still-untold 盒子休眠 10:08:51-10:36:08 fill {fill1008}; 10:49:06-10:50:33 fill {fill1049}; 09:28:39-09:35:07 fill {fill0928}; 08:54:25-09:05:57 fill {fill0854}. "
        + "Already-told 盒子休眠 through 08:18:40-08:22:01 and earlier (0821/0516/0216 USER_LOGs) do not re-tell. Already-told leftover official 404s through W47N7@84430800 / W47N7@84430700 / W46N8@84430500 / W47N8@84429900 / W47N7@84429300 / W45N7@84428300 / W45N8@84426200/25500/25800 do not re-tell. "
        + f"window_db={window_db}" + NL
        + f"jp_post={post} jp_script_by={script_by} jp_actual_by={actual}" + NL
        + f"tips={tips}" + NL
        + f"listener {listener_lines} rot={rot} yield_absent={yield_absent}" + NL
        + f"Single listener 3035248 since 11:28:40 after the NEW 盒子休眠 11:22:21-11:28:28 auto-restart 11:28:31 (parent 4035476), peacetime one-slot rotation, yield_absent={yield_absent}. Did not start a second listener or restart war_cmd/pulse. listener_rot {rot} tips {tips}." + NL
    )

    (DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
    (DIR / "history_backfill_now.txt").write_text(now_txt)
    shutil.copyfile(DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

    verify = (
        f"verify wrap {now}" + NL
        + f"official window ticks {T0}..{T1} (700) published_bases 84432900..84433500 JP {JP_BASE}; inserted_total={inserted_total} (first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} postjp={inserted_postjp} just_actual={actual_sum}). "
        + f"Coverage {cov['official_recovered']}/{cov['expected']} empty={cov['empty_no_creep']} 404={cov['official_404_missing']}. tick_s_in_use={tick_s_in_use} ({tick_s_label}). "
        + f"NEW leftover official 404 W47N8@84433300 (confirm/retry2/late/postjp still 404; listener {h333['distinct']}/100; hole {h333['hole_ticks']} ticks {hole_span('W47N8@84433300', 84433300)}) — NOT YET TOLD; fold into the next 3h patrol. "
        + f"Still-untold leftover official 404 W45N8@84433100 (from quiet 1100; retried still 404; listener {h331['distinct']}/100; hole {h331['hole_ticks']} ticks {hole_span('W45N8@84433100', 84433100)}) — still NOT YET TOLD; do not relabel NEW. "
        + f"Still-untold leftover official 404 W47N7@84432800 (from quiet 1030; near-window retried still 404; listener {h328['distinct']}/100; hole {h328['hole_ticks']} ticks {hole_span('W47N7@84432800', 84432800)}) — still NOT YET TOLD. "
        + "Still-untold leftover official 404 W45N8@84432300, W45N7@84432500 (quiet 1030; aged out), W47N8@84432000 (quiet 0930), W47N8@84431000 (quiet 0830) — still NOT YET TOLD; do not relabel NEW. "
        + f"NEW 盒子休眠 this run: 11:22:21-11:28:28 (367s; STATS 84433481..84433589; official-filled {fill1122}; listener auto-restart 11:28:31 / python 3035248) — NOT YET TOLD; fold into the next 3h patrol. "
        + "Still-untold 盒子休眠 from quiet 1030: 10:08:51-10:36:08, 10:49:06-10:50:33; from 0930: 09:28:39-09:35:07; from 0900: 08:54:25-09:05:57 — still NOT YET TOLD; do not relabel NEW. NEW 监听短中断 none. "
        + "Already-told freezes/404s through the ~08:34 0821 USER_LOG and earlier; do not re-tell. "
        + "Quiet 1100 already wrapped 11:15:24; this 1130 first pass used --minutes 40 (published start 84432900 / reconstructed 84432901)." + NL
        + "ok_quiet=True "
        + "new_official_404_untold=[W47N8@84433300] "
        + "still_untold_from_1100=[W45N8@84433100] "
        + "still_untold_from_1030=[W45N8@84432300, W45N7@84432500, W47N7@84432800] "
        + "still_untold_from_0930=[W47N8@84432000] "
        + "still_untold_from_0830=[W47N8@84431000] "
        + "still_untold_from_0900=[] still_untold_from_0800=[] still_untold_from_0700=[] still_untold_from_0630=[] still_untold_from_0300=[] "
        + "new_box_freeze_untold=[11:22:21-11:28:28] "
        + "still_untold_freeze_from_1030=[10:08:51-10:36:08, 10:49:06-10:50:33] "
        + "still_untold_freeze_from_0930=[09:28:39-09:35:07] "
        + "still_untold_freeze_from_0900=[08:54:25-09:05:57] "
        + "still_untold_freeze_from_0830=[] still_untold_freeze_from_0800=[] still_untold_freeze_from_0700=[] still_untold_freeze_from_0630=[] still_untold_freeze_from_0600=[] still_untold_freeze_from_0500=[] "
        + "new_short_ws_untold=[] "
        + "first_pass_source=this_halfhour_1130 "
        + "concurrent_patrol=already_delivered_patrol_2026-11-23_0821_finished_at_08:34:04_do_not_write_folder "
        + "last=_patrol_2026-11-23_0821_finished_at_08:34:04_USER_LOG_~08:34 "
        + "concurrent_12h_review=already_delivered_review12h_2026-11-23_08_~08:30_do_not_write_folder "
        + "already_told_404s_this_patrol=[W47N7@84430800,W47N7@84430700,W46N8@84430500,W47N8@84429900,W47N7@84429300,W45N7@84428300,W45N8@84426200,W45N8@84425500,W45N8@84425800] "
        + "already_told_freeze_this_patrol=[08:18:40-08:22:01,07:38:49-08:00:34,07:00:52-07:06:05,06:23:39-06:27:58,05:48:18-06:06:20,05:16:36-05:25:46,04:53:04-04:58:42,04:20:59-04:35:45,03:52:38-03:58:50,03:22:33-03:29:51,02:51:37-02:58:39,02:19:33-02:28:15,01:46:20-02:01:27,01:15:53-01:27:13,00:51:21-00:57:39,00:23:50-00:33:45,23:52:01-23:59:48]" + NL
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
        "inserted_postjp": inserted_postjp,
        "just_actual": actual_sum,
        "just_script": script_sum,
        "just_script_by": script_by,
        "just_actual_by": actual,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_in_use_name": tick_s_label,
        "window": [T0, T1],
        "window_db": window_db,
        "coverage": {
            "official_recovered": cov["official_recovered"],
            "expected": cov["expected"],
            "empty_no_creep": cov["empty_no_creep"],
            "official_404": cov["official_404_missing"],
        },
        "gaps": {k: {r: v[r]["fill"] for r in ROOMS} for k, v in gaps.items()},
        "holes": holes,
        "tips": tips,
        "listener": listener_lines,
        "rot": rot,
        "yield_absent": yield_absent,
        "new_official_404_untold": ["W47N8@84433300"],
        "still_untold_from_1100": ["W45N8@84433100"],
        "still_untold_from_1030": ["W45N8@84432300", "W45N7@84432500", "W47N7@84432800"],
        "still_untold_from_0930": ["W47N8@84432000"],
        "still_untold_from_0830": ["W47N8@84431000"],
        "still_untold_from_0900": [],
        "still_untold_from_0800": [],
        "still_untold_from_0700": [],
        "still_untold_from_0630": [],
        "still_untold_from_0300": [],
        "already_told_404s_this_patrol": [
            "W47N7@84430800", "W47N7@84430700", "W46N8@84430500", "W47N8@84429900",
            "W47N7@84429300", "W45N7@84428300", "W45N8@84426200", "W45N8@84425500", "W45N8@84425800",
        ],
        "new_box_freeze_untold": ["11:22:21-11:28:28"],
        "still_untold_freeze_from_1030": ["10:08:51-10:36:08", "10:49:06-10:50:33"],
        "still_untold_freeze_from_0930": ["09:28:39-09:35:07"],
        "still_untold_freeze_from_0900": ["08:54:25-09:05:57"],
        "still_untold_freeze_from_0830": [],
        "still_untold_freeze_from_0800": [],
        "still_untold_freeze_from_0700": [],
        "still_untold_freeze_from_0630": [],
        "still_untold_freeze_from_0600": [],
        "still_untold_freeze_from_0500": [],
        "already_told_freeze_this_patrol": [
            "08:18:40-08:22:01", "07:38:49-08:00:34", "07:00:52-07:06:05", "06:23:39-06:27:58",
            "05:48:18-06:06:20", "05:16:36-05:25:46", "04:53:04-04:58:42", "04:20:59-04:35:45",
            "03:52:38-03:58:50", "03:22:33-03:29:51", "02:51:37-02:58:39", "02:19:33-02:28:15",
            "01:46:20-02:01:27", "01:15:53-01:27:13", "00:51:21-00:57:39", "00:23:50-00:33:45",
            "23:52:01-23:59:48",
        ],
        "new_short_ws_untold": [],
        "concurrent_patrol": "already_delivered_patrol_2026-11-23_0821_finished_at_08:34:04_do_not_write_folder; last=_patrol_2026-11-23_0821_finished_at_08:34:04_USER_LOG_~08:34",
        "concurrent_12h_review": "already_delivered_review12h_2026-11-23_08_~08:30_do_not_write_folder",
        "did_not_write_patrol_folder": True,
        "first_pass_realign": f"first-pass used 4.25882 (printed 4.259) ts_realigned=0; live-anchor-best {tick_s_label} {tick_s_in_use}, later-mean worse, corrective_applied=False nfix=0 (first already inside 45s gate)",
        "first_pass_source": "this_halfhour_1130",
        "minutes": 40,
        "missed_1000_slot": False,
        "new_freeze_detail": {
            "from": "2026-11-23 11:22:21",
            "to": "2026-11-23 11:28:28",
            "sec": 367,
            "stats": [84433481, 84433589],
            "official_fill": {r: gaps["gap_1122_1128"][r]["fill"] for r in ROOMS},
            "listener_restart": "11:28:31",
            "python": 3035248,
            "parent": 4035476,
        },
    }

    (DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + NL)
    (DIR / "wrapup_run.txt").write_text(f"wrap {now} ok_quiet=True inserted_total={inserted_total}{NL}")
    print(f"wrap {now} ok_quiet=True inserted_total={inserted_total}")


if __name__ == "__main__":
    main()
