# Colony CPU: full tick-logic + historical analysis

**When:** 2026-11-10 16:40 Asia/Hong_Kong (box-local).  
**Live:** commit `5892e31` (deployed 13:37 HKT, tick 84181330). Both rooms RCL7, GCL 4. Shard3 ~4.42 s/tick. Limit 20, tickLimit 500, bucket 10000.  
**No live code was changed, deployed, or committed.** The in-flight W47 softCap surplus-gate + spawn-throttle work is treated as already underway and is not re-proposed here.

This note verifies, dates, and extends the 16:23 HKT `_softcap_cpu_analysis.md` 6h/24h snapshot. It walks every tick path from `src/main.js` and uses the full TimescaleDB history (room_stats from 2026-10-12, cpu_prof from 2026-10-20, creep_cpu / role counts for the same span).

---

## Conclusions

**Where 17–18 / 20 actually goes.**  
Two different CPU numbers are in play, and both are real.

- `room_stats.cpu` (STATS console, every 10 ticks, W46N8 row only): today **17.12** avg, p50 16.83, **p95 20.59**, max 75.78 (the 13:37 deploy). Last 6h earlier today was 17.37 / p95 20.49. This is what patrols and Grafana treat as “are we near the cap.” It systematically samples the expensive 10-tick beat (segment-90 stringify, room detail finds, `STATS` console.log). Live at 16:39 HKT, tick 84183810: STATS cpu **18.91**, `trace_cpu` **0.977**, bucket 10000, 41 creeps, Memory 26 349 bytes. A few minutes earlier, three STATS samples were 18.58 / **20.62** / 19.74.
- `cpu_prof` EMA (`Memory.stats.prof`, all ticks, 1/50): today **14.94** (10 polls, last 15:38 HKT). The all-tick mean is about **2.2 CPU lower** than room_stats. That gap has been stable since Oct 20 (1.7–2.4 every day we have both). It is mostly sampling bias, not 2 CPU of unmetered mystery work. On a STATS tick, `trace` alone is ~0.98 vs its EMA 0.16.

The budget that matters for the 20 cap is **per-tick used**, and p95 of the already-heavier STATS ticks is already on the limit. Bucket min today 9884; last-hour min 10000. Headroom is average-ok and high-percentile-gone.

**Section split (cpu_prof today vs Oct 20 daily baseline).**

| Section | Oct 20 daily | Today (10 polls) | Δ | What happened |
|---|---:|---:|---:|---|
| total (EMA) | 11.42 | **14.94** | **+3.52** | see below |
| creep | 8.96 | **10.38** | **+1.42** | more creeps, slightly fatter hauler/filler set |
| **spawn** (both home spawns) | **0.18** | **1.00** | **+0.82** | idle throttle disarmed by energy-wait |
| **w8spawn** (both W47 spawns) | **0.31** | **0.97** | **+0.66** | 2nd spawn, no throttle, heavier cascade |
| remote | 0.33 | 0.42 | +0.09 | modest; threat FSM + 3 guard-able remotes |
| w8tower | 0.15 | 0.29 | +0.14 | 3rd tower after W47 RCL7 |
| labs | 0.03 | 0.10 | +0.07 | `readyObs` every tick after labs exist; **labs still off** |
| w8layout | 0.04 | 0.10 | +0.06 | more RCL7 layout work, already every 20 ticks |
| mem | 0.39 | 0.31 | −0.08 | improved |
| alerts / links / roads / report / ledger / cmd / raidFlags / layout / tower / stats / trace | — | ≤0.16 each | small | no material drift |

Spawn + w8spawn = **+1.48**, creep = **+1.42**, the other drifted sections ≈ **+0.3**, mem improved. That accounts for the +3.5 EMA rise. The earlier “+1.5 is spawn alone” claim is confirmed; it is **not** the whole rise since October.

**How much the in-flight spawn throttle should recover.**  
The 16:23 estimate of **−0.9 to −1.3 CPU** (W47 once-per-room + idle/wait throttle ≈ 0.5–0.7 of 0.97; home wait-throttle ≈ 0.4–0.6 of 1.00) still holds. Hostiles and commander `consumeSpawn` must still force a full pass. After it lands, expect:

