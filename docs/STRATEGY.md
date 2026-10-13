# Strategy — W46N8 (home) + W45N8 (remote), 20 CPU, shard3

Sources: Screeps docs (control, defense, invaders, CPU), screepers wiki, Overmind / TooAngel / Hivemind patterns.
Last full refresh: **2026-10-13 strategy review** (see also `docs/DEFENSE.md`, `docs/LAYOUT_V2.md`, `docs/REMOTE_W45N8.md`, `docs/MODEL.md`, `docs/DATA.md`).

## Principles

1. **Energy throughput is everything early.** Two home sources = 20 e/t max; reserved remote adds ~10 e/t raw. Static miners + containers + haulers (then links) beat generic workers.
2. **Upgrade hard; build only what unlocks the next step.** Layout v2 is live (compact hub + fast-filler stamps, fixed roles, cached paths).
3. **CPU (20/tick) is precious.** Prefer fixed routes and stations over per-tick `find`. Keep bucket ≥ 5000. Measured ~3.5–4.5 CPU at RCL3 with remote.
4. **Defence = towers + ramparts + Misaki-controlled safe mode.** Towers do most early work; ramparts protect spawn/tower/core. **NEVER auto-activate safe mode** — alert Misaki and wait for her decision (standing rule since 2026-10-12).
5. **Growth after RCL4:** remote mining (W45N8 approved and live), then links; a 2nd room only with explicit Misaki approval (GCL 2 already allows a claim).
6. **Major decisions need approval:** claim/expand, attack or provoke player neighbours, spend credits/pixels, activate safe mode, respawn.

## Current state (2026-10-13 ~14:40 UTC+8)

| | |
|---|---|
| Home | W46N8 RCL3 ~113k/135k, tower (36,29), ramparts ~27k, cap 800, layout v2 |
| RCL4 ETA | ~15:50–17:30 today at ~16–19 e/t upgrade (home); model ideal with remote ~23.6/t |
| Remote | W45N8 reserved mining live; **paused** for NPC Invader until ~83614741; delivered 27.3k; reservation likely lapsed |
| CPU | ~3.5–4.2 avg, bucket 10000 |
| Novice ends | **2026-10-28 03:33 UTC+8** |
| Safe mode | Spawn SM ending soon; **2 available** — Misaki only |
| Neighbours | The Council (BustJetter RCL6 / Fandalah RCL5) flanking west & east remote; RCL8s outside novice |

Ideal vs actual: see `tools/model.py` / Grafana. Gap today ≈ paused remote + WORK-bound upgraders during builds/pause.

## Phases

| Phase | Trigger | Goals | Exit |
|---|---|---|---|
| P0 Bootstrap | spawn placed | harvesters → miners path | RCL2 ✅ |
| P1 Economy | RCL2 | extensions, containers, static miners + haulers, core roads | RCL3 ✅ |
| P2 Defence | RCL3 | tower #1, ramparts spawn/tower, **alerts (no auto SM)**, 10 ext, layout v2 | tower live before novice ends ✅ early |
| P3 Storage + remote harden | RCL4 | storage, 20 ext, CLAIM2 reserver, rampart HP 50k, optional Invader defender (see DEFENSE.md) | storage > 50k |
| P4 Links | RCL5 | filler A + hub links, stationary fillers + manager, tower #2 | CPU avg < 15 |
| P5 Minerals | RCL6 | terminal, extractor, labs, source A link | terminal active |
| P6 Expand | RCL6+, GCL≥2 | **2nd room only with Misaki approval** | 2nd room RCL3 |
| P7 RCL7–8 | — | spawns 2–3, factory, 6 towers, power spawn, nuker, observer; min-cut if needed | RCL8 |

## Standing rules

- Never let refill/harvesters drop to 0 (emergency body from `energyAvailable`).
- ≤ 5 construction sites; planner every 50 ticks or on RCL change.
- Every upload passes `scripts/check.js` (+ `scripts/sim.js`).
- Remote: flee + pause on hostile combat (Invader or player); never attack players; NPC defender only if approved.
- Safe mode: **alert only** — Misaki decides.
- Patrol owns `state/next_iteration.json` cadence; strategy review updates docs/roadmap and small safe code fixes.
