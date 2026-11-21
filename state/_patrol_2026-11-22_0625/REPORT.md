# 1h peacetime patrol 2026-11-22 06:25 Asia/Hong_Kong

Folder: state/_patrol_2026-11-22_0625
Previous: state/_patrol_2026-11-22_0522 (05:22 / delivered ~05:38, TIP 84407980, later live 84408039 / room_stats 84408050)
Live code: 2b5398f7 (2026-11-19 02:28). No src change, no deploy.lock, no game deploy.
Analysis TIP 84408860 at 2026-11-22 06:32:42 +08. Later live 84408948 ~06:38:55, later room_stats to 84408950 06:38:55.

## Alerts

FORMAL HOME upgrade CLEARS — no longer a dual after three consecutive duals since the 02:34 recovery (last patrol HOLDS as the third consecutive dual).
- exact2h 19.70/26.00=75.8% (prev 15.37=59.1%) is back above 70%
- meaningful short last800 22.90=88.1% is no longer soft
- 1h INTERP 23.33=89.7%, last1500 21.66=83.3%, last500 20.81=80.0%, last300 18.69=71.9% also above 70%
- last20-140 14.00 e/t=53.8% and last200 16.14=62.1% are nUp=1 after a brief mid-hour dip under the 15k floor (why=floor_bank) and must not be used to fire or to keep the alert; the clear is the exact2h + last800 dual rule
- model 1h measured upgrade 23.27 stor_delta -2.44 ticks 870 work=14 vs ideal 26 (snapshot at analysis already nUp=1, upgrader_bound WORK); 2h measured upgrade 19.72 stor_delta +1.91 ticks 1760
- nUp=2 from last tip 84407980 stor=19244 through 84408770, then nUp=1 from 84408780 06:27:14 stor=15464 (just after the 06:21 freeze, after min 14394@84408690) through tip 16418 and later. Live later one unboosted 14W upgrader (upgrader84407560 ttl 186 at 84408924); nUp=1 why=floor_bank storE=16968@84408905 / 17052@84408949. Do not change the 15k floor. Do not add a standing third.

FORMAL W47 upgrade STAYS CLEARED — first under after last hour's clearance, does not re-fire (needs 2 consecutive duals).
- exact2h 20.92/30.08=69.5% (prev 20.17=67.0%) is under 70% again
- meaningful short last800 20.66=68.7% is also soft again, so this patrol is a dual
- Because the previous patrol cleared, this is the FIRST under after clearance and does not re-fire. Re-fire only when a later patrol is again a dual
- last20-300 20.02-20.30 e/t=66.6-67.5% are the designed keep=2 20.00 e/t=66.5% soft window and must not fire or clear
- last500 18.65=62.0% under (span 410 includes the 06:21 STATS hole); last1500 21.23=70.6% just above; 1h INTERP 20.89=69.4% just under
- model_w8 1h alloc upgrade 20.87 stor_delta +5.19 ticks 870 cov 0.963 work=20 vs ideal 31; 2h alloc 20.95 stor_delta +0.57 ticks 1760 cov 0.981 work=20
- Do not change keep=2 / no standing third / do not unseal the 40k lock
- 40k/500t still unlocked: this hour W47 stor min 23834@84408450 06:04:37 max 32239@84408950 (at analysis max 30911@84408800), never reached 40k. Last observed >=40k remains 84406720-84406790 (70 ticks, max 41133@84406720 04:06:53) already told; 24h max still 42468@84390960 (already-known unlatched; prior best span 460 < 500). upArm=40000 upLatched=0 keep=2 upgCeil=2
- W47 stor this hour 25035@last tip -> min 23834@84408450 -> 29554@tip and later 30301@84408900 / 30747@84408930 / 32239@84408950. Live later two unboosted 10W w8upgraders (ttl 183 and 1018 at 84408924). sealPark=1 why=ok; threatSoft=0 softCap2=0 bankWhy=ready / w8day why=done phase=ready — the designed threat-soft linger after the already-told W47N7 invader has now cleared the soft-cap flags; sealPark remains 1 with why=ok, not a policy change. w8threat still 84407010. keep=2, two w8upgraders, not a standing third.

FORMAL storage-floor STAYS CLEAR. Last tip 19244 was ABOVE 15k (consec-under=0). This tip 16418 is still ABOVE 15k, so consec-under=0, does not fire.
- This hour home stor min 14394@84408690 06:21:08, under15k 3/64=4.7% of since-last samples, crossed back over 15k at 84408780 06:27:14 (15464). Tip 16418@84408860 06:32:42; later 16968@84408903, 16902@84408930, 17102@84408950; live 17102@84408948. Do not change the 15k floor.
- 20k/300t still unlocked: 3h max 19344, best >=20k tick-span=0 < 300.

