-- Screeps analytics schema (TimescaleDB 2.x on PostgreSQL 17). Apply: tools/db.py --init  (idempotent)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- every own creep, every tick a room update arrives over the websocket (0 in-game CPU)
CREATE TABLE IF NOT EXISTS creep_ticks (
  ts timestamptz NOT NULL, tick bigint NOT NULL, room text NOT NULL, creep text NOT NULL, role text,
  x smallint, y smallint, hits int, store int, state text, commit text);
SELECT create_hypertable('creep_ticks', by_range('ts', INTERVAL '1 day'), if_not_exists => true);
CREATE UNIQUE INDEX IF NOT EXISTS creep_ticks_uq ON creep_ticks (creep, tick, ts);
CREATE INDEX IF NOT EXISTS creep_ticks_room ON creep_ticks (room, ts DESC);

-- in-game 5-tick windows from memory segment 90 (CPU in ms, intents, work units, repaths, stuck events)
CREATE TABLE IF NOT EXISTS creep_cpu (
  ts timestamptz NOT NULL, tick bigint NOT NULL, creep text NOT NULL, role text, cpu_ms real, acts int, work int,
  repaths int, stuck int, target text, commit text);
-- rp_why: one char per PathFinder search in the window (n=new target, v=version bump, o=off path, s=stuck2, x=stuck8, z=stuck30; see src/utils/move.js)
ALTER TABLE creep_cpu ADD COLUMN IF NOT EXISTS rp_why text;
SELECT create_hypertable('creep_cpu', by_range('ts', INTERVAL '1 day'), if_not_exists => true);
CREATE UNIQUE INDEX IF NOT EXISTS creep_cpu_uq ON creep_cpu (creep, tick, ts);

-- path arrivals: planned path length vs actual ticks (route adherence)
CREATE TABLE IF NOT EXISTS path_arrivals (
  ts timestamptz NOT NULL, tick bigint NOT NULL, creep text NOT NULL, role text, target text, planned int, actual int, commit text);
SELECT create_hypertable('path_arrivals', by_range('ts', INTERVAL '7 days'), if_not_exists => true);
CREATE UNIQUE INDEX IF NOT EXISTS path_arrivals_uq ON path_arrivals (creep, tick, target, ts);

-- room economy / CPU every 10 ticks (STATS console line)
CREATE TABLE IF NOT EXISTS room_stats (
  ts timestamptz NOT NULL, tick bigint NOT NULL, room text NOT NULL, rcl int, progress bigint, progress_total bigint,
  energy int, energy_cap int, sites int, hostiles int, safe_mode int, cpu real, bucket int, trace_cpu real,
  gcl_progress double precision, creeps jsonb, commit text);
SELECT create_hypertable('room_stats', by_range('ts', INTERVAL '7 days'), if_not_exists => true);
CREATE UNIQUE INDEX IF NOT EXISTS room_stats_uq ON room_stats (room, tick, ts);

-- alerts, errors, STUCK, LAYOUT, listener events
CREATE TABLE IF NOT EXISTS events (
  ts timestamptz NOT NULL, tick bigint, kind text NOT NULL, room text, severity text, episode text, msg text, data jsonb);
SELECT create_hypertable('events', by_range('ts', INTERVAL '30 days'), if_not_exists => true);
CREATE INDEX IF NOT EXISTS events_kind ON events (kind, ts DESC);

CREATE TABLE IF NOT EXISTS deploys (ts timestamptz NOT NULL, tick bigint, commit text, note text);

-- alert acknowledgement state (alerts.py)
CREATE TABLE IF NOT EXISTS alert_state (episode text PRIMARY KEY, severity text, first jsonb, latest jsonb, acked bool DEFAULT false, ended bool DEFAULT false, seen timestamptz);

-- ---------- continuous aggregates (kept 400 days) ----------
CREATE MATERIALIZED VIEW IF NOT EXISTS creep_1m WITH (timescaledb.continuous) AS
  SELECT time_bucket('1 minute', ts) AS bucket, creep, role, room, count(*) AS samples,
         count(DISTINCT (x::int * 50 + y)) AS tiles, min(tick) AS t0, max(tick) AS t1, avg(store) AS store_avg, min(hits) AS hits_min
  FROM creep_ticks GROUP BY 1, 2, 3, 4 WITH NO DATA;
CREATE MATERIALIZED VIEW IF NOT EXISTS tile_traffic_10m WITH (timescaledb.continuous) AS
  SELECT time_bucket('10 minutes', ts) AS bucket, room, x, y, role, count(*) AS n
  FROM creep_ticks GROUP BY 1, 2, 3, 4, 5 WITH NO DATA;
CREATE MATERIALIZED VIEW IF NOT EXISTS role_cpu_10m WITH (timescaledb.continuous) AS
  SELECT time_bucket('10 minutes', ts) AS bucket, role, count(DISTINCT creep) AS creeps, sum(cpu_ms) AS cpu_ms,
         (max(tick) - min(tick) + 5) AS ticks, sum(acts) AS acts, sum(work) AS work, sum(repaths) AS repaths, sum(stuck) AS stuck,
         sum(CASE WHEN acts = 0 THEN 1 ELSE 0 END) AS idle_windows, count(*) AS windows
  FROM creep_cpu GROUP BY 1, 2 WITH NO DATA;
