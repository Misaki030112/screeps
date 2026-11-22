# Patrol 2026-11-22 09:18 (delivered ~09:29 Asia/Hong_Kong)

Folder: state/_patrol_2026-11-22_0918
Started: 2026-11-22 09:19:46 CST
Analysis tip: 84411380 at 2026-11-22 09:24:53.721282+08 stor 13962/35748
Later room_stats: 84411420 at 09:27:39 stor 15858/35748
Live commit: 2b5398f7 (deploy 2026-11-19 02:28). No src change, no deploy this hour.

## Alerts
- FORMAL W47 upgrade HOLDS — fourth consecutive dual after the 05:38 clearance (07:35 re-fired on the second dual; 08:28 was the third). exact2h 20.03/30.08=66.6% (prev 20.19=67.1%) under AND meaningful short last800 20.34=67.6% still soft. last20-140 designed keep=2 ~14.5-20.3 e/t=48-67% must not clear. Do not change keep=2 / no standing third / 15k floor / 40k lock. Re-clear only when a later patrol is no longer a dual.
- Home formal STAYS CLEARED: exact2h 23.63/26=90.9% ABOVE 70%. last800 24.09=92.6% and 1h 23.60=90.8% are context only. last20-30 14 e/t is the 15k floor (nUp=1) and must not fire.
- Storage formal STAYS CLEAR: prev tip 15004 ABOVE; this tip 13962 UNDER is the first under-at-tip after clearance (consec-under does not fire). Later recovered 15358@84411410 / 15858@84411420. Do not change the 15k floor.
- no formal (c): owned-room critical roles present at tip (miners 2, queens 2, w8fillers 2, w8miners 2, rminers 2). Home reserver gap 270t 84411040-84411310 (09:01-09:20) then replacement reserver84411311 in W45N8; W45N7 res 1904 still healthy. reserve7 zero 84410500-84410880 (380t) then present; reservation stayed healthy. Not formal (c) (same treatment as last patrol's reserve7 200t / home reserver 90t).
- no formal (d): no new stuck/oscillation. audit exit 2 is known deploy-baseline drift vs 2b5398f7 2026-11-19 02:28, IDENTICAL REGRESSION [deploy] string to the 08:28 patrol. creep_motion --patrol 1h/2h exit 1 known waiting_pickup / target_full / no_task / waiting_feed / queue_blocked / parked_threat. w8rminer swamp source same known watch (w8rminer84410392 1h swamp 177).
- no formal (e): CPU 1h min 14.01 max 21.59@84410520 mean 16.81, 2h min 14.01 max 29.75@84409680 (already-known earlier peak) mean 17.26, bucket min 9993 later 10000. Live 16.71@84411380 then 15.79@84411420 bucket 10000.
- no formal (f): infra ok this run (pg/grafana:200/dashboard:200/listener single-slot 5:5:1:1 rot W47N8 at 09:28, grafana_check ok, commander not holding slots, Memory.cmd c empty). Official history backfill --minutes 40 succeeded.

## W47 threat (notable, not a lettered formal)
At 84410850 08:48:46 W47N8 hostiles=1 for one room_stats sample; energy 5600→3680 (towers fired) then 4780@84410860 08:49:24 host=0 and 5600@84410880. w8guard84410842 spawned and later parked 29,5 (parked_threat). Live 84411393 all five vis host=0 core=0. Designed reaction still on: w8threat=w8flee=w8inv=84410850, sealPark=1 why=threat, threatSoft=1, softCap2=1, bankWhy=threatSoft, upgKeep=2, upgCeil=2, upLatched=0, upArm=40000. Do not start commander; no Safe Mode sma=6/6 ttd=150000; do not change seal/softCap/keep. This is designed reaction, not a policy change.

## Energy
- Home model 1h measured upgrade 23.56 stor_delta -1.20 ticks 870; 2h 23.80 stor_delta -1.00 ticks 1730. exact2h 23.63=90.9%. nUp=1 at tip (floor); nUp=3 84411300-84411340 handoff, nUp=2 from 84411340, nUp=1 from 84411370. 20k/300t still unlocked (3h max 18298, span=0).
- W47 model_w8 1h alloc upgrade 19.51 stor_delta +12.05 ticks 870 work=20 vs ideal 30.03; 2h alloc 20.03 stor_delta +4.16 ticks ~2h work=20. Root remains designed keep=2 (20 e/t=66.5% of ideal), plus this hour's brief threat / sticky sealPark. Do not change keep / add a standing third / unseal the 40k lock. 40k/500t still unlocked (this-hour max 36252@84411040, n>=40k=0; 8h/24h already-told earlier 40k touches unlatched).
- model_w8 src_A actual 0.0 is a measurement attribution artifact: w8miner84409631 sat 26,11 through 84411300 and replacement w8miner84411063 arrived 26,11 from 84411193 (handoff). w8miner count stayed 2 all hour.

## Remotes / labs / r7
Live SAFE cores 0 host 0 res 2120/1904/2773 (by Misaki), sites=0. labs Memory.ops.labs W46N8=KO unchanged; stocks O 83600 K 215756 KO 53236; later actOk=0 actGaps=homeStor is designed 15k KO act gate. r7 on endTime=84414192 by Misaki (was 84413428 last patrol; not touched). Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — do not touch. war_cmd/pulse stay stopped.

## Infra / backfill
- services.sh: postgres/views/grafana/listener/dashboard all ok.
- Listener: 1 process python 2371673 since 09:19:17, parent run_listener.sh 4035476 since Nov 13, yield_absent=True, peacetime 1-slot 5:5:1:1, rot W47N8 at 09:28:46 left 240s, no second listener, war_cmd/pulse not touched.
- Official history --minutes 40: game.time=84411311 published 84410600..84411200, reconstructed 84410601..84411300 (700) inserted=5417 already_in_db=18221 missing_chunks=1 W47N7@84411200 tick_s=4.017 first-pass ts_realigned=7354. tick_s_check: tick_s_in_use=4.08228 (span_mean), corrective_applied=False, over45 vs span_mean=0. confirm 09:23:59 gt=84411366 recovered W47N7@84411200 inserted=553 still_404=[]. Official coverage 84410601..84411300 all five 700/700. JP 84411300 at 09:29:21 gt=84411441 all_five_200=True inserted=2300 still_404=[]. Official+JP through 84411400 all five 100/100.
- NEW leftover official 404s: none.
- Already-told leftovers W47N8@84409800 / W46N8@84408300 / W47N8@84408300 / W47N7@84407900 / W45N8@84407700 / W46N8@84407000 and older aged out of window start 84410601, not retried, do not re-tell as new.
- NEW 盒子休眠 08:51:14–09:01:02 (581s, already healed; STATS 84410881..84411039 159t, official-filled 159/159 all five; listener auto-restart 09:01:06) — first told by this 1h patrol (quietly recorded by the 09:09 backfill).
- NEW 盒子休眠 09:14:15–09:19:05 (283s, already healed; STATS 84411221..84411299 79t, official-filled 79/79 all five; listener auto-restart 09:19:08, python 2371673 started 09:19:17) — first told by this 1h patrol.
- Older already-told freezes 07:44:22-08:02:42 and 07:20:32-07:26:28 and 06:50:03-07:02:08 remain already told. No new short WS beyond the freezes.
- ticksToDowngrade 150000/150000, safeModeAvailable 6/6 not activated.
- No code change and no deploy this hour (src clean, deploy.lock absent, live still 2026-11-19 02:28 code 2b5398f7).