No (c) formal for a lasting missing critical role: miner/rminer/queen/w8filler present throughout. Reserver was 0 for 180 ticks 84408060-84408240 (05:38:12-05:50:24); reservations stayed healthy (later ticksToEnd ~2377 / 2251 / 2446) and a reserver is present from 84408250 through tip and later. Flagged in the user log, not treated as a new shippable spawn bug this hour.

No (d) new stuck/oscillation. creep_audit --patrol rc=2 is the known REGRESSION [deploy] vs live 2b5398f7, identical deploy-class line to last hour, not alert (d). creep_motion --patrol 1h/2h rc=1 known waiting_pickup / target_full / waiting_feed / no_task / parked_threat. w8rminer swamp source is the same known watch (w8rminer84407680 1h swamp 182). W47 src_A link artifact 2h/1h —/— unmeasured is the same known accounting quirk (was 0.06/— last hour). Pattern did not change.

No (e) CPU issue: 1h mean 17.40 max 24.3 bucket min 10000 / live 10000.
No (f) infra down: postgres/grafana/listener/dashboard up; grafana_check all OK; analysis tools ran.

## Remotes

W45N8 / W45N7 / W47N7 all visible, SAFE, host=0, core=0. Later reservation ticksToEnd ~2377 / 2251 / 2446 (earlier this run 2409 / 2219 / 2414). Leftover defender rdef84406797 from the already-told 04:12 invader is gone (defs empty at 84408911; it was ttl 447 at 84407999 last patrol). Do not re-tell as a new incident. Do not start 指挥官 or Safe Mode.

## Backfill / coverage / freezes / official 404s

Official 40m backfill ticks 84408101..84408800 (700, published_bases 84408100..84408700 at game.time=84408807, tick_s=3.975, tick_s_in_use=3.97474, ts_realigned_first=9837, corrective nfix=1961 at gt=84408844 still_over_45s_vs_target=0) missing_chunks=5 W46N8@84408300, W47N8@84408300, W47N8@84408700, W45N8@84408700, W47N7@84408700; already_in_db=13895 inserted first=7666; first pass 30/35 official GETs 200. confirm 06:32:12 gt=84408853 recovered W47N8@84408700, W45N8@84408700, W47N7@84408700 inserted=2220; retry2 06:32:47 gt=84408861 inserted=123 (W45N8@84408700 already 100 distinct); late 06:34:19 gt=84408883 / post_jp 06:38:44 gt=84408947 still_404 W46N8@84408300, W47N8@84408300, W47N7@84407900, W45N8@84407700, W46N8@84407000. Just-published 84408800 at 06:38:16 gt=84408941 all_five_200=True inserted=1171 (W46N8 0 already 100, W47N8 438, W45N8 405, W45N7 0 already 100, W47N7 328). Official window plus just-published covers through 84408900 except the leftover 404 holes W46N8@84408300 and W47N8@84408300 (84408301..84408400). Coverage first-pass official_recovered=3000/3500 empty_no_creep=0 official_404=500; final official_recovered=3300/3500 official_404=200. JP chunk 84408801..84408900 all five 100/100.

NEW leftover official 404s (not yet told; fold into this 1h patrol USER_LOG):
- W46N8@84408300 (from the 06:15 half-hour; confirm 06:32:12 / retry2 06:32:47 / late 06:34:20 / post_jp 06:38:45 still 404; listener 0/100; hole 100 ticks 84408301..84408400)
- W47N8@84408300 (from the 06:15 half-hour; confirm 06:32:14 / retry2 06:32:49 / late 06:34:23 / post_jp 06:38:46 still 404; listener 0/100; hole 100 ticks 84408301..84408400)
- W47N7@84407900 (from the quiet 05:30 backfill, still-untold after 06:15; aged out of this 40m window start 84408101; re-confirmed 06:32:26 / late 06:34:25 / post_jp 06:38:57 still 404; listener 0/100; hole 100 ticks 84407901..84408000)

Already-told leftovers W45N8@84407700 (0/100) and W46N8@84407000 (85/100, hole 15 ticks 84407001..84407015) were re-confirmed still 404 this hour, do not re-tell as new. Older leftovers W45N8@84406400 / W46N8@84406600 / W46N8@84406700 / W45N7@84403800 / W45N7@84403700 and earlier aged out of this 40m window, not retried as new, do not re-tell. First-pass 404s W47N8@84408700, W45N8@84408700, W47N7@84408700 recovered on confirm (all five 100/100 for 84408701..84408800).

