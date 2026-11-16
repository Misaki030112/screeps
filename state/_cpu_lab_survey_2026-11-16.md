# CPU + KO lab readiness survey — 2026-11-16

**When:** 2026-11-16 16:08 Asia/Hong_Kong (box-local).  
**Live commit:** `ffdf767` (deployed 2026-11-15 00:27 Asia/Hong_Kong, tick 84268045). Confirmed in `deploys` and every recent `room_stats.commit`. No newer game deploy.  
**This run:** measurement and report only. No Memory writes, no deploy, no flag flips, no `Memory.cmd`, no second websocket slot, no `war_cmd`/`war_pulse`, no construction sites, no game-code edits. Console reads used `tools/q.py` only (expression, OK=0). Peacetime listener kept the single room slot.

**Shard / budget:** shard3, rooms W46N8 (home) + W47N8 (W47), remotes W45N8 / W45N7 / W47N7. `Game.cpu.limit=20`, `tickLimit=500`. Live at tick **84300846** (~16:03): bucket **10000**, 37–38 creeps, used mid-tick 17.92 (partial). Tick rate from 12h room_stats first/last: **4.480 s/tick**.

Supporting query dumps: `/workspace/screeps/state/_cpu_lab_survey_2026-11-16/`.

---

## 0. How to read the CPU numbers

Two different CPU series are in play, same gap as the 2026-11-10 analyses:

| Series | What it is | 12h mean | Use for |
|---|---|---:|---|
| `room_stats.cpu` (W46N8 row only; colony CPU is duplicated on W47 rows) | STATS console every 10 ticks, already the expensive beat (segment-90 stringify + room details + `STATS` log) | **17.766** | Headroom vs the 20 cap, p95, “are we over 18/20” |
| `cpu_prof` EMA (`Memory.stats.prof`, all ticks, listener poll ~15 min when the box is awake) | Section split | **15.548** (10 polls) | Where CPU goes. Live EMA at 16:03: **14.85** |

The ~2.2 gap is mostly sampling bias (STATS-tick `trace_cpu` avg **0.777**, max 6.187, vs EMA trace 0.148), not 2 CPU of unmetered mystery work. Post-loop Memory serialize is still not in `Game.cpu.getUsed()` / either table.

**Coverage holes:** box hibernation stops the listener; official history backfills `creep_ticks` only, not `room_stats` / `cpu_prof` / `creep_cpu`. 24 box pauses from 04:09–16:00, **19 697 s (~5.5 h)** frozen. `room_stats` 12h: 506 STATS samples vs ~981 if continuous every 10 ticks (**~52%**). `creep_cpu` 12h: 1 785 distinct ticks / ~9 640 span (**~18.5%**, segment-90 ring). Averages are usable; do not treat them as complete tick coverage. Histogram “% of ticks” below is **% of observed STATS samples**, which already over-weights the expensive 10-tick beat.

---

## 1. Prior CPU work vs what is expensive now

