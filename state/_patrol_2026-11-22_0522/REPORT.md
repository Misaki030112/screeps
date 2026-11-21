# 1h peacetime patrol 2026-11-22 05:22 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_0522
Previous: state/_patrol_2026-11-22_0422 (04:22 / delivered ~04:33, TIP 84407020, later live 84407066 / room_stats 84407060)
Live code: 2b5398f7 (2026-11-19 02:28). No src change, no deploy.lock, no game deploy.
Analysis TIP 84407980 at 2026-11-22 05:32:47 +08. Later live 84408039 ~05:36:43, later room_stats to 84408050 05:37:31.

## Alerts

FORMAL ALERT HOLDS on HOME upgrade — third consecutive dual after the 02:34 recovery (last patrol FIRED as the second consecutive dual).
- exact2h 15.37/26.00=59.1% (prev 13.16=50.6%) still under 70%
- meaningful short last800 16.49=63.4% still soft
- 1h INTERP 16.10=61.9%, last1500 15.97=61.4%, last500 18.60=71.5% just above, last300 21.69=83.4%
- last20-100 28.00 e/t=107.7% are nUp=2 after storage recovered above the 15k floor and must not be used to fire or to clear; the hold is the exact2h + last800 dual, not those short recovered samples
- last140/200 28.00=107.7% (post-05:23 restart samples only)
- model 1h measured upgrade 16.14 stor_delta +7.92; 2h measured upgrade 15.38 stor_delta +2.10; upgrader_bound energy, work=28 vs ideal 26
- Root is the designed 15k floor holding nUp=1 (why=floor_bank) for the first part of this hour, plus two box-freeze STATS holes and one short listener interruption. nUp=1 from last tip 84407020 stor=12910 through 84407550, 2@84407560-84407640, 1 again 84407650-84407840 (still above 15k; overlaps the 05:17 freeze), then 2 from 84407850 through tip and later. Live later two unboosted 14W upgraders at 84408006; nUp=2 why=ok storE=18694@84408039-84408040. Do not change the 15k floor. Do not add a standing third.

FORMAL W47 upgrade CLEARS — no longer a dual after thirty-seven consecutive duals since the 12:25 clearance.
- exact2h 20.17/30.08=67.0% (prev 19.77=65.7%) still under 70%
- meaningful short last800 21.11=70.2% is no longer soft (21.11/30.08=70.18%)
- last20-500 21.86-26.00 e/t=72.7-86.4% are also above 70%, not the designed keep=2 20.00 e/t=66.5% soft window, so they do not block this clear
- last1500 20.08=66.8% still under; 1h INTERP 20.96=69.7% just under. Clear follows the dual rule (exact2h back above 70% OR meaningful last800 no longer soft), not last1500
- model_w8 1h alloc upgrade 21.03 stor_delta -4.03 ticks 870 work=20 vs ideal 31; 2h alloc 20.24 stor_delta -1.14 ticks 1750 work=20
- Root of the long hold was designed keep=2 (20 e/t=66.5% of ideal). last800 has now edged above 70%. Do not change keep/softCap, no standing third, do not unseal the 40k lock.
- Re-fire only when a later patrol is again a dual (exact2h under 70% AND meaningful last800 also soft). last20-500 designed keep=2 20 e/t must not fire or clear.
- 40k/500t still unlocked: this hour W47 stor max 30074@84407020 (start of window) min 24537@84407590, never reached 40k. Last observed >=40k remains 84406720-84406790 (70 ticks, max 41133@84406720 04:06:53) already told last hour; even the optimistic hole-inclusive span was 360 < 500. 24h max still 42468@84390960 (already-known unlatched; prior best span 460-461 < 500). upArm=40000 upLatched=0 keep=2 upgCeil=2.
- W47 stor this hour 30074@last tip -> min 24537@84407590 -> 25035@tip and later still 25035@84408039-84408050. sealPark=1 why=threat / threatSoft=1 softCap2=1 bankWhy=threatSoft is the designed linger after the already-told W47N7 invader (w8threat=84407010), not a policy change. sealMinE=25000 unchanged. keep=2, two w8upgraders (ttl 497 and 1101 at 84408006), not a standing third.

FORMAL storage-floor STAYS CLEAR. Last tip 12910 was the FIRST under (consec-under=1, did not fire). This tip 19244 is back ABOVE 15k, so consec-under=0, does not fire.
- This hour home stor min 12152@84407120 04:34:25, under15k 20/57=35.1% of since-last samples, crossed back over 15k at 84407500 05:00:02 (15258). Tip 19244@84407980 05:32:47; later 18544@84407990 then 18794@84408050; live 18694@84408039. Do not change the 15k floor.
- 20k/300t still unlocked: 3h max 20870, best >=20k tick-span=90 < 300.

No (c) formal for a lasting missing critical role: miner/rminer/queen/w8filler present throughout. Reserver was 0 for 140 ticks 84407020-84407160 (04:27:39-04:37:08) immediately after the already-told W47N7 invader kill (spawn busy with defenders); reservations stayed healthy and a reserver is present from 84407170 through tip and later. Flagged in the user log, not treated as a new shippable spawn bug this hour.

No (d) new stuck/oscillation. creep_audit --patrol rc=2 is the known REGRESSION [deploy] vs live 2b5398f7, same class, not alert (d). creep_motion --patrol 1h/2h rc=1 known waiting_pickup / target_full / waiting_feed / queue_blocked / no_task / parked_threat. w8rminer swamp source is the same known watch. W47 src_A link artifact 2h 0.06 / 1h unmeasured is the same known accounting quirk (was 0.00 last hour). Pattern did not change.

