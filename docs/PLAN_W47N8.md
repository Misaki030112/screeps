# W47N8 development plan RCL4 → RCL8 (2026-10-19 17:15 UTC+8, tick 4.2 s)

Baseline (model_w8 at 17:10): harvest 37.2 e/t (A 9.7, B 9.7, R1/R2 W47N7 ~7.7/7.2 net), upgrade 14.1, build/repair 9.8,
upkeep 11.5, waste 1.8, storage 66. RCL4 progress 87.9k/405k. Structures: 20/20 ext, 1 tower, storage, 4 containers, 171 roads. Nothing
RCL4-gated is left to build, so every spare e/t should go to upgrading until RCL5.
Theoretical limit: 4 sources × 10 = 40 e/t; minimum upkeep at these distances is about 6.8, so about 31–32 e/t net for sinks.

## Stages
| stage | step | cost (energy) | effect | payback |
|---|---|---|---|---|
| RCL4 now | W47N7 road repair (other worker) | ~5.7k | remote CARRY 75→~45, -1.5 e/t upkeep, +0.5 decay saved | ~3k t (~3.5 h) |
| RCL4 now | Trim surplus haulers/builders (other worker) | 0 (recycle refunds) | +2–3 e/t to upgrade | immediate |
| RCL4 now | Stop extra ramparts (other worker) | saves ~0.5–1k | +sites energy to upgrade | immediate |
| RCL4→5 | Upgrade-max: 30 WORK, build only roads | — | upgrade 14→26–29 e/t; RCL5 ETA ~12.5 h (ideal) vs 26 h (current rate) | — |
| RCL5 | 10 ext (cap 1300→1800) | 30k | bigger bodies, fewer creeps, ~-1 e/t upkeep | ~30k t; required for RCL5 bodies |
| RCL5 | link A 26,12 → ctl 13,25 (pending OK) | 2×5k = 10k | -A hauler (0.6 e/t), -0.1 decay, +1 e/t to ctl | ~12k t (~14 h) |
| RCL5 | 2nd tower at **27,6** (north, 17:52) | 5k | east approach 540-600 dmg (was 150) | — |
| RCL6 | 10 ext, link hub, terminal, extractor, mineral trunk | ~10k ext + 5k link + 100k terminal | storage-centric logistics; ~-1 e/t haul | terminal no direct e/t payback; build after storage >30k |
| RCL7 | spawn 32,32 + 10 ext (200 cap each) | 15k + 20k | 2nd spawn, no queue blocking (38% upgrader queue_blocked now) | — |
| RCL7 | swap 5 temp ext near Spawn2 → v3b slots | 5×3k | haul -0.1 e/t | long; low priority, storage >50k |
| RCL8 | spawn 32,33; decide Spawn2 keep/remove | 15k | — | — |

Extension cost note: RCL5 extensions cost 3k each regardless (10 → 30k), RCL7 ext 200 cap still 3k each. Build order: closest to hub/haul
path first (hub ring, then link-road side), never near Spawn2.

ETAs (net upgrade 26 e/t at RCL4, ~28 at RCL5 with link, ~30 at RCL6+; tick 4.2 s): RCL5 (317k left / 26) ≈ 12.2k t ≈ 10-20 07:00;
RCL6 (1.215M / 28 ≈ 43k t ≈ 50 h) ≈ 10-22 09:00; RCL7 (3.645M / 30 ≈ 121k t ≈ 142 h) ≈ 10-28; RCL8 (10.935M / 30 ≈ 365k t ≈ 425 h) ≈ 11-14.
After RCL6 the limit is income (40 e/t gross), not logistics; only more remotes move RCL7/8 noticeably (+8 e/t net ≈ -25% time).

