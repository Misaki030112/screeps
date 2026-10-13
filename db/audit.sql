-- Per-creep audit for a time window. Params: %(a)s, %(b)s (timestamptz). Used by tools/creep_audit.py; documented in docs/DATA.md.
WITH p AS (
  SELECT creep, role, tick, room, x, y,
         (x, y, room) IS DISTINCT FROM (lag(x) OVER w, lag(y) OVER w, lag(room) OVER w) AS moved,
         (x, y, room) = (lag(x, 2) OVER w, lag(y, 2) OVER w, lag(room, 2) OVER w)
           AND (x, y, room) IS DISTINCT FROM (lag(x) OVER w, lag(y) OVER w, lag(room) OVER w) AS bounce
  FROM creep_ticks WHERE ts >= %(a)s AND ts < %(b)s
  WINDOW w AS (PARTITION BY creep ORDER BY tick)),
g AS (SELECT *, sum(moved::int) OVER (PARTITION BY creep ORDER BY tick) AS grp FROM p),
runs AS (SELECT creep, role, grp, min(tick) t0, max(tick) t1, count(*) n FROM g GROUP BY creep, role, grp),
stuck AS (
  SELECT r.creep, count(*) AS stuck_eps, sum(r.t1 - r.t0) AS stuck_ticks FROM runs r
  WHERE r.n >= 10 AND r.role NOT IN ('miner', 'rminer', 'filler', 'manager', 'upgrader')
    AND NOT EXISTS (SELECT 1 FROM creep_cpu c WHERE c.creep = r.creep AND c.tick BETWEEN r.t0 AND r.t1 + 4 AND c.acts > 0 AND c.ts >= %(a)s - interval '10 minutes')
    -- only count it as stuck while the creep still wanted to move (had an unfinished path); parked/waiting creeps are idle, not stuck
    AND EXISTS (SELECT 1 FROM creep_cpu c WHERE c.creep = r.creep AND c.tick BETWEEN r.t0 + 5 AND r.t1 AND c.target <> '' AND c.ts >= %(a)s - interval '10 minutes')
  GROUP BY r.creep),
pos AS (SELECT creep, min(role) role, count(*) samples, sum(moved::int) moves, count(DISTINCT (room, x, y)) tiles, sum(bounce::int) bounces,
               max(tick) - min(tick) + 1 AS ticks FROM p GROUP BY creep),
cpu AS (SELECT creep, min(role) role, sum(cpu_ms) cpu_ms, count(*) windows, avg((acts = 0)::int) idle, sum(work) work, sum(repaths) repaths, sum(stuck) stuck_ev
        FROM creep_cpu WHERE ts >= %(a)s AND ts < %(b)s GROUP BY creep),
arr AS (SELECT creep, count(*) trips, percentile_cont(0.5) WITHIN GROUP (ORDER BY actual::float / NULLIF(planned, 0)) excess,
               max(actual::float / NULLIF(planned, 0)) excess_max, percentile_cont(0.5) WITHIN GROUP (ORDER BY actual) trip_med
        FROM path_arrivals WHERE ts >= %(a)s AND ts < %(b)s GROUP BY creep)
SELECT coalesce(pos.creep, cpu.creep) creep, coalesce(pos.role, cpu.role) role, pos.ticks, pos.samples, pos.moves, pos.tiles,
       coalesce(stuck.stuck_eps, 0) stuck, coalesce(stuck.stuck_ticks, 0) stuck_ticks, coalesce(pos.bounces, 0) / 4 AS osc,
       round(cpu.idle::numeric, 2) idle, round((cpu.cpu_ms / (cpu.windows * 5))::numeric, 3) cpu_t,
       round((cpu.work / NULLIF(cpu.cpu_ms, 0))::numeric, 1) work_per_cpu, round((cpu.work::numeric / (cpu.windows * 5)), 2) work_t,
       round((cpu.repaths * 100.0 / (cpu.windows * 5))::numeric, 1) rp100, cpu.stuck_ev,
       coalesce(arr.trips, 0) trips, round(arr.excess::numeric, 2) excess, round(arr.excess_max::numeric, 2) excess_max, arr.trip_med
FROM pos FULL JOIN cpu ON cpu.creep = pos.creep LEFT JOIN stuck ON stuck.creep = coalesce(pos.creep, cpu.creep)
     LEFT JOIN arr ON arr.creep = coalesce(pos.creep, cpu.creep);
