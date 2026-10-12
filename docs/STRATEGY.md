# Strategy — single room, 20 CPU, shard3 (W46N8)

Sources: Screeps docs (control, defense, CPU limits), screepers wiki, and patterns common to open-source bots
(Overmind: bunker + static miners + haulers + "colony" managers; TooAngel: data-driven roles, conservative CPU;
Hivemind: room planner that scores layouts, min-cut ramparts, remote mining as main growth; screeps-bot-choreographer:
priority-queue spawning and kernel/process scheduling). The common conclusions:

1. **Energy throughput is everything early.** A room with 2 sources yields 20 energy/tick max (2×3000/300). Generic
   harvest-and-carry creeps reach ~50–60%; **static miners on containers + haulers** reach ~100%. Do this at RCL2–3.
2. **Upgrade hard, build only what unlocks the next step.** Extensions before roads; roads before more creeps.
3. **CPU (20/tick) is the binding constraint later.** Fewer, bigger creeps (body cost scales with energyCapacity),
   cache `find()` results, path reuse (`reusePath`), run planners every 50–100 ticks, keep bucket ≥ 5000.
4. **Defence = towers + ramparts + safe mode.** Towers do most of the work; ramparts make structures untargetable;
   safe mode is the panic button (auto-trigger if spawn/tower hit while hostiles present).
5. **Growth beyond RCL4 comes from remote mining** (reserve neighbouring rooms) and later a 2nd room when GCL allows
   (GCL 2 already → we may claim a second room once the first is stable).

## Phases, milestones and triggers

| Phase | Trigger to enter | Goals / milestones | Exit criteria |
|---|---|---|---|
| P0 Bootstrap (RCL1) | spawn placed | 3 harvesters, 3 upgraders, 2 builders (done) | RCL2 (reached tick ~83594750) |
| P1 Economy (RCL2) | RCL2 | 5 extensions (layout plan), containers at both sources + controller, **static miners (WORK×5) + haulers**, roads spawn→sources→controller | energyCap 550, sources ≥90% harvested |
| P2 Defence (RCL3) | RCL3 | tower #1, ramparts on spawn/tower, safe-mode auto-trigger, extensions → 10 | tower live **before novice ends 2026-10-28 03:33** |
| P3 Storage (RCL4) | RCL4 | storage, 20 extensions, upgraders pull from storage, rampart HP 50k | storage > 50k energy |
| P4 Links + remote (RCL5) | RCL5, bucket > 7000 | controller link + core link, tower #2, 1–2 remote rooms (reserver + miners) | CPU avg < 15 |
| P5 Minerals (RCL6) | RCL6 | terminal, extractor, 3 labs, source links | terminal active |
| P6 Expand (RCL6+, GCL≥2) | stable economy, CPU headroom ≥ 5 | claim 2nd room (needs user approval) | 2nd room RCL3 |
| P7 RCL7–8 | — | spawns 2–3, factory, 6 towers, power spawn, nuker, observer | RCL8 |

## Standing rules
- Never let harvesters drop to 0 (emergency body from energyAvailable) — done.
- Keep ≤ 5 construction sites active; planner runs every 50 ticks or on RCL change — done.
- Every upload passes `scripts/check.js`.
- Major decisions (claims, attacks, spending pixels/credits, safe mode outside emergencies) need user approval.
