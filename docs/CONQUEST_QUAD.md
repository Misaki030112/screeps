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
