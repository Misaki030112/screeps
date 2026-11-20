#!/usr/bin/env python3
"""Compute 12h review rates, short windows, 24h recap. Writes computed_metrics.txt."""
import json, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, "/workspace/screeps/tools")
import db as dbmod

OUT = Path("/workspace/screeps/state/_review12h_2026-11-20_20")
HKT = ZoneInfo("Asia/Hong_Kong")
CAP = 10935000
IDEAL = {"W46N8": 26.0, "W47N8": 30.08}
# Window from sql_window.txt (written by _sql.py)
_win = dict(line.split("=",1) for line in (OUT / "sql_window.txt").read_text().splitlines() if "=" in line)
START = int(_win["START_TICK"])
WIN_END = int(_win["END_TICK"])
PREV_FIRST = 84359020  # previous 12h review start (2026-11-19 20:27 / this morning's window start)
PREV_END = START

conn = dbmod.connect()

def q(sql, args=None):
    cur = conn.cursor()
    cur.execute(sql, args or ())
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    return [dict(zip(cols, r)) for r in rows]

def to_hkt(ts):
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(HKT)

lines = []
def p(s=""):
    lines.append(s)
    print(s)

# window bounds already known; re-read for safety
b = q("""
SELECT min(ts) AS first_ts, max(ts) AS last_ts,
       min(tick) AS first_tick, max(tick) AS last_tick,
       count(*) FILTER (WHERE room='W46N8') AS n_home
FROM room_stats
WHERE room IN ('W46N8','W47N8') AND tick >= %s AND tick <= %s
""", (START, WIN_END))[0]

first_ts, last_ts = b["first_ts"], b["last_ts"]
wall_s = (last_ts - first_ts).total_seconds()
ticks = WIN_END - START
tick_s = wall_s / ticks
expected_slots = ticks // 10 + 1
coverage = 100.0 * b["n_home"] / expected_slots

p(f"computed official window t{START}→{WIN_END} (first/last samples)")
p(f"wall {to_hkt(first_ts)} → {to_hkt(last_ts)} Asia/Hong_Kong")
p(f"ticks_sampled={ticks} wall_s={wall_s:.2f} wall_h={wall_s/3600:.3f} tick_s={tick_s:.4f}")
p(f"expected_10t_slots={expected_slots} n_samples/room={b['n_home']} coverage_pct={coverage:.1f}")
p(f"(first and last samples sit on START/END, so tick_s=wall_s/ticks is valid; shard sped up vs last evening 4.6936)")

# room window already in sql_room_window; recompute eta
rooms = q("""
WITH bounds AS (
  SELECT room,
         (ARRAY_AGG(progress ORDER BY tick ASC))[1] AS first_progress,
         (ARRAY_AGG(progress ORDER BY tick DESC))[1] AS last_progress,
         min(tick) AS first_tick, max(tick) AS last_tick,
         avg(storage)::float AS stor_avg,
         min(storage) AS stor_min, max(storage) AS stor_max,
         count(*) AS n,
         count(*) FILTER (WHERE storage < 15000) AS n_under15,
         count(*) FILTER (WHERE storage >= 20000) AS n_ge20,
         count(*) FILTER (WHERE storage >= 25000) AS n_ge25,
         count(*) FILTER (WHERE storage >= 30000) AS n_ge30,
         count(*) FILTER (WHERE storage >= 40000) AS n_ge40
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %s AND tick <= %s
  GROUP BY room
)
SELECT * FROM bounds ORDER BY room
""", (START, WIN_END))

etas = {}
for r in rooms:
    dt = r["last_tick"] - r["first_tick"]
    delta = r["last_progress"] - r["first_progress"]
    et = delta / dt
    pct = 100.0 * r["last_progress"] / CAP
    remain = CAP - r["last_progress"]
    eta = remain / et * tick_s / 86400
    etas[r["room"]] = eta
    p(f"{r['room']} first={r['first_progress']} last={r['last_progress']} delta={delta} e_per_t={et:.4f} pct={pct:.4f} remaining={remain} eta_days={eta:.2f}")
    p(f"  stor_avg={r['stor_avg']:.2f} min={r['stor_min']} max={r['stor_max']} n={r['n']} under15={r['n_under15']}={100*r['n_under15']/r['n']:.2f}% ge20={r['n_ge20']}={100*r['n_ge20']/r['n']:.2f}% ge25={r['n_ge25']}={100*r['n_ge25']/r['n']:.2f}% ge30={r['n_ge30']}={100*r['n_ge30']/r['n']:.2f}% ge40={r['n_ge40']}={100*r['n_ge40']/r['n']:.2f}%")