## Spawn relocation (decision: (a) keep Spawn2 until RCL7)
Facts: at RCL4–6 only ONE spawn is allowed, so moving means destroy Spawn2 then build 32,32 (15k). No home support (directive).
Spawn2 cluster = spawn 300 + 5 temp ext ×50 = 550 of 1300 cap (42%).
Haul cost of the far cluster: spawn spend ≈ 11.5 e/t × 42% ≈ 4.8 e/t carried an extra ~38 tiles round trip (hub 34,33 ↔ 15,18 ≈ 19 tiles)
→ 4.8×38/50 ≈ 3.7 CARRY ≈ 3.7×75/1500 ≈ **0.19 e/t**. Since the P0 hub-first fill order is live, the real figure is lower (~0.1).
| option | cost | gain | payback | risk |
|---|---|---|---|---|
| (a) keep, build 32,32 at RCL7 as 2nd spawn | 15k at RCL7 (needed anyway) | 0 now | — | none |
| (b) relocate now | 15k + no spawn ~600–1000 t (15k at ~20 e/t) → miners/haulers die, income falls toward 0, plus RCL5 delayed ~10 h (≈ 9k upgrade energy) | ≤0.19 e/t | 15k/0.19 ≈ 79k t ≈ **92 h**, plus downtime | high: no spawn under BustJetter threat, colony can collapse |
| (c) relocate at RCL5–6 | same as (b), still 1 spawn cap | same | ~90 h | same |
Conclusion: (b)/(c) lose ~25k energy and ~10 h of growth for a 0.1–0.2 e/t gain. (a) is fastest by net energy and has no risk.

## Remote candidates (need Misaki's approval, not deployed)
Adjacent unclaimed rooms not yet used: W48N8 (west), W48N7 (SW). Each 2-source remote at 1–2 rooms away adds ~+12–15 e/t gross,
minus ~5–6 upkeep (reserver + haulers) → net ~+7–9 e/t (+25–30%). Needs scouting (sources, Invader core, owner). W47N9/W48N9
are north, where BustJetter is; avoid. Without new remotes the ceiling is about 31 e/t net.

## Bodies
Local haulers 2:1 CARRY:MOVE on roads (already); remote haulers 1 WORK for road upkeep; upgraders max WORK with 1 CARRY + link at RCL5;
miners 5W (6W after RCL5 to absorb travel/latency). Reserver paid by home (existing arrangement).

## CPU
13.75 of 20 average with full bucket. A 3rd remote room adds ~1.5–2.5 CPU; still inside budget.

## Ownership / implementation now
Immediate steps (upkeep trim, W47N7 road, links at RCL5, rampart site removal) are owned by the two active workers. All RCL4 structures
already exist. No extra code deployed by this plan; it is a doc commit only.

## Tower slots (Misaki 17:52, tools/w47n8_tower_plan.py)
North approach = tiles y<=2 from which an enemy can hit a seal wall (east segment x24-31, west x8-11). Tower dmg 600 at r<=5 -> 150 at r>=20.
| slot | when | east approach min/avg | west min/avg | haul | notes |
|---|---|---|---|---|---|
| 33,35 (built) | RCL3-4 | 150 / 150 | 150 / 150 | 3 steps storage | core tower; kept, never destroyed (covers breaches into the hub) |
| 34,31 (old RCL5 plan) | — | 150 / 150 | 150 / 150 | beside storage | moved to RCL8 |
| **27,6** | **RCL5 (tower 2)** | **540 / 588** | 180 / 270 | 5 steps from source A container 26,11 (27 from storage) | swamp tile, off every road/post; r>=4 from all y<=2 tiles (enemy RA outside the seal cannot hit it) |
| **22,7** | RCL7 (tower 3) | 390 / 526 | 330 / 420 | 4 from 26,11 | covers both seal segments |
| 34,31, 36,31, 36,33 | RCL8 | core | | hub | |
ORDER.tower = 27,6 / 33,35 / 22,7 / 34,31 / 36,31 / 36,33 (layout.js + w47n8_plan3b.py). At RCL5: 33,35 + 27,6 -> east 690 min vs the
squad's 228 heal. Haulers refill towers via fillTarget (tower > 200 free); source A container 26,11 is the nearest stock.
Relocation of 33,35 at RCL4 is NOT planned: RCL4 allows 1 tower, so moving means destroying the only tower (5k rebuild, 0 towers
for ~300-500 ticks) under an active threat. RCL5 (ETA 10-20 ~07:00) adds 27,6 with zero gap.
17:58 hand-calc: a tower within 5 of y=3 near x28 (= 27,6) gives 600/t; focused with the defenders (~1050/t) vs both enemy groups' 396
heal/t turns scenario B from stalemate into a win. Today 33,35 adds only 150 at the wall; towerPick now counts tower + defender RA
together (3bdaefe), so it fires whenever the combined focus beats the heal. Render: tools/w47n8_tower_png.py -> /workspace/w47n8_tower_plan.png.
