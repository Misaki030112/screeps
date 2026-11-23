#!/usr/bin/env python3
import os, sys, json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import db as dbmod
from psycopg.rows import dict_row

OUT = "/workspace/screeps/state/_review12h_2026-11-23_08"
START_TICK = 84420960  # last successful 12h review tip ~2026-11-22 08:24 HKT
CAP = 10935000
HKT = ZoneInfo("Asia/Hong_Kong")

os.chdir("/workspace/screeps")
conn = dbmod.connect()
cur = conn.cursor(row_factory=dict_row)

def run(name, sql, args=None):
    cur.execute(sql, args or {})
    rows = cur.fetchall()
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        if not rows:
            f.write("(no rows)\n")
            return rows
        keys = list(rows[0].keys())
        f.write("\t".join(keys) + "\n")
        for r in rows:
            vals = []
            for k in keys:
                v = r[k]
                vals.append("" if v is None else str(v))
            f.write("\t".join(vals) + "\n")
    with open(path + ".json", "w") as f:
        json.dump(rows, f, indent=2, default=str)
    return rows

tip = run("sql_tip.txt", """
SELECT room, min(tick) FILTER (WHERE tick>=%(s)s) AS win_min_tick,
       max(tick) AS max_tick,
       min(ts) FILTER (WHERE tick>=%(s)s) AS win_min_ts,
       max(ts) AS max_ts,
       count(*) FILTER (WHERE tick>=%(s)s) AS n_win
FROM room_stats
WHERE room IN ('W46N8','W47N8')
GROUP BY room
ORDER BY room;
""", {"s": START_TICK})

end_ticks = [r["max_tick"] for r in tip]
END_TICK = min(end_ticks) if end_ticks else START_TICK
# snap to a 10-tick cadence if needed
if END_TICK % 10:
    END_TICK = END_TICK - (END_TICK % 10)

params = {"s": START_TICK, "e": END_TICK, "cap": CAP}

# wall / tick_s from shared first/last
bounds = run("sql_first_last_ts.txt", """
SELECT min(ts) AS first_ts, max(ts) AS last_ts,
       min(tick) AS first_tick, max(tick) AS last_tick,
       count(*) AS n, count(DISTINCT tick) AS n_ticks
FROM room_stats
WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s;
""", params)
b = bounds[0] if bounds else {}
first_ts, last_ts = b.get("first_ts"), b.get("last_ts")
wall_s = None
tick_s = None
ticks = END_TICK - START_TICK
if first_ts and last_ts:
    wall_s = (last_ts - first_ts).total_seconds()
    tick_s = wall_s / ticks if ticks else None

with open(os.path.join(OUT, "sql_window.txt"), "w") as f:
    f.write(f"START_TICK={START_TICK}\n")
    f.write(f"END_TICK={END_TICK}\n")
    f.write(f"TICKS={ticks}\n")
    f.write(f"CAP={CAP}\n")
    f.write(f"first_ts={first_ts}\n")
    f.write(f"last_ts={last_ts}\n")
    f.write(f"wall_s={wall_s}\n")
    f.write(f"wall_h={None if wall_s is None else wall_s/3600}\n")
    f.write(f"tick_s={tick_s}\n")
    f.write(f"n_rows_both={b.get('n')}\n")
    f.write(f"n_distinct_ticks={b.get('n_ticks')}\n")

# Hourly
run("sql_hourly.txt", """
SELECT room,
       date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour_hkt,
       min(tick) AS tick_min, max(tick) AS tick_max,
       min(progress) AS progress_min, max(progress) AS progress_max,
       max(progress)-min(progress) AS progress_span,
       avg(storage)::numeric(12,2) AS stor_avg,
       min(storage) AS stor_min, max(storage) AS stor_max,
       avg(cpu)::numeric(12,3) AS cpu_avg,
       count(*) AS n
FROM room_stats
WHERE room IN ('W46N8','W47N8')
  AND tick >= %(s)s AND tick <= %(e)s
GROUP BY room, date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong')
ORDER BY room, hour_hkt;
""", params)

