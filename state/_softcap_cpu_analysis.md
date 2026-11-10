# W47 softCap + colony CPU analysis

**When:** 2026-11-10 16:22 Asia/Hong_Kong (box-local).  
**Live:** commit `5892e31` (deployed 13:37 HKT, tick 84181330). Rooms W46N8 + W47N8 both RCL7. Shard3 tick ≈ 4.42 s.  
**Do not treat this as a deploy brief.** No live code was changed.

---

## Conclusions

**softCap verdict: the 25k/22k design is not banking energy. It is thrashing.**  
W47 storage spent 75% of last-6h *observed* room_stats samples below 22k, and only 6% at or above 25k. In the last 24h it never reached 25k at all until this afternoon, then *cleared 25k twice*, immediately spawned surplus upgraders (4, once 6), and both times the cushion collapsed back through 22k toward the 15k leanBank edge (now ~14.7–15.2k). The one period that actually worked was nUp=2 with storage *rising* 19.6k→22.6k at **20.0 e/t**. The surplus rule then undid it. Last 6h upgrade is **11.59 e/t (38.5% of ideal 30.08)**; last 24h **9.60 e/t (31.9%)**. A steady 2 would have been ~20 e/t (66%) *and* a rising bank.

**CPU verdict: 17–18 / 20 is real, and the Oct idle-throttle win has been lost.**  
room_stats (awake, every ~10 ticks, W46N8 row): last 1h avg **16.62**, 3h **17.33**, 6h **17.37**, 24h **16.89**. 6h p50 16.91, p95 **20.49** (already at the 20 limit), max **75.78** (the 13:37 deploy). Bucket min 9884 in 6h, 10000 in the last hour.  
cpu_prof EMA (only 10 polls today, last 15:38 HKT) reads lower (total **14.94**) but the section split is trustworthy: **spawn 1.00 + w8spawn 0.97**. Oct 20 daily baseline was **0.18 + 0.31**. That is a confirmed **+1.5 CPU** regression on spawn managers alone. Creep count is ~40–41 (Oct 20 review: 34). A new remote (~+2–3 CPU) or a 3rd claimed room (~+5–6) still does **not** fit.

**Primary softCap change (do now):** do *not* raise `LEAN_SOFT` (seal stays at 25k, per Misaki). **Delete / permanently gate the surplus rule that jumps to 4–6 the tick stor≥25k.** Hold **keep=2 until storage is sticky at 40k** (new constant, *separate from seal*). Then allow a **steady 3** only, re-arm to 2 below 30k. Never 4–6 until a much higher cushion (80k+, later). Expected climb ~20 e/t and +8–10 e/t into storage; 2–4 hours 15k→40k if income holds. Then ~28–30 e/t at 3. This is *faster* RCL7 than today's 11.6 e/t average, and it actually builds a cushion.

**Primary CPU changes (do now):** (1) run W47 `spawnRun` **once per room per tick**, plus an idle/wait throttle like home `IDLE_EVERY=4` — save ~0.5–0.7 of the 0.97 w8spawn. (2) home spawn: also throttle while *waiting for energy* (`sw.ne` is only armed on a fully idle pass today, so two RCL7 spawns re-run `run1` ~every tick) — save ~0.4–0.6 of the 1.00 spawn. Combined ~**1.0–1.3 CPU** with no ops change if hostiles still force a full pass.

---

## A. softCap findings

Sources: `room_stats` (storage, progress, cpu — **box-sleep holes, not filled by official history**), `creep_ticks` role=`wupgrader` (nUp — official history backfill, last 6h **98.2%** coverage), `src/rooms/w47n8/index.js` (`LEAN_SOFT=25000`, `LEAN_SOFT_ARM=22000`, surplus at `stor>=LEAN_SOFT` up to 6 if hub live + ctlBattery≥800, recycle keep=2 while `softCap2`, keep=3 in post-hysteresis [22k,25k)). Ledger snaps end 10:30 HKT, so this afternoon's recycle refund is **estimated** from the engine formula `floor(bodyCost * ttlLeft/1500)` with body 10W1C2M = 1150.

### A1. Storage time in band (observed room_stats only)

Window last 6h: ticks 84178670–84183530 (10:22–16:18 HKT), **300 samples** (expected ~486 if continuous every 10 ticks; ~38% of slots missing because of box sleep). Last 24h: 84163870–84183530, **516 samples**.

