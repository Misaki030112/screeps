# Patrol 2026-11-14 18:28 Asia/Hong_Kong (1h peacetime)

LIVE 4ff78b4 (held, deploy@84239549 2026-11-13 13:26; no new deploy this patrol). TIP 84263190 18:27:48 HKT, later 84263260 18:32:59.

## Alerts
No formal ALERT this run.

Home exact2h 17.00/26=65.4% (prev 13.75=52.9%) is still <70% (would have been the 49th consecutive) BUT short is no longer soft (last20 24.00=92.3%, last30 25.33=97.4%; last70-100 only span=40 after the 18:17-18:24 freeze so not used alone; last140 24.71=95.1%, last200 26.24=100.9%, last300 26.83=103.2%, 1h 20.74=79.8%). Last run home (a) formally held; this run it does not, same short-window rule used for W47 at 17:25 / 14:27 / 12:25. Cause of the 2h still being under 70%: nUp stayed 1 why=floor_bank until 84262850 18:02 when stor hit 17745 and upBank released the second upgrader (nUp=2 why=ok work=28 surplus=1125 at tip). Brief nUp=3 at 84262940-84263020 18:09-18:15 is a three-creep handoff, then nUp=2. Live at tip why=ok; later why=remote_pause after the 18:30 W45N7 core, still nUp=2.

W47 exact2h 21.06/30.08=70.0% (prev 19.84=66.0%) is no longer <70% (21.06/30.08=0.7001). 1h 22.44=74.6%. Short last20 15.00=49.9%, last30 16.67=55.4%, last70-100 17.50=58.2% span=40, last140 19.29=64.1%, last200 19.68=65.4% are soft because of a keep=2 handoff plus the 18:17-18:24 freeze (w8upgrader84261687 ttl 54 / 84261886 ttl 253 / replacement 84263126 walking in at tip; w8up 3→2 by 84263230). last300 21.71=72.2% still above 70%. Formal (a) does not hold. keep=2 designed, do not revert. threatSoft=0 softCap2=0 bankWhy=ready after leftover w8guard84260874 / w8defender84260874 aged out ~84262520 17:38; sealPark still on, softLeft 307 at tip later 789; stor min 22916@17:46 max 25719@17:29 tip 24661 later 25211.

FORMAL ALERT (b) stays RESET: home stor analysis tip 16125 ABOVE consec-under=0 (prev tip 15250 ABOVE consec-under=0). since-last min 15401@84262620 17:45 max 17745@84262850 18:02 under15k 0/56=0.0%. Path stayed above 15k through the tip. Later, after designed defender84263223 spawn_start 84263223 18:30, stor 15115@84263230, 14515@84263250, 14615@84263260 18:33 still UNDER; this later dip is after the analysis tip so (b) is not formal this run. 20k/300t not hit (3h max 17745, best>=20k span=0).

No formal (c)/(d)/(e)/(f).

Late-hour (after TIP, reported): W45N7 Invader core alert_new 84263222 18:30:11 why=core invOnly, designed defender84263223 (25A/25M ~3250e, same core budget as last W45N7/W47N7 cores) spawn_start 84263223 waited=1, still spawning at 84263254 left 119 (50 parts × 3 = 150t). upgFeed why=remote_pause, nUp still 2. Do not steal wartime command.

## B) Energy
Home: exact2h 17.00/26=65.4%, 1h 20.74=79.8%, short 24-26 e/t after nUp=2. model 2h measured upgrade 17.14 storage_delta +1.62; 1h upgrade 20.92 storage_delta +0.73. Biggest gap this hour was nUp=1 until 18:02; after release the short window is at/above ideal. Live tip why=ok nUp=2 tUp=2 work=28 surplus=1125 floor=15000 allowExtra=20000; later why=remote_pause surplus thin after the defender spawn. RCL7 59.65% tip p=6522352, later p=6524104 (59.66%) stor 14615.

W47: exact2h 21.06/30.08=70.0%, 1h 22.44=74.6%, model_w8 ideal 30.03, 2h actual 21.01, 1h 22.34, upgrader_work 30/31 (keep=2 + handoff). stor min 22916@17:46 max 25719@17:29 tip 24661 later 25211. sealPark on, sealMinE=25000, siteRem=0, feedOk=1, hubLink=1, leanBank=0, upLatched=0, softLeft 307 later 789, upArm=40000, ttdW 150000. model_w8 src_A 0.29 is the same known measurement artifact; 2h R1 6.78 R2 4.53 vs 9.5; 1h R1 8.03 R2 4.61 (cov 0.944 after two freezes). Biggest real gap remains upgrade vs ideal under keep=2; threatSoft/softCap2 cleared this hour.