# Per-room window summary
run("sql_room_window.txt", """
WITH bounds AS (
  SELECT room,
         (ARRAY_AGG(progress ORDER BY tick ASC))[1] AS first_progress,
         (ARRAY_AGG(progress ORDER BY tick DESC))[1] AS last_progress,
         min(tick) AS first_tick, max(tick) AS last_tick,
         (ARRAY_AGG(ts ORDER BY tick ASC))[1] AS first_ts,
         (ARRAY_AGG(ts ORDER BY tick DESC))[1] AS last_ts,
         avg(storage)::numeric(18,8) AS stor_avg,
         min(storage) AS stor_min, max(storage) AS stor_max,
         count(*) AS n,
         count(*) FILTER (WHERE storage < 15000) AS n_under15,
         count(*) FILTER (WHERE storage >= 20000) AS n_ge20,
         count(*) FILTER (WHERE storage >= 25000) AS n_ge25,
         count(*) FILTER (WHERE storage >= 30000) AS n_ge30,
         count(*) FILTER (WHERE storage >= 40000) AS n_ge40
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
  GROUP BY room
),
ext AS (
  SELECT b.*,
         (last_tick - first_tick) AS ticks,
         (last_progress - first_progress) AS delta
  FROM bounds b
)
SELECT room, first_tick, last_tick, ticks, first_ts, last_ts,
       first_progress, last_progress, delta,
       CASE WHEN ticks>0 THEN (delta::numeric / ticks) ELSE NULL END AS e_per_t,
       (last_progress::numeric / %(cap)s * 100) AS pct_of_cap,
       (%(cap)s - last_progress) AS remaining,
       stor_avg, stor_min, stor_max,
       n, n_under15, n_ge20, n_ge25, n_ge30, n_ge40,
       (n_under15::numeric / n * 100) AS pct_under15,
       (n_ge20::numeric / n * 100) AS pct_ge20,
       (n_ge25::numeric / n * 100) AS pct_ge25,
       (n_ge30::numeric / n * 100) AS pct_ge30,
       (n_ge40::numeric / n * 100) AS pct_ge40
FROM ext
ORDER BY room;
""", params)

# previous 12h window exact compare (2026-11-22 08:24→2026-11-22 20:30)
run("sql_morning_window.txt", """
WITH bounds AS (
  SELECT room,
         (ARRAY_AGG(progress ORDER BY tick ASC))[1] AS first_progress,
         (ARRAY_AGG(progress ORDER BY tick DESC))[1] AS last_progress,
         min(tick) AS first_tick, max(tick) AS last_tick,
         (ARRAY_AGG(ts ORDER BY tick ASC))[1] AS first_ts,
         (ARRAY_AGG(ts ORDER BY tick DESC))[1] AS last_ts,
         avg(storage)::numeric(18,8) AS stor_avg,
         min(storage) AS stor_min, max(storage) AS stor_max,
         count(*) AS n,
         count(*) FILTER (WHERE storage < 15000) AS n_under15,
         count(*) FILTER (WHERE storage >= 20000) AS n_ge20,
         count(*) FILTER (WHERE storage >= 25000) AS n_ge25,
         count(*) FILTER (WHERE storage >= 30000) AS n_ge30,
         count(*) FILTER (WHERE storage >= 40000) AS n_ge40
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= 84410500 AND tick <= 84420960
  GROUP BY room
)
SELECT room, first_tick, last_tick, (last_tick-first_tick) AS ticks, first_ts, last_ts,
       first_progress, last_progress, (last_progress-first_progress) AS delta,
       CASE WHEN last_tick>first_tick THEN ((last_progress-first_progress)::numeric / (last_tick-first_tick)) END AS e_per_t,
       (last_progress::numeric / 10935000 * 100) AS pct_of_cap,
       stor_avg, stor_min, stor_max, n,
       n_under15, n_ge20, n_ge25, n_ge30, n_ge40,
       (n_under15::numeric / n * 100) AS pct_under15,
       (n_ge20::numeric / n * 100) AS pct_ge20,
       (n_ge25::numeric / n * 100) AS pct_ge25,
       (n_ge30::numeric / n * 100) AS pct_ge30,
       (n_ge40::numeric / n * 100) AS pct_ge40
FROM bounds
ORDER BY room;
""")

