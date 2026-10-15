# Strategy — W46N8 (home) + W45N8 (remote), 20 CPU, shard3

Sources: Screeps docs (control, defense, invaders, CPU), screepers wiki, Overmind / TooAngel / Hivemind patterns.
Last full refresh: **2026-10-14 strategy review** (RCL5 readiness: `docs/RCL5.md`); 2026-10-15 review: RCL6 readiness `docs/RCL6.md` (see also `docs/DEFENSE.md`, `docs/LAYOUT_V2.md`, `docs/REMOTE_W45N8.md`, `docs/MODEL.md`, `docs/DATA.md`).

## Principles

1. **Energy throughput is everything early.** Two home sources = 20 e/t max; reserved remote adds ~10 e/t raw. Static miners + containers + haulers (then links) beat generic workers.
2. **Upgrade hard; build only what unlocks the next step.** Layout v2 is live (compact hub + fast-filler stamps, fixed roles, cached paths).
3. **CPU (20/tick) is precious.** Prefer fixed routes and stations over per-tick `find`. Keep bucket ≥ 5000. Measured ~3.5–4.5 CPU at RCL3 with remote.
4. **Defence = towers + ramparts + Misaki-controlled safe mode.** Towers do most early work; ramparts protect spawn/tower/core. **NEVER auto-activate safe mode** — alert Misaki and wait for her decision (standing rule since 2026-10-12).
5. **Growth after RCL4:** remote mining (W45N8 approved and live), then links; a 2nd room only with explicit Misaki approval (GCL 2 already allows a claim).
6. **Major decisions need approval:** claim/expand, attack or provoke player neighbours, spend credits/pixels, activate safe mode, respawn.

## Current state (2026-10-14 ~14:45 UTC+8)

| | |
|---|---|
| Home | W46N8 RCL4 288.6k/405k, cap 1300, storage ~2.2k, 1 tower (1000), 16 ramparts 50–57k (target 50k ✓), safe mode **3 available** |
| Upgrade | ~20/t (last 2h), 24/t when ctl container fed; 24h avg 14.3/t (incl. RCL4 build phase); model ideal 23.5 (energy-bound) |
| RCL5 ETA | **tonight ~21:00–22:00** — transition plan `docs/RCL5.md` |
| Remote | W45N8 SAFE, reserved (CLAIM2, ~4350 ticks), delivered 175k total (~7.5 e/t over 24h); 4 Invader episodes in 48h |
| CPU | ~4.1 avg (max 19.6 spike), bucket 10000 |
| Novice ends | **2026-10-28 03:33 UTC+8** |
| Neighbours | The Council: BustJetter (W47N9 RCL6, reserves W47N8; scouts our room constantly, 0 dmg), Fandalah (W44N8 **RCL6**, up from 5). RCL8 drtk712 W46N9 / FungousCoast245 W46N7 outside our novice zone; home has no N/S exits |

Ideal vs actual: `tools/model.py` / Grafana. Remaining gap ≈ ctl-feed dead-bands (closing) and remote pauses; more upgrade needs more income (expansion — shelved).

## Phases

| Phase | Trigger | Goals | Exit |
|---|---|---|---|
| P0 Bootstrap | spawn placed | harvesters → miners path | RCL2 ✅ |
| P1 Economy | RCL2 | extensions, containers, static miners + haulers, core roads | RCL3 ✅ |
| P2 Defence | RCL3 | tower #1, ramparts spawn/tower, **alerts (no auto SM)**, 10 ext, layout v2 | tower live before novice ends ✅ early |
| P3 Storage + remote harden | RCL4 | storage, 20 ext, CLAIM2 reserver, rampart HP 50k, optional Invader defender (see DEFENSE.md) | storage > 50k |
| P4 Links | RCL5 | tower #2 first; link plan per `docs/RCL5.md` (recommended: hub + controller link at RCL5, source A at RCL6; stationary fillers from RCL7) — needs Misaki | CPU avg < 15 |
| P5 RCL6 | RCL6 | source A link + 10 ext first; v4 walls (bank storage to 20k first); terminal/extractor/labs **deferred** (`plan.RCL6_MINERALS`, Misaki decides minerals/market) | walls step 2 |
| P6 Expand | RCL6+, GCL≥2 | **2nd room only with Misaki approval** | 2nd room RCL3 |
| P7 RCL7–8 | — | spawns 2–3, factory, 6 towers, power spawn, nuker, observer; min-cut if needed | RCL8 |

## Standing rules

- Never let refill/harvesters drop to 0 (emergency body from `energyAvailable`).
- ≤ 5 construction sites; planner every 50 ticks or on RCL change.
- Every upload passes `scripts/check.js` (+ `scripts/sim.js`).
- Remote: flee + pause on hostile combat (Invader or player); never attack players; NPC defender only if approved.
- Safe mode: **alert only** — Misaki decides.
- Patrol owns `state/next_iteration.json` cadence; strategy review updates docs/roadmap and small safe code fixes.
