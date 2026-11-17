# 1h peacetime patrol 2026-11-17 20:30 Asia/Hong_Kong

TIP 84322340 (20:26:39 HKT), later 84322384 (~20:30). LIVE c6d43491 held (deploy@84321282 19:02:43). No new src/deploy this patrol.

## Alerts
- FORMAL (a) HOLDS, eighth consecutive dual-condition on W47. exact2h 20.58/30.08=68.4% (prev 20.69=68.8%). Short last20-200 all designed keep=2 20.00=66.5%; last300-500 18.82=62.6% (handoff dip); last800 20.51=68.2%; 1h interp 20.35=67.7%; model 1h 20.36 / 2h 20.58. Root remains keep=2 (~20 e/t seated, already 66.5%). Do not change keep/softCap; no standing third.
- (b) does NOT fire: first consecutive under. Tip 14230 UNDER 15k (later 14130-14552 still under at 20:30). Prev tip 18053 ABOVE, consec-under=1. since_last min 13930@84322310 20:24 max 18553@84321620 19:29 under15k=12/39=30.8%. Home short is soft because floor_bank (last20-30 ~17-19 e/t, last140-300 ~14.5-15.7) but exact2h 21.93/26=84.4% still ABOVE, so home (a) does not fire. Do not change the 15k floor.
- (c) none: critical roles present (miner 2, queen 2, rminer 2, reserver 2, w8filler 2, w8miner 2, w8rminer 2, w8upgrader 2). reserve7 had a 160t count gap 84321570-84321730 before reserve784321920; reservation stayed ~2705, not formal.
- (d) none: first post-deploy replacement walk verified the c6d43491 fix (see below). creep_audit --patrol exit 2 is REGRESSION [deploy] vs c6d43491 baseline in the same known metric family (hauler/rhauler/whauler work_per_cpu, rminer/wminer idle, queen cpu), not a new stuck/oscillation. creep_motion 1h/2h exit 1 known waiting_pickup / target_full / waiting_feed / queue_blocked / no_task.
- (e) none: CPU 1h mean 16.68 max 20.88; 2h mean 18.00 max 30.12@84321320 19:05 (same known wake spike); bucket min 9916 later 10000.
- (f) none: infra up; 40m official backfill succeeded with known leftover official 404s.

## First post-deploy W47 replacement (c6d43491 verification)
w8upgrader84322007 first 84322009 20:00:38 at 34,30 state=spawning x37 (hatch through 84322045). Walk after hatch: 34,29 -> 33,29 (north hook 5t) -> 32,30 -> 33,31 -> 32,32 south bypass (5t from 84322058) -> 33,33/33,34 -> 32,35 then west along y=35 to first_seat 14,27@84322136 20:10:09. Walk after hatch=90t (127t including spawn). filler_post_34,32=0, pocket_bounce=0. Partner 21049 stayed 14,26. 20564 last_seat 12,25@84322072 20:05:35, seat gap=64t. Cleaner than the old 130-220t pocket spins; brief 33,29 hook then self-corrected south. No code change this hour.

## 40k / 20k
40k/500t still unlocked. New touch this hour 84322110-84322200 20:08-20:15 dt=90t first=40063 max=41413@84322120 20:08, then tip 38563 later 38063. Known best span still 480t (84313150-84313630). upLatched=0 keep=2 bankWhy=ready softCap2=0 threatSoft=0 sealPark=0.
Home 20k/300t still unlocked: 6h/3h max 19253@84321540 19:23, best>=20k span=0.

## Remotes / labs / infra
All vis SAFE reserved cores0 host0 (W45N8 res~2185, W45N7 res~1985, W47N7 res~2705). Labs mode=KO why=active Memory.ops.labs held, ready=0 actGaps=homeStor (floor). Home O 129200 K 190055 KO 8836 term K/O 3000/3000; W47 K 64 term E 1480. sma=6/smaW=6 ttd=150000 both never activated. sites=0. Memory.cmd.on=1 at=84224348 stale c={} s={} not touched. Listener single-slot 5:5:1:1, 20:30 still W46N8, commander not holding.

Official 40m backfill 84321601-84322300 tick_s=4.711 inserted=8687 already_in_db=13453 coverage 3395/3500; missing_chunks still 404 after retry: W45N7@84321600 (98t hole 84321603-84321700), W47N8@84322100 (7t leftover 84322194-84322200 after live fill). Unpublished latest ~40t at tip expected, later filled by listener. Leftover outside window W47N8@84321300 (61t) still 404. Box pauses 19:38:40-20:05:16 (~1590s, room_stats 84321730-84322080 350t) and 20:17:55-20:21:35 (~220s, 84322220-84322280 60t) known platform limit; official history filled published trajectories except the 404s.

## Model
HOME model 1h upgrade 23.29 stor_delta -5.57 spawn_util 0.67 (exact 1h 23.39=89.9%, exact2h 21.93=84.4%). W47 model 1h upgrade 20.36 stor_delta +4.13; 2h 20.58 stor_delta +7.96 (banked while keep=2). W47 src_A model 0.0 / 2h 0.33 e/t is link-accounting, not a harvest hole (w8miner84322192 seated 26,11).
RCL7 home 70.29% p=7686545 later 7687213; W47 40.88% p=4470611 later 4471491.
