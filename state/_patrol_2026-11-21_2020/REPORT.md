# Patrol 2026-11-21 20:34 亚洲/香港

Dir: `/workspace/screeps/state/_patrol_2026-11-21_2020`

## Window
- Previous delivered 1h: 19:28, analysis tip 84399390 / later 84399430
- This analysis tip: **84400300** at 20:29:43 亚洲/香港, stor home 19233 / W47 35349, progress 9261919 / 5991603 (84.70% / 54.79% of 10935000)
- Later room_stats: **84400350** 20:33:24 亚洲/香港 stor 19733 / 34649, progress 9263299 / 5992603
- Live ~20:34 t=84400355..84400365: home stor 19783 / W47 34149, p 9263439 / 5992703, nUp=2, w8upgraders=2, keep=2, upLatched=0, sealPark=1 why=threat, threatSoft=1, bankWhy=threatSoft, sma=6/6, ttd=150000/150000 earlier, bucket=10000, labs KO still on
- LIVE commit still 2b5398f7 (deploy@84345299 02:28)

## Formal alerts
- **W47 upgrade HOLDS** — twenty-ninth consecutive dual after 12:25 clearance. exact2h 19.32/30.08=64.2% (prev 19.08=63.4%) still under AND last800 19.56=65.0% still soft. last20–300 20.00=66.5% is designed keep=2 and must not clear. last500 20.17=67.1% still soft. 1h 19.64=65.3%. model_w8 2h 19.32 vs 30.03 stor_delta +3.02, 1h 19.64 stor_delta +13.85. Root remains designed keep=2. Do not change keep/softCap, no standing third, no 40k unseal.
- **Home formal stays CLEARED.** exact2h 18.21/26=70.0% (prev 20.36=78.3%) is on the 70% line, not under; last20–500 hard (~19–28 e/t, last20–140 104–108%); last800 17.16=66.0% soft is context only; 1h 17.71=68.1% also soft context. model 2h 18.11 stor_delta +1.58, 1h 17.08 +2.40.
- **Storage-floor stays CLEARED.** tip 19233 ABOVE, later ~19733–19783 ABOVE (prev tip 17114 ABOVE). Mid-hour dips (min 14214@84399560 19:37:13) do not fire. nUp=1 at floor then nUp=2@84400110. 20k/300t unlocked, 3h max ~19783, best>=20k span=0. Do not change 15k floor.
- Locked policy unchanged. 40k/500t still unlocked upLatched=0; no 40k touch this hour (W47 min 23855@84399650 19:43:37, max 38748@84400220 20:24:03, later 34149@84400355). sealPark re-closed why=threat / threatSoft after the W47N7 invader (was open why=ok at 84400221, storE then ~36785–38748).

## W47N7 Invader (OPEN this hour; must tell)
- Incident 84400223 20:24:17 THREAT why=solo, episode remote-W47N7-84400223, invOnly=true, creeps=1, positions [45,49], action defender requested
- Invader name invader_W47N7_768 body ttmmmmrwam hits 1000/1000
  - 84400223 at W47N7 45,49
  - 84400259 at W47N7 25,25 ttl 1464 still 1000/1000
- spawn_start 84400224 rdef84400224 waited 0–1; body 19R25M6H hits=5000 cost 5600 full budget (not capped at ~2500); Spawn2 W47N8 34,30
- Still spawning at live 84400365 20:34:28 rem ~9, hatch ~84400374 ~20:35
- Civilians: two rminers still in W47N7 at 84400267 (25,13 and 22,19); evac complete by 84400354 (all w8r* in W47N8; W47N7 vis=false at 84400364)
- Home remotes W45N8/W45N7 vis SAFE host=0 core=0 res 2395 / 2163 at 84400364
- Do not start 指挥官. No Safe Mode. sma=6.

## Remotes later / live
- W45N8 vis SAFE res=2395 host=0 core=0
- W45N7 vis SAFE res=2163 host=0 core=0
- W47N7 not vis at 84400364 after evac; last vis 84400259 res=2701 host=1 core=0
- No live reservers at 84400365. reserve7 last_nonzero 84400020 ~20:09:50; gap from 84400030 (~20:10, 270t by tip 84400300, longer by 20:34). Reservations healthy. Not formal missing-role. Owned critical roles present (miner/rminer/queen/w8filler live; home reserver count dipped to 0 late, reservations still healthy).

