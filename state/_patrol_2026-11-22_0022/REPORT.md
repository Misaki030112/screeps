# Patrol report 2026-11-22 00:35 Asia/Hong_Kong

Folder: `state/_patrol_2026-11-22_0022`. Started 00:24:55 CST. Analysis tip **84403680** (00:32:08, stor 15460/25234, p=9341827/6058316). Later room_stats **84403710** (00:34:17, stor 15760/25234, p=9342201/6058916). Later live 84403712 stor Game 15370/25234, nUp=1 why=remote_pause, w8up=2 keep=2 upLatched=0, sealPark=1 why=ok, threatSoft=0. LIVE commit still **2b5398f7**. No src change, no deploy.

## Alerts

**(a) ALERT FORMAL W47 upgrade HOLDS — thirty-third consecutive dual after the 12:25 clearance.**
- exact2h **19.35/30.08=64.3%** under (prev 19.43=64.6%) AND last800 **19.57=65.1%** still soft (prev 19.18=63.8%).
- last20–70 designed keep=2 **20.00=66.5%** must not clear.
- last100 20.30=67.5% still under; last140–200 21.20=70.5% and last300 21.53=71.6% just touch 70% and must not clear.
- last500 19.27=64.1%; 1h 19.59=65.1%; last1500 19.19=63.8%.
- Do not change keep=2 / no standing third / 15k floor / 40k lock. 40k/500t still unlocked (3h max **32035@84402750** 23:25:04; previous 34649@84400340 aged out of 3h). This-hour max 32035@84402790 min 24228@84403620 later 25234.
- One STATS sample at 84403260 (00:01:24) counted w8up=3, then 2 again by 84403360; live keep=2 w8up=2 — replacement overlap, not a standing third.

**Home formal stays CLEARED.** exact2h **22.48/26=86.5%** well above (prev 24.14=92.8%). last800 **19.52=75.1%** and 1h **19.31=74.3%** still above 70% (softer than prev 26.18 / 25.61 because nUp=1 from floor then remote_pause). last20–140 very soft (6.10–12.69) after the 00:11 freeze / nUp=1; last300 20.95=80.6% and last500 22.86=87.9% hard. Short softness does not fire.

**(b) Storage formal stays CLEARED** (last patrol ended ABOVE ~1.53–1.58万; this-hour dip recovered, not two consecutive unders).
- Already-told later unders from the previous patrol (after LAST_TIP but already reported at 23:35): 14406@84402820 … min 13706@84402830 recovered 15206@84402860 / 15306@84402870 / 15808@84402880.
- NEW this hour after the 00:11 freeze: 14960@84403550 (00:22:42) recovered 15060@84403560; second dip min **14360@84403570** (00:24:09), 14460–14960 climbing, recovered **15060@84403640** (00:29:13); tip 15460@84403680; later 15560@84403690 / 15660@84403700 / **15760@84403710**; live Game 15370@84403712 / upgFeed 15760. All later/live ABOVE.
- nUp=2 at 84403130 stor 18110, then nUp=1 from 84403590 stor 14560; live why=**remote_pause** (W45N7 DEFEND), upBank=1. Do not change 15k floor.
- 20k/300t unlocked: 3h max **18446** (best>=20k tick-span=0).

**(c)** Owned-room critical roles present: miner=2, queen=2, w8filler=2, w8miner=2. No formal. Remote reserver gap: reserver84402511 last in W45N7 at 84403122 (6,39 hits 400) before the core; reserver84402925 last in W45N8 at 84403536; live role count has no reserver (only reserve7=1). Reservations still 2291 / 1239 / 2434. W45N7 reserver deferral during DEFEND is expected. Not formal (c).

**(d)** Motion no new stuck/oscillation class. audit rc=2 known REGRESSION [deploy] vs already-live 2b5398f7, not a new stuck, not formal (d). motion rc=1 known watches (waiting_pickup / target_full / queue_blocked / waiting_feed / no_task / parked_threat for the designed north-hold until the guard aged out).

