# Patrol 2026-11-21 22:35 亚洲/香港

Dir: `/workspace/screeps/state/_patrol_2026-11-21_2226`

## Window
- Previous delivered 1h: 21:31, analysis tip 84401080 / later 84401150 / live 84401156
- This analysis tip: **84401970** at 22:29:15 亚洲/香港, stor home 16058 / W47 26299, progress 9303729 / 6024989 (85.08% / 55.10% of 10935000)
- Later room_stats: **84402040** 22:34:17 亚洲/香港 stor 16754 / 27328, progress 9304709 / 6026707
- Live ~22:34 t=84402043..84402046: home stor 16804 / W47 27328, p 9304751 / 6026779 (85.08% / 55.12%), nUp=1 why=ok, w8up=2 keep=2 upLatched=0, sealPark=1 why=threat, threatSoft=1, bankWhy=threatSoft, sma=6/6, ttd=150000/150000, bucket=10000, labs KO still on
- LIVE remains the already-live 2026-11-19 02:28 code (commit 2b5398f7, src clean, deploy.lock absent)

## Formal alerts
- **W47 upgrade HOLDS** — thirty-first consecutive dual after 12:25 clearance. exact2h 19.99/30.08=66.5% (prev 20.07=66.7%) still under AND last800 19.47=64.7% still soft. last20 25.70=85.4% / last30 21.57=71.7% are post-freeze short samples (room_stats gap 190t) and must not clear; last300 20.66=68.7% and last500 20.52=68.2% still soft. 1h 19.49=64.8%. model_w8 2h 19.99 vs 30.03 stor_delta -5.45, 1h 19.49 stor_delta +1.55. Root remains designed keep=2 plus residual threatSoft seal (w8threat=84401627, window 1500, ~1087 ticks / ~76 min left at live). Do not change keep/softCap, no standing third, no 40k unseal.
- **Home formal stays CLEARED.** exact2h 25.05/26=96.3% (prev 22.34=85.9%) well above 70%, not under; last800 22.05=84.8% hard; 1h 22.36=86.0% hard; last1500 24.71=95.1%. Short last20–500 soft (14.00=53.8% / last500 16.39=63.1%) is nUp=1 after the floor, context only, not a dual. model 2h 25.02 stor_delta -1.97, 1h 22.27 stor_delta +0.50.
- **Storage-floor stays CLEARED (first under this patrol, not two consecutive).** last patrol tip 16250 later ~15790 ABOVE (min 15540). This hour: before freeze 16120@84401310 21:42:21 ABOVE; first sample after freeze 14620@84401590 22:02:03 UNDER; min 14000@84401620 22:04:12; recovered 15048@84401680 22:08:32; later/live ~16654–17564 ABOVE (live 16804). since_last under15k=9/45=20%. Cause: late-replacement overlap nUp=3 (84401240–84401630; upgrader84399765 died 84401315, 84401234 already hatched, short-lived 84401574 during the freeze) kept upgrade ~26.8 e/t across the 279-tick freeze and drained 16120→14620. floor_bank then dropped to nUp=1 at 84401660 and storage recovered. Live nUp=1 why=ok (no longer floor_bank) at 16754 — not a missing role. 20k/300t unlocked, 3h max still 19933@84400370, best>=20k span=0. Do not change 15k floor.
- Locked policy unchanged. 40k/500t still unlocked upLatched=0; no 40k touch this hour (W47 since_last min 23656@84401680, max later 28128@84402000; 3h max still 38748@84400220 20:24:03). sealPark remains closed why=threat / threatSoft after w8threat=84401627. Brief home nUp=3 and earlier w8up=3@84401140 (already told last patrol) are replacement overlap, not a standing third. Live w8up=2 keep=2.

## W47 local threat stamp at 84401627 (not an active invader ALERT)
- Memory.ops.w8threat = w8flee = w8inv = 84401627 (~22:04). threatSoft still on (WINDOW 1500; expires ~84403127, ~76 min after live).
- w8guard84401622 spawned at W47N8 34,30 from 84401624, body hitsMax 4100 (never damaged), walked to the north hold 29,5 and stayed parked_threat. Cost ~2720 (w8fm ep 84401623).
- No invader name in creep_ticks; no new rem incident after the resolved 84400223 episode; owned-room room_stats hostiles=0 the whole hour; live host=0 core=0 in all five rooms.
- W47N7 civilians (w8rminers, w8rhauler, reserve7, leftover rdef) did not flee at 84401627 — they stayed on task. This looks like a brief/north-border flash (or a 1-tick hostile official history does not store), not an ongoing invasion.
- Leftover rdef84400224 aged out 84401873 during the second freeze, hits 5000 the whole life, last in W47N7 31,15. Not combat death.
- Do not start 指挥官. No Safe Mode. sma=6.

## Remotes later / live
- W45N8 vis SAFE res=2064 host=0 core=0 at 84402045
- W45N7 vis SAFE res=2294 host=0 core=0
- W47N7 vis SAFE res=2867 host=0 core=0
- Reservers present (2) and reserve7 present at later samples. Owned critical roles present (miner/rminer/queen/w8filler/upgraders live). nUp=1 is floor aftermath, not formal missing-role.

