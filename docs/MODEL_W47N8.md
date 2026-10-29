# W47N8 energy-flow model (`tools/model_w8.py`)
Rerun every W47N8 patrol iteration: `.venv/bin/python tools/model_w8.py [--hours 6]` → stage table on stdout, `metrics/model_w47n8.json`,
`model_params` rows `w8.*` (ideal vs actual, Grafana), and `Memory.ops.w8model = {rcarry, lcarry, upw}` (read back), which the spawn rules use.

Model: real terrain + live objects for W47N8 + W47N7 (one grid, seam W47N8 y=49 ↔ W47N7 y=0), Dijkstra road 1 / plain 2 / swamp 10,
ticks/tile from the live hauler bodies. Per source 10/t (owned/reserved) − container decay (0.1 owned / 0.5 remote) − miner upkeep −
hauler upkeep (CARRY need = 10 × (round trip × 1.10 + 4) / 50, load split 75% ctl cont 13,26 / 25% hub 33,33). Shared: roads, ramparts
0.03/t each, builder-lite 1000/1500. Upgrade = net / (1 + upgrader upkeep 1150/1500/10). RCL5: 1800 cap, best of source-A link→ctl or hub→ctl link (3% loss).
reserve7 (2 CLAIM) is spawned and paid by home.

## 2026-10-19 14:55 (6 h window, threat mode on for part of it; tick 4.20 s)
| stage | ideal | actual |
|---|---|---|
| mining A / B (local) | 10 / 10 | 10.0 / 9.6 (miners 93% working) |
| mining R1 / R2 (W47N7) | 10 / 10 | rminers 93% working; conts 1080 / 920 |
| round trip A / B / R1 / R2 | 48 / 38 / 99 / 132 t | — |
| local haul CARRY | 20.5 | 30 (3×10C10M; 80% moving, 11% blocked) |
| remote haul CARRY | 52 | 88 → 74 (14C7M/16C8M; 82% moving, 12% blocked) |
| net to sinks | 32.2 | upkeep live 12.7 (excl. reserve7) vs ideal ~6.8 |
| upgrade | 29.9 e/t (30 WORK) | 9.9 e/t (10–20 WORK, 41% queue_blocked) |
| build/repair | 0 (steady) | 13.4 e/t (seal walls + core ramparts to 50k, sites) |
| storage Δ | buffer | 0 (storage 316) |
| RCL5 ETA | 13.9 h | 42 h at 6 h rate |
| RCL5 ideal (links) | 30.3 e/t (link A→ctl) | — |

Balance: ~39 e/t mined ≈ 9.9 upgrade + 13.4 build + 12.7 upkeep + ~1.5 decay/carry-over. Upgraders are starved by allocation, not transport:
a third of income goes to walls/sites (threat-mode directive, temporary), and the fleet costs ~6 e/t more upkeep than ideal, mostly
oversized remote haulers (sized by loose-pile thresholds).

Fixes (0c590f1): remote haul fleet sized from model CARRY need (floor 60% ahead of builders, 110% + backlog term in step 7, max 8)
instead of loose thresholds; upgrader WORK cap = model `upw` (~30) instead of fixed 24 (applies when not in threat wall mode).
Next: local hauler 2C1M body on the fully paved local routes (−25% hauler upkeep); storage buffer once walls are done; RCL5 link A→ctl.

## 2026-10-19 15:10 bottleneck pass (allocation, not just upgrade)
6 h allocation (model `alloc` line, e/t): harvest 37.4 (miners 94%, rminers 93% working) = upgrade 9.9 + build/repair 13.1 + storage 0
+ upkeep 11.3 (excl. home-paid reserve7) + decay/stock/tower 3.2. Containers held ~9.6k idle stock (all 1.2-1.8k / 2000, W47N7 31,34 at 1790).
Findings:
- Sinks, not supply, bind: 1 upgrader (threat rule, walls < 50k) + 4 builders 64% walking. Walls 401k/750k hits at 15:05 -> done ~15:35.
- Remote haulers lost most of each trip inside W47N8: 24-143 ticks/trip filling single 50-energy extensions across the hub and
  flipping ctl <-> hub (w8rhauler83738293). Fix (0772f8b): no extension detours; one adjacent top-up in passing, fill duty only when spawn energy < 300 or no w8hauler -> ctl/hub cont -> storage.
  Measured after: in-room time per trip ~40-45 t (was 24-143, median ~70).
- Local hauler 10C10M on fully paved routes -> 10C5M (same 500 carry, -0.5 e/t upkeep).
- Upgrader count base was "2 while any site" (3 road sites ~700 left) and storage stock was invisible to it: base now by build backlog
  (>= 3000 -> 2, else 3), storage above 2k counts as stock, WORK cap = upw + 5 per 5k stored (max 40 = 4 stands x 10W).
Projected after walls: upkeep ~9.5, build ~1-2, upgrade ~24 e/t (30 with stock) -> RCL5 ~17-18 h (≈ 10-20 09:00-10:00 UTC+8).
RCL5 link proposal (needs approval, adds 2 tiles to v3b): ctl link 13,25 (dead-end tile beside stands 12,25/12,26/14,26) + source-A
link 26,12 (beside stand 26,11) -> model 30.3 e/t; v3b hub link 33,34 at RCL6.

