# 12-hour strategic review findings — 2026-11-15 20:2x Asia/Hong_Kong

Docs-only data collection for the parent to write the review. No src change, no deploy, no commit, deploy.lock not touched, labs/market/war not enabled. Live console used proven patrol/review expressions (17 queries; first `def` attempt had a missing brace and was not sent; retry succeeded). `tools/q.py` console stream only — no Memory._q / user/memory fallback. `model_w8.py` wrote `Memory.ops.w8model` as a normal tool side-effect (two tags at t84284692).

Canonical official window: **tick 84274500 → 84284720**. Prefer these numbers over live.json (slightly earlier) or later live queries.

## Window and coverage

- Official DB window: **t84274500 → 84284720** (10220 ticks), wall **2026-11-15 08:25:20.329004+08 → 2026-11-15 20:24:47.228391+08** (Asia/Hong_Kong), **43166.899387 s ≈ 11.9908 h**, measured **tick_s = 4.223767063307241**.
- Continuity with last review (2026-11-15 08:2x, commit f94c06f, docs only): last review ended at **t84274500**. First samples of this window match that end (home progress 6,729,834 / W47 3,579,390; W47 stor 34,965).
- Shard is faster than the morning window (morning tick_s **4.443**, 9850 t ≈ 12.16 h). Same 12h wall therefore covers more ticks.
- room_stats is a **10-tick** series, **494 samples/room**. Expected 10-tick slots = 1023. Coverage **494/1023 = 48.29%**. Gaps are shared box/listener freezes. Largest: **399 ticks** missing 84275550→84275950 (09:39:04→10:07:07). Also 329, 319 (twice), 309, 289, 269 (twice), 259 (twice), … Storage stretch math **breaks a stretch when the sample gap is >20 ticks** (more than one missed 10-tick slot), so a freeze will split a stretch even if storage probably stayed put.
- Live queries: **t84284749–84284775** (~20:27:3x–20:28:41 Asia/Hong_Kong). metrics/live.json copied at start was stats.t **84284690** / updated 2026-11-15 20:22:57 / storage home 17665 W47 24904. Use the live query tip below as the board, not that slightly earlier file.
- Listener peacetime single-slot **5:5:1:1**, `listener_yield_rooms` absent. rot at 20:23:22: `{"i":1,"room":"W47N8","left":292.3}`. No war_* processes.

## Repo / peacetime checks

- HEAD at collection: `14aa37f` routine state 2026-11-15 19:24. Commits since morning review `f94c06f` are routine state only (plus this would-be docs commit, not made here).
- `git status`: **src/ and docs/ and dist/ clean**. Dirty (routine, not this work): `state/_halfhour_backfill_*`, `state/history_backfill.json` / `.prev.json`. Untracked leftovers: `scripts/_patrol_*`, `tools/war_cmd_loop.py`, `tools/war_listen.py`, `tools/war_pulse.py` (not running). Also untracked half-hour dirs under state/.
- **No deploy.lock** anywhere relevant.
- Last game-code change: **ffdf767** 2026-11-15 00:27:15 +08, dist/main.js mtime 00:27:15. Deployed **@84268045 / 00:27 HKT** (“core fight: no readyTimeout wait-out; WAIT+core re-arms”). Already live before the morning review; **no new deploy this window**.
- room_stats commits this window: **only `ffdf767`** (494/494 W46N8 rows). deploys table latest remains 2026-11-15 00:27:27+08 tick 84268045 ffdf767. Memory.stats.commit was **null** in live queries; trust room_stats + deploys: **LIVE ffdf767**.
- `pgrep war_` = none. Memory.cmd unchanged stale object (see live tip).

## Live tip (t84284749–84284775, ~20:27–20:28 Asia/Hong_Kong)

### Home W46N8 (upgFeed / storage / controller)

- t84284749: stor **17025**, progress **6936713**, ea 5270/5600, bucket **10000**, cpu used **17.31**, creeps **40**, safeModeAvailable **6**, ticksToDowngrade **150000**. (err query a few ticks later had bucket **9985**; DB window min was 9994.)
- upgFeed (Memory t84284750): **why=ok**, **nUp=2**, tUp=2, **work=28**, hungry=0, **upExtra=0**, upExtraSince=0, upBank=0, surplus **+1665**, floor **15000**, allowExtra **20000**, storE **16665**, ctl 1302, ctlEma 790, ctlLinkE 10, hubLinkE 0, srcLinkE 100, boundHint=**energy**, warMode=0, pausedNet=0, idealAdj=26, rem=`W45N8:SAFE,W45N7:SAFE` (W47N7 omitted from this string; Memory.stats.remote has all three SAFE).
- During the query burst home stor oscillated **17025 → 16665 → 16715 → 16765**. Comfortably above the 15k floor, well under the 20k/300t gate.
- Construction sites: **0** both rooms (sites ns=0 at t84284757). room_stats sites were 0 for every sample this window.

### W47N8 (w8day / soft / extra) — notable change vs 19:24 patrol

