# Strategy — W46N8 (home) + W45N8 (remote), 20 CPU, shard3

Sources: Screeps docs (control, defense, invaders, CPU), screepers wiki, Overmind / TooAngel / Hivemind patterns.
Last full refresh: **2026-11-04 05:4x** (leanBank rebuild-band upgKeep ≤2); before that **2026-11-04 02:4x** (hub ferry prime arm LEAN_ARM / thrash-band hubPrime); before that **2026-11-03 23:4x** (hub-link PRE-WARM during softCap bank / hubPrime); before that **2026-11-03 HUB_LINK nod YES** (`config.HUB_LINK=true`; hubReady waits on structure 33,34; labs/industry/market still OFF; sealMinE 25k; 20:4x soft-band kept); before that **2026-11-03 20:4x** (W47 soft-band ≠ softE / softCap re-ON drain); before that **2026-11-03 17:3x** (W47 post-roadCrit feedBound / !HUB_LINK ceiling); before that **2026-11-03 14:4x** (W47 roadCrit before deep seal / Overmind critical=25%); before that **2026-11-03 11:3x** (W47 container-first repair / Overmind <50% battery); before that **2026-11-03 08:4x** (softCap2 leanBank-style hysteresis LEAN_SOFT_ARM=22k); before that **2026-11-03 05:4x** (HUB_LINK flip day-of upgCeil→hubLinkLive); before that **2026-11-03 02:4x** (seal soft-gate vs softCap2 / no sealMinE raise); before that **2026-11-02 23:4x** (W47 HUB_LINK plumbing readiness / no flip); before that **2026-11-02 20:4x** (softCap thrash / sealMinE briefly 35k then Misaki→25k); before that **2026-11-02 17:4x** (post-war fortify vs softCap / sealMinE→LEAN_SOFT); before that **2026-11-02 14:5x** (W47N9 wartime economy freeze / GO); before that **2026-11-02 14:4x** (W47 peacetime ctl-battery surplus gate); before that **2026-11-02 11:4x** (W47 threat-soft holds w8upgrader ≤2 past `LEAN_SOFT`); before that **2026-11-02 08:4x strategy review** (W47 soft-band park deadlock / WORK-bound ~55%); before that **2026-11-02 05:4x** (home energy-bound / short-soft); before that **2026-11-02 02:4x** (W47 HMAX 2→3); before that **2026-11-01 23:4x** (thin-K + KO activate seq); before that **2026-11-01 20:4x** (post-minBuild leanBank re-arm); before that **2026-11-01 17:4x** (w8mminer vs soft-cap spawn prio); before that **2026-11-01 14:4x** (home KO labReady propose); before that **2026-11-01 11:4x** (first-K send pacing); before that **2026-11-01 11:1x** (RCL6_MINERALS flip); before that **2026-11-01 08:4x** (hold-band sink → stor20k); before that **2026-11-01 05:4x** (soft-cap survives RCL6_MINERALS flip); before that **2026-11-01 02:4x** (leanBank hysteresis 15k + soft-cap 25k); before that **2026-10-31 23:4x** (RCL6_MINERALS flipReady + post-flip leanBank hold); before that **2026-10-31 20:4x** (leanBank arm on day-crit, not 50ext); before that **2026-10-31 17:4x** (day-of north tower ≥600 / close hubNeedy residual); before that **2026-10-31 14:4x** (dormant terminal.send K→W46N8); before that **2026-10-31 11:4x** (dormant w8mminer + haul→terminal); before that **2026-10-31 08:4x** (leanBank → stor≥20k); before that **2026-10-31 05:4x** (day-of energy crash / `w8day.towerMinE`); before that **2026-10-31 02:4x** (home upgrade vs ideal 26 / `upgFeed`); before that **2026-10-30 23:4x** (W47N8 lean KO scaffold / `RCL6_LABS` split / w8min); before that **2026-10-30 20:4x** (RCL7 day-of no pre-bank / w8day); before that **2026-10-30 17:4x** (soft-ramp SOFT_MIN+localOn); before that **2026-10-30 14:4x strategy review** (W47N8 soft-ramp staging 100k); before that **2026-10-30 11:4x** (post-300k fundSpend exit / energy reallocation); before that **2026-10-30 08:4x** (RCL7 peacetime hold at 300k / no auto 1M); before that **2026-10-30 05:4x** (W45N7 Invader-res reclaim via attackController); before that **2026-10-30 02:4x** (STATIONARY_FILL readiness — keep queens); before that **2026-10-29 23:4x** (lab ramparts); before that **2026-10-29 20:4x** (W47N8 RCL7 day-of gate + spur roads); before that **2026-10-29 17:4x** (fortify fundSpend); before that **2026-10-29 14:4x** (mineral/boost §4); before that **2026-10-20 00:0x** (remote posture after novice end: `docs/DEFENSE_NOVICE.md`); before that **2026-10-19** (CPU `docs/CPU.md`, market `docs/MARKET.md`); before that **2026-10-18 strategy review** (W47N8 hold / safe-mode mechanics: `docs/W47N8_HOLD.md`); before that **2026-10-17 strategy review** (neighbours: `docs/NEIGHBORS.md`); before that **2026-10-16 strategy review** (defence before novice end: `docs/DEFENSE_NOVICE.md`); prior: RCL6 readiness `docs/RCL6.md` (10-15), RCL5 `docs/RCL5.md` (10-14). Also `docs/DEFENSE.md`, `docs/DEFENSE_PLAN.md`, `docs/LAYOUT_V2.md`, `docs/REMOTE_W45N8.md`, `docs/MODEL.md`, `docs/DATA.md`.

