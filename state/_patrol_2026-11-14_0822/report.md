# Patrol 2026-11-14 08:28 Asia/Hong_Kong (peacetime 1h)

Window tip 84254160 (07:20 / 07:23 last patrol) → 84255030 (08:25:01). LIVE 4ff78b4 held (deploy@84239549 13:26); no new deploy, no src change.

## Formal flags
- FORMAL ALERT upgrade: home exact2h 13.85/26=53.3% (prev 13.77=53.0%) is 39th consecutive <70% AND short still soft (post-thaw last20-300 all 14.00=53.8% span 20-300, last200 span 170t after 08:12 stall, 1h 13.56=52.2%). nUp=1 floor_bank all analysis hour after the 07:17-07:23 handoff ended at 84254200; no later handoff.
- W47 exact2h 16.88/30.08=56.1% (prev 18.84=62.6%) is 41st consecutive AND short still soft (last20-200 all 20.00=66.5%, last300 15.10=50.2%, 1h 13.77=45.8%). The 1h/last300 dip is the designed upgrader handoff during the 07:39-08:02 box freeze: w8upgrader84253213 last 84254751 at 12,25; 84253019 aged walking empty 10,16@84254900; replacements 84254492/84254652 spawned 84254494/84254654, waiting_feed then seated 14,26/14,27. Progress flat 3199534 for ~40t 84254730-84254770 (et=0), 10 e/t at 84254810, then 20 e/t from 84254820/08:09. keep=2 designed, do not revert.
- no formal storage: home analysis tip 15358 ABOVE consec-under=0 RESET (prev tip 14296 UNDER consec-under=1). since-last min 12728@84254870 08:13 max 15768@84254730 08:02 under15k 39/54=72.2%. crossed under 14886@84254290 07:30, over 15768@08:02, under 14518@08:03, over 15458@84255010 08:23; later 15028/15128/14978@84255070 / 15078 / 15178@84255090 08:29 still ABOVE. 20k/300t not hit (3h max 16896, best>=20k span=0).
- no formal (c)/(d)/(e)/(f).

## Energy / strategy
- Home model 2h upgrade 13.85 e/t (ideal 26), 1h 13.56; nUp=1 work=14 is the cap and the single biggest gap (floor_bank, storage knife-edge).
- W47 model 2h 16.85 / 1h 13.66 vs ideal 30.03; live short 20 e/t is the 20 WORK cap, biggest real gap vs 31 WORK ideal while still under the 40k arm. Model 2h src_A 0.22 (1h 0.25) is the same known path_arrivals measurement hole: w8miner84253252 seated 26,11 all 616 samples until 84254775, then 3t handoff gap, w8miner84254686 seated 246; seated gaps only 3+4 official-hole+2 listener = 9t; not a missing-miner or pathing bug.
- Milestone: W47 storage first crossed 25000 at 84254220 07:25:21 (25048), max 25486@84254760 08:04, tip 25050, later 23850@84255080. softLeft 646→0, sealPark on, sealMinE=25000, phase=ready why=done softCap2=1 keep=2 leanBank=0 feedOk=1 hubLink=1 siteRem=0 upLatched=0 upArm=40000 ttdW 150000, progress 3191734→3204064@tip later 3205264. bankWhy soft→threatSoft after the 07:36 hostile (w8threat=84254373, WINDOW until ~84255873 / ~09:27 HKT).
- home lab 34,20 25360→29410/50000 only remaining home site (sites=1). W47 sites=0, all five labs + factory + minCont 37,44 exist. roadCrit=1 (was 0/16 earlier in the hour).
- ledger 2479t (~3.05h) home up 11.65 (undercount) spawn net 13.99 build 6.32 incl sp:w8defender=2.02 (spawned at home); W47 up 17.19 spawn net 15.21 build 0.12 incl sp:defender=1.31 sp:w8guard=1.10 rf:defender=1.03 th=0.05.
- labs OFF: live lab2 why=ready propose=1 actOk=1 actGaps="" homeStor~15078 (gate just opened because storage kissed 15k). Do not enable, do not re-ask. w8min why=ready flipGaps=already. minerals hsO=17324 termO=126976 termK=156748 W47 termE=1143 termK=40 wsK=64.
- sma 6/6 not activated; ttd home 150000 / W47 150000.