- EMA total in the **13.6–14.0** band if nothing else moves
- room_stats avg around **15.8–16.2**
- p95 still **~19–20**, because the STATS-tick observability spike (~+2 vs EMA) is untouched

That is a real recovery of the Oct 31–Nov 1 regression. It does **not** recreate the Oct 20 11.4 / 13.4 world, because creep CPU also grew by 1.4 and has no in-flight fix.

**What remains after that.**  
A comfortable margin for a new remote (+2–3) or a 3rd room (+5–6) is still **not** there. After the throttle, p95 stays near 20 and average room_stats stays mid-16. The next real lever is **creep count**, not another manager micro-cut:

- Haulers still dominate. Today’s model (16:21 HKT): W47 local CARRY **40 vs need 9**, remote CARRY **75 vs need 48.6**. Home rhauler live avg **6.78** vs a design 6 (5× W45N7 + 1× W45N8) — the extra is mostly prespawn overlap, not a 8-wide fleet (the 16:38 snapshot of 8 rhaulers was a handoff spike; 16:39 was back to 6).
- W47 src_A is still soft (**2.47 vs ideal 9.60** e/t). The 3rd/4th `w8hauler` is the overflow valve under keep-2. **Do not cut W47 haulers until the in-flight softCap policy is measured.**
- The Oct 20 W45N7 body trial (5× small → 2× cap-sized, same CARRY, ≈ **−0.7**) is still the best *additional* cut and is still unshipped.
- Leftover defenders this afternoon (`defender` 2, `w8defender` 1, `w8guard` 1 at 16:39, all idle=1.0 in the model) are a short-lived ~0.5–0.8 CPU after Invaders. W45N7 has been in DEFEND since 15:05 HKT with no `cleared` row yet; `remotePatrol` keeps them until TTL. **Do not recycle them for CPU.**
- Everything else that is still loose (`labs.readyObs` every tick, tower repair with no `hits < hitsMax` check, STATS/trace 10-tick spike) is **0.05–0.2 each**, worth doing after the throttle, not a substitute for it.

---

## Historical reconstruction

Sources: `room_stats` W46N8 only (colony cpu is duplicated on W47 rows), `cpu_prof` EMA, `room_stats.creeps` with missing roles counted as 0, `deploys`, `docs/CPU.md` Oct 20 baseline. Official history does **not** fill room_stats / cpu_prof / creep_cpu during box sleep.

### Daily colony CPU and census

| Day (HKT) | room_stats avg / p95 | cpu_prof total | creeps avg | Notes |
|---|---:|---:|---:|---|
| 10-12 | 2.67 / 4.24 | — | 9.9 | RCL2, single room |
| 10-13 | 3.73 / 4.79 | — | 13.9 | RCL3; **DB wipe after 10:19** (box image reset, docs/DATA.md) |
| 10-15 evening | 3.86 / 4.52 | — | 10.3 | restore; 10-13 10:19 → 10-15 23:33 is gone |
| 10-16 | 5.00 / 7.33 | — | 13.2 | W45N7 remote starts afternoon |
| 10-17 | 6.31 / 7.63 | — | 17.9 | home RCL6 |
| 10-18 | 9.36 / 14.36 | — | 24.2 | **W47N8 claimed ~15:24**; 18:00 6h slot already 12.74 / 35 creeps |
| 10-19 | 12.97 / 15.57 | — | 35.2 | two-room steady state |
| **10-20** | **13.36 / 16.41** | **11.42** | **37.0** | docs/CPU.md snapshot was **34 live / EMA 10.5** — that was a quiet moment, not the daily mean |
| 10-21 | 13.06 / 15.71 | 11.18 | 35.1 | |
| 10-22 (to 10:45) | 12.66 / 14.90 | 10.87 | 34.6 | then **7-day hole** (no room_stats / cpu_prof until 10-29 09:22) |
| 10-29 | 13.98 / 17.30 | 12.27 | 36.6 | **home RCL7 first visible 09:22** (cap 5600, 2nd spawn). May have flipped during the hole |
| 10-30 | 13.34 / 16.22 | 11.49 | 33.1 | spawn 0.34, w8spawn 0.38 — throttle still working |
| 10-31 | 13.39 / 16.21 | 11.57 | 35.0 | **W47 RCL7 at 17:13:38**, tick 83981380 (2nd spawn + tower 3 unlocked) |
| **11-01** | **14.68 / 17.57** | **12.83** | 36.2 | **spawn + w8spawn jump lands** (see below) |
| 11-02 | 15.72 / 18.89 | 13.68 | 37.9 | w8tower 0.28, labs 0.09, raid9 wartime bump |
| 11-03–04 | 15.73–15.81 / 18.5–19.0 | 13.6–13.8 | 36.9–37.4 | softCap hysteresis / HMAX valve; peacetime |
| 11-05 | 16.43 / **20.64** | 14.12 | 38.9 | p95 first sits on the 20 cap; 2nd maint builder, commander overlay |
| 11-06–09 | 16.32–16.88 / 19.7–20.0 | 14.3–14.9 (sparse) | 37.5–38.5 | box-sleep era: far fewer samples, averages still in the mid-16s |
| **11-10 (to 16:39)** | **17.12 / 20.59** | **14.94** | **39.6** | live 41; afternoon surplus-upgrader wave + leftover defenders |

