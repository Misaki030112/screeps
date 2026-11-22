# 1h peacetime patrol 2026-11-22 08:18 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_0818
Previous: state/_patrol_2026-11-22_0725 (07:25 / delivered ~07:35, TIP 84409680, later live 84409752 / room_stats 84409750)
Live code: 2b5398f7 (2026-11-19 02:28). No src change, no deploy.lock, no game deploy.
Analysis TIP 84410480 at 2026-11-22 08:23:24 +08. Later live/room_stats through 84410550 08:28:14, stor 14294/27147.

## Alerts

FORMAL W47 upgrade HOLDS — third consecutive dual after the 05:38 clearance (07:35 re-fired on the second dual; this hour is again a dual).
- exact2h 20.19/30.08=67.1% (prev 20.44=68.0%) is still under 70%
- meaningful short last800 20.72=68.9% is still soft, so this patrol is again a dual
- last20-70 20.00 e/t=66.5% are the designed keep=2 20.00 e/t=66.5% soft window and must not fire or clear
- last100 20.51=68.2%, last140 20.58=68.4%, last200 20.46=68.0% also soft; last300 21.62=71.9% is above 70% but is context only and must not clear (last500 equals last300, span only 290, because of the STATS gap in the box freeze)
- last1500 20.22=67.2%; 1h INTERP 20.65=68.7%
- model_w8 1h alloc upgrade 20.7 stor_delta -3.96 vs ideal 30.03 work=30; 2h alloc 20.2 stor_delta -1.38 vs ideal 30.03 work=30
- Do not change keep=2 / no standing third / do not unseal the 40k lock
- 40k/500t still unlocked: this hour W47 stor min 23983@84410240 08:06:56 max 28839@84409720 07:31:41, never reached 40k. Last observed >=40k remains 84406720-84406790 (70 ticks, max 41133@84406720 04:06:53) already told. 8h max 41133, 24h max 42468. upArm=40000 upLatched=0 keep=2 upgCeil=2
- W47 stor this hour min 23983 max 28839, tip 25266@84410480, later 25266@84410490-84410510 / 25600@84410520 / 26564@84410530 / 27147@84410540-84410550
- Brief dips under the 25k seal line (24283/23983@84410230-84410240, 24972@84410410-84410420, 24916@84410450, 24516@84410470) recovered quickly. Live later w8soft/w8day sealPark=0 why=ok storE=25600 then 27147. Opening/staying unsealed is the designed storage-seal reaction, not a policy change.
- Live later unboosted 10W w8upgraders: at 84410521, 84409008 seated 11,25 ttl=25, 84409843 seated 14,26 ttl=860, and 84410447 walking 28,35 ttl=1464. nUp/w8up=3 at tip and later through 84410550 is a handoff overlap, not a standing third. keep=2, upgCeil=2, feedOk=1, hubReady=1, bankWhy=ready, threatSoft=0, softCap2=0, phase=ready why=done. w8threat still 84407010.

FORMAL HOME upgrade STAYS CLEARED — last patrol stayed cleared (exact2h 22.67=87.2%). This hour exact2h 22.23/26.00=85.5% (prev 22.67=87.2%) stays well above 70%.
- meaningful short last800 24.27=93.4% is hard
- 1h INTERP 23.30=89.6%, last1500 23.63=90.9%, last200-500 26.72-27.12=102.8-104.3%, last20-140 28.00=107.7% all hard
- model 1h measured upgrade 23.90 stor_delta -0.82 ticks 830 vs ideal 26; 2h measured upgrade 22.50 cpu mean 17.23
- nUp=1 at last tip 84409680 stor=15988, nUp=2 from 84409790 07:36:26 stor=16814, nUp=3 from 84410450 08:21:20 stor=15504 through tip 15004 (handoff: 84408974 ttl=3 seated 30,30 plus 84409783 / 84410443). Later nUp=2 from 84410530 after 84408974 expired. Do not change the 15k floor. Do not add a standing third.

