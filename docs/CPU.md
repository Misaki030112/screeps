# CPU budget: two rooms on 20 CPU (strategy review 2026-10-19 14:40 UTC+8)

Sources: Screeps docs (CPU limit, "every action that changes game state costs an extra 0.2 CPU", bucket/pixels),
live `Memory.stats.prof` (per-section EMA, `src/utils/errors.js` + `src/managers/stats.js`), `creep_cpu` / `room_stats`
in TimescaleDB, `Memory.stats.sw` spawn counters. `Game.cpu.limit` = **20**, `tickLimit` 500, bucket ~10000.

## Where the CPU goes (live @ tick 83739452, before fbe8a00)

| Section | ms/tick | Note |
|---|---|---|
| creeps (34 alive) | 9.09 | 76% of total; ≈0.27 per creep |
| home spawn (`spawn`) | 0.91 | run1 ≈2.4 ms per call; spawn busy 63% / idle 36% / wait 1% of ticks |
| W47N8 spawn (`w8spawn`) | 0.49 | |
| Memory parse (`mem`) + pre-loop | 0.41 | |
| remote + alerts | 0.37 | |
| trace (telemetry) | 0.12 | |
| layout/tower/links/roads/stats/report (both rooms) | 0.30 | |
| **total** | **11.96** | hourly avg 11.7–14.2, max spikes 47–49 (bucket absorbs) |

24 h trend: 6.5–8.8 avg before the W47N8 claim (10-18 noon) → 11.2–14.2 since (10-18 16:00). The second room costs
≈ +5.5 CPU. Bucket never fell below 9972.

Creep CPU by role (3 h): rhauler 1.22, w8rhauler 1.17, w8builder 0.92, w8hauler 0.78, queen 0.69, miner 0.55,
upgrader 0.53, others ≤0.46. Haulers (all kinds) ≈ 3.3 ms = 35% of creep CPU.

## What limits it
- Each creep that moves or works every tick pays the 0.2 intent cost; our 0.27/creep is close to that floor. Logic
  tuning (path caches, sticky targets) has little left to give per creep. The real lever is **fewer creeps for the
  same energy**: bigger bodies, links instead of haulers, one big upgrader instead of several small ones.
- Home rhaulers: one 36-part and four 16-part bodies at cap 2300. Fewer, larger W45N7 haulers would carry the same
  energy with fewer move intents (patrol to evaluate: W45N7 hauler trial kept 4 on 10-18).
- W47N8 at cap 1300: 4 builders (15–18 parts), 3 haulers, 4 rhaulers. Its creep count falls naturally at RCL5 (links,
  bigger bodies) and when the build queue empties.

## Headroom and what it means for strategy
- 20 − 12.5 ≈ 7.5 CPU spare on average. A third claimed room (GCL 3 allows it) costs ≈ 5–6 CPU at today's efficiency,
  so it would run at ~18–20 with no margin for defence spikes. **A 3rd room needs CPU work first** (target ≤ 10 for
  the two rooms). CPU, not GCL, is the binding limit.
- Spare CPU above the average is lost while the bucket is full (it is full almost all the time). `Game.cpu.generatePixel()`
  could turn 10000 bucket into 1 pixel (refill ≈ 10000 / 7.5 ≈ 1300 ticks ≈ 1.5 h). It empties the bucket, and the
  bucket is our reserve for combat spikes (max 49 ms seen). Not enabled; a decision for Misaki (see ROADMAP).

## Shipped
- **fbe8a00** home spawn: after a pass that finds nothing to spawn, re-check every 4 ticks (hostiles in the room force
  a full pass). Expected ≈ −0.6 ms/tick. Check: `Memory.stats.prof.spawn` EMA (was 0.91) and `Memory.stats.sw.W46N8.skip`
  rising; no change in replacement timing beyond 3 ticks.

## Next CPU levers (ranked by expected saving / risk)
1. Same idle throttle for `w8spawn` (0.49) once the W47N8 spawn code stops changing daily.
2. Remote hauler bodies sized to cap (fewer W45N7 rhaulers).
3. W47N8 RCL5: links at sources/controller replace haulers.
4. `mem` 0.34: keep trimming Memory (alerts/stats already moved to heap on 10-19).

Observability gap: `Memory.stats.prof` is only readable live (q.py). Logging it into `room_stats` (or a small
`cpu_prof` table) every 10 ticks would give per-section CPU history in Grafana. Next review item.