- t84284749: stor **25004**, progress **3773883**, eaW 5600/5600, ttdW 150000, smaW 6.
- w8extra t84284752 / w8day Memory t84284740 (storE **24504**): **phase=ready**, **why=done**, **keep=2**, **siteRem=0**, **leanBank=0**, **bankLeft=0**, **softCap2=0**, **threatSoft=0**, **bankWhy=ready**, softE=0, **softBand=1**, **softLeft=496**, feedOk=1, **upArm=40000**, **upLatched=0**, **upStickyT=500**, **upRearm=30000**, sealMinE=25000, **sealPark=1**, sealRaise=0, **contMinPct=54**, **roadCrit=0**, hubLink=1, hubLinkE=800, hubReady=1, hubPrime=1, ctlBat=2385, **upgCeil=2**, eAvail=eCap=5600, looseE=642, builders=1, upgraders=2, need=7161297, warMode=0.
- Soft-cap reading: storage is **in the [22k, 25k) hysteresis band** (24504–25004), softLeft=496, softBand=1, softCap2 **OFF**. This is **not** the 19:24 leftover state. Last patrol had softCap2=1 / threatSoft=1 from the 18:28 W47N8 hostile sample (w8threat=84283072). WINDOW=1500 expires at **84284572**, which is before these queries — leftover cleared on its own. Memory.ops.w8threat / w8inv still stamp **84283072** (stale residue). upgCeil stays 2 because designed keep=2, not because of threatSoft.
- sealPark remains 1 (strict ≥25k; stor is just under). 40k latch **not** armed (upLatched=0, stor ~25k, 0 samples ≥40k this window).
- Tip is **not** an open ≥25k / ≥30k / ≥40k climb (window-end stor 24904 at t84284720; live 24504–25004).

### Roles / upgraders / defence / reservers

- roles t84284754 (40 creeps): rminer3 reserver2 rhauler7 miner3 queen2 **upgrader2** hauler1 w8rminer2 w8rhauler7 w8miner3 **w8upgrader2** w8hauler3 w8filler2 w8builder1. **No w8defender, w8guard, rdef, reserve7, defender.** (live.json at 20:22 still had w8defender=1; they are gone by 20:27.)
- Home ups: `upgrader84283854` (31,30) ttl 650 e22 **w=14**; `upgrader84283993` (29,30) ttl 789 e8 **w=14**.
- W47 ups: `w8upgrader84283326` (14,27) ttl **110** e40 **w=10** st=2 (handoff imminent); `w8upgrader84283531` (12,25) ttl 315 e30 **w=10** st=0.
- def retry t84284769: **n=0**, defs={}. North-exit leftover guards from 18:28 have expired.
- resv t84284761: r7 `{on:true, endTime:84287487, by:"Misaki"}` (~2718 ticks / ~3.2 h from then; matches W47N7 res 2732). Creeps listed: only the two reservers (W45N7 6,39 ttl 129; W45N8 7,37 ttl 523). **No reserve7.** Reservation still ~2732, so not an immediate reserve emergency; flag the missing dedicated reserve7.

### Remotes (vis / res / cores / host)

- rem t84284755, all three vis=true, cores=0, host=0:
  - W45N8 res **1934** (slightly under RES_SPAWN=2000, but reserver seated 7,37 — designed wait, not formal (c))
  - W45N7 res **2244**, reserver seated 6,39
  - W47N7 res **2732**, cores 0, no seated reserve7 (see above)
- remth / Memory.stats.remote: all **SAFE**; W45N7 and W47N7 why=`killed` (past cores). A 19:30 W47N7 core was in DEFEND at 19:40; by this tip the room is SAFE again (exact clear tick not in `incidents` — see Incidents).

### labs / minerals / terminals / walls

- labsN t84284758: **hLab=6, hFac=1, wLab=6, wFac=1, hTerm=1, wTerm=1**.
- lab2 t84284759: **mode=null**, why=ready, **propose=1**, **actOk=1**, **actGaps=""**, ready=1, homeStor=16715. w8minWhy=**miner**, w8minGaps=miner, flipGaps=`already`. w9on=false, w9phase=fallback, w9rec=true, w9note=`ABORT Misaki: withdraw recycle end wartime`.
- **Labs still OFF** (mode=null, not enabled). **actOk flipped to 1** (homeStor above the usual 15k actOk line; morning/earlier often actGaps=homeStor). This is a condition flag, not a turn-on. **No re-ask.**
- min2 t84284760:
  - home storage: E 16765, **O 17324**, K 0
  - home terminal: E 0, **O 126976**, **K 172792** (termO unchanged vs morning; termK same as morning 172792)
  - W47 storage: E 25004, O 0, K 64
  - W47 terminal: E 1096, O 0, **K 33708** (up from morning ~20k-class; 19:24 patrol already had K 33708)
- walls t84284764 (cheap mins): W46N8 41 walls / 20 ramparts, min wall **300001** at 27,7, min rampart **300221** at 34,20. W47N8 11 walls / 10 ramparts, min wall **553141** at 11,3, min rampart **300001** at 35,30 (factory). All ≥300k. Healthy.

### cmd / errors / CPU live

