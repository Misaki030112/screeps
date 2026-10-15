# Data platform (box): TimescaleDB + Grafana

## Why TimescaleDB
Box: 8 vCPU, 15 GiB RAM (≈6 GiB free), 117 GB free disk; no systemd or docker (tini as PID 1).
| Option | Verdict |
|---|---|
| SQLite (old metrics/ts.sqlite) | Fine for ingest, but no retention, downsampling or Grafana-native time series; single-writer. Retired (archived in metrics/archive/). |
| DuckDB + parquet | Great for ad-hoc analytics, but not a live store: concurrent append from the listener plus readers (Grafana, patrol) is awkward, and there is no background retention or aggregation. |
| **TimescaleDB 2.30 (PostgreSQL 17)** | **Chosen.** Plain SQL with window functions (trajectory/stuck analysis), hypertables, built-in retention, compression and continuous aggregates, first-class Grafana datasource, apt packages for Debian 13. ≈300 MB RAM. |
| QuestDB | Fast ingest, but weaker SQL for window/gaps-and-islands work and needs a JVM. Overkill for ~4 rows/s. |
| VictoriaMetrics / InfluxDB | Metric (label/value) model, poor fit for per-creep trajectories and joins; needs another store anyway. |

Load is tiny: ~15 creeps × 1 row per tick (≈3.9 s/tick) ≈ 4 rows/s.

## Services (`tools/services.sh` = start-if-down; run by the patrol, idempotent)
- PostgreSQL 17 cluster `17/main` on 127.0.0.1:5432, db `screeps`, user `screeps`. Password `PGPASSWORD` is in `.env` (gitignored). Config: `/etc/postgresql/17/main/conf.d/screeps.conf`.
- Grafana 13 on **http://127.0.0.1:3000** (box browser). Anonymous users get read-only access; the admin password is `GF_ADMIN_PASSWORD` in `.env`. Dashboard "Screeps W46N8" is provisioned from `grafana/dashboards/screeps.json`. Run `python3 tools/grafana_check.py` to check every panel query.
- Websocket listener (`tools/run_listener.sh`) writes through `tools/ingest.py`: one background writer, batches every 2 s, retries on DB errors. The old dashboard at http://127.0.0.1:8787/tools/dashboard.html still uses `metrics/live.json` (cache only) and `metrics/creep_audit.json`.
- There is no systemd. After a box restart, run `tools/services.sh` (the patrol does this every iteration).

## Box restarts and persistence (incident 2026-10-15)
- **Incident:** the box was stuck 20:57–23:28 (UTC+8) and came back from a fresh system image. `/workspace` and `/home/box` were kept, but system dirs (`/usr`, `/etc`, `/var/lib`) and apt packages were reset. PGDATA was at the Debian default `/var/lib/postgresql/17/main`, so the TimescaleDB data was lost. `services.sh` only started services and could not reinstall them. The 23:33 run reinstalled the packages and initialised an empty DB. No old cluster survived anywhere (searched for PG_VERSION). Recovered: the pre-Timescale archive `metrics/archive/` (10-12 17:20 → 10-13 10:19, via backfill) plus deploy rows `ef368d3` and `10f881a`. The data from 10-13 10:19 to 10-15 23:33 is gone.
- **Now:** PGDATA = `var/pg17` and its conf templates in `var/pg17-conf`. Grafana data is in `grafana/data`, the Grafana .deb is in `var/pkgs`, and Python deps are in `requirements.txt`. All of these are under /workspace and gitignored where needed.
- `tools/services.sh` reinstalls missing packages and the venv. It re-adopts `var/pg17` with `pg_createcluster -d` and drops the empty default cluster that apt creates. It refuses (exit 3) when a cluster elsewhere holds a `screeps` DB. It never runs initdb over existing data. If `var/pg17` is missing entirely, it creates a cluster there and restores the newest dump.
- **Backups:** `tools/pg_backup.sh` (called by services.sh) runs `pg_dump -Fc` when the newest dump is >6h old. It keeps 8 in `var/backups`, plus the 2 newest in the agent store `/cursor/stores/store-f5e64756-…/screeps-db` (a second copy outside the box disk). Each dump is ~110 KB now. Use `--force` to dump now. To restore by hand: create the extension, `timescaledb_pre_restore()`, `pg_restore` as postgres (no `--role`), then `timescaledb_post_restore()`.
- **Tested 23:40:** stop pg → services.sh restarts it from var/pg17. Fresh-box simulation (moved away /etc config and /var/lib data, apt-style default cluster) → dropped the default cluster, adopted var/pg17, data intact. Restore of the newest dump into a scratch DB returns the same row counts.
- Note: the reinstalled TimescaleDB is the Debian 2.19 (Apache) build, not 2.30, so there are no continuous aggregates; creep_audit falls back (029cbfb).

## Schema (db/schema.sql, apply with `.venv/bin/python tools/db.py --init`)
| Table | Grain | Source | Retention |
|---|---|---|---|
| `creep_ticks(ts,tick,room,creep,role,x,y,hits,store,state,commit)` | every own creep, every tick a room update arrives | websocket room objects (0 in-game CPU) | 7 days raw (compressed after 1 day) |
| `creep_cpu(ts,tick,creep,role,cpu_ms,acts,work,repaths,stuck,target,commit,rp_why)` | 5-tick window per creep; `rp_why` = one char per PathFinder search (n new target, v version bump, o off path, s stuck2, x stuck8, z stuck30) | memory segment 90 ring buffer, polled every 60 s; the listener only writes windows newer than the last ingested tick (ts is in the unique key, so the index alone cannot dedup re-reads — fixed 2026-10-13, ~14× duplicates removed) | 30 days (compressed after 1 day) |
| `path_arrivals(ts,tick,creep,role,target,planned,actual,commit)` | per path completed | segment 90 | forever (small) |
| `room_stats(ts,tick,room,rcl,progress,…,cpu,bucket,trace_cpu,creeps,commit)` | every 10 ticks | STATS console line | forever (small) |
| `events(ts,tick,kind,room,severity,episode,msg,data)` | kinds: alert_new/escalated/ended, stuck, layout, error, watch (W45N8), collect | console + listener | forever |
| `alert_state(episode,…,acked,ended)` | alert episodes | read and acked by `alerts.py` | – |
| `deploys(ts,tick,commit,note)` | every upload (`.venv/bin/python scripts/deploy.py "note"`) | deploy script | – |

