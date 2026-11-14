# Patrol 2026-11-14 17:25 Asia/Hong_Kong (1h peacetime)

LIVE 4ff78b4 (held, deploy@84239549 2026-11-13 13:26; no new deploy this patrol). TIP 84262350 17:25:29 HKT, later 84262388 17:28:29 / room_stats 84262390.

## Alerts
FORMAL ALERT (a) holds on home only this run.

Home exact2h 13.75/26=52.9% (prev 16.85=64.8%) is 48th consecutive <70% AND short is still soft (last20-30 all 14.00=53.8%, last70-140 only span=50 after the 17:14-17:21 freeze so not used alone; last200 15.35=59.0%, last300 14.90=57.3%, 1h 13.04=50.1%). Last run home (a) already formally held; this run it still does. Cause this hour: nUp stayed 1 why=floor_bank after last hour's under-15k; stor recrossed 15k at 16:40 but surplus stayed thin (live 430 then 600), so upBank did not release the second upgrader (tUp=1 work=14). Brief nUp=2 at 84262300-84262320 17:21-17:23 is a two-creep handoff after the second freeze (stor still 14080-14680), then nUp=1 from 84262320. Live why=floor_bank nUp=1 work=14.

W47 exact2h 19.84/30.08=66.0% (prev 19.58=65.1%) is still <70% BUT short no longer soft (last20 24.20=80.5%, last30 24.80=82.4%, last70-140 25.28=84.0% span=50 after the same freeze; last200 24.56=81.6%, last300 23.32=77.5%; 1h 19.69=65.5% dragged by the first half-hour at designed 20 e/t). So W47 (a) does not formally hold this run (same rule as 14:27 / 12:25). keep=2 designed, do not revert. Contributing: 3-upgrader handoff 84261690-84261780 16:36-16:43 (rates 20-26), then keep=2; post-17:09 samples also ran ~22-26 e/t with two counted w8upgraders. threatSoft=1 softCap2=1 sealPark=1 bankWhy=threatSoft still on from the 15:36 hostiles (no new hostile this hour); softLeft 526 at 17:23 later 771; remaining w8guard84260874 / w8defender84260874 parked 29,5 / 28,5 ttl~107-134 at 17:28. Earlier w8guard84260391 aged out this hour.

FORMAL ALERT (b) stays RESET: home stor analysis tip 15250 ABOVE consec-under=0 (prev tip 13618 UNDER consec-under=1). since-last min 11918@84261660 16:34 max 17172@84262190 17:13 under15k 19/50=38.0%. Path: still under at last later 12018, min 11918@16:34, recross 15218@84261750 16:40, over16k 16888@84262020 17:00, max 17172@17:13, freeze dip 14080@84262300 17:21, recross 15350@84262330 17:24, tip 15250, later 15600@84262388 17:28 still ABOVE. 20k/300t not hit (3h max 17457, best>=20k span=0).

No formal (c)/(d)/(e)/(f).

## B) Energy
Home: exact2h 13.75/26=52.9%, 1h 13.04=50.1%, short 14 e/t after nUp=1 floor_bank. model 2h measured upgrade 13.90 storage_delta -1.36; 1h upgrade 13.04 storage_delta +2.10. Biggest gap this hour is still nUp=1 after the floor was lost last hour and surplus never got large enough to release the second upgrader, plus two box freezes. Live why=floor_bank nUp=1 tUp=1 work=14 surplus=430→600 floor=15000 allowExtra=20000. RCL7 59.49% tip p=6505138, later p=6505670 (59.49%) stor 15600.

W47: exact2h 19.84/30.08=66.0%, 1h 19.69=65.5%, model_w8 ideal 30.03 (ratios vs established 30.08), 2h actual 19.75, 1h 19.5, upgrader_work 20/31 (keep=2). stor min 24474@17:21 max 31425@16:32 tip 24974 later 24519 (24229-25429). sealPark on, sealMinE=25000, siteRem=0, feedOk=1, hubLink=1, leanBank=0, upLatched=0, softLeft 526 later 771, upArm=40000, ttdW 150000. model_w8 src_A 0.30-0.65 is the same known measurement artifact; 2h R1 6.47 R2 6.29 vs 9.5; 1h R1 3.3 R2 3.05 is partly coverage (1h cov 0.879 after two freezes + the W47N8 official hole), not treated as a new remote-mining bug. Biggest real gap remains upgrade vs ideal under keep=2 + threatSoft/softCap2; storage fell ~7k this hour as upgrade and spawn continued while stor sat near the 25k seal line.

