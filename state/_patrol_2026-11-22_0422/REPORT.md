# 1h peacetime patrol 2026-11-22 04:22 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_0422
Previous: state/_patrol_2026-11-22_0318 (03:30, TIP 84406090, later live 84406149-84406152)
Live code: 2b5398f7 (2026-11-19 02:28). No src change, no deploy.lock, no game deploy.
Analysis TIP 84407020 at 2026-11-22 04:27:39 +08. Later live 84407066 ~04:30, later room_stats to 84407060 04:30:23.

## Alerts

FORMAL ALERT FIRES on HOME upgrade — second consecutive dual after the 02:34 recovery (last patrol exact2h 17.84/26=68.6% was the FIRST under after 18.50=71.2% went back ABOVE).
- exact2h 13.16/26.00=50.6% (prev 17.84=68.6%) still under 70%
- meaningful short last800 14.75=56.7% also soft
- 1h INTERP 14.24=54.8%, last1500 12.96=49.9%, last300/500 16.27=62.6% all soft
- last20-100 14.00 e/t=53.8% are nUp=1 floor_bank near the 15k floor and must not be used to fire or to clear; the fire is the exact2h + last800 dual, not those short post-freeze / floor samples
- last140 15.46=59.5%, last200 17.40=66.9% still under 70%
- model 1h measured upgrade 14.30 stor_delta -3.52; 2h measured upgrade 13.07 stor_delta -1.77; upgrader_bound energy, work=14 vs ideal 26
- Root is the designed 15k floor holding nUp=1 (Memory why=floor_bank, surplus negative) for most of this hour, plus two box-freeze STATS holes. nUp=1 from 84406220 03:32 stor=14270 through 84406780, then 2@84406790-84406880, then 1 again from 84406950 through tip and later. Live later one unboosted 14W upgrader (body wwwwwwwwwwwwwwcmm) 30,30 ttl=598 e=22 at 84407043; nUp=1 why=floor_bank storE=13010 then later 12560@84407066. Do not change the 15k floor. Do not add a standing third.

FORMAL W47 upgrade HOLDS — thirty-seventh consecutive dual after the 12:25 clearance.
- exact2h 19.77/30.08=65.7% (prev 19.22=63.9%) still under 70%
- meaningful short last800 20.28=67.4% still soft
- last20-500 designed keep=2 20.00 e/t=66.5% must not clear
- last1500 20.24=67.3%, 1h INTERP 20.19=67.1% all soft
- model_w8 1h alloc upgrade 20.17 stor_delta +5.84 ticks 870 work=30 vs ideal 30.03; 2h alloc 19.77 stor_delta -1.98 ticks 1730 work=30
- Root remains designed keep=2 (20 e/t=66.5% of ideal). Do not change keep/softCap, no standing third, do not unseal the 40k lock.
- Re-clear only when a later patrol is no longer a dual (exact2h back above 70% or meaningful last800 no longer soft).
- 40k/500t still unlocked: this-hour/3h/12h max 41133@84406720 04:06:53 (first observed 40k after the 03:47-04:06 freeze; stor was 34524@84406430 then 41133 on the first STATS sample after the hole). Observed >=40k samples 84406720-84406790 (70 ticks, last 40083) then 39283@84406800. Even if 40k began at the start of that unobserved hole, the optimistic span is 360 < 500. 24h max still 42468@84390960 (already-known first 40k touch, unlatched; prior best span 461 < 500). upArm=40000 upLatched=0 keep=2 upgCeil=2.
- W47 stor this hour went 24960@last tip -> min 24759@84406120 -> 41133@84406720 -> later 30074@tip, 29044@84407060, live 28544@84407066. sealPark=1 why=threat / threatSoft=1 softCap2=1 bankWhy=threatSoft at later 84407040-84407067 is the designed response to the W47N7 invader (and a short linger after the kill at 84407021), not a policy change. sealMinE=25000 unchanged.
- Live later three unboosted 10W w8upgraders (bodies wwwwwwwwwwcmm, no boost): 14,26 ttl=21 e=40 (dying, in w8recycle), 12,25 ttl=625 e=20, and 28,35 ttl=1460 e=0 walking in at 84407043. w8up=3 at 84406970 through later is handoff overlap, not a standing third. threatSoft=1, feedOk=1, hubLink=1. W47 RCL7 6121962/10935000=55.99% later 6122422.

