# 1h peacetime patrol 2026-11-22 01:31 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_0121
Previous: state/_patrol_2026-11-22_0022 (00:35, TIP 84403680, t508s3599)
Live code: 2b5398f7 (2026-11-19 02:28). No src change, no deploy.lock, no game deploy.
Analysis TIP 84404430 at 2026-11-22 01:26:18 +08. Later live 84404492 ~01:31.

## Alerts

FORMAL W47 upgrade HOLDS — thirty-fourth consecutive dual after the 12:25 clearance.
- exact2h 18.56/30.08=61.7% (prev 19.35=64.3%) still under 70%
- meaningful short last800 17.43=57.9% still soft
- last20 designed keep=2 20.00 e/t=66.5% must not clear
- last30–200 just-touch ~71–77% must not clear
- last300 18.21=60.5%, last500 17.04=56.6%, last1500 18.40=61.2%, 1h INTERP 17.52=58.3% all soft
- model_w8 1h alloc upgrade 17.49 stor_delta +9.63 ticks 820 work=20 vs ideal 30.03; 2h alloc 18.55 stor_delta +0.6 ticks 1650 work=20
- Root remains designed keep=2 (20 e/t=66.5% of ideal). Do not change keep/softCap, no standing third, do not unseal the 40k lock.
- Re-clear only when a later patrol is no longer a dual (exact2h back above 70% or meaningful last800 no longer soft).
- 40k/500t still unlocked: this-hour/3h max 36109 @84404460–84404490 (later live 36109), 12h max 38748@84400220 20:24, 24h max 42468@84391000 (already-known first 40k touch, unlatched; n>=40k in 24h is old samples). upArm=40000 upLatched=0 keep=2 upgCeil=2.
- Live later two unboosted 10W w8upgraders seated 14,26 ttl=333 e=20 and 12,25 ttl=1168 e=30 (bodies wwwwwwwwwwcmm, no boost). w8up=2 throughout (brief w8filler=3 at 84404090 was handoff).
- threatSoft=0, bankWhy=ready, softCap2=0. sealPark/w8sealPark now 0 why=ok (was 1 last patrol); do not force-reseal. W47 RCL7 6072500/10935000=55.53% later.

FORMAL ALERT does NOT fire on HOME: exact2h 16.50/26.00=63.5% (prev 22.48=86.5%) is the FIRST under after clearance. Short is also soft (last20–500 designed floor_bank 14.00 e/t=53.8%; last800/1h 13.01=50.0%; last1500 16.61=63.9%) but a first-under does not fire. Root is the locked 15k floor: nUp=1 why=floor_bank throughout since last tip (work=14). Live later one unboosted 14W upgrader84403127 seated 31,30 ttl=220 at 84404457 (still nUp=1 later). Do not change the 15k floor. Next patrol will fire home formal only if exact2h stays under 70% AND meaningful short remains soft.

FORMAL storage-floor STAYS CLEAR: last patrol ended ABOVE; this tip 16128 >=15000, later 16618/live 16668 still above. consec-under=0. Intra-hour unders recovered: 14620@84403720 then 15220@84403740; min 14264@84403900 00:48; after 00:50 freeze 14894@84404090 then 15954@84404120 and later stayed above. Hour min 14264@84403900 under15k=10/56=17.9% at tip. 20k/300t still unlocked (this-hour max 17014@84404240, 3h max 18446@84402240).

## Remotes / W45N7 Invader Core (follow-up)

- W45N8 SAFE vis res later 2337 host=0 core=0
- W47N7 SAFE vis res later 2670 host=0 core=0
- W45N7: core landed last hour at 84403447 (9,44, lv0, 100k hits). defender84403448 (cost 5600, hits 5000) dispatched 84403598, arrived 84403669 at 21,1. Approached via 13,32 @84403700. Official 404 hole 84403701–84403817. Listener 84403818–84403845: defender stood at 9,43 (adjacent to the core) hits still 5000; Memory.remote th.since=84403845 why=killed. Room now vis, SAFE, host=0, core=0. rminer84402946 back at 21,15. reserver84403846 on the way/in room; reservation later 1223 and rising (was ~1239 last later, dipped during the fight). Do not start 指挥官; no Safe Mode sma=6.
- All five rooms vis; live hostiles 0.

## Motion

