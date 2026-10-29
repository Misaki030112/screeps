# Strategy — W46N8 (home) + W45N8 (remote), 20 CPU, shard3

Sources: Screeps docs (control, defense, invaders, CPU), screepers wiki, Overmind / TooAngel / Hivemind patterns.
Last full refresh: **2026-10-30 05:4x strategy review** (W45N7 Invader-res reclaim via attackController); before that **2026-10-30 02:4x** (STATIONARY_FILL readiness — keep queens); before that **2026-10-29 23:4x** (lab ramparts); before that **2026-10-29 20:4x** (W47N8 RCL7 day-of gate + spur roads); before that **2026-10-29 17:4x** (fortify fundSpend); before that **2026-10-29 14:4x** (mineral/boost §4); before that **2026-10-20 00:0x** (remote posture after novice end: `docs/DEFENSE_NOVICE.md`); before that **2026-10-19** (CPU `docs/CPU.md`, market `docs/MARKET.md`); before that **2026-10-18 strategy review** (W47N8 hold / safe-mode mechanics: `docs/W47N8_HOLD.md`); before that **2026-10-17 strategy review** (neighbours: `docs/NEIGHBORS.md`); before that **2026-10-16 strategy review** (defence before novice end: `docs/DEFENSE_NOVICE.md`); prior: RCL6 readiness `docs/RCL6.md` (10-15), RCL5 `docs/RCL5.md` (10-14). Also `docs/DEFENSE.md`, `docs/DEFENSE_PLAN.md`, `docs/LAYOUT_V2.md`, `docs/REMOTE_W45N8.md`, `docs/MODEL.md`, `docs/DATA.md`.

## Principles

1. **Energy throughput is everything early.** Two home sources = 20 e/t max; reserved remote adds ~10 e/t raw. Static miners + containers + haulers (then links) beat generic workers.
2. **Upgrade hard; build only what unlocks the next step.** Layout v2 is live (compact hub + fast-filler stamps, fixed roles, cached paths).
3. **CPU (20/tick) is precious.** Prefer fixed routes and stations over per-tick `find`. Keep bucket ≥ 5000. Measured ~3.5–4.5 CPU at RCL3 with remote.
4. **Defence = towers + ramparts + Misaki-controlled safe mode.** Towers do most early work; ramparts protect spawn/tower/core. **NEVER auto-activate safe mode** — alert Misaki and wait for her decision (standing rule since 2026-10-12).
5. **Growth after RCL4:** remote mining (W45N8 approved and live), then links; a 2nd room only with explicit Misaki approval (GCL 2 already allows a claim).
6. **Major decisions need approval:** claim/expand, attack or provoke player neighbours, spend credits/pixels, activate safe mode, respawn.

## Current state (2026-10-30 ~05:40 Asia/Hong_Kong)

| | |
|---|---|
| Home | W46N8 **RCL7** ~581k/10.9M (~6 e/t under fundSpend; 0 home upgraders); storage ~14–15k (FLOOR 5k tug vs reserveE 15k); walls min **~230k** → **300k** (fundSpend live, fund~37.7k; ETA **~6 h** → ~11:40 Asia/Hong_Kong); towers 3; spawns 3 (cap 5600); terminal+extractor+3 labs; **lab ramparts ~600k**; O ~17k in storage, labs dormant; **`STATIONARY_FILL=false`** dual queens; SM avail 6 |
| W47N8 | **RCL6** ~2.902M/3.645M (~743k left, **RCL7 ~2026-10-31 21:50** Asia/Hong_Kong at ~22 e/t ≈ **~40 h**); seal+GATE **300k**; soft ramps spawn@34,30 ~20k / towers ~50k (raise with peacetime); towers 2; tower3@22,7 + spawn2@33,30 wait RCL7; stor ~1.6–2.5k; links live (`w8model.links`); `HUB_LINK=false` **`RCL7_INDUSTRY=false`** |
| Assault | **ABORTED** 2026-10-29 (~15:31): defend-only W47N9, keep mining O (no mineralCap), civilian building both rooms |
| Remote | W45N8 SAFE (Misaki res); **W45N7 SAFE why=killed** but Invader res lingering — **05:4x attackController reclaim**; W47N7 Misaki res; core buster live (46f1804) |
| CPU | **~9–15 / 20**, bucket 10000 — `docs/CPU.md` |
| GCL | **4** (3rd room still CPU-bound; no claim without Misaki) |
| Novice | **ended 2026-10-28 03:33 Asia/Hong_Kong** |
| Fortify | Lab cover ✅ (~600k); walls→300k in progress (~6 h); colony soft ramps thin; colony RCL7 day-of next; minerals after storage; barriers 1M; STATIONARY_FILL deferred to RCL8 — `docs/RCL7.md` |

Ideal vs actual: `tools/model.py` / `tools/model_w8.py` / Grafana. Priority: **walls→300k** → **W45N7 reclaim** → colony RCL7 tower3+spawn2 (factory OFF) → minerals → barriers 1M → STATIONARY_FILL/hybrid at RCL8.

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