FORMAL storage-floor STAYS CLEAR. Last tip 15988 was ABOVE 15k (consec-under=0). This analysis tip 15004 is still ABOVE 15k, so consec-under=0, does not fire.
- This hour analysis window home stor min 15004@84410480 (the tip), under15k 0/53=0.0%, max 18084@84410190 08:03:28. Later dipped under 15k from 84410500 08:24:45 (14904) then 14304@84410520 / 14404@84410530 / 14194@84410540 / 14294@84410550 08:28:14. That later under is the first under after clearance and must not re-fire. Do not change the 15k floor.
- 20k/300t still unlocked: 3h max 19194, best >=20k tick-span=0 < 300.
- labReady at 84410523 actOk=0 actGaps=homeStor (actHome=15000) while homeStor=14354 — designed KO pause under the 15k act gate. Memory.ops.labs W46N8=KO unchanged; labReady why=active; never unset.

No (c) formal for a lasting missing critical role: miner/rminer/queen/w8filler/w8miner present throughout. Home reserver zero_run 90 ticks 84410190-84410280 (08:03:28-08:09:41), under 100 ticks, not formal (c); reserver=2 at tip and later. reserve7 was 0 for 200 ticks 84409680-84409880 (continuing the already-flagged gap from 07:13), returned 84409890 07:43:14, then gone again from 84410500 08:24:45 through later 84410550; W47N7 reservation stayed healthy at ~2931. Flagged in the user log, not treated as a new shippable spawn bug this hour.

No (d) new stuck/oscillation. creep_audit --patrol rc=2 is the known REGRESSION [deploy] vs live 2b5398f7, identical deploy-class line to last hour, not alert (d). creep_motion --patrol 1h/2h rc=1 known waiting_pickup / target_full / waiting_feed / no_task / queue_blocked. w8rminer swamp-source watch unchanged (w8rminer84409047 1h swamp 141; 84407680 aged out). Pattern did not change.

No (e) CPU issue: 1h min 15.1 max 29.75 mean 17.78 bucket min 10000 / live 10000. 2h min 12.03 max 29.75 mean 17.23. Live later 15.28@84410550 bucket 10000.
No (f) infra down: postgres/grafana/listener/dashboard up; grafana_check all OK; analysis tools ran; 40m backfill missing_chunks=1 leftover W47N8@84409800 still 404 after confirm/retry2/late; JP 84410400 all five 200 inserted=2413.

## Remotes

W45N8 / W45N7 / W47N7 all visible, SAFE, host=0, core=0 at 84410497 / 84410520. Reservation ticksToEnd ~1940 / 1976 / 2931 (by Misaki). W45N8 and W45N7 just under RES_SPAWN=2000; home reservers still present. defs empty. Do not start 指挥官 or Safe Mode.

## Backfill / coverage / freezes / official 404s

Official 40m backfill ticks 84409701..84410400 (700, published_bases 84409700..84410300 at game.time=84410439, tick_s=4.055, ts_realigned=7680) missing_chunks=1 W47N8@84409800; already_in_db=22389 inserted first=3680; first pass 34/35 official GETs 200. confirm 08:23:26 gt=84410480, retry2 08:23:52 gt=84410487, and late 08:25:32 gt=84410511 still_404 W47N8@84409800 inserted=0 (listener 96/100 range 84409805..84409900; hole 4 ticks 84409801..84409804). Just-published 84410400 at 08:27:33 gt=84410540 all_five_200=True inserted=2413 (W46N8 794, W47N8 447, W45N8 379, W45N7 412, W47N7 381). Official window plus just-published covers through 84410500 all five 100/100 except the leftover 4-tick hole in W47N8@84409800. Hour window 84409681..84410480: four rooms 800/800, W47N8 796/800 missing only 84409801..84409804.

NEW leftover official 404: W47N8@84409800 (confirm+retry2+late still 404, inserted=0; listener 96/100; hole 4 ticks). Already-told leftovers W46N8@84408300 / W47N8@84408300 / W47N7@84407900 / W45N8@84407700 / W46N8@84407000 remain 404, aged out of this 40m window start 84409701, were reconfirmed still 404, do not re-tell as new. Older leftovers aged out, do not re-tell.

