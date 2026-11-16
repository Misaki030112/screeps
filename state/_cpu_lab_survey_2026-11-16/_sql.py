#!/usr/bin/env python3
import os, json
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db as dbmod
from psycopg.rows import dict_row

OUT = "/workspace/screeps/state/_cpu_lab_survey_2026-11-16"
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
        else:
            keys = list(rows[0].keys())
            f.write("\t".join(keys) + "\n")
            for r in rows:
                f.write("\t".join("" if r[k] is None else str(r[k]) for k in keys) + "\n")
    with open(path + ".json", "w") as f:
        json.dump(rows, f, indent=2, default=str)
    print(f"{name}: {len(rows)} rows")
    return rows

# Coverage / tip
run("sql_tip.txt", """
SELECT room,
       max(tick) AS max_tick,
       min(ts) FILTER (WHERE ts > now()-interval '12 hours') AS min_ts_12h,
       max(ts) AS max_ts,
       count(*) FILTER (WHERE ts > now()-interval '1 hour') AS n_1h,
       count(*) FILTER (WHERE ts > now()-interval '3 hours') AS n_3h,
       count(*) FILTER (WHERE ts > now()-interval '6 hours') AS n_6h,
       count(*) FILTER (WHERE ts > now()-interval '12 hours') AS n_12h
FROM room_stats
WHERE room IN ('W46N8','W47N8')
GROUP BY room ORDER BY room;
""")

# CPU histograms and percentiles for 1/3/6/12h, W46N8 only (colony cpu duplicated)
run("sql_cpu_windows.txt", """
WITH base AS (
  SELECT ts, tick, cpu, bucket, trace_cpu, hostiles, storage, creeps
  FROM room_stats
  WHERE room='W46N8' AND ts > now()-interval '12 hours'
),
wins AS (
  SELECT '1h'::text AS win, interval '1 hour' AS iv
  UNION ALL SELECT '3h', interval '3 hours'
  UNION ALL SELECT '6h', interval '6 hours'
  UNION ALL SELECT '12h', interval '12 hours'
)
SELECT w.win,
       count(*) AS n,
       min(b.ts) AS first_ts, max(b.ts) AS last_ts,
       min(b.tick) AS first_tick, max(b.tick) AS last_tick,
       round(avg(b.cpu)::numeric, 3) AS cpu_avg,
       round((percentile_cont(0.50) WITHIN GROUP (ORDER BY b.cpu))::numeric, 3) AS cpu_p50,
       round((percentile_cont(0.90) WITHIN GROUP (ORDER BY b.cpu))::numeric, 3) AS cpu_p90,
       round((percentile_cont(0.95) WITHIN GROUP (ORDER BY b.cpu))::numeric, 3) AS cpu_p95,
       round((percentile_cont(0.99) WITHIN GROUP (ORDER BY b.cpu))::numeric, 3) AS cpu_p99,
       round(min(b.cpu)::numeric, 3) AS cpu_min,
       round(max(b.cpu)::numeric, 3) AS cpu_max,
       min(b.bucket) AS bucket_min,
       round(avg(b.bucket)::numeric, 1) AS bucket_avg,
       max(b.bucket) AS bucket_max,
       count(*) FILTER (WHERE b.cpu > 20) AS n_gt20,
       count(*) FILTER (WHERE b.cpu > 18) AS n_gt18,
       count(*) FILTER (WHERE b.cpu >= 20) AS n_ge20,
       count(*) FILTER (WHERE b.cpu < 15) AS n_lt15,
       count(*) FILTER (WHERE b.cpu < 16) AS n_lt16,
       count(*) FILTER (WHERE b.cpu BETWEEN 16 AND 18) AS n_16_18,
       count(*) FILTER (WHERE b.cpu > 25) AS n_gt25,
       count(*) FILTER (WHERE b.cpu > 40) AS n_gt40,
       round((100.0*count(*) FILTER (WHERE b.cpu > 20)/count(*))::numeric, 2) AS pct_gt20,
       round((100.0*count(*) FILTER (WHERE b.cpu > 18)/count(*))::numeric, 2) AS pct_gt18,
       round((100.0*count(*) FILTER (WHERE b.cpu < 15)/count(*))::numeric, 2) AS pct_lt15,
       round(avg(b.trace_cpu)::numeric, 3) AS trace_avg,
       max(b.trace_cpu) AS trace_max,
       max(b.hostiles) AS host_max,
       count(*) FILTER (WHERE b.hostiles > 0) AS n_host
FROM wins w
JOIN base b ON b.ts > now() - w.iv
GROUP BY w.win
ORDER BY CASE w.win WHEN '1h' THEN 1 WHEN '3h' THEN 2 WHEN '6h' THEN 3 ELSE 4 END;
""")

