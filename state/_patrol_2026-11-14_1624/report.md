# Patrol 2026-11-14 16:24 Asia/Hong_Kong (1h peacetime)

LIVE 4ff78b4 (held, deploy@84239549 2026-11-13 13:26; no new deploy this patrol). TIP 84261590 16:29:08 HKT, later 84261670 16:35:02 / object 84261674.

## Alerts
FORMAL ALERT (a) holds on home and W47 this run.

Home exact2h 16.85/26=64.8% (prev 16.13=62.0%) is 47th consecutive <70% AND short is soft again (last20 8.20=31.5%, last30 10.13=39.0%, last300 9.65=37.1%; last70-200 only span=60 after the 16:11-16:24 freeze so not used alone; 1h 13.26=51.0%). Last run short had recovered so home (a) did not formally hold (it would have been 46th); this run it does. Cause this hour: stor crossed under 15k at 15:36, nUp 2→1 at 84260890 15:37 why=floor_bank (upBank on, surplus negative); brief nUp=2 at 84261530-84261540 16:24-16:25 is a two-creep handoff after the second freeze (stor still 13018-13118), then nUp=1 from 84261550. Live why=floor_bank nUp=1 tUp=1 work=14. ctl=0 at tip also dragged last20 below the nUp=1 14 e/t cap.

W47 exact2h 19.58/30.08=65.1% (prev 18.25=60.7%) is 49th consecutive <70% AND short is still soft (last20-300 all 20.00=66.5%; last70-200 span=60 after the same freeze, but last20, last30, last300 and 1h 20.00=66.5% all agree). last20 at designed keep=2 20.00=66.5% is not by itself "short recovered"; no ~30-300 window is >=70%. keep=2 designed, do not revert. Contributing: W47N8 host=2 @84260880 15:36, designed w8guard84260874 (25A/14M/2T) + w8defender84260874 (25RA/25M) spawn~84260874-84260876, parked 28,4 / 28,5 with earlier w8guard84260391 still at 29,5; live w8day bankWhy=threatSoft threatSoft=1 softCap2=1 sealPark=1 keep=2 phase=ready.

FORMAL ALERT (b) is FIRST under, not yet formal: home stor analysis tip 13618 UNDER consec-under=1 (prev tip 16677 ABOVE consec-under=0 RESET). since-last min 12917@84260900 15:38 max 17177@84260740 15:26 under15k 27/54=50.0%. Path: under16k 15527@84260830 15:33, under15k 14317@84260880 15:36, min 12917@15:38, freeze 15:39-15:56 then recross 15068@84261160 15:57, under 14758@84261190 15:59, over 15058@84261220 16:01, under 14358@84261230 16:02 and no recross after that; tip 13618, later 12018@84261670 16:35 / object 12068@84261674 still UNDER. 20k/300t not hit (3h max 17457, best>=20k span=0).

No formal (c)/(d)/(e)/(f).

## B) Energy
Home: exact2h 16.85/26=64.8%, 1h 13.26=51.0%, short ~8-10 e/t after nUp=1 floor_bank. model 2h measured upgrade 16.88 storage_delta -1.32; 1h upgrade 12.92 storage_delta -4.09. Biggest gap this hour is the return to nUp=1 after stor lost the 15k floor, plus two box freezes. Live why=floor_bank nUp=1 tUp=1 work=14 surplus=-2982 floor=15000 allowExtra=20000 ctl=0 hungry=0. RCL7 59.40% tip p=6494986, later p=6495762 (59.40%) stor 12018.

W47: exact2h 19.58/30.08=65.1%, 1h 20.00=66.5%, model_w8 ideal 30.03 (ratios vs established 30.08), 2h actual 19.5, 1h 20.0, upgrader_work 20/31 (keep=2). stor min 23226@15:39 max 30249@16:25 tip 30198 later 31425. sealPark on, sealMinE=25000, siteRem=0, feedOk=1, hubLink=1, leanBank=0, upLatched=0, softLeft=0, upArm=40000, ttdW 150000. model_w8 src_A 0.00 is the same known measurement artifact; src_B 6.81-6.82, R1 6.19-7.04, R2 7.64-7.65 vs 9.5. Biggest real gap remains upgrade vs ideal under keep=2 + threatSoft/softCap2.

