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

## Source-rooted flow (tools/flow.py, 2026-10-15) — replaces the "income − overhead" headline
Per source: gross 10/t → losses (container decay, link 3% on B's storage→ctl leg) → source upkeep (miner, haulers with ×1.10
congestion/pickup on the round trip, reserver for the remote) = net. Shared upkeep (queen, builder-lite, roads, ramparts 0.03/t each)
once; upgrade = net / (1 + 1300/1500/12). Steady state has no downtime (REMOTE_AVAIL=1); Invader risk is the separate stochastic layer:
EV = episodes per tick (events table, 7 d) × per-episode (downtime ×10/t, defender 1300 × defenders/episode, container rebuild 5000 × 0.25).
Gains: Invader tombstones only hold carried resources (none), body energy is not refunded → 0.
Validation compares upgrade_expected with measured upgrade + build + storage delta. ETA hours use measured tick seconds.

10-15 11:45 (6 h): A 8.78, B 9.13, R 5.99 net; shared 1.43; net 22.47 → upgrade 20.96 steady, 20.31 with Invader EV 0.69/t (range 0.11–1.15;
3 episodes / 7 d ≈ one per 19.5k ticks ≈ 195k remote energy). Measured sinks 18.40 + 0.51 + 0.19 = 19.10 (−6%; last 2 h upgrade 20.7, +2%).

## 2026-10-16 18:00 update: W45N7 added (flow.EXTRA_REMOTES)
W45N7 net = 10 − 0.5 container − 0.53 miner − 1.23 reserver − 3.20 haulers (6×8C8M) = **4.54/t** (the design figure of 4.2 included congestion).
Total net 28.09 → **upgrade ceiling 26.2/t** (steady state, before Invader EV). Invader EV in the DB is 0 now: the events table was lost in the 10-15 reset. The last measured value was 0.69/t for one remote; budget 0.7–1.4 for two. The realised share has been about 94% of the model (10-15 check: −6%). **Realistic steady rate is 24–25/t.**
WORK cap: 12W per upgrader (1800 cap, code min 12); 3 upgraders = 36 WORK, so the rate is energy-bound, not WORK-bound. 2 upgraders = 24 WORK is binding just below the ceiling.
Spawn: about 0.38 utilisation pre-W45N7, plus about 0.23 for W45N7 (96 hauler parts, 10 miner, reserver ×2.5), plus a 3rd upgrader → about 0.65. One spawn is enough.
Fluctuation (hourly W46N8 rate 10-16 00–15h, W45N8 only): 17.0–23.4, median about 20; a ±3/t band per hour. New sources of dips: remote opening spawn contention (16:00h 14.6/t, fixed in 147bbda); a miner swap deadlock (fixed in 00e1ded); the 3rd upgrader gate (storage ≥ floor+1000).


## 2026-10-20 00:5x: home ideal includes W45N7; upgraders were the cap

- `upgrade_max_ideal` summed A + B + W45N8 only (21.8). tools/flow.py already had W45N7 (net 4.54 after its rminer, 4x8C haulers, reserver), and the hauler need was fixed for the same gap at 21:5x. The ideal is now 26.0 (3-source value kept as `upgrade_max_ideal_3src`). `upgrade_max_live_comp` / `upgrader_bound` still use 3 sources; read them with that in mind.
- 6h balance: upgrade 22.7 + builder 2.4 + storage -0.2, plus upgrader upkeep ~1.7, comes to ~26.9 of a flow net of 28.1, so ~1.2 e/t is overhead above the model (extra queen/rhauler bodies). Energy is not lost. Live at 00:4x the ctl container was full (2000) with 2x12W: WORK-bound, not energy-bound.
- Lever: 14W1C2M upgraders at RCL6-7 (e1df502). 28 WORK sits just above the ~26 feed, so the room stays slightly energy-bound and the 3rd-upgrader gate (storage >= floor+1000, ctlEma >= 700) stays for real surplus only.

## 2026-10-20 02:4x strategy review: does home still need its hauler at RCL6?

Open question from the 23:5x evaluation: the home hauler (link era, 6C3M, 450 e, upkeep 0.30 e/t) shows ~97-100% waiting_pickup.
- **Measured (creep_ticks, 6 h to t83749739, role hauler in W46N8):** picked 900 e and delivered 1050 e in 5109 ticks, about **0.18 e/t**. All pickups were at 33,30 (hub side) and 750 of the deliveries at 31,29 (ctl container 30,30); 0 pickups at source A container 31,12. Live: container 31,12 at 72, link 30,11 cycling (150, cooldown 6), 0 drops. Link 30,11 carries all of source A; the hauler is a slow spare ferry.
- **Saving if removed:** ~0.3 e/t (about 1.1% of the 26 e/t upgrade), so RCL7 lands ~1.5 h earlier out of ~5.5 days. Small.
- **Why not remove it now:** (1) `bodyEnergy('queen')` sizes a queen to `energyAvailable` when no hauler is alive, so hauler 0 would quietly shrink queen bodies; (2) the hauler is the only creep that empties the mineral container 41,24 during an O cycle (next regen ~10-21 20:30) and clears source A overflow if link 30,11 stalls; (3) the 2-creep emergency path (`!alive.hauler && !alive.queen ...`) assumes it. Taking it out means decoupling all three for 0.3 e/t.
- **Decision:** keep 1x 6C3M through RCL6. At RCL7 sizing, if Misaki pauses the O cycle (`Memory.ops.mineralCap`, still awaiting her answer since 22:4x), revisit as spawn-on-demand (hauler only while container 31,12 > 1000, mineral container > 400, or drops > 300) after decoupling the queen sizing from `alive.hauler`.