- cmd t84284756: **on=1, at=84224348, by=cmd, c={}, s={}, v=1**, keys=["on","c","at","by","s","v"]. Same stale command object as prior reviews; not touched.
- err: lastErrorTick **83976900** (old, before this window). nErr omitted (falsy). live.json nerr=10 is a long-lived counter, not a new tip error.

## DB room_stats — per room (t84274500–84284720, n=494)

RCL8 cap = **10,935,000**. tick_s **4.223767063307241**.

### W46N8 (home)

- Progress **6,729,834 → 6,935,901** (first/last), **delta +206,067**, **e/t = 20.163111545988258**, **63.42844993141289%** of cap, remaining **3,999,099**. ETA to RCL8 at this window pace: **9.69596 days** (206067/10220 e/t × tick_s 4.223767 / 86400). Morning was 18.67 e/t / ~11.6 d.
- Storage **avg 15840.80566802**, **min 9073** at tick **84278070 / 2026-11-15 12:36:37.147129+08** (single sample), **max 20459** at tick **84283060 / 2026-11-15 18:28:00.552828+08** (single sample).
- Share of samples: **<15k 131/494 = 26.51821862348178%**; **≥20k 5/494 = 1.012145748987854%**; **≥25k 0**; **≥30k 0**; **≥40k 0**.
- Longest contiguous under-15k (gap break >20): **711 ticks**, 72 samples, **84277870–84278580 / 12:22:28.936197–13:12:51.324459**, stor **9073–14777**. This is the home formal-alert dip after the 11:24 Invader + 12:00 W45N7 core bills. Next under-15k stretches are short (101, 91, 41, …). Tip is **not** under 15k (open stretch: none).
- Longest contiguous stor≥20000 (gap break >20): **only 41 ticks**, 5 samples, **84283020–84283060 / 18:25:10.743311–18:28:00.552828**, stor **20059–20459**. **20k/300t 3rd-upgrader gate did not arm.** This is the first ≥20k sample cluster in many reviews (morning had **zero** ≥20k, max 18946). The flicker coincides with the 18:28 W47N8 hostile glimpse / spawn-refill; storage then fell (19:24 patrol: home 20459→14859). Live tip ~16.7–17.0k, upExtra still 0.

### W47N8

- Progress **3,579,390 → 3,773,303**, **delta +193,913**, **e/t = 18.973874755381605**, **34.506657521719255%** of cap, remaining **7,161,697**. Window-pace ETA **18.45211 days**. Morning was 19.20 e/t / ~19.7 d. Slightly slower pace, but a faster shard and a larger delta in ticks still improve the clock ETA.
- Storage **avg 28728.11943320**, **min 22082** at ticks **84275510–84275520 / 09:36:14.716460–09:36:56.762355** (during the 09:30 W47N7 core), **max 39332** at tick **84282960 / 2026-11-15 18:20:52.890823+08** (single sample).
- Share of samples: **<15k 0/494 = 0%**; **≥20k 494/494 = 100%**; **≥25k 429/494 = 86.84210526315789%**; **≥30k 158/494 = 31.98380566801619%**; **≥40k 0**.
- Never below the 22k ARM this window (min 22082, just under 22k for two samples at 09:36; then back up). 0% <15k throughout.
- Longest stor≥25000 (gap>20): **841 ticks**, 85 samples, **84277870–84278710 / 12:22:28–13:22:05**, stor 25626–32486. **Not open at tip.**
- Longest stor≥30000 (gap>20): **231 ticks**, 24 samples, **84282960–84283190 / 18:20:52–18:37:08**, stor **33532–39332**. This is the 18:20 peak. **Not 500 t, and never reached 40k. Not open at tip.**
- Other notable ≥30k climbs (all closed): 171 t at 08:34–08:46 max **38466**; 151 t at 19:18–19:29 max 32058; 121 t at 12:45–12:54 max 32486; 111 t at 17:32–17:40 max **35916**; 101 t at 18:02–18:10 max 37323; and an **opening continuation** 81 t at 08:25:20–08:30:58, stor 34965–36878 (the morning “closest yet ~35k” climb, still on at window start).
- Longest stor≥40000: **none**. **40k/500t latch could not have armed.** Closest yet is now **39332 @ 18:20:52** (668 below 40k), beating morning’s live ~35385 / official end-sample 34965 and the same-morning 08:46 peak 38466.
- Morning max note (flag, not a conflict): official morning-window room_stats max is **34965 at t84274500** (this window’s first sample). The morning writeup’s **35385** was a **live tip shortly after that sample** (08:28 patrol: later 35385–36878 @84274510–84274540). Use 34965 as the official morning-window last sample; 35385 as the live figure they published.
- Sites: **0 for the entire window** both rooms (n_zero=494, n_nonzero=0, sites_max=0).

## Hourly (Asia/Hong_Kong, room_stats)

