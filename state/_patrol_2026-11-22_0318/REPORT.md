# 1h peacetime patrol 2026-11-22 03:30 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_0318
Previous: state/_patrol_2026-11-22_0226 (02:34, TIP 84405330, later live 84405353-84405360)
Live code: 2b5398f7 (2026-11-19 02:28). No src change, no deploy.lock, no game deploy.
Analysis TIP 84406090 at 2026-11-22 03:24:10 +08. Later live 84406149-84406152 ~03:28, later room_stats to 84406150 03:28:16.

## Alerts

FORMAL W47 upgrade HOLDS — thirty-sixth consecutive dual after the 12:25 clearance.
- exact2h 19.22/30.08=63.9% (prev 18.35=61.0%) still under 70%
- meaningful short last800 19.16=63.7% still soft
- last20-500 designed keep=2 20.00-20.24 e/t=66.5%-67.3% must not clear
- last1500 19.00=63.2%, 1h INTERP 19.22=63.9% all soft
- model_w8 1h alloc upgrade 19.18 stor_delta -10.4 ticks 820 work=20 vs ideal 30.03; 2h alloc 19.19 stor_delta -4.8 ticks 1680 work=20
- Root remains designed keep=2 (20 e/t=66.5% of ideal). Do not change keep/softCap, no standing third, do not unseal the 40k lock.
- Re-clear only when a later patrol is no longer a dual (exact2h back above 70% or meaningful last800 no longer soft).
- 40k/500t still unlocked: this-hour max is the declining series (tip 24960; hour started 33142@84405330), 3h max 38369@84404920 02:01, 12h max 38748@84400220 20:24, 24h max 42468@84390960 (already-known first 40k touch, unlatched; best>=40k span=461 < 500). upArm=40000 upLatched=0 keep=2 upgCeil=2.
- W47 stor this hour fell from ~33142 at last tip to ~2.45-2.52万 (STATS min 24759@84406120, live later 24509@84406149). sealPark was 1 at 84406107 when storE=24710 hit sealMinE=25000, then later end_ops sealPark=0 why=ok at 84406150. This is the designed 25k seal, not a policy change.
- Live later two unboosted 10W w8upgraders (bodies wwwwwwwwwwcmm, no boost): 14,27 ttl=123 e=20 and 14,26 ttl=958 e=20 at 84406106. w8up=2 at tip, later 3 at 84406130-84406150 is handoff overlap, not a standing third. threatSoft=0, bankWhy=ready, softCap2=0, feedOk=1, hubLink=1. W47 RCL7 6103095/10935000=55.81% later 6104417.

FORMAL ALERT does NOT fire on HOME: last patrol exact2h 18.50/26=71.2% was back ABOVE 70%; this exact2h 17.84/26.00=68.6% is the FIRST under after that recovery, so it does not fire even though meaningful short is soft (last800 11.93=45.9%, 1h INTERP 12.95=49.8%, last300/500 9.46=36.4% on the post-freeze 290-tick STATS span). last20 1.40=5.4% last30 5.00=19.2% last70-200 6.37-9.42=24.5%-36.2% are the nUp=1 TTL handoff plus thin surplus near the 15k floor and must not fire. last1500 18.21=70.0% sits on the line. Root of the soft hour: the 02:44-03:03 box-freeze STATS hole, W45N7 invader evac cutting remote income, storage refill (stor_delta +3.52 e/t in the 1h model), and end-of-hour upgrader TTL handoff (upgrader84404507 ended 84406056, upgrader84406091 spawning 84406092) / later thin_surplus. Live later: seated 29,30 ttl=40 then replacement spawning 14W unboosted; nUp=1 at tip, 2@84406100-84406110, 3 handoff@84406120-84406140, 2@84406150; Memory later nUp=1 why=thin_surplus at 15970. Do not change the 15k floor. Do not add a standing third.

FORMAL storage-floor STAYS CLEAR: last patrol ended ABOVE; this tip 18670>=15000; later room_stats 17870@84406100, 17970@84406110, 18070@84406120, 16570@84406130, 15870@84406140, 15970@84406150 still above; live Game 15970@84406149. consec-under=0. Intra-hour unders recovered: 14570@84405430 02:38 through 14270@84405480, min 13970@84405450 02:39:51 then 15170@84405490 02:42. Hour min 13970 under15k=6/49 this-hour-to-tip. 20k/300t still unlocked (first 20k touch this hour: 20070@84405980 through 20870@84406060 03:22, best>=20k span=90; this-hour/3h max 20870).

## Remotes

- W45N8 SAFE vis res later 2012 (live 84406151; earlier 2059@84406104) host=0 core=0
- W45N7 SAFE vis res later 1510 (1463@84406104) host=0 core=0
- W47N7 SAFE vis res later 2763 (2716@84406104) host=0 core=0
- NEW this hour: W45N7 solo unhealed Invader at 84405402 02:36:20 (49,37, ra=1, hits=1000, heal=false, boosted=false, ttl=1500). Creeps evac'd north (rminer/rhauler to y=0). defender84405551 spawned at home 84405551 (48-part, 4800 hits, full budget), entered W45N7 84405787, incident cleared 84405804 ev=killed from=DEFEND dur=402 why=killed; defender hits stayed 4800 then left via W45N8 (still in W45N8 25,41 ttl=1095 at 84406099). No Invader core. Reservation dropped from ~2158 to ~1463 then later 1510. Official empty_no_creep in W45N7 84405446..84405786 (evac+freeze) and 84405818..84405854 (defender left), not 404s.
- All five rooms vis; live hostiles 0. Do not start commander; no Safe Mode sma=6/smaW=6, ttd=150000 / later home 149997.
- Critical roles present: miners 2, queens 2, w8fillers 2, w8miners 2-3 handoff, rminers 2, reserver 1 + reserve7 1 at live snapshots, w8up 2 (later 3 handoff), home upgraders 1 then 2 then 3 handoff then 2. Reserver TTL: W45N7 reserver84404728 expired ~84405339 (600-tick claim life) just before the invader; W45N8 reserver84405081 expired ~84405692 during the freeze; reserve7 was present by 84405800; replacement reserver84405962 walking from home 84405964. Not formal (c): owned-room miners/queens/w8fillers/rminers were present, reserve7 covered the gap, new reserver in flight, reservations still healthy.