| Band | 6h samples | 6h share | 24h samples | 24h share |
|---|---:|---:|---:|---:|
| <15k (leanBank re-arm edge) | 78 | 26.0% | 217 | 42.1% |
| <22k (softCap2 energy half ON) | 226 | **75.3%** | 442 | **85.7%** |
| [22k, 25k) (hysteresis hold, base 3 allowed) | 55 | 18.3% | 55 | 10.7% |
| ≥25k (clear, surplus armed) | 19 | **6.3%** | 19 | **3.7%** |

6h stor min **4836** (10:52 HKT, 0 hostiles — leanBank already on, nUp 0–1; not a combat drain), max **25704**. 24h max is the same 25704: **the only ≥25k samples in a full day are this afternoon's two events.**

Simulated energy-softCap (sticky `softE`, same 25k clear / 22k re-arm rules), observed samples only:

1. **CLEAR 1** tick 84181170, **13:25:35 HKT**, stor 25445 (previous sample 23957). Live, not a sleep crossing.  
   **REARM 1** tick 84181370, **13:40:10 HKT**, stor 21567. ~15 minutes above 22k, then through the floor.
2. **CLEAR 2** tick 84182480, **15:01:30 HKT**, stor 25704. Previous awake sample 22554 at 14:42. **Box-sleep crossing** (sleep 14:42–15:00). Official `creep_ticks` show surplus already spawning at **14:45**.  
   **REARM 2** tick 84182780, **15:23:33 HKT**, stor 21752. Previous sample still 25704 at 15:09. **Re-arm also happened during box sleep** (15:09–15:22).

No other 25k clears in the last 24h of observed room_stats. Overnight the bank never got there (hourly maxes typically 15–18k, with several sub-10k dips).

### A2. nUp (live + spawning) — last 6h is the reliable window

`creep_ticks` W47N8 last 6h: ticks 84178642–84183504, distinct 4775 / span 4863 = **98.2%**. Only hole ≥5 ticks: 84183400–84183485 (86 ticks, unpublished/current-chunk lag around 16:08–16:15).  
Last 24h coverage is only **39%** (overnight official-history not fully backfilled). Do not over-claim 24h nUp shares; the 4- and 6-counts below all sit inside the last 6h anyway.

Last 6h nUp distribution (4772 ticks with a W47 row):

| nUp | ticks | share |
|---|---:|---:|
| 0 | 403 | 8.4% (morning leanBank <15k, spawn rule can hold 0 if downgrade is safe) |
| 1 | 504 | 10.6% |
| 2 | 2204 | 46.2% |
| 3 | 319 | 6.7% (hysteresis-off band, base 3) |
| 4 | 1243 | **26.0%** |
| 5 | 2 | ~0% |
| 6 | 97 | **2.0%** |
| **avg 2.40, max 6** | | |

This is not a brief overshoot. **A quarter of the last 6 hours was spent at 4 upgraders.**

Event 1 (clear at 13:25): nUp already 3 from ~13:11 (hysteresis-off in [22k,25k) allows base 3 — `w8upgrader84180984` / `84181054` spawned then). At the exact clear tick 84181170, **both W47 spawns started a surplus body** (`84181168` and `84181169`, same-tick). nUp=4 from 84181170 through ~14:10 (**~480 ticks, including ~400 ticks AFTER the 13:40 re-arm**). Recycle of the older 3rd/4th only finished 14:13 / 14:21 at spawn (33,29). Recycle lag, not just a 20-tick walk.

Event 2 (sleep clear ~14:45): nUp=2 and *working* 14:30–14:42 (storage climbing). Surplus pair `84182263`/`84182264` started **14:45** during box sleep, nUp=4 until 15:10. Then handover spawned `84182607`/`84182608` and nUp hit **6 for 97 ticks** (84182610–84182706, 15:10–15:17). The 13:25 pair then died of old age (~15:17–15:18, full 1538-tick lives). The 14:45 pair was recycled 15:33 / 15:38 at 33,31. nUp back to 2 by 15:40. Those 15:10 bodies are the keep-2 still alive at 16:16.

Reliable 6h spawn/recycle of surplus (ignore 24h “short” lives — those are trail gaps, not recycles):

