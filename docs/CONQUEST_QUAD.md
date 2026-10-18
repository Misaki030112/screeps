# W47N8 quad conquest — PLAN ONLY (2026-10-18 13:20 UTC+8). No military spawn / hostile action until Misaki approves.
Live checks @ tick 83718156 (4.24 s/tick):
- GCL 3 (1.45M/8.69M) -> may own 3 rooms; novice cap 3 rooms. Claim allowed.
- W46N8 + W47N8 both novice zone until 2026-10-28 03:33 UTC+8 (same zone as BustJetter): entry/attack/claim allowed.
- W47N8: reserved by BustJetter until tick 83721324 (~3170 t, ~3.7 h); reserver 2C2M at 14,26; ctl 15,25; sources 27,11 / 11,44;
  2 containers, no towers; his economy creeps (3 haulers, 3 miners, 5W15C10M worker, 4T4M scout). upgradeBlocked expired.
- Exits: E x49 y13-27 (from us), N y0 x9-24 + x32-38 (his W47N9 RCL6, towers 940/820), S y49 x11-19 + x26-36 (his W47N7 remote), W none.
- W48N9: 22 creeps incl 6T12A18M (360 melee dps), 7H7M, 6H6M; towers ~empty. W47N9 towers full.
- Safe mode: one room per shard at a time (ERR_BUSY); ERR_TIRED if upgradeBlocked / cooldown; +1 activation per new RCL.
  W47N8 RCL2 guarantees >=1 activation. While W47N8 is in SM (~20000 t ~ 23.5 h) home W46N8 cannot SM (walls 141k+, 2 towers).
- attackController on a reserved ctl: -1 reservation tick per CLAIM per tick (no cooldown when not owned).
Bodies (cap 2300): quad member 4R5H9M = 2300e, 18 parts, full speed plain; quad = 160 ranged dps, 240 heal/t (adjacent).
Breaker 3CLAIM3M 1950e (600 t life): 2 breakers + natural = 7/t. Claimer 1CLAIM1M 650. Worker 5W5C5M 1000.
Energy ~16.8k (quad 9.2k, breakers 3.9k, claimer 0.65k, 3 workers 3k) + keep >= 8k home reserve -> bank to ~25k.
Spawn time ~300 t (+refill waits) ~ 30-40 min.
Code status: 96cbda0 pair squad (cqsquad 6R2H8M, cqbreaker, cqworker, tools/conquest.py, inert behind Memory.ops.cq) is deployed-inert.
Missing: quad formation movement (2x2 anchor, move only when all 4 fatigue 0, swamp-aware, rotate/squeeze at chokepoints,
retreat as a block, shared focus target, heal lowest). ~200 lines + tests + sim, est. 1.5-2 h.


## Implementation status (2026-10-18 ~13:30 UTC+8) — INERT

Code lives in `src/roles/quad.js` (+ `cqhauler` in `src/roles/conquest.js`). Deployed behind `Memory.ops.cq.armed` (must stay unset until Misaki's go).

### Combat sources adopted
| Pattern | From | Where we use it |
|---|---|---|
| 2×2 swarm clearance matrix (anchor cost = worst of 4 cells); move only when all fatigue 0; regroup before advance; single-file squeeze | Overmind `Pathing.findSwarmPath` / Swarm | `anchorCost`, `quadMatrix`, modes `advance`/`fatigue`/`regroup`/`squeeze` |
| Tower falloff 600@≤5 … 150@≥20; maxDamageAtPos; maxHostileHealingTo; RMA 10/4/1 | Overmind `CombatIntel` | `towerDmg`, `dmgAt`, `hostileHealTo`, `useMass` |
| Target score = our focused dmg − their max heal; CLAIM first | Overmind `CombatTargeting` / TooAngel | `scoreTarget` (CLAIM +1e6) |
| Kiting: keep range ≥3 from ATTACK; step-back-then-shoot | Overmind `Movement.combatMove` + wiki "kiting" | `combatStep` maximises min-melee-range |
| Rotate so healthiest face the threat | Overmind Swarm rotate | `rotateAssign` |
| **No automatic retreat** — retreat only on `cmd='retreat'` | Misaki 13:17 | auto-retreat removed from `conquest.js` and never present in `quad.js` |

### North entrance defence (terrain verified)
`tools/w47n8_access.py` Dijkstra over shard terrain: from W47N9 / W48N9 avoiding W46N8, the only short entry into W47N8 is the **NORTH** (cost 50 / 278). South entry needs a ~430-tile detour via W47N7 (his remote). Posts: quad0 at (26,4) covers x32–38 corridor; quad1 at (8,4) covers x9–24; further quads hold near controller (16,22).

### Activation (Misaki personal command only)
```
Memory.ops.cq.armed = true          // master switch; without it NOTHING spawns
Memory.ops.cq.quadSpawn = true      // first 4 (one quad)
Memory.ops.cq.reinforce = 4         // optional: +N members (fill short quads first = merge, else new qid)
Memory.ops.cq.cmd = 'go'            // enter W47N8, kill reserver, hold north
Memory.ops.cq.claim = true          // breakers (3CLAIM3M) then workers + cqhaulers
Memory.ops.cq.cmd = 'retreat'       // ONLY way to retreat; also stops spawning
```
Fast RCL2: `cqworker` harvests W47N8 sources / his containers / drops first, else hauls from home; `cqhauler` (10C10M) ferries home storage → drop/container near controller.

### Banking
Construction paused (`reserveE=1e6`). Storage dips during pause were spawn refill (queen filling extensions for replacement rhaulers 16C8M/24C12M), not builder drain — builders get `pickSource=null` under `defLow`. Live rate ~25 e/t once spawn waves settle.
