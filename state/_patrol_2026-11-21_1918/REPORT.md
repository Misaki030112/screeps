# Patrol 2026-11-21 19:28 亚洲/香港

Dir: `/workspace/screeps/state/_patrol_2026-11-21_1918`

## Window
- Previous delivered 1h: 18:27, analysis tip 84398530 / later 84398580
- This analysis tip: **84399390** at 19:24:47 亚洲/香港, stor home 17114 / W47 25612, progress 9245811 / 5973705
- Later room_stats: **84399430** 19:27:43 亚洲/香港 stor 16414 / 25312, progress 9246229 / 5974505
- Live snapshot ~19:19–19:20 t=84399316..84399331: nUp=2 why=ok, w8up=2, keep=2, upLatched=0, sealPark=1 why=ok, threatSoft=0, softLeft=0, bankWhy=ready, rem W45N8:SAFE,W45N7:SAFE, sma=6/6, ttd=150000/150000, bucket=10000, labs KO actOk=1

## Formal alerts
- **W47 upgrade HOLDS** — twenty-eighth consecutive dual after 12:25 clearance. exact2h 19.08/30.08=63.4% (prev 17.96=59.7%) still under AND last800 18.95=63.0% still soft. last20–300 20.00=66.5% is designed keep=2 and must not clear. last500 19.61=65.2% still soft. 1h 19.00=63.2%. model_w8 2h 19.0 vs 30.03 stor_delta -1.79, 1h 18.98 stor_delta -9.93. Root remains designed keep=2. Do not change keep/softCap, no standing third, no 40k unseal.
- **Home formal stays CLEARED.** exact2h 20.36/26=78.3% (prev 19.37=74.5%) ABOVE 70%; last800 19.13=73.6% hard; last20–500 hard (~25–28 e/t). 1h 19.45=74.8%. model 2h 20.24 stor_delta +0.09, 1h 18.61 +1.01.
- **Storage-floor stays CLEARED.** tip 17114 ABOVE, later 16414 ABOVE (prev tip 15888 ABOVE). Mid-hour dips (min 14347@84398640 18:31:10) do not fire. nUp=3@84398610 was handoff, not a standing third; nUp=1@84398720 floor then nUp=2@84399030. 20k/300t unlocked, 3h max 17798, best>=20k span=0. Do not change 15k floor.
- Locked policy unchanged. 40k/500t still unlocked upLatched=0; no 40k touch this hour (W47 min 25408@84399180 19:09:32, max 33758@84398530 tip start, later 25312). 3h max still 36750@84398220 18:00. sealPark re-opened (was 0 last patrol) at sealMinE=25000, sticky why=ok.

## W45N7 Invader Core (CLOSED this hour; fold into user log)
- Incident 84398417 18:15:05 THREAT why=core (already told last patrol as hatching)
- spawn_start 84398431 18:16:10 defender84398431 waited 14; hatch/defend 84398581 18:26:54 why=dispatched dur=164; body 25A25M hits=5000 full budget
- arrive 84398649 18:31:48 travel=68 at W45N7 21,0
- cleared 84398824 18:44:14 ev=cleared why=killed dur=407; hits min/max 5000/5000 entire life
- Left W45N7 84398866, briefly W46N8 48,21 @84398907, lingered W45N8 3,26 (known queue_blocked post-check; motion 137 queue_blocked ticks); gone live by 84399321 (roles had no defender; defs out={})
- Civilians returned W45N7 84399001 ~18:56:43 (reserver, rhauler, rminer)
- All three remotes vis SAFE host=0 core=0 at live 84399327/84399328. Do not start 指挥官. No Safe Mode. sma=6/6.

## Remotes later / live
- W45N8 vis SAFE res=2348 host=0 core=0
- W45N7 vis SAFE res=1012 host=0 core=0 (reservation low due to evac)
- W47N7 vis SAFE res=2585 host=0 core=0
- reserve784398359 last W47N7 84398970 ~18:55; replacement reserve784399413 in creep_ticks 84399414..84399423 ~19:27; gap ~444t; reservation 2585 healthy. Not formal missing-role. Owned critical roles present (miner/rminer/reserver/queen/w8filler live).