The climb is **stepwise over three weeks**, not a one-afternoon event:

1. **Oct 18 15:24 — second room.** +5–6 CPU. Permanent.
2. **Oct 29 — home RCL7 / 2nd spawn.** room_stats +0.6–1, home `spawn` 0.22 → 0.39. Throttle still mostly armed.
3. **Oct 31 17:13 — W47 RCL7 / 2nd spawn.** `w8spawn` 0.30 (12:00 slot) → **0.66** (18:00) → **0.91** (Nov 1 00:00). No `IDLE_EVERY` on `W8.spawnRun`; two full find-cascades per tick.
4. **Nov 1 morning — home wait-throttle lost.** `spawn` 0.41 (00:00) → **0.70** (06:00) → **0.88** (12:00). Aligns with 02:46 `3f1e0c8` leanBank/soft-cap, 05:52, 07:38 soft-upgrade bank: the 15k floor + replacement stream keeps `run1` in “want but wait for energy,” and `sw.ne` is only armed when `!waited`. Two RCL7 home spawns then re-run the ~2.4 ms path every tick. `w8filler` also steps 1.1 → 2.2 (second refill body, kept since).
5. **Nov 2–5 — slower creep-side drift.** w8hauler 2.1 → 3.9 (HMAX overflow valve under softCap), w8rhauler 4.4 → 5.0, w8tower / labs / w8layout step up, p95 reaches 20. After that the mid-16 / p95-20 regime is the new normal, and today is the high end of that band, not a new kind of problem.

### Spawn regression is dated, not just hypothesized

| 6h slot (HKT) | spawn | w8spawn | What changed |
|---|---:|---:|---|
| 10-31 12:00 | 0.31 | 0.30 | pre-RCL7 W47 |
| 10-31 18:00 | 0.41 | **0.66** | W47 RCL7 at 17:13 |
| 11-01 00:00 | 0.41 | **0.91** | 2nd W47 spawn, unthrottled cascade |
| 11-01 06:00 | **0.70** | 0.93 | home wait-throttle failing |
| 11-01 12:00 | **0.88** | 0.89 | stays here |
| 11-04 … 11-10 | 0.8–1.22 | 0.76–1.14 | no further regime change |

One 15:38 poll today shows `w8spawn` **0.273** (and `spawn` still 1.051, total EMA 14.05). That is a real dip, likely both W47 spawns busy (`spawnRun` returns after `mine()` + sites + `updateSealPark`). The daily mean is still ~0.97. Do not read a single poll as “w8spawn already fixed.”

### Creep census vs the “34 on Oct 20” line

The Oct 20 review’s **34** was a live snapshot (tick 83748924, EMA 10.5). The same day’s room_stats average was **37.0** (range 31–45). Oct 22 (last full pre-hole day) averaged **34.6**.

Today’s daily average is **39.6** (range 34–45), live **41** at 16:39. Versus the Oct 20 *daily* mean that is **+2.6 creeps**, not +7. Versus the oft-cited snapshot it is +7. At 0.25–0.28 per creep, +2.6 ≈ +0.7 CPU; the rest of the +1.42 creep-section rise is a fatter mix (2 fillers, 4 local W47 haulers, ~5 remote W47 haulers, leftover defence this afternoon).