| Creep | Born (HKT) | Fate | Seen ticks | Est. net spawn cost (1150 − refund) |
|---|---|---|---:|---:|
| 84179544 | 11:26 | aborted/recycled at spawn after 62t | 62 | ~18 |
| 84180984 | 13:11 (base-3 in band) | recycled 14:13 @33,29 | 841 | ~615 |
| 84181054 | 13:17 | recycled 14:21 @33,29 | 884 | ~648 |
| 84182263 | 14:45 surplus | recycled 15:33 @33,31 | 658 | ~475 |
| 84182264 | 14:45 surplus | recycled 15:38 @33,31 | 721 | ~523 |
| **Net spawn waste** | | | | **~2.3k energy, ≈0.47 e/t over 6h** |

The energy lost to spawn-recycle is small. The damage is the *bank* and the *upgrade blackout* while extras walk to Spawn2.

### A3. Upgrade e/t vs ideal (progress is valid across sleep gaps)

Ideal from `model_params` / `model_w8` at 15:25 HKT: **w8.upgrade 30.08 e/t** (links era, net ~32.4). Home ideal 26.00.

| Window | W47 ticks | W47 e/t | vs 30.08 | W46 e/t | vs 26.00 |
|---|---|---:|---:|---:|---:|
| 1h (15:23–16:18) | 750 | 14.01 | 46.6% | 9.60 | 36.9% |
| 2h | 1620 | 15.94 | 53.0% | 15.23 | 58.6% |
| 3h | 2440 | 12.17 | 40.5% | 16.88 | 64.9% |
| **6h (10:22–16:18)** | 4860 | **11.59** | **38.5%** | 19.17 | 73.7% |
| **24h** | 19660 | **9.60** | **31.9%** | 20.38 | 78.4% |

Awake-segment e/t on W47 (gap>50 ticks starts a new segment), last 6h, tells the story:

- 14:18–14:42, nUp=2, stor **19618→22554**, upgrade **20.0 e/t**. This is the design *working*: two 10W stands, ~66% of ideal, bank **+9.5 e/t**.
- 15:01–15:09, nUp=4, stor stuck at 25704, upgrade **22.7 e/t**. Four upgraders bought only **+2.7 e/t** over the steady-2 rate. `creep_cpu` codes last 6h (awake only, 18% tick coverage — do not treat as full-day): wupgrader **waiting_feed 40.7%**, working 45.8%, moving 10.6%, spawning 2.9%. Feed cannot support WORK40–60. This is the failure the 11:4x comments already predicted; the surplus rule still does it.
- 13:03–14:10 (includes clear 1 + recycle lag), stor 21447→25445→17988, upgrade **5.4 e/t**. Overshoot-then-recycle is *worse* than holding 2.
- 15:23–15:39 (re-arm + trim), stor 21752→20046, **9.09 e/t**.
- Morning leanBank (nUp 0–1, stor 4.8k→20k): 4.4–4.9 e/t. Banking happened only because upgrade was nearly off; then the 25k latch wasted it.

A steady 3, if actually fed, should be close to ideal (~28–30 e/t) and would hold the bank roughly flat. We did not get a clean 3-only window long enough to measure; the [22k,25k) nUp=3 stretch immediately became a 4.

### A4. Did the bank rise, or yo-yo?

It yo-yoed around 22–25k and then *fell through* to the 15k leanBank edge.

- After clear 1: 25445 (13:25) → 21567 (13:40) → 16202 (13:55). **−9.2k in ~30 minutes.**
- After clear 2: 25704 (15:01) → 21752 (15:23, during sleep) → 20046 (15:39) → 14696 (16:08). **−11k in ~1 hour.** Latest samples ~14.2–15.2k.
- Conservative counterfactual: the 14:18–14:42 nUp=2 segment banked **+9.5 e/t**. From 22554 at 14:42, 1360 ticks to 16:18 would have been ~**35k**, not 15k. First event similarly turned a 25.4k peak into 16k instead of a 30k+ cushion.
- Extra upgraders after a brief 25k clear burned almost no *net spawn* (~2.3k) but dumped **~10k storage per event** into the controller / waiting_feed / recycle walk, then left upgrade at 5–9 e/t during the hangover.

### A5. Coupling with home 15k floor

Home `room_stats` last 6h (304 samples): avg 15195, min **12063**, **35.5% of samples <15k**, only 19% ≥16k (the `allowExtra` / upBank recover line). Last 24h is the same picture (34.6% <15k).