## Principles

1. **Energy throughput is everything early.** Two home sources = 20 e/t max; reserved remote adds ~10 e/t raw. Static miners + containers + haulers (then links) beat generic workers.
2. **Upgrade hard; build only what unlocks the next step.** Layout v2 is live (compact hub + fast-filler stamps, fixed roles, cached paths).
3. **CPU (20/tick) is precious.** Prefer fixed routes and stations over per-tick `find`. Keep bucket ≥ 5000. Measured ~3.5–4.5 CPU at RCL3 with remote.
4. **Defence = towers + ramparts + Misaki-controlled safe mode.** Towers do most early work; ramparts protect spawn/tower/core. **NEVER auto-activate safe mode** — alert Misaki and wait for her decision (standing rule since 2026-10-12).
5. **Growth after RCL4:** remote mining (W45N8 approved and live), then links; a 2nd room only with explicit Misaki approval (GCL 2 already allows a claim).
6. **Major decisions need approval:** claim/expand, attack or provoke player neighbours, spend credits/pixels, activate safe mode, respawn.

## Current state (2026-11-04 ~05:45 Asia/Hong_Kong)

| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** ~23.74%; last3h~19.2 e/t; soft CLEARED; stor~16k ABOVE; labs OFF |
| W47N8 | **RCL7** ~9.85%; **leanBank=1** bankLeft~2.8k + softCap2 ON softLeft~7.8k; **hubReady1 hubPrime1** upgCeil6; sealPark1 roadCrit0; **upgKeep banded** (05:4x: <15k→1, [15k,20k)→2); labs/industry OFF |

Peacetime; remotes SAFE (W45N7 InvaderCore killed ~84054839); roads.phase=done; ~35 creeps CPU~12–15 bucket10k. Deploy **c5334c8** → next leanUpKeep commit.

Ideal vs actual: `tools/model.py` / Grafana / `upgFeed` / `w8day` (softCap2, softE/softArm/**softBand**, **upgKeep**, feedOk, feedBound/upgCeil, sealPark, hubReady/**hubPrime**, contMinPct/contLow/roadCrit) / `w8soft` / `labReady`. **Peacetime priority:** leanBank rebuild [15k,20k) with **upgKeep=2** → softCap clear ≥25k / nUp→ceil6 short≥70% → seal→1M under soft-gate (roadCrit held 0) → home floor ≥15k → labs KO (**no re-ask**). Detail: `docs/RCL7.md` 05:4x leanUpKeep + 02:4x LEAN_ARM prime + HUB_LINK nod.
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
