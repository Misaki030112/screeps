# 1h peacetime patrol 2026-11-22 15:32 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_1521
Started: 2026-11-22 15:23:45 CST
Newest prior: 14:28/14:31 _patrol_2026-11-22_1419 finished 14:30:21
Live commit: 2b5398f7 (2026-11-19 02:28). No src change, no deploy this hour.

## Alerts
- ALERT FORMAL W47 upgrade CLEARS — ninth consecutive dual last hour after the 05:38 clearance (07:35 re-fired on the second dual; then 08:28 3rd, 09:29 4th, 10:33 5th, 11:27 6th, 12:31 7th, 13:39 8th, 14:28/14:31 9th). This hour is no longer a dual: exact2h 20.46/30.08=68.0% (prev 20.23=67.3%) is still under 70%, BUT meaningful short last800 21.68=72.1% is now hard (prev 19.75=65.7% soft). last20-30 20 e/t=66.5% is the designed keep=2 rate and must not hold or re-fire. last70 21.20=70.5% last100 22.52=74.9% last200 23.06=76.7% last300 22.24=73.9% last500 20.68=68.8%; 1h INTERP 21.56=71.7% also above 70% (context only). model_w8 1h alloc upgrade 21.58 stor_delta -5.59 work=20 vs ideal 30.03, 2h alloc 20.47 stor_delta -1.66 work=20. Root remains designed keep=2 (20 e/t=66.5% of ideal). Do not change keep/softCap, do not add a standing third, do not unseal the 40k lock. A later single dual after this clearance does not immediately re-fire (07:35 re-fired on the second dual).
- FORMAL ALERT on HOME STAYS CLEARED: exact2h 20.74/26.00=79.8% (prev 20.00=76.9%) still ABOVE 70%. last800 23.56=90.6% and 1h INTERP 23.74=91.3% hard. last20-30 27.00-27.33 e/t=103.8-105.1% hard. model 1h measured upgrade 23.82 stor_delta -0.99 ticks 850, 2h 20.69 stor_delta -0.84 ticks 1710.
- Storage formal STAYS CLEARED: prev tip 15292 and this tip 15192 both ABOVE 15k; consec-under=0. Mid-hour min 14132@84415880, under from 84415860 (14732), recovered 15232@84415910; nUp=1 84415900-84416250 during that dip (and across the 14:47 freeze), nUp=2 again at 84416250 stor=15252. Later 15292@84416660 15392@84416670 15492@84416680, live 15142@84416685. 20k/300t still unlocked (3h max 18552, n>=20k span=0).
- no formal (c): owned-room critical roles present (miners 2 later handoff 3, queens 2, w8fillers 2, w8miners 2, rminers 2, reserver 1). reserve7 zero 84415770-84416040 (270t) then present; reservation stayed healthy (live 2795 later 2843); not formal (c).
- no formal (d): audit exit 2 is known deploy-baseline drift vs 2b5398f7 2026-11-19 02:28, IDENTICAL REGRESSION [deploy] string to the 14:28 and 13:39 and 12:31 patrols. creep_motion --patrol 1h/2h exit 1 known waiting_pickup / target_full / no_task / waiting_feed / queue_blocked / parked_threat. w8rminer swamp source same known watch (w8rminer84414454 1h swamp 68 / 2h 209; also w8rminer84415806 1h swamp 140).
- no formal (e): CPU 1h min 13.94 max 34.71@84416330 mean 18.03, 2h min 13.94 max 34.71 mean 17.39, bucket min 10000 later 10000. One post-restart spike to 34.71, bucket stayed full, not a persistent drain. Live 17.85@84416650 then 18.79/16.49/18.20 later / 18.51@84416685 bucket 10000.
- no formal (f): infra ok this run.

## Threat / strategy
No new hostiles this hour (room_stats hostiles count 0; live later all five vis host=0 core=0). Already-told brief W47 threat stamp remains w8threat=w8flee=w8inv=84415078. threatSoft=0, softCap2=0, bankWhy=ready, softLeft=0. sealPark=1 why=ok (W47 storE tip 25347, later 24997, near sealMinE=25000), w8guard84415074 parked 29,5, w8defender84415075 at 28,5 (low TTL at the first live snap). Do not start commander; no Safe Mode. keep=2, two unboosted 10W w8upgraders seated (w8upgrader84415599 ttl≈496 at 14,27 and w8upgrader84416203 ttl≈1100 at 14,26, body wwwwwwwwwwcmm). tip/handoff w8up=3 at 84415690 and 84416250, w8up=2 otherwise and at later snap. upArm=40000 upLatched=0 upgCeil=2 w8up on=0.

