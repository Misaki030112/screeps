# 1h peacetime patrol 2026-11-13 18:26 Asia/Hong_Kong

LIVE 4ff78b4 (deploy@84239560 13:26). No src/deploy this hour.

## Alerts
FORMAL (a) holds: home exact2h 13.72/26=52.8% (prev 14.06=54.1%) is 25th consecutive <70%, short also soft (post-thaw last20 14.00=53.8% — last20–140 only span 20t after the second freeze; last200 13.91=53.5%; last300 12.89=49.6% after brief feed dips 10.8/1.4 e/t @18:03 and 9.4/2.8 @18:06; 1h 13.32=51.2%). nUp=1 floor_bank all hour, no handoff.
W47 exact2h 0/30.08 (27th), progress 3150854, keep=1 (minBuild + threatSoft from last-hour Invader, w8threat=84242746), do not revert.
Home stor analysis tip 14532 UNDER would have been consec-under=2 (prev tip 10364 UNDER consec-under=1 FIRST). Mid-hour recovered over15k 84243330 18:03 max 16104@84243380 18:07, then after the second freeze 14332@84243570 18:21; later live recrossed 15722@84243630 18:25 / 15582@84243640 18:26 still ABOVE, formal (b) not standing at log time.
No formal (c)/(d)/(e)/(f).

## Energy / buildings
Milestone: W47 lab 27,39 completed this hour (structure hits 500 by 18:00 thaw; was 49192/50000 at 17:31; W47 sites 7→6 at 84243290). Remaining W47 labs 29,38 22480→32380, 28,37 9549→13239, 28,38 still 0, 27,40 0→1802. Home labs 34,20 531→2751, 33,22 still 0 (labsN=4 home). minCont 37,44 still 0/5000. Planned roads 18,48 / 14,28 / 33,34 finished early this hour; new road 25,35 0/300; 37,42 still 0/300. siteRem 174859→158149, roadCrit 30→29.
20k/300t not hit (3h max 16772, best>=20k span=0).
Biggest gaps: home upgrade capped at 14 e/t by 15k floor (stor only just recrossed); W47 upgrade 0 by authorized minBuild. Home 2h remote R 4.65 vs net 6.86; W47 1h R1/R2 5.53/6.50 vs ~9.5, watch, not shipped.

## Remotes / motion / defence
W45N8/W45N7/W47N7 SAFE vis res 2432/1923/2586 cores0 host0, incidents since last 0, live host 0.
reserve784242308 aged ~17:33 (designed 600t), replacement reserve784243352 spawned 84243352 after r7 fell under 2500, on station 39,27 ttl 327, r7 endTime 84245699→84246213 left≈2592>2500, not (c).
Home reserver always present in traces (mincount 1); reserver84243540 walking W45N7 11,15 ttl 515 after W45N7 res dropped under RES_SPAWN, W45N8 2432>RES_SPAWN, not (c).
w8defender84242739 born ~84242889, reached GHOLD 28,5 at 84242962, parked_threat ttl 767, designed, no recycle.
audit --patrol exit 2 is same known deploy-window metric shift vs 4ff78b4 (hauler waiting_pickup, queen target_full, miner trip, wbuilder cpu), motion --patrol exit 1 waiting_pickup/target_full/no_task/waiting_feed/queue_blocked/parked_threat; w8filler ABA is known target_full hub weave, hauler84241522/84242991 empty at 35,29/33,29 same known waiting_pickup, not shipped.

## Infra
Two box freezes this hour, both self-healed: 17:34:43-18:00:22 ~1538s room_stats 360t/1575s 84242930-84243290, listener restart 18:00:25; 18:08:59-18:20:46 ~702s room_stats 170t/753s 84243400-84243570, listener restart 18:20:49. Peacetime single-slot 5:5:1:1 (yield absent, rot i=1 W47N8 at 18:22 left~496s / 18:26 left~236s). Memory.cmd.on=1 at=84224348 stale c={} s={}, commander not live, not touched, not reclaimed. war_cmd/pulse stopped NO_WAR_PROCS.
services.sh all ok postgres/views/grafana200/listener/dashboard200; grafana_check 20/20; q.py live OK (lab/min/soft2 syntax rejected first pass, lab2/min2/w8th/resv2 landed); DB writers fresh (room_stats lag ~15s tip 84243640, creep_ticks few seconds).
40m backfill game.time=84243576 published 84242800-84243400 ticks 84242801-84243500 (700) inserted=12385 already_in_db=15124 ts_realigned=60 tick_s=4.427 missing_chunks=2; retry of W45N8@84242900 and W47N8@84243100 still official 404 (also 404 at 18:04 half-hour), remaining holes 84242901-84243000 and 84243101-84243200 with 0 live ticks (inside the first freeze). W46N8/W45N7/W47N7 700/700, W45N8/W47N8 600/700. Unpublished latest ~100t expected.
CPU 1h avg 18.09 max 21.51@84243390 18:08 p95 20.39 bkt min 10000 now 10000, 2h avg 17.67 max 25.39 leftover@84242000, not (e).
Labs stay OFF (labReady actOk=0 actGaps=homeStor at Memory 14422, later stor 15582, do not enable, do not re-ask). sma 6/6 ttd=150000/129854 not activated.
minerals hsO=17324 termO=126976 termK=151080 W47 termE=1338 termK=56 wsK=64; min line why=minCont (site 37,44 still 0/5000), flipReady=0.
Ledger ~2.93h home up 11.68 (undercount) spawn net 13.58 incl sp:w8defender=2.09 build 7.00; W47 up 0.00 spawn net 14.22 build 22.09.
HOME W46N8 RCL7 57.16% (p6250148 stor14532@84243590 18:22 HKT; later p6250848 stor15582@84243640 18:26) live uf why=floor_bank nUp=1 tUp=1 work=14 surplus=-378 then stor ABOVE floor=15000 allowExtra=20000.
W47 stor min 3288@18:05 max 6022@17:34 live 4110-5746 keep=1 phase=minBuild bankWhy=minBuild leanBank=1 threatSoft=1 sealPark on sealMinE=25000 hubReady=1 hubLink=1 feedOk=1 upgCeil=1.
no layout change shipped; no new deploy.
