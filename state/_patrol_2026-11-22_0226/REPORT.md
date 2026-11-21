# 1h peacetime patrol 2026-11-22 02:34 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_0226
Previous: state/_patrol_2026-11-22_0121 (01:31, TIP 84404430, later live 84404492, t508s3601)
Live code: 2b5398f7 (2026-11-19 02:28). No src change, no deploy.lock, no game deploy.
Analysis TIP 84405330 at 2026-11-22 02:31:12 +08. Later live 84405353-84405360 ~02:32-02:33.

## Alerts

FORMAL W47 upgrade HOLDS — thirty-fifth consecutive dual after the 12:25 clearance.
- exact2h 18.35/30.08=61.0% (prev 18.56=61.7%) still under 70%
- meaningful short last800 19.13=63.6% still soft
- last20-500 designed keep=2 20.00 e/t=66.5% must not clear
- last1500 18.05=60.0%, 1h INTERP 19.17=63.7% all soft
- model_w8 1h alloc upgrade 19.15 stor_delta -4.47 ticks 820 work=20 vs ideal 30.03; 2h alloc 18.33 stor_delta +4.79 ticks 1650 work=20
- Root remains designed keep=2 (20 e/t=66.5% of ideal). Do not change keep/softCap, no standing third, do not unseal the 40k lock.
- Re-clear only when a later patrol is no longer a dual (exact2h back above 70% or meaningful last800 no longer soft).
- 40k/500t still unlocked: this-hour/3h max 38369 @84404920 02:01, 12h max 38748@84400220 20:24, 24h max 42468@84390960 (already-known first 40k touch, unlatched). upArm=40000 upLatched=0 keep=2 upgCeil=2.
- Live later two unboosted 10W w8upgraders seated 12,25 ttl=281 e=40 and 14,27 ttl=885 e=40 (bodies wwwwwwwwwwcmm, no boost). w8up=2 throughout (brief w8up=3 at 84404700 and home nUp=3 at 84404600 were handoff overlap, not a standing third).
- threatSoft=0, bankWhy=ready, softCap2=0. sealPark/w8sealPark 0 why=ok (already unsealed last patrol); do not force-reseal. W47 RCL7 6088565/10935000=55.68% later 6089165.

FORMAL ALERT does NOT fire on HOME: last patrol exact2h 16.50/26=63.5% was the FIRST under after clearance; this exact2h 18.50/26.00=71.2% is back ABOVE 70%, and meaningful short is HARD (last800 24.14=92.9%, 1h INTERP 23.73=91.3%, last300 24.73=95.1%, last500 24.55=94.4%). last20 4.20=16.2% and last30 8.27=31.8% are post-02:26-freeze short samples and must not fire. last70-200 18.13=69.7% are the same 60-tick post-wake span. Root of the recovery is nUp=2 from 84404510 01:32 (after the locked 15k floor had held nUp=1 last hour). Do not change the 15k floor. Live later two unboosted 14W upgraders seated 30,30 ttl=713 e=22 and 29,30 ttl=802 e=36. nUp=2 why=ok / later thin_surplus.

FORMAL storage-floor STAYS CLEAR: last patrol ended ABOVE; this tip 15580 >=15000; later room_stats 15680@84405340, 15780@84405350, 15080@84405360 still above. consec-under=0. Intra-hour unders recovered: 14970@84404610 then 15070@84404620; min 14920@84404650 01:42 then 15020@84404660. A live Game query at 84405353 saw 14980, then room_stats 15080@84405360. Hour min 14920@84404650 under15k=2/58=3.4% at tip. 20k/300t still unlocked (this-hour max 17590@84404510, 3h max 18110@84403130).

## Remotes

