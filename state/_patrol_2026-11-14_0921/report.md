# 2026-11-14 09:31 Asia/Hong_Kong 1h peacetime patrol

TIP 84255820 09:23:09 HKT (window since last tip 84255030). Later live through 84255930 09:31.
LIVE 4ff78b4 held (deploy@84239549 13:26); no new deploy.

## Alerts
FORMAL ALERT (a) holds: home exact2h 13.35/26=51.4% (prev 13.85=53.3%) is 40th consecutive <70%, short also soft; W47 exact2h 16.89/30.08=56.1% (prev 16.88=56.1%) is 42nd consecutive, short 20.00=66.5% still soft.
No formal (b): tip stor 14178 UNDER consec-under=1 (prev tip 15358 ABOVE consec-under=0 RESET); later 16088@84255930 09:31 recrossed ABOVE.
No formal (c)/(d)/(e)/(f).

## Energy
Home RCL7 58.65% p6413166 stor14178@tip; later p6414302 stor16088. 1h 13.14=50.5%. nUp=1 floor_bank, handoff nUp=2 84255590-84255800 (09:06-09:21) then nUp=1; tip short 4 e/t was waiting_feed on new upgrader84255581, later last20=14.00.
W47 RCL7 29.45% p3219864 stor25427@tip later 3222064 / 25156; 1h 20.00=66.5% recovered from last hour handoff dip. keep=2 phase=ready sealPark on sealMinE=25000 softLeft=0 softCap2=1. w8threat 84254373 expired ~84255873 / 09:27, bankWhy threatSoft→ready, threatSoft=0.
20k/300t home not hit (3h max 16896).

## Remotes / motion
W45N7 Invader-core alert 84255099 08:30 spawn_start defender84255100 (5000 body, not 2500-capped). Defender walked in, 0 combat (hits 5000 throughout), recycled home. Live cores=0 host=0 SAFE. Reserver84254916 parked_threat at home; reservation vis dipped to 759 then 841 at 09:31 (climbing, reserver84255508 on 6,39). W45N8/W47N7 vis 1964/2812 Misaki. reserve7 designed wait 130t at window start then reserve784255370 on 39,27.
audit --patrol EXIT2 same deploy-window metric shift vs 4ff78b4 as last hour. motion EXIT1 waiting_pickup/target_full/no_task/waiting_feed/queue_blocked/parked_threat. w8filler ABA 162/109 known hub weave. rminer84254757 osc 42 is travel/threat detour onto W45N7 source, not new post-deploy stuck. Not shipped.

## CPU / infra
CPU 1h avg 17.17 max 20.57@84255800 p95 19.5 bkt min 9998 now 10000; 2h avg 17.53 max 24.17. Not (e).
Two box freezes 08:35:13-09:00:35 (1521s) and 09:08:44-09:21:09 (739s), listener restarts 09:00:38 / 09:21:12 pid 2492451, self-healed. Peacetime single-slot 5:5:1:1 yield absent; rot later i=3 W45N7. Memory.cmd.on=1 at=84224348 stale c={} s={}, commander not live, not reclaimed. war_cmd/pulse stopped. services.sh ok, grafana 20/20, q.py OK, DB writers fresh after thaw.
history_backfill 40min game.time=84255799 published 84255000-84255600 ticks 84255001-84255700 (700) inserted=6904 already_in_db=22381 ts_realigned=0 tick_s=4.416 missing_chunks=1 W45N7@84255200 official 404 (also confirmed 09:03/09:04 and this run). Other four rooms 700/700. W45N7 distinct 488 (official hole + carry-over). Unpublished 84255700+ expected. W47N8 live filled most of trailing ticks.

## Other
labs OFF actOk=0 actGaps=homeStor why=ready, do not enable, do not re-ask.
sma 6/6 not activated; ttd 150000/150000.
minerals hsO=17324 termO=126976 termK=158528 W47 termE=1082 termK=0 wsK=64.
home lab 34,20 29410→31296/50000 only remaining home site.
ledger 2465t (~3.03h) home up 11.49 (undercount) spawn net 16.02 build 4.75; W47 up 17.94 spawn net 13.94 build 0.12.
No src change from this patrol.