No (e) CPU issue: 1h mean 17.64 max 25.04 bucket min 9998 / live 10000.
No (f) infra down: postgres/grafana/listener/dashboard up; grafana_check all OK; analysis tools ran.

## Remotes

W45N8 / W45N7 / W47N7 all visible, SAFE, host=0, core=0. Later reservation ticksToEnd ~2202 / 2364 / 3289 (earlier this run 2239 / 2327 / 3326). Leftover defender rdef84406797 still in W47N7 (hits 5000, ttl 447 at 84407999) from the already-told 04:12 invader; do not re-tell as a new incident. Do not start 指挥官 or Safe Mode.

## Backfill / coverage / freezes / official 404s

Official 40m backfill ticks 84407101..84407800 (700, published_bases 84407100..84407700 at game.time=84407892, tick_s=4.093, tick_s_in_use=4.09301, ts_realigned_first=0, corrective=0) missing_chunks=1 W45N8@84407700; already_in_db=19414 inserted first=6541; confirm 05:31:59 gt=84407969 / retry2 05:32:05 gt=84407970 / late 05:33:10 gt=84407986 / post_jp 05:36:43 gt=84408038 still_404 W45N8@84407700 inserted=0. Just-published 84407800 at 05:32:22 gt=84407974 all_five_200=True inserted=3181 (W46N8 601, W47N8 1314, W45N8 297, W45N7 477, W47N7 492). Official window plus just-published covers through 84407900 except the leftover 404 hole W45N8@84407700 (84407701..84407800). Coverage first-pass official_recovered=3400/3500 empty_no_creep=0 official_404=100. JP chunk 84407801..84407900 all five 100/100.

NEW leftover official 404s (not yet told; fold into this 1h patrol USER_LOG):
- W46N8@84407000 (from the 05:12 half-hour; aged out of this 40m window start 84407101; re-confirmed 05:32:10 gt=84407971 still 404; listener 85/100 84407016..84407100; hole 15 ticks 84407001..84407015)
- W45N8@84407700 (new in this first pass; confirm/retry2/late/post_jp still 404; listener 0/100; hole 100 ticks 84407701..84407800)

Already-told leftovers W45N8@84406400 (0/100), W46N8@84406600 (0/100), W46N8@84406700 (40/100), W45N7@84403800 / W45N7@84403700 / W45N7@84400400 / W45N7@84400300 / W47N8@84400100 aged out of this 40m window, not retried as new, do not re-tell.

NEW box freezes (not yet told):
- 盒子休眠 04:41:06-04:59:17 (1086s; already healed; STATS 84407211..84407499, 289t; official-filled ALL FIVE 289/289; first-pass official covers the whole freeze through 84407500 and does not overlap W46N8@84407000; listener auto-restart 04:59:20, python 2264003 started 04:59:30)
- 盒子休眠 05:17:11-05:23:17 (361s; already healed; STATS 84407741..84407849, 109t; official-filled W46N8 109/109, W47N8 109/109, W45N7 109/109, W47N7 109/109, W45N8 49/109 — first-pass covers 84407741..84407800 except leftover 404 W45N8@84407700 (0/60); just-published tail 84407801..84407849 all five 49/49; listener auto-restart 05:23:20, python started ~05:23:30)

NEW short listener interruption (not a box freeze; no box_pauses row):
- 监听短中断 05:25:19-05:27:20 (last STATS 84407870 at 05:25:19, next 84407900 at 05:27:20, ~121s; missed samples 84407880 and 84407890, hole 29 ticks 84407871..84407899; listener auto-restart 05:26:38, python 2274875 started 05:26:47; just-published official-filled ALL FIVE 29/29)

Already-told freezes 03:47:58-04:06:12 and 04:18:46-04:22:28 (and older 02:44 / 02:13 / 01:50 / 01:18 / 00:50 / 00:11 / 23:53 and older) remain already told; do not re-tell.

Listener healthy at end: 1 process (2274875 since 05:26:47, parent run_listener.sh 4035476 since Nov 13), yield_absent=True, peacetime 1-slot 5:5:1:1, no second listener, war_cmd/pulse not touched. Console replies did not stall after the 05:26 restart; listener was not manually restarted.

## Other

labs KO mode=KO (actOk=1 actGaps= empty this hour after homeStor recovered; last hour actOk=0 actGaps=homeStor). Never unset Memory.ops.labs. sma=6/smaW=6 ttd=150000 both never activated; sites=0.
mineral home stor O/K/KO 85200/217356/51636 term O/K 3000/3000, koLab 730; W47 term E 1284 K 52.
r7 on endTime=84411330 by Misaki (was 84409268 last patrol; not touched this hour).
Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — do not touch.
W47 src_A link artifact 0.06/— ; src_B 2h/1h 9.14/7.91, R1 6.15/5.82, R2 7.35/5.73.
Critical roles present at tip and later (miner 2, rminer 2, queen 2, w8filler 2, reserver 1, w8miner 2).
LIVE still 2b5398f7 (deploy 2026-11-19 02:28, no new game deploy this patrol). No src/ change. No code change and no deploy this hour (src clean, deploy.lock absent, live still 2026-11-19 02:28 code 2b5398f7).
