# 2026-11-14 03:25 Asia/Hong_Kong 1h peacetime patrol

TIP 84251010 @ 03:28:37 Asia/Hong_Kong, later live through 84251063. LIVE 4ff78b4 held (deploy@84239560 13:26 HKT); no new deploy / no src change.

## Alerts
FORMAL ALERT (a) holds: home exact2h 13.92/26=53.5% (prev 13.92=53.5%) is 34th consecutive <70% AND short still soft (last20-300 all 14.00=53.8% exact span, 1h 14.00=53.8%); nUp=1 floor_bank all analysis hour, no handoff. After tip, W45N7 core flipped uf to remote_pause and nUp=0 (designed, not in the exact2h window).
W47 exact2h 0.00/30.08=0.0% is 36th consecutive, progress flat 3150854, keep=1 do not revert.
Formal (b) not standing: tip 14676 UNDER is FIRST (prev tip 16886 ABOVE consec-under=0 RESET); later still 12196-13376 UNDER.
No formal (c)/(d)/(e)/(f).

## Economy / buildings
Home RCL7 58.07% p=6350431 (later 6350747) stor tip 14676 then ~13.2k; since-last min 12836@84250860 03:17 max 17086@84250200 02:29 under15k 48/83=57.8%. 20k/300t not hit (3h max 17154, best>=20k span=0).
Milestone: home lab 33,22 COMPLETED this hour (LAYOUT site rampart 33,22 @84250450 02:47; live lab 500 + rampart 300821). Remaining home lab 34,20 4303→7473. W47 lab 27,40 26301→42411. Road 25,10 finished hits 5000. minCont 37,44 still 0/5000; roads 36,43 still 0, new 27,43/27,44 0/300. siteRem 29389→13789, roadCrit 30→38, threatSoft stays 0. keep=1 phase=minBuild bankWhy=minBuild leanBank=1 sealPark on sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 softLeft=18190 softCap2=1.
Ledger 1686t (~2.06h): home up 11.76 (undercount) spawn net 15.27 build 7.63; W47 up 0.00 spawn net 12.28 build 20.78.

## Remotes / defense
Incidents in analysis window (through 84251010): 0. vis at 84251030 SAFE cores0 host0 res 2389/2034/2491.
At 84251031 03:30 HKT W45N7 Invader core appeared (alert_new why=core, defender requested). Live 84251060: core 6af7653ef7be4958d025c0a8 at 10,43 hits 100000/100000 level 0, host 0. Designed core-buster defender84251055 (25A/25M ~3250e, not the 5400 kite kit) spawn_start ~84251055 at home Spawn3 30,34 rem 144/150. W45N7 my creeps evacing (rminer 21,4, reserver 21,7). uf why=remote_pause nUp=0 hs=12196. Did not touch Memory.cmd (stale on=1 at=84224348 c={}) or Safe Mode.
reserve784249978 last on station 39,27 through 84250589 (~02:57, designed 600t life from 84249980), replacement reserve784251022 spawning/walking from 84251023 after 433t gap, live W47N8 34,32 ttl 593, r7 endTime 84253521 left≈2485, reservation held, report not formal (c). Home reserver zero_run 60t 02:43-02:47 designed handoff, live W45N7/W45N8 on station, not formal (c). miner=2 all hour (brief 3 during 98t handoff).

## Motion / CPU / infra
audit --patrol EXIT2 REGRESSION [deploy] is window metric shift vs 4ff78b4 (hauler cpu/rp100, miner trip, queen work_per_cpu, wbuilder cpu). motion --patrol EXIT1 waiting_pickup/target_full/no_task/queue_blocked/waiting_feed, w8filler ABA 136/124 is known target_full hub weave (up from 116/103, same class), no new stuck/oscillation after last deploy, not shipped.
CPU 1h avg 17.24 max 21.39@84250600 02:58 p95 20.16 bkt min 9999 now 10000, 2h avg 17.16 max 21.39 p95 19.86 bkt min 9993, not (e).
No new box freeze this hour (last still 02:10:28-02:25:39; room_stats gaps>=30t since last: none). Listener last restart 02:39:08 after ping/pong timeout (not a box freeze), pid 2380163 since 02:39:18. Peacetime single-slot 5:5:1:1 (yield absent, rot i=1 W47N8 at 03:27 left~140s / i=3 W45N7 at 03:32 left~70s; Memory.cmd stale, commander not live, not reclaimed). war_cmd/pulse stopped NO_WAR_PROCS. services.sh all ok postgres/views/grafana200/listener/dashboard8787-200. grafana_check 20/20. q.py live OK. DB writers fresh (room_stats lag ~40s at tip then a few seconds; creep_ticks ~2-4s).
history_backfill 40min game.time=84251000 published 84250300-84250900 ticks 84250301-84251000 (700) inserted=6893 already_in_db=15887 ts_realigned=0 tick_s=4.425 missing_chunks=4 then confirm/retry: W47N8@84250900 official 200 inserted=3 (already live-complete); W47N7@84250900 official 200 on late confirm GET 03:33:00 inserted=3; W45N7@84250800 persistent official 404 (confirm 03:29:21 and late 03:33:03 still 404; adjacent 84250700 and 84250900 both 200); W45N8@84250900 still official 404 on confirm 03:29:27 and late 03:32:59 (game.time=84251070). After retry: W46N8/W47N8/W47N7 700/700, W45N8/W45N7 600/700, plus unpublished tail after 84251000. Leftover official 404s unchanged outside window (W47N8@84249600, W45N8@84248300 confirm still 404, plus older W45N7@84246800 / W47N7@84246700 / W46N8@84246500 / W45N7@84246300 / W47N7@84246300 / W47N8@84243700 / W47N8@84243100 / W45N8@84242900).
labs OFF actOk=0 actGaps=homeStor why=ready homeStor 13326, do not enable, do not re-ask. sma 6/6 not activated. ttd home 150000 / W47 122439. minerals hsO=17324 termO=126976 termK=151080 W47 termE=1338 termK=56 wsK=64; min line why=minCont (site 37,44 still 0/5000), flipGaps=homeStor,already.