NEW box freezes (not yet told):
- 盒子休眠 05:52:44-06:04:12 (683s; already healed; STATS 84408271..84408449, 179t; official-filled W46N8 79/179, W47N8 79/179, W45N8 179/179, W45N7 179/179, W47N7 179/179 — W46N8 and W47N8 short because leftover official 404 W46N8@84408300 and W47N8@84408300 cover 84408301..84408400; listener auto-restart 06:04:15, python 2290083 started 06:04:25)
- 盒子休眠 06:21:56-06:26:26 (269s; already healed; STATS 84408691..84408779, 89t; official-filled ALL FIVE 89/89 after confirm recovered the 84408700 chunks; first-pass already had W46N8 and W45N7 @84408700; listener auto-restart 06:26:29, python 2299582 started 06:26:38)

The 06:26 listener python pid change (2290083 -> 2299582) is this box-freeze auto-restart, not a tools/services.sh status restart. services.sh only starts run_listener.sh when that wrapper is down; parent run_listener.sh 4035476 has been running since Nov 13. No second listener was started. This run did not restart the listener again.

No new short listener WS interruption this hour beyond the two box freezes (already-told 05:25:19-05:27:20 remains already told). Already-told freezes 05:17:11-05:23:17 and 04:41:06-04:59:17 (and older 04:18 / 03:47 / 02:44 / 02:13 / 01:50 / 01:18 / 00:50 / 00:11 / 23:53 and older) remain already told; do not re-tell.

Listener healthy at end: 1 process (2299582 since 06:26:38, parent run_listener.sh 4035476 since Nov 13), yield_absent=True, peacetime 1-slot 5:5:1:1 (listener_rot W47N8 at 06:38:12), no second listener, war_cmd/pulse not touched. Console replies did not stall after the 06:26 restart; listener was not manually restarted.

## Pillars

A. Motion: no new stuck/oscillation. Known waiting_pickup / target_full / waiting_feed / no_task / parked_threat (w8defender leftover parked_threat until ~06:12, then expired). w8rminer swamp-source watch unchanged. Home/W47 upgraders waiting_feed at known rates. Trajectories after official fill plus JP cover the hour except leftover 404 holes W46N8/W47N8@84408300 and unpublished tail after 84408900.

B. Energy / flow: home exact2h now 75.8% (clears). Mid-hour storage dipped to 14394 then recovered; designed 15k floor now holds nUp=1 why=floor_bank with tip/later still above 15k. W47 keep=2 delivers ~20 e/t short windows and 20.92 exact2h (69.5%), first under after clearance. Sources and remotes flowing; no new invader spend.

C. Strategy / buildings / remotes / CPU: remotes SAFE host=0 core=0, reservations healthy. sites=0. labs remain KO (actOk=1 actGaps=empty, why=active); never unset Memory.ops.labs; never re-ask market. r7 still on endTime=84411346 by Misaki (was 84411330 last patrol; not touched). sma=6/smaW=6 ttd=150000 never activated. CPU 1h mean 17.40 max 24.3 bucket 10000. keep=2 / 15k floor / 40k lock unchanged. sealPark=1 why=ok after threat-soft flags cleared.

D. Infra: services up. Two new box freezes already official-healed (05:52 short on W46N8/W47N8 due to leftover 404s; 06:21 all five 89/89). Listener auto-restarted after the 06:21 freeze; single peacetime slot. Leftover official 404s listed above remain unfilled holes. grafana_check all OK. No code/deploy this hour.

## Other

labs KO mode=KO (actOk=1 actGaps= empty; labReady why=active). Never unset Memory.ops.labs. sma=6/smaW=6 ttd=150000 both never activated; sites=0.
mineral home stor O/K/KO 84400/216556/52436 term O/K 3000/3000 plus small GO/ZH/UH, koLab 390; W47 term E 1284 K 52.
r7 on endTime=84411346 by Misaki (was 84411330 last patrol; not touched this hour).
Memory.cmd stale on=1 at=84224348 c={} s={} v=1 — do not touch.
W47 src_A link artifact —/— ; src_B 2h/1h 6.87/5.35, R1 5.96/6.25, R2 5.94/6.29.
Critical roles present at tip and later (miner 2, rminer 2, queen 2, w8filler 2, reserver 1, w8miner 3).
LIVE still 2b5398f7 (deploy 2026-11-19 02:28, no new game deploy this patrol). No src/ change. No code change and no deploy this hour (src clean, deploy.lock absent, live still 2026-11-19 02:28 code 2b5398f7). Locked policy: designed 15k floor holding nUp=1 (why=floor_bank) is not a number we change this hour.