Ledger 2585t (~3.18h): home up 13.34 (undercount) spawn net 16.42 build 1.82; W47 up 19.18 spawn net 15.96 (includes this-hour w8guard 2.10 e/t and the W45N7 defender spawn).

## A) Motion
audit --patrol EXIT2 REGRESSION [deploy] is window metric shift vs 4ff78b4 (same numbers as last hour: hauler.cpu_t_sum 0.131→0.278, hauler.rp100 0.1→1.1, miner.trip_med 56→81, queen.work_per_cpu 142.68→66.85, reserve.rp100 2.4→6.0, reserver.idle 0.04→0.12, reserver.rp100 0.1→0.3, rminer.excess 1.38→2.5, rminer.trip_med 18→35, wbuilder.cpu_t_sum 1.249→2.046, wrminer.idle 0.19→0.28; not shipped).
motion --patrol EXIT1 waiting_pickup/target_full/no_task/waiting_feed/queue_blocked/parked_threat.
w8filler ABA 127/83 known hub weave (vs last 144/148, same class).
w8hauler circ/aba elevated is corridor swap-weave not 2-tile stuck.
home hauler84260649 waiting_pickup all hour; not formal (c) (hauler not in the critical-role set).
parked_threat on w8guard84260391 / w8guard84260874 / w8defender84260874 is designed after the 15:36 hostiles.
No new stuck/oscillation after last deploy, not shipped.

## C) Strategy / remotes / CPU / buildings
Remotes W45N8/W45N7/W47N7 vis res 2336/897/2614 (q2 at 84261635) cores0 host0 SAFE (W45N7/W47N7 why=killed leftover).
W45N7 Invader core inc=84261198 alert_new 84261198 16:00 why=core invOnly, designed defender84261199 (25A/25M full budget) spawn 84261199 waited=1, walked W46N8→W45N8@84261376 16:13 (during the second freeze; trail from official history), entered W45N7 84261422 16:16, cleared 84261598 16:29 ev=cleared DEFEND→SAFE why=killed dur=400. Live leftover defender still in W45N7 15,18 ttl~1225 after clear, report not formal (c).
W45N8 reserver84261157 on 7,37 ttl~131-141, res 2336 designed, report not formal (c).
W45N7 reserver84260388 aged out 84260999 ~15:45 on 6,39; replacement reserver84261599 walking through W46N8 (38,26 then 47,17) toward W45N7, res 897 still Misaki, designed wait, report not formal (c).
reserve7 zero_run since 84261330 (~260t at tip); r7.on endTime=84264249, W47N7 res 2614 still healthy, designed wait, report not formal (c).
home critical roles present (miner/queen/rminer/reserver/w8filler); reserver zero_run 0t at 84261150 is a single thaw sample, not a gap.
sites=0 both rooms. Home lab 34,20 + rampart still up (rampart ~301k).
CPU 1h min 14.62 max 26.27@84260820 15:32 (neighbors 17.16/19.31) avg 17.59 p95 20.04 bkt 10000 min 9998, not (e). 2h max 47.91 is leftover from last tip.
sma 6/6 ttd 150000/150000. Memory.cmd.on=1 at=84224348 stale c={} s={} v=1 confirmed live, not touched.
labs OFF why=ready propose=1 actOk=0 actGaps=homeStor (homeStor now under the floor; last run actOk=1); min line why=ready flipGaps=homeStor,already; do not enable do not re-ask.
minerals hsO=17324 termO=126976 termK=169892 W47 termE=1195 termK=0 wsK=64.

## D) Infra
See infra.txt. Peacetime single-slot 5:5:1:1, commander not live. Two box freezes this hour, both self-healed; official history filled the freeze gaps. history_backfill missing_chunks=0 in-window; leftover official 404s unchanged (confirm+retry2 still 404). W45N7 180t with no creep_ticks (84261242-84261421) is an empty-room span (rminer walked out, defender entered later), not an official hole (other four rooms 180/180). Unpublished latest ~70-100 tick chunk expected.

No src change, no deploy this patrol.
