# 1h peacetime patrol 2026-11-13 19:24 Asia/Hong_Kong

LIVE 4ff78b4 (deploy@84239560 13:26). No src/deploy this hour.

## Alerts
FORMAL (a) holds: home exact2h 13.46/26=51.8% (prev 13.72=52.8%) is 26th consecutive <70%, short also soft (post-thaw last20–300 all 14.00=53.8% — last20–100 only span 20t after the second freeze; last140 span 140; last200 span 200; last300 span 230; 1h 13.60=52.3%). nUp=1 floor_bank almost all hour, brief nUp=2 only 84243790–84243840 18:37–18:41 designed handoff then back to 1.
W47 exact2h 0/30.08 (28th), progress 3150854, keep=1 (minBuild; threatSoft expired this hour, w8threat window from 84242746 ended ~84244246 / ~19:11), do not revert.
Home stor analysis tip 16939 ABOVE consec-under=0 RESET (prev tip 14532 UNDER but later live recrossed, formal (b) was not standing; this hour mid min 13342@84243730 18:33 under15k 18/38=47.4%, later live 17039@84244400 / 16989@84244420 still ABOVE). Formal (b) not standing.
No formal (c)/(d)/(e)/(f).

## Energy / buildings
Authorized sites progressed: home lab 33,22 started 0→3153/50000, 34,20 2751→4253; W47 labs 29,38 32380→45430 nearly done, 28,37 13239→16329, 27,40 1802→2642, 28,38 still 0. minCont 37,44 still 0/5000. Planned road 25,35 finished this hour (sites 9→8); 37,42 still 0/300. siteRem 158149→141049, roadCrit 29→35 (up during freezes / unrepaired decay, watch, not shipped). labsN home still 4 (34,23 structure hits 500).
20k/300t not hit (3h max 16939, best>=20k span=0).
Biggest gaps: home upgrade capped at 14 e/t by 15k floor; W47 upgrade 0 by authorized minBuild. Home 2h remote R net 6.86 / W45N7 net 4.54; W47 1h R1/R2 5.01/6.95 vs ~9.5, same known watch, not shipped.

## Remotes / motion / defence
W45N8/W45N7/W47N7 SAFE vis res 2230/2099/2476 cores0 host0 (stats why=killed leftover on W45N7/W47N7), incidents since last 0, live host 0.
reserve784243352 aged 84243963 at station 39,27 (designed ~600t) during the long freeze start; r7 fell under 2500, replacement reserve784244398 spawned 84244399, walking W47N8 33,34 ttl 586 at 84244423, r7 endTime 84246213→84246897 left≈2476, not (c).
Home reserver84243540 finished the W45N7 walk and aged 84244151 at 6,39 after res recovered; reserver84244049 on W45N8 7,37 ttl 237, reservations 2230/2099 both >RES_SPAWN, not (c).
w8defender84242739 stayed GHOLD 28,5 and aged 84244387 hits 5000 designed, no recycle; live nDef=0.
audit --patrol exit 2 is same known deploy-window metric shift vs 4ff78b4 (hauler waiting_pickup, queen target_full, miner trip, wbuilder cpu), motion --patrol exit 1 waiting_pickup/target_full/no_task/parked_threat/queue_blocked; w8filler ABA is known target_full hub weave, hauler84242991 empty waiting_pickup same known, no new stuck/oscillation after last deploy, not shipped.

## Infra
Two box freezes this hour, both self-healed: 18:42:53–19:04:25 1287s room_stats 300t/1330s 84243860–84244160, listener restart 19:04:28; 19:12:17–19:19:55 457s room_stats 120t/533s 84244250–84244370, listener restart 19:19:58. Also a short listener restart 18:35:24 with room_stats 40t/148s 84243730–84243770 (not in box_pauses). Peacetime single-slot 5:5:1:1 (yield absent, rot i=1 W47N8 at 19:20 left~281s / 19:23 left~106s). Memory.cmd.on=1 at=84224348 stale c={} s={}, commander not live, not touched, not reclaimed. war_cmd/pulse stopped NO_WAR_PROCS.
services.sh all ok postgres/views/grafana200/listener/dashboard200; grafana_check 20/20; q.py live OK (lab/min/soft2 syntax rejected first pass, lab2/min2/opsRem/vis landed); DB writers fresh (room_stats lag ~seconds tip 84244420, creep_ticks few seconds).
40m backfill game.time=84244376 published 84243600–84244200 ticks 84243601–84244300 (700) inserted=6750 already_in_db=19335 ts_realigned=4 tick_s=4.450 missing_chunks=1; retry of W47N8@84243700 still official 404 (also 404 at 19:08 half-hour), remaining hole 84243701–84243800 with 0 live ticks. W46N8/W45N8/W45N7/W47N7 700/700, W47N8 600/700. Unpublished latest ~100t expected. Older official 404s outside this window unchanged (W45N8@84242900, W47N8@84243100, etc.).
CPU 1h avg 17.78 max 20.84@84243800 18:38 p95 20.07 bkt min 10000 now 10000, 2h avg 17.90 max 21.51 leftover@84243390, not (e).
Labs stay OFF (labReady actOk=1 actGaps="" why=ready homeStor 16989, do not enable, do not re-ask). sma 6/6 ttd=150000/129068 not activated.
minerals hsO=17324 termO=126976 termK=151080 W47 termE=1338 termK=56 wsK=64; min line why=minCont (site 37,44 still 0/5000), flipReady=0 flipGaps=already.
Ledger ~2.93h home up 11.56 (undercount) spawn net 14.51 build 5.01; W47 up 0.00 spawn net 14.17 build 23.07.
HOME W46N8 RCL7 57.26% (p6261026 stor16939@84244390 19:21 HKT; later p6261446 stor16989@84244420 19:24) live uf why=floor_bank nUp=1 tUp=1 work=14 surplus=+1989 floor=15000 allowExtra=20000.
W47 stor min 4110@18:22 max 8800@19:04 live 6260–7784 keep=1 phase=minBuild bankWhy=minBuild leanBank=1 threatSoft=0 sealPark on sealMinE=25000 hubReady=1 hubLink=1 feedOk=1 upgCeil=1.
no layout change shipped; no new deploy.
