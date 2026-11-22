# Patrol 2026-11-22 12:22 / delivered ~12:31 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_1222
Previous: _patrol_2026-11-22_1117 delivered 11:28 (analysis tip 84413060 / later 84413150).

## Alerts
- ALERT FORMAL W47 upgrade HOLDS — seventh consecutive dual after the 05:38 clearance (11:27 was the sixth). exact2h 19.47/30.08=64.7% under AND meaningful short last800 19.14=63.6% still soft. last20-300 designed keep=2 20 e/t=66.5% must not clear. Do not change keep=2 / no standing third / 15k floor / 40k lock.
- Home formal STAYS CLEARED: exact2h 22.40/26.00=86.1% ABOVE 70%; last800 20.49=78.8% hard; 1h INTERP 20.87=80.3%.
- Storage formal STAYS CLEARED: prev tip 16910 and this tip 15398 both ABOVE 15k. Brief mid-hour under (min 14430@84413380) recovered; later 15498-15798.
- no formal (c): critical owned-room roles present. reserve7 gap after 11:45 freeze until 84414080; reservation stayed healthy (~2525..2504).
- no formal (d): audit exit 2 IDENTICAL REGRESSION [deploy] string vs 11:27 and 10:33, known baseline drift vs 2b5398f7 2026-11-19 02:28. motion 1h/2h exit 1 known waiting_pickup / target_full / no_task / waiting_feed / queue_blocked. w8rminer swamp source same known watch.
- no formal (e): CPU 1h min 14.61 max 25.53@84413170 mean 17.47; 2h min 14.61 max 25.53 mean 17.46; bucket min 9992 later 10000.
- no formal (f): infra ok; leftover official 404 W46N8@84413700 is a history hole, not infra down.

## Backfill
- Official history shard3 5 rooms ticks 84413201..84413900 (700), published_bases 84413200..84413800 at game.time=84413980.
- First pass 34/35 official GETs 200, missing_chunks=1 W46N8@84413700; inserted=5196 already_in_db=18435 ts_realigned=17187; tick_s printed 4.009 exact 4.00945.
- tick_s_in_use=4.00945 (first); later-mean-robust 4.16816 refused (worse vs live anchor); corrective first realign nfix=433 still_over_45s=0.
- confirm 12:26:37 gt=84414015, retry2 12:27:12 gt=84414023, late retry 12:29:30 gt=84414056 still_404=['W46N8@84413700'] inserted=0. Listener 0/100 (slot was W47N8/W45N8). Hole 100 ticks 84413701..84413800.
- JP 84413900 at 12:28:25 gt=84414040 all_five_200=True inserted=2947 still_404=[]. Official+JP through 84414000: four rooms 800/800, W46N8 700/800 missing only the leftover 404 hole.

## Freezes / gaps (to tell)
- NEW 盒子休眠 11:45:08-12:00:47 (931s; STATS 84413411..84413649 239t; official-filled 239/239 all five; listener restart 12:00:50, python 2431743 started 12:00:59). Recorded quietly by 12:09 backfill; first told here.
- NEW 盒子休眠 12:20:45-12:23:11 (139s; STATS 84413921..84413969 49t; official-filled 49/49 all five after JP; listener restart 12:23:14, python 2442173 started 12:23:23).
- NEW 监听短中断 12:14:21-12:14:56 (restart 12:14:44, no box_pauses row; STATS 84413821..84413849 29t; official-filled 29/29 all five).
- Already-told freezes through 10:45:15-11:06:19 and older, and leftover 404s W47N7@84412400 / W45N7@84411500, not retried (aged out of window start 84413201).

## Live / later
- Analysis tip 84414020 12:26:59 stor 15398/25216 p=9544845/6262495 nUp=2 w8up=2. Later 84414080 12:31:08 stor 15698/25216 p=9546525/6263731, reserve7 present.
- Remotes later vis SAFE host 0 core 0 res ~2260/2104/2525 (end 2281/2083/2504).
- keep=2 upLatched=0 upArm=40000 upgCeil=2 w8up on=0 feedOk=1 hubReady=1. sealPark=1 why=ok, threatSoft=0 softCap2=0 bankWhy=ready softLeft=0 (sticky leftover after last hour's kill).
- labs Memory.ops.labs W46N8=KO; labReady actOk=1 actGaps=empty; stocks O 81600 K 214156 KO 54836; koLab 560.
- r7 on endTime=84416576 by Misaki (was 84415534; not touched).
- Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — not touched. war_cmd/pulse stopped.
- Listener: 1 process pid=2442173 since 12:23:23 parent=4035476, yield_absent=True, peacetime 1-slot 5:5:1:1 rot W47N8, no second listener.
- ticksToDowngrade 150000/150000, safeModeAvailable 6/6 not activated.
- LIVE still 2b5398f7 (deploy 2026-11-19 02:28). src clean. No code change, no deploy.
