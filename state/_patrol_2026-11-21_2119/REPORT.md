# Patrol 2026-11-21 21:31 亚洲/香港

Dir: `/workspace/screeps/state/_patrol_2026-11-21_2119`

## Window
- Previous delivered 1h: 20:34, analysis tip 84400300 / later 84400350 / live 84400355
- This analysis tip: **84401080** at 21:25:50 亚洲/香港, stor home 16250 / W47 25711, progress 9283565 / 6007616 (84.90% / 54.94% of 10935000)
- Later room_stats: **84401150** 21:30:53 亚洲/香港 stor 15740 / 24762, progress 9285525 / 6009016
- Live ~21:31 t=84401156..84401158: home stor 15790 / W47 25512, p 9285693 / 6009136, nUp=2, w8up=3 (brief handoff), keep=2, upLatched=0, sealPark=1 why=threat, threatSoft=1, bankWhy=threatSoft, sma=6, ttd=150000/150000, bucket=10000, labs KO still on
- LIVE remains the already-live 2026-11-19 02:28 code (src clean, deploy.lock absent)

## Formal alerts
- **W47 upgrade HOLDS** — thirtieth consecutive dual after 12:25 clearance. exact2h 20.07/30.08=66.7% (prev 19.32=64.2%) still under AND last800 20.52=68.2% still soft. last20–300 20.00=66.5% is designed keep=2 and must not clear. last500 also 20.00=66.5% still soft. 1h 20.49=68.1%. model_w8 2h 20.07 vs 30.03 stor_delta +0.24, 1h 20.5 stor_delta -15.17 (evac/defender spend + threat-seal). Root remains designed keep=2 plus residual threatSoft seal after the Invader. Do not change keep/softCap, no standing third, no 40k unseal.
- **Home formal stays CLEARED.** exact2h 22.34/26=85.9% (prev 18.21=70.0% on the line) is well above 70%, not under; last20–800 hard (~27.4–28 e/t, 105–108%); last800 27.76=106.8%; 1h 27.77=106.8% also hard; last1500 22.30=85.8%. model 2h 22.24 stor_delta -0.10, 1h 27.76 stor_delta -2.30.
- **Storage-floor stays CLEARED.** tip 16250 ABOVE, later 15540–15790 ABOVE (prev tip 19233 later ~19783 ABOVE). since_last under15k=0/57; later min 15540@84401130 21:29:28 still above. nUp=2 throughout this hour after last patrol. 20k/300t unlocked, 3h max 19933@84400370 20:34:47, best>=20k span=0. Do not change 15k floor.
- Locked policy unchanged. 40k/500t still unlocked upLatched=0; no 40k touch this hour (W47 since_last min 25711@tip then later 24511@84401110, max 35349@84400300; 3h max still 38748@84400220 20:24:03). sealPark remains closed why=threat / threatSoft after the W47N7 invader (storE near/under sealMinE 25000). Brief w8up=3 @84400380–84400450 (new w8upgrader84400374 hatch overlap) and again at live 84401157 are handoff, not a standing third.

## W47N7 Invader (RESOLVED this hour; must tell)
- Incident 84400223 20:24:17 THREAT why=solo, episode remote-W47N7-84400223, invOnly=true; last patrol left defender still spawning
- rdef84400224 hatch exactly 84400374 20:35:03 at W47N8 34,29 (as predicted), body 19R25M6H hits=5000 cost 5600 full budget
- Walked to south exit W47N8 18,49 at 84400413 20:37:23; entered W47N7 ~84400414
- Episode ended 84400430 20:39:04 action=remote resumed, severity low; w8threat/w8flee last stored 84400419 (inside the fight window)
- Invader not stored in creep_ticks (official W47N7 evac-empty 84400296..84400496, including combat 84400414..84400496); no second invader name ever appeared. Live and later host=0 core=0 in all five rooms
- Defender never damaged (hits 5000 the whole recorded life). Reappears in DB at 84400497 20:43:27 W47N7 27,21; still in W47N7 at live 84401123 26,15 ttl 750 hits 5000
- Civilians returned 84400598 (w8rminers / w8rhaulers / reserve7). Live two w8rminers working in W47N7
- Reservation recovered/healthy: last vis last patrol 2701, this hour 2911@84401049 then 2848@84401158
- Home remotes W45N8/W45N7 vis SAFE throughout
- Do not start 指挥官. No Safe Mode. sma=6. Not a continuing or new invader ALERT

## Remotes later / live
- W45N8 vis SAFE res=2253 host=0 core=0 at 84401158
- W45N7 vis SAFE res=2359 host=0 core=0
- W47N7 vis SAFE res=2848 host=0 core=0
- Reservers present (2) at later 84401122; reserve7 present at analysis tip, not in the 84401122 role counts (reservation still healthy). Not formal missing-role. Owned critical roles present (miner/rminer/queen/w8filler/upgraders live)

