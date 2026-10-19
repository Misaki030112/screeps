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
