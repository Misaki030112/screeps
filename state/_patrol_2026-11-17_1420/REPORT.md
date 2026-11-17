# 1h peacetime patrol 2026-11-17 ~14:30 Asia/Hong_Kong

Analysis TIP 84317740 (14:24:52), later room_stats 84317810 (14:30:22). LIVE 85c19c2e (deployed 2026-11-16 19:19 @84303299, PR 55). No code change, no new deploy.

## Alerts
- **FORMAL W47 upgrade alert** — second consecutive dual-condition (exact2h under 70% AND short-window soft). exact2h 17.81/30.08=59.2% (prev 16.61=55.2%); short last200–800 19.00–19.73 e/t = 63.2–65.6%; 1h INTERP 19.64=65.3%; model_w8 1h 20.0 / 2h 17.96 vs ideal 30.03. Root: keep=2 caps seated upgrade near 20 e/t (~66.5% of 30.08) plus known hub-pocket handoff stalls. Replacement w8upgrader84317671 was at 32,35 walking to 14,27 at live 84317779 — same pocket path. Do not change keep/softCap, do not add a standing third, do not ship a CMV bandage this run.
- **W47N7 Invader Core** appeared 14:00:22 inc=84317428 (alert_new THREAT, core). Full-budget rdef84317429 (5000, 25A/25M) spawn_start 84317429, hatched 84317579 14:12:12, last official 84317600 14:13:51 at W47N8 17,33 still walking south. Mid-fight ticks after 84317600 are unpublished + 14:12–14:19 box freeze. Live 84317771–84317777: cores=[], host=[], Memory.stats SAFE why=killed, reservation ~2716–2722, miners seated, rdef absent (recycled). Memory.cmd untouched; no Safe Mode.

Home upgrade is not in alert: exact2h 23.69/26=91.1% (prev 20.62=79.3%) ABOVE; short last200–800 ~25–27 e/t. Storage not in alert: tip 16128 later 15628, since_last under15k=0/48, min=15628.

## Energy / storage
- HOME: nUp=2 work=28 why=ok bound=energy; model 1h upgrade 26.93 storage_delta -3.84 spawn_util 0.64; 2h upgrade 23.77 spawn_util 0.64. stor max 20244@13:37, 20k/300t still unlocked (best ≥20k span ~20–30 t). RCL7 69.36% (7584023) later p=7585983 stor15628@84317810.
- W47: stor min 30346@13:29 max 40490@14:20 later 41280@14:30. Crossed 40k at 84317690 14:20:57; current ≥40k span=120 t; 40k/500t still unlocked (longest still 470 t from 84313160–84313630 this morning; 6h max 43041@84313260). keep=2 bankWhy=ready upArm=40000 upLatched=0 feedOk=1 hubReady=1 sealPark=0. Biggest real gap is upgrade vs 30.03, surplus into storage.

## Remotes / roles
- W45N8 / W45N7 / W47N7 vis SAFE, no cores/hostiles; reservation ~1992 / 2331 / 2722.
- W45N8 rminer84316381 at 13,11 ttl~131 (replacements rminer84317748 walking, 84317762 spawning). W45N7 rminer84316459 at 21,15 ttl~209–212; reserver84317175 at 6,39 ttl~7, reservation healthy.
- W47N7 miners w8rminer84317021 at 18,17 ttl~771 and w8rminer84317407 at 31,34 ttl~1157; reserve784317554 at 39,25 ttl~386–388.
- Home miners/queens/upgraders/reservers present. sites=0. Labs KO active (stocks home O 131600–134600 K 192855–195855, term O 3000 K 3000) — never re-ask. W47N9 remains aborted. safeModeAvailable 6/6, ticksToDowngrade 150000 both rooms. Memory.cmd on=1 empty c/s at=84224348 old.

## Motion / audit
- creep_audit --patrol exit 2: REGRESSION [deploy] **identical** to 13:36 / 12:37 / 11:37 / 10:33 vs 85c19c2e — known, not a new formal deploy regression.
- Motion --patrol exit 1 both 1h and 2h: lost/h almost all known waiting_pickup / target_full / queue_blocked / no_task. Incoming W47 upgrader 17671 may repeat the hub-pocket stall; 16232/16732 were seated this hour after last hour's escapes.

## CPU / infra
- CPU since_last min 15.29 mean 18.10 max 23.60 p95 20.76, bucket min 10000 (later sample 9999); ~1h mean 18.13 max 23.60. No formal CPU alert.
- Infra healthy: postgres accepting; Grafana all 20 panels OK; dashboard :8787 200; listener single-slot 5:5:1:1 (restarted 14:19:54 after the 14:12 freeze, rot 14:20 W45N7 i=3 then 14:25–14:30 W46N8 i=0); no yield file; commander not holding slots (war_cmd/pulse stay stopped, aborted_by_misaki). DB writers fresh (room_stats lag ~22–36s, creep_ticks ~2–5s on the current slot, creep_cpu ~6–20s).
- History backfill official shard3 5 rooms ticks 84316901..84317600 (700, published 84316900..84317500 at game.time=84317692; first-pass missing_chunks=0, 35 of 35 official GETs 200), inserted=5302 already_in_db=20057; tick_s first 4.74225 printed 4.742, ts_realigned_first=0. tick_s_check: first over45=460 mean_off=+17.94; later_mean_robust 4.68503 over45=0; all_mean 4.69460 over45=0 over15=20; best sane=all_mean; corrective applied nfix=0 onto 4.69460 at game.time=84317744, after over45=0; in-use tick_s=4.69460. backfill_retry: all 21 leftover chunks still 404, inserted=0. This 40m window fully covered (5 rooms × 700 t, holes []). Leftovers from prior hours remain W45N8@84314900 (100t hole 84314901..84315000) and W47N7@84315100 (100t hole 84315101..84315200). W45N7@84314500, W47N8@84314000, W46N8@84313200 and older leftovers unchanged. Unpublished latest chunk 84317601+ expected (hour-window missing 84317601..TIP on non-listener rooms; W46N8 listener-filled after 14:25).
- Box pauses this window: 13:48:54–13:59:17 (~623s, room_stats 84317270–84317420 150 t); 14:12:36–14:19:51 (~435s, 84317570–84317680 110 t) — known platform limit, not a listener bug; official history filled published creep_ticks in the 40m window completely. Short last20–140 home/W47 windows start after the last gap (span only 60 t). No formal infra alert.

## Code / deploy
No code change, no new deploy. LIVE still 85c19c2e.

## Userlog
See `state/_patrol_2026-11-17_1420/userlog_zh.txt`.