# Hourly CPU + census
run("sql_cpu_hourly.txt", """
SELECT date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour_hkt,
       min(tick) AS tick_min, max(tick) AS tick_max,
       count(*) AS n,
       round(avg(cpu)::numeric, 3) AS cpu_avg,
       round((percentile_cont(0.50) WITHIN GROUP (ORDER BY cpu))::numeric, 3) AS cpu_p50,
       round((percentile_cont(0.95) WITHIN GROUP (ORDER BY cpu))::numeric, 3) AS cpu_p95,
       round(min(cpu)::numeric, 3) AS cpu_min,
       round(max(cpu)::numeric, 3) AS cpu_max,
       min(bucket) AS bucket_min,
       count(*) FILTER (WHERE cpu > 20) AS n_gt20,
       count(*) FILTER (WHERE cpu > 18) AS n_gt18,
       count(*) FILTER (WHERE cpu < 15) AS n_lt15,
       max(hostiles) AS host_max,
       count(*) FILTER (WHERE hostiles > 0) AS n_host,
       round(avg(storage)::numeric, 0) AS stor_avg,
       min(storage) AS stor_min, max(storage) AS stor_max,
       round(avg((SELECT sum((v)::int) FROM jsonb_each_text(creeps) e(k,v)))::numeric, 1) AS creeps_avg,
       max((SELECT sum((v)::int) FROM jsonb_each_text(creeps) e(k,v))) AS creeps_max
FROM room_stats
WHERE room='W46N8' AND ts > now()-interval '12 hours'
GROUP BY 1
ORDER BY 1;
""")

# Histogram bins last 12h / 3h / 1h
run("sql_cpu_hist.txt", """
WITH base AS (
  SELECT cpu, ts,
         CASE
           WHEN cpu < 14 THEN '<14'
           WHEN cpu < 15 THEN '14-15'
           WHEN cpu < 16 THEN '15-16'
           WHEN cpu < 17 THEN '16-17'
           WHEN cpu < 18 THEN '17-18'
           WHEN cpu < 19 THEN '18-19'
           WHEN cpu < 20 THEN '19-20'
           WHEN cpu < 22 THEN '20-22'
           WHEN cpu < 25 THEN '22-25'
           WHEN cpu < 40 THEN '25-40'
           ELSE '>=40'
         END AS bin,
         CASE
           WHEN ts > now()-interval '1 hour' THEN 1 ELSE 0 END AS in_1h,
         CASE
           WHEN ts > now()-interval '3 hours' THEN 1 ELSE 0 END AS in_3h,
         CASE
           WHEN ts > now()-interval '6 hours' THEN 1 ELSE 0 END AS in_6h
  FROM room_stats
  WHERE room='W46N8' AND ts > now()-interval '12 hours'
)
SELECT bin,
       count(*) AS n_12h,
       sum(in_6h) AS n_6h,
       sum(in_3h) AS n_3h,
       sum(in_1h) AS n_1h
FROM base
GROUP BY bin
ORDER BY min(cpu);
""")

# Spikes over 20 in last 12h with context
run("sql_cpu_spikes.txt", """
SELECT (ts AT TIME ZONE 'Asia/Hong_Kong') AS hkt, tick, round(cpu::numeric,2) AS cpu,
       bucket, round(trace_cpu::numeric,3) AS trace_cpu, hostiles, storage,
       (SELECT sum((v)::int) FROM jsonb_each_text(creeps) e(k,v)) AS n_creeps,
       creeps
FROM room_stats
WHERE room='W46N8' AND ts > now()-interval '12 hours' AND cpu > 20
ORDER BY ts;
""")

