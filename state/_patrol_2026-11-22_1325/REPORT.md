# Patrol 2026-11-22 13:25 / delivered ~13:39 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_1325
Previous: _patrol_2026-11-22_1222 delivered 12:31–12:33 (analysis tip 84414020 / later 84414080).

## Alerts
- ALERT FORMAL W47 upgrade HOLDS — eighth consecutive dual after the 05:38 clearance (12:31 was the seventh). exact2h 19.88/30.08=66.1% under AND meaningful short last800 20.06=66.7% still soft. last20-30 designed keep=2 20 e/t=66.5% must not clear. Do not change keep=2 / no standing third / 15k floor / 40k lock.
- Home formal STAYS CLEARED: exact2h 21.34/26.00=82.1% ABOVE 70%; last800 21.16=81.4% hard; 1h INTERP 21.67=83.3%.
- Storage formal STAYS CLEARED: prev tip 15398 and this tip 16732 both ABOVE 15k. Brief mid-hour under (min 13988@84414220 12:40:47) recovered by 84414270 stor 15688; later 16832–17782.
- no formal (c): critical owned-room roles present (miners 2 after a brief tip handoff of 3, queens 2, w8fillers 2, w8miners 2, rminers 3, reserver 1). reserve7 present 84414080–84414680 then zero from 84414690 through later 84415056; three remotes' reservations stayed healthy (~2120/2148/2625 then 2183/2085/2562).
- no formal (d): audit exit 2 IDENTICAL REGRESSION [deploy] string vs 12:31 and earlier, known baseline drift vs 2b5398f7 2026-11-19 02:28. motion 1h/2h exit 1 known waiting_pickup / target_full / no_task / waiting_feed / queue_blocked. w8rminer swamp source same known watch.
- no formal (e): CPU 1h min 14.22 max 22.89@84414320 mean 17.15; 2h min 12.83 max 23.00 mean 17.12; bucket min 10000 later 10000.
- no formal (f): infra ok; leftover official 404 W46N8@84414700 is a history hole, not infra down.

## Backfill
- Official history shard3 5 rooms ticks 84414201..84414900 (700), published_bases 84414200..84414800 at game.time=84414918.
- First pass 34/35 official GETs 200, missing_chunks=1 W46N8@84414700; inserted=8864 already_in_db=16475 ts_realigned=14797; tick_s printed 4.054 exact 4.05432.
- tick_s_in_use=4.05432 (first); later-mean-robust 4.21078 refused (worse vs live anchor); corrective first realign nfix=587 still_over_45s=0.
- confirm 13:31:36 gt=84414950, retry2 13:32:25 gt=84414962, late retry 13:38:39 gt=84415052 still_404=['W46N8@84414700'] inserted=0. Listener 0/100 (slot was W45N8/W45N7, then the 13:16 freeze). Hole 100 ticks 84414701..84414800.
- JP 84414900 at 13:37:58 gt=84415042 all_five_200=True inserted=2550 still_404=[]. Official+JP through 84415000: four rooms 800/800, W46N8 700/800 missing only the leftover 404 hole.

## Freezes / gaps (to tell)
- NEW 盒子休眠 12:51:44-13:03:45 (715s; STATS 84414371..84414559 189t; official-filled 189/189 all five; listener restart 13:03:48, python 2459147 started 13:03:58). Recorded quietly by the 13:11 backfill; first told here.
- NEW 盒子休眠 13:16:57-13:26:20 (563s; STATS 84414731..84414879 149t; official-filled W47N8/W45N8/W45N7/W47N7 149/149, W46N8 79/149 missing 70 ticks 84414731..84414800 due to leftover official 404 W46N8@84414700; listener restart 13:26:23, python 2466379 started 13:26:32). The ~13:27 pid change vs 2459147 is this freeze restart, not a short WS and not an ordinary rotate. NEW short WS: none.
- NEW leftover official 404 W46N8@84414700 (confirm+retry2+late retry still 404; listener 0/100; hole 100 ticks 84414701..84414800) — first told by this 1h patrol.
- Already-told freezes through 12:20:45-12:23:11 and older, and leftover 404s W46N8@84413700 / W47N7@84412400 / W45N7@84411500, not retried (aged out of window start 84414201). W46N8@84413700 remains 404.

## Live / later
- Analysis tip 84414950 13:31:35 stor 16732/28268 p=9565415/6281582 nUp=2 w8up=2. Later live 84415056 13:38:56 stor 17782/29711 p=9568155/6283702; room_stats later through 84415050 home 17682 / W47 29711 (W47 peaked 30011@84414990-84415040).
- Remotes later vis SAFE host 0 core 0 res ~2120/2148/2625 (end 2183/2085/2562).
- keep=2 upLatched=0 upArm=40000 upgCeil=2 w8up on=0 feedOk=1 hubReady=1. sealPark=0 why=done (w8soft why=ok, w8sealPark=0); threatSoft=0 softCap2=0 bankWhy=ready softLeft=0. Last hour's sticky sealPark=1 leftover after the Invader kill has cleared itself. Do not change seal/keep numbers.
- Two unboosted 10W w8upgraders seated (84414160 ttl=701 at 14,26 and 84414764 ttl=1305 at 12,25) at live 84414997.
- labs Memory.ops.labs W46N8=KO; labReady actOk=1 actGaps=empty; stocks O 81600 K 213756 KO 55636; koLab 225.
- r7 on endTime=84417620 by Misaki (was 84416576 last patrol; not touched).
- Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — not touched. war_cmd/pulse stopped.
- Listener: 1 process pid=2466379 since 13:26:32 parent=4035476, yield_absent=True, peacetime 1-slot 5:5:1:1 rot W47N8 at end, no second listener.
- ticksToDowngrade 150000/150000, safeModeAvailable 6/6 not activated.
- 20k/300t still unlocked (3h max 18688, n>=20k span=0). 40k/500t still unlocked (this-hour-to-tip hist max 28692@84414930, later max 30011@84414990; n>=40k=0; already-told earlier 40k touches unlatched 12h/24h max 41133@84406720).
- LIVE still 2b5398f7 (deploy 2026-11-19 02:28). src clean. No code change, no deploy.
