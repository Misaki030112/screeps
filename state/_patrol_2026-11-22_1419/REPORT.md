# 1h peacetime patrol 2026-11-22 14:28 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_1419
Started: 2026-11-22 14:20:55 +0800
Newest prior: 13:39 _patrol_2026-11-22_1325 finished 13:40:38
Live commit: 2b5398f7 (2026-11-19 02:28). No src change, no deploy this hour.

## Alerts
- ALERT FORMAL W47 upgrade HOLDS — ninth consecutive dual after the 05:38 clearance (07:35 re-fired on the second dual; 08:28 third; 09:29 fourth; 10:33 fifth; 11:27 sixth; 12:31 seventh; 13:39 eighth). exact2h 20.23/30.08=67.3% (prev 19.88=66.1%) still under 70% AND meaningful short last800 19.75=65.7% still soft. last20-100 10 e/t=33.2% span=40 is post-freeze thin and must not clear or fire. last200 17.50=58.2% last300 18.33=60.9% last500 19.82=65.9%; 1h INTERP 19.54=64.9% soft. model_w8 1h alloc upgrade 19.63 stor_delta +3.48 work=30 vs ideal 30.03, 2h alloc 20.23 stor_delta +2.73 work=30. Root remains designed keep=2 (20 e/t=66.5% of ideal). Do not change keep/softCap, do not add a standing third, do not unseal the 40k lock.
- FORMAL ALERT on HOME STAYS CLEARED: exact2h 20.00/26.00=76.9% (prev 21.34=82.1%) still ABOVE 70%. last800 17.03=65.5% and 1h INTERP 17.70=68.1% are the designed 15k-floor nUp=1 period (84415150-84415570) and must not fire. last20-30 28 e/t=107.7% hard. model 1h measured upgrade 17.16 stor_delta -1.83 ticks 810, 2h 19.94 stor_delta -0.18 ticks 1710.
- Storage formal STAYS CLEARED: prev tip 16732 and this tip 15292 both ABOVE 15k; consec-under=0. Mid-hour min 12382@84415160, under from 84415130, recovered 16168@84415440, later 15742@84415760. 20k/300t still unlocked (3h max 18552, n>=20k span=0).
- no formal (c): owned-room critical roles present (miners 2, queens 2-3 handoff, w8fillers 2-3 handoff, w8miners 2, rminers 2-3, reserver 1, reserve7 gap 200t 84414950-84415150 then present; reservation stayed healthy).
- no formal (d): audit exit 2 is known deploy-baseline drift vs 2b5398f7 2026-11-19 02:28, IDENTICAL REGRESSION [deploy] string to the 13:39 and 12:31 patrols. creep_motion --patrol 1h/2h exit 1 known waiting_pickup / target_full / no_task / waiting_feed / queue_blocked / parked_threat. w8rminer swamp source same known watch (w8rminer84414454 1h swamp 157).
- no formal (e): CPU 1h min 14.02 max 20.79@84415570 mean 16.68, 2h min 12.83 max 22.89 mean 16.80, bucket min 10000 later 10000. Live 16.36@84415690 then 13.42-19.58 later / 18.15@84415760 bucket 10000.
- no formal (f): infra ok this run.

## Threat
At 84415078 (~13:40:38) a brief W47 threat stamped w8threat=w8flee=w8inv=84415078. room_stats hostiles=0 on the 10-tick grid, but W47 spawn/extension energy 5600@84415070 -> 3680@84415080 (towers fired) and w8guard84415074 / w8defender84415075 appeared. Live later: all five vis host=0 core=0. Designed sealPark=1 why=threat, threatSoft=1, softCap2=1, bankWhy=threatSoft, w8guard parked 29,5, w8defender 28,5. Do not start commander; no Safe Mode. keep=2, two unboosted 10W w8upgraders seated (84414764 ttl=578 at 12,25 and 84415599 ttl=1413 at 15,31 at q 84415724); tip w8up=3 was handoff, w8up=2 from 84415700.

## Infra / backfill
- services: postgres / views_apache / grafana / listener / dashboard all ok; grafana_check all OK.
- Listener: 1 process pid=2490792 since 14:20:14 parent=4035476, yield_absent=True, peacetime 1-slot 5:5:1:1 (end rot W45N7), no second listener, commander not holding slots, war_cmd/pulse not touched. Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — do not touch.
- Official history backfill --minutes 40: game.time=84415661 published 84414900..84415500, reconstructed 84414901..84415600 (700) inserted=5514 already_in_db=19279 missing_chunks=1 W45N8@84415500 tick_s=4.208 first-pass ts_realigned=0; tick_s_in_use=4.20604 (prev_later) corrective_applied=False nfix=0 still_over_45s=0.
- confirm 14:23:17 gt=84415690 still_404=['W45N8@84415500'] inserted=0; retry2 14:23:38 gt=84415695 still_404 same inserted=0; late retry 14:27:34 gt=84415751 still_404 same inserted=0.
- coverage official window 84414901..84415600: W46N8/W47N8/W45N7/W47N7 700/700, W45N8 600/700 hole 100.
- JP 84415600 at 14:26:58 gt=84415742 all_five_200=True inserted=3114 still_404=[]. Official+JP through 84415700 four rooms 800/800, W45N8 700/800 missing only the leftover 404 hole.
- NEW leftover official 404 W45N8@84415500 (confirm+retry2+late retry still 404; listener 0/100; hole 100 ticks 84415501..84415600) — first told by this 1h patrol.
- Already-told leftover W46N8@84414700 and older remain aged out of window start 84414901, not retried, do not re-tell as new.
- NEW 盒子休眠 13:48:49–13:57:59 (544s, STATS 84415191..84415339 149t, official-filled 149/149 all five, listener restart 13:58:02 python 2481423 started 13:58:12) — first told by this 1h patrol (quietly recorded by the 14:09 backfill).
- NEW 盒子休眠 14:15:32–14:20:01 (269s, STATS 84415571..84415649 79t, official-filled W46N8/W47N8/W45N7/W47N7 79/79, W45N8 49/79 missing 30 ticks 84415571..84415600 due to the leftover 404, listener restart 14:20:04 python 2490792 started 14:20:14) — first told by this 1h patrol.
- NEW short WS none.
- Already-told freezes 13:16:57-13:26:20 and 12:51:44-13:03:45 and 12:20:45-12:23:11 and 11:45:08-12:00:47 and 10:45:15-11:06:19 and older remain already told.

## Other
- ticksToDowngrade 150000/150000, safeModeAvailable 6/6 not activated.
- labs Memory.ops.labs W46N8=KO unchanged; stocks stor O 80800 K 212956 KO 55636; later actOk=1 actGaps= empty; koLab 590.
- r7 on endTime=84418598 by Misaki (was 84417620 last patrol; not touched).
- Home RCL7 9577756/10935000=87.59% later 9579716; W47 6296293/10935000=57.58% later 6297233.
- 40k/500t still unlocked (this-hour-to-tip hist max 31242@84415570, min 25424@84415190, n>=40k=0; already-told earlier 40k touches unlatched 12h/24h max 41133@84406720; upArm=40000 upLatched=0 keep=2 upgCeil=2 w8up on=0).
- No code change and no deploy this hour (src clean, deploy.lock absent, live still 2026-11-19 02:28 code 2b5398f7).
