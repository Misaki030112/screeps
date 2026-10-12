# Screeps bot — Misaki @ shard3 / W46N8

First spawn `Spawn1` at W46N8 (35,28), placed 2026-10-12. Novice protection until ~2026-10-28 03:33 (UTC+8).

## Layout
- `src/main.js` – loop: memory cleanup → spawns → construction → creeps → stats (every step wrapped by `utils/errors`).
- `src/roles/` – harvester, upgrader, builder (+ `index.js` registry).
- `src/managers/` – `spawn` (role targets, body sizing), `construction` (extensions), `stats` (Memory.stats).
- `src/utils/` – `energy` (gather/toggle), `errors` (try/catch + error buffer).
- `scripts/build.js` – flattens `src/` to `dist/` (`roles/harvester.js` → `roles.harvester`), rewriting requires.
- `scripts/check.js` – build + `node --check` + one-tick smoke test with a mocked Game.
- `upload.js` – runs check, then POSTs `dist/` to `/api/user/code` (branch `default`, active on shard3).
- `collect.py` → appends Memory.stats to `metrics/metrics.jsonl`; `status.py [--live]` prints a summary.
- `tools/` – room scouting scripts used to choose the start room; `data/` – scan results.

## Usage
```
node scripts/check.js      # build + checks only
node upload.js             # check then upload
python3 status.py --live   # collect + summary
```
Token lives in `.env` (`SCREEPS_TOKEN=...`, chmod 600, gitignored).
