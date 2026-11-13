# Patrol 2026-11-14 04:25 Asia/Hong_Kong (1h peacetime)

TIP 84251740 (04:22:06 HKT), window tick ~84251010–84251740, later live to 84251780. LIVE 4ff78b4 held (deploy@84239560 13:26). No src/deploy this patrol.

## ALERTS
- FORMAL (a) home exact2h 12.02/26=46.2% (prev 13.92=53.5%) is 35th consecutive <70% AND short still soft (post-thaw last20-30 all 14.00=53.8% span 20-30 after 04:05-04:18 freeze; last70-200 span only 40t 13.55=52.1%; last300 13.46=51.8% span 300; 1h 10.05=38.7%). nUp=1 at last tip then remote_pause nUp=0 84251050-84251150 (~100t) while W45N7 core, nUp=1 again after first thaw. W47 exact2h 0.00/30.08=0.0% at TIP is 37th consecutive, progress still 3150854 at tip; after tip upgrade started (3150854→3151244 by 84251780).
- FORMAL (b) home stor analysis tip 14741 UNDER consec-under=2 (prev tip 14676 UNDER consec-under=1 FIRST). Mid-hour min 10631@84251110 03:35 after designed core-buster spend ~3250e; recrossed over15k 15441@84251700 04:19, under again 14641@84251730 04:21; later live 13811@84251770 / 13911@84251780 still UNDER. 20k/300t not hit (3h max 17154, best>=20k span=0). The brief recross then slip is knife-edge floor_bank, not a new unapproved spend.
- no formal (c)/(d)/(e)/(f)

## Economy / buildings
- HOME W46N8 RCL7 58.14% (p6357416 stor14741@84251740 04:22 HKT; later p6357976 stor13911@84251780 still UNDER). live uf why=floor_bank nUp=1 tUp=1 work=14 surplus=-259 floor=15000 allowExtra=20000. lab 34,20 7473→9223.
- W47 stor min 5510@03:30 max later 16327, live ~16027 keep=1 phase=minBuild bankWhy=minBuild leanBank=1 threatSoft=0 sealPark on sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 softLeft=8904 softCap2=1 siteRem 13789→979 later 769.
- Milestone: W47 lab 27,40 COMPLETED (hits 500); all five W47 labs exist. Roads 27,43 / 27,44 / 36,43 finished (5000). minCont 37,44 0→4021/5000. After lab shells finished, w8upgrader84251580 reached 12,25 and started upgrading (progress left 3150854 after tip); w8upgrader84251774 spawning. keep=1 not changed, no policy edit.
- ledger 2413t (~2.95h) home up 10.68 (undercount) spawn net 14.41 incl sp:defender=1.35 rf:defender=1.00 build 6.17; W47 up 0.03 spawn net 10.44 build 20.19 sp:w8upgrader=0.48.

## Remotes / defense
- W45N7 Invader core inc 84251031 03:30 at 10,43 hits 100000 level 0, cleared killed 84251463 04:01 dur 432 from DEFEND why=killed. designed core-buster defender84251055 (25A/25M ~3250e) spawn_start 84251055, entered W45N7 84251288, near core 84251327-84251464, walked home, last 84251585 35,29 then recycled (ledger rf:defender). Opening THREAT row dropped by listener ingest (inv=[] vs integer) at 03:30:08; spawn_start and cleared rows stored.
- Remotes W45N8/W45N7/W47N7 vis res 2117/712/2813 cores0 host0 SAFE (W45N7/W47N7 why=killed leftover). W45N7 res dropped during evac, reserver84251464 back on station 6,39 ttl 321, res climbing (704→712). W45N8 reserver84251489 on 7,37 ttl 346. reserve784251022 aged 84251633 at 39,27 designed, r7 endTime 84254565 left≈2791>2500 spawn waits, report not formal (c). home reserver zero_run 60t 84251400-84251460 after evac then replacements, report not formal (c).
- Memory.cmd.on=1 at=84224348 stale c={} s={}, not touched. sma 6/6 not activated. ttd home 150000 / W47 121725 then 124924 after upgrade started.

## Motion
- audit --patrol EXIT2 REGRESSION [deploy] is the same window metric shift vs 4ff78b4 (hauler cpu/rp100, miner trip, queen work_per_cpu, wbuilder cpu). motion --patrol EXIT1 waiting_pickup/target_full/no_task/queue_blocked/waiting_feed/parked_threat. w8filler ABA 211/207 is known target_full hub weave (up from 136/124, same class). rminer84250953 ABA 395 is evac/return during the W45N7 core (home 84251049-84251473 then back), not new pathfinding. no new stuck/oscillation after last deploy, not shipped.

## CPU / infra
- CPU 1h avg 16.98 max 21.09@84251480 04:02 p95 20.62 bkt min 10000 now 10000, 2h avg 17.15 max 21.39 leftover@84250600, not (e).
- Two box freezes 03:39:29-03:56:32 1018s room_stats 250t/1096s 84251150-84251400 and 04:05:44-04:18:14 746s room_stats 190t/839s 84251510-84251700; listener restarts 03:56:35 / 04:18:17 pid 2413757 since 04:18:27. peacetime single-slot 5:5:1:1 (yield absent, rot i=1 W47N8 at 04:18 left~296s / i=2 W45N8 at 04:25 left~45s; Memory.cmd stale, commander not live, not reclaimed). war_cmd/pulse stopped NO_WAR_PROCS.
- services.sh all ok postgres/views/grafana200/listener/dashboard8787-200; grafana_check 20/20; q.py live OK; DB writers fresh (room_stats lag ~30s at tip then a few seconds, creep_ticks ~5s).
- history_backfill 40min game.time=84251700 published 84251000-84251600 first-pass ticks 84251001-84251600 (600) inserted=6342 already_in_db=16592 ts_realigned=7279 tick_s=4.335 missing_chunks=5 (all rooms @84251600 official 404, then in-progress). confirm GET 04:22:04-04:22:20 recovered all five @84251600 official 200 inserted=3691, 100/100 each; unpublished 84251700 all 404 as expected. W46N8/W47N8/W45N8/W47N7 700/700 through 84251700; W45N7 463/700 empty-owned 237t 84251078-84251287 (plus 26t 84251506-84251531) during evac, official 200 not a fetch hole; plus unpublished tail after 84251700. leftover official 404s unchanged outside window (W45N7@84250800, W45N8@84250900, W47N8@84249600, W45N8@84248300 confirm still 404, plus older W45N7@84246800 / W47N7@84246700 / W46N8@84246500 / W45N7@84246300 / W47N7@84246300 / W47N8@84243700 / W47N8@84243100 / W45N8@84242900).
- labs OFF actOk=0 actGaps=homeStor why=ready homeStor 14761, do not enable, do not re-ask.
- minerals hsO=17324 termO=126976 termK=151080 W47 termE=1338 termK=56 wsK=64; min line why=minCont (site 37,44 4021/5000), flipGaps=homeStor,already.
- no src change from this patrol.