run("sql_stor_minmax.txt", """
WITH base AS (
  SELECT room, tick, ts, storage
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
),
agg AS (
  SELECT room, min(storage) AS stor_min, max(storage) AS stor_max FROM base GROUP BY room
)
SELECT b.room,
       a.stor_min,
       (SELECT min(tick) FROM base x WHERE x.room=b.room AND x.storage=a.stor_min) AS min_first_tick,
       (SELECT min(ts) FROM base x WHERE x.room=b.room AND x.storage=a.stor_min) AS min_first_ts,
       (SELECT max(tick) FROM base x WHERE x.room=b.room AND x.storage=a.stor_min) AS min_last_tick,
       (SELECT max(ts) FROM base x WHERE x.room=b.room AND x.storage=a.stor_min) AS min_last_ts,
       a.stor_max,
       (SELECT min(tick) FROM base x WHERE x.room=b.room AND x.storage=a.stor_max) AS max_first_tick,
       (SELECT min(ts) FROM base x WHERE x.room=b.room AND x.storage=a.stor_max) AS max_first_ts,
       (SELECT max(tick) FROM base x WHERE x.room=b.room AND x.storage=a.stor_max) AS max_last_tick,
       (SELECT max(ts) FROM base x WHERE x.room=b.room AND x.storage=a.stor_max) AS max_last_ts
FROM (SELECT DISTINCT room FROM base) b
JOIN agg a ON a.room=b.room
ORDER BY b.room;
""", params)

# Stretches: break when sample gap >20 ticks (more than one missed 10-tick slot)
# kinds: under15, ge20, ge25, ge30, ge40
run("sql_stor_stretches.txt", """
WITH base AS (
  SELECT room, tick, ts, storage,
         CASE WHEN storage < 15000 THEN 1 ELSE 0 END AS under15,
         CASE WHEN storage >= 20000 THEN 1 ELSE 0 END AS ge20,
         CASE WHEN storage >= 25000 THEN 1 ELSE 0 END AS ge25,
         CASE WHEN storage >= 30000 THEN 1 ELSE 0 END AS ge30,
         CASE WHEN storage >= 40000 THEN 1 ELSE 0 END AS ge40
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
),
ord AS (
  SELECT *, lag(tick) OVER (PARTITION BY room ORDER BY tick) AS prev_tick
  FROM base
),
marked AS (
  SELECT *, CASE WHEN prev_tick IS NULL OR tick - prev_tick > 20 THEN 1 ELSE 0 END AS brk
  FROM ord
),
grp AS (
  SELECT *, sum(brk) OVER (PARTITION BY room ORDER BY tick) AS gap_id
  FROM marked
),
lagged AS (
  SELECT *,
         lag(under15) OVER (PARTITION BY room, gap_id ORDER BY tick) AS prev_under15,
         lag(ge20) OVER (PARTITION BY room, gap_id ORDER BY tick) AS prev_ge20,
         lag(ge25) OVER (PARTITION BY room, gap_id ORDER BY tick) AS prev_ge25,
         lag(ge30) OVER (PARTITION BY room, gap_id ORDER BY tick) AS prev_ge30,
         lag(ge40) OVER (PARTITION BY room, gap_id ORDER BY tick) AS prev_ge40
  FROM grp
),
flag15 AS (
  SELECT *, under15 AS flag,
         sum(CASE WHEN under15 IS DISTINCT FROM prev_under15 THEN 1 ELSE 0 END)
           OVER (PARTITION BY room, gap_id ORDER BY tick) AS flid
  FROM lagged
),
flag20 AS (
  SELECT *, ge20 AS flag,
         sum(CASE WHEN ge20 IS DISTINCT FROM prev_ge20 THEN 1 ELSE 0 END)
           OVER (PARTITION BY room, gap_id ORDER BY tick) AS flid
  FROM lagged
),
flag25 AS (
  SELECT *, ge25 AS flag,
         sum(CASE WHEN ge25 IS DISTINCT FROM prev_ge25 THEN 1 ELSE 0 END)
           OVER (PARTITION BY room, gap_id ORDER BY tick) AS flid
  FROM lagged
),
flag30 AS (
  SELECT *, ge30 AS flag,
         sum(CASE WHEN ge30 IS DISTINCT FROM prev_ge30 THEN 1 ELSE 0 END)
           OVER (PARTITION BY room, gap_id ORDER BY tick) AS flid
  FROM lagged
),
flag40 AS (
  SELECT *, ge40 AS flag,
         sum(CASE WHEN ge40 IS DISTINCT FROM prev_ge40 THEN 1 ELSE 0 END)
           OVER (PARTITION BY room, gap_id ORDER BY tick) AS flid
  FROM lagged
),
agg15 AS (
  SELECT room, 'under15' AS kind, min(tick) AS t0, max(tick) AS t1, min(ts) AS ts0, max(ts) AS ts1,
         (max(tick)-min(tick)+1) AS tick_span, count(*) AS n, min(storage) AS stor_min, max(storage) AS stor_max
  FROM flag15 WHERE flag=1 GROUP BY room, gap_id, flid
),
agg20 AS (
  SELECT room, 'ge20' AS kind, min(tick) AS t0, max(tick) AS t1, min(ts) AS ts0, max(ts) AS ts1,
         (max(tick)-min(tick)+1) AS tick_span, count(*) AS n, min(storage) AS stor_min, max(storage) AS stor_max
  FROM flag20 WHERE flag=1 GROUP BY room, gap_id, flid
),
agg25 AS (
  SELECT room, 'ge25' AS kind, min(tick) AS t0, max(tick) AS t1, min(ts) AS ts0, max(ts) AS ts1,
         (max(tick)-min(tick)+1) AS tick_span, count(*) AS n, min(storage) AS stor_min, max(storage) AS stor_max
  FROM flag25 WHERE flag=1 GROUP BY room, gap_id, flid
),
agg30 AS (
  SELECT room, 'ge30' AS kind, min(tick) AS t0, max(tick) AS t1, min(ts) AS ts0, max(ts) AS ts1,
         (max(tick)-min(tick)+1) AS tick_span, count(*) AS n, min(storage) AS stor_min, max(storage) AS stor_max
  FROM flag30 WHERE flag=1 GROUP BY room, gap_id, flid
),
agg40 AS (
  SELECT room, 'ge40' AS kind, min(tick) AS t0, max(tick) AS t1, min(ts) AS ts0, max(ts) AS ts1,
         (max(tick)-min(tick)+1) AS tick_span, count(*) AS n, min(storage) AS stor_min, max(storage) AS stor_max
  FROM flag40 WHERE flag=1 GROUP BY room, gap_id, flid
),
allst AS (
  SELECT * FROM agg15 UNION ALL SELECT * FROM agg20 UNION ALL SELECT * FROM agg25
  UNION ALL SELECT * FROM agg30 UNION ALL SELECT * FROM agg40
)
SELECT * FROM allst
ORDER BY room, kind, tick_span DESC, t0;
""", params)