## Motion

- creep_audit --patrol rc=2: known REGRESSION [deploy] vs live 2b5398f7 2026-11-19 02:28, same class, not alert (d). 1h worst w8hauler84404898 osc=46 is waiting_pickup at pickup tiles, not a new oscillation (same known class as last patrol's wrhauler osc).
- creep_motion --patrol 1h/2h rc=1: known waiting_pickup / target_full / waiting_feed / queue_blocked / no_task. Home upgraders waiting_feed matches energy-bound / ctl feed during the storage-refill hour. w8rminer swamp source is the same known watch. miner queue_blocked is a source-seat wait. defender84405551 queue_blocked is the post-kill return through W45N8, not new stuck (hits 4800 the whole time). No new stuck/oscillation after last deploy. No src fix this hour.

## Energy / harvest

- Home model 1h upgrade 12.33 stor_delta +3.52 ticks 820 work=28 vs ideal 26; 2h upgrade 17.87 stor_delta +1.63 ticks 1680. upgrader_bound energy; delivered ctl 2.93 e/t in the 1h window (storage was being refilled).
- Home harvest A/B/R 1h 9.97/10.00/6.92, 2h 9.98/9.98/6.97. Biggest home gap this hour was W45N7 downtime during the invader evac, plus ctl-feed/storage refill rather than a harvest collapse on A/B.
- W47 src_A link artifact 1h/2h 0.00/0.00 (same known accounting quirk). src_B 1h/2h 6.84/8.85; R1 3.78/5.14; R2 4.60/4.66 softer than last patrol 1h 5.36/5.38 and 2h 6.85/6.75. That, plus keep=2 upgrade ~19.2 e/t, explains the ~8k storage drain and the 25k seal flicker. Not a reason to change keep=2.

## CPU / infra

- no formal (e): CPU 1h n=54 min 14.19 max 22.30@84405440 02:39 mean 17.50 p95 21.53, 2h n=107 min 13.06 max 23.48@84404620 01:40 (previous hour) mean 17.12 p95 20.47, bkt min 9999; live later bucket 10000 cpu ~14-20.
- Infra OK (not formal f): grafana all 20 panels 200, postgres/dashboard/listener up, peacetime single-slot 5:5:1:1 (after 03:03:43 restart; python 2219657 started 03:03:53; rotate W47N8 then W45N8 / W45N7 / W46N8), commander not holding slots, yield absent; Memory.cmd stale on=1 at=84224348 c={} s={} v=1 not touched. q.py live queries all succeeded (q_live1-3 and q_extra 4/4).
- Official 40m backfill ticks 84405301..84406000 (700, published_bases 84405300..84405900 at game.time=84406057, tick_s=4.246 / tick_s_in_use=4.24614, first-pass ts_realigned=4040, no later-mean corrective) missing_chunks=0; already_in_db=22286 inserted first=2982; confirm skipped no targets; late retry skipped no targets; just-published 84406000 at 03:27:37 gt=84406140 all_five_200 inserted=2987 still_404=[]. Official window plus just-published covers through 84406100 all five; remaining holes are the unpublished tail after 84406100 / current listener rotate, expected. W45N7 official_empty_no_creep 378 ticks in the 40m window (84405446..84405786 and 84405818..84405854), official_404=0.
- NEW box freeze 02:44:07-03:03:40 (1172s; already healed; STATS 84405501..84405799, 299t; official-filled W46N8/W47N8/W45N8/W47N7 299/299, W45N7 13/299 present 84405787..84405799, remaining official empty_no_creep 84405446..84405786; first-pass official covers the whole freeze through 84405800 and beyond; listener auto-restart 03:03:43, python 2219657 started 03:03:53) — first told this patrol (recorded earlier by the 03:14 30-min backfill). No new short listener WS gaps (the 39s 03:03:54-03:04:33 is the first incident line after restart, not a WS hole). Already-told 02:13:42-02:26:20 and 01:50:21-02:00:50 (and older) not re-told.
- Official 404s NEW none. Already-told leftovers W45N7@84403800 (28/100, range 84403818..84403845) and W45N7@84403700 (0/100) plus older W45N7@84400300 / W45N7@84400400 / W47N8@84400100 aged out of this 40m window start 84405301, not retried as new.
- labs KO mode=KO (actOk=1 actGaps empty, never unset Memory.ops.labs); sma=6/smaW=6 ttd=150000 both never activated; sites=0.
- mineral home stor O/K/KO 86000/217756/50436 term O/K 3000/3000 (also small GO/ZH/UH), koLab 980; W47 term E 1284 K 52.
- r7 on endTime=84408826 by Misaki (not touched).
- LIVE still 2b5398f7 (deploy 2026-11-19 02:28, no new game deploy this patrol). No src/ change. No code change and no deploy this hour (src clean, deploy.lock absent, live still 2026-11-19 02:28 code 2b5398f7). No decision required from Misaki; do not start 指挥官.