Role averages with zeros (room_stats, selected):

| Role | Oct 20 | Oct 30 | Nov 1 | Nov 10 | per-creep ms (today) |
|---|---:|---:|---:|---:|---:|
| rhauler | 6.39 | 5.07 | 6.56 | **6.78** | 0.240 |
| w8rhauler | 4.00 | 4.10 | 4.38 | **5.23** | 0.277 |
| w8hauler | 3.13 | 2.09 | 2.09 | **3.97** | 0.284 |
| w8filler | 1.05 | 1.10 | **2.19** | 2.15 | 0.260 |
| queen | 2.09 | 2.12 | 2.11 | 2.11 | **0.410** (highest per creep) |
| w8upgrader | 2.81 | 3.14 | 1.51 | 2.24 | 0.238 |
| defender + w8defender + w8guard | 1.33 | 0.54 | 0.60 | 0.75 (16:00 hour: 2+1+1) | ~0.16–0.20 |

Hauler CPU if those daily counts are live: rhauler ~1.63 + wrhauler ~1.45 + whauler ~1.13 + home hauler ~0.22 ≈ **4.4**, still ~40% of creep CPU, same story as October, bigger fleet.

Queen rp100 is still high (~15 today). Last 6h `rp_why` for queen: **647 `c` (path-cache hit, cheap)**, 424 `n`, 102 `s`, 19 `x`. 720380f did its job; leftover queen repath is a minor lever (~0.1), not a first cut.

### Other sections that drifted (not just spawn)

- **w8tower 0.15 → 0.29:** W47 RCL7 unlocks a 3rd tower. Peace repair is an 0.2 intent per firing tower. Code still has the Oct 20 leftover: `tower.repair(rep)` with **no `hits < hitsMax` check**, target re-picked every 10 ticks.
- **labs 0.03 → 0.10 from Nov 2:** `labs.run` always calls `readyObs`, which does `FIND_MY_STRUCTURES` every tick on W46N8, even when `Memory.ops.labs` is unset. Reaction path returns immediately. Labs are off. This is a cheap, safe throttle.
- **w8layout 0.04 → 0.10:** already gated `Game.time % 20`. Leave.
- **remote 0.33 → 0.42:** `refreshReservations` + `threat.run` per CFG/GUARD remote every tick. Modest. Not a first cut.
- **mem improved** (0.39 → 0.31). Memory is 26 349 bytes live. Post-loop Memory *serialization* is billed by the engine and is **not** in `Game.cpu.getUsed()` / room_stats / cpu_prof. We cannot measure it. Parse at 0.31 suggests the tail is modest; do not invent a number.

---

## Tick map

Order is `src/main.js`. Costs are cpu_prof EMA today unless noted. “STATS tick” = `Game.time % 10 === 0` (and some work also on `% 5 === 0`).

