# 1h peacetime patrol 2026-11-22 07:25 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_0725
Previous: state/_patrol_2026-11-22_0625 (06:25 / delivered ~06:44, TIP 84408860, later live 84408948 / room_stats 84408950)
Live code: 2b5398f7 (2026-11-19 02:28). No src change, no deploy.lock, no game deploy.
Analysis TIP 84409680 at 2026-11-22 07:28:58 +08. Later live 84409752 ~07:33:50, later room_stats to 84409750 07:33:43.

## Alerts

FORMAL W47 upgrade RE-FIRES — second consecutive dual after the 05:38 clearance (last patrol was the first dual and did not re-fire).
- exact2h 20.44/30.08=68.0% (prev 20.92=69.5%) is still under 70%
- meaningful short last800 19.69=65.5% is still soft, so this patrol is again a dual
- Because the previous patrol was already a dual after clearance, this is the SECOND consecutive dual and formally re-fires
- last20-140 20.00-20.04 e/t=66.5-66.6% are the designed keep=2 20.00 e/t=66.5% soft window and must not fire or clear
- last200 21.77=72.4%, last300 22.01=73.2%, last500 21.59=71.8% are above 70% but are context only and must not block the fire
- last1500 20.16=67.0%; 1h INTERP 19.72=65.6%
- model_w8 1h alloc upgrade 19.72 stor_delta -2.74 ticks 860 work=20 vs ideal 31; 2h alloc 20.39 stor_delta +1.91 work=20 vs ideal 30.03
- Do not change keep=2 / no standing third / do not unseal the 40k lock
- 40k/500t still unlocked: this hour W47 stor min 28356@84409660 07:27:37 max 33177@84409000 06:42:19, never reached 40k. Last observed >=40k remains 84406720-84406790 (70 ticks, max 41133@84406720 04:06:53) already told. upArm=40000 upLatched=0 keep=2 upgCeil=2
- W47 stor this hour min 28356 max 33177@84409000 06:42:19, tip 28356@84409680, later 28839@84409720-84409740 / 28539@84409750; live 28539@84409752
- Live later two unboosted 10W w8upgraders (ttl 218 and 822 at 84409724). sealPark=0 why=ok (stor above the 25k seal line); threatSoft=0 softCap2=0 bankWhy=ready / w8day why=done phase=ready. Last patrol still had sealPark=1 why=ok; opening is the designed storage-seal reaction, not a policy change. w8threat still 84407010. keep=2, two w8upgraders, not a standing third.

FORMAL HOME upgrade STAYS CLEARED — last patrol cleared (exact2h 19.70=75.8% back above 70%). This hour exact2h 22.67/26.00=87.2% (prev 19.70=75.8%) stays well above 70%.
- meaningful short last800 21.79=83.8% is hard
- 1h INTERP 21.13=81.3%, last1500 22.41=86.2%, last500 21.47=82.6%, last300 19.73=75.9% also above 70%
- last20-140 14.00 e/t=53.8% and last200 15.59=60.0% are nUp=1 after a mid-hour dip under the 15k floor (why=floor_bank) and must not be used to fire
- model 1h measured upgrade 21.25 stor_delta +0.14 ticks 860 work=14 vs ideal 26 (upgrader_bound energy); 2h measured upgrade 22.62 stor_delta -1.81 ticks 1740
- nUp=1 at last tip 84408860 stor=16418, nUp=2 from 84408980 06:40:57 stor=17312, brief nUp=3 84409030 06:44:21 stor=17748 (handoff overlap, not a standing third), nUp=2 from 84409110, then nUp=1 from 84409530 07:18:32 stor=14288 through tip 15988 and later. Live later one unboosted 14W upgrader (upgrader84408974 ttl 800 at 84409724); nUp=1 why=floor_bank storE=17414@84409690 / 17214@84409752. Do not change the 15k floor. Do not add a standing third.

FORMAL storage-floor STAYS CLEAR. Last tip 16418 was ABOVE 15k (consec-under=0). This tip 15988 is still ABOVE 15k, so consec-under=0, does not fire.
- This hour home stor min 14088@84409510 07:17:09, under15k 6/56=10.7% of since-last samples, crossed back over 15k at 84409540 07:19:14 (15188). Tip 15988@84409680 07:28:58; later 17414@84409690 then 16714-17214; live 17214@84409752. Do not change the 15k floor.
- 20k/300t still unlocked: 3h max 19344, best >=20k tick-span=0 < 300.

No (c) formal for a lasting missing critical role: miner/rminer/queen/w8filler present throughout. Home reserver was 0 for 270 ticks 84409050-84409320 (06:45:42-07:04:00, overlapping the 06:50 box freeze); reservations stayed healthy (later ticksToEnd ~2285 / 2035 / 2626) and a reserver is present from 84409320 through tip and later (live reserver=2). W47N7 reserve7 was 0 from 84409450 07:13:00 through tip and later live (roles have reserver=2, no reserve7); W47N7 reservation stayed healthy at ~2626. Flagged in the user log, not treated as a new shippable spawn bug this hour.

No (d) new stuck/oscillation. creep_audit --patrol rc=2 is the known REGRESSION [deploy] vs live 2b5398f7, identical deploy-class line to last hour, not alert (d). creep_motion --patrol 1h/2h rc=1 known waiting_pickup / target_full / waiting_feed / no_task / queue_blocked. w8rminer swamp source is the same known watch (w8rminer84407680 1h swamp 84 / 2h 263). parked_threat / leftover rdef only appear in the 2h window (already-told expired defender), not in 1h. Pattern did not change.

