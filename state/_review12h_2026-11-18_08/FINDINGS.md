# 12h strategic review — data collection
2026-11-18 ~08:2x Asia/Hong_Kong (morning). Official window t84322300→84331400.

This file is factual collection only. It does not declare a strategic plan or recommend keep/softCap/floor changes.

Comparisons: last 12h review 2026-11-17 20:2x (t84313190→84322300) and, where useful, 2026-11-17 08:2x (t84304140→84313190).

## Window bounds and coverage

- START_TICK=84322300 (2026-11-17 20:23:27 Asia/Hong_Kong) — end of last evening's review
- END_TICK=84331400 (2026-11-18 08:23:11 Asia/Hong_Kong) — room_stats tip snapped to 10-tick cadence
- ticks=9100, wall_s=43184.10, wall_h=11.9956, tick_s=4.7455
- Last evening tick_s was 4.7097; this window is slightly slower (~+0.036 s/t)
- expected 10-tick slots=911, n_samples/room=535, coverage=58.73% (was 70.07% last evening, 56.51% yesterday morning)
- 27 box_pause events in the window, sum 16809 s ≈ 4.67 h of collector downtime
- Confirmed freeze 2026-11-18 06:37:05–07:05:46 Asia/Hong_Kong ~1720 s (tick resume 84330045), as the half-hour backfill journals said
- Other long freezes include 02:41:09–03:02:43 (~1293 s), 03:38:35–03:58:00 (~1156 s), 01:39:14–01:58:27 (~1153 s), 04:42:19–05:00:55 (~1108 s), 20:45:14–21:02:28 (~1022 s)
- Official creep_ticks coverage for W47N8 in the official window is much denser than room_stats: 8893 distinct ticks / 9101 want (~97.7%)

## LIVE commit vs HEAD vs last night

- Last evening LIVE was c6d43491 @84321282 / 19:02:43 Asia/Hong_Kong (PR 61 spawn-pocket yieldPost), already live at this window's open
- room_stats.commit: c6d43491 from 84322300 through 84324680 (20:23:27–23:31:25, 159 samples), then 8daf0494 from 84324690 through 84331400 (23:32:13–08:23:11, 376 samples)
- Deploy table: 8daf0494 deployed 2026-11-17 23:30:52 Asia/Hong_Kong @84324673 — note "fix(w47n8): yieldHub takes the filler post when 33,33 is occupied (cul-de-sac bounce 32,32↔33,31)"
- Local HEAD is 253f5167 `routine state 2026-11-18 07:29`. Game is not at HEAD; LIVE is 8daf0494
- Memory.stats.commit and Memory.commit are null at the live tip (q_home @84331411 and q_err @84331427). This is the same as last evening's live q (cmt=null @84322298). room_stats/deploy table are the source of LIVE
- state/deploy.lock does not exist
- No deploy and no Memory change by this review

Git (local master vs origin/master): **ahead 22, behind 6** — the same divergence count as at the start of this collection. Did not pull/rebase/push.

