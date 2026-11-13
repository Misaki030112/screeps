# Patrol 2026-11-13 22:22 Asia/Hong_Kong (1h peacetime)

TIP 84246880 2026-11-13 22:24:48 Asia/Hong_Kong; later live 84246910 22:27 stor 15344 still ABOVE. LIVE 4ff78b4 (held, deploy@84239560 13:26; no new deploy this patrol).

## ALERTS
FORMAL ALERT (a) holds. Home exact2h 12.73/26=48.9% (prev 12.41=47.7%) is 29th consecutive <70% AND short still soft (post-thaw last20-200 all 14.00=53.8% but only span 20t after the 22:12-22:22 freeze; last300 14.39=55.3% still soft; 1h 14.10=54.2% recovered vs last hour 11.30=43.5% after ctl-link came back). nUp=1 almost all hour; designed nUp=2 handoff only during the second freeze (upgrader84246722 spawned 84246722, old upgrader84245253 aged ~84246803, ttl matched; uf nUp=1 work=14 at thaw).
W47 exact2h 0.00/30.08=0.0% (prev 0.0%) is 31st consecutive <70% AND short all 0.00 e/t, progress flat 3150854, keep=1 do not revert: authorized sites progressed (W47 lab 28,37 COMPLETED this hour, look hits 500, was 49319; 28,38 0→12909; 27,40 3662→5942; home 33,22 12456→20136, 34,20 still 4303 second hour no progress, watch; labsN=4) plus minCont 37,44 still 0/5000, roads 17,47 and 31,35 finished, 37,42 and 36,43 still 0, siteRem 103459→86809, roadCrit 34→31, threatSoft=0.
Home stor analysis tip 16394 ABOVE consec-under=0 (prev tip 15398 ABOVE; formal (b) not standing; since-last min 14146@84246650 22:07 max=tip 16394 under15k 4/29=13.8%; recrossed 16194@84246860 22:23; later live 15194@84246895 / 15344@84246910 22:27 still ABOVE). 20k/300t not hit (3h max 17149, best>=20k span=0).
No formal (b)/(c)/(d)/(e)/(f).

## Energy / strategy
Biggest gaps: home upgrade capped at 14 e/t by 15k floor (1h recovered to 14.10 after last hour's ctl-link starve; ctl never 0 this hour, tip 1346). W47 upgrade 0 by authorized minBuild. Home 2h income A/B ~9.99/10.00 R 8.13; model flow nets R 6.86 / W45N7 4.54. W47 2h R1/R2 7.09/7.36 vs ~9.5 (1h R1 4.48 likely undercount from W47N7 official 404s during freezes), same known watch, not shipped.
Ledger 0.92h (753t since last snap) home up 11.98 (undercount) spawn net 13.12 build 9.80; W47 up 0.00 spawn net 11.49 build 23.39.
HOME W46N8 RCL7 57.55% (p6293408 stor16394@84246880 22:24 HKT; later p6293828 stor15344@84246910 22:27 still ABOVE) live uf why=floor_bank nUp=1 tUp=1 work=14 surplus=+194 floor=15000 allowExtra=20000 ctl 1216/ema 1547.
W47 stor min 4501@21:32 max 7298@22:23 live 6698 later 6845-7592 keep=1 phase=minBuild bankWhy=minBuild leanBank=1 threatSoft=0 sealPark on sealMinE=25000 hubLink=1 feedOk=1 upLatched=0.

## Remotes / motion / defence
W45N8/W45N7/W47N7 vis res 2326/1961/2762 user Misaki cores0 host0, live stats SAFE (W45N7/W47N7 why=killed leftover). No hostiles and incidents=0 this hour.
Leftover home defender84244890 aged 84246533 ~21:59 at W45N8 24,10 hits 4800, designed TTL (403 remaining at 21:31), no recycle.
reserve784246476 on station W47N7 39,27 ttl ~168-182, r7 endTime 84249655 left≈2750>2500 spawn waits. Early room_stats zero_run 150t 21:29-21:40 after last reserve7 aged ~84246035 is designed, report not formal (c).
Home reserver84245662 aged ~84246273 at W45N7 7,41; reserver84246163 on W45N8 7,37 through 84246774; replacement reserver84246880 spawned 84246880, live walking W45N8 1,22 ttl 572 (W45N7 res 1961 < RES_SPAWN). Brief reserver count 0 only 10t at 84246860-84246870, not (c).
audit --patrol exit 2 is same known deploy-window metric shift vs 4ff78b4 (hauler waiting_pickup, queen target_full, miner trip, wbuilder cpu), motion --patrol exit 1 waiting_pickup/target_full/no_task/queue_blocked/waiting_feed; w8filler ABA is known target_full hub weave, hauler84245929 empty waiting_pickup same known, defender leftover queue_blocked until designed age, no new stuck/oscillation after last deploy, not shipped.

## Infra
Two box freezes this hour, both self-healed: 21:40:46-22:01:58 1271s room_stats 310t/1336s 84246270-84246580, listener restart 22:02:13, then subscribe-limit-reached 22:02/05/07/09 (known after thaw); no-STATS 183s at 22:12:25 then box freeze 22:12:40-22:22:22 577s room_stats 190t/839s 84246670-84246860, listener restart 22:22:35 pid 2321082. Peacetime single-slot 5:5:1:1 (yield absent, rot i=0 W46N8 at 22:22:37 left~411s). Memory.cmd.on=1 at=84224348 stale c={} s={}, commander not live, not touched, not reclaimed. war_cmd/pulse stopped NO_WAR_PROCS.
services.sh all ok postgres/views/grafana200/listener/dashboard200; grafana_check 20/20; q.py live OK (skipped known-bad lab/min/soft2 syntax, lab2/min2/opsRem/vis landed); DB writers fresh (room_stats lag ~17s tip 84246880, later 84246910; creep_ticks few seconds).
40m backfill game.time=84246856 published 84246100-84246700 ticks 84246101-84246800 (700) inserted=9794 already_in_db=14599 ts_realigned=0 tick_s=4.369 missing_chunks=4; confirm GET 22:24:48 and retry2 22:27:34 all four still official 404, 0 live ticks: W45N7@84246300 and W47N7@84246300 (also 404 at 22:07 half-hour), new W46N8@84246500 (mid-window, adjacent 84246400 and 84246600 both 200, overlaps end of first freeze), W47N7@84246700 (in published range, still 404). W47N8/W45N8 700/700, W46N8 600/700, W45N7 600/700, W47N7 500/700. Unpublished latest ~100t after 84246800 expected (W46N8 live listener filled from ~84246800 while rotated on home). Leftover official 404s outside this window unchanged (W47N8@84243700, W47N8@84243100, W45N8@84242900, 0 live ticks).
CPU 1h avg 17.43 max 22.3@84246160 21:31 p95 20.43 bkt min 9997 now 10000, 2h avg 17.41 max 24.19 leftover@84245450, not (e).
Labs stay OFF (labReady actOk=1 actGaps="" why=ready homeStor 15394, do not enable, do not re-ask). sma 6/6 ttd=150000/126570 not activated.
minerals hsO=17324 termO=126976 termK=151080 W47 termE=1338 termK=56 wsK=64; min line why=minCont (site 37,44 still 0/5000), flipReady=0 flipGaps=already.
no layout change shipped; no new deploy; no src change from this patrol.
