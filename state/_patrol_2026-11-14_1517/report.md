# Patrol 2026-11-14 15:24 Asia/Hong_Kong (1h peacetime)

LIVE 4ff78b4 (held, deploy@84239549 2026-11-13 13:26; no new deploy this patrol). TIP 84260650 15:19:46 HKT, later 84260710 15:24:10.

## Alerts
FORMAL ALERT (a) holds on W47 only this run: W47 exact2h 18.25/30.08=60.7% (prev 19.34=64.3%) is 48th consecutive <70% AND short is soft again (last100 17.40=57.8%, last140 15.29=50.8%, last200 16.20=53.9%, last300 16.63=55.3%; last20-70 all 20.00=66.5% is keep=2 designed 20 e/t; 1h 19.54=65.0%). Last run W47 short had recovered so W47 (a) did not formally hold; this run it does. keep=2 designed, do not revert. Contributing this hour: brief W47N8 hostile 1 @84260400 15:01, designed w8guard84260391 (25A/14M/2T) spawn~84260391, parked 29,5 after spawn; live w8day bankWhy=threatSoft threatSoft=1 softCap2=1 sealPark=1 keep=2 phase=ready. Remotes stayed SAFE.

Home exact2h 16.13/26=62.0% (prev 14.13=54.3%) is still <70% (would be 46th consecutive if formal) BUT short is no longer soft (last20-200 all 28.00=107.7%, last300 24.92=95.8%, 1h 18.26=70.2%). nUp=1→2 this hour after storage stayed above the 15k floor (why=ok, upBank released, tUp=2 work=28 is the designed peacetime target when sites=0 and not floor_bank). So home (a) does not formally hold this run (same rule as W47 on the 14:27 patrol).

FORMAL ALERT (b) stays RESET: home stor analysis tip 16677 ABOVE consec-under=0 (prev tip 15179 ABOVE consec-under=0). since-last min 14075@84260090 14:38 max 17457@84260320 14:55 under15k 8/79=10.1%. Brief under 14885@14:33 and 14885@14:35, min 14075@14:38, recross 15375@84260140 14:42, later 16877@84260710 / object 16927 still ABOVE. 20k/300t not hit (3h max 17457, best>=20k span=0).

No formal (c)/(d)/(e)/(f).

## B) Energy
Home: exact2h 16.13/26=62.0%, 1h 18.26=70.2%, short 28 e/t after nUp=2. model 2h measured upgrade 16.16 storage_delta +0.73; 1h upgrade 18.32 storage_delta +2.00. Biggest remaining gap is the first half of the 2h window still sitting in the floor_bank nUp=1 era; live why=ok nUp=2 surplus=1527 floor=15000 allowExtra=20000 ctl=362 hungry=0. RCL7 59.27% tip p=6480654, later p=6482334 (59.28%) stor 16877.

W47: exact2h 18.25/30.08=60.7%, 1h 19.54=65.0%, model_w8 ideal 30.03 (ratios vs established 30.08), 2h actual 18.37, 1h 19.53, upgrader_work 20/31 (keep=2). stor min 23334@15:06 max 25890@tip later 28419. sealPark on, sealMinE=25000, siteRem=0, feedOk=1, hubLink=1, leanBank=0, upLatched=0, softLeft=0, upArm=40000, ttdW 150000. model_w8 src_A 0.00–0.32 is the same known measurement artifact (miner sat at 26,11 loaded all hour, replacement w8miner84260394 arrived 84260492); src_B 7.4–9.1, R1/R2 ~5.0–5.8 vs 9.5. Biggest real gap remains upgrade vs ideal under keep=2 + this hour's threatSoft/softCap2 and 3-upgrader handoffs.

Ledger 3188t (~3.92h): home up 13.03 (undercount) spawn net 12.96 build 4.84; W47 up 19.21 spawn net 15.30 (includes last-hour rdef recycle and this-hour w8guard 0.85 e/t).

## A) Motion
audit --patrol EXIT2 REGRESSION [deploy] is window metric shift vs 4ff78b4 (same numbers as last hour: hauler.cpu_t_sum 0.131→0.278, miner.trip_med 56→81, queen.work_per_cpu 142.68→66.85, reserve.rp100 2.4→6.0, reserver.idle 0.04→0.12, rminer.excess 1.38→2.5, rminer.trip_med 18→35, wbuilder.cpu_t_sum 1.249→2.046, wrminer.idle 0.19→0.28; not shipped).
motion --patrol EXIT1 waiting_pickup/target_full/no_task/waiting_feed/queue_blocked/parked_threat.
w8filler ABA 144/148 known hub weave (vs last 149/95, same class).
w8hauler circ/aba elevated is corridor swap-weave not 2-tile stuck.
home hauler84259180 waiting_pickup all hour then aged out; replacement hauler84260649 already live at 32,28. Not formal (c) (hauler not in the critical-role set; gap brief).
No new stuck/oscillation after last deploy, not shipped.

## C) Strategy / remotes / CPU / buildings
Remotes W45N8/W45N7/W47N7 vis res 2409/2036/2509 (q2) cores0 host0 SAFE (W45N7/W47N7 why=killed leftover).
W45N8 reserver84260113 on 7,37 ttl~20 at 15:24, res 2409 designed wait, report not formal (c).
W45N7 reserver84260388 on 6,39 ttl~295, report not formal (c).
reserve7 zero_run since 84260320 (~330t at tip); r7.on endTime=84263211, W47N7 res 2509 still healthy, designed wait, report not formal (c).
home critical roles present (miner/queen/rminer/reserver/w8filler); reserver zero_run 40t 14:36-14:39 designed.
sites=0 both rooms. Home lab 34,20 + rampart still up (rampart ~300k).
CPU 1h min 13.77 max 47.91@84260650 15:19 (single sample; 84260640=17.54, 84260660=19.11, later 17.34) avg 18.64 p95 21.57 bkt 10000 min 9993, not (e).
sma 6/6 ttd 150000/150000. Memory.cmd.on=1 at=84224348 stale, not touched.
labs OFF actOk=1 why=ready propose=1 do not enable do not re-ask; min line why=ready flipGaps=already.
minerals hsO=17324 termO=126976 termK=168172 W47 termE=1253 termK=76 wsK=64.

## D) Infra
See infra.txt. Peacetime single-slot 5:5:1:1, commander not live. Short self-healed freeze only. history_backfill missing_chunks=1 in-window official 404 W46N8@84260300 (confirm+retry2 still 404). Unpublished latest chunk expected.

No src change, no deploy this patrol.
