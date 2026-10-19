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

## 2026-10-20 01:4x refresh: growth budget, siege budget, low-bucket mode (strategy review, tick 83748924)

**Now (Memory.stats.prof EMA, t83748924):** total **10.5** (was 11.96 at t83739452), creep 8.63 over 34 creeps =
**0.254 per creep** (intent floor ~0.2), home spawn 0.15 (was 0.91: fbe8a00 idle throttle verified), w8spawn 0.05-0.11
(was 0.49), remote 0.34, mem 0.37, trace 0.13, everything else ≤ 0.11. `room_stats.cpu` (sampled on STATS ticks, which do
extra room detail work) 2-hour averages 12.0-13.9 over the last 26 h; bucket min 9958. Max spikes 44-63 only at deploy
global resets.

**Real fight cost (10-19, W47N8, 1-6 hostiles, joint defence):** 15-min avg 11.4-15.8, max 19.6, bucket min 9958.
wdefender per-creep CPU is about a third of a hauler's (0.46 vs 1.2-1.7 per sample window). A fight of that size never
touched the bucket.

**Growth (next ~7 days):**
- W47N8 RCL5 (~10-20 06:10-07:00): links 13,25 + 26,12 and the 1800 cap allow fewer, bigger haulers/upgraders. Expect
  -2..-3 creeps (≈ -0.5..-0.75 CPU) once the RCL5 builds finish; +1 builder (~0.25) during them. Net ≈ flat.
- Home RCL7 (~10-26): cap 5600 lets W45N7's 6x16-part rhaulers become ~3x32 (≈ -0.75 CPU). Tower 3 / spawn 3 ≈ +0.1.
- GCL 3 → 4: 2.34M / 8.69M, ~56 e/t total upgrade → ~5.5 days (~10-25). GCL 3 already allows a 3rd room.
- **3rd room:** ≈ +5.5 CPU at today's efficiency → ~16 avg (EMA) / ~18.5 on STATS ticks. It fits on average, but leaves
  only ~1.5-4 CPU for fights. Still: a 3rd room should wait for the RCL5/RCL7 creep consolidation above (≈ -1.5 CPU), and
  it is Misaki's decision. CPU limit is fixed at 20 without a subscription unlock (credits/money: Misaki's decision).

**Siege budget (after novice end 10-28):** bucket 10000, limit 20, ~4.18 s/tick. Sustained 25 CPU drains it in ~2000
ticks (~2.3 h); sustained 30 in ~1000 ticks (~70 min). After that `tickLimit` ≈ 20 and the script is cut off mid-loop.
Creeps used to run in `Game.creeps` order, so defenders could be the ones left unrun.

**Shipped (this review): `src/utils/cpuorder.js` low-bucket mode, dormant while bucket ≥ 2000.** Below 2000: combat creeps
(guard, defender, w8defender, w8healer, cq*) run first, then queen / w8filler (spawn and tower refill), then economy. When
used CPU gets within 5 of `tickLimit`, the remaining economy creeps skip the tick, so stats/report still run and the tick is
never hard-terminated. Spawns and towers already run before creeps. Test: `tests/cpu_order.js`.

**Observability shipped:** the listener now writes `Memory.stats.prof` into a `cpu_prof` table every ~5 min
(ts, tick, section, ms EMA, bucket, commit). Per-section CPU history: `SELECT time_bucket('1 hour',ts), section, avg(ms)
FROM cpu_prof GROUP BY 1,2`. The gap noted above is closed.

**Levers, re-ranked:** (1) RCL5/RCL7 body consolidation (no code beyond normal sizing); (2) W45N7 rhaulers to cap at RCL7;
(3) `mem` 0.37 trim; (4) w8spawn throttle dropped from the list (already ~0.1).