At both W47 clears, home was already thin:

- 13:25 W47 25445, home **15042** (had been 14842 a few samples earlier).
- 15:01 W47 25704, home **14488** and stayed under 15k. Home 1h upgrade only **9.60 e/t (36.9% of ideal)** — upBank keep-1 behaviour.

There is no energy pipe from W47 storage to home (mineral `terminal.send` is dormant). The coupling is colony-level: **home was already under its 15k floor, with no cushion for defence, while W47 spent a 25k “bank” on 4–6 upgraders the feed could not support.** A real W47 cushion would at least give the colony one room that can absorb a defender wave.

### A6. Recommendation

**One primary change:** keep `LEAN_SOFT=25000` for seal / soft-gate (Misaki already rejected a 35k sealMinE). Add a *separate* upgrader latch:

1. **Delete or hard-gate the surplus term** in `spawnRun` (`stor>=LEAN_SOFT` + `(stor-2000)/600` up to `upgCeil=6`). That jump to 4–6 the tick of a 25k clear is the bug. The 17:4x comments already documented 25.1k→22.7k in ~30 minutes; today's two events reproduced it (25.4k→16k, 25.7k→14.7k).
2. **Hold keep=2 until storage stays ≥40k for 500 ticks** (~37 min at 4.42 s/tick). Then allow a **steady 3** only. Re-arm to 2 below 30k (wider than 22/25, so a 3 does not immediately yo-yo).
3. Leave `threatSoft` ≤2 as it is.
4. Optional later, not now: allow 4 only if stor≥80k **and** ctlBattery stays ≥FEED_MIN for a full 500-tick window.

**Expected:**

- Climb phase: ~**20 e/t** upgrade (66% of 30.08), measured this afternoon with nUp=2; bank **+8–10 e/t** when src_A is not soft. 15k→40k in roughly 2–4 hours of healthy income (2500–3500 ticks).
- After 40k sticky, steady 3: ~28–30 e/t if hub→ctl is live, bank roughly flat. That is *better* GCL than today's 11.6 / 9.6 e/t averages.
- Spawn/recycle: ~2.3k net waste per similar 6h afternoon goes away; more importantly the 5.4 e/t recycle blackouts go away.
- Risk to 15k/25k cushions: **down**, not up. The current rule is what keeps piercing them. Home 15k policy is unchanged.
- CPU: dropping the 26% of ticks at nUp=4 (and the 6-burst) is ~0.1–0.3 CPU average, small but free.

**Alternatives (not preferred):**

- Only “forbid surplus, allow 3 immediately at 25k, keep 22k re-arm.” Better than today, but 3 at the exact 25k edge can still flatten or slowly eat a thin bank, and today's nUp=3 already appeared *before* the first clear. The 40k sticky target is what actually *banks*.
- Drop softCap and run a steady 2 or 3 forever. Steady 2 works (20 e/t) but never uses the 3rd stand once a cushion exists. Steady 3 always will spend down toward a lower equilibrium and fight the 15k leanBank edge. Worse cushion, not clearly faster than “2 until 40k, then 3.”
- Raising `LEAN_SOFT` itself to 40k would also move seal. Do not do that.

**Do now** (code change, not deployed in this pass). **Measure first** after deploy: W47 stor time-in-band, nUp shares, 2h e/t vs 20 / 30, recycle count, src_A harvest (already soft at 2.0 e/t vs ideal 9.6 in the 15:25 model — keep the overflow hauler valve while nUp=2, or A will stay soft).

---

## B. CPU findings

Sources: `room_stats.cpu` / `bucket` (awake STATS ticks, use this for headroom), `cpu_prof` EMA section split (sparse: **10 polls today**, 10:37–15:38 HKT; none after the 15:40–16:01 and 16:09–16:15 sleeps), `creep_cpu` (segment 90, **not** in official history; last 6h distinct ticks 916 / span 5066 = **18% coverage** — use per-creep ms and live counts, not span-averaged totals), `docs/CPU.md` Oct 20 baseline, `src/main.js` + `src/managers/spawn.js` + `src/rooms/w47n8/index.js`.

### B1. Limit, bucket, averages

Documented and unchanged: `Game.cpu.limit=20`, `tickLimit=500`.  

