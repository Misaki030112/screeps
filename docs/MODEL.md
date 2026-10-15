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

## Audit 2026-10-15 (first principles + 6 h data, window 05:38–11:38 after the Invader incident)
| Component | Verdict | Note / fix |
|---|---|---|
| Source 3000/300 = 10/t, reserved 3000 | correct | unreserved remote would be 1500 (5/t) |
| Container decay 0.1 owned / 0.5 remote | correct | |
| Road decay 0.001/t plain, 0.005 swamp | correct | road on wall (×150) not handled, none today |
| Body cost / 1500, CLAIM 600 | correct | upgrader upkeep folded via 1300/1500/12 per upgrade/t |
| Miner 5W1C3M = 700 | correct | |
| WORK-bound vs energy-bound | correct | 24 WORK > 23.2 available → energy-bound |
| Travel/fatigue + carry formula | correct shape, optimistic ~10% | measured cycles hauler 70 vs 64, rhauler 92 vs 84: add swap/pickup/blocked overhead |
| Tick time 3.9 s | **wrong** → fixed | now measured from room_stats (4.08 s) |
| Link loss 3% | **missing** | ~0.2–0.3/t on hub→controller flow |
| Tower energy (repair/attack), rampart decay 0.03/t each | **missing** | small now; grows with walls (RCL6+) |
| Construction / storage refill (Δstorage) | **missing** | model is steady-state; actual upgrade must be compared as upgrade + build + Δstorage |
| Miner replacement gap (no pre-spawn) | **missing** | remote pickup 8.2/t vs 10; miner pre-spawn pending |
| Structure | improve | rewrite as explicit flow balance: gross income − (upkeep + decay + link loss + tower) = upgrade + build + Δstorage |