**(e)** CPU 1h mean 17.25 max **27.42@84402920** (23:37:13) bucket full. 2h mean 17.07 max 27.42. Not near drain.

**(f)** Infra OK; writers fresh after the just-ended 00:11 freeze was official-filled.

## W47 threat window expiry + W45N7 Invader Core

- Local W47 stamp 84401627 (~22:04), window 1500, expired ~84403127 (~23:52) as predicted.
- Live later: threatSoft=0, softCap2=0, bankWhy=ready, softLeft=0, sealPark=**1** why=**ok** (no longer "threat"). w8threat/w8flee/w8inv stamps still 84401627. Do not force-unseal locked policy. Do not start 指挥官. No Safe Mode (sma=6 both rooms).
- w8guard84401622 parked 29,5 hitsMax 4100 never damaged through 84403500; absent from official 84403501–84403600 and from live Game.creeps. parked_threat in the 1h motion window is this designed hold, not a new stuck. Do not replace the guard as a policy change.

- **NEW W45N7 Invader Core** during the 00:11 freeze: inc=84403447, first official-history tick **84403448**, id 6b01c388e4a8197b2c82bf53, level 0, **9,44**, hits 100000/100000, user Invader, strongholdId W45N4_84317679, actionLog reserveController 6,40, effect 1002 endTime 84405144. Still present in official 84403501–84403600 and live later (vis=true, core=1, host=0, res=1239).
- Listener missed the land (box freeze). On restart at 84403550: alert_new why=core, defender requested. Defender **defender84403448** spawned at home (50-part, 5000 hits, spawn cost **5600** full budget, not capped at ~2500); finished spawning / dispatched at 84403598 (INCIDENT DEFEND why=dispatched dur=151, def="out"); Memory arrived **84403668**, mission=core, squad=[defender84403448]. Later vis W45N7 host=0 core=1. rminer84402946 fled north full-health 84403490 into W45N8 then home — designed flee, not a kill.
- W45N7 pauseStart=84403447; home nUp=1 why=remote_pause. W45N8 and W47N7 stay SAFE (res later 2291 / 2434). Do not start 指挥官. No Safe Mode. No code change this hour — this is the designed remote-core response.

## Remotes (later live 84403714)

| room  | vis | state  | res  | host | core |
|-------|-----|--------|------|------|------|
| W45N8 | yes | SAFE   | 2291 | 0    | 0    |
| W45N7 | yes | DEFEND | 1239 | 0    | 1    |
| W47N7 | yes | SAFE   | 2434 | 0    | 0    |

Early live (slot on W46N8) could not see W45N7; later snapshot after rotate/defender arrival has vis on all three.

## Backfill

- First pass (already running at patrol start): `history_backfill.py --minutes 40 --rooms W46N8,W47N8,W45N8,W45N7,W47N7 --compare`
- game.time=84403584 published_bases=84402800..84403400; reconstructed **84402801..84403500 (700)**; first pass **35/35** official GETs 200, missing_chunks=0; tick_s=**4.321**; already_in_db=17800 would_insert/inserted=**7205**; overlap compared=16976 match=15885 differ=1091 (store/energy diffs around 84403101, freeze edge; ts_realigned=0).
- Per first-pass db: W46N8/W47N8/W45N8/W47N7 700/700; W45N7 690/700 empty-no-creep 84403491–84403500 (rminer had just left; official chunk 200).
- confirm + retry2 skipped (no 404 targets). **NEW leftover official 404s: none.**
- Just-published **84403500** at 00:29:18 Asia/Hong_Kong gt=84403641 (threshold 84403640): all_five_200, inserted=**3031** (W46N8 748, W47N8 1553, W45N8 321, W45N7 0 empty-no-creep 100 official ticks, W47N7 409). Post-JP official 84402801..84403600: four rooms 800/800; W45N7 690/800 empty 84403491–84403600.
- Unpublished latest chunk 84403600 (ticks 84403601..) is expected lag.