`commit` on each row is the latest deploy's commit, so any metric can be split before/after a deploy.
`state` is currently derived box-side (`spawning`/`loaded`/`empty`).

Continuous aggregates (real-time, refreshed every 1–5 min, kept 400 days): `creep_1m`, `tile_traffic_10m` (heatmaps), `role_cpu_10m`, `room_stats_10m`.

## Disk estimate (measured ≈245 B/row incl. indexes, uncompressed)
- creep_ticks: ≈22k ticks/day × 15 creeps ≈ 330k rows/day ≈ 80 MB/day raw. Compression after 1 day (≈10×), so 7 days ≈ 80 + 6×8 ≈ **130 MB** (≈560 MB worst case uncompressed).
- creep_cpu: ≈66k rows/day ≈ 16 MB/day, compressed after 1 day, ≈ 60 MB for 30 days.
- Aggregates and the rest: < 5 MB/day.
- **Total steady state < 1 GB with 30 creeps**, against 117 GB free. Check with: `SELECT hypertable_name, pg_size_pretty(hypertable_size(format('%I',hypertable_name)::regclass)) FROM timescaledb_information.hypertables;`

## Audit
`tools/creep_audit.py` runs `db/audit.sql` over 1h/6h/24h windows, compares each window with the previous one and with the period before the last deploy, writes `metrics/creep_audit.json` and `metrics/traffic_<room>.png`, and has `--patrol` exit codes. The listener runs it every ~10 min.

Stuck (audit): a run of ≥10 samples on one tile with no successful intent **while the creep still had a pending path** (`creep_cpu.target <> ''`); parked/waiting creeps count as idle, not stuck.

## Example queries (`.venv/bin/python tools/db.py "SQL"`)
```sql
-- ingestion keeps up? ticks seen vs tick span, last 10 min
SELECT count(DISTINCT tick) seen, max(tick)-min(tick)+1 span, now()-max(ts) lag FROM creep_ticks WHERE ts > now()-interval '10 minutes';
-- trajectory of one creep
SELECT tick, room, x, y, store FROM creep_ticks WHERE creep='rhauler83609332' AND ts > now()-interval '1 hour' ORDER BY tick;
-- CPU per tick by role, hourly trend
SELECT time_bucket('1 hour', bucket) h, role, sum(cpu_ms)/sum(ticks) cpu_t, sum(idle_windows)::float/sum(windows) idle FROM role_cpu_10m GROUP BY 1,2 ORDER BY 1,2;
-- before/after the last deploy (1 h each), per role
WITH d AS (SELECT ts FROM deploys ORDER BY ts DESC LIMIT 1)
SELECT role, ts >= (SELECT ts FROM d) AS after, sum(cpu_ms)/(count(*)*5) cpu_t, avg((acts=0)::int) idle, sum(repaths)*100.0/(count(*)*5) rp100
FROM creep_cpu WHERE ts BETWEEN (SELECT ts FROM d)-interval '1 hour' AND (SELECT ts FROM d)+interval '1 hour' GROUP BY 1,2 ORDER BY 1,2;
-- route adherence: worst targets by excess
SELECT role, target, count(*), round(avg(actual::numeric/planned),2) excess, percentile_cont(0.5) WITHIN GROUP (ORDER BY actual) trip FROM path_arrivals WHERE ts > now()-interval '24 hours' GROUP BY 1,2 HAVING count(*)>=3 ORDER BY excess DESC LIMIT 10;
-- stuck runs (same tile >= 10 consecutive samples, moving roles)
WITH p AS (SELECT creep, role, tick, (x,y,room) IS DISTINCT FROM (lag(x) OVER w, lag(y) OVER w, lag(room) OVER w) mv FROM creep_ticks WHERE ts > now()-interval '1 hour' WINDOW w AS (PARTITION BY creep ORDER BY tick)),
g AS (SELECT *, sum(mv::int) OVER (PARTITION BY creep ORDER BY tick) grp FROM p)
SELECT creep, role, min(tick), count(*) FROM g WHERE role NOT IN ('miner','rminer','upgrader','filler','manager') GROUP BY creep, role, grp HAVING count(*) >= 10 ORDER BY 4 DESC;
-- why do creeps repath? (reason codes per role, last hour)
SELECT role, ch, count(*) FROM creep_cpu, regexp_split_to_table(rp_why, '') ch WHERE ts > now()-interval '1 hour' AND rp_why <> '' GROUP BY 1,2 ORDER BY 1,3 DESC;
-- heatmap of the busiest tiles, 24 h
SELECT room, x, y, sum(n) FROM tile_traffic_10m WHERE bucket > now()-interval '24 hours' GROUP BY 1,2,3 ORDER BY 4 DESC LIMIT 20;
-- remote energy flow: rhauler loads arriving home
SELECT time_bucket('1 hour', ts) h, count(*) FILTER (WHERE store > 0 AND room='W46N8' AND x < 48) FROM creep_ticks WHERE role='rhauler' GROUP BY 1 ORDER BY 1;
```
