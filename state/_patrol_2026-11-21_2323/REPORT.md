# Patrol 2026-11-21 23:35 亚洲/香港

Dir: `/workspace/screeps/state/_patrol_2026-11-21_2323`

## Window
- Previous delivered 1h: 22:35, analysis tip 84401970 / later 84402040 / live 84402043
- This analysis tip: **84402790** at 23:27:55 亚洲/香港, stor home 15706 / W47 32035, progress 9324953 / 6040857 (85.28% / 55.24% of 10935000)
- Later room_stats: **84402870** 23:33:40 亚洲/香港 stor 15306 / 30285, progress 9326073 / 6042457; 84402880 23:34:23 stor 15808 / 30285
- Live ~23:33 t=84402869..84402872: home stor 15306 / W47 30285, p 9326059 / 6042437 (85.29% / 55.26%), nUp=1 why=floor_bank, w8up=2 keep=2 upLatched=0, sealPark=1 why=threat, threatSoft=1, bankWhy=threatSoft, sma=6/6, ttd=150000/150000, bucket=10000, labs KO still on
- LIVE remains the already-live 2026-11-19 02:28 code (commit 2b5398f7, src clean, deploy.lock absent)

## Formal alerts
- **W47 upgrade HOLDS** — thirty-second consecutive dual after 12:25 clearance. exact2h 19.43/30.08=64.6% (prev 19.99=66.5%) still under AND last800 19.18=63.8% still soft. last20 20.00=66.5% / last30 20.00=66.5% is designed keep=2 and must not clear; last140 15.86=52.7% / last200 15.60=51.9% / last300 17.07=56.7% / last500 17.68=58.8% are softer and include the 23:20 STATS gap, also must not clear. 1h 19.50=64.8%. model_w8 2h 19.43 vs 30.03 stor_delta +4.51, 1h 19.29 stor_delta +5.41. Root remains designed keep=2 plus residual threatSoft seal (w8threat=84401627, window 1500, expires ~84403127, ~257 ticks / ~18 min left at later ~84402870). Do not change keep/softCap, no standing third, no 40k unseal.
- **Home formal stays CLEARED.** exact2h 24.14/26=92.8% (prev 25.05=96.3%) well above 70%, not under; last800 26.18=100.7% hard; 1h 25.61=98.5% hard; last1500 23.67=91.0%; short last20–500 all hard (23.80=91.5% through 27.69=106.5%). model 2h 24.11 stor_delta -0.09, 1h 25.74 stor_delta -0.30.
- **Storage-floor stays CLEARED (unders this hour recovered; not two consecutive patrols).** last patrol tip 16058 later ~16654–16804 ABOVE. This tip 15706 ABOVE. Two unders this hour, both recovered: (1) 14976@84402600 23:14:12, next sample 15076@84402610 23:14:57; (2) after tip 14406@84402820 23:30:07, min 13706@84402830 23:30:52, recovered 15206@84402860 23:32:58, later 15306@84402870 and 15808@84402880. since_last under15k through tip was 1/61=1.6%; later added the second dip then recovery. floor_bank dropped nUp to 1 by later (84402870 / live why=floor_bank). Live/later ABOVE. 20k/300t unlocked, 3h max still 19933@84400370, best>=20k span=0. Do not change 15k floor.
- Locked policy unchanged. 40k/500t still unlocked upLatched=0; no 40k touch this hour (W47 since_last min 26299@84401970, max 32035@84402750, later 30285; 3h max 34649@84400340 20:32:41 — previous 38748@84400220 20:24:03 aged out of this 3h window). sealPark remains closed why=threat / threatSoft after w8threat=84401627. Brief home nUp=3@84402750–84402780 and w8up=3@84402580–84402680 / w8filler 3 after 84402820 are replacement overlap, not a standing third. Later w8up=2 keep=2.

## W47 local threat stamp at 84401627 (still windowed, not an active invader ALERT)
- Memory.ops.w8threat = w8flee = w8inv = 84401627 (~22:04). threatSoft still on (WINDOW 1500; expires ~84403127, ~18 min after later 84402870, around ~23:52).
- w8guard84401622 still at W47N8 29,5, hits 4100/4100 the whole hour, ttl 458 at 84402786 (~374 at later). parked_threat is the designed north-hold, not a new stuck.
- No invader in creep_ticks; owned-room room_stats hostiles=0 the whole hour; live/later host=0 core=0 in all five rooms.
- Do not start 指挥官. No Safe Mode. sma=6.

## Remotes later / live
- W45N8 vis SAFE res=2052 host=0 core=0 at 84402871
- W45N7 vis SAFE res=2114 host=0 core=0
- W47N7 vis SAFE res=2641 host=0 core=0
- Reserver present (1) and reserve7 present at later samples. Owned critical roles present (miner/rminer/queen/w8filler/upgraders live). nUp=1 is floor_bank after the 13706 dip, not formal missing-role.
- reserve7 was absent 84402119..84402560 (old reserve784401507 aged out 84402118, new reserve784402559 spawned 84402561). This is designed: wantSpawn only when our reservation left < 2500. W47N7 reservation stayed healthy (later 2641). Not formal (c). Home reserver zero-run 50 ticks 84402460–84402510 is a normal replacement, under 100.