hour | W46N8 progress span / stor avg (min–max) / n | W47N8 progress span / stor avg (min–max)
---|---|---
15 08:00 | 6729834–6737820 +7986 / 16826 (15692–18992) n=27 | 3579390–3584790 +5400 / 36842 (34965–**38466**) n=27
15 09:00 | 6743482–6752194 +8712 / 15970 (14700–17632) n=30 | 3588950–3598750 +9800 / 27581 (**22082**–32103) n=30
15 10:00 | 6762976–6774490 +11514 / 16280 (14094–17770) n=45 | 3606750–3615220 +8470 / 25226 (24566–26314) n=45
15 11:00 | 6778270–6793886 +15616 / 16334 (13964–18778) n=52 | 3619545–3636378 +16833 / 25668 (24073–28194) n=52
15 12:00 | 6794026–6802826 +8800 / **11983 (9073–14362)** n=62 | 3636578–3650824 +14246 / 29296 (24385–32486) n=62
15 13:00 | 6802938–6809452 +6514 / 14744 (11487–17047) n=49 | 3651084–3663337 +12253 / 28934 (26901–32083) n=49
15 14:00 | 6813932–6830966 +17034 / 16792 (15991–17781) n=35 | 3669469–3686804 +17335 / 26142 (24104–30198) n=35
15 15:00 | 6831226–6844504 +13278 / 15799 (14347–17480) n=30 | 3687004–3697726 +10722 / 27095 (24520–30264) n=30
15 16:00 | 6851196–6864501 +13305 / 17186 (16634–17638) n=29 | 3702466–3713423 +10957 / 26325 (23858–28445) n=29
15 17:00 | 6873741–6887619 +13878 / 15908 (13705–17948) n=35 | 3720737–3727171 +6434 / 28329 (22111–35916) n=35
15 18:00 | 6891817–6908811 +16994 / 17721 (14859–**20459**) n=49 | 3732441–3748355 +15914 / 34943 (30978–**39332**) n=49
15 19:00 | 6908951–6919857 +10906 / 16627 (14993–17961) n=36 | 3748615–3761303 +12688 / 30357 (25558–33908) n=36
15 20:00 | 6926801–6935901 +9100 / 17384 (16805–18365) n=15 | 3766503–3773303 +6800 / 25177 (24904–25404) n=15

Home 12:00 hour is the formal-alert crash (avg 12.0k, min 9073, only +8800 progress). 18:00 is the only hour with a ≥20k print (max 20459) and W47’s 39332 peak. W47 08:00 is the leftover morning climb (avg 36.8k, max 38466). W47 17:00 progress span is soft (+6434) from the 17:05 handoff tail (matches patrol 1h 15.40=51.2%).

## CPU (W46N8 room_stats, 494 samples)

- avg **17.608947**, p95 **20.845000**, max **27.32** at tick **84278570 / 2026-11-15 13:12:07.432327+08**, commit ffdf767, bucket 10000.
- bucket min **9994**, max 10000, avg 9999.9211.
- **No cpu≥40 deploy-spike ticks** in this window (n_cpu_ge40=0). Next-highest: 26.02 @84281020 16:04, 25.03 @84277360 11:46, 23.97 @84276180 10:23. Model 12h cpu **17.596**. Quiet, similar to morning 17.73 / p95 20.80 / max 29.66 (that max was the 00:27 deploy tick, outside this window).

## Models

- `model.py --hours 12`: ticks 10200, tick_s 4.22365, coverage 0.9736, measured upgrade **20.1477 e/t**, build 0.305, storage_delta **−0.110**, cpu 17.596, energy_fill 0.862, upgrade_per_tick_1h 25.45, ideal upgrade 26.00, live upgrader_work 28 energy-bound. Matches room_stats 20.163 e/t closely (model window is wall-hours, not the exact tick window).
- `model.py --hours 3`: ticks 2540, tick_s 4.23425, coverage 0.8944, upgrade **20.959**, build 0, storage_delta **+0.767**.
- `model_w8.py --hours 12`: window 10200t cov 0.968 tick 4.22s, RCL7 3772723/10935000, **actual upgrade 18.97 e/t** vs ideal 30.03, upgrader_work actual 20 vs ideal 31, build_repair 2.0, storage_delta **−0.95**, eta ~443 h at this pace. Harvest 37.9 / upkeep 17.9. w8upgrader idle: working 0.86, waiting_feed 0.08. **src_A actual 0.46 e/t** vs ideal 9.6 — known link-metering bias, still present. R1 6.24 / R2 6.27 under model 9.5.
- `model_w8.py --hours 3`: 2540t cov 0.871 tick 4.23s, **upgrade 18.79 e/t**, build_repair 2.35, storage_delta −0.23. waiting_feed down to 0.04, working 0.93.

## Ledger (`python3 tools/ledger.py snapdiff 12`)

**Incomplete 12h ledger, same problem as the morning review.** Last snap before this collection was still **t84267292 / 2026-11-14 23:31:01+08**. No snap exists near official start t84274500. This review took a new snap at **t84284775 / 2026-11-15 20:28:41+08** (appended to `state/ledger_snaps.jsonl` only; no src/docs).

Printed snapdiff 12 window: **t84267292 → t84284775 = 17483 ticks (20.96 h wall)** — this is 12h-back from the new snap against the newest snap ≥12h old, **not** the official review window 84274500→84284720.

