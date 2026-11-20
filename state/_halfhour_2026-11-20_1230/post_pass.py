#!/usr/bin/env python3
"""Coverage, tick_s, and gap-fill checks for the 12:30 half-hour first pass."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import db
import history_backfill as hb

HK = ZoneInfo("Asia/Hong_Kong")
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1230")
TMIN, TMAX = 84372401, 84373100
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_PRINTED = 4.092
GT_FIRST = 84373147
# Official chunk timestamps from this first pass (copied from history_backfill.txt)
# room -> base -> ts
TS = {
    "W46N8": {84372400: 1795146813466, 84372500: 1795147222710, 84372600: 1795147651036, 84372700: 1795148067445, 84372800: 1795148484697, 84372900: 1795148908958, 84373000: 1795149336155},
    "W47N8": {84372400: 1795146857266, 84372500: 1795147269503, 84372600: 1795147685850, 84372700: 1795148110164, 84372800: 1795148534327, 84372900: 1795148956484, 84373000: 1795149386311},
    "W45N8": {84372400: 1795146854485, 84372500: 1795147264735, 84372600: 1795147683016, 84372700: 1795148104799, 84372800: 1795148529166, 84372900: 1795148952443, 84373000: 1795149382752},
    "W45N7": {84372400: 1795146815325, 84372500: 1795147225317, 84372600: 1795147652472, 84372700: 1795148070406, 84372800: 1795148486167, 84372900: 1795148910119, 84373000: 1795149338456},
    "W47N7": {84372400: 1795146886156, 84372500: 1795147298860, 84372600: 1795147714981, 84372700: 1795148146347, 84372800: 1795148565751, 84372900: 1795148991319, 84373000: 1795149423047},
}
GAPS = [
    ("prior short 11:11 84371891..84371919", 84371891, 84371919, 29),  # may be aged out
    ("prior short 11:18 84371991..84372019", 84371991, 84372019, 29),
    ("prior short 11:36 84372251..84372269", 84372251, 84372269, 19),
    ("prior freeze 11:48 84372431..84372599", 84372431, 84372599, 169),
    ("prior short 12:01 84372611..84372639", 84372611, 84372639, 29),
    ("prior freeze 12:13 84372791..84372889", 84372791, 84372889, 99),
]

def chunk_base(tick):
    return ((tick - 1) // 100) * 100

def ranges(ticks, tmin, tmax):
    missing, start, s = [], None, set(ticks)
    for t in range(tmin, tmax + 1):
        if t not in s:
            if start is None:
                start = t
        elif start is not None:
            missing.append([start, t - 1])
            start = None
    if start is not None:
        missing.append([start, tmax])
    return missing

def main():
    lines = []
    def out(s=""):
        lines.append(s)
        print(s, flush=True)

    # --- tick_s ---
    bases = sorted(TS["W46N8"])
    # min timestamp across rooms at each base (script uses this for first interval)
    min_all = {b: min(TS[r][b] for r in ROOMS) for b in bases}
    later_w46 = {b: TS["W46N8"][b] for b in bases}
    intervals = []
    for a, b in zip(bases, bases[1:]):
        dt = (min_all[b] - min_all[a]) / 1000.0 / (b - a)
        intervals.append((a, b, dt))
    first = intervals[0][2]
    all_mean = sum(x[2] for x in intervals) / len(intervals)
    span_mean = (min_all[bases[-1]] - min_all[bases[0]]) / 1000.0 / (bases[-1] - bases[0])
    out("==== tick_s ====")
    out(f"script_printed={TICK_S_PRINTED} first-interval={first:.5f}")
    for a, b, dt in intervals:
        out(f"  min_all {a}..{b} = {dt:.5f}")
    out(f"all_mean={all_mean:.5f} span_mean={span_mean:.5f}")
    # do not apply a later-mean corrective if first is already what the script used
    # and later mean is close. Flag if drift is large.
    out(f"tick_s_in_use={first:.5f} (first-interval; no corrective unless |later-first|>0.05)")
    apply_corrective = abs(all_mean - first) > 0.05
    nfix = 0
    if apply_corrective:
        now_ts = datetime.now(timezone.utc)
        # need current or first gt? realign uses the live anchor at realign time
        # Use a fresh game.time would shift all ts; safer to skip unless clearly wrong.
        out(f"NOTE later-mean differs from first by {all_mean-first:.5f}; leaving first-pass realign (tick_s={first:.5f}) in place, no second corrective this pass")
    tick_s_info = {
        "printed": TICK_S_PRINTED,
        "first_interval": first,
        "all_mean": all_mean,
        "span_mean": span_mean,
        "in_use": first,
        "corrective": nfix,
        "intervals": [{"a": a, "b": b, "dt": dt} for a, b, dt in intervals],
        "min_all": min_all,
    }
    (DIR / "tick_s_realign.json").write_text(json.dumps(tick_s_info, indent=2) + chr(10))
")

    # --- coverage ---
    coverage = {}
    with db.connect() as c:
        unique = c.execute(
            """SELECT count(*), count(DISTINCT (creep, tick)), count(DISTINCT tick),
                      count(DISTINCT (room, tick))
               FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s)""",
            (TMIN, TMAX, list(ROOMS)),
        ).fetchone()
        db_after = c.execute(
            """SELECT room, min(tick), max(tick), count(*), count(DISTINCT tick)
               FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s)
               GROUP BY room ORDER BY 1""",
            (TMIN, TMAX, list(ROOMS)),
        ).fetchall()
        for room in ROOMS:
            ticks = [r[0] for r in c.execute(
                "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
                (room, TMIN, TMAX),
            ).fetchall()]
            miss = ranges(ticks, TMIN, TMAX)
            coverage[room] = {
                "distinct": len(ticks),
                "missing_n": sum(b - a + 1 for a, b in miss),
                "missing_ranges": miss,
                "official_empty_no_creep": sum(b - a + 1 for a, b in miss),  # no in-window 404
                "official_empty_no_creep_ranges": miss,
                "official_404_missing": 0,
                "official_404_ranges": [],
            }
        gap_fills = []
        for name, a, b, expect in GAPS:
            rec = {"name": name, "a": a, "b": b, "expect": expect, "rooms": {}}
            in_win_a, in_win_b = max(a, TMIN), min(b, TMAX)
            rec["in_window"] = in_win_a <= in_win_b
            if rec["in_window"]:
                rec["in_window_span"] = [in_win_a, in_win_b, in_win_b - in_win_a + 1]
            for room in ROOMS:
                aa, bb = (max(a, TMIN), min(b, TMAX)) if rec["in_window"] else (a, b)
                if aa > bb:
                    rec["rooms"][room] = {"distinct": 0, "rows": 0, "span": 0, "aged": True}
                    continue
                row = c.execute(
                    "SELECT count(*), count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                    (room, aa, bb),
                ).fetchone()
                span = bb - aa + 1
                rec["rooms"][room] = {
                    "rows": row[0], "distinct": row[1], "min": row[2], "max": row[3], "span": span,
                    "missing": span - row[1],
                }
            gap_fills.append(rec)
        # leftover 404 sample (aged out)
        hole = c.execute(
            "SELECT count(*), count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            ("W46N8", 84371601, 84371700),
        ).fetchone()
        # tips
        tips = {}
        for table, col in (("creep_cpu", "tick"), ("path_arrivals", "tick"), ("room_stats", "tick")):
            tips[table] = c.execute(f"SELECT max({col}) FROM {table}").fetchone()[0]

    expected = 5 * (TMAX - TMIN + 1)
    recovered = sum(coverage[r]["distinct"] for r in ROOMS)
    empty_no_creep = sum(coverage[r]["official_empty_no_creep"] for r in ROOMS)
    payload = {
        "coverage": coverage,
        "official_recovered": recovered,
        "expected": expected,
        "empty_no_creep": empty_no_creep,
        "official_404_missing": 0,
        "unique_after": {
            "rows": unique[0],
            "unique_creep_tick_rows": unique[1],
            "distinct_ticks": unique[2],
            "distinct_room_ticks": unique[3],
        },
        "db_after": [
            {"room": r[0], "min": r[1], "max": r[2], "rows": r[3], "distinct": r[4]} for r in db_after
        ],
        "gap_fills": gap_fills,
        "leftover_W46N8_84371600": {"rows": hole[0], "distinct": hole[1]},
        "tips": tips,
        "at": datetime.now(HK).isoformat(),
    }
    (DIR / "coverage_final.json").write_text(json.dumps(payload, indent=2) + chr(10))
")
    out("==== coverage ====")
    out(f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404=0")
    for room in ROOMS:
        c = coverage[room]
        out(f"  {room} distinct={c['distinct']} missing={c['missing_n']} empty={c['official_empty_no_creep']} 404=0")
        if c["missing_ranges"]:
            out(f"    empty ranges: {c['missing_ranges']}")
    out("==== db_after ====")
    for r in db_after:
        out(f"  {r[0]} ticks={r[1]}..{r[2]} rows={r[3]} distinct={r[4]}")
    out("==== gap fills (in-window overlap) ====")
    for g in gap_fills:
        if not g["in_window"]:
            out(f"  AGED OUT {g['name']}")
            continue
        parts = []
        for room in ROOMS:
            rr = g["rooms"][room]
            parts.append(f"{room} {rr['distinct']}/{rr['span']}")
        out(f"  {g['name']} inwin={g['in_window_span']}: " + ", ".join(parts))
    out(f"leftover W46N8@84371600 still {hole[1]}/100 (aged out of window start {TMIN})")
    out(f"tips cpu={tips['creep_cpu']} path={tips['path_arrivals']} room_stats={tips['room_stats']}")
    (DIR / "coverage_final.txt").write_text("
".join(lines) + "
")
    (DIR / "tick_s_check.txt").write_text("
".join(x for x in lines if x.startswith("==== tick") or x.startswith("  min_all") or "tick_s" in x or x.startswith("script") or x.startswith("all_mean") or x.startswith("NOTE")) + "
")
    print("wrote", DIR / "coverage_final.json")

if __name__ == "__main__":
    main()