p(f"last evening tick_s was 4.6936; this window tick_s {tick_s:.4f} (shard faster — calendar tightens even if e/t slowed)")

# Interpolated exact windows ending at tip
def interp_at(room, tip_tick, tip_ts, tip_p, wall_s, ideal):
    target_ts = tip_ts - timedelta(seconds=wall_s)
    rows = q("""
        SELECT tick, ts, progress, storage FROM room_stats
        WHERE room=%s AND ts BETWEEN %s AND %s
        ORDER BY ts
    """, (room, target_ts - timedelta(hours=1), target_ts + timedelta(hours=1)))
    before = [r for r in rows if r["ts"] <= target_ts]
    after = [r for r in rows if r["ts"] >= target_ts]
    if not before or not after:
        return None
    a, b = before[-1], after[0]
    if a["ts"] == b["ts"]:
        frac, itick, ip = 0.0, a["tick"], a["progress"]
    else:
        frac = (target_ts - a["ts"]).total_seconds() / (b["ts"] - a["ts"]).total_seconds()
        itick = a["tick"] + frac * (b["tick"] - a["tick"])
        ip = a["progress"] + frac * (b["progress"] - a["progress"])
    dt = tip_tick - itick
    dprog = tip_p - ip
    et = dprog / dt if dt else 0
    shard_st = wall_s / dt if dt else 0
    pct = 100 * et / ideal if ideal else 0
    return dict(itick=itick, ip=ip, dt=dt, dprog=dprog, et=et, pct=pct, shard_st=shard_st, target_ts=target_ts)

tips = {}
for room in ("W46N8", "W47N8"):
    row = q("SELECT tick, ts, progress, storage FROM room_stats WHERE room=%s AND tick=%s", (room, WIN_END))[0]
    tips[room] = row
    p(f"TIP {room} t{row['tick']} {to_hkt(row['ts'])} p={row['progress']} stor={row['storage']}")
    for label, ws in (("exact2h", 7200), ("1h", 3600), ("3h", 10800), ("6h", 21600)):
        r = interp_at(room, row["tick"], row["ts"], row["progress"], ws, IDEAL[room])
        if not r:
            p(f"  {room} {label} INTERP FAILED")
            continue
        p(f"  {room} {label} INTERP dt={r['dt']:.1f} dprog={r['dprog']:.1f} {r['et']:.2f}/{IDEAL[room]}={r['pct']:.1f}% shard_s/t={r['shard_st']:.3f} start_tick={r['itick']:.1f} {to_hkt(r['target_ts'])}")

# short windows at tip
p("short windows at tip:")
for room in ("W46N8", "W47N8"):
    rows = q("""
        SELECT tick, ts, progress, storage FROM room_stats
        WHERE room=%s AND tick<=%s ORDER BY tick DESC LIMIT 250
    """, (room, WIN_END))
    rows = list(reversed(rows))
    tip = rows[-1]
    for span in (20, 30, 70, 100, 140, 200, 300, 500, 800, 1500):
        start_cands = [r for r in rows if r["tick"] >= tip["tick"] - span]
        start = start_cands[0] if start_cands else rows[0]
        dt = tip["tick"] - start["tick"]
        if dt <= 0:
            continue
        et = (tip["progress"] - start["progress"]) / dt
        pct = 100 * et / IDEAL[room]
        n = sum(1 for r in rows if start["tick"] <= r["tick"] <= tip["tick"])
        p(f"  {room} last{span}t (n={n} span={dt}) {et:.2f} e/t {pct:.1f}% stor {start['storage']}->{tip['storage']} t{start['tick']}->{tip['tick']}")

