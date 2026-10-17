# Strategy — W46N8 (home) + W45N8 (remote), 20 CPU, shard3

Sources: Screeps docs (control, defense, invaders, CPU), screepers wiki, Overmind / TooAngel / Hivemind patterns.
Last full refresh: **2026-10-17 strategy review** (neighbours: `docs/NEIGHBORS.md`); before that **2026-10-16 strategy review** (defence before novice end: `docs/DEFENSE_NOVICE.md`); prior: RCL6 readiness `docs/RCL6.md` (10-15), RCL5 `docs/RCL5.md` (10-14). Also `docs/DEFENSE.md`, `docs/DEFENSE_PLAN.md`, `docs/LAYOUT_V2.md`, `docs/REMOTE_W45N8.md`, `docs/MODEL.md`, `docs/DATA.md`.

## Principles

1. **Energy throughput is everything early.** Two home sources = 20 e/t max; reserved remote adds ~10 e/t raw. Static miners + containers + haulers (then links) beat generic workers.
2. **Upgrade hard; build only what unlocks the next step.** Layout v2 is live (compact hub + fast-filler stamps, fixed roles, cached paths).
3. **CPU (20/tick) is precious.** Prefer fixed routes and stations over per-tick `find`. Keep bucket ≥ 5000. Measured ~3.5–4.5 CPU at RCL3 with remote.
4. **Defence = towers + ramparts + Misaki-controlled safe mode.** Towers do most early work; ramparts protect spawn/tower/core. **NEVER auto-activate safe mode** — alert Misaki and wait for her decision (standing rule since 2026-10-12).
5. **Growth after RCL4:** remote mining (W45N8 approved and live), then links; a 2nd room only with explicit Misaki approval (GCL 2 already allows a claim).
6. **Major decisions need approval:** claim/expand, attack or provoke player neighbours, spend credits/pixels, activate safe mode, respawn.

## Current state (2026-10-16 ~14:35 UTC+8)

| | |
|---|---|
| Home | W46N8 RCL5 **~631k/1.215M** (~52%), cap 1800, storage ~2.0–2.4k, **2 towers** (~970e), critical ramparts ≥100k (filler stand-tiles decaying by design), safe mode **4 available** |
| Upgrade | ctl_ema ≈21–23/t (energy-bound; model ideal ~21.8–23.5); ~+270k progress in ~15.5 h DB window |
| RCL6 ETA | **~10-17 21:00 – 10-18 morning** — then bank 20k → outer walls (`docs/DEFENSE_NOVICE.md`) |
| Remote | W45N8 SAFE, CLAIM2, reservation ~1.9k, delivered **~506k**, container 100k hits; **remoteDefender ON** |
| Defence flags | `remoteDefender` ON; `guards` / `earlyWalls` **OFF** (upgrade-first; Misaki 10-16) |
| CPU | ~4.0–4.5 avg, bucket 10000, nerr 0 |
| Novice ends | **2026-10-28 03:33 UTC+8** (~11.5 days) |
| Neighbours (10-17) | W48N9 army swings 4–15 combat creeps (median 6), towers unfed, never staged in W47N8/W47N7; W48N8 = Evans_702 (no exit to W47N8). See `docs/NEIGHBORS.md`. Earlier: Council: BustJetter W47N9 RCL6 + W48N9 ~8 combat (watch, thinned); scouts through us 0 dmg. Fandalah W44N8 RCL6 no combat. RCL8 N/S still outside our exits |

Ideal vs actual: `tools/model.py` / Grafana. Remaining gap ≈ ctl-feed dead-bands (closing) and remote pauses; more upgrade needs more income (expansion — shelved).

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
