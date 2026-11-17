# Patrol 2026-11-17 23:18–23:31 Asia/Hong_Kong (1h peacetime)

## Verdict
FORMAL W47 upgrade alert HOLDS (11th consecutive dual-condition). Home (a) cleared. (b) does not fire (first later dip under 15k only). (c)(d)(e)(f) not formal. Shipped 8daf0494 @84324673 23:30:51.

## Alerts
- W47 exact2h 19.31/30.08=64.2% (prev 64.2%) AND short soft (last20–70 all 20.00=66.5% seated keep=2). last100–300 22.79/23.60/22.79/22.23 overlap box-pause 22:49–23:01 plus delayed handoff — do not use to clear. 1h 18.83=62.6%. Root: locked keep=2 (~20 e/t = 66.5%) PLUS 159t solo handoff from 233t 32,32 cul-de-sac walk. Do not change keep/softCap; no standing third. 40k/500t unlocked (hour max 35128@22:30; 12h best still 270t peak 42880).
- Home exact2h 21.49/26=82.7% (prev 16.86=64.9% first-under cleared); 1h 23.94=92.1%; shorts not soft.
- Home storage: analysis tip 15310 ABOVE (prev 15010 ABOVE). Later first dip (14710, min 14610, live ~14160–14998, floor_bank nUp=1). (b) does not fire. 15k floor stays. 20k/300t unreached (3h max 18170, 6h max 19253).

## Fix shipped
Root cause: c6d43491 yieldPost (POST 34,32 cost 4) correctly kept replacements off the filler post (this walk filler_post=0) and sent them 32,32→33,33. 32,32 is a 2-exit cul-de-sac (33,33 and 33,31) after link 32,33 / terminal 33,32 / ext 32,31. CMV.to ignores creeps until STUCK=3. When 33,33 was occupied (mainly w8hauler84322906), w8upgrader84323984 entered 32,32 and bounced 32,32↔33,31 (pocket=176t, 5 bounce events, walk 233t, first_seat 14,27@84324219; predecessor left 12,25@84324059; solo 159t).

Fix: `fill.yieldHub` used by W47 `go()`. When 33,33 is occupied, 32,32 and 33,33 cost 8 (>POST_COST) so the search takes 34,32→34,33→33,34; a creep already in the pocket leaves via 33,31. Occupancy is not painted into cached `move.matrix` (stale across ticks). `yieldPost` itself unchanged. C.SPAWN stays [15,18]. Deploy 8daf0494 tick 84324673 23:30:51. Next replacement walk will verify.

## Energy / rooms
- Home RCL7 70.68% p=7729081 later 7730377. W47 41.27% p=4513005 later 4514341 stor 31740.
- Remotes all SAFE, reserved, 0 cores / hostiles. W45N8 ~2372, W45N7 ~1892, W47N7 ~2904 (r7.on until 84327525).
- threatSoft still in WINDOW until ~84325127; w8guard at 29,5.
- reserve7 gap 180t 22:25–22:39 then reserve784324023; live ttl was 8 at 23:23. Not formal (c) (listed critical roles have no zero_runs).
- Labs KO held; actGaps=homeStor. KO ~9636+400+645. sma=6 both, never activated. Memory.cmd stale, not touched.

## Motion / CPU
- creep_audit --patrol exit 2: known metric family vs c6d43491, not formal (d).
- creep_motion 1h/2h exit 1: known waiting_* / parked_threat, not new stuck after last deploy.
- CPU since_last mean 17.86 max 24.59@22:32 bucket min 9999.

## Infra
- services.sh all ok. Listener single-slot 5:5:1:1, restarted 23:18:22 after box pause, at 23:31:43 W46N8 left 119.9s. No yield file. Commander not holding.
- DB fresh: room_stats/creep_ticks tip 84324680 23:31:25.
- Backfill 84323801–84324500 inserted=4243 already_in_db=21352; W47N8@84324300 still 404 after retry2 (74t hole 84324301–84324374); others 700/700. tick_s later-mean-robust 4.72696 nfix=7513.
- Box pauses: 22:49:11–23:01:18; 23:15:58–23:18:18; short 84323970–84324000.