# Top spikes including deploy-like
run("sql_cpu_top15.txt", """
SELECT (ts AT TIME ZONE 'Asia/Hong_Kong') AS hkt, tick, round(cpu::numeric,2) AS cpu,
       bucket, hostiles, storage,
       (SELECT sum((v)::int) FROM jsonb_each_text(creeps) e(k,v)) AS n_creeps,
       creeps
FROM room_stats
WHERE room='W46N8' AND ts > now()-interval '12 hours'
ORDER BY cpu DESC
LIMIT 15;
""")

# Coverage gaps (box pauses + rotation)
run("sql_room_stats_gaps.txt", """
WITH s AS (
  SELECT ts, tick, lag(ts) OVER (ORDER BY ts) AS prev_ts, lag(tick) OVER (ORDER BY tick, ts) AS prev_tick
  FROM room_stats
  WHERE room='W46N8' AND ts > now()-interval '12 hours'
)
SELECT (prev_ts AT TIME ZONE 'Asia/Hong_Kong') AS gap_from,
       (ts AT TIME ZONE 'Asia/Hong_Kong') AS gap_to,
       round(EXTRACT(EPOCH FROM (ts-prev_ts))::numeric,0) AS gap_s,
       prev_tick, tick, (tick-prev_tick) AS tick_span
FROM s
WHERE ts-prev_ts > interval '90 seconds'
ORDER BY prev_ts;
""")

# Role census hourly (from room_stats creeps jsonb)
run("sql_roles_hourly.txt", """
SELECT date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour_hkt,
       k AS role,
       round(avg(v::int)::numeric, 2) AS avg_n,
       min(v::int) AS min_n,
       max(v::int) AS max_n
FROM room_stats, jsonb_each_text(creeps) e(k,v)
WHERE room='W46N8' AND ts > now()-interval '12 hours'
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
""")

# Role census last 1h / 3h / 6h / 12h averages
run("sql_roles_windows.txt", """
WITH wins AS (
  SELECT '1h'::text AS win, interval '1 hour' AS iv
  UNION ALL SELECT '3h', interval '3 hours'
  UNION ALL SELECT '6h', interval '6 hours'
  UNION ALL SELECT '12h', interval '12 hours'
)
SELECT w.win, k AS role,
       round(avg(v::int)::numeric, 2) AS avg_n,
       min(v::int) AS min_n,
       max(v::int) AS max_n
FROM wins w
JOIN room_stats r ON r.room='W46N8' AND r.ts > now()-w.iv
JOIN jsonb_each_text(r.creeps) e(k,v) ON true
GROUP BY w.win, k
ORDER BY w.win, avg_n DESC;
""")

# creep_cpu by role, last 12h / 3h / 1h (awake coverage only)
run("sql_creep_cpu_windows.txt", """
WITH wins AS (
  SELECT '1h'::text AS win, interval '1 hour' AS iv
  UNION ALL SELECT '3h', interval '3 hours'
  UNION ALL SELECT '6h', interval '6 hours'
  UNION ALL SELECT '12h', interval '12 hours'
)
SELECT w.win, role,
       count(*) AS windows,
       count(DISTINCT creep) AS creeps,
       count(DISTINCT tick) AS ticks,
       round((sum(cpu_ms)::numeric / NULLIF(count(*)*5,0)), 4) AS cpu_per_tick_per_creep,
       round(sum(cpu_ms)::numeric, 1) AS cpu_ms_sum,
       round(avg((acts=0)::int)::numeric, 3) AS idle_frac,
       round((sum(repaths)*100.0/NULLIF(count(*)*5,0))::numeric, 2) AS rp100,
       round(max(cpu_ms)::numeric, 3) AS win_cpu_max
FROM wins w
JOIN creep_cpu c ON c.ts > now()-w.iv
GROUP BY w.win, role
ORDER BY w.win, cpu_per_tick_per_creep DESC;
""")