Aged-out already-told leftovers (do not re-tell): W45N7@84400300, W45N7@84400400, W47N8@84400100 and older.

## Box freezes / short WS (verified this run)

Must tell (not in the 23:35 USER_LOG):

1. **NEW 盒子休眠 23:53:42–23:57:33** (222s, already healed). STATS hole 84403151..84403209 (**59t**). Official-filled all five **59/59**. Listener auto-restart 23:57:36, python 2151688 started 23:57:45. Matches the 00:08 half-hour note; re-verified.
2. **NEW 盒子休眠 2026-11-22 00:11:07–00:22:22** (671s, already healed). STATS hole **84403391..84403549 (159t)** (room_stats cannot be official-filled; last STATS 84403390@00:11:02, next 84403550@00:22:42). Official creep_ticks after this run's backfill + just-published: W46N8/W47N8/W45N8/W47N7 **159/159**; W45N7 **100/159** with empty-no-creep 84403491–84403549 (workers already fled; official chunks 200). Listener auto-restart 00:22:25, python **2159379** started 00:22:35. Current writers fresh.

No new short WS gaps 3–59s after 23:35 (console 3–59s list empty; 120s/600s silences are slot-rotate announcements). Console silences 23:50:43→23:57:47 and 00:08:40→00:22:37 contain the two box freezes.

Already-told, omitted: 盒子休眠 23:20:38–23:24:23 and 22:49:18–22:59:56 (and older 22:14 / 21:42); leftover official 404s W45N7@84400300 / W45N7@84400400 / W47N8@84400100 and older.

## Harvest / CPU / labs

- Home 1h measured upgrade 19.38 e/t; income A 10.0 / B 9.94 / R **8.62** (R a bit better vs last 1h 7.72). 2h upgrade 22.53; A/B 9.97, R 8.55 (vs last 2h 8.34).
- W47 1h upgrade 19.58 e/t; src_A 0.0 known link artifact; B 9.42; R1 6.57; R2 **3.39** softer vs last 1h 8.68/9.90. 2h upgrade 19.31; A 0.0; B 9.6; R1 7.68; R2 6.30.
- CPU 1h mean 17.25 max 27.42@84402920 bucket 10000. Labs KO still on (mode=KO, why=active). Never unset Memory.ops.labs. Mineral: storage K 219356 / O 88800 / KO 49636 at live 84403651; later labReady k 222356 / o 89400 / ko 560 in lab. sites=0. Memory.cmd standing peacetime object only (`on:1, c:{}`); no takeover.
- Home p later 9342201 = 85.43% of 10,935,000; W47 6058916 = 55.41%. ttd 149995/150000. sma=6 both. reserve7 on, endTime 84406110.

## Infra / listener

- services.sh + grafana_check OK at start; DB accepting; rechecked at 00:34 db ok, room_stats lag ~5s.
- Peacetime single-slot rotate W46N8:W47N8:W45N8:W45N7 = 5:5:1:1. No war_cmd / war_listen / war_pulse. Current python listener **2159379** (started 00:22:35). At analysis start slot was W46N8; later rot i=1 room **W47N8** left~345s at 00:34:21.
- Box sleep is a known platform limit, not a listener bug. Both freezes self-healed.

## Code / deploy

- LIVE still the already-live 2026-11-19 02:28 code (2b5398f7). src clean, deploy.lock absent. room_stats commit=2b5398f7 at tip and later.
- No code change and no deploy this hour. W45N7 core is handled by the designed full-budget defender path. Home storage dips recovered after the designed 15k floor and remote_pause. W47 threatSoft expiry left sealPark=1 why=ok; do not force-unseal. Motion anomalies are known watches / known deploy-regression, not a new shippable stuck class. Locked policies not touched.