## Remotes / defense
- remotes W45N8/W45N7/W47N7 vis res 2190/1885/2804 (Misaki) cores0 host0 SAFE (W45N7/W47N7 why=killed leftover). incidents since last 0 (only prior W47N7 core cleared 84253448).
- W47N8 hostiles=1 at 84254370 07:36:27, gone by 84254380. Designed w8guard84254369 (2T/25A/14M, born 34,30) and w8defender84254370 (25R/25M, born home 35,28) walked to parked_threat 29,5/28,5 hits full, ttl~938/966. threatSoft=1, bankWhy=threatSoft. No Invader core, remotes stayed SAFE. Do not touch Memory.cmd (on=1 at=84224348 stale c={} s={}).
- reserve7: reserve784254322 on 39,27 84254323-84254900 after designed wait, renewed endTime 84257869 left≈2812>2500, then zero_run from 84254940, live n=0 designed wait; report not formal missing-role.
- home reservers: 84253651 on W45N8 until ~84254700, replacement 84254733 now W45N8 7,37 ttl~277; 84253968 on W45N7 then 84254916 now W45N7 6,39 ttl~460. zero_run only a single thaw sample, not formal (c).
- W47N7 miners stayed on 18,17 and 31,34 (handoff 84252833→84254141 and 84253350→84254702).

## Motion
- audit --patrol EXIT2 REGRESSION [deploy] is the same window metric shift vs 4ff78b4 (hauler cpu/rp100, miner trip, queen work_per_cpu, reserve rp100, reserver idle/rp100, rminer excess/trip, wbuilder cpu, wrminer idle). Same known issue, not shipped.
- motion --patrol EXIT1 waiting_pickup/target_full/no_task/waiting_feed/queue_blocked/parked_threat. w8filler ABA 111/108 known target_full hub weave (vs last hour 129/90/35/76, same class). rminer84250953 osc 98 is still the 6h leftover, absent from the 1h motion window. miner84254842 excess 13.33 / queue_blocked is first sit 35,28→38,32 after miner84253422 aged on 38,32; same class as last hours, not a pathing bug. hauler84253274 waiting_pickup ~400t parked empty is known idle when the home link carries source B. No new stuck/oscillation after last deploy, not shipped.

## CPU / infra
- CPU 1h avg 17.70 max 24.17@84254800 08:07 p95 20.59 bkt min 10000 now 10000; 2h avg 17.67 max 24.17 bkt min 9996; not (e).
- New box freeze this hour: 07:39:56-08:02:22 ~1337s, room_stats gap 320t/1403s 84254410-84254730 (07:39:22-08:02:45). Listener restart 08:02:26. Then ws ping/pong timeout 08:11:58, restart 08:12:02, room_stats gap 40t/179s 84254820-84254860 (08:09:22-08:12:21). Then ws "Connection to remote host was lost" 08:24:26, restart 08:24:26, pid 2481803 since then; re-subscribed W47N8 leftover then rotated W45N8/W45N7 and at 08:29:52 i=0 W46N8 left 600s. errors.log has freeze + two ws errors only (no no-STATS / subscribe-limit this hour).
- Peacetime single-slot 5:5:1:1 (yield absent; Memory.cmd stale, commander not live, not reclaimed). war_cmd/pulse stopped NO_WAR_PROCS.
- services.sh all ok postgres/views/grafana200/listener/dashboard8787-200. grafana_check 20/20. q.py live OK. DB writers fresh (room_stats lag ~24s at tip then a few seconds, creep_ticks ~3s).
- history_backfill 40min game.time=84255004 published 84254300-84254900 ticks 84254301-84255000 (700) inserted=9244 already_in_db=15532 ts_realigned=0 tick_s=4.476 missing_chunks=3 (W47N8/W45N8/W47N7@84254900 official 404; W46N8 and W45N7 200). confirm GET 08:24:00 still 404. retry2 GET 08:28:33 all three HTTP 200; second backfill inserted=801 already_in_db=26731 missing_chunks=0, all five rooms 700/700 in the 40m window. Unpublished latest chunk 84255000 expected (game.time was 84255083). Leftover official 404s unchanged outside window (W47N7@84253600, W45N8@84253800, W46N8@84253100, W46N8@84252400, W46N8@84252000, W45N7@84251800, W45N7@84251700, W45N7@84250800, W45N8@84250900, W47N8@84249600, W45N8@84248300, plus older W45N7@84246800 / W47N7@84246700 / W46N8@84246500 / W45N7@84246300 / W47N7@84246300 / W47N8@84243700 / W47N8@84243100 / W45N8@84242900).
- HOME W46N8 RCL7 58.55% (p6402806 stor15358@84255030 08:25 HKT; later p6403646 stor15178@84255090 08:29 ABOVE) live uf why=floor_bank nUp=1 work=14 surplus=138 floor=15000 allowExtra=20000.