| Path | When it runs | Work | Throttle in peacetime now | Cost | Verdict |
|---|---|---|---|---|---|
| Memory parse + pre (`err.pre`) | every tick, before loop body | engine deserialize + one `Memory.creeps` touch | n/a | mem 0.31, pre 0.10 | **Leave.** Already better than Oct. |
| `trace.wrap` / `ledger.wrap` | once per global reset | hook Creep/Spawn/Tower/Link intents | n/a after first tick | folded into intent / ledger 0.03 | **Leave.** |
| dead `Memory.creeps` GC | every tick | loop names | n/a | unmetered, tiny | **Leave.** |
| **home `spawnMgr.run` × 2** | every tick, both RCL7 spawns | `fillmeter.tick`; if spawning: `setRoleTargets` (filter all creeps, pickup backlog, walls, `targets()`). If idle: `IDLE_EVERY=4` **only after a fully idle pass**. Energy-wait (`waited=true`) **clears `sw.ne`**, so both spawns re-run `run1` (~2.4 ms historically) every tick: `_.filter(Game.creeps)`, remote spawn scans, `FIND_HOSTILE` on the skip path, plan/roads/walls, sometimes `FIND_MY_SPAWNS` for W47 independence. | **Mis-armed.** Skip works on true idle; **not** while wanting a body and waiting for energy — the common 15k-floor state. Hostiles force a full pass (good). | **spawn 1.00** (was 0.18) | **Already in-flight** (arm `sw.ne` on wait too). |
| **`W8.spawnRun` × 2** | every tick, both W47 spawns, **no idle throttle** | always: `mine()` over `Game.creeps`, `FIND_MY_CONSTRUCTION_SITES`, `updateSealPark`. If not spawning: full want cascade — `looseE` (2 finds), `FIND_HOSTILE`, `wallsLow` / `FIND_STRUCTURES`, leanBank / softCap / surplus, mineral finds, `dayofMiss`, etc. | **None.** Early-return only while `spawn.spawning` or commander owns the spawn. Two spawns × the heavy path. | **w8spawn 0.97** (was 0.31; 0.05–0.11 in the Oct 20 quiet snapshot) | **Already in-flight** (one decision per room + idle/wait throttle, hostiles/commander bypass). softCap surplus jump is a separate in-flight policy fix, not the main CPU cut. |
| `W8.layoutRun` | every 20 ticks (`Game.time % 20`) | sites, seal, RCL7 industry flags | armed | w8layout 0.10 | **Leave.** |
| `W8.towerRun` | every tick, 3 towers | hostiles find; peace: retarget every 10, then heal/repair intents | retarget every 10; growthPaused every 5; energy floors 600/800 | **w8tower 0.29** (was 0.15) | **Measure first:** skip repair when `hits >= hitsMax` (Oct 20 item, still unfixed). Do not drop a tower. |
| home `layout.run` | every 25 ticks, or RCL change | FIND structures/sites/hostiles, place/destroy | armed | layout 0.04 | **Leave.** |
| home `tower.run` | every tick, 3 towers | same pattern as W47 | same | tower 0.10 | **Measure first**, same hits check. Currently cheap. |
| `links.run` | every 3 ticks, home only | cached links, at most a few `transferEnergy` | armed (`% 3`) | links 0.03 | **Leave.** |
| `labs.run` (home; W47 has no call in this branch) | **every tick** | `readyObs`: `FIND_MY_STRUCTURES`, walk labs, write `Memory.ops.labReady`. Reaction only if `Memory.ops.labs` is set — it is not. | **Not armed.** Dormant reaction, hot observation. | **labs 0.10** | **Cut now** (throttle `readyObs` to 10–50 ticks). Do not flip labs on. |
| `alerts.run` owned + remotes | every tick (hostiles + event log); structure hit-diff every 5 | `FIND_HOSTILE`, `getEventLog`; every 5: `FIND_STRUCTURES` | scan throttled to 5 | alerts 0.15 (flat since Oct) | **Leave.** Needed for Invader alerts. |
| `remote.run` + `threat.run` | every tick, every CFG + GUARD remote (W45N8, W45N7, W47N7, plus dynamic `resRooms`) | reservation scan of visible rooms, threat FSM, lookForAt on visible remotes | none (cheap bookkeeping) | remote 0.42 | **Leave.** Do not open another remote. |
| `roads.run` | RCL≥6; phase `done` → `maintain` every 100 ticks | look at planned tiles, maybe re-site decay | armed (`% 100 === 63` in maintain) | roads 0.03 | **Leave.** |
| `cmd.armed` / `runHeldStructures` | every tick check; body only if `Memory.cmd.on` | one falsy check in peacetime | dormant | cmd 0.03 | **Leave.** |
| `raid9.tickFlags` | every tick | forceGo flags; no raid live | cheap when idle | raidFlags 0.03 | **Leave.** |
| `cpuorder.order/shed` | every tick | bucket ≥ 2000 → `Object.keys(Game.creeps)`, no sort, no shed | **Dormant** (bucket 10000, LOW=2000) | unmetered, tiny | **Leave.** Correctly asleep. |
| **creep loop** (41 live) | every tick, skip spawning | `home.flee` for civilians (hostiles cached per room/tick — peacetime one FIND then false). Role `run`. `move.to` uses heap path cache (`c` reason) + per-room matrix version (FIND structures/sites once per room per tick). Intent cost ~0.2 when they actually act. | no per-role throttle; sticky targets / path cache already on | **creep 10.38** (~0.25–0.28 each; queen 0.41) | **Do not cut miners, queens, 2 fillers, reservers, or armed defenders.** Hauler-count levers: see ranked cuts. |
| `home.flee` | every civilian creep | peacetime: cached empty hostile list | cached | inside creep | **Leave.** |
| `utils/move.js` | on movement | version + matrix cached per room/tick; search cache up to 2000 entries | armed | inside creep (queen/hauler) | **Leave.** Cache hits already dominate queen rp100. |
| `visuals.js` | **not called from `main.js`** | — | not in the tick | unmetered, **zero** | **Leave.** Do not turn it on. |
| `walls.js` / `upgfeed.js` | not a top-level manager. walls: from spawn/layout/tower. upgfeed: from stats every 5 ticks, home only, writes `Memory.ops.upgFeed` (obs, no spawn change) | finds via roomcache | upgfeed every 5 | inside spawn / stats 0.12 | **Leave.** |
| `threat.js` leftover after a kill | threat FSM stays in DEFEND until cleared; `remotePatrol` default ON (defenders patrol until TTL, no auto-recycle) | defender/guard creeps still run | policy, not a bug | visible this hour: 2+1+1 combat creeps, model idle 1.0 | **Leave.** W45N7 still DEFEND since 15:05; W47N7 cleared 16:04, bodies still walking down TTL. |
| `ledger.tick` | every tick | source regen waste, ids cached | cheap | ledger 0.03 | **Leave.** |
| `trace.tick` + `trace.run` | tick: every tick, one char per creep. run: every 5 build a window; **every 10 stringify ≤90 KB into segment 90** | JSON.stringify of the ring | every 10 for the expensive write | EMA **trace 0.16**; **STATS-tick `trace_cpu` 0.98** (live 16:39: 0.977) | **Measure first** if we want p95 relief (offset the write off `% 10 === 0`, or cap ring size more aggressively). Real average save is small; observability risk if we drop windows. |
| `stats.run` | every tick cheap fields; room details every 5 (`FIND` sites + hostiles, storage/ctl) | plus EMA update, remote snapshot, upgfeed every 5 | details every 5 | stats 0.12 EMA; heavier on STATS ticks | **Leave** the data; maybe don’t pile more finds onto `% 10`. |
| `report.run` | every 10 ticks | `console.log` of the STATS JSON (both rooms, creeps, gcl) | armed | report 0.03 EMA; the log itself is why room_stats ticks are dearer | **Leave.** This *is* the patrol feed. |
| Post-loop Memory serialize | after `loop` returns; billed, not in getUsed() | 26 KB live | n/a | **unmetered** | **Leave.** Cannot cut without shrinking Memory.ops / stats. Do not invent a cost. |

