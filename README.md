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
- Each iteration: analyse (status.py, metrics.jsonl, alerts.py), fix + next ROADMAP step, `node upload.js`, commit, verify, update state/.
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

## Usage
```
node scripts/check.js      # build + checks only
node upload.js             # check then upload
python3 status.py --live   # collect + summary
```
Token lives in `.env` (`SCREEPS_TOKEN=...`, chmod 600, gitignored).
