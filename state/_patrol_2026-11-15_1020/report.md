# Patrol 2026-11-15 10:25 Asia/Hong_Kong (1h peacetime)

TIP 84276150 @ 10:21:17 Asia/Hong_Kong. LIVE ffdf767 (held, deploy@84268045 00:27; no new deploy). Last patrol TIP 84275360 @ 09:28.

## ALERTS
- FORMAL ALERT (a) HOLDS on W47 only: exact2h 19.04/30.08=63.3% (prev 19.04=63.3%) is the SEVENTH consecutive patrol under 70% AND short is soft (last20-30 span=10 after sparse samples not used alone; last70-200 all 20.00=66.5% span=70-200; last300 span=200 also 20.00=66.5%; 1h 20.00=66.5%). keep=2 designed 20 e/t=66.5% already under the 70% bar. Do not revert keep=2.
- Home (a) stays CLEARED: exact2h 23.56/26=90.6% (prev 21.68=83.4%) ABOVE 70%; 1h 25.40=97.7%; short last200 27.32=105.1% span=200 (last300 also span=200); nUp=2 why=ok work=28 through tip.
- FORMAL ALERT (b) stays RESET at analysis tip 16974 ABOVE consec-under=0 (prev tip 17532 ABOVE). since-last min 15232@84275410 09:29 max 17770@84275980 10:09 under15k 0/37=0.0%. later 15374@84276180 / 15474@84276190 / 15574@84276200 10:24 still ABOVE (designed spawn+refill). 20k/300t not hit (3h max 18992, best>=20k span=0).
- (c) no: critical roles present (miner/rminer/queen/w8filler/w8miner/w8rminer). Home reserver 50-tick zero at tip is handoff (reserver84276167 spawning). reserve7=2 on W47N7.
- (d) no new stuck/oscillation. audit exit 2 / motion exit 1 are the same known REGRESSION [deploy] vs ffdf767 (cpu/trip metrics) and known waiting_pickup / target_full / no_task. Not worse in a material new way.
- (e) no: CPU 1h avg 18.91 max 23.05@84275540 09:38, bucket 9994-10000.
- (f) no: infra self-healthy this run.

## W47N7 Invader core (this hour)
- inc=84275423 alert_new 09:30 why=core lv0 at (41,30) hits 100000, invOnly, 0 hostile creeps. pauseStart=84275423.
- rdef84275457 spawn_start 84275457 09:32 waited=34, hits=5000 (full budget, not ~2500 cap), spawned in W47N8, entered W47N7 84275647 09:45, sat/fought adjacent at (40,30).
- Official history: 100k@84275423-84275600; 94k@84275700; 19k@84275800; killed 84275827 09:58 became ruin 6af911bfcd37876cfeb5e866 at (41,30). dur=404. rdef hits stayed 5000; last seen 84275875 10:01 leaving at (18,0). Live defs n=0, cores=0, host=0, SAFE since 84275827.
- Box-sleep 09:39-10:07 (room_stats gap 84275550-84275950, 400t) missed defend/arrive/cleared incident rows; reconstructed from official history. Memory.th.why/gone still stale (gone=84247906); `since` is correct. No src change (platform gap, state already SAFE).
- threatSoft=0 softCap2=0 (not latched this time). sealPark=1 known deferred.

## Energy / strategy
- Home RCL7 61.90% p=6768440; model 2h upgrade 23.43 e/t, 1h 25.97. Biggest gap: none material (A/B ~10 e/t).
- W47 RCL7 33.02% p=3610750; model 2h 19.05 / 1h 20.07 e/t. src_A actual ~0 is the known linkA->ctl measurement artifact (w8miner still on (26,11)). R1/R2 1h 5.27/3.77 dragged by core pause. Biggest designed gap remains keep=2 cap.
- W47 stor since_last min 22082@09:36 max 28236@09:25 (last tip) last 25180 later 25070. 3h max 38466@08:37, zero samples >=40k, not a latch. keep=2 upArm=40000 upLatched=0 bankWhy=ready.
- w8up 2→3@84276140 10:20 handoff (w8upgrader84274684 ttl~58 + newborn 84276123); not the 40k latch. After-tip upgrade briefly ~10 e/t as the newborn walks in; do not treat as policy change.
- Labs OFF. Minerals: home stor O=17324; terminal O=126976 K=172792; W47 stor K=64; W47 terminal K=25512 E=1096. ttd 150000 both, sma=6 both, never activated. sites=0. Memory.cmd leftover empty on=1 at=84224348, not live command. No yield file.

## Motion / infra
- creep_audit --patrol exit 2; creep_motion 1h/2h exit 1. Known.
- Listener peacetime 1-slot 5:5:1:1 (10:21 W46N8, 10:25 W47N8). services all ok. Grafana OK.
- 40m history backfill: 84275401..84276100 tick_s=4.325 inserted=7032 already=19790 ts_realigned=2148. Official 404s retried still 404: W45N7@84275600, W47N8@84275800. Unpublished latest ~50-100 ticks expected. Hour coverage otherwise full (W46N8 missing only unpublished 22t at tip).
- No src change, no deploy.
