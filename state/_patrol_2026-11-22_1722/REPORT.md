# Patrol 2026-11-22 17:22 (delivered ~17:33 Asia/Hong_Kong)

Folder: state/_patrol_2026-11-22_1722
Previous delivered: ~16:32 _patrol_2026-11-22_1621 USER_LOG finished_at 16:33:58
LIVE still 2b5398f7 (deploy@2026-11-19 02:28). No src change, no deploy this hour.

## ALERTS
- FORMAL W47 upgrade RE-FIRES — second consecutive dual after the 15:32 clearance (16:32 was the first dual and did not re-fire): exact2h 19.83/30.08=65.9% (prev 20.80=69.1%) under AND meaningful short last800 19.24=64.0% still soft. last20-500 designed keep=2 20.00=66.5% must not clear. 1h INTERP 19.50=64.8%. model_w8 1h alloc upgrade 19.41 stor_delta -1.68 work=20 vs ideal 30.03; 2h alloc 19.83 stor_delta -0.01 work=20. Root remains designed keep=2 (20 e/t=66.5% of ideal). live two unboosted 10W w8upgraders seated 12,25 (84417038 ttl=219 at 84418357) / 14,27 (84417642 ttl=823), w8up on=0, not a standing third. Do not change keep/softCap, do not add a standing third, do not unseal the 40k lock.
- 40k/500t still unlocked: this-hour hist max 29839@84417640 16:38:35 min 25326@84418330+ later 25326; n>=40k=0; upArm=40000 upLatched=0 keep=2 upgCeil=2. sealPark=0 why=ok (last hour was 1) storE=25326 just above sealMinE=25000.
- NEW W45N7 Invader (not formal c): incident 17:28:25 tick=84418355 from SAFE->THREAT why=solo, invader_W45N7_892 body ttmmmmrwam hits=1000 ttl~1499 heal=false, no core. Home upgFeed rem W45N8:SAFE,W45N7:THREAT, nUp why=remote_pause. Home pile was short after upgrader84418335 (hea 5050/5600 at 84418390); defender started 84418409 after refill, full ~5600 budget (ea dropped to 102 then 617), still spawning at Spawn1 rem=132 at 84418421. Last seen 21,1 ttl=1443; later W45N7 vis=false (civilians left). Do not start commander, no Safe Mode. Reservations later W45N8 2292 / W45N7 last 1994 / W47N7 2467.

## Formal that stay cleared
- Home upgrade formal stays CLEARED: exact2h 18.06/26.00=69.5% is FIRST under after prev 21.10=81.2% ABOVE, does not fire. last800 17.69=68.0% and 1h INTERP 17.42=67.0% soft; last20-300 14.00=53.8% is 15k floor / later remote_pause nUp=1 and must not fire. model 1h measured upgrade 17.38 stor_delta +1.18 ticks 860; 2h 18.00 stor_delta +0.60 ticks 1720. Do not change the 15k floor and do not add a third.
- FORMAL storage does NOT fire: prev tip 15914 and this tip 17128 both ABOVE (consec-under=0); mid-hour min 14272@84418030 17:05:22 under15k=6/54=11.1%; recovered 15272@84418050 then again 14572@84418100 recovered 15272@84418130; later 16625-17228 all ABOVE (16925@84418420 / q_later 16875@84418415). 20k/300t still unlocked (3h max 17728, n>=20k span=0).
- no formal (c): critical roles present (miner 2, queen 2, rminer 2-3, reserver 2 then 1 at later 20t only, w8filler 2, w8miner 2, w8rminer 2, reserve7 1). reserver zero 270t 84417700-84417970 (around the 16:44 freeze); reserve7 zero 180t 84417950-84418130; reservations healthy — not formal missing-staff. Home builder 1 (sites=0).
- no formal (d): no new stuck/oscillation; audit --patrol exit 2 is known deploy-baseline drift vs 2b5398f7 2026-11-19 02:28, IDENTICAL REGRESSION [deploy] string to the 16:32 / 15:32 patrols, not alert (d); creep_motion --patrol 1h/2h exit 1 known waiting_pickup / target_full / no_task / queue_blocked / waiting_feed. w8rminer swamp source same known watch (w8rminer84417161 1h swamp 160; w8rminer84417245 1h fail 164).
- no formal (e): CPU 1h min 13.66 max 24.22@84417600 16:35:49 mean 17.57 p95 20.86, 2h min 13.66 max 34.94 (prior hour) mean 17.79, since_last n=54 mean 17.52 bucket min 9997 later 10000. Live 14.21@84418338 then 16.83@84418415 bucket 10000. Not (e).
- no formal (f): infra self-healed.