# CPU
run("sql_cpu.txt", """
SELECT
  count(*) AS n,
  avg(cpu)::numeric(12,6) AS cpu_avg,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY cpu)::numeric(12,6) AS cpu_p95,
  max(cpu) AS cpu_max,
  min(bucket) AS bucket_min,
  max(bucket) AS bucket_max,
  avg(bucket)::numeric(12,4) AS bucket_avg,
  count(*) FILTER (WHERE cpu >= 40) AS n_cpu_ge40
FROM room_stats
WHERE room='W46N8' AND tick >= %(s)s AND tick <= %(e)s;
""", params)

run("sql_cpu_spikes.txt", """
SELECT tick, ts, cpu, bucket, commit, room
FROM room_stats
WHERE room='W46N8' AND tick >= %(s)s AND tick <= %(e)s AND cpu >= 40
ORDER BY tick;
""", params)

run("sql_cpu_top.txt", """
SELECT tick, ts, cpu, bucket, commit
FROM room_stats
WHERE room='W46N8' AND tick >= %(s)s AND tick <= %(e)s
ORDER BY cpu DESC, tick
LIMIT 15;
""", params)

run("sql_sites_summary.txt", """
WITH s AS (
  SELECT room, tick, ts, sites
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
)
SELECT room,
  (SELECT sites FROM s x WHERE x.room=s.room ORDER BY tick ASC LIMIT 1) AS first_sites,
  (SELECT tick FROM s x WHERE x.room=s.room ORDER BY tick ASC LIMIT 1) AS first_tick,
  (SELECT sites FROM s x WHERE x.room=s.room ORDER BY tick DESC LIMIT 1) AS last_sites,
  (SELECT tick FROM s x WHERE x.room=s.room ORDER BY tick DESC LIMIT 1) AS last_tick,
  (SELECT max(tick) FROM s x WHERE x.room=s.room AND x.sites>0) AS last_nonzero_tick,
  (SELECT max(ts) FROM s x WHERE x.room=s.room AND x.sites>0) AS last_nonzero_ts,
  (SELECT sites FROM s x WHERE x.room=s.room AND x.sites>0 ORDER BY tick DESC LIMIT 1) AS last_nonzero_sites,
  (SELECT min(tick) FROM s x WHERE x.room=s.room AND x.sites=0) AS first_zero_tick,
  (SELECT min(ts) FROM s x WHERE x.room=s.room AND x.sites=0) AS first_zero_ts,
  count(*) FILTER (WHERE sites=0) AS n_zero,
  count(*) FILTER (WHERE sites>0) AS n_nonzero,
  min(sites) AS sites_min, max(sites) AS sites_max
FROM s
GROUP BY room
ORDER BY room;
""", params)