No (e) CPU issue: 1h mean 16.85 max 29.75 bucket min 10000 / live 10000.
No (f) infra down: postgres/grafana/listener/dashboard up; grafana_check all OK; analysis tools ran; 40m backfill missing_chunks=0; JP 84409600 all five 200.

## Remotes

W45N8 / W45N7 / W47N7 all visible, SAFE, host=0, core=0. Later reservation ticksToEnd ~2285 / 2035 / 2626 (earlier this run 2253 / 2003 / 2658). defs empty. Do not start 指挥官 or Safe Mode.

## Backfill / coverage / freezes / official 404s

Official 40m backfill ticks 84408901..84409600 (700, published_bases 84408900..84409500 at game.time=84409663, tick_s=4.094, tick_s_in_use=4.094, ts_realigned_first=0, no corrective) missing_chunks=0; already_in_db=19437 inserted first=7010; first pass 35/35 official GETs 200. confirm / retry2 / late skipped no targets. Just-published 84409600 at 07:33:07 gt=84409741 all_five_200=True inserted=3070 (W46N8 454, W47N8 1559, W45N8 374, W45N7 364, W47N7 319). Official window plus just-published covers through 84409700 all five 100/100. Coverage official_recovered=3500/3500 empty_no_creep=0 official_404=0; JP chunk also 500/500.

NEW leftover official 404s: none. Already-told leftovers W46N8@84408300 / W47N8@84408300 / W47N7@84407900 / W45N8@84407700 / W46N8@84407000 (85/100, hole 15 ticks 84407001..84407015) remain 404, aged out of this 40m window start 84408901, were not retried, do not re-tell as new. Older leftovers aged out, do not re-tell.

NEW box freezes (not yet told):
- 盒子休眠 06:50:03-07:02:08 (725s; already healed; STATS 84409111..84409299, 189t; official-filled ALL FIVE 189/189; listener auto-restart 07:02:11, python 2315680 started 07:02:21)
- 盒子休眠 07:20:32-07:26:28 (356s; already healed; STATS 84409551..84409649, 99t; official first pass filled 50/99 through 84409600; after JP 84409600 all five 99/99; listener auto-restart 07:26:31, python 2325173 started 07:26:41)

The 07:26 listener python pid change (2315680 -> 2325173) is this box-freeze auto-restart, not a tools/services.sh status restart. services.sh only reported ok listener; parent run_listener.sh 4035476 has been running since Nov 13. No second listener was started. This run did not restart the listener again.

No new short listener WS interruption this hour beyond the two box freezes (already-told 05:25:19-05:27:20 remains already told). Already-told freezes 06:21:56-06:26:26 and 05:52:44-06:04:12 (and older 05:17 / 04:41 / 04:18 / 03:47 and earlier) remain already told; do not re-tell.

Listener healthy at end: 1 process (2325173 since 07:26:41, parent run_listener.sh 4035476 since Nov 13), yield_absent=True, peacetime 1-slot 5:5:1:1 (listener_rot W46N8 at 07:34:03, ~200s left), no second listener, war_cmd/pulse not touched. Console replies did not stall after the 07:26 restart; listener was not manually restarted.

## Pillars

A. Motion: no new stuck/oscillation. Known waiting_pickup / target_full / waiting_feed / no_task / queue_blocked. w8rminer swamp-source watch unchanged. Home/W47 upgraders waiting_feed at known rates. Trajectories after official fill plus JP cover the hour except the unpublished tail after 84409700.

B. Energy / flow: home exact2h 87.2% stays cleared. Mid-hour storage dipped to 14088 then recovered; designed 15k floor now holds nUp=1 why=floor_bank with tip/later still above 15k. W47 keep=2 delivers ~20 e/t short windows and 20.44 exact2h (68.0%), second dual after clearance so formal re-fires. Sources and remotes flowing; no new invader spend.

C. Strategy / buildings / remotes / CPU: remotes SAFE host=0 core=0, reservations healthy. sites=0. labs remain KO (actOk=1 actGaps=empty, why=active); never unset Memory.ops.labs; never re-ask market. r7 still on endTime=84412380 by Misaki (was 84411346 last patrol; not touched). sma=6/smaW=6 ttd=150000 never activated. CPU 1h mean 16.85 max 29.75 bucket 10000. keep=2 / 15k floor / 40k lock unchanged. sealPark=0 why=ok after stor stayed above the 25k seal line.

D. Infra: services up. Two new box freezes already official-healed (06:50 all five 189/189; 07:20 all five 99/99 after JP). Listener auto-restarted after the 07:20 freeze; single peacetime slot. No new official 404s. grafana_check all OK. No code/deploy this hour.

## Other

labs KO mode=KO (actOk=1 actGaps=empty; labReady why=active). Never unset Memory.ops.labs. sma=6/smaW=6 ttd=150000 both never activated; sites=0.
mineral home stor O/K/KO 84400/216556/52436 term O/K 3000/3000 plus small GO/ZH/UH, koLab 790; W47 term E 1284 K 52.
r7 on endTime=84412380 by Misaki (was 84411346 last patrol; not touched this hour).
Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — do not touch.
war_cmd/pulse stay stopped.
LIVE still 2b5398f7 (deploy 2026-11-19 02:28, no new game deploy this patrol). No src/ change.