## Energy / harvest
- Home 1h income A/B/R 9.99/9.98/8.06; 2h 9.99/9.99/9.47. R 1h a bit softer vs 2h, still the main home harvest gap vs 10 gross.
- W47 src_A model harvest 1h 0.00 / 2h 0.08 is the same known measurement/attribution artifact — w8miners were seated. 2h R1/R2 7.05/6.80, 1h 3.38/3.52 softer this hour (freeze window + travel). src_B 1h 8.48 / 2h 9.25.

## Threat / remotes / labs
- Remotes: W45N8/W47N7 vis SAFE host=0 core=0; W45N7 THREAT as above. Threat window stamps still 84415078 (13:40, expired); threatSoft=0 softCap2=0 bankWhy=ready sealPark=0 why=ok / w8day.why=done phase=ready feedOk=1 hubLink=1 storE 25326. Do not start commander, no Safe Mode, do not change seal/keep numbers.
- Labs KO still on (Memory.ops.labs.W46N8=KO, never unset); labReady why=active actOk=1 actGaps=. Minerals home stor K 215472 O 80000 KO 57236 koLab=305 plus lab K/O 1195/1195, term O/K 3000/3000 plus minor GO/ZH/UH, sites=0.
- safeModeAvailable 6/6 both, ticksToDowngrade 150000 both, never activated.
- Memory.ops.upgFeed.rem later W45N8:SAFE,W45N7:THREAT. r7 on endTime=84420776 by Misaki (was 84420060; not touched). Memory.cmd stale on=1 at=84224348 c={} s={} v=1 by=cmd not touched. war_cmd/pulse not restarted.
- Home RCL7 9630938/10935000=88.07% later 9631170 / live 9631100; W47 6350090/10935000=58.07% later 6351490 / live 6351390.

## Infra / backfill / freezes
- postgres/grafana/listener/dashboard ok; grafana_check all OK; peacetime listener single_slot 5:5:1:1 (restarted 17:22:48 after the 17:12 freeze, python 2569929 started 17:22:57 parent 4035476; end rot W47N8 left~95s at 17:33:33). Earlier restart 16:59:21 after the 16:44 freeze (python 2562267 started 16:59:30).
- 40m official backfill ticks 84417501..84418200 (700, published 84417500..84418100 at game.time=84418294 tick_s=4.099) missing_chunks=0 inserted 6686 already_in_db=19516 ts_realigned=18662. First pass 35/35 official GETs 200. tick_s_in_use=4.13871 (all_mean; later-mean 4.14658) corrective_applied=False nfix=0. confirm/retry2 skipped no targets inserted=0. JP 84418200 at 17:31:26 gt=84418398 all_five_200=True inserted=669 still_404=[] ts_realigned=0. Official+JP through 84418300 all five 800/800. Residual missing ticks are only the unpublished latest chunk after 84418300 (expected).
- NEW leftover official 404 none. Already-told leftover W45N8@84415500 and older aged out of window start 84417501, not retried, do not re-tell as new.
- NEW 盒子休眠 16:44:58–16:59:18 (850s, STATS 84417731..84417949 219t, official-filled 219/219 all five, listener restart 16:59:21 python 2562267 started 16:59:30) — recorded by the quiet 17:07 half-hour and first told in this 1h user log.
- NEW 盒子休眠 17:12:37–17:22:45 (601s, STATS 84418131..84418279 149t, official+JP filled 149/149 all five, listener restart 17:22:48 python 2569929 started 17:22:57) — first told by this 1h patrol.
- NEW 监听短中断 none. Already-told freezes 16:15:02-16:22:09 and 14:47:50-15:01:16 and 14:15:32-14:20:01 and older remain already told. Already-told short interruptions 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20 remain already told.
- exact2h 2h shard_s/t=4.160 1h 4.173. hostiles in owned-room room_stats since last: 0.
- TIP 84418350 stor 17128/25326 17:28:02; later to 84418420 stor 16925/25326; q_later 16875/25326@84418415.

No code change and no deploy this hour (src clean, deploy.lock absent, live still 2026-11-19 02:28 code 2b5398f7).
