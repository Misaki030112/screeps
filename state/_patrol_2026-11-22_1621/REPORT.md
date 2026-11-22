# 1h peacetime patrol 2026-11-22 16:32 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_1621
Started: 2026-11-22 16:22:54 CST
Newest prior: 15:32/15:34 _patrol_2026-11-22_1521 finished 15:34:21
Live commit: 2b5398f7 (2026-11-19 02:28). No src change, no deploy this hour.

## Alerts
- FORMAL W47 upgrade STAYS CLEARED — 15:32 cleared after the ninth consecutive dual following the 05:38 clearance (exact2h then 20.46=68.0% under BUT last800 21.68=72.1% hard). This hour is a dual, but it is the FIRST after clearance and does not re-fire (07:35 re-fired on the second dual): exact2h 20.80/30.08=69.1% (prev 20.46=68.0%) is still under 70%, AND meaningful short last800 20.05=66.6% is soft again (prev 21.68=72.1% hard). last20-30 24.50-25.00 e/t=81.4-83.1% is the post-freeze short burst and must not fire or hold; last70-200 also look hard for the same reason; last500 20.07=66.7% last800 20.05=66.6% last1500 20.74=69.0% are soft or designed keep=2. 1h INTERP 20.04=66.6% is context only. model_w8 1h alloc upgrade 20.04 stor_delta +1.64 work=20 vs ideal 30.03, 2h alloc 20.80 stor_delta -2.06 work=20. Root remains designed keep=2 (20 e/t=66.5% of ideal). Do not change keep/softCap, do not add a standing third, do not unseal the 40k lock. If the next patrol is also a dual, the formal alert will re-fire.
- FORMAL ALERT on HOME STAYS CLEARED: exact2h 21.10/26.00=81.2% (prev 20.74=79.8%) still ABOVE 70%. last800 18.23=70.1% and 1h INTERP 18.97=73.0% are at/above 70%. last20-200 13.56-14.00 e/t=52.2-53.8% is the 15k floor nUp=1 14 e/t and must not fire. model 1h measured upgrade 18.89 stor_delta -0.11 ticks 860, 2h 21.06 stor_delta +0.16 ticks 1720.
- Storage formal STAYS CLEARED: prev tip 15192 and this tip 15914 both ABOVE 15k; consec-under=0. Mid-hour min 13652@84417170 16:05:59, under15k=20/71=28.2% with several brief dips (first under 14892@84416740 15:36:25); nUp=1 from 84417170 through the tip (why=floor_bank). Later 16014@84417480 16114@84417490 16214@84417500 16314@84417510 15864@84417520 16034@84417530 15834@84417540 15934@84417550, live 16314@84417509, all ABOVE. 20k/300t still unlocked (3h max 17882, n>=20k span=0).
- no formal (c): owned-room critical roles present (miners 2, queens 2, w8fillers 2-3 handoff, w8miners 2, rminers 2-3, reserver 2). reserver zero 120t 84416780-84416900 then present; reserve7 zero 430t 84416790-84417220 then present; reservations stayed healthy (live 2402/2142/2559 later 2458/2198/2615); not formal (c).
- no formal (d): audit exit 2 is known deploy-baseline drift vs 2b5398f7 2026-11-19 02:28, IDENTICAL REGRESSION [deploy] string to the 15:32 and 14:28 and 13:39 patrols. creep_motion --patrol 1h/2h exit 1 known waiting_pickup / target_full / no_task / waiting_feed / queue_blocked / parked_threat. w8rminer swamp source same known watch (w8rminer84415806 1h swamp 166; also w8rminer84414454 2h swamp 61 and w8rminer84417245 1h swamp 13).
- no formal (e): CPU 1h min 14.5 max 34.94@84416800 15:40:31 mean 17.92 p95 21.34, 2h min 13.94 max 34.94 mean 17.97, since_last n=71 mean 17.98 bucket min 9997 later 10000. One spike to 34.94 (and 31.00@84417180), bucket stayed full, not a persistent drain. Live 15.82@84417432 then 17.31@84417509 / later 16.37-22.27 bucket 10000.
- no formal (f): infra ok this run.

## Threat / strategy
No new hostiles this hour (room_stats hostiles count 0; live later all five vis host=0 core=0). Already-told brief W47 threat stamp remains w8threat=w8flee=w8inv=84415078. threatSoft=0, softCap2=0, bankWhy=ready, softLeft=0. sealPark=1 why=ok (W47 storE tip 26754, later 26754 then 25554@84417550, still above sealMinE=25000). Last hour's parked w8guard84415074 / w8defender84415075 expired (last nonzero 84416720, low TTL already noted at 15:32); none present at the later snap. Do not start commander; no Safe Mode. keep=2, two unboosted 10W w8upgraders seated (w8upgrader84416203 ttl≈264 at 14,26 and w8upgrader84417038 ttl≈1099 at 12,25, body wwwwwwwwwwcmm). w8up=3 only as handoff overlap at 84417040, otherwise 2; w8up on=0. upArm=40000 upLatched=0 upgCeil=2.

