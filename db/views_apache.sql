-- Apache-license Timescale (Debian 2.19) has no continuous aggregates.
-- Plain views keep Grafana + creep_audit heatmaps working (see docs/DATA.md).
-- Idempotent; safe to re-run every patrol / services.sh.
CREATE OR REPLACE VIEW tile_traffic_10m AS
  SELECT time_bucket('10 minutes', ts) AS bucket, room, x, y, role, count(*)::bigint AS n
  FROM creep_ticks GROUP BY 1, 2, 3, 4, 5;
CREATE OR REPLACE VIEW role_cpu_10m AS
  SELECT time_bucket('10 minutes', ts) AS bucket, role,
         count(DISTINCT creep)::bigint AS creeps, sum(cpu_ms) AS cpu_ms,
         (max(tick) - min(tick) + 5)::bigint AS ticks, sum(acts) AS acts, sum(work) AS work,
         sum(repaths) AS repaths, sum(stuck) AS stuck,
         sum(CASE WHEN acts = 0 THEN 1 ELSE 0 END)::bigint AS idle_windows,
         count(*)::bigint AS windows
  FROM creep_cpu GROUP BY 1, 2;
CREATE OR REPLACE VIEW room_stats_10m AS
  SELECT time_bucket('10 minutes', ts) AS bucket, room, max(rcl) AS rcl, max(progress) AS progress,
         min(tick) AS t0, max(tick) AS t1, avg(energy) AS energy_avg, max(energy_cap) AS energy_cap,
         avg(cpu) AS cpu_avg, max(cpu) AS cpu_max, min(bucket) AS bucket_min, avg(trace_cpu) AS trace_cpu_avg
  FROM room_stats GROUP BY 1, 2;
CREATE OR REPLACE VIEW creep_1m AS
  SELECT time_bucket('1 minute', ts) AS bucket, creep, role, room, count(*)::bigint AS samples,
         count(DISTINCT (x::int * 50 + y))::bigint AS tiles, min(tick) AS t0, max(tick) AS t1,
         avg(store) AS store_avg, min(hits) AS hits_min
  FROM creep_ticks GROUP BY 1, 2, 3, 4;
GRANT SELECT ON tile_traffic_10m, role_cpu_10m, room_stats_10m, creep_1m TO PUBLIC;
