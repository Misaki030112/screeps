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
| RCL5 | 2nd tower at **24,8** (north, Misaki 18:06) | 5k | with 33,35: east 600 min / 681 avg, west 420 / 510 (was 150) | — |
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
| **24,8** | **RCL5 (tower 2, Misaki 18:06)** | **450 / 531** | 270 / 360 | 3 steps from source A container 26,11 (25 from storage) | plain, no road/post/ext/link conflict, r=6 from every y<=2 tile, connectivity ok |
| 27,6 | (17:52 proposal, replaced) | **540 / 588** | 180 / 270 | 5 steps from source A container 26,11 (27 from storage) | swamp tile, off every road/post; r>=4 from all y<=2 tiles (enemy RA outside the seal cannot hit it) |
| **22,7** | RCL7 (tower 3) | 390 / 526 | 330 / 420 | 4 from 26,11 | covers both seal segments |
| 34,31, 36,31, 36,33 | RCL8 | core | | hub | |
ORDER.tower = 24,8 / 33,35 / 22,7 / 34,31 / 36,31 / 36,33 (layout.js + w47n8_plan3b.py). At RCL5: 33,35 + 24,8 -> east 600 min, west 420 min vs the
squad's 228 heal. Refill of 24,8 (19:5x review, 75f8265): see "RCL5 transition" below; road 23,8 is adjacent, 25,10/25,12 lead to source A.
Relocation of 33,35 at RCL4 is NOT planned: RCL4 allows 1 tower, so moving means destroying the only tower (5k rebuild, 0 towers
for ~300-500 ticks) under an active threat. RCL5 (ETA 10-20 ~07:00) adds 24,8 with zero gap. Misaki 18:06: 33,35 is NOT relocated.
17:58 hand-calc: a tower within 5 of y=3 near x28 (= 27,6) gives 600/t; focused with the defenders (~1050/t) vs both enemy groups' 396
heal/t turns scenario B from stalemate into a win. Today 33,35 adds only 150 at the wall; towerPick now counts tower + defender RA
together (3bdaefe), so it fires whenever the combined focus beats the heal. Render: tools/w47n8_tower_png.py -> /workspace/w47n8_tower_plan.png.

## RCL5 transition (2026-10-19 19:5x strategy review, tick 83743900, deployed 75f8265)
Live at 19:45 (t83743815): RCL4 130.3k/405k, 20/20 ext (15 v3b + 5 temp), tower 33,35, storage 35,32, 0 sites, 0 hostiles.
**ETA RCL5: 274.7k left at 24-30 e/t (live ~30, 45-min window 24) x 4.2 s/t = 10.7-13.4 h -> 10-20 ~06:30-09:15 UTC+8 (central ~07:30).**

Tower slot check (Misaki 18:06): layout.js ORDER.tower[0] = **24,8**, 33,35 second (built, kept), 22,7 RCL7, 34,31/36,31/36,33 RCL8.
tests/w47n8_tower_first.js asserts the only RCL5 site is the tower at 24,8 and no 2nd tower site at RCL4. Live code = 108baf0+ (deployed 18:09).
The 17:55 log line "verify the only new site is tower 34,31" predates the 18:06 decision and is superseded: **verify 24,8**.
Tile 24,8 is plain and empty live; road 23,8 adjacent (built), 25,10 / 25,12 built.

Build order at RCL5 (layoutRun): tower 24,8 (5k) alone -> 10 ext (30k) -> links 13,25 + 26,12 (10k, placed as the last ext sites go up).
Next 10 ext slots (ORDER 16-25): 39,34 39,35 39,36 28,34 28,36 30,27 32,27 37,37 39,37 27,34, all plain and empty live; their strip roads
(38,33-38,38 / 27-29,35 / 31,25-31,28) are built. Filler body at 1800: 20C10M (duty 1250). Storage exists (RCL4).
Link timing kept after extensions: links pay back in ~14 h (+1 e/t ctl, -0.6 hauler) while 1800 cap gives bigger defender/hauler bodies
for the defence; the whole 45k bill is ~1.5-2 h of income and moves the RCL6 ETA (~50 h) by < 1 h whichever order.