Sources: `state/_cpu_full_logic_analysis.md` and `state/_softcap_cpu_analysis.md` (both 2026-11-10, then-live `5892e31`), plus `docs/CPU.md` (Oct 20 baseline). The spawn-idle / softCap / `labs.readyObs` work landed as `c6c80d38` (“fix(w47): hold 2 upgraders until 40k sticky bank; throttle idle spawn and lab scan (#33)”) and is **in the live `ffdf767` tree**.

| Item (Nov 10 conclusion) | Expected | Live now (12h cpu_prof unless noted) | Verdict |
|---|---|---|---|
| W47 `spawnRun` once-per-room + idle/wait throttle | −0.5 to −0.7 of then 0.97 `w8spawn` | **w8spawn 0.695** (range 0.262–0.897; live 16:03 EMA **0.856**; 15:38 poll 0.262) | **Partial win.** Down from 0.97, still ~2× Oct 20 daily 0.31. Swings with whether both spawns are busy. |
| Home `sw.ne` also armed on energy-wait (`IDLE_EVERY=4`) | −0.4 to −0.6 of then 1.00 `spawn` | **spawn 2.012** (range 1.719–2.444; live EMA **1.475**; 15:38 poll 1.853) | **Not fixed — worse.** This is now the #1 manager cost. See §5 candidate 1. |
| Throttle `labs.readyObs` to 10–50 ticks (`READY_EVERY=20` in `src/managers/labs.js`) | −0.05 to −0.08 of then 0.10 | **labs 0.031** | **Done.** Stay off until a deliberate labs-on decision. |
| After throttle, room_stats avg 15.8–16.2, p95 still ~19–20, EMA 13.6–14.0 | — | room_stats 12h **17.77 / p95 20.84**; 3h **18.11 / p95 21.50**; EMA 15.55 | **The promised average recovery did not show up**, because home `spawn` rose instead of falling, and creep count stayed ~36–40. |
| Next real lever is creep count (haulers), not more manager micro-cuts | W45N7 5×8C8M → 2×20C20M, ~−0.7, unshipped | Still unshipped. Haulers still ~4.5 CPU (see below). | Still the largest creep lever. Standing constraint: do not change live transport bodies unless new data overturns the RCL7 8C8M model — flag, do not ship blind. |
| Tower `repair` only if `hits < hitsMax` | 0.05–0.15?, unmeasured | `w8tower` 0.368 + `tower` 0.202. Home `tower.js` L125 still calls `t.repair(rep)` without a `hits < hitsMax` check (candidate set is filtered by `hits < capFor(s)` when retargeted). | Still open, smaller than spawn. Measure before cutting. |
| Offset segment-90 stringify off the STATS tick | p95 cosmetics | STATS-tick `trace_cpu` still ~0.78 avg, 6.19 max | Still open, p95 only. |
| Do not flip labs / market; do not open a remote; do not cut keep / 15k / max-spec defenders; military path cache stays off | — | All still hold in live flags/code. | Still stand. |

**Nov 10 accounting still describes the shape, not the current magnitudes.** Creep is still ~10.3 / ~66% of EMA. Spawn managers were supposed to shrink by ~1.0–1.3 and did not (net spawn+w8spawn now **2.71** vs Nov 10 **1.97** vs Oct 20 daily **0.49**).

---

## 2. CPU picture, last 12 / 6 / 3 / 1 hours

Window source: `room_stats` where `room='W46N8'` and `ts > now()-interval`. Computed 16:03 Asia/Hong_Kong (tip later 16:07, tick 84300890). Bucket is effectively full in every window (12h min **9983**, 1h min **9999**, avg 9999.9–10000).

| Window | samples | first→last (HKT) | ticks | avg | p50 | p90 | p95 | p99 | min | max | >20 | ≥20 | >18 | <15 | bucket min |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **1h** | 43 | 15:04–16:03 | 84300100–84300840 | **17.333** | 17.330 | 19.278 | **20.042** | 21.536 | 14.40 | 21.99 | 3 (7.0%) | 3 | 14 (32.6%) | 3 (7.0%) | 9999 |
| **3h** | 131 | 13:04–16:03 | 84298590–84300840 | **18.105** | 17.710 | 20.720 | **21.495** | 23.171 | 14.40 | **23.88** | 22 (16.8%) | 22 | 65 (49.6%) | 3 (2.3%) | 9983 |
| **6h** | 277 | 10:03–16:03 | 84296140–84300840 | **17.862** | 17.500 | 20.266 | **21.058** | 24.314 | 13.28 | **27.11** | 33 (11.9%) | 33 | 115 (41.5%) | 10 (3.6%) | 9983 |
| **12h** | 506 | 04:03–16:03 | 84291200–84300840 | **17.766** | 17.500 | 20.035 | **20.843** | 23.209 | 13.28 | **27.11** | 53 (10.5%) | 53 | 198 (39.1%) | 15 (3.0%) | 9983 |

No sample in 12h exceeded 40 (no deploy / global-reset spike in this window). 3 ticks in 6h/12h were in 25–40: **27.11, 26.66, 25.69**, all in the 11:09–11:32 cluster.

**Histogram (observed STATS samples):**

| bin | 12h | 6h | 3h | 1h |
|---|---:|---:|---:|---:|
| <14 | 1 | 1 | 0 | 0 |
| 14–15 | 14 | 9 | 3 | 3 |
| 15–16 | 61 | 34 | 12 | 7 |
| 16–17 | 106 | 55 | 23 | 6 |
| 17–18 | 124 | 62 | 28 | 13 |
| 18–19 | 84 | 44 | 28 | 8 |
| 19–20 | 63 | 39 | 15 | 3 |
| 20–22 | 42 | 24 | 18 | 3 |
| 22–25 | 8 | 6 | 4 | 0 |
| 25–40 | 3 | 3 | 0 | 0 |

Plain reading: on the already-heavy STATS beat, **about 2 in 5 samples are over 18, about 1 in 10 over 20**. p95 sits on or above the 20 cap in every window. The 1h just after 15:00 is a bit quieter (avg 17.3, 7% >20) but p95 is still 20.04. This matches the 15:27 patrol (1h avg ~18.2, peak 23.01) and the 14:26 patrol (1h avg 18.48, peak 23.88) — those peaks are real and recurrent, not one-tick flukes.

**Hourly room_stats (home storage in this table is W46N8 only):**

| Hour HKT | n | avg | p95 | max | >20 | >18 | creeps avg/max | notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 04 | 33 | 16.89 | 19.52 | 21.30 | 1 | 6 | 35.5 / 38 | |
| 05 | 38 | 17.22 | 19.46 | 20.40 | 2 | 10 | 34.7 / 37 | W45N7 Invader 05:30, ended 05:57 |
| 06 | 38 | 18.09 | 20.24 | 21.89 | 4 | 20 | 36.7 / 39 | |
| 07 | 44 | 17.84 | 20.61 | 20.82 | 4 | 18 | 37.0 / 40 | |
| 08 | 36 | 18.60 | 21.91 | 22.38 | 6 | 20 | 39.5 / 41 | W45N7 Invader 08:17; w8rhauler up to 7, a home builder briefly live |
| 09 | 36 | 17.29 | 20.17 | 21.70 | 3 | 9 | 36.2 / 39 | |
| 10 | 51 | 16.99 | 19.58 | 20.53 | 1 | 9 | 35.6 / 40 | W47N7 Invader 10:45, ended 11:10 |
| 11 | 48 | 18.21 | **24.04** | **27.11** | 4 | 20 | 38.1 / 40 | Three 25–27 spikes, 0 home hostiles (see below) |
| 12 | 46 | 17.58 | 20.61 | 23.22 | 5 | 19 | 37.6 / 41 | |
| 13 | 42 | 18.04 | 21.60 | 23.24 | 7 | 18 | 38.7 / 42 | Dual Invader W45N7+W47N7 13:24; W45N7 high 13:32, both clear by 13:44 |
| **14** | 46 | **18.99** | **22.60** | **23.88** | **13** | **34** | **39.7 / 44** | Hangover + leftover defenders; bucket min **9983**; worst sustained hour |
| 15 | 45 | 17.41 | 20.01 | 21.99 | 3 | 15 | 34.0 / 37 | Quieter census; W47 storage first touched 40k |
| 16 (partial, after 15:46–16:00 pause) | 3 | 16.67 | 17.24 | 17.32 | 0 | 0 | 36.7 / 37 | Too few samples to call the hour |

`room_stats.hostiles` on the W46N8 row stayed 0 all 12h — remotes do not appear there. Hostile context is from `events` (`alert_new` / `alert_ended`).

### 2.1 Section split (cpu_prof)

10 polls in 12h (04:41, 05:34, 06:41, 07:37, then a morning hole, 11:21, 12:37, 13:39, 14:35, 15:09, 15:38). EMA `total` 14.829 → 17.046 → **13.988** (last poll). Live `Memory.stats.prof` at 16:03 tick 84300846:

`total 14.85, creep 10.068, spawn 1.475, w8spawn 0.856, remote 0.392, w8tower 0.376, mem 0.328, alerts 0.159, tower 0.126, trace 0.148, stats 0.105, w8layout 0.095, labs 0.03, others ≤0.032`.

| Section | 12h avg | 6h avg | 3h avg | 1h avg (2 polls) | 12h min–max | vs Nov 10 (then 14.94 / spawn 1.00 / w8spawn 0.97 / creep 10.38 / labs 0.10) |
|---|---:|---:|---:|---:|---|---|
| **total** | **15.548** | 15.607 | 15.448 | 14.858 | 13.988–17.046 | +0.6 vs Nov 10 EMA |
| **creep** | **10.291** | 10.364 | 10.278 | 9.631 | 9.257–11.421 | ~flat |
| **spawn** (both home spawns) | **2.012** | 2.023 | 1.990 | 2.120 | 1.719–2.444 | **+1.0 vs already-high Nov 10** |
| **w8spawn** | **0.695** | 0.650 | 0.545 | 0.506 | 0.262–0.897 | −0.27 vs Nov 10 |
| remote | 0.384 | 0.388 | 0.389 | 0.375 | 0.365–0.408 | ~flat |
| w8tower | 0.368 | 0.365 | 0.370 | 0.389 | 0.308–0.407 | +0.08 |
| mem | 0.321 | 0.324 | 0.326 | 0.316 | 0.306–0.342 | ~flat |
| tower | 0.202 | 0.213 | 0.259 | 0.271 | 0.072–0.387 | higher, noisy |
| alerts | 0.158 | 0.157 | 0.159 | 0.149 | 0.149–0.180 | ~flat |
| trace | 0.148 | 0.149 | 0.148 | 0.141 | 0.134–0.166 | ~flat (STATS-tick still ~0.78) |
| labs | **0.031** | 0.031 | 0.030 | 0.030 | 0.029–0.033 | throttle held |
| everything else | ≤0.12 | | | | | no material drift |

### 2.2 Creep-role CPU (creep_cpu per-creep ms × room_stats mean count including zeros)

`creep_cpu` role names are short (`wrhauler`, `whauler`, …). Counts come from `room_stats.creeps` with missing keys treated as 0. 6h is the more stable “current regime”; 1h is the quieter post-invasion hour.

| Role | 6h n | 6h ms/creep | **6h CPU** | 12h n | 12h ms/creep | 12h CPU | 6h idle | 6h rp100 | 1h CPU |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rhauler | 6.76 | 0.261 | **1.76** | 6.65 | 0.259 | 1.72 | 0.80 | 4.5 | 1.79 |
| w8rhauler | 5.35 | 0.306 | **1.64** | 5.27 | 0.302 | 1.59 | 0.86 | 11.4 | 1.34 |
| w8hauler | 2.86 | 0.352 | **1.01** | 2.96 | 0.350 | 1.04 | 0.86 | **15.3** | 0.72 |
| hauler (home) | 1.01 | 0.144 | 0.15 | 1.01 | 0.139 | 0.14 | **0.98** | 1.6 | 0.13 |
| **all haulers** | **16.0** | | **4.55** | 15.9 | | **4.49** | | | **3.99** |
| queen | 2.17 | 0.339 | 0.74 | 2.15 | 0.343 | 0.74 | 0.74 | 9.5 | 0.66 |
| w8filler | 2.17 | 0.309 | 0.67 | 2.20 | 0.319 | 0.70 | 0.79 | 7.0 | 0.77 |
| w8upgrader | 2.12 | 0.302 | 0.64 | 2.12 | 0.304 | 0.64 | 0.17 | 0 | 0.64 |
| miner | 2.19 | 0.281 | 0.62 | 2.19 | 0.280 | 0.61 | 0.06 | 0.1 | 0.61 |
| upgrader | 1.66 | 0.357 | 0.59 | 1.59 | 0.354 | 0.56 | 0.07 | 0.1 | 0.72 |
| rminer | 2.30 | 0.247 | 0.57 | 2.34 | 0.246 | 0.58 | 0.19 | 1.0 | 0.59 |
| w8rminer | 2.28 | 0.220 | 0.50 | 2.27 | 0.218 | 0.50 | 0.17 | 0.3 | 0.48 |
| w8builder | 1.05 | 0.481 | 0.51 | 1.04 | 0.460 | 0.48 | 0.47 | 0 | 0.46 |
| w8miner | 2.17 | 0.223 | 0.48 | 2.15 | 0.226 | 0.49 | 0.21 | 0.2 | 0.54 |
| reserver | 1.17 | 0.240 | 0.28 | 1.42 | 0.234 | 0.33 | 0.20 | 0.8 | 0.09 |
| reserve7 | 0.84 | 0.232 | 0.19 | 0.73 | 0.229 | 0.17 | 0.14 | 1.2 | 0.06 |
| defender | 0.53 | 0.252 | 0.13 | 0.39 | 0.271 | 0.11 | 1.00 | 0 | 0.11 |
| w8defender / w8guard / builder | low | | ≤0.05 each | | | | 1.00 combat | | 0 |
| **mminer / w8mminer / lab tech / booster / rdef** | **0** | — | **0** | 0 | | 0 | | | 0 |

Haulers are still ~**44% of creep CPU** and ~**25% of STATS-tick used**. w8hauler is the most expensive *per creep* among haulers (0.35 ms, rp100 **15.3**, idle 86%). Home hauler is almost parked (idle 98%, 0.14 CPU) — that is the body `labRun` will ride if KO is turned on. No mineral miner was alive in any 12h `room_stats` sample.

12h live census (zeros included), typical range: 36–40 creeps, max **44** at 14:13. 6h role floors that never dropped to 0: rhauler ≥6, w8rhauler ≥3, w8hauler ≥2, both queens, both filler-capable counts, keep-2 W47 upgraders.

### 2.3 Notable spikes (what was happening)

Top 12h STATS samples, all with `hostiles=0` on the home row:

| HKT | tick | CPU | creeps | Context |
|---|---:|---:|---:|---|
| 11:32:00 | 84297360 | **27.11** | 36 | 0 home hostiles; W47N7 invader had ended at 11:10. `trace_cpu` only 0.607 — **not** a stringify spike. Census ordinary (w8rhauler 6). Unexplained ~10 CPU single-tick jump. Neighbour samples 17.6 / 18.4. |
| 11:30:32 | 84297340 | **26.66** | 37 | Same cluster, `trace_cpu` 1.106. |
| 11:09:37 | 84297060 | **25.69** | 38 | During the W47N7 invader that ended 11:10:59 (tick 84297078). `trace_cpu` 1.073. Next sample already 17.93. |
| 14:13:45 | 84299470 | **23.88** | **44** | Post 13:24–13:44 dual invader (W45N7 + W47N7, one escalation to high). Leftover defenders + handoff overlap: rhauler 8, reserve7 2, reserver 2, w8rminer 3, w8rhauler 6, w8upgrader 3, miner 3. Matches the 14:26 patrol peak. |
| 13:44:24 | 84299100 | 23.24 | 41 | Exact end of the W47N7 core fight (alert_ended 13:44:39). Census: defender 2, w8defender 1, w8guard 1. |
| 12:04:02 | 84297790 | 23.22 | 38 | Peacetime, 0 alerts. Isolated. |
| 14:32:06 | 84299700 | 23.01 | 39 | Same 14:00 hangover hour (34 of 46 samples >18). 15:27 patrol peak. |
| 15:43:51 | 84300600 | 21.99 | 35 | Quiet census; last >20 before the 15:46 pause. |

**14:00 was the only hour that systematically sat on the cap** (avg 18.99, 13/46 >20, 34/46 >18, creeps 39.7/44, bucket 9983). That is leftover defence + inflated hauler/reserver overlap after the 13:24 dual invader, plus `defenseDue()` in `src/managers/spawn.js` L505–513 (and the W47 equivalent `spawnForce`) bypassing the idle skip whenever `threat.wantDefender` / `holding` / `energyHold` is set. Do not recycle those defenders for CPU (standing constraint: do not shrink max-spec defenders).

The 11:30 25–27 cluster is **not explained** by home hostiles, creep count, or `trace_cpu`. A CloudAgent should not “fix” it without a new per-section capture around a recurrence. Treat as a rare single-tick jump the bucket absorbs.

`events` 12h: 24 `box_pause`, 6 `alert_new`, 5 `alert_ended`, 1 `stuck` (w8filler at 14:57, 33,33→34,32, known-class), 336 `watch`. No error flood.

---

## 3. Live colony snapshot

Console: `q_flags.json` tick **84300846** (~16:03), stores/labs/deposits/ramparts/creeps **84300855–84300899** (~16:04–16:07). All Asia/Hong_Kong.

### 3.1 Energy

| Location | Energy | Notes |
|---|---:|---|
| W46N8 storage | **16 697** | Above the 15k floor, cushion only ~1.7k. 12h min 12 916, max 19 787, never ≥20k (3rd-upgrader 20k/300t gate still unreached). 12h 118/506 samples <15k (23%). 1h all ≥16 397. |
| W46N8 terminal | **0** | |
| W47N8 storage | **36 183** | Down from the 15:08–15:24 40 553 touch (~210 ticks, 8 `room_stats` samples ≥40k, lock 500t **not** triggered). `Memory.ops.w8day.upgKeep` live **2**. 12h min 23 061, max 40 553. |
| W47N8 terminal | **1 096** | Enough for a thin K send fee, but send is blocked on home terminal fullness (below). |
| `Memory.defense.reserveE` | **15 000** | Unchanged. Do not change it. |

### 3.2 Minerals (live; Nov 15 03:20/04:33 snapshot is stale only in the W47 K-deposit and W47 terminal K)

| Resource | Home storage | Home terminal | W47 storage | W47 terminal | Containers | Deposit | **Colony total in stores** |
|---|---:|---:|---:|---:|---:|---|---:|
| **K** | 0 | **172 792** | 64 | **33 708** | home 0; W47 37,44: 20 | W47 (37,45): **0, regen 29 370 ticks** (~36.5 h at 4.48 s/t, ~04:37 on 11-18) | **206 584** |
| **O** | **17 324** | **126 976** | 0 | 0 | home 41,24: 20 | Home (40,24): **30 680 still remaining**, ttr=0, extractor CD 0 | **144 320** in stores + 30 680 in the deposit |
| **KO** | 0 | 36 | 17 | 118 | 0 | — | **171** (Invader-loot leftovers) |
| GO / ZH / UH / LO | 0 | 135 / 42 / 19 / 0 | 390 / 69 / 11 / 19 | 570 / 138 / 11 / 0 | 0 | — | small loot only |

Home **O** extractor at (40,24) hits 500; W47 **K** extractor at (37,45) hits 500, deposit empty.

**Home terminal is 300 000 / 300 000, free 0** (`O+K+GO+KO+ZH+UH`). `Memory.ops.w8min.sendWhy='homeFull'`, `homeFree=0`. Last successful K send: tick **84263164**, amount 256 — about **47 h earlier** (~17:10 on 11-14). W47 still has 33 708 K waiting in its terminal.

`Memory.ops.mineralCap = 50000`. `mineralCapped()` in `src/managers/spawn.js` L89–93 stops a room’s mineral miner when storage+terminal of that mineral ≥ cap. Home O (144 300) is **capped**, so no `mminer`. W47 K in-room (33 772) is **under** 50k, but `mineralAmount===0`, so no `w8mminer` either. `w8min.miners=0`, `why/gaps='miner'`, `minerPrio=1`, `minOk=1`, `labsOk=0`.

### 3.3 Labs, factories, flags, covers

Both rooms: **6 labs + 1 factory**, all standing, all **empty** (no minerals, no energy, cooldown 0). Factory both at **(35,30)**.

Home labs (all have point ramparts):

| Tile | Role in the 11-12 plan | Rampart hits | Cap |
|---|---|---:|---:|
| 34,22 | input A (RCL6, already built) | 1 003 701 | 1e8 |
| 35,21 | input B (RCL6) | 1 001 981 | 1e8 |
| 33,21 | output (RCL6) | 1 001 941 | 1e8 |
| **34,23** | output (RCL7) — asked tile | **304 201** | 1e8 |
| **33,22** | output (RCL7) — asked tile | **303 681** | 1e8 |
| 34,20 | output (RCL7) | 301 541 | 1e8 |
| Factory 35,30 | | 300 721 | 1e8 |

Asked home covers **34,23 / 33,22 already exist and are above 300k**. The three legacy RCL6 labs still sit at ~1.00M (placed before `f7328c4e` capped new covers at 300k).

W47 labs (cluster matches the 11-12 plan; unique input pair would be 27,38 + 27,39):

| Tile | Rampart | Sites |
|---|---|---|
| 27,38 (plan input A) | **300 621** | none |
| 27,39 (plan input B) | **NONE** | none |
| 29,38 | **NONE** | none |
| 28,37 | **NONE** | none |
| 28,38 | **NONE** | none |
| 27,40 | **NONE** | none |
| Factory 35,30 | **300 701** | none |
| Hub link **32,33** | **NONE** (link hits 1000, no rampart, no site) | none |
| Old hub 33,34 | road only (4300), link is gone | none |

W47 has **zero construction sites**. Five of six W47 labs, and the hub link at 32,33, have no 300k cover and nothing queued. Record only; nothing was placed.

**Memory / compile flags (live, unread-only):**

- `Memory.ops.labs` = **null** (off). `Memory.ops` keys include `labReady`, `w8min`, `mineralCap`, `upgFeed`, `w8day`, … — no `labs`, no `market`.
- `Memory.ops.market` = **null**.
- `Memory.ops.mineralCap` = **50000**.
- `Memory.ops.labReady` at 84300837: `mode=null`, `why='ready'`, `propose=1`, `ready=1`, **`actOk=1`, `actGaps=''`**, `labsN=6`, `kTerm=172792`, `oTerm=126976`, `k=172792`, `o=144300`, `homeStor=16497`, `koTerm=36`, `koLab=0`, `ko=36`, floors `actHome=15000`, `actK=3000`, `actO=3000`. Checklist already green.
- Compile-time: `src/utils/plan.js` `RCL6_MINERALS=true`, `RCL7_INDUSTRY=false`. `src/rooms/w47n8/config.js` `RCL6_MINERALS: true`, `RCL6_LABS: false`, `RCL7_INDUSTRY: false`. Shells were operator-placed; the planner flags are still off and were not flipped.

### 3.4 Creeps (tick 84300870, n=38; one more tick later n includes the spawning defender)

`rminer 2, reserver 2, rhauler 8, miner 3, queen 2, upgrader 2, hauler 1, defender 1 (spawning), w8rminer 3, w8rhauler 4, w8upgrader 3, w8hauler 2, w8builder 1, w8filler 2, w8miner 2`.

- **No** `mminer`, `w8mminer`, lab-tech, or booster role is even in the role table.
- Combat: only `defender84300803`, still spawning at home spawn (35,28), body **25 ATTACK + 25 MOVE** (core buster, 50 parts, unboosted). Memory: `{role:'defender', home:'W46N8', remote:'W45N7', core:1, squad:1, v2:1, _h:5000}`. Visible rooms (W46N8 / W47N8 / W45N8 / W47N7) had **no invader cores**. **W45N7 was not visible**, so the core was not confirmed. `threat.wantDefender/holding/energyHold` were false on all five room names; `home.wantGuards=0`; `w8day.upgKeep=2`. Treat as “home started a W45N7 core-buster at 16:04; destination room not visible in this snapshot.”
- No live kite (`RANGED_ATTACK`) body, no `rdef` / `w8defender` / `w8guard` at this snapshot (those only appear after invasions; 6h averages 0.53 / 0.33 / 0.32).
- `w8upgrader=3` at this snapshot is a handoff overlap under keep=2 (1h average 2.09, max 3), not a 40k latch.

---

## 4. Existing code status (checkout only, no edits)

Live code already contains a **dormant KO reaction + hauler logistics path**. It does **not** contain a boost path.

### 4.1 Reaction / lab operator — exists, flag-gated

| Piece | File / symbol | What it does |
|---|---|---|
| Flag | `Memory.ops.labs = { W46N8: 'KO' }` | `labs.cfg(room)` in `src/managers/labs.js` L18. Never auto-set. `readyObs` only *proposes*. |
| Recipe table | `labs.R` L6 | `KO: ['K','O']` plus LO/UH/OH/ZO/UO. First-class KO plan. |
| Ready / activate checklist | `readyObs`, `PROPOSE_K/O=1000`, `ACT_HOME_STOR=15000`, `ACT_K_BUF=3000`, `ACT_O_BUF=3000`, `READY_EVERY=20` | Already publishing `labReady.propose=1` and `actOk=1`. |
| Reaction tick | `labs.run` L81–96 | If cfg set: find labs, `roles()` (output = unique lab in range 2 of both others), `runReaction` when both inputs ≥5, output empty or already KO, no cooldown. Returns 0 immediately if cfg unset. |
| Lab logistics | `roles/hauler.js` `labRun` L92–109, called from `homeHauler` `run` L129 after `mineralRun` | Empty home hauler executes `labs.task()`: fill each input from terminal to 1000, dump output ≥1000 back to terminal, empty a wrong reagent. No dedicated lab-tech body. |
| Task | `labs.task` L27–33 | Terminal must exist; cfg must be set. |
| W47 K pump | `rooms/w47n8/index.js` `mineralSend` L760–828 | Already live while `RCL6_MINERALS`. Currently **`sendWhy=homeFull`**. Batches 5000, or 1000 when stor < `LEAN_ARM`. |
| Tests | `tests/labs_hauler.js` (referenced from the hauler comment) | |

**W47 is not on this path today.** `src/main.js` L21: for `W8.ROOM` the loop runs `w8layout` + `w8tower` and **`continue`s**, so `labs.run` is **never called** on W47. `labRun` is only on the home `hauler` role, not `w8hauler`. Turning on W47 reactions needs a new `labs.run` call (and probably a W47 hauler logistics hook) plus O in that room — not a Memory flag.

### 4.2 Boost path — does **not** exist

The only `boostCreep` hit in `src/` is a comment in `labs.js` L5 / L38: *“Lab energy fill / boostCreep wait KO≥900 (**boost.js later**).”* There is no `src/managers/boost.js`, no `boostCreep(` call, no lab-energy fill, no spawn-side “walk to lab and boost before leaving,” and no default-boost hook on defender / rdef / guard / kite spawn.

“远程攻击兵” in this codebase is the **kite** recipe `B.defender` / `B.guard` in `src/managers/spawn.js` L45–55, L77–78: at RCL7 cap 5600 = **19 RA + 25 MOVE + 6 HEAL** (190 dmg / 72 heal). `rdef` and home guards use the same body. The 25A25M body seen live is `B.coreBuster` (melee, not a KO target). Combat roles exist (`defender`, `rdef`, `w8defender`, `w8guard`); none is boosted.

Default-boosting kites with KO **requires new code and a deploy**, not a flag flip.

### 4.3 CPU and energy cost of enabling, from the code (high level)

**KO reactions only** (`Memory.ops.labs = { W46N8: 'KO' }`, no new deploy if we accept current `ffdf767` behaviour):

- `readyObs` drops its 20-tick throttle the moment cfg is set (L44 is `if (!cfg(room) && …)`), so home `FIND_MY_STRUCTURES` returns to every tick (~+0.07–0.10; we measured the throttled residual at 0.03).
- `labs.run` additionally finds labs every tick and, once reagents are loaded, `runReaction` (0.2 intent) on each output that is off cooldown. T1 cooldown is 10. With the unique input pair (34,22)+(35,21) in range 2 of all four other home labs, **up to 4 outputs** can run: 4 × 0.2 / 10 = **0.08** average, plus 4 × 5 KO / 10 ticks = **2.0 KO/tick** once both inputs stay ≥5.
- `labRun` rides the existing home hauler, which is idle **98%** of 6h and costs 0.14 already. Extra cost is a few withdraw/transfer intents and walks while loading/unloading, not a new creep. First fill is two 1 000-unit terminal→lab trips.
- Reaction itself **consumes no energy**. Boost later does (20 energy per boosted part, in the lab).
- Net estimate: **+0.15 to +0.40 CPU** while reacting, after the one-time load. Small next to the 2.0 home-spawn problem, but it is a cost, not a saving.

**Default KO boost** (not in tree): one-time (or per-wave) 19×30 = **570 KO** and 19×20 = **380 energy** per max-spec kite, plus a boost lab that must be filled with KO+energy, plus `boostCreep` intents, plus spawn-to-lab travel / a possible spawn-wait. The comment’s KO≥900 floor is a conservative single-lab fill (covers 30 parts; a 19-RA kite only needs 570). Do not pull that 380e out of storage while the 15k floor has only a ~1.7k cushion.

---

## 5. Readiness call — K+O→KO and default KO boost

### 5.1 Home KO reactions: **GO, with three operational caveats** (do not flip the flag in this run)

Why GO:

- Stocks crush a conservative first batch. Checklist floors are 1 000 / 3 000; home already holds **172 792 K** and **144 300 O**. A 1 000+1 000 first fill (the code’s `task` / `PROPOSE_*` size) is <1% of stock. Even a 10k batch is fine. O is the limiter; 144 300 O → 144 300 KO if fully reacted.
- `labReady.propose=1` and **`actOk=1`** already. Home storage 16 697 ≥ 15 000. Terminal K/O buffers ≫ 3 000.
- All 6 home labs + factory already have ≥300k covers (asked tiles 34,23 / 33,22 included).
- Operator body already exists: the idle home hauler + `labRun`. No new spawn, no 15k-floor creep cost.
- Reaction uses no energy, so it does not fight the 15k floor or the RCL8 / upgrade push by itself.
- At 2.0 KO/tick (4 outputs, after both inputs are loaded) the current home O stock is ~**20 hours** of continuous full-rate reaction, or ~**90 hours** if you count only 0.5 KO/tick on a single output. No need to mine anything for the first wave.

Caveats (fix or accept before / as you flip `Memory.ops.labs`):

1. **Home terminal is full.** First withdraw of 1 000 K + 1 000 O opens 2 000 free, which is enough to take 1 000 KO back — volume is net-neutral after that (K+O out, KO in). Continuous reaction will work, but `mineralSend` stays `homeFull` and W47’s 33 708 K cannot move. **Recommended pre-step (ops, not a flag):** move a slice of terminal O (and/or excess K) into home storage (965 979 free) so `homeFree` is healthy and KO / future K have a sink. The current `task()` will not do that itself. Do not do this in a way that confuses the hauler mid-reaction.
2. **“Stable production” is currently paused, not broken.** W47 K deposit is **empty, regen ~36.5 h**. Home O can still be mined (30 680 left) but `mineralCap=50000` is holding `mminer` at 0 because O stock is 144k. That is fine for a first reaction wave; it is not “K and O are being produced right now.” After KO starts, consider raising or scoping `mineralCap` so a drained reagent can refill, and expect K mining to resume only after ~11-18 04:37 HKT.
3. **CPU is already on the 20 cap at p95.** Enabling reactions adds ~0.15–0.40. Prefer landing the home-spawn cut (§5) in the same or an earlier deploy, or accept a slightly tighter peacetime average.

Do **not** start W47 reactions now: `labs.run` is not called there, 5/6 labs and hub link 32,33 have no covers and no sites, and W47 has almost no O. “实验室全部进行起来” should mean **home chamber first**; W47 is a later, separate piece of work (covers + hook + O).

### 5.2 Default-boost ranged attackers with KO: **WAIT — missing code, not missing minerals**

Reasons:

- No `boost.js`, no `boostCreep`, no lab energy fill, no spawn hook. Labs are at 0 energy. Flipping `ops.labs` will make KO; it will **not** boost anyone.
- Need a design+deploy: which lab is the boost lab (must not be an input/output of the reaction pair, or reactions pause while boosting), fill KO≥570 (use the existing 900 floor), fill energy, call `boostCreep` on new kites (`defender` / `rdef` / `guard` / `w8defender` kite bodies) before they leave home, skip core-busters (ATTACK, not RA).
- Energy conflict: 380e per max kite is small, but home storage is only 1.7k above the 15k floor. Do not auto-fill lab energy from storage while under ~20k, or fill from a reserved terminal energy buffer after some energy is moved there (terminal energy is currently 0).
- A 1 000 KO first batch already covers **one** max-spec kite (570) with margin. Do not wait on mining.

**Recommendation to Misaki, short:** 本家 K/O 库存非常充足，反应代码和搬运工都已经在树上，本家六座实验室和护罩也齐了，**可以先在本家开 K+O→KO**（只改 `Memory.ops.labs = { W46N8: 'KO' }`，建议先把终端里一部分 O 挪到仓库腾出空位）。W47 的实验室还缺护罩、也没有反应入口，先不要开。给远程攻击兵默认加 KO 强化 **还不能做**——`boost.js` 根本没写，需要先部署强化走流程，再谈默认强化。K 矿正在再生约一天半，O 矿因为 5 万库存上限暂时停挖，但不耽误第一批反应。

---

## 6. Concrete CPU-cut candidates

Ranked by evidence × expected save. None of these was applied.

| # | Change | Evidence now | Expected save | Risk / constraint |
|---|---|---|---|---|
| **1. Port home spawn to W47’s once-per-room gate** | Home `spawn` is **2.01** EMA (12h), worse than Nov 10’s 1.00, after the wait-throttle already landed. Two RCL7 home spawns still run independently: a busy spawn calls `setRoleTargets` every tick (`spawn.js` L476); `sw` is per-room but `ne` is cleared when a spawn actually starts (L501), so the sibling immediately does a full `run1` (~2.4 ms historically). W47 already has `spawnGate` / `room._sg` (`w47n8/index.js` L65–114): one planning pass per room, second idle spawn returns, hostiles/`defenseDue` still bypass. Live `sw.W46N8` at 16:03: skip 174 738, `ne` was 0 mid-spawn, then re-armed to 84300903; last recorded wait was `w8defender` 5000 at tick 84292163. | **0.8–1.3 CPU** if home matches W47’s “one cascade per room + keep skip armed for the sibling”; maybe another 0.2–0.4 if `setRoleTargets` is not repeated on a busy spawn. This is the only manager cut big enough to move p95 off 20 in peacetime. | Replacement may start ≤3 ticks later (already the documented IDLE_EVERY contract). **Hostiles, `defenseDue` (remote threat / holding / energyHold), commander, and `canPay` must still force a full pass** — do not weaken first-tick defender spawn (PR 42 / max-spec constraint). Measure `Memory.stats.prof.spawn` and `sw.skip` after. |
| **2. Keep tightening W47 `w8spawn` busy path** | 12h 0.695, still 2× Oct 20 daily 0.31. Code already one-pass; residual is `mine()` + `FIND_MY_CONSTRUCTION_SITES` + `updateSealPark` even when a spawn is busy, plus `spawnForce` during leftover `holding`. | **0.15–0.35** if the busy spawn skips the find cascade (planning already done that tick). | Same defence/commander bypass. Do not drop a W47 spawn. |
| **3. W45N7 rhauler body trial (5×8C8M → 2× cap-sized, same CARRY)** | Still the best creep-count lever (Oct 20 / Nov 10, unshipped). 6h: rhauler 6.76 × 0.26 = 1.76 CPU, idle 80%. 1h rhauler still 6.77 (max 8) even in a quiet hour. | **~0.7** if the trial holds, at zero energy cost. | **Standing constraint: do not change live transport bodies unless new data overturns the RCL7 8C8M hauler model.** Today’s data still shows a large, idle 8C8M fleet, which *supports* a trial, but it does not overturn the model by itself. Ship only as a watched trial with a one-constant rollback. Lumpier deliveries, 3 container neighbours, `rhGap` / lead timing. |
| **4. After keep=2 is sticky and src_A is healthy, revisit W47 HMAX / 3rd–4th `w8hauler`** | 6h w8hauler 2.86 × 0.35 = 1.01 CPU, idle 86%, **rp100 15.3** (highest hauler repath). 1h already down to 2.19 / 0.72 CPU. | Maybe **0.3–0.6** later (one overflow body). | **Don’t, until measured.** Nov 10 forbade this while src_A was 2.47 vs 9.60. Re-check src_A / looseE before cutting the valve. Do not cut keep=2. |
| **5. Offset or shrink segment-90 stringify off `Game.time % 10 === 0`** | STATS-tick `trace_cpu` avg 0.78, max 6.19; p95 is the 20-cap problem. | Mostly **p95 cosmetics** (~0.5–0.8 on those ticks), little average. | Observability risk if windows drop. Not a substitute for (1). |
| **6. Tower `repair` only when `hits < hitsMax` (and drop a stale full `towerRep`)** | `w8tower` 0.37 + `tower` 0.20; L125 still repairs without a hits check. Cand is already `hits < capFor(s)` at retarget. | **0.05–0.15?**, still unmeasured. | Low if the check is correct. Measure `tr` ledger vs hits first. Do not drop a tower. |
| **7. Queen sticky fill / fewer new-target walks** | Queen 0.74 CPU, rp100 9.5, idle 74%. | **~0.1** | Small; not first. |

**Do not cut / do not do:**

- W47 `keep=2` or the 40k/500t latch (lock has not triggered; first 40k touch was ~210 t).
- `Memory.defense.reserveE=15000`.
- Max-spec defenders / kites / first-tick spawn (PR 42). Leftover defence CPU after an invader is temporary; do not recycle for CPU.
- Opening a new remote (~+2–3 CPU; p95 already on 20).
- Re-enabling the military path cache unless a new trace clearly overturns that decision (no such data in this window).
- `generatePixel` (bucket is the only reserve for 23–27 peacetime spikes and 40–70 deploy/combat spikes).
- Gutting ops to chase 15.8–16.2 STATS CPU; T3 kite remains the north-star.
- Flipping labs on as a CPU project (it adds CPU).

**Order for a CloudAgent:** implement (1) first (home once-per-room spawn, defence bypass preserved), measure a few hours, then optionally (2) and (5). Treat (3) as a separate, explicit trial under the 8C8M constraint. KO flag flip is an ops decision, independent of (1), but should not land *instead of* (1). Boost is a later deploy, after reactions have actually produced ≥900 KO and a boost lab design exists.

---

## 7. Query windows, files, live ticks

- DB queries: `/workspace/screeps/state/_cpu_lab_survey_2026-11-16/_sql.py` and the `sql_*.txt` dumps next to it. Windows are `now()-1h/3h/6h/12h` from ~16:03 HKT, 2026-11-16.
- Console: `q_flags.json` (84300846), `q_labs.json` (84300855), `q_stores_home.json` / `q_stores_w47.json` (84300858–859), `q_deposits.json` (84300860), `q_ramp_home.json` / `q_ramp_w47.json` (84300862–863), `q_creeps.json` (84300870), `q_sites_w47.json` (84300880), `q_threat.json` (84300884), `q_core_spawn.json` (84300899).
- Prior analyses: `state/_cpu_full_logic_analysis.md`, `state/_softcap_cpu_analysis.md`, `docs/CPU.md`.
- Live code citations: `src/managers/labs.js`, `src/roles/hauler.js` `labRun`, `src/main.js` L21, `src/managers/spawn.js` (`IDLE_EVERY`, `defenseDue`, `setRoleTargets`, `B.defender`, `mineralCapped`), `src/rooms/w47n8/index.js` (`spawnGate`, `mineralSend`, `IDLE_EVERY`), `src/rooms/w47n8/config.js` gates, `src/utils/plan.js` `RCL6_MINERALS` / `RCL7_INDUSTRY`.
- Box pauses: `metrics/box_pauses.jsonl`, 24 since 04:09, last 15:46:44–16:00:33 (820 s). Listener was up at 16:00; this survey did not start a second slot.

**Bottom line for the parent briefing:** peacetime STATS CPU is still 17.3–18.1 average, p95 on or above 20, bucket full. The Nov 10 spawn-throttle recovered W47 only; **home `spawn` is the leftover problem (~2.0 CPU)**. Haulers remain ~4.5 CPU. Home K/O stocks are huge, lab shells and 300k covers are ready, reaction+hauler code is live and dormant — **home KO can start** after a terminal-space hygiene step; **default kite boost cannot**, because `boost.js` was never written. W47 labs are standing but mostly uncovered and not hooked to `labs.run`.
