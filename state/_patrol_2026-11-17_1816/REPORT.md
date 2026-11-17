# 1h peacetime patrol 2026-11-17 18:26 Asia/Hong_Kong

Analysis TIP 84320740 @ 2026-11-17 18:20:22 Asia/Hong_Kong; later live to 84320830 18:27:25.
LIVE 85c19c2e (held, deploy@84303299 2026-11-16 19:19); no new deploy this patrol.

## Alerts
- FORMAL W47 upgrade ALERT HOLDS (sixth consecutive dual-condition).
- HOME upgrade CLEAR (exact2h 86.4% ABOVE 70%).
- HOME storage formal CLEAR (tip 16297 later 16189 ABOVE 15k; consec-under=0). Mid-hour dip min 14313@18:06 under15k 11/58=19.0% — not formal.
- No formal missing critical role / new stuck / CPU / infra.

## Upgrade & storage
- HOME exact2h 22.47/26=86.4% (prev 23.14=89.0%); 1h 23.31=89.6%; short last20-200 14.00=53.8% (designed nUp=1 after 15k floor); last300 17.29=66.5%; last500 21.06=81.0%; last800 23.15=89.0%.
- W47 exact2h 19.21/30.08=63.9% (prev 18.83=62.6%); 1h 20.10=66.8%; short all soft (last20-140 ~12-14 e/t, last200 15.39=51.2%, last300 16.93=56.3%, last500 19.00=63.2%, last800 20.11=66.9%).
- HOME stor tip 16297, later 16969/15889/16189; min 14313@84320560 18:06; max 18623@84320060 17:26. 20k/300t unlocked (6h max 20244@13:37, span 20t).
- W47 stor tip 27742 later 26542; this hour max 34470@17:26; 40k/500t unlocked (span still 84317690-84317950 dt=260t max 42880).
- bankWhy=ready softCap2=0 threatSoft=0 sealPark=0 keep=2 (threatSoft leftover cleared after w8guard84318755 last 29,5@17:51). Did not change softCap.

## Motion / handoffs
- HOME: upgrader84319714 left 29,30 @18:04 after stor under 15k; 19476 stayed 30,30; nUp=1 from 84320540 18:04 until replacement upgrader84320795 hatching 30,34 @84320796 18:24; nUp=2 again @84320830 18:27 (still spawning).
- W47: w8upgrader84319110 last_loaded 14,26@18:10:55, gone after 18:13:14; 19610 stayed 14,27; 20564 spawn 33,30@18:06:56, pocket bounce 32,30/33,31, live seated 12,25 e=10 ~18:23 (~220t). Known CMV spawn-pocket issue. Do not start routing fix.
- creep_audit --patrol exit 2: same known REGRESSION [deploy] vs 85c19c2e.
- creep_motion --patrol 1h/2h exit 1: known waiting_pickup / target_full / waiting_feed / parked_threat / queue_blocked, not new stuck.

## Remotes / roles
- All vis SAFE, cores 0, host 0; res ~2105 / 2323 / 2591 (W45N8/W45N7/W47N7).
- Reservers expired (19803@17:54 W45N8, 20113@~18:17 W45N7, 19824@17:56 W47N7); reservations still healthy — designed wait, not formal.
- Critical owned roles present (miner/queen/w8filler/rminer).

## CPU / infra
- CPU 1h mean 18.46 max 36.0@84320100 17:30 wake (already seen last patrol); 2h mean 18.32; bucket ~10000.
- pg / grafana:200 / dashboard:200 / listener single-slot 5:5:1:1 (now W46N8), commander not holding, no yield file.
- Official 40m backfill ticks 84320001..84320700, game.time=84320712, published 84320000..84320600; first-pass inserted=4348 already_in_db=21644 missing_chunks=1 404 W47N7@84320600; confirm 18:27:00 recovered inserted=220, coverage 3500/3500; leftovers W47N8@84319900 and older still 404.
- tick_s first 4.62058 printed 4.621 ts_realigned_first=6617; later_mean_robust 4.71737 no corrective (vs_later over45 higher than vs_first).
- Box pause 17:45:39-17:55:57 (~619s, room_stats gap 84320300-84320430 dt=130t); official history filled the trajectory hole.
- Labs OFF mode=KO ready=0; Memory.cmd.on=1 at=84224348 stale not touched; sma=6/smaW=6 ttd=150000 never activated; sites=0.
- Minerals home O 130000 K 191255 term 3000/3000; W47 K 64 term E 1480.

## Models
- HOME model 1h upgrade 23.41 stor_delta -3.12 spawn_util 0.654; 2h 22.96 / -0.43; ideal 26.
- W47 model 1h upgrade 20.31 stor_delta -10.25; 2h 19.5 / +0.41; ideal 30.03. Biggest gap: keep=2 plus ~220t unseated handoff.

No code or deploy this patrol.