## New freezes / 404s
- **MUST TELL:** NEW 盒子休眠 18:47:50–18:58:17 (626s, already healed; STATS 84398871..84399029, 159t; official-filled W46N8/W47N8/W45N8/W47N7 159/159, W45N7 29/159 only 84399001..84399029 because evac empty 84398871..84399000 official 200 not a 404; listener auto-restart 18:58:20)
- **MUST TELL:** NEW 盒子休眠 19:10:45–19:18:45 (476s, already healed; STATS 84399191..84399309, 119t; after just-published fill: W46N8 115/119, W47N8 109/119, W45N8 100/119, W45N7 47/119, W47N7 109/119; missing head is leftover official 404 84399100 (84399191..84399200); listener auto-restart 19:18:48, resumed single-slot W46N8)
- **MUST TELL:** NEW leftover official 404 all five @84399100 (first pass and confirm 19:22 gt=84399359 still 404; listener partial only). NEW leftover official 404 W45N8@84399300 (just-published 19:28 gt proxy 84399430 still 404 after retry; other four rooms 200, 100/100 84399301..84399400).
- Already-told freeze 17:51:07–17:58:33 and short WS 17:23:22 remain already-told, not re-told.
- Already-told leftovers W45N7@84397400 / W47N7@84395600 / W47N8@84395100 / W46N8@84394300 / W45N8@84392600 / W46N8@84390400 / W46N8@84390800 / W47N7@84390900 / W45N7@84388500 / W45N8@84386600 and older remain already-told (aged out or not retried).
- After this log is delivered: fold only newer freezes/404s than 19:10:45–19:18:45 and newer leftover 404s than all-five @84399100 plus W45N8@84399300.

## Backfill
- Official history 84398601..84399300 (700, published_bases 84398600..84399200 at game.time=84399316; first pass 30/35 official GETs 200, missing_chunks=5 all five @84399100) inserted=4918 already_in_db=18654 tick_s=4.217 ts_realigned=12345
- 84399200 was 200 on first pass (all five)
- Confirm 19:22 still 404 all five @84399100 inserted=0
- Just-published 84399300 at 19:28:10 gt proxy 84399430: W46N8/W47N8/W45N7/W47N7 200 inserted=80/1515/496/415, W45N8 still 404
- W45N7 evac empty 84398601..84398648 and 84398866..84399000 are official 200, not 404s
- Remaining holes: leftover 84399100 (partial listener), leftover W45N8@84399300, unpublished tail after 84399400, W45N7 evac empty

## CPU / motion / harvest
- CPU 1h min 13.68 max 25.78@84399170 19:08:49 mean 17.66 p95 20.39 bucket 10000 n=58; 2h min 12.71 max 25.78 mean 17.29 p95 20.04 bucket 9999 n=132; bucket never drained. No formal CPU.
- audit exit 2 = known REGRESSION [deploy] vs 2b5398f7 2026-11-19 02:28, not new stuck, not alert (d)
- motion exit 1 = known watches waiting_pickup / target_full / queue_blocked / waiting_feed / no_task / w8hauler circ / w8rminer swamp; defender84398431 queue_blocked is post-check linger in W45N8, not a new stuck class; rhauler waiting_pickup elevated during W45N7 evac
- Home harvest 2h A/B/R 9.98/9.98/8.61, 1h 10.00/9.96/7.06 (R biggest home gap — W45N7 evac)
- W47 src_A 0.32/0.69 is the known link-accounting artifact; src_B 9.17/9.27; R1 7.85/5.64; R2 6.84/1.79 (1h R2 dip from miner handoff + 84399100 hole + freeze; live w8rminer=2)
- exact2h shard_s/t 2h/1h 4.295
- hostiles in owned-room room_stats since last: 0

## Labs / minerals / cmd / listener / infra
- Labs KO still on actOk=1; never unset Memory.ops.labs
- Minerals at 84399323: stor K 221756 O 90000 KO 47236, koLab=790, term K/O 3000 plus small GO/ZH/UH; sites=0
- Memory.cmd stale on at 84224348 by cmd — not taken over
- war_cmd/pulse not running (aborted_by_misaki); commander not holding slots
- Listener single-slot 5:5:1:1 (rot i=0 W46N8 at 19:22 / 19:19)
- Infra postgres/grafana/listener/dashboard ok; q/DB writers fresh
- r7.on endTime=84401912 by Misaki

## Code / deploy
- LIVE still 2b5398f7 (deploy@84345299 02:28). No src change. No deploy this hour. deploy.lock absent.
- Cited game-code baseline remains 289a7f06. Do not name docs squash SHAs or present as game deploys.
- PR 76, PR 77, and 12h review already told — do not re-tell.
- No code fix shipped: core response used full-budget defender and evac/return worked; locked policy forbids keep/floor/labs changes; no new motion/logic bug beyond known classes.

## Remaining not-yet-told after this delivery
- None from the 19:09 backfill (18:47 freeze is included here) or this hour's 19:10 freeze and new leftover 404s. Next patrol should fold only freezes newer than 19:10:45–19:18:45 and newer leftover 404s than all-five @84399100 plus W45N8@84399300.
