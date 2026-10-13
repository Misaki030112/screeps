# Screeps bot — Misaki @ shard3 / W46N8

First spawn `Spawn1` at W46N8 (35,28), placed 2026-10-12. Novice protection until ~2026-10-28 03:33 (UTC+8).

## Attack alerts (no automatic safe mode — user decision)
- In-game `src/managers/alerts.js`: hostile creeps by owner (ATTACK/RANGED_ATTACK/CLAIM/HEAL = medium; WORK-only neighbour
  harvesters = low unless structures lose hits), structure hit loss (natural decay ignored), event-log attackers (= high).
  Episodes per owner end after 50 quiet ticks. Written to `Memory.stats.alerts` and logged as `ALERT {json}`.
- The websocket listener appends new/escalated/ended episodes to `metrics/alerts.jsonl` and keeps `metrics/alerts_state.json`.
- **Check pending:** `python3 /workspace/screeps/alerts.py` (exit 0 none, 1 only low, 2 medium/high; `--json`, `--ack ID|all`, `--all`).

## Iterations (state/)
- `state/next_iteration.json` – `{"next_at": "<ISO time, +08:00>", "reason": "..."}`: when the next improvement iteration is worthwhile.
  A scheduler/check should run an iteration only when now >= next_at (or when `alerts.py` exits 2).
- `state/iterations.log` – one line per iteration: `<time UTC+8> | <what changed> | next_at=<ISO>`.
- Each iteration: analyse (status.py, metrics.jsonl, alerts.py, **`.venv/bin/python tools/creep_audit.py --patrol`** — rolling 1h/6h/24h windows + before/after last deploy; exit 1 = findings, 2 = regression after deploy → investigate/rollback first), fix + next ROADMAP step, `node upload.js`, commit, verify, update state/.
  No safe-mode activation and no major decisions (claims, attacks, spending) without user approval.

## Layout
- `src/main.js` – loop: memory cleanup → spawns → construction → creeps → stats (every step wrapped by `utils/errors`).
- `src/roles/` – harvester, upgrader, builder (+ `index.js` registry).
- `src/managers/` – `spawn`, `layout` (sites from plan per RCL), `tower`, `stats`; `src/layouts/` – generated plans; `src/utils/report.js` – STATS console line.
- `src/utils/` – `energy` (gather/toggle), `errors` (try/catch + error buffer).
- `scripts/build.js` – flattens `src/` to `dist/` (`roles/harvester.js` → `roles.harvester`), rewriting requires.
- `scripts/check.js` – build + `node --check` + one-tick smoke test with a mocked Game.
- `upload.js` – runs check, then POSTs `dist/` to `/api/user/code` (branch `default`, active on shard3).
- `collect.py` → appends Memory.stats to `metrics/metrics.jsonl`; `status.py [--live]` prints a summary.
- `tools/` – room scouting scripts used to choose the start room; `data/` – scan results.

## Observability
- **Websocket listener** (`tools/listener.py`, kept alive by `tools/run_listener.sh`): subscribes to
  `user:<id>/console`, `user:<id>/cpu`, `room:shard3/W46N8`. Writes `metrics/console.log`, `metrics/errors.log`,
  `metrics/metrics.jsonl` (STATS line the bot logs every 10 ticks ≈ 40 s), `metrics/live.json` (live room objects, updated every tick ≈ 4 s).
  Start: `nohup tools/run_listener.sh >/dev/null 2>&1 &`  Stop: `kill $(cat metrics/listener.pid); pkill -f "[l]istener.py"`
- **Dashboard**: `nohup tools/run_dashboard.sh > metrics/dashboard.out 2>&1 &` → http://127.0.0.1:8787/tools/dashboard.html (box browser; refreshes every 2 s: room map, stats, errors, console).
- `python3 status.py` (summary incl. websocket data) · `.venv/bin/python status.py --map` → `metrics/room_live.png`.
- `collect.py` (REST Memory.stats, rate-limited 1440/day) remains as a fallback.
- Python deps live in `.venv/` (websocket-client, pillow).

## Layout
`tools/plan_layout.py W46N8 35 28` regenerates `data/layout_W46N8.json`, `src/layouts/W46N8.js`, `docs/layout_W46N8.png`. See docs/LAYOUT.md, docs/STRATEGY.md.

## Layout v2 (live)
`data/layout_W46N8_v2.json` → `src/layouts/W46N8.js` (via `tools/plan_v2.py`, `tools/export_v2.py`, `tools/patch_v2_live.py`).
Checks: `node scripts/check.js` = build + syntax + `scripts/sim.js` (600-tick simulation on `data/sim_snapshot.json`;
refresh the snapshot from the live room before big changes).
Deploy lock: while a deploy runs, `state/deploy.lock` exists; the patrol routine must not upload or change layout/spawn logic then.

## Usage
```
node scripts/check.js      # build + checks only
node upload.js             # check then upload
python3 status.py --live   # collect + summary
```
Token lives in `.env` (`SCREEPS_TOKEN=...`, chmod 600, gitignored).
- Remote mining status: `python3 tools/remote_status.py`; W45N8 activity log `metrics/w45n8_activity.jsonl` (docs/REMOTE_W45N8.md).

## Creep telemetry (continuous, long-term)
- **Store:** `metrics/ts.sqlite` (tools/tsdb.py, SQLite WAL, append-only). Retention 7 days full resolution, then every 10th tick for 60 days (`creep_audit.py --prune`, run daily by the listener).
  - `pos`: every own creep's room/x/y/hits/energy for **every tick** a room update arrives over the websocket (W46N8 + W45N8). Costs zero in-game CPU.
  - `cpu`: in-game per-creep CPU, intents, work units, repaths and stuck events in 5-tick windows. Kept in a ring buffer in memory segment 90 (last 300 ticks); the listener polls it every 60 s.
  - `arr`: path arrivals, planned path length vs actual ticks (route adherence).
  - `deploys`: tick + git commit of every upload (`python3 scripts/deploy.py "note"`), so before/after comparisons are possible.
- **Audit:** `tools/creep_audit.py` (also run every ~10 min by the listener) writes `metrics/creep_audit.json` and `metrics/traffic_<room>.png` (log heatmap + trajectories of the 3 worst creeps). It flags stuck/oscillation episodes, idle ratio, repaths/100 ticks, route excess, CPU/tick per creep and role, and work per CPU ms, plus regressions vs the previous window and vs before the last deploy. A summary appears in `status.py` and the dashboard.
- **Movement** (src/utils/move.js): one cached serialized path per creep and target. Fallback ladder when stuck: 2 ticks → repath around creeps; 4 → swap or push our own non-stationary creep; 8 → step aside and repath; 30 → console `STUCK`. Paths are invalidated only when the room's structure or site count changes. Fixed spots cost 20 in the matrix, so traffic yields to miners, fillers and upgraders. Remote creeps flee home on hostiles (managers/remote.js).