run("sql_sites_changes.txt", """
WITH s AS (
  SELECT room, tick, ts, sites,
         lag(sites) OVER (PARTITION BY room ORDER BY tick) AS prev
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
)
SELECT room, tick, ts, prev AS sites_prev, sites
FROM s
WHERE prev IS DISTINCT FROM sites
ORDER BY room, tick;
""", params)

run("sql_commits.txt", """
SELECT commit, min(tick) AS t0, max(tick) AS t1, min(ts) AS ts0, max(ts) AS ts1, count(*) AS n
FROM room_stats
WHERE room='W46N8' AND tick >= %(s)s AND tick <= %(e)s
GROUP BY commit
ORDER BY t0;
""", params)

run("sql_deploys.txt", """
SELECT ts, tick, commit, note
FROM deploys
ORDER BY ts DESC
LIMIT 10;
""")

run("sql_gaps.txt", """
WITH s AS (
  SELECT room, tick, ts, lag(tick) OVER (PARTITION BY room ORDER BY tick) AS prev,
         lag(ts) OVER (PARTITION BY room ORDER BY tick) AS prev_ts
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
)
SELECT room, prev AS gap_from, tick AS gap_to, (tick-prev-1) AS missing, prev_ts AS ts_from, ts AS ts_to
FROM s
WHERE prev IS NOT NULL AND tick-prev > 20
ORDER BY (tick-prev) DESC, room, tick;
""", params)

run("sql_first_last_rows.txt", """
(SELECT room, tick, ts, rcl, progress, progress_total, energy, energy_cap, sites, hostiles, safe_mode, cpu, bucket, gcl_progress, creeps, commit, storage, ctl, ctl_ema
 FROM room_stats WHERE room='W46N8' AND tick>=%(s)s AND tick<=%(e)s ORDER BY tick ASC LIMIT 1)
UNION ALL
(SELECT room, tick, ts, rcl, progress, progress_total, energy, energy_cap, sites, hostiles, safe_mode, cpu, bucket, gcl_progress, creeps, commit, storage, ctl, ctl_ema
 FROM room_stats WHERE room='W46N8' AND tick>=%(s)s AND tick<=%(e)s ORDER BY tick DESC LIMIT 1)
UNION ALL
(SELECT room, tick, ts, rcl, progress, progress_total, energy, energy_cap, sites, hostiles, safe_mode, cpu, bucket, gcl_progress, creeps, commit, storage, ctl, ctl_ema
 FROM room_stats WHERE room='W47N8' AND tick>=%(s)s AND tick<=%(e)s ORDER BY tick ASC LIMIT 1)
UNION ALL
(SELECT room, tick, ts, rcl, progress, progress_total, energy, energy_cap, sites, hostiles, safe_mode, cpu, bucket, gcl_progress, creeps, commit, storage, ctl, ctl_ema
 FROM room_stats WHERE room='W47N8' AND tick>=%(s)s AND tick<=%(e)s ORDER BY tick DESC LIMIT 1);
""", params)

run("sql_hostiles.txt", """
SELECT room, tick, ts, hostiles, storage, sites, progress
FROM room_stats
WHERE room IN ('W46N8','W47N8','W45N8','W45N7','W47N7')
  AND tick >= %(s)s AND tick <= %(e)s AND hostiles > 0
ORDER BY tick, room;
""", params)

run("sql_incidents_full.txt", """
SELECT ts, tick, remote, inc, ev, from_state, state, why, inv, inv_ttl, def, dur, data
FROM incidents
WHERE tick >= %(s)s AND tick <= %(e)s
ORDER BY tick, remote, ev;
""", params)

