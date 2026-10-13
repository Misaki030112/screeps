# W46N8 layout review (2026-10-13) — v2 vs what top bots use

Inputs: real terrain `data/terrain_W46N8.txt`, plan `data/layout_W46N8_v2.json`. Tool: `.venv/bin/python tools/layout_review.py` →
`metrics/layout_review.json`, image **`docs/layout_review.png`** (numbers = RCL built; green fill = min-cut rampart line).

## 1. What strong players/bots do (summary of the common approaches)
| Approach | Who / where | Idea | Fit for W46N8 |
|---|---|---|---|
| **Bunker** (13×13 or 11×11, symmetric) | Overmind (bencbartlett), many older bots | Everything in one square; 1–2 queens walk a ring; a rampart square around it (≈50–60 ramparts). | Doesn't fit around Spawn1 (35,28): 13×13 only fits at x10–24/y3–17 ⇒ would need a new spawn. Already rejected in LAYOUT_V2. |
| **Stamps** (fast-filler 5×5, hub/core, 4×4 lab stamp, placed by distance transform) | Tigga, hoho-style, most current top bots; "diamond" is a fast-filler variant | Stationary fillers next to every extension, link-fed; hub manager touches storage/terminal/link/factory/PS; labs in a stamp where 2 inputs reach 8 outputs. | **This is what v2 is.** |
| **Dynamic / road-heavy** (TooAngel and others) | TooAngel | Place structures along roads near the spawn; walking queens/haulers. | Simple but lots of roads and walking; our v1 was like this (116 roads). |
| **Distance transform + flood fill + min-cut** (Screeps wiki "base planning", saruss min-cut) | Most planners | Distance transform finds open space for stamps; min-cut finds the fewest rampart tiles separating the base from exits. | Applied below. |

## 2. v2 scored on real terrain (RCL8 final plan)
| Metric | v2 | Reference / comment |
|---|---|---|
| Energy structures (60 ext + 3 spawns) touching a stationary creep | **60 / 63** | the 3 exceptions are RCL8 ext (33,29) (34,29) (32,28) |
| Max structures per filler | 7 | |
| Full refill at RCL8 (ext 200 each, all fillers in parallel) | **≈14 ticks**, 0 walking, 0 `find` | bunker queen ≈110 ticks (≈60 transfers + ≈50 tiles) |
| Storage → source B / source A | **1** (miner transfers directly) / 21 ticks (link from RCL6) | |
| Storage → controller (range 3) / mineral | 6 / 7 | controller link from RCL7 |
| Storage → filler A container / B link / C link | 9 / 8 / 16 | B, C fed by links (0 walking) |
| Labs reachable by 2 inputs | **8 / 8** | |
| Towers (6): minimum damage on any open tile | **900/t**; ≥2 910 at core ramparts | |
| Roads | 34 (8 on swamp) | v1: 116 |
| Point ramparts (v2) | 27 (only on key structures) | |
| **Min-cut rampart line** (protect every structure + creep spots) | **26** (no buffer) / **33** (2-tile buffer vs ranged) | bunker ring ≈50–60 |

Conclusion: v2 already follows the modern stamp approach and is near the practical optimum here: refill is ≈8× faster than a bunker, CPU ≈3 at RCL8, the
room's natural chokes give a 33-tile perimeter. **No v3, nothing to demolish.**

## 3. Proposed v2.1 tweaks (future entries only, nothing built yet is touched)
1. **3 orphan RCL8 extensions** (33,29) (34,29) (32,28) touch no filler and every tile next to a filler is used. Option: keep them, put them **last** in `spawnCreep(…, {energyStructures})` and let the queen top them up only when < full (≤600 energy, 5% of capacity). Cost: no walking in normal operation.
2. **Min-cut perimeter instead of only point ramparts** from RCL5–6: 33 ramparts on the chokes (green on the image) protect everything incl. labs, upgraders and the source-A link; point ramparts stay on spawns/towers/storage. Build 33 × 1 energy, repair to RCL6 target 300k hits ≈ 3 000 energy each (≈100k total, spread over RCL6), decay ≈ 33 × 300 hits/100 ticks ≈ **1 energy/tick**. Safe-mode/novice until 10-28 covers the gap; decide at the 10-25 defence review.
3. Keep the swamp road tiles (8): they are on the only trunk; 5× decay costs ≈0.4 energy/tick in total.