- W45N8 SAFE vis res later 2134 host=0 core=0
- W45N7 SAFE vis res later 2158 host=0 core=0 (recovered from ~1223 after last hour's core kill; no recurrence)
- W47N7 SAFE vis res later 2861 host=0 core=0
- All five rooms vis; live hostiles 0. Do not start commander; no Safe Mode sma=6/smaW=6, ttd=150000 both.
- Critical roles present: miners 2 (3 during handoff), queens 2-3 handoff, w8fillers 2, w8miners 2-3 handoff, rminers 2, reservers 2 then 1 at later snapshot (still present, not a zero_run), w8up 2, home upgraders 2. No formal (c).

## Motion

- creep_audit --patrol rc=2: known REGRESSION [deploy] vs live 2b5398f7 2026-11-19 02:28, same class, not alert (d). 1h worst miner excess / queen near-hub / w8rhauler osc=12 is waiting_pickup at pickup tiles, not a new oscillation.
- creep_motion --patrol 1h/2h rc=1: known waiting_pickup / target_full / waiting_feed / queue_blocked / no_task. w8rminer swamp source is the same known watch. miner queue_blocked is a source-seat wait. 2h defender84403448 queue_blocked is the already-told W45N7 core defender, not new stuck. No new stuck/oscillation after last deploy.

## Energy / harvest

- Home model 1h upgrade 23.90 stor_delta -2.45 ticks 820 work=28 vs ideal 26; 2h upgrade 18.62 stor_delta +0.07 ticks 1650.
- Home harvest R 2h/1h 6.77/6.35 (1h better vs last patrol 5.92 during the W45N7 core pause). A/B ~9.95/9.96. Biggest home gap remains remotes (W45N7 still climbing back).
- W47 src_A link artifact 1h unset / 2h 0.18 (same known accounting quirk). 2h R1/R2 6.85/6.75, 1h 5.36/5.38 softer than last patrol 7.09/8.62. src_B 1h/2h 9.07/9.53.

## CPU / infra

- no formal (e): CPU 1h n=51 min 13.06 max 23.48@84404620 01:40 mean 16.88 p95 20.07, 2h n=114 min 13.06 max 33.99 (previous hour) mean 17.39 p95 20.68, bkt min 9999; live later bucket 10000 cpu ~13-19.
- Infra OK (not formal f): grafana all 200, postgres/dashboard/listener up, peacetime single-slot 5:5:1:1 (after 02:26:23 restart; python 2208243 started 02:26:32; seen W47N8 then W45N8 / W45N7), commander not holding slots, yield absent; Memory.cmd stale on=1 at=84224348 c={} s={} v=1 not touched.
- Official 40m backfill ticks 84404501..84405200 (700, published_bases 84404500..84405100 at game.time=84405294, tick_s=4.258) missing_chunks=0; already_in_db=22560 inserted first=0; confirm skipped no targets; just-published 84405200 at 02:32:02 gt=84405342 all_five_200 inserted=1340. Hour-window remaining holes after just-published are the unpublished tail after 84405300 / current listener rotate, expected.
- NEW box freeze 01:50:21-02:00:50 (621s; already healed; STATS 84404761..84404919, 159t; official-filled all five 159/159; listener auto-restart 02:00:53, python 2201574 started 02:01:03) — first told this patrol (recorded earlier by 02:11 30-min backfill).
- NEW box freeze 02:13:42-02:26:20 (753s; already healed; STATS 84405081..84405269, 189t; official-filled 84405081..84405200 all five 120/120; just-published 84405200 filled 84405201..84405300, completing the freeze window; listener auto-restart 02:26:23, python 2208243 started 02:26:32).
- Official 404s: NEW none. Already-told leftovers W45N7@84403800 (28/100) and W45N7@84403700 (0/100) plus older W45N7@84400300 / W45N7@84400400 / W47N8@84400100 aged out of this 40m window, not retried as new. No new short listener WS gaps.
- labs KO mode=KO (actOk=1 actGaps empty, never unset Memory.ops.labs); sma=6/smaW=6 ttd=150000 both never activated; sites=0.
- mineral home stor O/K/KO 86400/218556/50436 (lab2 later O/K 89400/221556, koLab 600), term O/K 3000/3000; W47 term E 1284 K 52.
- r7 on endTime=84408216 by Misaki.
- LIVE still 2b5398f7 (deploy 2026-11-19 02:28, no new game deploy this patrol). No src/ change.
