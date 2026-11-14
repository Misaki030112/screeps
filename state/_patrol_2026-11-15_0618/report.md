# 1h peacetime patrol 2026-11-15 ~06:25 Asia/Hong_Kong

LIVE ffdf767 (held, deploy@84268045 00:27; no new deploy). TIP 84272790 @ 06:22:14, later live through 84272830 @ 06:25:15. Commander not live (Memory.cmd.on=1 at=84224348 stale).

## Alerts
- FORMAL ALERT (a) HOLDS on W47 only: exact2h 18.36/30.08=61.0% (prev 17.80=59.2%) is the THIRD consecutive patrol under 70% AND short is soft (last20-300 all designed keep=2 20.00=66.5%, span=20-30 after 06:12-06:19 freeze not used alone; last200 span=200 and last300 span=230 also 20.00=66.5%; 1h 18.46=61.4%). First formal was last run after the 03:20 clear / 04:33 first short-soft. keep=2 designed 20 e/t=66.5% already under the 70% bar; last run's 10 e/t handoff 05:09-05:21 has recovered. Do not revert keep=2.
- Home (a) does NOT fire: exact2h 15.54/26=59.8% (prev 20.01=77.0%) is the FIRST under 70% after being CLEARED, but short is not soft (last200 20.30=78.1% span=200, last300 19.48=74.9% span=230, last20-30 28.00=107.7% with nUp=2; last140 23.00=88.5%). 1h 15.80=60.8% dragged by floor_bank nUp=1 from 05:23-06:10.
- FORMAL ALERT (b) RESET: analysis tip 16786 ABOVE consec-under=0 (prev tip 13880 UNDER consec-under=1). since-last min 13680@84271980 05:21 max 18096@84272650 06:12 under15k 14/38=36.8%. Recross 15006@84272090 05:29, under 14606@84272210 05:38, recross 15826@84272560 06:04 after the long freeze, later 17086@84272820 / 17186@84272830 06:25 still ABOVE. uf why=ok nUp=2 tUp=2 work=28. 20k/300t not hit (3h max 18629, best>=20k span=0).
- no formal (c)/(d)/(e)/(f).

## Energy / strategy
- nUp 2@84271970 stor 13880 → 1@84272010 05:23 stor 14326 why=floor_bank → 2@84272640 06:10 stor 17996 through tip and later.
- w8up 2→3@84272000 (handoff) → 2@84272100, last=2. W47 stor min 23402@tip max 28235@84272150 05:34, later 25400@84272830 06:25 just recrossed sealMinE=25000. softLeft was 1598/1098 = 25000-storE, not a new soft cap. sealPark 1 (known: updateSealPark clears only at nUp>=3, deferred, no src change). sealMinE=25000 phase=ready why=done bankWhy=ready keep=2 siteRem=0 feedOk=1 hubLink=1 hubReady=1 leanBank=0 threatSoft=0 softCap2=0 upLatched=0 upArm=40000 ttdW 150000 progress 3532278→3547318@tip later 3548118. home sites=0 progress 6681306→6694238@tip later 6695358. sma 6/6 ttd 150000/150000 not activated.
- model home 2h upgrade 15.09 / 1h 15.73 vs ideal 26; income 1h A 9.97 B 9.79 R 7.10 (R still the biggest harvest gap, W45N7 post-core + freezes). W47 model upgrade 2h 18.26 / 1h 18.44 vs ideal 30.03, work=20 designed. src_A still known link-metering bias (0.0 e/t; w8miner84271853 seated 26,11 harvesting). src_B 1h 10.71 / 2h 10.3. R1 1h 8.11 / 2h 5.74, R2 1h 7.14 / 2h 5.99 (better than last hour's 3.97/5.04); W47N7 containers both 2000. Biggest W47 gap remains keep=2 vs 30 e/t ideal.
- mineral: home stor E~17086 O 17324, term K~172792 O~126976; W47 stor E~23902 later 25400, K 64, term E 1096 K 18672. Labs remain OFF, not re-asked.

## Remotes / roles
- All SAFE, no cores, no hostiles (live vis). W45N8 res~2113, reserver84271847 last seated 7,37 until 84272458 (~05:52), left then ~2471 still above RES_SPAWN=2000, designed wait, not formal (c). W45N7 res~1881 (rebuilding from ~946 after core kill 04:59), reserver84272644 seated 6,39 ttl~434, rminer84272307 at 21,15. W47N7 res~2427, old reserve784271701 sat 39,27 until 84272312 when left was still ~2931, replacement reserve784272747 spawn 84272752 when left ~2491 (threshold ~2500), walking 32,26 ttl~537; 90t room_stats zero_run is sparse sampling across designed wait, not formal (c).
- Home critical roles present (miner/queen/w8filler/rminer/reserver). miners: 38,32 B miner84271887 ttl~598, 31,12 A miner84272400 ttl~1111. defs n=0. Memory.cmd not touched.

## Motion
- creep_audit --patrol exit 2 known deploy-baseline regressions vs ffdf767. creep_motion --patrol 1h/2h exit 1 known waiting_pickup / target_full / waiting_feed / no_task / queue_blocked. w8filler ABA/osc known target_full hub weave. miner84271887 excess 13.5 is B-source sit 38,32, not new stuck. w8rminer swamp/fail is W47N7 source sit, not new stuck. No new stuck/oscillation.

## CPU / infra
- CPU 1h min 13.52 max 20.17@84272770 06:20 avg 17.23 p95 19.79 bkt 10000; 2h max 23.67 was last hour 05:10, avg 17.48; not (e).
- Box freezes 05:31:28-05:32:30 ~61s (room_stats gap 84272110→84272140 30t / 132s), 05:39:59-06:04:12 ~1453s (84272220→84272560 340t / 1532s), 06:12:26-06:19:07 ~400s (84272650→84272760 110t / 473s), all self-healed.
- Backfill and listener as in infra.txt. No src change, no deploy this patrol.