## New freezes / 404s
- **MUST TELL:** NEW 盒子休眠 21:42:29–22:01:09 (1115s, already healed; STATS 84401311..84401589, 279t; official-filled all five 279/279; room_stats gap 84401310..84401590 wall ~1182s is this freeze; listener auto-restart 22:01:12, python 2104047 started 22:01:21). Folded from the quiet 22:00 backfill; not told in the 21:31 patrol.
- **MUST TELL:** NEW 盒子休眠 22:14:12–22:26:30 (737s, already healed; STATS 84401751..84401939, 189t; official-filled all five 189/189 after just-published 84401900 at 22:34:58 — first pass already had 84401751..84401900 150/150 all five; unpublished tail 84401901..84401939 filled official 22:34; listener auto-restart 22:26:33, python 2110888 started 22:26:42).
- No new leftover official 404 this hour (first pass 35/35 official GETs 200, missing_chunks=0; just-published all_five_200, still_404 none). No new short WS after 21:31 (3–5s gaps are q.py intervals).
- Already told by the 21:31 patrol and not re-told: 盒子休眠 20:49:04–21:04:03, 监听短中断 21:13:29, leftover official 404s W45N7@84400300, W45N7@84400400, and older (W47N8@84400100, W45N7@84399800, W45N8@84399500, 19:52:19–20:02:21, 20:21:38, etc.). Those leftovers have aged out of this window start 84401201 and were not retried.
- After this log is delivered: fold only newer freezes/short WS than 21:42:29–22:01:09 and 22:14:12–22:26:30, and newer leftover official 404s than the already-told set (W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older).

## Backfill
- Official history 84401201..84401900 (700, published_bases 84401200..84401800 at game.time=84401945; first pass 35/35 official GETs 200, missing_chunks=0) inserted=9732 already_in_db=14023 tick_s=4.185 ts_realigned=13680
- overlap compared=13793 match=13793 differ=0
- Confirm/retry2 skipped (no 404 targets)
- Just-published 84401900 at 22:34:37–22:34:58 gt=84402045 all_five_200=True inserted=2817 (W46N8 846, W47N8 649, W45N8 485, W45N7 390, W47N7 447); all five 100/100 in 84401901..84402000
- Remaining holes: unpublished tail after 84402000 only (expected)

## CPU / motion / harvest
- CPU 1h min 13.51 max 25.74@84401290 21:40:56 mean 17.33 p95 19.77 bucket 10000 n=40; 2h min 13.51 max 25.74 mean 17.11 p95 20.34 bucket 10000 n=101; bucket never drained. Max is higher than last patrol's 21.7 but not near drain. No formal CPU.
- audit exit 2 = known REGRESSION [deploy] vs already-live 2026-11-19 02:28 code, not new stuck, not alert (d)
- motion exit 1 = known watches waiting_pickup / target_full / queue_blocked / waiting_feed / no_task / parked_threat. rdef84400224 queue_blocked is the same known post-combat linger until TTL end 84401873. w8guard84401622 parked_threat is the designed north-hold after the 84401627 stamp, not a new stuck. No new stuck/oscillation class.
- Home harvest 2h A/B/R 9.99/9.95/8.48, 1h 10.00/9.92/8.95 (R still the biggest home gap, but improved vs last patrol 6.94/6.85)
- W47 src_A 0.21/0.42 is the known link-accounting artifact; src_B 8.24/7.92; 2h R1 3.23 / R2 2.95 still carry the earlier evac hole, 1h R1 5.65 / R2 6.03 recovering — expected, not a new bug
- exact2h shard_s/t 2h 4.294 / 1h 4.270
- hostiles in owned-room room_stats since last: 0

## Labs / minerals / cmd / listener / infra
- Labs KO still on; never unset Memory.ops.labs
- Minerals at 84401972: stor K 220156 O 89200 KO 48836, term K/O 3000 plus small GO/ZH/UH; sites=0
- Memory.cmd stale on at 84224348 by cmd — not taken over
- war_cmd/pulse not running (aborted_by_misaki); commander not holding slots; no handoff
- Listener single-slot 5:5:1:1 (rot i=2 W45N8 at 22:35:05 left 50s) — python 2110888 started 22:26:42 after the second freeze restart
- Infra postgres/grafana/listener/dashboard ok; grafana_check OK; q/DB writers fresh; 40m history backfill succeeded
- W47 mineral miner=0 why=miner is a known mineral-line gap, not a formal missing critical role

## Code / deploy
- LIVE still the already-live 2026-11-19 02:28 code (2b5398f7). src clean, deploy.lock absent.
- No code change and no deploy this hour. Home storage dip is the designed 15k floor after a late-replacement nUp=3 overlap drained storage during the first freeze. W47 threatSoft is the designed 1500-tick window after the 84401627 stamp; no visible invader remains. Motion anomalies are known watches, not a new shippable stuck class. Locked policies not touched.
