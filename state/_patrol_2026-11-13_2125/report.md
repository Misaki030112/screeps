# 1h peacetime patrol 2026-11-13 21:25 Asia/Hong_Kong

LIVE 4ff78b4 (deploy@84239560 13:26). No src/deploy this hour.

## Alerts
FORMAL (a) holds: home exact2h 12.41/26=47.7% (prev 13.56=52.2%) is 28th consecutive <70%, short also soft (post-thaw last20–30 all 14.00=53.8% exact span; last70–300 at analysis tip only span=30 because of the 21:06–21:26 freeze; using pre-gap sample 84245810→tip 12.77 e/t also soft; 1h 11.30=43.5%). nUp=1 floor_bank almost all hour, leftover nUp=2 only 84245290–84245330 20:27–20:31 from last hour's designed handoff then uf still why=floor_bank work=14. 1h dip vs designed 14 is ctl link energy sitting at 0 from ~84245360 through the under-15k period (upgrader84245253 waiting_feed 143); after stor recrossed and ctl refilled (1912 at 84246090 21:26) short window is back to 14.
W47 exact2h 0/30.08 (30th), progress 3150854, keep=1 (minBuild; threatSoft=0), do not revert.
Home stor analysis tip 15398 ABOVE consec-under=0 RESET (prev tip 9082 UNDER consec-under=1 FIRST; formal (b) does not stand). Recrossed over15k at first post-thaw sample 84246090 21:26:46 stor=15548 (prev sample 14282@84245810 21:06). since-last min=8532@84245340 20:31 max=15548@84246090 under15k 34/38=89.5%; later live 15448@84246124 / 15348@84246140 / 15548@84246160 21:31 still ABOVE.
20k/300t not hit (3h max 17149, best>=20k span=0).
No formal (b)/(c)/(d)/(e)/(f).

## Energy / buildings
Authorized sites progressed: W47 lab 28,37 31169→49319, 27,40 3542→3662 (look 3692), 28,38 still 0. Home lab 33,22 9452→12456, 34,20 still 4303 (no progress this hour, watch), labsN=4 (34,23 structure hits 500). minCont 37,44 still 0/5000. Planned roads 37,42 and 36,43 still 0/300; new roads 17,47 and 31,35 appeared at 0/300. siteRem 120979→103459, roadCrit 39→34 (improved).
Biggest gaps: home upgrade capped at 14 e/t by 15k floor, plus this hour ctl-link/feed starvation while stor was low (1h 11.30 vs 14); W47 upgrade 0 by authorized minBuild. Home 2h actual income A/B ~9.99 / R 7.88; model flow nets R 6.86 / W45N7 4.54. W47 2h R1/R2 7.53/6.98 vs ~9.5 (improved vs last hour 4.63/4.71), 1h 7.91/7.78, same known watch, not shipped.

## Remotes / motion / defence
W45N8/W45N7/W47N7 vis res 2025/2468/2839 user Misaki cores0 host0, live stats SAFE (W45N7/W47N7 why=killed leftover). No hostiles and incidents=0 this hour.
Leftover home defender84244890 (18RA/24M/6H 4800 hits, ~5400e) still alive, looping W45N8↔W45N7 then lingering in W45N8 (live 25,41 ttl 403 hits 4800, motion queue_blocked), designed no recycle, should age in ~30 min, not shipped.
reserver84245211 aged 84245822 at W45N8 7,37 designed after refresh; reserver84245221 aged 84245832 at W45N7 6,39 designed; replacement reserver84245662 on W45N7 7,41 ttl 139. W45N8 currently has no live reserver, reservation 2025 still Misaki, spawn waits, home reserver count never 0, not (c).
reserve784245434 spawned 84245435, last at W47N7 station 39,27 in backfill through 84246000, aged designed around ~84246035 (~600t CLAIM). r7 endTime 84247933→84248975 left≈2841>2500, no live reserve7 at tip, spawn waits, early zero_run 140t before spawn is designed, report not formal (c).
audit --patrol exit 2 is same known deploy-window metric shift vs 4ff78b4 (hauler waiting_pickup, queen target_full, miner trip, wbuilder cpu), motion --patrol exit 1 waiting_pickup/target_full/no_task/waiting_feed/queue_blocked; w8filler ABA is known target_full hub weave, hauler84244460 empty waiting_pickup same known, defender leftover queue_blocked expected, upgrader waiting_feed 143 explained by ctl=0 while stor was low (not a new stuck/oscillation after last deploy), not shipped.