FORMAL storage-floor STAYS CLEAR: last patrol tip 18670 was ABOVE; this tip 12910<15000 is the FIRST under after that, so it does not fire even though later is still under. consec-under=1. Intra-hour unders recovered then fell again: 14570@84406170 03:29 through 14070@84406200, min in that dip 14070 then 15570@84406230; brief 14846@84406860-14946@84406870 then 15046@84406880; after the 04:18-04:22 freeze 14870@84406950 down to tip 12910@84407020, later room_stats 13010/13110/13210/12510@84407030-84407060, live Game 12560@84407066 still under. Hour min 12910 (later 12510) under15k=16/60=26.7% this-hour-to-tip. Do not change the 15k floor. 20k/300t still unlocked (no 20k this hour; 3h max still 20870@84406060, best>=20k span=90 from last hour).

## Remotes

- W45N8 SAFE vis res later 2097 (live 84407068; earlier 2124@84407041) host=0 core=0
- W45N7 SAFE vis res later 2373 (2400@84407041) host=0 core=0
- W47N7 SAFE vis res later 2200 (2227@84407041) host=0 core=0
- NEW this hour: W47N7 solo unhealed Invader at 84406796 04:12:17 (43,49, ra=1, hits=1000, heal=false, boosted=false, ttl=1500). Creeps evac'd (official empty_no_creep 84406901..84406973 in the just-published chunk). rdef84406797 spawned immediately 84406797 (waited=1), arrived 84406986 travel=39, incident cleared 84407021 04:27:44 ev=cleared from=DEFEND dur=225 why=killed; defender hits stayed 5000, still in W47N7 28,18 ttl=1410 at 84407036. No Invader core. Later reservation 2227 then 2200. All five rooms vis; live hostiles 0. Do not start commander; no Safe Mode sma=6/smaW=6, ttd=150000 both.
- Critical roles present: miners 2, queens 2, w8fillers 2, w8miners 2, rminers 2, reserve7 1 at live snapshots (reserver absent only at the tip sample 84407020 / 84407035, reserve7 covered, not formal (c)). w8up 3 handoff, home upgrader 1. defender84405551 still in W45N8 25,41 ttl=158 hits=4800 is the previous hour's already-told defender aging out, not a new incident. w8defender84406914 was spawning at home 84407036.

## Motion

- creep_audit --patrol rc=2: known REGRESSION [deploy] vs live 2b5398f7 2026-11-19 02:28, same class, not alert (d). 6h worst w8hauler84404898 osc=58 is waiting_pickup at pickup tiles, not a new oscillation (same known class as last patrol).
- creep_motion --patrol 1h/2h rc=1: known waiting_pickup / target_full / waiting_feed / queue_blocked / no_task. Home upgrader waiting_feed matches energy-bound / floor_bank feed. w8rminer swamp source is the same known watch. miner queue_blocked is a source-seat wait. defender84405551 queue_blocked is the already-told post-kill return through W45N8, not new stuck (hits 4800 the whole time). No new stuck/oscillation after last deploy. No src fix this hour.

## Energy / harvest

- Home model 1h measured upgrade 14.30 stor_delta -3.52; 2h measured upgrade 13.07 stor_delta -1.77; upgrader_bound energy; work=14 vs ideal 26. Delivered ctl is thin because nUp=1 floor_bank.
- Home source nets (model layout) A/B/R 8.95/9.13/6.86, W45N7 net 4.54. Softness is the 15k floor + STATS holes, not a harvest collapse on A/B.
- W47 src_A link artifact 1h/2h 0.00/0.00 (same known accounting quirk). src_B 1h/2h 9.87/8.49; R1 6.17/5.70; R2 9.62/6.93 (1h R2 recovered vs last patrol 4.60). 1h stor_delta +5.84 reflects the climb to 41k during the long freeze; 2h stor_delta -1.98 after the post-40k drain and threat seal. Not a reason to change keep=2.

## CPU / infra

