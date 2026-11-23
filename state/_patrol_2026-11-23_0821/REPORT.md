# Patrol 2026-11-23 08:21 / delivered 08:33 Asia/Hong_Kong (3h cadence)

See USER_LOG.txt for the message to Misaki.

Analysis tip 84431030 2026-11-23 08:29:07 Asia/Hong_Kong
Later room_stats through 84431080 (and live queries through 84431085).
LIVE commit still 2b5398f7. No src change, no deploy.

W47 upgrade: FIRST dual after the 05:38 clearance (exact2h 19.26/30.08=64.0% under AND last800 19.46=64.7% soft). Formal does not fire yet (needs two consecutive). last20-200 designed keep=2 20.00=66.5% must not fire or clear. Do not change keep=2 / no standing third / 15k floor / 40k lock. 3h W47 stor min 18439@05:40 max 28141@08:01, never 40k; last >=40k remains 84406790 40083 ~04:11 Nov 22; upArm=40000 upLatched=0 keep=2 upgCeil=2.

Home formal stays CLEARED (exact2h 23.15/26=89.0%, last800 24.27=93.4% hard). last20-100 14 e/t is the 15k floor (nUp=1 why=floor_bank).
Storage formal stays CLEARED (prev tip 17865 ABOVE; this tip 14146 FIRST under, consec-under=1, does not fire; later 15246@84431050 08:30 then 15030@84431080 ABOVE). Mid-window unders 14465@07:07 and 14799@08:17 recovered.

W47N7 05:00 Invader already told at 05:40; no further incidents after arrive 84428382; live all five host=0 core=0 vis=true, remotes res 2196/1988/2627 SAFE; no rdef live; do not start 指挥官; no Safe Mode. w8threat=w8flee still leftover 84428409; sealPark=1 why=ok / w8day why=done threatSoft=0; 封仓停工 still on.

Official first pass ticks 84427701..84430900 (3200) missing_chunks=6; first-pass realign crashed on a Timescale chunk constraint; tick_s_check live-anchor-best prev_later 4.29750, chunk-safe/full nfix=84922, still_over_45s=0. JP 84430900 at 08:29:54 gt=84431041 all_five_200 inserted=3309. Official+JP through 84431000: W46N8/W47N8/W45N7 3200/3300 (one 100-tick 404 hole each), W45N8 3300/3300, W47N7 2920/3300 (80-tick designed civilian-hold 84428303..84428382 plus three 404 holes).

NEW leftover official 404s folded: W47N7@84429300, W47N8@84429900, W46N8@84430500, and NEW this pass W47N7@84430700 and W47N7@84430800 (confirm+retry2 still 404). Already-told W45N7@84428300 still 404, in-window, not re-told as new.

NEW 盒子休眠 folded: 05:48:18-06:06:20, 06:23:39-06:27:58, 07:00:52-07:06:05, 07:38:49-08:00:34, and NEW 08:18:40-08:22:01 (200s; STATS 84430871..84430939, 69t; official-filled four rooms 69/69, W47N7 39/69 missing 84430871..84430900 due to 84430800 404; listener auto-restart 08:22:04, python 2955920 started 08:22:13, parent 4035476). No new 监听短中断 (08:22:16-08:23:12 56s is slot-rotate leftover after restart).

Motion: no new stuck/oscillation; audit --patrol exit 2 is known deploy-baseline drift vs 2b5398f7, IDENTICAL REGRESSION [deploy] string to the 05:38 patrol, not alert (d); creep_motion --patrol 1h/2h/3h exit 1 known waiting_pickup / target_full / no_task / queue_blocked / waiting_feed. CPU since_last mean 17.10 max 24.52@05:41 bucket min 9860, not (e). Infra ok, peacetime single_slot 5:5:1:1, yield_absent, commander not holding slots.