## 4. Per-RCL build plan (from data/layout_W46N8_v2.json)
| RCL | Structure | Count | Coordinates | Why |
|---|---|---|---|---|
| 1 | spawn | 1 | (35,28) | fast-filler stamp edge / hub (RCL8 spawn3 spawns manager in place) |
| 2 | container | 4 | (35,24) (31,12) (38,32) (30,30) | buffer at miner/controller/filler entrance |
| 2 | extension | 5 | (33,24) (33,25) (33,26) (33,27) (33,28) | every one touches a stationary filler: 0 walking to refill |
| 2 | road | 28 | (36,32) (37,32) (38,31) (38,30) (38,29) (38,28) (38,27) (38,26) (38,25) (38,24) (37,23) (36,23) (35,22) (34,21) (33,20) (32,19) (33,18) (34,17) (35,16) (34,15) (33,15) (32,14) (31,13) (35,32) (34,31) (33,30) (32,29) (31,29) | single trunk + spurs only (34 tiles total) |
| 3 | extension | 5 | (34,24) (34,26) (34,28) (35,25) (35,27) | every one touches a stationary filler: 0 walking to refill |
| 3 | rampart | 2 | (35,28) (36,29) | core point ramparts (see min-cut proposal) |
| 3 | tower | 1 | (36,29) | inside core, spread so min room-wide damage ≥900/tick |
| 3 | road | 3 | (41,22) (42,21) (43,20) | single trunk + spurs only (34 tiles total) |
| 4 | extension | 10 | (36,24) (36,26) (36,28) (37,24) (37,25) (37,26) (37,27) (37,28) (36,31) (37,30) | every one touches a stationary filler: 0 walking to refill |
| 4 | storage | 1 | (37,31) | touches manager tile and source-B miner (direct transfer) |
| 4 | road | 1 | (34,30) | single trunk + spurs only (34 tiles total) |
| 4 | rampart | 14 | (37,31) (36,30) (34,25) (34,27) (36,25) (36,27) (33,33) (31,33) (33,35) (31,35) (31,26) (31,24) (29,26) (29,24) | core point ramparts (see min-cut proposal) |
| 5 | link | 2 | (35,26) (37,29) | storage hub / filler centres / source A / controller |
| 5 | container | 1 | (34,34) | buffer at miner/controller/filler entrance |
| 5 | extension | 10 | (34,32) (33,32) (32,32) (31,32) (30,32) (34,33) (32,33) (30,33) (33,34) (31,34) | every one touches a stationary filler: 0 walking to refill |
| 5 | road | 1 | (35,33) | single trunk + spurs only (34 tiles total) |
| 5 | tower | 1 | (37,33) | inside core, spread so min room-wide damage ≥900/tick |
| 5 | rampart | 1 | (37,33) | core point ramparts (see min-cut proposal) |
| 6 | extension | 10 | (34,35) (32,35) (30,35) (34,36) (33,36) (32,36) (31,36) (30,36) (32,27) (32,26) | every one touches a stationary filler: 0 walking to refill |
| 6 | terminal | 1 | (35,31) | hub, manager reach |
| 6 | link | 1 | (30,11) | storage hub / filler centres / source A / controller |
| 6 | container | 1 | (39,24) | buffer at miner/controller/filler entrance |
| 6 | extractor | 1 | (40,24) | on mineral |
| 6 | lab | 3 | (34,22) (35,21) (33,21) | 4×4 stamp, 2 inputs reach all 8 |
| 6 | rampart | 1 | (35,31) | core point ramparts (see min-cut proposal) |
| 7 | spawn | 1 | (30,34) | fast-filler stamp edge / hub (RCL8 spawn3 spawns manager in place) |
| 7 | container | 1 | (30,27) | buffer at miner/controller/filler entrance |
| 7 | extension | 10 | (32,25) (32,24) (32,23) (31,27) (31,25) (31,23) (30,26) (30,24) (29,27) (29,25) | every one touches a stationary filler: 0 walking to refill |
| 7 | factory | 1 | (35,30) | hub |
| 7 | lab | 3 | (33,22) (34,20) (34,23) | 4×4 stamp, 2 inputs reach all 8 |
| 7 | road | 1 | (31,28) | single trunk + spurs only (34 tiles total) |
| 7 | rampart | 3 | (30,34) (35,30) (35,34) | core point ramparts (see min-cut proposal) |
| 7 | tower | 1 | (35,34) | inside core, spread so min room-wide damage ≥900/tick |
| 7 | link | 1 | (30,31) | storage hub / filler centres / source A / controller |
| 8 | link | 2 | (32,34) (30,25) | storage hub / filler centres / source A / controller |
| 8 | extension | 10 | (29,23) (28,27) (28,26) (28,25) (28,24) (28,23) (30,23) (33,29) (34,29) (32,28) | every one touches a stationary filler: 0 walking to refill |
| 8 | spawn | 1 | (35,29) | fast-filler stamp edge / hub (RCL8 spawn3 spawns manager in place) |
| 8 | lab | 4 | (35,20) (35,23) (36,21) (36,22) | 4×4 stamp, 2 inputs reach all 8 |
| 8 | nuker | 1 | (38,23) | beside trunk |
| 8 | observer | 1 | (33,31) | any free core tile |
| 8 | rampart | 6 | (35,29) (36,34) (32,30) (32,31) (38,23) (36,33) | core point ramparts (see min-cut proposal) |
| 8 | powerSpawn | 1 | (36,33) | hub |
| 8 | tower | 3 | (36,34) (32,30) (32,31) | inside core, spread so min room-wide damage ≥900/tick |
| 4 | **remove** container | 1 | (38,32) | source B miner transfers straight into storage |
| 6 | **remove** container | 1 | (31,12) | source A link built; optional — keep as overflow buffer if container cap allows |

Fixed creep spots: manager (36,30); fillers A (34,25)(34,27)(36,25)(36,27), B (33,33)(31,33)(33,35)(31,35), C (31,26)(31,24)(29,26)(29,24);
upgraders (30,30)(31,30)(29,30)(31,31)(29,31); miners (31,12) (38,32); mineral miner (39,24).