- no formal (e): CPU 1h n=54 min 12.33 max 23.48@84406280 03:37 mean 17.32 p95 20.18, 2h n=111 min 12.33 max 23.48@84406280 mean 17.44 p95 20.55, bkt min 9997; live later bucket 10000 cpu ~15-18.
- Infra OK (not formal f): grafana all 20 panels 200, postgres/dashboard/listener up, peacetime single-slot 5:5:1:1 (after 04:22:31 restart; python 2251463 started 04:22:41; rotate W47N8 37s then W45N8 120s / W45N7 120s / W46N8 600s, still on W46N8 at 04:30), commander not holding slots, yield absent; Memory.cmd stale on=1 at=84224348 c={} s={} v=1 not touched. q.py live queries all succeeded (q_live1-3, q_extra 4/4, q_later 4/4).
- Official 40m backfill ticks 84406201..84406900 (700, published_bases 84406200..84406800 at game.time=84406980, tick_s=4.012 / tick_s_in_use=4.07699 prev_later, first-pass ts_realigned=3685, corrective later-mean refused, corrective prev_later realign nfix=1164 still_over_45s=0) missing_chunks=3 W45N8@84406400, W46N8@84406600, W46N8@84406700; already_in_db=20420 inserted first=2847; confirm 04:27:33 gt=84407018 still_404 those three inserted=0; retry2 04:27:44 gt=84407021 still_404 inserted=0; late 04:27:49 gt=84407022 still_404 inserted=0; just-published 84406900 at 04:29:06 gt=84407041 all_five_200 inserted=3136 still_404=[]; post_jp retry 04:30:40 gt=84407064 still_404 the same three inserted=0. Official window plus just-published covers through 84407000 except the three leftover 404 holes and W47N7 official_empty_no_creep 84406901..84406973 (evac, 27/100 present 84406974..84407000). Remaining holes after 84407000 are the unpublished tail / current listener rotate, expected. Coverage first-pass official_404=260 (W46N8 160 + W45N8 100), empty_no_creep=0 in 84406201..84406900.
- NEW box freeze 03:47:58-04:06:12 (1093s; already healed; STATS 84406431..84406719, 289t; official-filled W46N8 175/289, W47N8 289/289, W45N8 219/289, W45N7 289/289, W47N7 289/289; first-pass official covers 84406431..84406700 except leftover 404 holes W45N8@84406400 overlap 84406431..84406500 and W46N8@84406600 84406601..84406700; unpublished tail 84406701..84406719 sits in still-404 W46N8@84406700 except listener 40 ticks 84406715..84406754; listener auto-restart 04:06:15) — first told this patrol (recorded earlier by the 04:16 30-min backfill).
- NEW box freeze 04:18:46-04:22:28 (221s; already healed; STATS 84406881..84406949, 69t; after just-published official-filled W46N8/W47N8/W45N8/W45N7 69/69, W47N7 20/69 present 84406881..84406900, remaining official empty_no_creep during the W47N7 evac 84406901..84406949; listener auto-restart 04:22:31, python 2251463 started 04:22:41) — first told this patrol.
- No new short listener WS gaps (the 4s 04:12:17-04:12:21 is two incident lines; the 37s 04:22:42-04:23:19 is the first slot switch after restart, not a WS hole). Already-told 02:44:07-03:03:40 and 02:13:42-02:26:20 and 01:50:21-02:00:50 (and older) not re-told.
- Official 404s NEW leftovers, still 404 after confirm/retry2/late/post_jp: W45N8@84406400 (listener 0/100; hole 100 ticks 84406401..84406500), W46N8@84406600 (listener 0/100; hole 100 ticks 84406601..84406700), W46N8@84406700 (listener 40/100 range 84406715..84406754; hole 60 ticks 84406701..84406714 and 84406755..84406800; just-published is a different base, this chunk still 404). Already-told leftovers W45N7@84403800 (28/100, range 84403818..84403845) and W45N7@84403700 (0/100) plus older W45N7@84400300 / W45N7@84400400 / W47N8@84400100 aged out of this 40m window start 84406201, not retried as new.
- labs KO mode=KO (actOk=0 actGaps=homeStor because home storage is under the 15k actHome, never unset Memory.ops.labs); sma=6/smaW=6 ttd=150000 both never activated; sites=0.
- mineral home stor O/K/KO 85200/217756/50836 term O/K 3000/3000 (also small GO/ZH/UH), koLab 245; W47 term E 1284 K 52.
- r7 on endTime=84409268 by Misaki (not touched).
- LIVE still 2b5398f7 (deploy 2026-11-19 02:28, no new game deploy this patrol). No src/ change. No code change and no deploy this hour (src clean, deploy.lock absent, live still 2026-11-19 02:28 code 2b5398f7). No decision required from Misaki beyond standing policy: do not change the 15k floor / keep=2 / no standing third / 40k lock; do not start 指挥官.