## Infra
Two box freezes this hour, both self-healed: 20:43:38–20:57:30 827s room_stats 200t/875s 84245500–84245700, listener restart 20:57:33; 21:06:33–21:25:57 1159s room_stats 280t/1227s 84245810–84246090, listener restart 21:26:01. Peacetime single-slot 5:5:1:1 (yield absent, rot i=0 W46N8 at 21:31:22 left~157s). Memory.cmd.on=1 at=84224348 stale c={} s={}, commander not live, not touched, not reclaimed. war_cmd/pulse stopped NO_WAR_PROCS.
services.sh all ok postgres/views/grafana200/listener/dashboard200 (dashboard :8787); grafana_check 20/20; q.py live OK (skipped known-bad lab/min/soft2 syntax, lab2/min2/opsRem/vis landed); DB writers fresh (room_stats lag ~15s tip 84246120, later 84246160; creep_ticks few seconds).
40m backfill game.time=84246083 published 84245300–84245900 ticks 84245301–84246000 (700) inserted=10131 already_in_db=15201 ts_realigned=1304 tick_s=4.479 missing_chunks=0; all 35 official chunks HTTP 200 100/100; W46N8/W47N8/W45N8/W45N7/W47N7 all 700/700. Unpublished latest ~100t after 84246000 expected (hour-window missing 84246001–tip; W46N8 live listener filled from ~84246083 while rotated on home). Leftover official 404s outside this window unchanged (W47N8@84243700, W47N8@84243100, W45N8@84242900, 0 live ticks).
CPU 1h avg 17.52 max 24.19@84245450 20:39 p95 20.43 bkt min 9997 now 10000, 2h avg 17.37 max 24.19, not (e). Later sample cpu 22.3@84246160 bkt 10000.
Labs stay OFF (labReady actOk=1 actGaps="" why=ready homeStor 15298, do not enable, do not re-ask). sma 6/6 ttd=150000/127341 not activated.
minerals hsO=17324 termO=126976 termK=151080 W47 termE=1338 termK=56 wsK=64; min line why=minCont (site 37,44 still 0/5000), flipReady=0 flipGaps=already.
Ledger ~2.16h (1762t) home up 10.68 (undercount) spawn net 17.66 build 5.55; W47 up 0.00 spawn net 13.45 build 23.71.
HOME W46N8 RCL7 57.45% (p6282652 stor15398@84246120 21:29 HKT; later p6283212 stor15548@84246160 21:31 still ABOVE) live uf why=floor_bank nUp=1 tUp=1 work=14 surplus=+448 floor=15000 allowExtra=20000.
W47 stor min 4367@21:06 max 9959@20:39 live 5801 later 5101 keep=1 phase=minBuild bankWhy=minBuild leanBank=1 threatSoft=0 sealPark on sealMinE=25000 hubLink=1 feedOk=1 upLatched=0.
no layout change shipped; no new deploy.

## USER_LOG_ZH
【巡检 21:25 Asia/Hong_Kong】警报仍在：本家近 2 小时升级 12.41/26（47.7%），已是连续第 28 次低于理想的 70%，短窗也偏软（解冻后 last20–30 都是 14 e/t=53.8%，1 小时 11.30=43.5%）；几乎整小时都只有 1 个升级工卡在 15k 地板，仅上一轮交接尾巴 20:27–20:31 短暂为 2 个。本小时 1 小时升级偏软，主要是仓库还在 15k 以下时控制器链路大部分时间为空，升级工有 143 tick 在等喂；大约 21:26 仓库回到 15k 以上、链路重新有能量后，短窗已回到 14 e/t。W47 近 2 小时仍是 0/30.08，进度钉在 3150854，已连续第 30 次，keep=1 不要改——授权工地还在推进：W47 实验室 28,37 从 31169 做到 49319，27,40 3542→3662，28,38 仍为 0；本家实验室 33,22 9452→12456，34,20 仍停在 4303；矿容器 37,44 仍是 0/5000。本家仓库分析点 15398，已经回到 15k 以上（上一轮是 9082，连续不足复位），仓储警报不成立；本小时最低 8532，约 21:26 解冻时看到已回到 15548，到 21:31 仍是 15548。外矿 W45N8/W45N7/W47N7 现在都安全，视野预订 2025/2468/2839，核心和敌人均为 0。上一轮留下的远程防御者还在 W45N8 一带徘徊，ttl 约 403，按设计不回收，大约半小时后会自然老化。预定还健康，没有缺关键角色。CPU 1 小时均 17.52、峰值 24.19，bucket 满。监听在两次箱体休眠（20:43–20:57、21:06–21:26）后都自己恢复了，40 分钟官方历史已补完，本窗口没有缺失块；更早的 W47N8@84243700 等官方 404 还在。实验室保持关闭，没有改代码、没有新部署。
