# Patrol 2026-11-21 18:27 亚洲/香港

Dir: `/workspace/screeps/state/_patrol_2026-11-21_1817`

## Window
- Previous delivered 1h: 17:33, analysis tip 84397740 / later 84397830
- This analysis tip: **84398530** at 18:23:16 亚洲/香港, stor home 15888 / W47 33758, progress 9229429 / 5957345
- Later live: **84398576/84398577** (~18:26) stor 16388 / 32208, nUp=2 why=remote_pause, w8up=2, keep=2, upLatched=0, sealPark=0, threatSoft=0, softLeft=0, bankWhy=ready
- Later room_stats: **84398580** 18:26:49 亚洲/香港 stor 16388 / 32208, progress 9230277 / 5958345

## Formal alerts
- **W47 upgrade HOLDS** — twenty-seventh consecutive dual after 12:25 clearance. exact2h 17.96/30.08=59.7% (prev 18.71=62.2%) still under AND last800 19.11=63.5% still soft. last20-100 20.00=66.5% is designed keep=2 and must not clear. 1h 18.94=63.0%. model_w8 2h 17.95 vs 30.03 stor_delta +4.79, 1h 19.02 +6.26. Root remains designed keep=2. w8up=3@84398270-84398370 was handoff, not a standing third.
- **Home formal stays CLEARED.** exact2h 19.37/26=74.5% (prev 14.92=57.4%) NOW ABOVE 70%; last800 21.61=83.1% hard; last20-300 hard. 1h 21.89=84.2%. model 2h 19.39 stor_delta +0.75, 1h 21.84 -0.82.
- **Storage-floor stays CLEARED.** tip 15888 ABOVE, later 16388 ABOVE (prev tip 16972 ABOVE). Mid-hour dips (min 14360@84398050 17:48:42; also 14788@84398460 18:18) do not fire. 20k/300t unlocked, 3h max 17798, best>=20k span=0. Do not change 15k floor.
- Locked policy unchanged: keep=2 until 40k/500t locks, no standing third, 15k floor, no labs/market/industry reopen. 40k/500t still unlocked upLatched=0; no 40k touch (W47 min 28762@84397750 max 36750@84398220).

## W45N7 Invader Core (NEW this hour; fold into user log)
- Incident 84398417 18:15:05 亚洲/香港, SAFE->THREAT why=core, def=none
- spawn_start 84398431 18:16:10 defender84398431 waited 14; spawning W46N8 30,34 hits=5000 body=25A25M (full 50-part, not ~2500 cap), memory core=1 remote=W45N7; still spawning at 84398576 (hatch ~84398581)
- Evac complete: rhaulers left 21,0 @84398430-431; rminer84397777 left 21,0 @84398460, W45N8 22,48 @84398461, live 84398542 W45N8 7,30 ttl=764 alive
- W45N7 later not visible. Do not start 指挥官. No Safe Mode. sma=6/6. ttd 150000/150000. W47 seal still lifted.

## Remotes later
- W45N8 vis SAFE res=2084 host=0 core=0
- W45N7 THREAT not vis
- W47N7 vis SAFE res=2479 host=0 core=0
- reserve7 died last 84397922, replacement reserve784398359 spawn 84398361, gap 420t; reservation 2479 healthy. Not formal missing-role. Owned critical roles present.

## New freezes / 404s
- **MUST TELL:** NEW 盒子休眠 17:51:07–17:58:33 (442s, already healed; official-filled all five STATS 84398081..84398189 109/109; listener auto-restart 17:58:36, python 2000028 started 17:58:45)
- **No newer freezes** after 17:51 this run. No new short WS.
- **No new leftover official 404s.**
- Already-told freezes through 17:33 (16:48:46–17:04:41 and 监听短中断 17:23:22, plus older) remain already-told.
- Already-told leftovers including W45N7@84397400 aged out of this official window start 84397701 and were not retried (still 0/100). Also W47N7@84395600, W47N8@84395100, W46N8@84394300, W45N8@84392600, W46N8@84390400, W46N8@84390800, W47N7@84390900, W45N7@84388500, W45N8@84386600 and older — still already-told.
- After this log is delivered: fold only newer freezes/404s than the 17:33 set plus this 17:51 freeze.

## Backfill
- Official history 84397701..84398400 (700, published_bases 84397700..84398300 at game.time=84398495; first pass 35/35 200, missing_chunks=0) inserted=2762 tick_s=4.252
- Just-published 84398400 at 18:23:18 gt=84398531 all_five_200=True; four rooms 100/100 84398401..84398500; W45N7 60/100 max 84398460 (evac empty, not a 404)
- Remaining holes: unpublished tail after 84398500; W45N7 empty after evac. Hour LAST_TIP+1..84398400 all five 660/660.

## CPU / motion / harvest
- CPU 1h min 12.71 max 20.58 avg 17.031 p95 19.78 bucket 9999 n=74; 2h max 23.96@84397560 already told; bucket never drained
- audit exit 2 = known REGRESSION [deploy] vs 2b5398f7 2026-11-19 02:28, not new stuck
- motion exit 1 = known watches waiting_pickup/target_full/queue_blocked/waiting_feed/no_task/parked_threat/w8hauler circ/w8rminer swamp
- Home harvest 2h A/B/R 9.98/9.97/8.12, 1h 9.96/10.00/8.67 (R biggest home gap)
- W47 src_A 0.17/0.00 known link-accounting artifact; src_B 10.42/10.03 R1 7.92/9.78 R2 8.45/10.09
- exact2h shard_s/t 2h 4.273 1h 4.298
- hostiles in owned-room room_stats since last: 0

## Labs / minerals / cmd / listener / infra
- Labs KO still on actOk=1; never unset Memory.ops.labs
- Minerals at 84398503: stor K 221756 O 91200 KO 47236, koLab=380, term K/O 3000
- Memory.cmd stale on at 84224348 by cmd — not taken over
- war_cmd/pulse not running (aborted_by_misaki); commander not holding slots
- Listener single-slot 5:5:1:1 (rot i=1 W47N8)
- Infra postgres/grafana/listener/dashboard ok; q/DB writers fresh
- r7.on endTime=84400992 by Misaki

## Code / deploy
- LIVE still 2b5398f7 (deploy@84345299 02:28). No src change. No deploy this hour. deploy.lock absent.
- Cited game-code baseline remains 289a7f06. Do not name docs squash SHAs or present as game deploys.
- PR 76 and 12h review already told — do not re-tell.
- No code fix shipped: core response used full-budget defender and evac worked; locked policy forbids keep/floor/labs changes.

## Remaining not-yet-told after this delivery
- None from the 18:13 backfill (17:51 freeze is included here). Next patrol should fold only freezes/404s newer than 17:51:07–17:58:33 and newer leftover 404s than the already-told set (no new leftover this hour).