## New freezes / 404s
- **MUST TELL:** NEW 盒子休眠 20:49:04–21:04:03 (895s, already healed; STATS 84400561..84400789, 229t; official-filled all five 229/229; room_stats gap 84400560..84400790 wall ~978s is this freeze; listener auto-restart 21:04:06, python 2082229 started 21:04:16)
- **MUST TELL:** NEW 监听短中断 21:13:29 ping/pong timed out (not a box freeze; no box_pauses row); restart 21:13:33, python 2086972 started 21:13:43 and still running; no extra missing room_stats decile around 84400900..84400950
- **MUST TELL:** leftover official 404 W45N7@84400300 (from quiet 20:45 / 21:18 backfills; this 40m first pass still 404; confirm 21:24:15 gt=84401057, retry2 21:27:55 gt=84401109, late just-pub 21:30:38 gt=84401142 still 404; listener 0/100; hole 100 ticks 84400301..84400400)
- **MUST TELL:** leftover official 404 W45N7@84400400 (from quiet 21:18 backfill; confirm+retry2+late still 404; listener 27/100 84400403..84400429; hole 73 ticks 84400401..84400402 and 84400430..84400500)
- Already told by the 20:34 patrol and not re-told: 盒子休眠 19:52:19–20:02:21, 监听短中断 20:21:38, leftover official 404s W45N8@84399500, W45N7@84399800, W47N8@84400100, and older (19:10:45–19:18:45, 18:47:50–18:58:17, all-five @84399100, W45N8@84399300, etc.). Those three leftovers have aged out of this window start 84400301 and were not retried.
- Official-200 evac empty W47N7 84400301..84400496 (196t; continues last patrol’s 84400296..84400496) is NOT a 404
- After this log is delivered: fold only newer freezes/short WS than 20:49:04–21:04:03 and 21:13:29, and newer leftover official 404s than W45N7@84400300 / W45N7@84400400

## Backfill
- Official history 84400301..84401000 (700, published_bases 84400300..84400900 at game.time=84401037; first pass 33/35 official GETs 200, missing_chunks=2 W45N7@84400300, W45N7@84400400) inserted=6065 already_in_db=18659 tick_s=4.314 ts_realigned=0
- overlap compared=18030 match=17337 differ=693 (same class as the 21:18 halfhour diffs around 84400786–787; not treated as a motion bug)
- Confirm 21:24:15 gt=84401057 still_404 both leftovers inserted=0
- retry2 21:27:55 gt=84401109 still those two 404s inserted=0
- Just-published 84401000 at 21:30:21 gt=84401142 all_five_200=True inserted=27 (W46N8 0, W47N8 0, W45N8 7, W45N7 0, W47N7 20); all five 100/100 in 84401001..84401100
- Late leftover retry at 21:30:38–21:30:39 still_404 the two leftovers inserted=0
- Remaining holes: leftover W45N7@84400300 (empty), leftover W45N7@84400400 (partial listener), W47N7 official-200 evac empty 84400301..84400496, unpublished tail after 84401100

## CPU / motion / harvest
- CPU 1h min 13.76 max 21.7@84400920 21:14:00 mean 16.79 p95 20.11 bucket 10000 n=62; 2h min 13.58 max 22.14@84399600 19:40:01 (already in last patrol’s 2h window) mean 17.12 p95 20.11 bucket 9995 n=131; bucket never drained. No formal CPU.
- audit exit 2 = known REGRESSION [deploy] vs already-live 2026-11-19 02:28 code, not new stuck, not alert (d)
- motion exit 1 = known watches waiting_pickup / target_full / queue_blocked / waiting_feed / no_task / w8hauler circ / w8rminer swamp. rdef84400224 queue_blocked after the kill is the same known class (post-combat linger), not a new stuck. No new stuck/oscillation class.
- Home harvest 2h A/B/R 9.99/9.99/6.94, 1h 10.00/9.98/6.85 (R still the biggest home gap; 1h R improved vs last patrol 6.03)
- W47 src_A 0.0/0.1 is the known link-accounting artifact; src_B 8.14/8.47; 1h R1 0.91 / R2 0.0 is the evac downtime, 2h R1 6.18 / R2 6.62 recovered vs the evac hole — expected, not a new bug
- exact2h shard_s/t 2h 4.297 / 1h 4.314
- hostiles in owned-room room_stats since last: 0 (invader was in remote W47N7 and is gone)

## Labs / minerals / cmd / listener / infra
- Labs KO still on; never unset Memory.ops.labs
- Minerals at 84401045: stor K 220956 O 89600 KO 48036, term K/O 3000 plus small GO/ZH/UH; sites=0; koLab KO 850 / K 1050 / O 1050
- Memory.cmd stale on at 84224348 by cmd — not taken over
- war_cmd/pulse not running (aborted_by_misaki); commander not holding slots; no handoff
- Listener single-slot 5:5:1:1 (rot i=1 W47N8 at 21:31:04 left 445s) — appropriate after the W47N7 incident; python 2086972
- Infra postgres/grafana/listener/dashboard ok; grafana_check OK; q/DB writers fresh; 40m history backfill succeeded
- W47 mineral miner=0 why=miner is a known mineral-line gap, not a formal missing critical role

## Code / deploy
- LIVE still the already-live 2026-11-19 02:28 code. src clean, deploy.lock absent.
- No code change and no deploy this hour. Invader response was correct (immediate full-budget defender, hatch on time, remote resumed, no new wave). Motion anomalies are known watches, not a new shippable stuck class. Locked policies not touched. W47 1h remote harvest dip is evac, not a logic bug.