run("sql_incidents.txt", """
SELECT remote, inc,
       min(tick) AS t0, max(tick) AS t1, (max(tick)-min(tick)) AS tick_span,
       min(ts) AS ts0, max(ts) AS ts1,
       max(dur) AS max_dur,
       (ARRAY_AGG(ev ORDER BY tick)) AS evs,
       (ARRAY_AGG(DISTINCT def) FILTER (WHERE def IS NOT NULL)) AS defs,
       (ARRAY_AGG(why ORDER BY tick) FILTER (WHERE why IS NOT NULL)) AS whys,
       (ARRAY_AGG(state ORDER BY tick)) AS states
FROM incidents
WHERE tick >= %(s)s AND tick <= %(e)s
GROUP BY remote, inc
ORDER BY t0, remote;
""", params)

run("sql_alerts.txt", """
SELECT ts, tick, kind, room, severity, episode, msg, data
FROM events
WHERE kind LIKE 'alert%%' AND tick >= %(s)s AND tick <= %(e)s
ORDER BY tick, kind;
""", params)

run("sql_box_pauses.txt", """
SELECT ts, tick, kind, room, msg, data
FROM events
WHERE kind='box_pause' AND ts >= (
  SELECT min(ts) FROM room_stats WHERE room='W46N8' AND tick>=%(s)s
) AND ts <= (
  SELECT max(ts) FROM room_stats WHERE room='W46N8' AND tick<=%(e)s
)
ORDER BY ts;
""", params)

run("sql_event_kinds.txt", """
SELECT kind, count(*) AS n, min(tick) AS t0, max(tick) AS t1
FROM events
WHERE tick >= %(s)s AND tick <= %(e)s
GROUP BY kind
ORDER BY n DESC;
""", params)

# coverage
expected_slots = (END_TICK - START_TICK) // 10 + 1
run("sql_coverage.txt", """
SELECT room, count(*) AS n,
       count(DISTINCT tick) AS n_ticks,
       min(tick) AS t0, max(tick) AS t1
FROM room_stats
WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
GROUP BY room;
""", params)


run("sql_home_ge20k.txt", """
WITH s AS (
  SELECT tick, ts, storage,
         tick - 10 * ROW_NUMBER() OVER (ORDER BY tick) AS grp
  FROM room_stats
  WHERE room='W46N8' AND tick >= %(s)s AND tick <= %(e)s AND storage >= 20000
)
SELECT min(tick) AS t0, max(tick) AS t1, (max(tick)-min(tick)) AS dt,
       min(ts) AS ts0, max(ts) AS ts1, count(*) AS n,
       min(storage) AS stor_min, max(storage) AS stor_max
FROM s GROUP BY grp ORDER BY t0;
""", params)

run("sql_w47_ge40k.txt", """
WITH s AS (
  SELECT tick, ts, storage,
         tick - 10 * ROW_NUMBER() OVER (ORDER BY tick) AS grp
  FROM room_stats
  WHERE room='W47N8' AND tick >= %(s)s AND tick <= %(e)s AND storage >= 40000
)
SELECT min(tick) AS t0, max(tick) AS t1, (max(tick)-min(tick)) AS dt,
       min(ts) AS ts0, max(ts) AS ts1, count(*) AS n,
       min(storage) AS stor_min, max(storage) AS stor_max
FROM s GROUP BY grp ORDER BY t0;
""", params)

run("sql_w47_lt22k.txt", """
WITH s AS (
  SELECT tick, ts, storage,
         tick - 10 * ROW_NUMBER() OVER (ORDER BY tick) AS grp
  FROM room_stats
  WHERE room='W47N8' AND tick >= %(s)s AND tick <= %(e)s AND storage < 22000
)
SELECT min(tick) AS t0, max(tick) AS t1, (max(tick)-min(tick)) AS dt,
       min(ts) AS ts0, max(ts) AS ts1, count(*) AS n,
       min(storage) AS stor_min, max(storage) AS stor_max
FROM s GROUP BY grp ORDER BY t0;
""", params)

print(f"SQL done END_TICK={END_TICK} ticks={ticks} tick_s={tick_s} wall_h={None if wall_s is None else wall_s/3600}")
conn.close()
