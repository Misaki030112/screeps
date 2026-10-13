# Roadmap (priority order) — see docs/STRATEGY.md for phases

Novice zone ends ~2026-10-28 03:33 (UTC+8). Spawn safe mode active ~19.6k ticks (~21 h from 2026-10-12 17:40), 1 more safe mode available.

1. ✅ Extensions — placed from layout plan per RCL (layout manager).
2. ⏳ **Static miners + haulers + source containers** (containers already in plan at RCL2) — biggest economy win.
3. ⏳ Roads spawn→sources→controller — started 2026-10-12 22:32; 2026-10-12 23:12 builders split onto roads once lead site ≥40% + 3rd builder when backlog high.
4. ⏳ **Tower (RCL3)** — 2026-10-13 02:14: v1 RCL3+ extensions/roads HELD in layout.js (`HOLD`) because they conflict with draft layout v2; tower (36,29) + spawn/tower ramparts still auto-place. **Pending decision: Misaki approves layout v2 (docs/LAYOUT_V2.md) or keeps v1 → then remove/replace HOLD.** — tower manager already implemented (attack/heal/repair).
5. ⏳ **Ramparts** on spawn/tower (plan, after tower) + attack alerts to Misaki (NO auto safe mode — her decision). Deadline 2026-10-28.
6. Storage (RCL4); upgraders/builders withdraw from storage (energy util already supports it).
7. Links (RCL5: controller + core link; source links RCL6/7).
8. Remote mining: **W45N8 LIVE since 2026-10-13** (reserved, 1 source; see docs/REMOTE_W45N8.md). Watch diplomatic reaction from The Council (BustJetter/Fandalah). Upgrade reserver to CLAIM2 automatically at RCL4.
9. Perimeter min-cut ramparts; CPU optimisation (cached finds, path reuse); 2nd room claim (needs approval).

## 2026-10-13: Layout v2 live
- ✅ v2 layout manager (plan JSON → sites per RCL, safe conflict removal), fixed-position roles (miner spots, queen stops,
  upgrader spots), cached paths (`utils/move.js`), per-RCL role table (`managers/spawn.js`), link manager (RCL5+),
  tower repairs only planned structures. Multi-tick simulator `scripts/sim.js` runs in every check.
- ⏳ RCL3: 10 extensions at stamp A. 2026-10-13 09:56: 5 v2 built → gradual swap started (c4680d1: one v1 ext destroyed per 50 cap above 650, so the CLAIM1 reserver stays spawnable). v1 36,25 + 38,29 gone; 38,27 + 34,31 go as v2 sites finish; 36,31 kept (RCL4 plan ext), so 35,27 waits for RCL4.
- ⏳ RCL4 (ETA ~18:00–21:00 10-13 at 7–10/t during the build phase): storage (37,31); miner B delivers straight into storage; hub extensions.
- ⏳ RCL5: filler A link + hub link → stationary fillers + manager replace the queen; tower 2.
- Tuning: CPU is ~4 (vs ~3.6 before) while the 5 old haulers age out to the target of 2–3.

- [x] 2026-10-13 Continuous creep telemetry (ts.sqlite, segment 90 ring buffer, creep_audit.py windows/regressions/heatmaps) + simplified movement with fallback ladder.
- [ ] Use audit findings each patrol: fix worst creeps/roles; consider shared per-route path cache if repaths/100 stays high.