## New freezes / 404s
- **MUST TELL:** NEW 盒子休眠 22:49:18–22:59:56 (634s, already healed; STATS 84402241..84402409, 169t; official-filled all five 169/169; room_stats gap 84402240..84402410 wall ~721s is this freeze; listener auto-restart 22:59:59, python 2124111 started 23:00:09). Folded from the quiet 23:10 backfill; not told in the 22:35 patrol. Re-verified against freeze_clock / box_pauses / official fill this run.
- **MUST TELL:** NEW 盒子休眠 23:20:38–23:24:23 (224s, already healed; STATS 84402681..84402749, 69t; official first pass filled 84402681..84402700 20/20 all five; unpublished tail 84402701..84402749 filled official 23:33:37 just-published 84402700, all five 49/49 and 84402701..84402800 100/100; listener auto-restart 23:24:26, python 2135086 started 23:24:35). The 23:17:11–23:20:11 room_stats timestamp bunching (84402650–84402680 flushed together) is the onset of this same freeze, not a separate short WS or box_pauses row.
- No new leftover official 404 this hour (first pass 35/35 official GETs 200, missing_chunks=0; just-published first attempt 23:28:52 gt=84402801 all five still 404, too early; retry2 23:30:55 gt=84402831 SSL error; late 23:33:37 gt=84402869 all_five_200, still_404 none). No new short WS after 22:35 (freeze_clock short 3–59s list empty; 3–5s gaps are q.py intervals).
- Already told by the 22:35 patrol and not re-told: 盒子休眠 21:42:29–22:01:09, 盒子休眠 22:14:12–22:26:30, leftover official 404s W45N7@84400300, W45N7@84400400, W47N8@84400100 and older. Those leftovers have aged out of this window start 84402001 and were not retried.
- After this log is delivered: fold only newer freezes/short WS than 22:49:18–22:59:56 and 23:20:38–23:24:23, and newer leftover official 404s than the already-told set (W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older).

## Backfill
- Official history 84402001..84402700 (700, published_bases 84402000..84402600 at game.time=84402776; first pass 35/35 official GETs 200, missing_chunks=0) inserted=5680 already_in_db=19041 tick_s=4.220 ts_realigned=13452
- overlap compared=18737 match=18737 differ=0
- Confirm/retry2 skipped (no 404 targets)
- Just-published 84402700 first 23:28:52 gt=84402801 all five 404 inserted=0; retry2 23:30:55 gt=84402831 SSL mid-GET; late 23:33:37–23:33:57 gt=84402869 all_five_200=True inserted=2839 (W46N8 754, W47N8 907, W45N8 376, W45N7 406, W47N7 396); all five 100/100 in 84402701..84402800
- Remaining holes: unpublished tail after 84402800 only (expected)

## CPU / motion / harvest
- CPU 1h min 13.72 max 24.03@84402560 23:11:18 mean 16.94 p95 19.87 bucket 10000 n=62; 2h min 13.51 max 25.74@84401290 mean 17.09 p95 19.87 bucket 10000 n=102; since_last min 13.72 max 24.03 mean 16.92 p95 20.23 n=61. Bucket never drained. No formal CPU.
- audit exit 2 = known REGRESSION [deploy] vs already-live 2026-11-19 02:28 code, not new stuck, not alert (d)
- motion exit 1 = known watches waiting_pickup / target_full / queue_blocked / waiting_feed / no_task / parked_threat. w8guard84401622 parked_threat is the designed north-hold after the 84401627 stamp, not a new stuck. rdef84400224 still appears only in the 2h window (aged out 84401873, already told last patrol). No new stuck/oscillation class.
- Home harvest 2h A/B/R 9.97/9.96/8.34, 1h 9.94/10.00/7.72 (R still the biggest home gap; 1h 7.72 a bit softer than last patrol 8.95)
- W47 src_A 0.21 / 1h "—" is the known link-accounting artifact; src_B 8.21/8.97; 2h R1 6.94 / R2 7.70, 1h R1 8.68 / R2 9.90 recovered from last patrol's 1h 5.65/6.03 — expected, not a new bug
- exact2h shard_s/t 2h 4.284 / 1h 4.290
- hostiles in owned-room room_stats since last: 0

## Labs / minerals / cmd / listener / infra
- Labs KO still on; never unset Memory.ops.labs
- Minerals at 84402787: stor K 220156 O 89200 KO 48836, term K 1800 O 3000 plus small GO/ZH/UH; sites=0
- Memory.cmd stale on at 84224348 by cmd — not taken over
- war_cmd/pulse not running (aborted_by_misaki); commander not holding slots; no handoff
- Listener single-slot 5:5:1:1 (rot i=1 W47N8 at 23:32:53 left 230s, slot started 23:26:43 for 600s) — python 2135086 started 23:24:35 after the 23:20 freeze restart
- Infra postgres/grafana/listener/dashboard ok; grafana_check OK (login 200, /api/health database ok, dashboard 200); q/DB writers fresh; 40m history backfill succeeded (late just-published recovered)
- W47 mineral miner=0 why=miner is a known mineral-line gap, not a formal missing critical role
- errors.log after 22:35 contains only the two box-freeze reconnect lines (22:59:56 and 23:24:23); no new game console errors

## Code / deploy
- LIVE still the already-live 2026-11-19 02:28 code (2b5398f7). src clean, deploy.lock absent. room_stats commit=2b5398f7 at tip.
- No code change and no deploy this hour. Home storage dips are the designed 15k floor after brief nUp=2 drain (floor_bank then nUp=1, later recovered). W47 threatSoft is the designed 1500-tick window after the 84401627 stamp; no visible invader remains; reserve7 replacement delay is the designed left<2500 gate. Motion anomalies are known watches, not a new shippable stuck class. Locked policies not touched.
