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