---

## Ranked additional CPU cuts

In-flight work is listed only so it is not double-counted.

| # | Action | Est. save | Locus | Risk | When |
|---|---|---|---|---|---|
| — | W47 `spawnRun` once per room + idle/wait throttle; home `sw.ne` also on energy-wait | **0.9–1.3** | `rooms/w47n8/index.js`, `managers/spawn.js`, `main.js` | replacement may start ≤3 ticks later; hostiles/commander must bypass | **Already in-flight** |
| — | Gate W47 surplus upgraders (keep=2 until sticky 40k, then steady 3) | **0.1–0.3** CPU plus the bank/upgrade win | `rooms/w47n8/index.js` | ops win, not a CPU project | **Already in-flight** |
| 1 | W45N7 rhauler body trial: 5× small → 2× cap-sized, same CARRY (Oct 20 proposal, still unshipped) | **~0.7** | `managers/spawn.js` / remote CFG (`haulers`, `rhE`, `rhGap`) | lumpier deliveries, 3 container neighbours, lead/gap timing. Rollback = one constant | **Measure first / trial.** Best remaining creep-count lever. Do not ship blind. |
| 2 | Throttle `labs.readyObs` (every 10–50 ticks). Do not set `Memory.ops.labs` | **0.05–0.08** of the 0.10 | `managers/labs.js` `run` / `readyObs` | patrol `labReady` becomes slightly staler | **Cut now** after the in-flight PR, or even in it if convenient. Labs stay off. |
| 3 | Tower `repair` only if `hits < hitsMax` (and drop a already-full `towerRep`) | **0.05–0.15?** unmeasured | `managers/tower.js` ~L81; `rooms/w47n8/index.js` tower path | none if the check is correct; was already recommended 10-20 | **Measure first** (`tr` ledger vs hits). |
| 4 | After softCap is sticky at keep=2 and src_A recovers, revisit W47 HMAX / 3rd–4th `w8hauler` | maybe **0.3–0.6** later (2 haulers × 0.28) | `rooms/w47n8/index.js` HMAX / looseE valve | **src_A is 2.47 vs 9.60 right now.** Cutting the valve will pile source A | **Don’t, until measured post-softCap** |
| 5 | Offset or shrink segment-90 stringify so it does not land on the STATS tick | mostly **p95 cosmetics** (~0.8 on those ticks), little average | `utils/trace.js` `run` (`Game.time % 10 === 0`) | can hide patrol lag or drop windows if over-shrunk | **Measure first.** Not a substitute for (1) or the spawn PR. |
| 6 | Queen sticky fill / fewer new-target walks | **~0.1** | `roles/queen.js` | small; rp100 is mostly cache hits | **Not first.** |