room_stats, W46N8 row only (colony cpu is duplicated on both rooms):

| Window | samples | t range (HKT) | avg | p50 | p95 | max | bucket min |
|---|---:|---|---:|---:|---:|---:|---:|
| 1h | 37 | 15:23–16:18 | **16.62** | 16.20 | 19.22 | 20.18 | 10000 |
| 3h | 150 | 13:19–16:18 | **17.33** | 16.82 | 20.15 | **75.78** | 9987 |
| 6h | 300 | 10:22–16:18 | **17.37** | 16.91 | **20.49** | 75.78 | **9884** |
| 24h | 516 | 11-09 16:22–11-10 16:18 | **16.89** | 16.67 | 20.21 | 75.78 | 9884 |

The 75.78 spike is the 13:37 `5892e31` deploy (global reset). Removing that one sample only drops the 3h mean to ~16.9 — the 17-ish average is not a spike artifact. p95 already sits on the 20 cap, so there is **no p95 headroom**.

cpu_prof `total` today averages **14.94** (range 13.17–16.66). It systematically under-reads room_stats (~2.5 CPU). Use it for *where* CPU goes (EMA of `Memory.stats.prof`), not for “are we at 15 or 17.” Polls are also missing every box sleep and the last ~40 minutes.

### B2. Section breakdown vs Oct 20

`err.wrap` keys on the first word, so `spawn Spawn1` + `spawn Spawn2` sum into `spawn`, and both W47 spawns already share `w8spawn`.

| Section | Oct 20 daily cpu_prof | Oct 20 01:4x snapshot in docs/CPU.md | Today (10 polls) | Δ vs Oct 20 daily |
|---|---:|---:|---:|---:|
| total (EMA) | 11.42 | 10.5 | **14.94** | +3.5 |
| creep | 8.96 | 8.63 (34 creeps, 0.254 each) | **10.38** | +1.4 |
| **spawn** | **0.18** | **0.15** (idle throttle verified) | **1.00** | **+0.82** |
| **w8spawn** | **0.31** | **0.05–0.11** (a low point; even the 01:00–03:00 polls avg 0.37) | **0.97** | **+0.66** |
| remote | 0.33 | 0.34 | 0.42 | +0.09 |
| mem | 0.39 | 0.37 | 0.32 | −0.07 (improved) |
| w8tower | 0.15 | — | 0.29 | +0.14 |
| trace | 0.14 | 0.13 | 0.16 | +0.02 |
| everything else | — | — | ≤0.15 each (stats 0.13, alerts 0.15, report 0.03, labs 0.10, roads 0.03) | small |

The spawn+w8spawn regression is confirmed in *both* the optimistic 01:4x snapshot and the Oct 20 daily mean. It jumped on **Nov 1** (spawn 0.68, w8spawn 0.93) and has stayed there (last 7d: 1.00 / 0.92). That lines up with RCL7 second spawns + the softCap/leanBank cascade landing in `w47n8/index.js`.

**Why w8spawn is ~1 CPU (code, current tree):** `W8.spawnRun` has **no `IDLE_EVERY` throttle**. Every W47 spawn, every tick, even when `spawn.spawning`, does `mine()` over `Game.creeps`, `FIND_MY_CONSTRUCTION_SITES`, and `updateSealPark`. Every *idle* spawn then walks the full want cascade: `looseE` (2 finds), `wallsLow`, `dayofMiss` (`FIND_MY_STRUCTURES`), leanBank/softCap/surplus, mineral finds, etc. RCL7 has **two** W47 spawns, so the heavy path runs twice. Home `fbe8a00` throttle was never ported here. The Oct 20 “already ~0.1, drop from the list” note is stale.

**Why home `spawn` is ~1 CPU again:** `IDLE_EVERY=4` still exists, but `sw.ne` is armed only when `run1` returns without wanting anything (`!waited`). If some role is wanted and energy is short, `waited=true` and **both RCL7 home spawns re-run `run1` (~2.4 ms in the Oct comment) every tick**. The 15k floor / replacement stream keeps the room in that “want but wait” state a lot. Two spawns sum into one `spawn` section.

### B3. Roles and repaths (post-720380f / post-5892e31)

`creep_cpu` is awake-only (18% of last 6h ticks). Per-creep ms is usable; do not divide role sums by the sleep-inclusive span.