- Behind (on origin, not in local master): c6d43491 fix(w47n8) keep spawn-pocket trips off the filler post (#61); 33fb991e / 10295c85 / 65263790 / da8d5fa8 / 38658296 handbook / docs-site PRs #60–#56
- Ahead (local, not on origin): 22 commits starting from 28f119e3 routine state 2026-11-17 12:38 through 253f5167 routine state 2026-11-18 07:29
- Non-routine commits in this window: 187b4aff (2026-11-17 20:28:46) last evening 12h review docs; 8daf0494 (2026-11-17 23:30:34) filler-post fix, which was deployed the same minute

## Already-live ships this window (not this review)

1. **c6d43491** (PR 61 yieldPost) — already live at window open; deploy was last evening @84321282 / 19:02:43, before this window
2. **8daf0494** — "fix(w47n8): take the filler post when hub container 33,33 is occupied", committed 23:30:34, deployed 23:30:52 @84324673. Already-live overnight; not a ship from this morning review

## Home W46N8 progress / e/t / ETA / storage

- Official window: progress 7685887→7873927, delta=188040, **20.66 e/t**, **72.01%** of RCL8 cap 10,935,000, remaining=3,061,073, **ETA 8.14 days** at this pace and tick_s
- Last evening: 70.29%, 20.62 e/t, ETA 8.59 d; yesterday morning: 68.57%, 18.73 e/t, ETA 10.15 d
- 3h (84329180–84331400, 2220 t, n=135, 05:26:51–08:23:11): **18.07 e/t** (was 22.14 last evening)
- 6h (84326850–84331400, 4550 t, n=255, 02:22:16–08:23:11): **21.84 e/t** (was 22.35)
- Storage: avg 16113, max **19077** @84327410 / 03:06:13, min **13298** @84324650 / 23:29:01
- **0 samples ≥20k** (last evening max 20244 / only 20 t; yesterday morning first touch 20753 / 51 t). The 20k/300t latch would not have armed
- Under-15k: **19.25%** (103/535) — was 16.1% last evening, 25.2% yesterday morning
- Longest under-15k stretches: **131 t** (84324570–84324700 / 23:22:41–23:33:00, min 13298), **121 t** (21:03:23–21:12:57, min 13663), **121 t** (02:00:17–02:09:38, min 14254). Last evening's longest was 191 t (min 13354) plus 151 t (min 12164)
- Live tip (q @84331411–84331412): stor ~18861–19011, nUp=2, work=28, why=ok, floor=15000, surplus=3861, upExtra=0. Above the 15k floor

## W47N8 progress / e/t / ETA / storage gates

- Official window: progress 4469811→4651772, delta=181961, **19.996 e/t**, **42.54%** of cap, remaining=6,283,228, **ETA 17.26 days**
- Last evening: 40.88%, 18.83 e/t, ETA 18.72 d; yesterday morning: 39.31%, 18.75 e/t, ETA 19.58 d
- 12h pace is 66.5% of the 30.08 ceiling (designed keep=2 20 e/t)
- 3h: **19.45 e/t**; 6h: **19.82 e/t** (last evening 3h was 20.58)
- Storage: avg 28450, max **38563** @84322300–84322340 / 20:23:27–20:26:40 (window open), min **17514** @84331370–84331380 / 08:20:44–08:21:34
- **0% ≥40k** (was 12.7% last evening, 8.2% yesterday morning). No ≥40k camp this window, so no 500 t latch and no box-freeze merge question. All-time high remains yesterday morning 44416 / 341 t. Last evening's closest clean camp was 470 t / peak 43041, 30 t short of the latch
- ≥20k 99.25%; ≥25k 88.79% (was 99.2%); ≥30k 35.51% (was 70.1%)
- First <22k ARM in these reviews (last evening min was 23932, never <22k): 60 t 08:07:35–08:12:27 (20184–21880) and 70 t 08:17:20–08:23:11 (17514–20314, still open at official tip). Live stor 20214 @84331413
- Live w8day @84331414–84331415: **keep=2**, upLatched=0, **softCap2=1**, **threatSoft=1**, **sealPark=1**, leanBank=0, siteRem=0, phase=ready, bankWhy=soft, softLeft=4786 (25000−20214), upArm=40000, sealMinE=25000, hubReady=1, upgCeil=2
- Memory.ops.w8inv=84329860 (W47N8 hostile sample 06:20:33) and w8threat=84331315 (during the 08:00–08:16 W47N7 invader). Last evening tip had softCap2=0 threatSoft=0 sealPark=0; a 22:23 leftover (WINDOW=1500 from a ~5 t north-edge invader) would have expired overnight; the flags at this tip are a new leftover plus storage under bankSoft/sealMinE 25000 and softArm 22000

## Formal upgrade-alert dual-condition (overnight patrols)

Rule used by the hourly patrols: formal W47 (a) needs exact2h under 70% **and** short soft, and does not re-fire until that dual-condition holds two consecutive patrols after a clear. keep=2 was left unchanged throughout.

| patrol (Asia/Hong_Kong) | W47 exact2h | short | formal (a) |
|---|---|---|---|
| 17th 20:30 | 20.58=68.4% | soft (designed 20=66.5%) | HOLDS, 8th consecutive |
| 21:17 | 19.78=65.8% | soft designed 20 | HOLDS, 9th |
| 22:23 | 19.32=64.2% (REPORT; later exact2h.txt in that dir was overwritten at 00:22) | last20–70 used; last200/300 across a box-pause not used to clear | HOLDS, 10th |
| 23:18 | 19.31=64.2% | soft last20–70 20=66.5% | HOLDS, 11th. 8daf0494 shipped this hour |
| 18th 00:19 | 20.44=67.9% still under 70% | **not soft** (last20 21.50=71.5%; last70–300 78–83%) | **CLEARS** after 11 holds since 13:36 |
| 01:26 | 21.08=70.1% **above** 70% | designed 20=66.5% | stays CLEARED |
| 02:17 / ~02:34 | 20.77=69.1% under again | not soft (last20 21.20=70.5%, last70–500 ~81%) | stays CLEARED |
| 03:20 / ~03:31 | 20.88=69.4% | last200 21.08=70.1% not soft | stays CLEARED; dual has not held two consecutive |
| 04:20 / ~04:31 | 19.98=66.4% | last200 19.59=65.1% soft (last20–140 span=40 after a pause, not used alone) | **first** dual after the clear; does not re-fire |
| 05:25 / ~05:40 | 19.95=66.3% | last20–200 span=40 after a pause not used alone; last300/500/1h 71.3/72.0/70.1% not soft | short not soft; dual did not hold a second consecutive |
| 06:20 / ~06:29 | 19.27=64.0% (exact2h.txt) / memory 19.35=64.3% | short soft (last20 20=66.5%; last70–300 50.9–59.8%) | **first** dual after that non-dual; stays CLEARED |
| 07:20 / ~07:23 | 19.83=65.9% | short recovered, **not soft** (last20 21.50=71.5%) | last hour's first dual did not hold a second; stays CLEARED |
| 08:22 exact2h (file already written; patrol may still be in progress) | **20.40=67.8%** still under 70% | last20/70 **20.00=66.5% soft**; last200 14.00=46.5%; last300 16.00=53.2%; last500 18.24=60.6% | after 07:20 short was not soft, this is again a **first** dual; formal does not re-fire on a single dual |

Home formal: 07:20 was the first home dual (exact2h 17.20/26=66.1%, short soft, nUp=1 floor_bank). 08:22 home exact2h **19.61/26=75.4% ABOVE**, short last20–500 93–107% not soft — that first home dual did not hold a second consecutive either. Live nUp=2 why=ok, stor tip ABOVE 15k, consec-under reset earlier in the 07:20 patrol (stor tip 16137 ABOVE).

40k/500t still unlocked (this window never touched 40k; this-hour max from the 07:20 patrol was 30626, later stor 30259; official window max 38563 at the open). keep=2 unchanged. This review did not change keep/softCap.

## Remotes, hostiles, incidents

Live q @84331417 / remth @84331426: W45N8 / W45N7 / W47N7 all visible, cores 0, hostiles 0, reservations 2142 / 1900 / 2424. Memory.stats.remote all SAFE (W45N7 and W47N7 why=killed). r7.on=true endTime=84333841 by=Misaki.

Incidents / alerts this official window:

1. **W45N7** inc 84322460 @20:36:15–20:36:20, solo Invader at 39,48, body 5M1W2T1A1R, eventDamage=0 / totalDamage=0. incidents table has only `spawn_start` THREAT (defender84322461). **No `cleared` row, no alert_ended.** Observability gap recurred here.
2. **W47N7** inc 84325756, alert_new @00:59:38 tick 84325800 solo Invader at 23,16; incidents has only `defend` dispatched @01:08:05 tick 84325907 (dur 151, inv=0). **No spawn_start row, no `cleared` row, no alert_ended.** Gap recurred.
3. **W47N7** inc 84331122 @08:00:35–08:16:59, solo Invader at 43,48. Full chain: spawn_start THREAT (rdef84331123) → defend dispatched @08:12:43 dur 151 → **cleared SAFE why=killed** @08:16:59 dur 204, plus alert_ended "remote resumed". This is the gap last evening was missing; it **did not recur** on this later incident.

W47N8 itself: 22:23 patrol recorded invader_W47N8_764 entering 33,1 @84323623, towers killed at 32,2 in ~5 t (death 84323627); threatSoft/softCap2/sealPark latched as designed (WINDOW=1500). Separately, room_stats hostiles=1 for a single sample @84329860 / 06:20:33 (0 at 84329850 and 84329870); w8guard and w8defender appear on that same sample; Memory.ops.w8inv is still 84329860 at the 08:25 tip. **No alert_new row** for the 06:20 sample.

sql_hostiles has that one W47N8 row only.

## CPU

- 12h (535 samples): avg **17.821**, p95 **21.36**, max **25.99**, bucket min **9930**, bucket avg 9999.65, **n_cpu≥40 = 0**
- Last evening: avg 18.13, p95 21.98, max 36.0, bucket min 9916, n_cpu≥40=0

## Home KO / labs

- Live @84331423: storage KO **13236**, lab 34,22 KO **835**, terminal KO 0 → **total 14071** (was 9516 last evening = 8836 stor + 680 lab; yesterday morning 4981)
- Inputs: K 187703 stor + 3000 term + 1065 lab = 191768; O 124400 stor + 3000 term + 1465 lab = 128865
- labReady @84331422: mode=KO, why=**active**, actOk=**1**, actGaps="", homeStor=19011 — the 15k reaction floor is **not** pausing (last evening tip was paused, actOk=0 actGaps=homeStor, stor ~13.9–14.6k)
- 20k boost skip held: home never reached 20k (max 19077); no boost-kind event in the window
- w8min why=ready, flipGaps=already; w9on=false, w9phase=fallback, w9rec=true, note="ABORT Misaki: withdraw recycle end wartime"

## Sites, walls, industry counts, war_/cmd

- Construction sites: 0 all window (n_zero=535 both rooms), live ns=0
- Labs/factory/terminal @84331421: home 6 labs + 1 factory + 1 terminal; W47 6 labs + 1 factory + 1 terminal
- Walls @84331428:
  - W46N8: 41 walls min **300001** @27,7; 20 ramparts min **300021** @33,22 (last evening min wall 300001 / rampart 301081)
  - W47N8: 11 walls min **998491** @24,3; 10 ramparts min **295301** @35,32 (last evening min wall 1000001 / rampart 300001). Rampart min is below the 300k figure last evening reported as the peacetime floor; wall min is slightly under 1M
- Memory.cmd @84331418: on=1, at=84224348, by="cmd", c={}, s={}, v=1 — **the same stale cmd as last evening**, not a new war command
- w47n9 remains aborted_by_misaki (on=false, recycle, ABORT note). war_* not restarted

## Ledger

A clean start snap existed at t84322337 (2026-11-17 20:26:28 Asia/Hong_Kong, t0=83976835) — unlike last evening, which had no snap between the 16th 08:27 (t84294791) and that review. A read-only tip snap was taken at t84331436. Diff window 9099 ticks / 11.99 h wall:

- W46N8: spawn 15.19 e/t (recycle refund 0.64, net 14.55) | repair 3.79 (walls/ramparts 1.07) | **up 17.65** | build 0.00. net sp:upgrader **1.72** (sp:upgrader 2.21 − rf:upgrader 0.49), still under the ~5 e/t waste gate (last evening's 36h net was 1.61)
- W47N8: spawn 16.05 (refund 0, net 16.05) | repair 2.22 (walls/ramparts 0.31) | **up 20.00** | build 0.00. Ledger up 20.00 matches room_stats 19.996

## W47 replacement upgrader walks (yieldPost / filler-post)

Source: official history in creep_ticks (not a live room WebSocket subscription). Seats treated as {(12,25),(14,26),(14,27),…}. South bypass tiles include 32,32. Filler post is 34,32. Hub container is 33,33.

Already seated at the start of the trail (pre-c6d43491 births): 84320564, 84321049.

**Post-c6d43491, pre-8daf0494** (yieldPost already live; filler-post fix not yet):

- w8upgrader84322007: first 34,30@84322009 20:00:38, first_seat 14,27@84322136 20:10:19, walk 127 t / 129 t incl. spawn. 32,32 ×5, south bypass ×5, north hook ×5, filler_post ×0, hub 33,33 ×4, pocket_bounce 0. This is last evening's first post-yieldPost walk, carrying into this window.
- 84322545: 34,30@20:43:42 → 13,27@20:53:17, walk 129/131. 32,32 ×5, bypass ×5, north ×5, post ×0, hub ×3
- 84323446: 34,30 → 13,27, walk 128/130. 32,32 ×5, bypass ×5, north ×5, post ×0, hub ×4
- 84323984: 34,30@22:36:42 → 14,27@22:55:20, walk **233/235**. 32,32 ×**75**, bypass ×75, north ×5, post ×0, hub ×24, pocket_bounce **5**. This is the 32,32 cul-de-sac the 23:18 patrol cited when shipping 8daf0494. It never stepped on 34,32.

**Post-8daf0494** (deploy @84324673 / 23:30:52):

- 84324885: first 33,30@23:47:48 → 13,27@23:57:21, walk 123/125. 32,32 ×5, bypass ×5, north ×1, post ×0, hub ×3. First post-deploy replacement in the 00:19 patrol ("no bounce")
- 84325423: first *observed* 29,35@00:35:13 → 13,27@00:39:47, walk_from_first 58, walk_incl_spawn 125. No pocket tiles in the observed prefix (history hole around spawn)
- 84326324: first *observed* 32,32@ (mid-path) → 14,27, walk_from_first 82, walk_incl_spawn 155. 32,32 ×3, bypass ×3, post ×0, hub ×3
- 84326862: 34,30 → 13,27, walk 128/129. 32,32 ×5, bypass ×5, north ×5, post ×0, hub ×3
- 84327763: 34,30 → 14,26, walk 132/134. 32,32 ×4, bypass ×4, post ×0, hub ×0. 04:20 patrol: 33,33 empty, fillers held 34,32/34,33, so the yieldHub branch did not trigger; later official-chunk staleness noted by that patrol
- 84328301: first *observed* 23,35 (mid-path after a hole) → 14,27, walk_from_first 38, walk_incl_spawn 128. No pocket tiles in the observed prefix
- 84329202: 34,30 → 13,27, walk 139/140. 32,32 ×5, bypass ×5, north ×5, post ×0, hub ×3 (self on 33,33 for 3 t). 33,33 was busy (fillers, haulers, rminers, reserve7, self); 34,32 also occupied by builder/fillers/haulers. Took the south bypass, not the filler post
- **84329740**: 33,30 → 13,27, walk 129/130. 32,32 ×0, bypass ×0, **filler_post 34,32 ×2** (self @84329795–84329796), hub ×0. During the approach, 33,33 was occupied by w8builder84329444, w8filler84329452, w8hauler84328370, w8rhauler84329264. **8daf0494 branch showed up**
- **84330641**: 34,30@07:23 → 14,27@07:30, walk 147/149. 32,32 ×0, bypass ×0, north ×5, **filler_post 34,32 ×5** (self @84330693–84330697), hub ×0. 33,33 occupied by fillers/hauler/rhauler; 07:20 patrol described this as a yieldHub 34,32 handoff. **8daf0494 branch showed up**
- 84331179: 34,30 → 13,27, walk 152/154. 32,32 ×5, bypass ×5, north ×9, post ×0, hub ×3 (self on 33,33 for 3 t). 34,32 was occupied by fillers and a hauler during the approach

Be factual: two post-8daf0494 walks (29740, 30641) stepped on 34,32 while 33,33 was occupied. Other post-fix walks used the 32,32 south bypass and did not step on 34,32 (sometimes 34,32 was itself occupied, sometimes 33,33 was empty). Pre-fix 23984 is the long 32,32 cul-de-sac that never took 34,32.

## iterations.log / errors

- events.kind=error, n=1 @84329960 / 2026-11-18 06:28:29 Asia/Hong_Kong. The payload is a console `QQ…` reply listing Memory.ops keys and Memory.stats keys (`hasUf:false`), not a bot stack trace. Treated as a collector misclassification, not a runtime exception
- Live lastErrorTick=83976900 (unchanged vs last evening). nErr is absent from the live Memory.stats payload (the 06:28 dump of Memory.stats keys has `errors` and `lastErrorTick`, not `nErr` or `commit`)
- state/iterations.log last write 2026-11-18 07:29 (1284 lines). A grep for Error/TypeError in the overnight patrol timestamps returned no exception lines. The 08:22 patrol had not yet appended a line when this review collected
- CPU/path audit notes in overnight patrols (creep_audit exit 2 vs the 8daf0494 baseline, motion exit 1 waiting_pickup / target_full / no_task) were classified by those patrols as known, not formal

## Overnight patrol narrative (short)

Evening opened with formal W47 (a) still held (8th–11th consecutive dual-condition, exact2h 64–68%, short at the designed keep=2 20 e/t). 22:23 a ~5 t W47N8 north-edge invader latched threatSoft/softCap2/sealPark for WINDOW=1500. 23:18 shipped and deployed 8daf0494 after the 233 t 32,32 cul-de-sac walk (23984). 00:19 the formal alert **cleared** because short was no longer soft (exact2h still 67.9%). After that, exact2h briefly went above 70% at 01:26 (21.08=70.1%), then sat under 70% again, but short was not soft for two consecutive hours, so formal stayed cleared. 04:20 and 06:20 each produced a **first** dual that did not survive the next patrol. 07:20 short had recovered (not soft); home logged its first dual (17.20=66.1%, nUp=1 floor_bank) without a formal fire. 08:22 exact2h is 20.40=67.8% with short soft again (last200 dropped to 14 e/t during the 08:00 W47N7 invader and the storage dip under 22k), so this is another first dual, not a second consecutive. Storage drained overnight from 38.6k at the open to a 17.5k min around 08:21; 40k was never retouched; live 20.2k with softCap2/threatSoft/sealPark on. Remotes were standing-ops and SAFE at the tip. 40k/500t and 20k/300t remain unlatched. keep=2 throughout.

## Anomalies / observability gaps

- Incident `cleared` row: last evening's W47N7-core gap **recurred** on W45N7 84322460 and W47N7 84325756 (no cleared / no alert_ended). It **did not recur** on W47N7 84331122 this morning, which has the full chain and alert_ended
- No alert_new for the 06:20:33 W47N8 hostiles=1 sample, even though w8inv latched 84329860
- Memory.stats.commit is null live (same as last evening); LIVE comes from the deploy table / room_stats
- One events.kind=error row is a mis-ingested console query, not a bot exception
- room_stats coverage 58.7% (box freezes); official creep_ticks much denser, with leftover official 404s noted in overnight backfill journals (W47N7@84330300, W45N8@84328100, W45N7@84328300) and mid-path first-seen on some upgrader walks
- `_patrol_2026-11-17_2223/exact2h.txt` was overwritten at 00:22 with the 00:19 numbers; 22:23 formal figures above come from that hour's REPORT.md
- W47 rampart min 295301 is below last evening's 300001 peacetime-floor figure; wall min 998491 is slightly under 1M
- W47 crossed under the 22k ARM this morning (min 17514) and softCap2/threatSoft/sealPark are on at the tip — a new fact versus last evening (min 23932, flags off). 40k/500t still unlocked. This review did not change keep/softCap

## Files

All outputs: `/workspace/screeps/state/_review12h_2026-11-18_08/`

Pointer: `/workspace/screeps/state/_review12h_2026-11-18_08.txt`

Scripts reused and path-edited: `_sql.py`, `_run_queries.py` (18/18 live queries ok @08:25:26 CST). Ledger snap+diff is read-only. No src change, no deploy, no commit, no Memory write, no long WebSocket room subscription, no messages sent.