- W46N8: spawn 15.38 e/t (recycle refund 1.29, net 14.08) | repair 5.25 (walls/ramparts 1.42) | **up 16.69** | **build 0.00**. **sp:upgrader = 2.31 gross, rf:upgrader = 0.73, net 1.58 e/t** (still under the 5 e/t waste gate; morning’s last available comparable was net 1.35 on t84257520→84267292). Also sp:defender=0.87, sp:w8defender=0.86 (home-paid W47 guards).
- W47N8: spawn 16.69 e/t (recycle refund 0.88, net 15.81) | repair 2.74 (walls/ramparts 0.77) | **up 19.06** | **build 0.00**. sp:w8upgrader=1.64 (rf 0).
- Ledger `up` undercounts ~13% (docs/MODEL.md). Official pace is room_stats e/t.
- For context, vs t84264699 (24.15 h, near morning-window start): home net sp:upgrader 1.52, W47 net w8 1.60. Cannot produce a clean official-12h ledger net.

## 20k-gate and 40k-latch results

- **Home 20k/300t 3rd-upgrader latch: NOT armed.** Longest ≥20k stretch **41 t** (need 300). Max **20459** @ 18:28:00. Live why=ok, nUp=2, upExtra=0, allowExtra=20000, surplus only +1665. First ≥20k samples since several reviews, but a flicker, not a latch.
- **W47 40k/500t latch: NOT armed** (upLatched=0, 0 samples ≥40k, max **39332**, longest ≥30k only **231 t**). keep is 2 because that is the designed peacetime keep until the latch; upgCeil=2. Closest yet (39332), still not a latch. Do not add a third.

## Community (Overmind UpgradeSite) — re-fetched this run, not invented

