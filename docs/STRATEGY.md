# Strategy — W46N8 (home) + W45N8 (remote), 20 CPU, shard3

Sources: Screeps docs (control, defense, invaders, CPU), screepers wiki, Overmind / TooAngel / Hivemind patterns.
Last full refresh: **2026-11-09 17:1x** (autonomous push — docs/canvas scoreboard; waiting on bank20 ticks; no game code); before that **2026-11-09 14:3x** (north-star = T3 kiter; peacetime energy order unchanged); before that **2026-11-09 08:1x** (12h peacetime plan holds / leanBank→softCap clear); before that **2026-11-08 20:1x**; before that **2026-11-08 08:1x**; before that **2026-11-07 20:2x** (12h peacetime plan holds / leanBank→softCap clear + defender #1 ea-budget); before that **2026-11-07 08:1x**; before that **2026-11-06 20:1x**; before that **2026-11-06 08:1x**; before that **2026-11-05 20:2x** (12h post-W47N9 peacetime / severe cont debt 2nd maint); before that **2026-11-04 17:4x** (soft-band surplus trim / softCap hysteresis nUp4 thrash); before that **2026-11-04 14:4x** (post-abort maint cont debt); before that **2026-11-04 11:4x** (soft-band sticky preempt post-clear ctl sk); before that **2026-11-04 08:4x** (W47 link HMAX 3→4 overflow under softCap bank); before that **2026-11-04 05:4x** (leanBank rebuild-band upgKeep ≤2); before that **2026-11-04 02:4x** (hub ferry prime arm LEAN_ARM / thrash-band hubPrime); before that **2026-11-03 23:4x** (hub-link PRE-WARM during softCap bank / hubPrime); before that **2026-11-03 HUB_LINK nod YES** (`config.HUB_LINK=true`; hubReady waits on structure 33,34; labs/industry/market still OFF; sealMinE 25k; 20:4x soft-band kept); before that **2026-11-03 20:4x** (W47 soft-band ≠ softE / softCap re-ON drain); before that **2026-11-03 17:3x** (W47 post-roadCrit feedBound / !HUB_LINK ceiling); before that **2026-11-03 14:4x** (W47 roadCrit before deep seal / Overmind critical=25%); before that **2026-11-03 11:3x** (W47 container-first repair / Overmind <50% battery); before that **2026-11-03 08:4x** (softCap2 leanBank-style hysteresis LEAN_SOFT_ARM=22k); before that **2026-11-03 05:4x** (HUB_LINK flip day-of upgCeil→hubLinkLive); before that **2026-11-03 02:4x** (seal soft-gate vs softCap2 / no sealMinE raise); before that **2026-11-02 23:4x** (W47 HUB_LINK plumbing readiness / no flip); before that **2026-11-02 20:4x** (softCap thrash / sealMinE briefly 35k then Misaki→25k); before that **2026-11-02 17:4x** (post-war fortify vs softCap / sealMinE→LEAN_SOFT); before that **2026-11-02 14:5x** (W47N9 wartime economy freeze / GO); before that **2026-11-02 14:4x** (W47 peacetime ctl-battery surplus gate); before that **2026-11-02 11:4x** (W47 threat-soft holds w8upgrader ≤2 past `LEAN_SOFT`); before that **2026-11-02 08:4x strategy review** (W47 soft-band park deadlock / WORK-bound ~55%); before that **2026-11-02 05:4x** (home energy-bound / short-soft); before that **2026-11-02 02:4x** (W47 HMAX 2→3); before that **2026-11-01 23:4x** (thin-K + KO activate seq); before that **2026-11-01 20:4x** (post-minBuild leanBank re-arm); before that **2026-11-01 17:4x** (w8mminer vs soft-cap spawn prio); before that **2026-11-01 14:4x** (home KO labReady propose); before that **2026-11-01 11:4x** (first-K send pacing); before that **2026-11-01 11:1x** (RCL6_MINERALS flip); before that **2026-11-01 08:4x** (hold-band sink → stor20k); before that **2026-11-01 05:4x** (soft-cap survives RCL6_MINERALS flip); before that **2026-11-01 02:4x** (leanBank hysteresis 15k + soft-cap 25k); before that **2026-10-31 23:4x** (RCL6_MINERALS flipReady + post-flip leanBank hold); before that **2026-10-31 20:4x** (leanBank arm on day-crit, not 50ext); before that **2026-10-31 17:4x** (day-of north tower ≥600 / close hubNeedy residual); before that **2026-10-31 14:4x** (dormant terminal.send K→W46N8); before that **2026-10-31 11:4x** (dormant w8mminer + haul→terminal); before that **2026-10-31 08:4x** (leanBank → stor≥20k); before that **2026-10-31 05:4x** (day-of energy crash / `w8day.towerMinE`); before that **2026-10-31 02:4x** (home upgrade vs ideal 26 / `upgFeed`); before that **2026-10-30 23:4x** (W47N8 lean KO scaffold / `RCL6_LABS` split / w8min); before that **2026-10-30 20:4x** (RCL7 day-of no pre-bank / w8day); before that **2026-10-30 17:4x** (soft-ramp SOFT_MIN+localOn); before that **2026-10-30 14:4x strategy review** (W47N8 soft-ramp staging 100k); before that **2026-10-30 11:4x** (post-300k fundSpend exit / energy reallocation); before that **2026-10-30 08:4x** (RCL7 peacetime hold at 300k / no auto 1M); before that **2026-10-30 05:4x** (W45N7 Invader-res reclaim via attackController); before that **2026-10-30 02:4x** (STATIONARY_FILL readiness — keep queens); before that **2026-10-29 23:4x** (lab ramparts); before that **2026-10-29 20:4x** (W47N8 RCL7 day-of gate + spur roads); before that **2026-10-29 17:4x** (fortify fundSpend); before that **2026-10-29 14:4x** (mineral/boost §4); before that **2026-10-20 00:0x** (remote posture after novice end: `docs/DEFENSE_NOVICE.md`); before that **2026-10-19** (CPU `docs/CPU.md`, market `docs/MARKET.md`); before that **2026-10-18 strategy review** (W47N8 hold / safe-mode mechanics: `docs/W47N8_HOLD.md`); before that **2026-10-17 strategy review** (neighbours: `docs/NEIGHBORS.md`); before that **2026-10-16 strategy review** (defence before novice end: `docs/DEFENSE_NOVICE.md`); prior: RCL6 readiness `docs/RCL6.md` (10-15), RCL5 `docs/RCL5.md` (10-14). Also `docs/DEFENSE.md`, `docs/DEFENSE_PLAN.md`, `docs/LAYOUT_V2.md`, `docs/REMOTE_W45N8.md`, `docs/MODEL.md`, `docs/DATA.md`.

## Principles

1. **Energy throughput is everything early.** Two home sources = 20 e/t max; reserved remote adds ~10 e/t raw. Static miners + containers + haulers (then links) beat generic workers.
2. **Upgrade hard; build only what unlocks the next step.** Layout v2 is live (compact hub + fast-filler stamps, fixed roles, cached paths).
3. **CPU (20/tick) is precious.** Prefer fixed routes and stations over per-tick `find`. Keep bucket ≥ 5000. Measured ~3.5–4.5 CPU at RCL3 with remote.
4. **Defence = towers + ramparts + Misaki-controlled safe mode.** Towers do most early work; ramparts protect spawn/tower/core. **NEVER auto-activate safe mode** — alert Misaki and wait for her decision (standing rule since 2026-10-12).
5. **Growth after RCL4:** remote mining (W45N8 approved and live), then links; a 2nd room only with explicit Misaki approval (GCL 2 already allows a claim).
6. **Major decisions need approval:** claim/expand, attack or provoke player neighbours, spend credits/pixels, activate safe mode, respawn.
7. **Commander overlay is opt-in.** `Memory.cmd` (docs/COMMANDER.md) can take one creep or one structure and hand it back. It does not replace roles, and it must not write `Memory.ops` / `raidOrder` / softCap. Absent `Memory.cmd` means peacetime scripts are unchanged.

## North star (2026-11-09 ~14:3x · Misaki)

**Goal:** field (then sustain) at least one Tom-Roy-class full-T3 RA+self-heal kiter (4T/28RA/8H/10M; XGHO2×4 XKHO2×28 XZHO2×10 XLHO2×8) plus a supporting dismantle+heal pair. Spawn+boost energy for one kiter ≈7740; compound minerals 1500 (raw ≈ O1500 H1500 X1500 K960 Z420 L360 U120). Detail / phase checklist: living Page「通向三级风筝兵的发展规划」(ops canvas); combat autopsy `data/bustjetter_wipe/`.

**Order of work (does not replace peacetime energy policy):**
0. Energy pad — leanBank→20k → hold 15k floor → softCap clear ≥25k; **labs stay OFF** at ~15k storage
1. Upgrade pull — nUp→ceil6 / short≥70% → seal→1M under soft-gate
2. Push both RCL7 → RCL8 (CONTROLLER_LEVELS[7]=10.935M)
3. Industry prep — energy buffer toward ~100k (Overmind-style); labs 3→6→10; missing H/X/Z/L/U later decision (no market gate now)
4. T3 reactions → first one-off boost stock → sustained production
**Explicitly not now:** labs-on in live code, market, assault / war_cmd restart, new remote grab for minerals.

**12h review scorecard (mandatory from 2026-11-09 17:1x):** every 12h strategic review MUST score the living T3 north-star phases in Findings, not only the peacetime energy line. Minimum lines:
- **Phase0 energy pad:** bankLeft / softLeft / home stor vs 15k floor / labs OFF? (pass|fail|waiting)
- **Phase1 upgrade pull:** gated until Phase0 exit — nUp/ceil6 / short≥70% / seal soft-gate (blocked|ready|active)
- **Phase2 RCL8 prep:** both rooms RCL% + rem to 10.935M (observe only until Phase1)
- **Phase3+ industry:** deferred until ~100k-style buffer + RCL8 lab capacity — **no labs/market re-ask**
- One-line verdict: `waiting on ticks` | `small safe ship` | `phase exit` — capability to stock a kiter ≠ order to fight.


## Current state (2026-11-09 ~17:1x Asia/Hong_Kong · local metrics only)

| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** ~43.35% (4.740M/10.935M); stor **15309** ABOVE the 15k floor; labs OFF; LIVE **87d8c84** |
| W47N8 | **RCL7** ~20.97% (2.293M); stor **14579**; softCap2 **ON** softLeft≈10421 softBand1 leanBank1 phase=**bank20** bankLeft≈5421; upgKeep2 sealPark1; contMinPct~50 roadCrit residual under mvp pause (by design) |

PEACETIME; war_cmd pause `aborted_by_misaki`; remotes held SAFE this afternoon (W45N7 CLEARED since84163037 earlier window); raidLeft=0; listener single-slot 5:5:1:1; CPU~15–16/20 bucket10k. KEY~300k DONE.

**Phase0 status (T3 north-star):** still **waiting on ticks** — leanBank→20k not stuck on a code lever (noon-style peak-then-bleed continues; 14:29 tip bankLeft~5136 / softLeft~10136; 15:19 bankLeft 4166 / softLeft 9166 / roadCrit34; 17:15 live tip bankLeft≈5421 / softLeft≈10421). Home floor held ABOVE. Labs stay OFF. No softCap/labs/industry/market re-ask. No war_* restart.

Ideal vs actual: `tools/model.py` / Grafana / `upgFeed` / `w8day` (softCap2, softE/softArm/**softBand**, **upgKeep** 2|3|0, hMax, feedOk, sealPark, hubReady/**hubPrime**, leanBank/phase/bankLeft, contMinPct/roadCrit) / `w8soft` / `labReady`. **Peacetime priority = Phase0:** **leanBank→20k → softCap bank→clear ≥25k** (soft-band park + surplus trim nUp≤3 while stor<25k) → nUp→ceil6 only at true ≥25k / short≥70% → seal→1M under soft-gate → home floor ≥15k → labs KO (**no re-ask**). Long-term north-star after that pad: RCL8 + ~100k energy buffer + T3 kiter industry (see **North star** above) — still **no labs/market/war re-ask**. Living checklist: Page「通向三级风筝兵的发展规划」. Detail: `docs/RCL7.md`. Commander takeover, when wanted, is a separate key (`docs/COMMANDER.md`); it is off until `Memory.cmd` is armed and does not change this order.

## Phases

| Phase | Trigger | Goals | Exit |
|---|---|---|---|
| P0 Bootstrap | spawn placed | harvesters → miners path | RCL2 ✅ |
| P1 Economy | RCL2 | extensions, containers, static miners + haulers, core roads | RCL3 ✅ |
| P2 Defence | RCL3 | tower #1, ramparts spawn/tower, **alerts (no auto SM)**, 10 ext, layout v2 | tower live before novice ends ✅ early |
| P3 Storage + remote harden | RCL4 | storage, 20 ext, CLAIM2 reserver, rampart HP 50k, Invader defender ON (DEFENDER.md) | storage > 50k ✅ (economy); walls bank still pending |
| P4 Links | RCL5 | tower #2 first; link plan per `docs/RCL5.md` (recommended: hub + controller link at RCL5, source A at RCL6; stationary fillers from RCL7) — needs Misaki | CPU avg < 15 |
| P5 RCL6 | RCL6 | source A link + 10 ext first; v4 walls (bank 20k → step 1 100k before 10-28); terminal/extractor/labs **deferred** (`plan.RCL6_MINERALS`) | wall step 1 live; step 2 may finish after novice end |
| P6 Expand | RCL6+, GCL≥2 | **2nd room only with Misaki approval** | 2nd room RCL3 |
| P7 RCL7–8 | — | spawns 2–3, factory, 6 towers, power spawn, nuker, observer; min-cut if needed | RCL8 |

## Standing rules

- Never let refill/harvesters drop to 0 (emergency body from `energyAvailable`).
- ≤ 5 construction sites; planner every 50 ticks or on RCL change.
- Every upload passes `scripts/check.js` (+ `scripts/sim.js`).
- Remote: flee + pause on player combat; **NPC Invader defender ON** (W45N8); never attack players.
- Safe mode: **alert only** — Misaki decides.
- Patrol owns `state/next_iteration.json` cadence; strategy review updates docs/roadmap and small safe code fixes.
- Commander (phase 0, 2026-11-05): takeover lives in `Memory.cmd`, not in `Memory.ops.w47n9`. Release / TTL / `CMD.disarm()` restores the role. Do not auto-arm war, safe mode, claim, or market from that channel. Detail: `docs/COMMANDER.md`.
- Websocket rooms (2026-11-05): peacetime ops listener holds one slot, wall-clock W46N8:W47N8:W45N8:W45N7 = 5:5:1:1 (`tools/room_rot.py`). While the commander bot is live-commanding, ops drops room subscriptions (`touch metrics/listener_yield_rooms`); the commander subscribes the battle rooms and may use both official slots. Remove the file after handback. This is box ops, not `Memory.cmd`.