# Estimated role total CPU: per-creep ms * live average count (1h and 6h)
# We'll compute in a later join in python if needed; also dump coverage
run("sql_creep_cpu_coverage.txt", """
SELECT
  count(DISTINCT tick) FILTER (WHERE ts>now()-interval '1 hour') AS ticks_1h,
  count(DISTINCT tick) FILTER (WHERE ts>now()-interval '3 hours') AS ticks_3h,
  count(DISTINCT tick) FILTER (WHERE ts>now()-interval '6 hours') AS ticks_6h,
  count(DISTINCT tick) FILTER (WHERE ts>now()-interval '12 hours') AS ticks_12h,
  min(ts) FILTER (WHERE ts>now()-interval '12 hours') AS first_ts,
  max(ts) AS last_ts,
  min(tick) FILTER (WHERE ts>now()-interval '12 hours') AS first_tick,
  max(tick) AS last_tick
FROM creep_cpu
WHERE ts > now()-interval '12 hours';
""")

# cpu_prof section averages by window
run("sql_cpu_prof_windows.txt", """
WITH wins AS (
  SELECT '1h'::text AS win, interval '1 hour' AS iv
  UNION ALL SELECT '3h', interval '3 hours'
  UNION ALL SELECT '6h', interval '6 hours'
  UNION ALL SELECT '12h', interval '12 hours'
)
SELECT w.win, section,
       count(*) AS n_polls,
       round(avg(ms)::numeric, 3) AS ms_avg,
       round(min(ms)::numeric, 3) AS ms_min,
       round(max(ms)::numeric, 3) AS ms_max
FROM wins w
JOIN cpu_prof p ON p.ts > now()-w.iv
GROUP BY w.win, section
ORDER BY w.win, ms_avg DESC;
""")

run("sql_cpu_prof_polls.txt", """
SELECT DISTINCT (ts AT TIME ZONE 'Asia/Hong_Kong') AS hkt, tick, bucket
FROM cpu_prof
WHERE ts > now()-interval '12 hours'
ORDER BY 1;
""")

run("sql_cpu_prof_total_trend.txt", """
SELECT (ts AT TIME ZONE 'Asia/Hong_Kong') AS hkt, tick,
       round(ms::numeric, 3) AS total_ms, bucket
FROM cpu_prof
WHERE section='total' AND ts > now()-interval '12 hours'
ORDER BY ts;
""")

# Hostiles / events last 12h
run("sql_events_12h.txt", """
SELECT (ts AT TIME ZONE 'Asia/Hong_Kong') AS hkt, tick, kind, room, severity, episode, left(msg,180) AS msg
FROM events
WHERE ts > now()-interval '12 hours'
ORDER BY ts;
""")

run("sql_hostiles_hourly.txt", """
SELECT date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour_hkt, room,
       max(hostiles) AS host_max, count(*) FILTER (WHERE hostiles>0) AS n_host, count(*) AS n
FROM room_stats
WHERE room IN ('W46N8','W47N8','W45N8','W45N7','W47N7')
  AND ts > now()-interval '12 hours'
GROUP BY 1,2
ORDER BY 1,2;
""")

# Storage both rooms last 6h
run("sql_stor_windows.txt", """
WITH wins AS (
  SELECT '1h'::text AS win, interval '1 hour' AS iv
  UNION ALL SELECT '3h', interval '3 hours'
  UNION ALL SELECT '6h', interval '6 hours'
  UNION ALL SELECT '12h', interval '12 hours'
)
SELECT w.win, r.room,
       count(*) AS n,
       min(storage) AS stor_min, max(storage) AS stor_max,
       round(avg(storage)::numeric,0) AS stor_avg,
       count(*) FILTER (WHERE storage < 15000) AS n_lt15k,
       count(*) FILTER (WHERE storage >= 20000) AS n_ge20k,
       count(*) FILTER (WHERE storage >= 40000) AS n_ge40k
FROM wins w
JOIN room_stats r ON r.room IN ('W46N8','W47N8') AND r.ts > now()-w.iv
GROUP BY w.win, r.room
ORDER BY w.win, r.room;
""")

print("done")