NEW box freeze (not yet told by a 1h patrol; recorded quietly by the 08:15 backfill):
- 盒子休眠 07:44:22-08:02:42 (1093s; already healed; STATS 84409901..84410189, 289t; official-filled ALL FIVE 289/289; listener auto-restart 08:02:45, python 2336374 started 08:02:54)

The 08:02 listener python pid change is this box-freeze auto-restart, not a tools/services.sh status restart. services.sh only reported ok listener; parent run_listener.sh 4035476 has been running since Nov 13. No second listener was started. This run did not restart the listener again. room_stats gap 84409900-84410190 (290t, 1175s) is this freeze; official history does not fill room_stats.

No new short listener WS interruption this hour beyond the box freeze (already-told 05:25:19-05:27:20 remains already told). Already-told freezes 07:20:32-07:26:28 and 06:50:03-07:02:08 (and older 06:21 / 05:52 / 05:17 / 04:41 / 04:18 / 03:47 and earlier) remain already told; do not re-tell.

Listener healthy at end: 1 process (2336374 since 08:02:54, parent run_listener.sh 4035476 since Nov 13), yield_absent=True, peacetime 1-slot 5:5:1:1 (listener_rot W47N8 at 08:28:26, ~85s left), no second listener, war_cmd/pulse not touched. Console replies did not stall after the 08:02 restart; listener was not manually restarted.

## Pillars

A. Motion: no new stuck/oscillation. Known waiting_pickup / target_full / waiting_feed / no_task / queue_blocked. w8rminer swamp-source watch unchanged. Home/W47 upgraders waiting_feed at known low rates. Trajectories after official fill plus JP cover the hour except the 4-tick leftover 404 hole in W47N8 and the unpublished tail after 84410500.

B. Energy / flow: home exact2h 85.5% stays cleared; short windows hard at two 14W upgraders. Analysis-tip storage stayed just above 15k then later dipped under; designed 15k floor should press nUp down (later already 2 after the handoff). W47 keep=2 delivers ~20 e/t short windows and 20.19 exact2h (67.1%), third dual after clearance so formal holds. Sources and remotes flowing; no new invader spend. Biggest near-term gap remains designed W47 keep=2 vs 30.08 ideal, not a shippable policy change.

C. Strategy / buildings / remotes / CPU: remotes SAFE host=0 core=0, reservations healthy. sites=0. labs remain KO (labReady why=active; actOk=0 actGaps=homeStor is the designed 15k act gate); never unset Memory.ops.labs; never re-ask market. r7 still on endTime=84413428 by Misaki (was 84412380 last patrol; not touched). sma=6/smaW=6 ttd=150000 never activated. CPU 1h mean 17.78 max 29.75 bucket 10000. keep=2 / 15k floor / 40k lock unchanged. sealPark=0 why=ok at tip and later after brief under-25k dips.

D. Infra: services up. One new box freeze already official-healed (07:44 all five 289/289). Listener auto-restarted after that freeze; single peacetime slot. One new leftover official 404 W47N8@84409800 (4-tick hole). grafana_check all OK. No code/deploy this hour.

## Other

labs KO mode=KO (labReady why=active; actOk=0 actGaps=homeStor after the later under-15k dip). Never unset Memory.ops.labs. sma=6/smaW=6 ttd=150000 both never activated; sites=0.
mineral home stor O/K/KO 83600/215756/53236 at 84410491 term O/K 3000/3000 plus small GO/ZH/UH; later koLab 385. W47 term E 1284 K 52.
r7 on endTime=84413428 by Misaki (was 84412380 last patrol; not touched this hour).
Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — do not touch.
war_cmd/pulse stay stopped.
LIVE still 2b5398f7 (deploy 2026-11-19 02:28, no new game deploy this patrol). No src/ change.
