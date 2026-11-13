# Patrol 2026-11-13 23:28 Asia/Hong_Kong (1h peacetime)

TIP 84247740 23:28:01 HKT LIVE 4ff78b4 (held, deploy@84239560 13:26; no new deploy this patrol).

## Formal alerts
- (a) YES: home exact2h 14.07/26=54.1% (prev 12.73=48.9%) is 30th consecutive <70% AND short still soft (post-thaw last20-200 all 14.00=53.8% span 20t after 23:10-23:26 freeze, last300 14.00=53.8% span 300; 1h 14.00=53.8%). nUp=1 floor_bank all hour, no handoff.
- W47 exact2h 0.00/30.08=0.0% (prev 0.0%) is 32nd consecutive, progress flat 3150854, keep=1 do not revert.
- (b) no: home stor analysis tip 17424 ABOVE consec-under=0 (prev tip 16394 ABOVE). min 14312@84247480 23:08 max 17474@84247720 23:26 under15k 3/35=8.6%; later 16674-17024-16724@84247810 23:33 still ABOVE.
- (c) no: critical roles present. reserver84247245 on W45N8 7,37 ttl~91, W45N7 res 2083>RES_SPAWN spawn waits; reserve784247520 on station 39,27 ttl~366, r7 endTime 84250329 left≈2570>2500.
- (d) no: audit --patrol EXIT2 is same known deploy-window metric shift vs 4ff78b4 (hauler waiting_pickup, queen target_full, miner trip, wbuilder cpu). motion --patrol EXIT1 waiting_pickup/target_full/no_task/queue_blocked, w8filler ABA 180/175 is known target_full hub weave, N-exit flips=0 (same as last hour), #37=0 PR34 (22,15)=0 (10,33)=0. No new stuck/oscillation after last deploy, not shipped.
- (e) no: CPU 1h avg 17.52 max 21.64@84247020 p95 20.84 bkt min 10000 now 10000; 2h avg 17.40 max 22.3 leftover@84246160.
- (f) no: infra self-healed (see below).

## Authorized sites
W47 lab 28,38 12909→31959, 27,40 5942→7142, minCont 37,44 still 0/5000, roads 37,42 and 36,43 still 0; home 33,22 20136→28644, 34,20 still 4303 (stalled 3rd hour), labsN=4. siteRem 86809→66499, roadCrit 31→32. threatSoft 0→1.

## W47N7 solo Invader (end of hour)
invader_W47N7_833 entered ~84247689 (ttl 1500→1407 at live 84247782) during the 23:10-23:26 box freeze, so no incidents row. Body 2T/5M/1RA/1W/1A hits 1000 at 32,25. stats.remote W47N7 THREAT why=solo. Designed full-budget rdef84247690 (19RA/25M/6H ~5400e) spawn_start 84247690 at W47N8 33,30, still spawning at 84247757. Miners evac'd to W47N8 (stands 31,34 / 18,17 left ~84247690-84247700). reserve7 still on controller 39,27. Did not touch Memory.cmd or Safe Mode. No src change.

## Remotes
W45N8/W45N7 vis SAFE res Misaki 2328/2091 cores 0 host 0 (W45N7 why=killed leftover). W47N7 vis res 2570 host 1 cores 0 THREAT why=solo.

## Infra
Two box freezes: 22:44:15-23:01:43 ~1039s (no-STATS 266s at 22:43:59 first), room_stats 310t/1364s 84247080-84247390; and 23:10:34-23:26:17 ~943s, room_stats 230t/989s 84247490-84247720. Listener restarts 22:43:59 / 23:01:46 / 23:26:20 pid 2336762; rotate i=0→i=1 hit subscribe-limit (W46N8 23:26:32, W47N8 23:31:04), this patrol killed listener.py only (wrapper relaunch 23:32:52 pid 2340524), W47N8 live ticks resumed (84247819 lag ~5s). Peacetime single-slot 5:5:1:1 (yield absent, rot i=1 W47N8 at 23:33 left~440s; Memory.cmd stale at=84224348, commander not live, not reclaimed). war_cmd/pulse stopped NO_WAR_PROCS. services.sh all ok postgres/views/grafana200/listener/dashboard8787-200. grafana_check 20/20. q.py live OK. history_backfill 40min game.time=84247724 published 84247000-84247600 ticks 84247001-84247700 (700) inserted=10586 already_in_db=13285 ts_realigned=0 tick_s=4.423 missing_chunks=0 all five rooms distinct=700 plus unpublished tail after 84247700. Leftover official 404s outside window (distinct 1): W45N7@84246800, W47N7@84246700, W46N8@84246500, W45N7@84246300, W47N7@84246300, plus older W47N8@84243700 / W47N8@84243100 / W45N8@84242900.

## Other
labs OFF actOk=1 actGaps="" why=ready homeStor 16724, do not enable, do not re-ask. sma 6/6 ttd 150000/125714 not activated. minerals hsO=17324 termO=126976 termK=151080 W47 termE=1338 termK=56 wsK=64. min line why=minCont (site 37,44 still 0/5000), flipReady=0 flipGaps=already. ledger 846t (~1.04h) home up 11.80 (undercount) spawn net 8.71 build 10.15; W47 up 0.00 spawn net 24.82 incl sp:defender=6.62 build 23.30. HOME W46N8 RCL7 57.66% (p6305448 stor17424@84247740 23:28 HKT; later p6306428 stor16724@84247810 23:33 still ABOVE) live uf why=floor_bank nUp=1 tUp=1 work=14 surplus=+1674 floor=15000 allowExtra=20000. W47 stor min 86-146 after defender spend (max 7592@22:27) keep=1 phase=minBuild bankWhy=minBuild leanBank=1 threatSoft=1 sealPark on sealMinE=25000 hubLink=1 feedOk=1 upLatched=0. no src change from this patrol.
