# Ideal-efficiency model (`tools/model.py`)
Rerun (the patrol can call this every iteration): `.venv/bin/python tools/model.py [--hours 6] [--no-db]`
Outputs: `metrics/model.json`, `docs/model_routes.png` (terrain + ideal routes + 6h traffic + tiles to pave), DB table `model_params(ts,key,ideal,actual,unit)` → Grafana panels "Ideal vs actual".

## Model
- Terrain from `data/terrain_<room>.txt` (API fetch if missing), live objects from `game/room-objects`. W46N8 and W45N8 are joined into one 100×50 grid (exit seam x=49|50).
- Paths: Dijkstra, cost road 1 / plain 2 / swamp 10 (same as `src/utils/move.js`), obstacles = non-walkable structures; target range 1.
- Ticks/tile: fatigue = terrain factor × non-MOVE parts (empty CARRY weightless), each MOVE −2/tick. 1:1 hauler loaded: plain/road 1, swamp 5.
- Per source 3000/300 = 10 e/t (owned or reserved). Miner needs 5 WORK. Hauler CARRY = income × (round-trip ticks + 4) / 50 (≈ 2·dist·income/50 without swamps).
- Overhead = Σ body cost / lifetime (1500, CLAIM 600) + container decay (0.1 owned / 0.5 remote) + road decay. Max upgrade = income − overhead. Upgraders are WORK-bound if Σ WORK < that, energy-bound otherwise.
- ETA RCL4..6 = remaining progress / max upgrade rate (3.9 s/tick).

## Actuals (DB, default 6 h)
upgrade rate (room_stats progress), pickups per source (positive store deltas within 2 tiles of the source, normalised by tick coverage — a lower bound), deliveries (hub vs controller container), per-role idle/repaths/CPU (creep_cpu), planned vs actual path length (path_arrivals), hauler cycle median, share of hauling traffic on ideal-route tiles ± 1.