CREATE MATERIALIZED VIEW IF NOT EXISTS room_stats_10m WITH (timescaledb.continuous) AS
  SELECT time_bucket('10 minutes', ts) AS bucket, room, max(rcl) AS rcl, max(progress) AS progress, min(tick) AS t0, max(tick) AS t1,
         avg(energy) AS energy_avg, max(energy_cap) AS energy_cap, avg(cpu) AS cpu_avg, max(cpu) AS cpu_max, min(bucket) AS bucket_min, avg(trace_cpu) AS trace_cpu_avg
  FROM room_stats GROUP BY 1, 2 WITH NO DATA;

DO $$ BEGIN
  PERFORM add_continuous_aggregate_policy('creep_1m', start_offset => INTERVAL '2 days', end_offset => INTERVAL '1 minute', schedule_interval => INTERVAL '1 minute', if_not_exists => true);
  PERFORM add_continuous_aggregate_policy('tile_traffic_10m', start_offset => INTERVAL '2 days', end_offset => INTERVAL '10 minutes', schedule_interval => INTERVAL '5 minutes', if_not_exists => true);
  PERFORM add_continuous_aggregate_policy('role_cpu_10m', start_offset => INTERVAL '2 days', end_offset => INTERVAL '10 minutes', schedule_interval => INTERVAL '5 minutes', if_not_exists => true);
  PERFORM add_continuous_aggregate_policy('room_stats_10m', start_offset => INTERVAL '2 days', end_offset => INTERVAL '10 minutes', schedule_interval => INTERVAL '5 minutes', if_not_exists => true);
  -- retention: raw tick data 7 days, cpu windows 30 days, aggregates 400 days
  PERFORM add_retention_policy('creep_ticks', INTERVAL '7 days', if_not_exists => true);
  PERFORM add_retention_policy('creep_cpu', INTERVAL '30 days', if_not_exists => true);
  PERFORM add_retention_policy('creep_1m', INTERVAL '400 days', if_not_exists => true);
  PERFORM add_retention_policy('tile_traffic_10m', INTERVAL '400 days', if_not_exists => true);
  PERFORM add_retention_policy('role_cpu_10m', INTERVAL '400 days', if_not_exists => true);
END $$;
-- compression of raw chunks older than 1 day
ALTER TABLE creep_ticks SET (timescaledb.compress, timescaledb.compress_segmentby = 'creep', timescaledb.compress_orderby = 'tick');
SELECT add_compression_policy('creep_ticks', INTERVAL '1 day', if_not_exists => true);
GRANT SELECT ON ALL TABLES IN SCHEMA public TO PUBLIC;
-- real-time aggregation (materialized + not-yet-materialized raw rows)
ALTER MATERIALIZED VIEW creep_1m SET (timescaledb.materialized_only = false);
ALTER MATERIALIZED VIEW tile_traffic_10m SET (timescaledb.materialized_only = false);
ALTER MATERIALIZED VIEW role_cpu_10m SET (timescaledb.materialized_only = false);
ALTER MATERIALIZED VIEW room_stats_10m SET (timescaledb.materialized_only = false);
ALTER TABLE creep_cpu SET (timescaledb.compress, timescaledb.compress_segmentby = 'creep', timescaledb.compress_orderby = 'tick');
SELECT add_compression_policy('creep_cpu', INTERVAL '1 day', if_not_exists => true);

-- remote threat FSM incidents (src/managers/threat.js 'INCIDENT {json}' lines, one row per transition/milestone).
-- ev: threat | wait | defend(=spawn end/dispatch) | spawn_start | arrive | cleared | cancel | resume ; inc = tick the incident started
CREATE TABLE IF NOT EXISTS incidents (
  ts timestamptz NOT NULL, tick bigint, remote text, inc bigint, ev text, from_state text, state text, why text,
  inv int, inv_ttl int, def text, dur int, data jsonb);
CREATE INDEX IF NOT EXISTS incidents_inc ON incidents (remote, inc, tick);
-- one row per incident: timings + estimated energy lost (paused ticks × 6 e/t remote net income, tools/model.py)
CREATE OR REPLACE VIEW incident_summary AS
SELECT remote, inc, min(ts) AS started, max(ts) AS ended,
  max(tick) FILTER (WHERE ev='spawn_start') - inc AS ticks_to_spawn,
  max(tick) FILTER (WHERE ev='defend') - inc AS ticks_to_dispatch,
  max(tick) FILTER (WHERE ev='arrive') - inc AS ticks_to_arrive,
  max(tick) FILTER (WHERE state='SAFE') - inc AS paused_ticks,
  (array_agg(why ORDER BY tick DESC))[1] AS outcome,
  bool_or(ev='spawn_start') AS defender_used,
  (max(tick) FILTER (WHERE state='SAFE') - inc) * 6 AS energy_lost_est
FROM incidents WHERE inc IS NOT NULL GROUP BY remote, inc;