## Infra / backfill
- services: postgres / views_apache / grafana / listener / dashboard all ok; grafana_check all OK. dashboard :8787 was up (python pid 8041).
- Listener: 1 process pid=2548139 since 16:22:22 parent=4035476, yield_absent=True, peacetime 1-slot 5:5:1:1 (start rot W45N8, end rot W46N8 left=225s at 16:32:41), no second listener, commander not holding slots, war_cmd/pulse not touched. Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — do not touch.
- Official history backfill --minutes 40: first pass 16:23:29-16:24:50 exit=0, no retry needed. game.time=84417422 published 84416700..84417300, reconstructed 84416701..84417400 (700) inserted=6668 already_in_db=19882 missing_chunks=0 first-pass 35/35 official GETs 200 tick_s printed 4.097 (exact first 4.09735) ts_realigned=2998. tick_s_in_use=4.16269 (all_mean; later-mean 4.17576) corrective_applied=False nfix=0 still_over_45s vs all_mean=0.
- confirm 16:27:07 skipped no targets inserted=0; retry2 16:27:07 skipped no targets inserted=0; late retry 16:27:07 skipped no targets inserted=0.
- coverage official window 84416701..84417400: all five 700/700, official_404=0.
- JP 84417400 at 16:31:42 gt=84417540 all_five_200=True inserted=3573 still_404=[] ts_realigned=0. Official+JP through 84417500 all five 800/800. Residual missing ticks are only the unpublished latest chunk after 84417500 (expected).
- NEW leftover official 404 none.
- Already-told leftover W45N8@84415500 and older remain aged out of window start 84416701, not retried, do not re-tell as new.
- NEW 盒子休眠 16:15:02–16:22:09 (423s, STATS 84417291..84417409 119t wall 16:14:20–16:22:41, official-filled 110/110 through 84417400 plus JP tail 9/9 84417401..84417409, all five 119/119; listener auto-restart 16:22:13, python 2548139 started 16:22:22) — first told by this 1h patrol.
- NEW short WS 监听短中断 16:02:42-16:02:55 (WS ping/pong timed out, no box_pauses row; STATS 84417111..84417129, 19t, one missed 10-tick sample 84417120; official-filled all five 19/19; listener auto-restart 16:02:46, python 2540965 started 16:02:55, later replaced by the 16:22 freeze restart) — recorded by the quiet 16:12 half-hour and first told in this 1h user log.
- Already-told freezes 14:47:50-15:01:16 and 14:15:32-14:20:01 and 13:48:49-13:57:59 and 13:16:57-13:26:20 and 12:51:44-13:03:45 and 12:20:45-12:23:11 and 11:45:08-12:00:47 and 10:45:15-11:06:19 and older remain already told. Already-told short interruptions 12:14:21-12:14:56 and 05:25:19-05:27:20 remain already told.

## Other
- ticksToDowngrade 150000/150000, safeModeAvailable 6/6 not activated.
- labs Memory.ops.labs W46N8=KO unchanged; stocks stor O 80000 K 213808 KO 56436 (term O/K 3000/3000 plus minor GO/ZH/UH); tip actOk=1 actGaps= empty; koLab 665.
- r7 on endTime=84420060 by Misaki (was 84419440 last patrol; not touched).
- Home RCL7 9615666/10935000=87.93% later 9616786 / live 9616212; W47 6332815/10935000=57.91% later 6334697 / live 6333829.
- 40k/500t still unlocked (this-hour-to-tip hist max 28454@84417410, min 24099@84416790, n>=40k=0; later 26754 then 25554@84417550; already-told earlier 40k touches unlatched; upArm=40000 upLatched=0 keep=2 upgCeil=2 w8up on=0).
- Home nUp=2 at start of hour (from last tip), nUp=3 only 84416730-84416810 as hatch overlap, nUp=2 until 84417170, nUp=1 from 84417170 (stor=13652) through later snap why=floor_bank.
- w8 src_A model harvest 1h 0.16 / 2h 0.33 is the same known measurement/attribution artifact — w8miners were seated.
- No code change and no deploy this hour (src clean, deploy.lock absent, live still 2026-11-19 02:28 code 2b5398f7).