Ledger 2442t (~3.01h): home up 13.38 (undercount) spawn net 15.44 build 1.65; W47 up 19.65 spawn net 16.56.

## A) Motion
audit --patrol EXIT2 REGRESSION [deploy] is window metric shift vs 4ff78b4 (same numbers as last hour: hauler.cpu_t_sum 0.131→0.278, hauler.rp100 0.1→1.1, miner.trip_med 56→81, queen.work_per_cpu 142.68→66.85, reserve.rp100 2.4→6.0, reserver.idle 0.04→0.12, reserver.rp100 0.1→0.3, rminer.excess 1.38→2.5, rminer.trip_med 18→35, wbuilder.cpu_t_sum 1.249→2.046, wrminer.idle 0.19→0.28; not shipped).
motion --patrol EXIT1 waiting_pickup/target_full/no_task/waiting_feed/queue_blocked/parked_threat.
w8filler ABA 106/100 known hub weave (vs last 127/83, same class).
w8hauler circ/aba elevated is corridor swap-weave not 2-tile stuck.
miner84261954 excess 13.67 + queue_blocked 72 is a designed source-B replacement: spawned 84261956, walked to (38,32), queued then mined in place; predecessor miner84261048 stayed on source A (31,12). Not formal (c) (hauler/miner present) and not a new stuck bug.
w8rminer84261468 fail 99 / swamp 128 is in-place mining on W47N7 swamp container (18,17); same class as w8rminer84260771 at (31,34). Not a new stuck/oscillation.
home hauler84260649 / hauler84262118 waiting_pickup; hauler not in the critical-role set.
parked_threat on remaining w8guard84260874 / w8defender84260874 is designed after the 15:36 hostiles; w8guard84260391 aged out this hour.
No new stuck/oscillation after last deploy, not shipped.

## C) Strategy / remotes / CPU / buildings
Remotes W45N8/W45N7/W47N7 vis res 1905/1462/2903 (q at 84262332-84262340) cores0 host0 SAFE (W45N7/W47N7 why=killed leftover). No new incident this hour after last patrol's W45N7 core clear.
W45N8 reserver84262263 on 7,37 ttl~485-536, report not formal (c).
W45N7 reserver84262040 arrived 7,41 ttl~262-313, res recovered 897→1462, report not formal (c).
reserve7 zero_run 150t 84261590-84261740 then reserve784261750 spawned 84261752, arrived W47N7 39,27 @84261839, aged out ~84262361; at later 84262389 no replacement yet (~28t), r7.on endTime=84265293, res ~2900 still healthy, designed wait, report not formal (c).
home critical roles present (miner/queen/rminer/reserver/w8filler) all hour; reserver dipped 2→1 briefly at 84261770 during the W45N8 replacement, not a >100t gap.
sites=0 both rooms. Home lab 34,20 + rampart still up (rampart ~303-304k).
CPU 1h min 14.59 max 24.3@84261680 16:35 (neighbors 23.38@16:34 / 21.13@17:09) avg 17.50 p95 20.49 bkt 10000 min 9996, not (e). 2h max 26.27 is leftover from 15:32 last hour.
sma 6/6 ttd 150000/150000. Memory.cmd.on=1 at=84224348 stale c={} s={} v=1 confirmed live, not touched.
labs OFF why=ready propose=1 actOk=1 actGaps="" (homeStor back above the floor; last run actOk=0); min line why=ready flipGaps=already; do not enable do not re-ask.
minerals hsO=17324 termO=126976 termK=171536 W47 termE=1139 termK=0 wsK=64.

## D) Infra
See infra.txt. Peacetime single-slot 5:5:1:1, commander not live. Two box freezes this hour, both self-healed; official history filled the freeze gaps except the persistent W47N8@84261900 official 404 (confirm+retry2 still 404). W45N7 18t with no creep_ticks (84261642-84261659) is an empty-room span (defender walked out, rhauler entered later), not an official hole. Unpublished latest ~100-tick chunk expected. Same known post-thaw subscribe-limit after the 16:24 wake, recovered; 16:59 and 17:21 thaws did not repeat it.

No src change, no deploy this patrol.