Ledger 2507t (~3.09h): home up 13.87 (undercount) spawn net 15.54 build 1.99; W47 up 20.58 spawn net 16.52.

## A) Motion
audit --patrol EXIT2 REGRESSION [deploy] is window metric shift vs 4ff78b4 (same numbers as last hour: hauler.cpu_t_sum 0.131→0.278, hauler.rp100 0.1→1.1, miner.trip_med 56→81, queen.work_per_cpu 142.68→66.85, reserve.rp100 2.4→6.0, reserver.idle 0.04→0.12, reserver.rp100 0.1→0.3, rminer.excess 1.38→2.5, rminer.trip_med 18→35, wbuilder.cpu_t_sum 1.249→2.046, wrminer.idle 0.19→0.28; not shipped).
motion --patrol EXIT1 waiting_pickup/target_full/no_task/waiting_feed/queue_blocked/parked_threat.
w8filler ABA 190/144 known hub weave (vs last 106/100, same class).
w8hauler circ/aba elevated is corridor swap-weave not 2-tile stuck.
miner84262467 queue_blocked 54 is a designed source-B replacement at the near source, not a new stuck bug.
w8rminer84261468 / 84262820 swamp+fail is in-place mining on W47N7 swamp containers, not a new stuck/oscillation.
parked_threat on leftover w8guard84260874 / w8defender84260874 is designed and ended mid-hour (~17:38).
No new stuck/oscillation after last deploy, not shipped.

## C) Strategy / remotes / CPU / buildings
Remotes W45N8/W45N7/W47N7 vis res 2145/2246/2703 (q at 84263172) cores0 host0 SAFE at the analysis tip (W45N7/W47N7 why=killed leftover). After TIP: W45N7 Invader core inc=84263222 alert_new 18:30:11 why=core invOnly, stats.st=THREAT, designed defender84263223 spawn as above; W45N8 SAFE; W47N7 SAFE why=killed leftover.
W45N7 reserver84262040 on 7,41 aged out ~84262651 17:48; replacement reserver84262494 spawned 84262495 and walked W45N8→W45N7 (last trusted live-ish pos 6,39 @84262664); official rows after the freeze wrongly pin it at the home spawn tile (history artifact). W45N8 reserver84262263 on 7,37 through official tip 84263100, aged around the 18:17-18:24 freeze. room_stats reserver=0 from 84263150 through later 84263260 (~110t); no live reserver at 84263234 and Spawn3 idle while Spawn1 is busy with the defender. Reservations still ~2100-2700, designed wait, report not formal (c).
reserve7 zero_run 300t 84262390-84262690 then reserve784262794 spawned ~84262794, arrived W47N7 39,27, still on controller at later ttl~171, r7.on endTime=84265887, res ~2700 healthy, designed wait earlier in the hour, report not formal (c).
home critical roles miner/queen/rminer/w8filler present all hour.
sites=0 both rooms. Home labs + ramparts still up (~300-301k).
CPU 1h min 15.23 max 23.54@84262620 17:45 avg 17.81 p95 21.5 bkt 10000, not (e). 2h max 24.3 is leftover from 16:35 last hour.
sma 6/6 ttd 150000/150000. Memory.cmd.on=1 at=84224348 stale c={} s={} v=1 confirmed live, not touched.
labs OFF why=ready propose=1 actOk=1 actGaps=""; min line why=ready flipGaps=already; do not enable do not re-ask.
minerals hsO=17324 termO=126976 termK=172792 W47 termE=1096 termK=244 wsK=64.

## D) Infra
See infra.txt. Peacetime single-slot 5:5:1:1, commander not live. Two box freezes this hour, both self-healed; official history filled the freeze gaps except the persistent W46N8@84262500 official 404 (confirm+retry2 still 404). Unpublished latest ~90t at TIP expected; W47N8 live filled part of that chunk. Same known post-thaw subscribe-limit after the 18:01 wake (x1 only, recovered); 18:10 and 18:24 thaws did not repeat it.

No src change, no deploy this patrol.