- creep_audit --patrol rc=2: known REGRESSION [deploy] vs live 2b5398f7 2026-11-19 02:28, same class, not alert (d). 1h defender.cpu_t_sum rise is the expected W45N7 defender, not a new stuck.
- creep_motion --patrol 1h/2h rc=1: known waiting_pickup / target_full / waiting_feed / no_task / queue_blocked / parked_threat. w8rminer swamp source is the same known watch. miner queue_blocked is a source-seat wait. No new stuck/oscillation after last deploy.
- Critical roles present: miners 2, queens 2, w8fillers 2 (brief 3 handoff), w8miners 2, rminers 3, w8up 2, home upgrader 1, reservers 3. reserve7 zero_run ~200t from 84404230 with W47N7 reservation still 2670, not formal (c). home reserver gap 84403680–84403840 recovered to 3, reservations healthy, not formal (c).

## Energy / harvest

- Home model 1h: upgrade 13.01/26 work=14 stor_delta +1.67 ticks 820; income A 9.95 B 10.00 R 5.92 (softer; W45N7 paused during the core). 2h: upgrade 16.41/26 stor_delta +0.32 ticks 1650; income A 9.98 B 9.97 R 7.88.
- W47 model_w8 src_A 0.35/0.17 is the same known link-accounting artifact (live miners seated). 1h R1/R2 7.09/8.62, 2h 6.58/5.86. Biggest designed gap remains keep=2 vs ideal 31 work.
- Labs KO on (Memory.ops.labs W46N8=KO, labReady why=active). Storage KO ~49636, lab KO 955, K/O healthy. Never unset labs, no market.

## CPU / infra

- CPU 1h mean 18.03 max 33.99@84404280 01:15:28; 2h mean 17.56 max 33.99; bucket full 10000 throughout. No formal (e).
- services.sh: ok postgres / views_apache / grafana / listener / dashboard. Grafana check all OK. DB writers fresh (seconds).
- Peacetime single-slot 5:5:1:1; Memory.cmd is the same dormant on=1 empty c (at 84224348), not a live 指挥官 battle. Listener auto-restart 01:21:30 after the 01:18 freeze, python 2185293 started 01:21:40; rot at 01:31 still W46N8.
- Official 40-min backfill: game.time=84404386 published_bases 84403600..84404200, reconstructed 84403601..84404300 (700), first pass 33/35 official GETs 200, missing_chunks=2 W45N7@84403700 and W45N7@84403800; already_in_db=25078 inserted_first=3844 overlap match=22876 differ=468; tick_s=4.378 ts_realigned_first=1101. confirm 01:26:46 gt~84404437 still_404 both inserted=0; retry2 01:29:41 gt=84404475 still_404 both inserted=0. just-published 84404300 at 01:28:11 gt=84404456 all_five_200 inserted=3567 (W46N8 608, W47N8 1509, W45N8 519, W45N7 429, W47N7 502). Window 84404301..84404400 all five 100/100 after JP.

## Box freezes / leftover official 404s (this log tells)

NEW, told here:
- 盒子休眠 00:50:16–01:00:10 (588s, already healed; STATS 84403921..84404079, 159t; official-filled W46N8/W47N8/W45N8/W47N7 159/159, W45N7 126/159 present 84403954..84404079, remaining official empty_no_creep; listener auto-restart 01:00:13, python 2176402 started 01:00:22)
- 盒子休眠 01:18:01–01:21:27 (201s, already healed; STATS 84404311..84404369, 59t; official-filled all five 59/59 after just-published 84404300; listener auto-restart 01:21:30, python 2185293 started 01:21:40)
- leftover official 404 W45N7@84403700 (listener 0/100; hole 100 ticks 84403701..84403800; still 404 after 00:46 / 01:00 / this patrol confirm+retry2)
- leftover official 404 W45N7@84403800 (listener 28/100 84403818..84403845; hole 72 ticks 84403801..84403817 and 84403846..84403900; still 404 after 01:00 / this patrol confirm+retry2)

Already told in the 00:35 USER_LOG, not re-told: 盒子休眠 23:53:42–23:57:33 and 00:11:07–00:22:22 (and older 23:20 / 22:49 / 22:14 / 21:42); leftover official 404s W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older.

No new short WS besides the two box freezes. No code change and no deploy this hour.