### Energy to tower 24,8 (Misaki 18:06: "ample energy supply")
Path costs (road 1 / plain 2 / swamp 10): hub POST 34,32 -> 24,8 = 23 tiles (~50 t round trip); source A container 26,11 -> 24,8 = 2 tiles;
source B 11,43 -> 24,8 = 40. Before 75f8265 the hub filler would walk the 50 t round trip whenever the hub was full (hub unattended
during that time = slower extension refill), and once link 26,12 exists nothing stocks 26,11 any more (the miner ships source A to the ctl).
Now (dormant until 24,8 + link 26,12 exist):
- **tower within 4 of source-A stand < 600 energy -> source-A miner skips the link**; harvest overflows into container 26,11 (stops at 1500).
  ~10 e/t = exactly one tower firing every tick. Haulers score 26,11 x3 and their nearest fill target from there is 24,8 (2 tiles, > 200 free).
- >= 600: source A goes back to link 26,12 -> ctl link 13,25.
- Hub filler serves only core towers (<= 8 of POST, i.e. 33,35); never walks north.
- First fill after the tower is built uses the same path (tower 0 -> 600 via 26,11, ~60-100 t).
Cost: while 24,8 is below 600 the controller loses the link's ~10 e/t; in quiet times the tower spends only on heal/rampHold (~0.2 e/t).

### Controller-feed stall (19:37, ~80 t) - no hauler-priority change
Cause: replacement spawn burst with storage < 100, so haulers filled spawn/extensions first (correct: spawn first) and 13,26 ran dry.
Energy was not lost (containers had room; 4 upgraders = 40 WORK vs upw 30 caught up after); cost ~2.4k progress-time = ~6 min of ETA.
Storage is now rising (1.6-1.9k) with defenders gone; RCL5 link 26,12 -> 13,25 gives the ctl a ~10 e/t feed that haulers cannot divert.
Revisit only if 13,26 empties again while storage > 3k (patrol watch, unchanged).

### Patrol checklist at RCL5
1. Only site = tower 24,8 until built; then ext sites (max 6 open) then links 13,25 / 26,12. No 34,31 tower site.
2. After link 26,12: w8miner si0 gets 1 CARRY (bodyFor); link transfers 400 at a time (linkRun); ctl link drained by upgraders on 12,25/12,26/14,26.
3. Tower 24,8 rises to >= 600 within ~100 t of completion via 26,11 (Memory: none; watch container 26,11 and tower energy).
4. Filler stays in the hub when only 24,8 is low.

## Threat-mode wall cap at RCL5+ (2026-10-20 06:3x strategy review, tick 83753035, deployed bc7bf57)
Question: with BustJetter camping W47N9 (north_watch keeps `w8threatN` fresh, threat mode effectively always on), what happens the
moment W47N8 reaches RCL5 (live t83753006: RCL4 354.8k/405k, seal walls 12/12 at 50.0-50.5k, ETA ~08:45 UTC+8)?
Finding: `TH.wallTarget(WALL_TARGET[rcl])` = max(rcl target, 50k) under threat, and both the spawn wall mode (`wallsLow`: 1-2 upgraders,
up to 3 builders) and the builder's threat job (`tj`, ahead of every construction site) used that full value. At RCL4 it is 50k (= floor),
so nothing showed. At RCL5 the target jumps to 100k: every seal wall would read "low" (< 90k), upgraders drop to 1-2 and builders repair
~600k hits (~6k energy, ~400 t) **before tower 24,8**; at RCL6 (300k) ~3M hits (~30k energy, hours on 1-2 upgraders), RCL7 1M worse.
That contradicts Misaki's rules: tower 24,8 first at RCL5 (18:06), threat floor 50k ahead of upgrading (14:23), per-RCL seal target only
from surplus (19:18).
Shipped bc7bf57: `TH.urgentTarget()` = 50k while threat is on, 0 otherwise. `wallsLow` and the builder `tj` cap at it; the per-RCL target
is unchanged for the surplus wall builder (spawn step 6) and the builder's after-sites repair path. RCL2-4 behaviour unchanged.
Siege repair of attacked walls (repairPick) is unaffected. tests/w47n8_threat_wall_cap.js fails on the old code (builder walks to the walls
instead of building 24,8). Live: errors 0, bucket 10000, urgentTarget 50000.
Patrol check at RCL5: the tower 24,8 site gets built while the camp persists, upgraders stay at 2 (sites) not 1, no wall mode.