**Do not cut:** local miners, remote miners, the two queens, the two W47 fillers (refill = defence reaction speed), reservers / reserve7, armed or just-cleared defenders and the W47 gate guard, upgrade itself, or the leftover overflow haulers while src_A is soft. **Do not** open a remote, flip labs or market, or call `generatePixel` (the bucket is the only reserve for 28–76 deploy/combat spikes).

---

## Data holes (do not over-claim)

- **room_stats / cpu_prof / creep_cpu vanish in box sleep** and are not backfilled from official history. From Nov 5 onward the box hibernates most of each hour: today 427 W46N8 STATS samples vs ~1300+ if continuous; notable sleeps today include 03:24–04:18, 04:26–05:18, and a long string of ~50 min holes through the morning, plus afternoon 14:42–15:00, 15:09–15:22, 15:40–16:01, 16:09–16:15 (from the 16:23 note and `metrics/box_pauses.jsonl`). Averages are still usable; do not treat them as complete tick coverage.
- **cpu_prof is sparse after Nov 5:** 10 / 7 / 1 / 10 polls on Nov 6, 8, 9, 10. **None on Nov 7.** Last poll today **15:38 HKT** — the 16:00 hour (leftover defenders, STATS 18–20) is **not** in cpu_prof. Section ratios are trustworthy where polls exist; today’s 14.94 is an all-tick EMA, not a substitute for the 17.12 / 20.59 room_stats figures.
- **Oct 13 10:19–Oct 15 23:33** was lost in the box image reset (docs/DATA.md). **Oct 22 10:45–Oct 29 09:22** is a second 7-day hole (no room_stats, no cpu_prof). Home RCL7 is first *visible* at 10-29 09:22; it may have happened during the hole.
- **Oct 20 “34 creeps / 10.5 EMA / w8spawn 0.05–0.11”** in docs/CPU.md is a quiet snapshot, not the daily baseline (37.0 creeps, EMA 11.42, w8spawn 0.31). Comparisons in this note use the daily figures unless labelled as a snapshot.
- **creep_cpu is awake-only** (segment 90). Use per-creep ms and live counts, not span-averaged role totals across sleep. W47 role names in `creep_cpu` are short (`wrhauler`, `whauler`, …); `room_stats.creeps` uses `w8*`.
- **Official history** fills `creep_ticks` positions only. Newest ~100 ticks are unpublished. Listener is single-slot 5:5:1:1; this analysis did not start a second websocket or war_cmd/pulse.
- Live census 16:39 HKT is from `metrics/live.json` (existing listener), not a new API memory read.

---

## Bottom line

The 17–18 / 20 number is a three-week climb: second room, then RCL7 second spawns, then the Nov 1 loss of the Oct spawn-throttle win, then a slower hauler/filler creep-count drift. The in-flight spawn throttle should give back the **+1.5 spawn regression**. After that we will still be in the mid-16s on STATS ticks with p95 near 20, because creeps (especially haulers) are 1.4 CPU heavier than October and the 10-tick observability beat is unchanged. Next safe lever is the W45N7 rhauler body trial, then small dormant-path trims (labs obs, tower repair check). Not another remote, not labs on, not cutting W47 haulers while source A is still at 2.5 e/t.