# 24h recap: wall 24h ending at tip. First sample at/after tip_ts-24h, or nearest.
p("24h recap (wall 24h ending at tip, plus since last evening sampled start 84350530):")
for room in ("W46N8", "W47N8"):
    tip = tips[room]
    target = tip["ts"] - timedelta(hours=24)
    # first sample >= target
    row = q("""
        SELECT tick, ts, progress, storage FROM room_stats
        WHERE room=%s AND ts >= %s
        ORDER BY ts ASC LIMIT 1
    """, (room, target))
    if row:
        s = row[0]
        dt = tip["tick"] - s["tick"]
        dprog = tip["progress"] - s["progress"]
        et = dprog / dt if dt else 0
        wall = (tip["ts"] - s["ts"]).total_seconds()
        p(f"  {room} 24h-from-first-sample t{s['tick']}→{tip['tick']} ({to_hkt(s['ts'])} → {to_hkt(tip['ts'])}) ticks={dt} wall_h={wall/3600:.2f} delta={dprog} e_per_t={et:.2f} start_stor={s['storage']}")
    # extremes in wall 24h
    ext = q("""
        SELECT min(storage) AS stor_min, max(storage) AS stor_max,
               count(*) AS n,
               count(*) FILTER (WHERE storage < 15000) AS n_u15,
               count(*) FILTER (WHERE storage >= 20000) AS n20,
               count(*) FILTER (WHERE storage >= 40000) AS n40
        FROM room_stats WHERE room=%s AND ts >= %s AND tick <= %s
    """, (room, target, WIN_END))[0]
    p(f"    24h samples n={ext['n']} min={ext['stor_min']} max={ext['stor_max']} under15={ext['n_u15']}={100*ext['n_u15']/ext['n']:.2f}% ge20={ext['n20']} ge40={ext['n40']}")
    # when max/min
    mx = q("""
        SELECT tick, ts, storage FROM room_stats
        WHERE room=%s AND ts >= %s AND tick <= %s AND storage = %s
        ORDER BY tick LIMIT 1
    """, (room, target, WIN_END, ext["stor_max"]))[0]
    mn = q("""
        SELECT tick, ts, storage FROM room_stats
        WHERE room=%s AND ts >= %s AND tick <= %s AND storage = %s
        ORDER BY tick LIMIT 1
    """, (room, target, WIN_END, ext["stor_min"]))[0]
    p(f"    24h max {mx['storage']} @ t{mx['tick']} {to_hkt(mx['ts'])}; min {mn['storage']} @ t{mn['tick']} {to_hkt(mn['ts'])}")

# since last evening sampled window start (84350530) through now (~23h from 09:23)
p("since last evening sampled start t84350530→84369500 (~23h from 09:23 11-19):")
for room in ("W46N8", "W47N8"):
    s = q("SELECT tick, ts, progress, storage FROM room_stats WHERE room=%s AND tick=%s", (room, PREV_FIRST))[0]
    tip = tips[room]
    dt = tip["tick"] - s["tick"]
    dprog = tip["progress"] - s["progress"]
    et = dprog / dt
    wall = (tip["ts"] - s["ts"]).total_seconds()
    pct = 100.0 * tip["progress"] / CAP
    p(f"  {room} t{s['tick']}→{tip['tick']} ticks={dt} wall_h={wall/3600:.2f} start_p={s['progress']} end_p={tip['progress']} delta={dprog} e_per_t={et:.2f} end_pct={pct:.2f}")

# hourly tick_s from consecutive hour first/last samples (home)
p("hourly tick_s (W46N8 first/last sample of each clock hour):")
hrs = q("""
SELECT date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour_hkt,
       min(tick) AS t0, max(tick) AS t1,
       min(ts) AS ts0, max(ts) AS ts1,
       count(*) AS n
FROM room_stats
WHERE room='W46N8' AND tick >= %s AND tick <= %s
GROUP BY 1
ORDER BY 1
""", (START, WIN_END))
for h in hrs:
    dt = h["t1"] - h["t0"]
    wall = (h["ts1"] - h["ts0"]).total_seconds()
    ts_h = wall / dt if dt else None
    p(f"  {h['hour_hkt']} t{h['t0']}-{h['t1']} n={h['n']} dt={dt} wall_s={wall:.1f} tick_s={ts_h:.3f}" if ts_h else f"  {h['hour_hkt']} n={h['n']} insufficient")

# CPU already known
cpu = q("""
SELECT count(*) AS n, avg(cpu)::float AS cpu_avg,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY cpu)::float AS cpu_p95,
       max(cpu) AS cpu_max, min(bucket) AS bucket_min,
       count(*) FILTER (WHERE cpu>=40) AS n40
FROM room_stats
WHERE room='W46N8' AND tick >= %s AND tick <= %s
""", (START, WIN_END))[0]
p(f"CPU 12h n={cpu['n']} avg={cpu['cpu_avg']:.2f} p95={cpu['cpu_p95']:.2f} max={cpu['cpu_max']} bucket_min={cpu['bucket_min']} n_cpu>=40={cpu['n40']}")

# box pause total already computed externally; record n from events
p("done")

(OUT / "computed_metrics.txt").write_text("\n".join(lines) + "\n")
print("wrote", OUT / "computed_metrics.txt")
conn.close()