Last 6h per-creep CPU (ms/tick) and typical live counts from room_stats (16:21 census = **41 creeps**):

| Role | per-creep | typical n (latest) | ~role CPU if those n are live | rp100 (post-5892e31) |
|---|---:|---:|---:|---:|
| rhauler | 0.245 | 6 | ~1.47 | 4.50 |
| wrhauler | 0.280 | 5 | ~1.40 | 3.35 |
| whauler | 0.285 | 4 | ~1.14 | 3.37 |
| queen | 0.406 | 2 | ~0.81 | **10.98** |
| wupgrader | 0.231 | 2 (was 4–6) | 0.46 (0.92–1.4 when overshot) | 0 |
| wfiller | 0.261 | 2 | ~0.52 | 3.46 |
| upgrader (home) | 0.285 | 1–2 | ~0.3–0.6 | 0.45 |
| wbuilder | 0.376 | 2 | ~0.75 | 0 |

Haulers still dominate, same as Oct, but **counts grew**: Oct 20 W47 wrhauler 1.10 / whauler 0.70 vs ~1.40 / 1.14 now. Model at 15:25: `w8.carry_remote` live **90 vs need 48.6**, `w8.carry_local` **40 vs need 9**. That is leftover overflow valve + softCap-era pile logic, and it is extra CPU.

Queen rp100 is still ~11–13 (Oct 20 was 14.8). **Do not read this as “720380f failed.”** The pre-fix 381-repath storm was a different bug (unreachable extension). Post-720380f `rp_why`: **540 `c` (path-cache hit in `move.js`, cheap, still counted as a repath)**, 169 `n` (new target), 87 `s` (stuck2), 18 `x` (stuck8). Real PathFinder work is much smaller than rp100 implies. 720380f did its job; leftover queen repath is a minor lever (~0.1), not a first cut.

wupgrader shows 485 intent fails post-5892e31 (upgrade/recycle while waiting_feed or walking). Not a repath storm.

### B4. Creep count

Latest census 16:21 HKT, tick 84183570, **41 creeps** (miner 2, queen 2, hauler 1, rminer 2, rhauler 6, w8guard 1, w8miner 2, defender 2, reserve7 1, reserver 2, upgrader 2, w8filler 2, w8hauler 4, w8rminer 2, w8builder 2, w8rhauler 5, w8defender 1, w8upgrader 2). Hourly averages today 38–42, peaks 45 around the 13:00 and 15:00 surplus waves. Oct 20 review was **34**. At ~0.25–0.28 per creep, **+6–11 creeps ≈ +1.5–3.0 CPU**, which matches the creep-section rise (8.96→10.38) plus some of the room_stats 17 vs EMA 15 gap if counts spiked between polls.

### B5. Top safe CPU cuts (no ops regression)

1. **W47 spawn: one decision per room per tick + idle/wait throttle.** Code path: `src/rooms/w47n8/index.js` `spawnRun`, called twice from `main.js` with no `IDLE_EVERY`. Evidence: w8spawn 0.31→0.97, two full find cascades per tick. Expected **−0.5–0.7 CPU**. Hostiles / commander `consumeSpawn` must still force a full pass (same contract as home). **Do now.**

2. **Home spawn: wait-throttle.** Code path: `src/managers/spawn.js` `run`, `sw.ne` only set when `!waited`. Evidence: spawn 0.18→1.00 after RCL7 two-spawn + frequent energy-wait. Expected **−0.4–0.6 CPU**. Worst case a replacement starts 3 ticks later, already accepted for idle. **Do now.**

3. **Kill W47 surplus upgraders (the softCap change above).** Evidence: 26% of last 6h at nUp=4, 97 ticks at 6, waiting_feed 40.7%. Expected **−0.1–0.3 CPU** average, plus the energy/upgrade win. **Do now** (same deploy is fine).

4. **W45N7 rhauler body consolidation** (Oct 20 proposal, still unshipped): fewer, cap-sized haulers, same CARRY. Evidence: 6 rhaulers × 0.245 ≈ 1.47 CPU; Oct estimate **−0.7**. Risk: lumpier deliveries, container neighbour slots, rhGap. **Trial, measure first** (rollback = one constant).