## RCL6 gate (2026-10-20 03:4x strategy review, tick 83750598, deployed 7b0b0b4)
Question: what does layoutRun place the moment W47N8 hits RCL6 (ETA ~10-22 08:00-10:00: 1.215M at ~28-30 e/t)?
Finding (tests/w47n8_rcl6_gate.js on the old code): 10 ext (30k), hub link 33,34 (5k), **terminal 33,32 (100k), extractor 37,45 (5k),
3 labs 33,29-35,29 (150k)** and the extractor trunk roads. No W47N8 code uses the terminal, extractor, labs or hub link (no mineral
miner, no lab/terminal logic, linkRun only moves A -> ctl), and `siteRem >= 3000` would also hold upgraders at 2 + 4 builders through the
whole bill. That is ~260k idle energy, ~8.7k t (~10 h) of upgrade, ~20% of the RCL6->7 time lost. Same trap home hit on 10-15
(plan.RCL6_MINERALS).
Shipped: `config.RCL6_MINERALS=false` (terminal/extractor/labs + MINERAL roads not placed) and `config.HUB_LINK=false` (hub link 33,34
not placed). RCL6 still places the 10 extensions; RCL5 still places links 13,25 + 26,12 (asserted). Dormant until RCL6.
**Proposal for Misaki (not urgent, before ~10-22):** keep both off until there is a use. Options to revisit then:
(a) hub link 33,34 -> ctl link 13,25 fed from storage (needs a hub manager; worth it only if haulers can't keep the ctl container fed);
(b) terminal at W47N8 so home can `terminal.send` energy (cost ~3% at range 1) or minerals: only useful with a market/boost plan;
(c) extractor + labs: needs mineral miner + lab code, and only matters for boosts after novice end.

## Spawn relocation executed (Misaki order 10-20 13:39, supersedes decision (a))
- Spawn2 15,18 -> hub 32,32 (under the existing 32,32 rampart). RCL5 = 1 spawn, so `moveRun` (index.js) destroys the old spawn and
  places the 15k site next layout tick. Phases in `Memory.ops.w8move`: prep -> build -> ext -> done (`hold` = aborted).
- prep fires only when: no hostiles, TH.on()/invasion() quiet, storage >= 16k, spawn idle + energy full, 2 miners + 2 haulers TTL>=500,
  a builder TTL>=700. During prep/build upgraders are capped at 1 (bank). During build no other sites are placed.
- ext: the 5 temp extensions (13,16 14,15 16,15 17,16 12,16) are destroyed one at a time (storage > 3.5k, energy full) into
  v3b slots 27,36 30,26 32,26 37,38 39,38 (capacity dips 50 per swap, never more).
- Ramparts: held only when necessary: gate 29,3, ramparts over spawn/storage/tower/terminal and hub spawn slot 32,32
  (rampNeeded). Empty-slot ramparts 33,32 33,30 34,31 36,31 36,33 32,33 and old 15,18 (after the move) decay.
- Roads (tools/w47n8_roads.py, spawn2 trunk replaced by tower 24,8 trunk; spawn-cluster traffic not kept): 128 -> 101 planned tiles,
  35 dropped (decay, never dismantled), 8 added.

## Spawn-move bank (2026-10-20 14:4x strategy review, tick 83760038, deployed 2255f96)
The move (Spawn2 15,18 -> 32,32) fires from `w8move` phase `prep` only when storage >= MOVE_E (16k) and a builder with TTL >= 700 is alive
(moveReady 'ttl'). Live t83759997: storage 816, north line 84.8k-93.6k (stage-1 cap 100k), 3 builders 6W TTL 616/1402/1496, 3 upgraders
(two at TTL 39/84, so 1 after they expire; `moving()` caps upgraders at 1).
Two problems the review found in the path to the move:
1. **Builders spent the bank.** With 0 sites and the walls at the 100k cap, `w8builder` fell back to `w8upgrader`, which refills through
   `getEnergy` and may withdraw from storage. 3 x 6 WORK = ~18 e/t, about the whole W47N8 surplus (model_w8 6h: harvest 38.7, upkeep 13.4,
   1 upgrader 10), so storage would hover near the filler reserve until the builders died. Fix: during `prep` an idle builder parks on a
   `UPG_EXTRA` tile and does nothing. It still repairs walls/roads/containers and builds sites first, and the fallback returns after the move.
2. **No builder at the trigger.** Builders only spawn for sites, `wallsLow` or a wall below the plan target, none of which holds once the line
   is at 100k (constructed walls don't decay). The fresh builders' TTL drops below 700 in ~800 t, about when the bank would fill, so prep
   could stall on 'ttl' until the gate rampart decays under 90k by chance. Fix: in `prep`, once storage >= MOVE_E - 3000 and no builder has
   TTL >= 700 (or is spawning), queue one w8builder (6W6C6M, 1200 e) ahead of upgraders.
Expected timeline (estimate, ~4.3-5.7 s/tick): north line at 100k ~15-25 min after 14:45, then ~15 e/t net banking -> 16k after ~1000 t,
prep fires ~16:30-17:30 UTC+8, 15k spawn build ~300-500 t -> hub spawn 32,32 ~17:30-18:30, then stage 3 (300k) from surplus. W47N8 upgrade
runs ~10 e/t (1 upgrader) during the bank, so the RCL6 ETA slips by about the banking time (~1.5 h).
Test: `tests/w47n8_move_bank.js` (fails on the old code). Patrol check: builders parked (not upgrading) while `w8move.why` = ['storage'];
storage rising ~15 e/t once walls are at 100k; one fresh builder appears near 13k.

## RCL6 extensions after the move + road cut (2026-10-21 02:4x strategy review, tick ~83769925)
Question: W47N8 RCL5 259k/1.215M, RCL6 ~10-23. What does layoutRun place at RCL6 now that the spawn sits at 34,30 and the road plan was cut
to v4 (116 plan + 32 w8link tiles; 177 live roads, the rest decay)? Simulated `layoutRun` on the live structure list (/tmp/rcl6sim.js):
- RCL6 places only the 10 extensions (terminal/extractor/labs/hub link still gated off, RCL6 gate above holds). Bill 30k, ~1.3k t at ~23 e/t.
- **Gap found:** 4 of the 10 next ORDER slots (28,26, 37,39, 39,39, 27,24) have no neighbour on the v4 road plan: their stand tiles
  27-28,25 (strip 4) and 38,37-38 (x38 strip below 38,36) were dropped by the drastic cut and are decaying. Queens would walk off-road to
  refill them right when the refill priority matters most (Misaki: spawns never wait).
- **Fix (layout.js order only, no road added):** unbuilt slots re-ordered stably so slots touching a kept road come first. RCL6 now takes
  26,34 26,36 25,34 25,36 24,34 24,36 (y35 row, stand 24-28,35) + 30,25 32,25 30,24 32,24 (x31 column, stand 31,24-26); path cost from
  storage 6-9 vs 12-16 before. Test `tests/w47n8_rcl6_ext_roads.js` (fails on old order); all tests pass.
- **RCL7 note:** only 2 served slots remain (30,23 32,23). Before RCL7 (+10 ext, spawn 2 at 33,30) re-run the v4 road tool with the RCL7
  slots as goals, or choose RCL7 slots next to kept roads; don't re-add strip 4 (y25) roads blindly.
- Minor: plan road 18,49 (south exit tile) can never be placed (border tile), so layoutRun retries it each run; harmless, left as is.

## RCL7 day-of (2026-10-29 20:4x strategy review, tick ~83942750)
Question: the moment W47N8 hits RCL7 (~11-01 at ~20 e/t; live 2.740M/3.645M), what does `layoutRun` place, in what order, and are the new tiles road-served?

**Sim (`/tmp/rcl7sim.js` on live structure list + CONTROLLER_STRUCTURES):**
1. **First tick (sites budget 6, towerSite holds extensions):** `spawn@33,30` + `tower@22,7` only. Correct — same PRIO as RCL5 tower-first doctrine (`docs/DEFENSE_W47N8.md`).
2. **After spawn2 + tower3 built:** 10 extensions (ORDER slots 40–49: 30,23 32,23 28,26 37,39 39,39 27,24 27,26 28,24 37,40 39,40) then **`factory@35,30` (100k)**.
3. Minerals / hub link stay gated (`RCL6_MINERALS` / `HUB_LINK` still false). Live already has an extractor (Misaki-placed); gate only blocks new terminal/labs.

**Trap (same class as RCL6 gate 03:4x / home `plan.RCL7_INDUSTRY`):** Screeps RCL7 unlocks factory (100k). No W47N8 factory/lab code exists; placing it would steal ~5k t of upgrade (~6–7 h at ~20 e/t) and hold upgraders via `siteRem`. Home already gates factory via `plan.RCL7_INDUSTRY=false` (`docs/RCL7.md`).

**Road gap (flagged 10-21 02:4x, never fixed):** of the 10 RCL7 extension slots only **2** (30,23 32,23) touched the v4 road plan. Orphans: strip4 (27–28,24/26) and x38 strip (37/39,39–40). Queens would walk plain/swamp to refill the new 100-cap extensions right when spawn energy matters most.

**Tower3 northFeed:** `22,7` is range **4** of source-A stand `26,11` (edge of `northFeed` ≤4), so the miner overflow → 26,11 → short haul path still works once tower3 dips under 600. Live roads stop at x25; spur `24,7`/`23,7`/`22,8` gives an adjacent road without sitting on the tower tile.

**Shipped:**
- `config.RCL7_INDUSTRY=false` → layout zeros `factory` / `powerSpawn` / `nuker` / `observer` (RCL8-safe).
- `roads.js` +11 spur tiles (127 total, still one 8-connected network): strip4 bridge `27–30,25`; x38 `38,37–40`; tower3 `24,7`/`23,7`/`22,8` (~3.3k e).
- Day-of energy bill ≈ **53k** (spawn 15k + tower 5k + 10×3k + roads 3.3k), not 153k.
- Tests: `tests/w47n8_rcl7_gate.js` (fails on old code), `w47n8_roads_connected.js` wired into `scripts/check.js`.

**Day-of ops (autonomous, no Misaki decision):**
1. Let layout place spawn2 + tower3 first; do not flip `RCL7_INDUSTRY` / `RCL6_MINERALS` / `HUB_LINK`.
2. After those two stand, extensions + spur roads fill in; storage will be thin (~3k today) so builders pull from source overflow / ctl — expect upgrade to dip for a few hours.
3. Minerals / K→home send wait until **storage ≥20k** after tower3+spawn2 (`docs/MINERAL_DEFENSE_ROADMAP.md` §B).
4. Seal `planTarget` stays STAGE3 **300k** (WALL_TARGET[7]=1M unused); raise later via surplus after minerals, not on day-of.

## Soft-ramp staging (strategy 14:4x, 2026-10-30)

Before RCL7 day-of tower3/spawn2, KEY soft ramparts (spawn/tower/storage) climb to **100k** (`GATE_TOWER` = `SOFT_RAMP`). Seal walls + GATE@29,3 stay at **300k**. Soft raise: peacetime = `!threat.localOn()` (neighbor `w8threatN` does **not** block) + `SOFT_MIN=0` (17:4x — upgrade-first stor never hit the old 5k gate); spawn/gate always via GATE_TOWER. Cost ~1–1.8k e. See `docs/RCL7.md` 14:4x/17:4x. Factory still gated (`RCL7_INDUSTRY=false`).

## Day-of energy: no pre-bank (2026-10-30 20:4x strategy review)

**Decision:** do **not** hold upgrade to pre-bank ~50k before RCL7. Spurs are already live → bill ≈ **50k**. Existing `siteRem≥3k → ≤4 builders` + 2 upgraders finishes spawn+tower in ~15–20 min and the full batch in ~2–3 h while the controller keeps receiving ~10–12 e/t. Pre-bank would slip RCL7 by ~1–2 h for no gain. Overmind/TooAngel also react to sites, not RCL banks. Observability: `Memory.ops.w8day`. Detail: `docs/RCL7.md` 20:4x.

## 2026-10-30 23:4x — lean KO gate split
`RCL6_MINERALS` now means **logistics only** (terminal + extractor + `MINERAL_CONT` 37,44 + MINERAL trunk). Colony labs gated by **`RCL6_LABS`** (default false). See `docs/MINERAL_DEFENSE_ROADMAP.md` §5. Do not flip either gate until RCL7 day-of + stor≥20k + w8mminer/send.

## Day-of energy crash risk (2026-10-31 05:4x strategy review)

**Question:** With colony storage chronically ~1–3k, does the first RCL7 site wave (~20k spawn2+tower3, then ~30k ext) risk emptying towers / crashing `energyAvailable` so miners die?

**Answer: NO crash expected. Keep no-pre-bank. Watch north tower via `w8day.towerMinE`.**

### Live (t~83970965, Asia/Hong_Kong 05:46)
- Need ~247k → **RCL7 ~2026-10-31 ~17:40** Asia/Hong_Kong @~23 e/t (~910 t/h).
- `storE` 1561; `energyAvailable` **2300/2300 full**; towers **920/950**; soft COMPLETE; `w8model.links=true` `lcarry=9` → HMAX already 2.
- `w8day` bill 50k why=upgrade; gates OFF.

### Why spawn/eAvail holds
1. Local+remote income ~35–40 e/t continues through links while builders spend sites.
2. `w8filler` prioritizes spawn (−1e6 score); haulers `fillTarget(c,true)` include spawn/ext before `fed()` builders.
3. First wave sites budget 6 + `towerSite` holds extensions → only spawn+tower (~20k) first ≈ **15–20 min**, not the full 50k at once.
4. Overmind Hatchery / TooAngel also refill spawn before construction sinks; we already match that order.

### Residual risk (north tower only)
- `fill.js` `hubNeedy` blocks **filler** tower top-ups while any hub strip/point has free capacity — true often during builder spawns.
- Haulers still refill towers when `free>200`, but sticky `ft` + hub builder-feed can delay **north** tower 24,8 (and later 22,7). Hub tower 33,35 stays easy.
- Soft already COMPLETE; peacetime soft idle. Risk window = probe/BJ during the ~2–3 h day-of build if north tower <600.

### Observability shipped
`Memory.ops.w8day` now also reports `towerMinE`, `eAvail`, `eCap`. Patrol: if `why=dayof` and `towerMinE<500` → alert; if `eAvail` chronically ≪ body costs → alert. No fill-priority behavior change this run (propose later: filler ignore `hubNeedy` when towerE<500).

## Post-dayof leanBank → stor≥20k (2026-10-31 08:4x strategy review)

**Decision:** after day-of structures complete, **auto throttle colony upgrade** until storage ≥20k (`leanBank`, default ON). Does **not** pre-bank before RCL7 (20:4x stands). Does **not** flip mineral gates. Opt-out `Memory.ops.w8leanBank=false`.

Natural stor→20k under full upgrade never happens (24h proof stor stuck 0.5–3k). With ≤1 upgrader, ~1 h bank. Home upgrade untouched (separate economies). Detail: `docs/RCL7.md` 08:4x. Patrol: `w8day.phase` `bank20`→`ready`, `bankEta`, `leanBank`.

## 2026-10-31 11:4x — dormant w8mminer + haul→terminal
Shipped colony mineral **roles** behind `RCL6_MINERALS=false`: `w8mminer` (stand 37,44) + `w8hauler.mineralRun` (minCont→terminal). **No** `terminal.send` yet; **no** gate flip. See `docs/MINERAL_DEFENSE_ROADMAP.md` §5.9. After RCL7 day-of + leanBank ready, next code slice is send, then propose flip.