## New freezes / 404s
- **MUST TELL:** NEW 盒子休眠 19:52:19–20:02:21 (599s, already healed; STATS 84399771..84399919, 149t; official-filled W46N8/W47N8/W45N8/W47N7 149/149, W45N7 30/149 only 84399771..84399800 because leftover official 404 W45N7@84399800 plus official-200 empty 84399901..84399919; listener auto-restart 20:02:25, python 2055432 started 20:02:34)
- **MUST TELL:** NEW 监听短中断 20:21:38 ping/pong timed out (not a box freeze; no box_pauses row); restart 20:21:41, slot W46N8 20:21:53; STATS hole 84400171..84400189 (19t) after 84400170 20:20:31 before 84400190 20:21:55 wall 84s vs normal ~42s sample; official/listener fill 19/19 for W46N8, W45N8, W45N7, W47N7; W47N8 0/19 because leftover official 404 W47N8@84400100
- **MUST TELL:** NEW leftover official 404 W45N8@84399500 (from quiet 19:47 backfill; confirm 20:25:50 gt=84400245, retry2 20:28:08 gt=84400277, late 20:33:06 still 404; listener 28/100 84399548..84399575; hole 72 ticks 84399501..84399547 and 84399576..84399600)
- **MUST TELL:** NEW leftover official 404 W45N7@84399800 (from quiet 20:00 halfhour; confirm+retry2+late still 404; listener 0/100; hole 100 ticks 84399801..84399900)
- **MUST TELL:** NEW leftover official 404 W47N8@84400100 (first-pass 404; confirm 20:25:52, retry2 20:28:11, late just-pub 20:33:06 still 404; listener 0/100 in chunk, including the 20:21 19-tick STATS hole; hole 100 ticks 84400101..84400200)
- Already told by the 19:18/19:28 patrol and not re-told: 盒子休眠 19:10:45–19:18:45, 18:47:50–18:58:17, leftover official 404 all five @84399100, W45N8@84399300, and older freezes/404s.
- After this log is delivered: fold only newer freezes/short WS than 19:52:19–20:02:21 and 20:21:38, and newer leftover official 404s than W45N8@84399500 / W45N7@84399800 / W47N8@84400100.

## Backfill
- Official history 84399501..84400200 (700, published_bases 84399500..84400100 at game.time=84400206; first pass 30/35 official GETs 200, missing_chunks=5 W45N8@84399500, W45N7@84399800, W47N8@84400100, W45N8@84400100, W47N7@84400100) inserted=4514 already_in_db=19786 tick_s=4.212 ts_realigned=0
- Confirm 20:25:49 gt=84400245 recovered W45N8@84400100 inserted=444 and W47N7@84400100 inserted=547; still_404 W45N8@84399500, W45N7@84399800, W47N8@84400100
- retry2 20:28:08 gt=84400277 still those three 404s; W45N8@84400100 +6
- Just-published 84400200 at 20:32:42 gt=84400340 all_five_200=True inserted=2299 (W46N8 503, W47N8 433, W45N8 562, W45N7 460, W47N7 341); W47N7 db 95/100 missing official-empty 84400296..84400300 (evac, our creeps gone; not a 404)
- Late leftover retry at 20:33 still_404 the three leftovers inserted=0
- Remaining holes: leftover W45N8@84399500 (partial listener), leftover W45N7@84399800, leftover W47N8@84400100, unpublished tail after 84400300, W47N7 evac empty at end of 84400200

## CPU / motion / harvest
- CPU 1h min 13.58 max 22.14@84399600 19:40:01 mean 17.27 p95 19.56 bucket 9995–10000 n=71; 2h min 13.58 max 25.78@84399170 19:08:49 (already in last patrol's 2h window) mean 17.48 p95 20.37 bucket ~10000 n=130; bucket never drained. No formal CPU.
- audit exit 2 = known REGRESSION [deploy] vs 2b5398f7 2026-11-19 02:28, not new stuck, not alert (d)
- motion exit 1 = known watches waiting_pickup / target_full / queue_blocked / waiting_feed / no_task / w8hauler circ / w8rminer swamp. No new stuck/oscillation class.
- Home harvest 2h A/B/R 9.99/9.98/6.46, 1h 9.98/10.00/6.03 (R still the biggest home gap)
- W47 src_A 0.43/0.21 is the known link-accounting artifact; src_B 9.50/8.64; R1 9.55/11.4; R2 7.91/12.63 (1h R2 recovered from last patrol's dip)
- exact2h shard_s/t 2h 4.285 / 1h 4.271
- hostiles in owned-room room_stats since last: 0 (invader is in remote W47N7)

## Labs / minerals / cmd / listener / infra
- Labs KO still on; never unset Memory.ops.labs
- Minerals at 84400218: stor K 220956 O 89600 KO 48036, term K/O 3000 plus small GO/ZH/UH; sites=0
- Memory.cmd stale on at 84224348 by cmd — not taken over
- war_cmd/pulse not running (aborted_by_misaki); commander not holding slots
- Listener single-slot 5:5:1:1 (rot i=1 W47N8 at 20:26:08 / 20:34:08 left 54.9s) — appropriate during the W47N7 incident
- Infra postgres/grafana/listener/dashboard ok; q/DB writers fresh; 40m history backfill succeeded
- r7.on endTime=84402960 by Misaki
- W47 mineral miner=0 why=miner is a known mineral-line gap, not a formal missing critical role

## Code / deploy
- LIVE still 2b5398f7. src clean, deploy.lock absent.
- No code change and no deploy this hour. Invader response is correct (immediate full-budget defender, evac completed). Motion anomalies are known watches, not a new shippable stuck class. Locked policies not touched.