### 16:15 after (18f621f, 0772f8b, 9c3162c, ab1a912)
- Walls/core ramparts reached 50k ~15:47; wall-mode gate now enters below 45k (rampart decay no longer flips it back).
- Upgrade: 20 e/t (2 upgraders) -> 40 e/t from t83740650 (4x10W) while the ~8k container stock drains; sustained ~25-27 e/t once
  stock is gone (4th upgrader not replaced unless storage >= 5k). 200-tick avg 24.4 (still part 2-upgrader).
- Upkeep live 12.0 (transitional: 4 upgraders, 5 haulers -> max 4, 2 leftover 6W builders) -> ~10 steady.
- RCL5 at ~25.5 e/t: 332k left -> ~15 h (10-20 ~06:00-09:00 UTC+8), was 42 h.

### 18:05 loss pass (a2523dd, cefd388, 233b0b8)
| e/t | 17:10 (1 h) | 18:00 (290 t, threat + filler buffer) | steady target (no threat) |
|---|---|---|---|
| harvest (40 max) | ~37 (local miners 85%) | ~31 (1 rminer holding in base on flee) | ~39 (6W miners) |
| rhaulers | 4.2 (75 CARRY) | 4.2 | 3.1 (56 CARRY) |
| upgraders | 2.3 | 2.3 | 2.3 |
| local haulers | 1.0-2.5 | 2.0 | 1.5 (3x10C5M) |
| builders | 2.4 (3x6W) | 0 | 0-0.6 |
| miners + rminers | 1.7 | 1.7 | 1.8 |
| filler | - | 0.6 | 0.6 |
| local defenders | - | 2.5 (home-sent 2.9 paid by home) | 0 |
| decay (conts 1.4, roads 0.2, ramparts 0.3) | 1.8 | 1.9 | 1.9 |
| build (rhauler WORK roads) | ~4 (builders' non-upgrade share) | 0.5 | 0.5 |
| storage | 0 | +3.6 (filler reserve fill, one-off) | 0 |
| upgrade | 20.3 | 10.5 | ~27 |
W47N7 road: 25 tiles missing = 6.9k energy for ~0.3 e/t (6 CARRY fewer) -> ~27 h payback; left to in-passing rhauler WORK, not accelerated.
Reserver (home-paid 2.17 e/t) doubles both W47N7 sources (+10 e/t): keep.

## 2026-10-19 21:4x strategy review: why upgrade is ~2/3 of ideal and the ctl container keeps emptying
6 h window to t83745409 (RCL4 165.2k/405k), model ideal 29.8 e/t, actual 21.1 e/t. Gap 8.7 e/t, all accounted for:
| item | ideal | actual | gap e/t | note |
|---|---|---|---|---|
| harvest (4 sources) | 40 | 38.2 | 1.8 | local A/B full (A 0 left at ttr 48); **W47N7 5W rminers lose ~10%** (below) |
| upkeep (excl. home-paid reserve7) | 8.5 | 11.2 | 2.7 | wrhauler 4.17 vs 2.7 (60 vs 48 CARRY), whauler 1.5 vs 1.0, wfiller 0.6 unmodelled (known, roadmap watch) |
| build (W47N7 roads by rhauler WORK) | 0 | 2.5 | 2.5 | temporary: 3 sites left at 21:13 |
| decay/tower/stock (waste_other) | 1.7 | 3.0 | 1.3 | tower heal/rampHold repair, container stock swings |
| storage | 0 | +0.4 | 0.4 | |
**Ctl container 13,26:** 30 WORK upgraders can burn 30 e/t; ~21 e/t reaches it, so it drains to 0 and refills in cycles (upgraders
queue_blocked 29%). That is the symptom of the energy gap above, not a routing fault — no hauler-priority change (as at 19:5x).

**Root cause found (new): remote container repair blocks harvest.** Reserved (unowned) room containers decay 5000 hits / 100 t = 50 hits/t
(CONTAINER_DECAY / CONTAINER_DECAY_TIME; owned room 500 t). `repair` and `harvest` share one action pipeline (docs.screeps.com
simultaneous-actions: the right-most wins, harvest is blocked). The w8rminer body was 5W1C3M = exactly 10/t with no slack, repairing
whenever the container is < 50% (both W47N7 containers sat at exactly 125,000/250,000 at t83745439), i.e. 1 tick in 10 → ~9 e/t per
source, plus every replacement gap lost for good. Live: R2 30,35 had 900 energy left at ttr 32 (t83745419). Home solved the same issue on
10-15 (`rmBody` 6W, measured 8.7 → 10 e/t); W47N8's module never got the port. The replacement lead was a fixed TTL 100 vs ~70 t walk
(R2) + 30 t spawn + queue behind upgraders/filler on the single Spawn2.
**Fix (751c6e7 t83745490 + guard 3ce6174 t83745499):** w8rminer 6W1C3M (800; empty CARRY weighs nothing → 1 tile/t on road;
250 harvest + ~25 repair ticks per 300 → full 10/t, +25 t slack), replacement lead = learned walk (`Memory.ops.w8rlead[si]`, set on first
reaching the source, only 1–300 t) + 3×parts + 20, default walk 90 → 140 t for the 10-part body. Upkeep +0.13 e/t. Expected +1.5–2 e/t
to upgrading once both rminers are replaced (current ttl 735 / 1150 at t83745493 → ~22:35 and ~23:05 UTC+8). `tests/w47n8_rminer.js`.
Model: remote miner cost 800; the `alloc` harvest proxy is now 2 × WORK × working per source capped at 10 (it was 10 × working, which
read 6W miners waiting for regen as lost harvest: 35.2 → 38.2 for the same window).
**Verify (w8patrol):** after each replacement, W47N7 source energy at ttr < 30 should be ~0; `Memory.ops.w8rlead` ~45–75; no rminer gap.
Remaining levers in order: (1) roads finish → build 2.5 → ~0.5 by itself; (2) hauler sizing at natural replacement (~+1.3, roadmap);
(3) RCL5 links (non-divertible ctl feed). With (1)+fix: ~24–25 e/t → RCL5 ~10-20 09:30–10:30 UTC+8 (ideal 9.3 h).

## 2026-10-29 11:4x strategy review: RCL6→RCL7 upgrade ~24 vs ideal ~30

**Question:** why is W47N8 stuck at ~23–24 e/t while the link-aware model says ~30, and what safe lever closes the gap?

**Live (tick ~83935480, 6 h window ~1970 t, cov 0.55):** RCL6 2.605M/3.645M, storage ~2.5k, ctl cont 13,26 ~1.1k, towers 2, sites 0.
Links **live and transferring**: A 26,12 → ctl 13,25 (both hold energy; hauler pickup at A = 0, link-meter artifact).
| stage | ideal (linkA→ctl) | actual |
|---|---|---|
| harvest (4 sources) | 40 | 38.5 |
| upgrade | 30.2 | 23.8 |
| upkeep (excl. home-paid reserve7) | ~6.5 | 10.8 |
| build/repair | ~0.7 | 1.1 |
| waste_other (decay/tower/stock) | ~1.7 | 2.8 |
| local CARRY need / live | **9** (B only) | **30** (3×10C) |
| remote CARRY need / live | 48.6 | 60 |
| wupgrader waiting_feed | — | 0.15 |
| delivered haulers ctl / hub | 75/25 mix | 15.5 / 18.1 |

**Gap ~6.4 e/t, accounted for:**
1. **waste_other ~2.8–3.4** — tower rampHold / road repair + container stock swings under the north-seal defense posture. By design at RCL6 with wall 300k; not a routing bug. TooAngel feeds the controller from storage beside the upgrader; we already have the Screeps-docs pattern (source-A link → ctl link), so architecture is fine.
2. **Fleet upkeep +2–3 vs ideal** — local haul stuck at 3×10C (HMAX floor 3) even though link-era need is ~9 CARRY + ~10 refill ≈ 2 haulers; remote 60 vs 48.6. Mild.
3. **waiting_feed 15%** — ctl is fed (cont ~1k, link draining) but not saturated; remotes still dump hub-first (hub delivered 18 > ctl 15). Not starving; hub→ctl link (gated `HUB_LINK=false`) stays optional.

**Root cause found (observability / spawn feed):** `tools/model_w8.py` wrote `Memory.ops.w8model.lcarry` from the **no-link** flow F4 (~22, still prices A haul) even after A→ctl links existed. Spawn `HMAX = max(3, min(4, ceil((lcarry+10)/10)+1))` therefore never saw the link-era need. Fixed this review: when both links are live, Memory gets `lcarry≈9`, `upw≈31`, `links:true` from the link-aware flow; Grafana `w8.upgrade` ideal also switches. **HMAX floor dropped to 2 when `Memory.ops.w8model.links`** (patrol 2026-10-29 15:54, post-raid abort): saves ~0.5–1.5 e/t local hauler upkeep; pre-link rooms keep floor 3. Unit test covers both.

**Plan recalibration (no Misaki decision):**
- Steady RCL6 upgrade under current defense: **~23–24 e/t** (not 30). Trimmed (HMAX→2 + quieter waste): ~26. Ideal 30 only with zero tower/stock waste.
- Remaining 1.04M at 23.8 e/t × 4.36 s/t ≈ **53 h → ~2026-10-31 16:00 UTC+8**; at 26 ≈ 48 h; at 30 ≈ 42 h.
- RCL7 gate unchanged: layoutRun places tower#3 (22,7) + spawn#2 (33,30) automatically; no early place (ERR_RCL_NOT_ENOUGH confirmed).
- Do **not** enable `HUB_LINK` / minerals yet; waiting_feed is mild and storage is thin (~2k).

**Verify (next model_w8 / w8patrol):** `Memory.ops.w8model.links === true` and `lcarry` ~9; local CARRY should fall toward ~20 (2×10C) as the 3rd hauler ages out; upgrade target ~24–26 while waste_other ~3.