## Infra / backfill
- services: postgres / views_apache / grafana / listener / dashboard all ok; grafana_check all OK. dashboard :8787 was up (python pid 8041).
- Listener: 1 process pid=2507398 since 15:01:28 parent=4035476, yield_absent=True, peacetime 1-slot 5:5:1:1 (start rot W47N8, end rot W46N8 left=465s at 15:32:48), no second listener, commander not holding slots, war_cmd/pulse not touched. Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — do not touch.
- Official history backfill --minutes 40: first attempt 15:24:48 gt=84416573 died mid-chunk on SSL EOF after ok W47N8@84416000; idempotent retry 15:25:41-15:26:22 exit=0. game.time=84416586 published 84415800..84416400, reconstructed 84415801..84416500 (700) inserted=6271 already_in_db=20408 missing_chunks=0 first-pass 35/35 official GETs 200 tick_s printed 4.220 (exact first 4.21953) ts_realigned=8865. tick_s_in_use=4.18594 (all_mean; later-mean 4.17922) corrective_applied=False nfix=0 still_over_45s vs all_mean=0.
- confirm 15:27:58 skipped no targets inserted=0; retry2 15:27:58 skipped no targets inserted=0; late retry 15:27:59 skipped no targets inserted=0.
- coverage official window 84415801..84416500: all five 700/700, official_404=0.
- JP 84416500 at 15:29:35/15:29:37 gt=84416642 all_five_200=True inserted=2126 still_404=[] ts_realigned=0. Official+JP through 84416600 all five 800/800. Residual missing ticks are only the unpublished latest chunk after 84416600 (expected).
- NEW leftover official 404 none.
- Already-told leftover W45N8@84415500 still 0/100 (hole 84415501..84415600) but aged out of window start 84415801, not retried, do not re-tell as new. Older leftovers W46N8@84414700 and W46N8@84413700 and W47N7@84412400 and W45N7@84411500 and older also aged out.
- NEW 盒子休眠 14:47:50–15:01:16 (797s, STATS 84416041..84416249 209t, official-filled 209/209 all five, listener restart 15:01:19 python 2507398 started 15:01:28) — first told by this 1h patrol (quietly recorded by the 15:09 backfill; verified this run from box_pauses / freeze_clock / official fill).
- NEW short WS none.
- Already-told freezes 14:15:32-14:20:01 and 13:48:49-13:57:59 and 13:16:57-13:26:20 and 12:51:44-13:03:45 and 12:20:45-12:23:11 and 11:45:08-12:00:47 and 10:45:15-11:06:19 and older remain already told. Already-told short interruptions 12:14:21-12:14:56 and 05:25:19-05:27:20 remain already told.

## Other
- ticksToDowngrade 150000/150000, safeModeAvailable 6/6 not activated.
- labs Memory.ops.labs W46N8=KO unchanged; stocks stor O 80800 K 212956 KO 56436; tip actOk=1 actGaps= empty; koLab 245.
- r7 on endTime=84419440 by Misaki (was 84418598 last patrol; not touched).
- Home RCL7 9600522/10935000=87.80% later 9601274 / live 9601414; W47 6316379/10935000=57.76% later 6316979 / live 6317079.
- 40k/500t still unlocked (this-hour-to-tip hist max 30301@84415740, min 24800@84416350, n>=40k=0; later 25347 then 24997@84416680 / 24997@84416685; already-told earlier 40k touches unlatched 12h/24h max 41133@84406720; upArm=40000 upLatched=0 keep=2 upgCeil=2 w8up on=0).
- Home nUp=2 at start of hour (from last tip), nUp=1 84415900-84416250 during the mid-hour storage dip, nUp=2 from 84416250 and at later snap why=ok.
- No code change and no deploy this hour (src clean, deploy.lock absent, live still 2026-11-19 02:28 code 2b5398f7).