5. **Do not cut W47 local/remote haulers until the new nUp policy is stable.** Model says they are fat (40 vs 9 local CARRY), but with keep=2 the 11-02 comment still applies: ctl saturates, source piles grow, **src_A already harvests only 2.0 e/t vs ideal 9.6**. The 3rd/4th whauler is an overflow valve into storage. Measure looseE and src_A after the softCap change; then maybe drop HMAX.

Not first cuts: queen sticky fill (~0.1, and rp100 is inflated by cache hits); w8tower 0.29 vs 0.15 (maybe 3rd tower — measure first); mem/report/visuals (visuals are not even in `main.js`; mem already better than Oct); `generatePixel` (bucket is the only reserve for 28–75 spikes).

### B6. Another remote?

**No.** Prior conclusion stands, and the fresh numbers are tighter. room_stats 6h avg 17.37 with p95 20.49 leaves ~2.6 CPU average and **zero high-percentile margin**. A 4th remote at +2–3 CPU would sit at ~19.5–20.5 average and blow the cap on ordinary p95 ticks, before any Invader. A 3rd claimed room at +5–6 is impossible on a 20 CPU limit. Even after the spawn cuts above (~−1.0–1.3) and a rhauler trial (~−0.7), headroom is still a maybe for *one* cheap remote, and only once those cuts are measured in room_stats, not assumed. Do not open a new remote on this analysis.

---

## Data holes (do not over-claim)

- **room_stats / creep_cpu / cpu_prof do not exist during box sleep** and are not backfilled from official history. Last 6h room_stats is ~300/486 expected 10-tick slots. Notable sleeps: 14:42–15:00, 15:09–15:22, 15:40–16:01, 16:09–16:15 (and many ~40–50 min holes overnight). Clear 2 and re-arm 2 both happened in sleep; nUp for those spans comes from official history in `creep_ticks`.
- **Official history** last 6h W47N8 is 98.2% (86-tick hole 16:08–16:15). Last 24h `creep_ticks` is only 39% — overnight nUp/lifetimes are truncated and must not be used as recycle evidence.
- **cpu_prof**: 10 samples today, last **15:38 HKT**, EMA under-reads room_stats by ~2.5. Section ratios are still the right tool for spawn vs creep.
- **Ledger** last snap 10:30 HKT (`rf:` hook live since `b9c984e` 08:19). Afternoon recycle refunds are estimated from TTL, not from `Memory.ledger`.
- **wupgrader waiting_feed 40.7%** is from awake `creep_cpu` only (18% of ticks). Directionally consistent with the 22.7 vs 20 e/t overshoot, but not a full-6h occupancy.
- src_A 2.0 e/t (15:25 model) is a real income problem under nUp=2; don't claim the +9.5 e/t bank rate holds every hour.

---

## Ranked actions

| # | Action | When | Why |
|---|---|---|---|
| 1 | Gate/delete W47 surplus (max 6); hold keep=2 until stor sticky ≥40k, then steady 3, re-arm 30k. Do not raise `LEAN_SOFT`. | **Do now** | Two 25k clears today both crashed the bank; 4 upgraders added only +2.7 e/t then a 5.4 e/t recycle blackout. Steady 2 already measures 20 e/t and +9.5 e/t banking. |
| 2 | W47 `spawnRun` once per room + idle/wait throttle (`IDLE_EVERY=4`, hostiles/commander bypass). | **Do now** | w8spawn 0.31→0.97; two unthrottled find cascades every tick. Save ~0.5–0.7. |
| 3 | Home `spawn.js`: arm `sw.ne` also when waiting for energy, not only on full idle. | **Do now** | spawn 0.18→1.00; `waited` disables the Oct throttle. Save ~0.4–0.6. |
| 4 | After (1)–(3) deploy: measure 2h W47 e/t, stor bands, nUp, src_A, room_stats cpu 1h/3h, `Memory.stats.prof.spawn` / `w8spawn`. | **Measure first** | Confirm 20 e/t + rising bank, and that spawn EMAs actually fall. |
| 5 | W45N7 rhauler consolidation trial (one constant, patrol-watched). | **Measure first / trial** | Still the best creep-count lever (~−0.7). Don't ship blind. |
| 6 | Cut W47 haulers / raise a 4th upgrader / open another remote / generate pixels / raise seal 25k. | **Don't** | Haulers are the overflow valve while keep=2 (src_A already soft). p95 is already 20.5. Bucket is the spike reserve. Seal 25k was a Misaki decision. |