- URL: https://raw.githubusercontent.com/bencbartlett/Overmind/master/src/hiveClusters/upgradeSite.ts (and the github blob page). Live fetch 2026-11-15 20:2x.
- **master** still: **energyBuffer=100000**, **energyPerBodyUnit=10000**, linksRequestBelow=200, minLinkDistance=10. `getUpgradePowerNeeded()` still `amountOver = max(energy - energyBuffer, 0)`; `upgradePower = 1 + floor(amountOver / energyPerBodyUnit)`.
- blob **2eae97b** (https://raw.githubusercontent.com/bencbartlett/Overmind/2eae97b/src/hiveClusters/upgradeSite.ts): still **storageBuffer=100000**, **energyPerBodyUnit=25000**, linksRequestBelow=200. The **100k buffer gate is unchanged**.
- Live energy (home ~16.7–17.0k / W47 ~24.5–25.0k) ≪ 100k. Having all 6+6 lab shells + factories is normal; enabling reactions / XGH2O is not. TooAngel was not re-fetched this run; prior reviews’ note still applies qualitatively (park upgrade when thin, keep logistics+repair warm). keep=2 + 2×10W at a ~25k bank match that posture. New remotes stay nod-only: CPU 17.61/20 is still tight.

## Incidents (invader / core) this window

Compiled from `incidents` + `events` alerts + patrol narrative. Some `incidents` rows are incomplete (missing `cleared`); those ends are taken from patrols/alerts and flagged.

1. **W47N7 core inc=84275423**, alert 09:30:08, why=core at (41,30) 100k, rdef84275457 spawn 84275457 (waited 34). Patrol 11:26: **cleared 84275827 / 09:58**. Duration ~404 t. `incidents` has only spawn_start (clear ev missing). W47 stor min 22082 @09:36 during this bill.
2. **W45N7 solo Invader inc=84277047**, 11:24:17–11:44:26, duration **221 t**, defender84277048, dispatched 11:34, arrived 11:39, escalated high (container 5000 hits), ended high, totalDamage 5280. why=solo, 1 creep at (46,49) then (20,7).
3. **W45N7 core inc=84277556**, 12:00:20–12:27:42, duration **388 t**, defender84277557, cleared why=**killed**, remote resumed. Combined with (2), this is the root of the home 12:22–13:12 under-15k stretch (min 9073) and the 13:31 home (a) FIRE.
4. **W47N8 hostile glimpse** room_stats hostiles=2 at **84278010 / 12:32:20**, stor 30339. Patrol 13:31: w8threat=84278015, threatSoft/softCap2 ON, leftover WINDOW=1500 expired **84279515 ~14:19** (14:31 patrol: softCap2 back to 0). Not a remote core; owned-room sample. Home-spawned guards likely from this stamp.
5. **W47N7 core inc=84279676**, alert 14:30:08, why=core at (42,29) 100k, rdef84279677 spawn 84279677 (waited 1). Patrol 15:31: rdef left spawn ~84279826, entered 18,1 @84279867, arrived 42,30 @84279918 14:46:56. **Clear ev missing from `incidents` and no alert_ended row.** Patrol 15:31 already calls it CLEARED; exact end tick uncertain (after 14:46, before 15:31).
6. **W47N7 core inc=84281822**, alert 17:02:18 (tick 84281850), cleared **84282194 / 17:26:33**, dur **372**, why=killed, remote resumed. `incidents` has the cleared row only (start missing). Overlaps the 17:05 W47 upgrader handoff softness.
7. **W47N8 hostile glimpse** room_stats hostiles=1 at **84283070 / 18:28:42**, stor 37082 (just after the 39332 peak). Last patrol: w8threat/w8inv=84283072, w8defender/w8guard parked north exit, softCap2 ON. WINDOW=1500 expired **84284572 ~20:16**. Live tip: threatSoft=0, softCap2=0, guards gone; stamp still 84283072.
8. **W47N7 core inc=84283941**, alert 19:30:09, rdef84283942 spawn 84283942, defend/dispatched 84284092 / 19:40:47 dur-to-dispatch 151. **No cleared row in `incidents` as of t84284720.** Live remotes are SAFE at 20:27, so it cleared in the unpublished tail. Exact end tick **uncertain**.

No Safe Mode. sma 6/6 throughout live queries.

## Patrol narrative (08:28 through 19:24, Asia/Hong_Kong)

All patrols: LIVE ffdf767 held, no src change, no deploy, labs OFF not re-asked, keep=2 held, 20k/300t not armed, war_* stopped, listener 5:5:1:1. Formal (c)–(f) did not fire. Box freezes every hour (self-healed); typical 30–399 tick room_stats holes.

- **08:28** (tick~84273600–84274500, overlaps morning review end): W47 (a) **holds** exact2h 18.72/30.08=62.3% (5th consec) short last300 20.00=66.5% at designed keep=2. Home (a) **CLEARS** exact2h 20.64/26=79.4%, short 28.00=107.7%, 1h 22.56=86.8%. nUp recovered to 2. W47 stor later 35385–36878; threatSoft leftover from 07:27 still on, expiry ~08:36.
- **09:28**: W47 (a) **holds** 19.04=63.3% (6th) short 20.00=66.5%; 1h 18.08 dragged by 08:38–08:45 nUp 2→3→2 handoff + freezes. Home stays clear 21.68=83.4%. **W47 stor max 38466 @08:37** (closest yet at that time). **threatSoft leftover expired ~08:36; softCap2=0, sealPark briefly off.**
- **10:25**: W47 (a) **holds** 19.04=63.3% (7th) short 20.00=66.5%. Home 23.56=90.6%. W47N7 core 09:30 in progress / just handled. W47 stor min 22082 @09:36. softCap2=0, sealPark=1 (known nUp≥3 unlatch deferral).
- **11:26**: W47 (a) **holds** 18.60=61.9% (8th) short 20.00=66.5%; 1h 17.08 from keep=2 + freezes. Home 22.63=87.0%. Core 84275423 cleared 09:58. W45N7 solo Invader appeared 11:24.
- **12:26**: W47 (a) **holds** 17.07=56.8% (9th) short last300 **10.77=35.8%** (below designed 20) from handoff + waiting_feed. Home exact2h 16.28=62.6% first under after CLEARED, short 11.06=42.5%, 1h 13.38 — (a) not yet formal (needs 2nd consec). (b) not fired (tip under but consec-under=1). W45N7 core 12:00. Home nUp=1 floor_bank through tip (remote_pause). sealPark briefly off when w8up hit 3 at 12:01.
- **13:31**: Home (a) **FIRES** exact2h 11.95/26=45.9% (2nd consec) short last300 12.17=46.8%, 1h 10.62=40.8%, nUp=1 floor_bank, stor min **9073 @12:36**. Home (b) RESET (tip 16747 back above). W47 (a) **CLEARS** — exact2h 19.50=64.8% still under 70% (would have been 10th) but short no longer soft (designed 20). W47 max 32486. softCap2 ON again from 12:32 W47N8 glimpse (w8threat=84278015).
- **14:31**: Home (a) **HOLDS** 12.23=47.0% (3rd) short last300 14.00=53.8% designed floor_bank; nUp=1 most of the hour, 2 @14:26. W47 exact2h 20.76=69.0% + short 20.68=68.8% slightly under — **does not formally hold** after the clear. threatSoft leftover expired ~14:19, softCap2=0. W47N7 core appeared 14:30.
- **15:31**: W47 (a) **FIRES** exact2h 20.37=67.7% (2nd consec under) short last300 INTERP 21.01=69.8% slightly soft near designed 20. Home (a) **clears** 20.09=77.3%, 1h 26.13=100.5%. W47N7 core 84279676 described cleared; rdef full-budget 25A/25M. Brief home floor_bank at the tip.
- **16:31**: W47 (a) **HOLDS** 19.35=64.3% (3rd) short last300 20.04=66.6% slightly soft at designed 20; 1h 17.48=58.1% from 15:27–15:37 post-handoff ~10 e/t waiting_feed, then designed 20 from 15:37. Home stays clear 24.23=93.2%. softCap2=0. Do not add a third.
- **17:31**: W47 (a) **HOLDS** 17.72=58.9% (4th) short last300 **10.00=33.2%** from 17:05 handoff (replacement empty-waited at hub; two newborns still walking at 17:30, only ~10 e/t). Home 24.44=94.0%, 1h 26.72=102.8%. W47N7 core 17:02–17:26. softCap2=0. keep=2 held.
- **18:26**: W47 (a) **HOLDS** 17.40=57.8% (5th) short last300 20.00=66.5% at designed keep=2; 1h 15.40=51.2% from the 17:05 handoff tail (second new upgrader hatched 17:26, empty-waited ~353 t, first loaded ~17:55). Home 22.36=86.0%. **W47 stor max 39332 @18:20:52**, tip still ~37k, softCap2=0, sealPark=0 at that tip. Closest yet to 40k, not a latch.
- **19:24**: W47 (a) **CLEARED** — exact2h 17.76=59.0% still under (would be 6th) but short last300 **22.33=74.2%** and last200 21.32=70.9% recovered. Brief 26 e/t from keep=2 plus an idle builder at the controller from ~18:43; then back to designed 20. Handoffs to 3 at 18:47 and 19:01 already back to 2. Home stays CLEARED exact2h 19.11=73.5%, 1h 19.95=76.7%, short last300 14 e/t floor_bank from 18:58 (after the 18:28 tip). W47 stor min 30978 @18:48 after spawn/refill; **softCap2 ON again** from 18:28 W47N8 hostile leftover; w8defender/w8guard parked north exit. 20k flicker 20459 @18:28 noted; gate not armed.

Hourly 30-min history backfills through 20:00 were OK (quiet) per journal; not re-run here.

## Scorecard inputs (for the review writeup)

**Phase0 — bank / soft / floor / labs**
- Home 15k floor: intact at the tip (why=ok, nUp=2, surplus +1665, stor ~16.7–17.0k). Mid-window crash to min 9073 (12:36) after designed remote defender bills; recovered. under-15k share **26.52%** (was 28.3%).
- W47 leanBank=0, bankWhy=ready, bankLeft=0, softCap2=**0**, threatSoft=**0**, softLeft=496 (hysteresis, stor in [22k,25k)). Leftover from 18:28 has expired. softCap2 was ON at morning tip, cleared ~08:36, ON again 12:32–14:19, ON again 18:28–~20:16, **OFF now**.
- Labs **OFF** (mode=null). actOk=**1** (new vs typical homeStor gap) — do not read as “labs on”. No re-ask.
- sealPark=1 (stor just under 25k). sealMinE=25000 unchanged.

**Phase1 — nUp / ceil**
- Home nUp=2, tUp=2, work=28, upExtra=0, boundHint=energy, 3rd-upgrader gate not armed.
- W47 keep=2, upgCeil=2, upLatched=0, upArm=40000, siteRem=0, phase=ready, feedOk=1. Do not add a third until 40k/500t.

**Phase2 — RCL% and ETAs**
- Home **63.43%** (6,935,901), +206,067 / 20.16 e/t, RCL8 **≈ 9.70 days** (was 61.54% / 18.67 e/t / ≈11.6 d).
- W47 **34.51%** (3,773,303), +193,913 / 18.97 e/t, RCL8 **≈ 18.45 days** (was 32.73% / 19.20 e/t / ≈19.7 d). Designed keep=2 20 e/t is already 66.5% of the 30.08 ceiling, so formal short-soft (a) alerts at the designed rate are expected — not a reason to revert keep=2.

**Phase3 — energy vs 100k**
- Home ~17k, W47 ~25k, both ≪ Overmind 100k buffer (re-confirmed). No industry / reactions / market re-ask.

**CPU / remotes / cmd**
- CPU 12h avg 17.61, p95 20.85, max 27.32, bucket min 9994, zero cpu≥40.
- Remotes SAFE, cores 0, host 0 at tip. Several designed core/Invader bills during the window (see Incidents).
- Memory.cmd stale, not touched. Listener 5:5:1:1, yield absent. war_* stopped (`aborted_by_misaki` still the standing order).

## What changed vs last review (2026-11-15 08:2x, window t84264650→84274500)

- LIVE still **ffdf767** (@84268045 / 00:27 HKT). No new deploy.
- Home RCL7 **61.54% (6.730M, +184k/12h ≈18.67 e/t, RCL8≈11.6 d)** → **63.4284% (6,935,901, +206,067 / 20.16311 e/t, RCL8≈9.696 d)**. Pace recovered further (3h model 20.96; some afternoon hours ~25–26 e/t when nUp=2 stuck). Still a hair under ideal 26 e/t (energy-bound 28W).
- Home stor avg 15.8k → **15840.81**, max 18946 → **20459**, min 9775 → **9073**, under-15k share 28.3% → **26.52%**. Live ~18.9–19.0k why=ok nUp=2 → **~16.7–17.0k why=ok nUp=2 work=28 upExtra=0**. First ≥20k samples (5 / 41 t) appeared and did not latch.
- W47 **32.73% (3.579M) 19.20 e/t ≈19.7 d** → **34.5067% (3,773,303) 18.9739 e/t ≈18.45 d**. keep=2, phase=ready, siteRem=0 throughout.
- W47 stor avg 26.2k → **28728**, max 35385 live / 34965 official-end → **39332**, min 21653 → **22082**, <15k 0%→0%, ≥20k 100%→100%, ≥25k 70.2%→**86.84%**, ≥30k 13.56%→**31.98%**, ≥40k still 0. Closest yet to the 40k latch (39332), still not a latch. Opening 08:25–08:46 climb continued the morning “35k” run to 38466, then a bigger 18:20 peak.
- softCap2: morning tip ON (07:27 leftover). This window: cleared ~08:36, re-armed 12:32 and 18:28 from W47N8 hostile samples, **cleared again by the live tip**.
- Remotes still SAFE at tip; several cores/Invaders billed through the day (W47N7 ×4, W45N7 Invader+core). No new code needed; ffdf767 already covered the wait-out bug.
- Labs still OFF. actOk 0-typical → **actOk=1** at this tip (homeStor recovered). termO 126976 unchanged; termK 172792 unchanged vs morning; W47 term K 33708 (already at 19:24).
- Ledger: no complete 12h net again. 20.96h net sp:upgrader **1.58 e/t** (was 1.35 on the previous stale-snap interval). Home ledger up 16.69 / build 0 (sites already done). W47 ledger up 19.06 / build 0.
- CPU 17.73 → **17.61** avg, p95 20.85, max 27.32 (no deploy spike), bucket min 9861 → **9994**.
- w8defender/w8guard present at morning and at 19:24 leftover; **absent at 20:27**.

## Flags / surprises / small-safe-ship candidates (describe only — do not implement)

1. **20k gate held, but first ≥20k flicker this cycle** (41 t, max 20459 @18:28). Not a latch. No ship. Keep the sticky 20k/300t rule.
2. **W47 39332 @18:20 is the closest yet to 40k/500t** (prior 38466 earlier this morning, 35385 live / 34965 official at last review, 32.3k on 11-11). Longest ≥30k only 231 t; 0 samples ≥40k; tip back to ~25k. Not a latch. keep=2 until it actually holds.
3. **softCap2 is OFF at the tip** (cleared after the 18:28 leftover expired ~20:16). Do not unpark ceil/seal mid leftover in general; this leftover already expired on its own. w8threat stamp 84283072 is stale residue.
4. **Labs still OFF, but actOk=1.** Not somehow on. No re-ask. Energy ≪ 100k (community constants re-confirmed).
5. **Missing reserve7** at the live tip (r7.on until 84287487, reservation ~2732). Watch, not an emergency. Similar to a previous review’s ageing reserve7 flag.
6. **`incidents` table missed some clear/start rows** (84275423, 84279676, 84283941 end; 84281822 start). Patrol + alerts fill the story. Observability only; exact end of the 19:30 W47N7 core is uncertain (SAFE by 20:27).
7. **Known W47 src_A link-metering bias still on** (model 12h actual 0.46 e/t vs 9.6). Not new, not a ship this review.
8. **Formal W47 (a) alerts at designed keep=2 20 e/t (=66.5% of 30.08) are expected.** Many consecutive under-70% looks today, several cleared when short recovered. Already-deferred observability: 70% alert floor vs designed 20 e/t. Do not revert keep=2 or add a third.
9. **Already-deferred:** sealPark nUp≥3 handoff unlatch. No ship.
10. No new deploy, no cpu≥40 spike, no war_* process, src clean. **No small safe game-code ship identified** that should go out with this review.

Uncertainties (do not over-claim): exact clear tick of W47N7 inc 84279676 and 84283941; morning published max 35385 vs official last-sample 34965 (explained above); ledger has no clean official-12h window; Memory.stats.commit is null (LIVE taken from deploys + room_stats); live stor oscillated a few hundred energy during the query burst — use the ranges given.

## Raw artifacts

All under `/workspace/screeps/state/_review12h_2026-11-15_20/`:

- FINDINGS.md (this file), computed_metrics.txt, overmind_constants.txt
- model_12h.txt / model_3h.txt / model_w8_12h.txt / model_w8_3h.txt
- ledger_12h.txt, ledger_windows_compact.txt
- q_*.json + q_all.json + run.txt + queries_stdout.txt + _run_queries.py
- live.json, listener_rot.json, repo_checks.txt
- sql_window.txt, sql_tip.txt, sql_hourly.txt, sql_room_window.txt, sql_morning_window.txt, sql_stor_minmax.txt, sql_stor_stretches.txt, sql_stor_longest.txt, sql_stor_key_stretches.txt, sql_series.csv, sql_cpu.txt, sql_cpu_spikes.txt, sql_cpu_top.txt, sql_sites_summary.txt, sql_sites_changes.txt, sql_commits.txt, sql_deploys.txt, sql_gaps.txt, sql_first_last_rows.txt, sql_hostiles.txt, sql_incidents.txt, sql_incidents_full.txt, sql_alerts.txt, sql_box_pauses.txt, sql_event_kinds.txt, sql_coverage.txt, sql_morning_w47_stor_max.txt, sql_morning_w47_stor_near_end.txt, _sql.py / _sql_rest.py
- patrol_iterations_slice.txt, patrol_digest.md, patrol_digest.json

Canonical numbers use **END_TICK=84284720**. Live queries are a few dozen ticks later (progress already 6,936,713 / 3,773,883). Prefer the official window for the table; use the live tip for the board state.
