# W45N7 远程矿（2026-10-16 14:39 Misaki 批准开工）

规划：`/workspace/w45n7_ops_plan_cn.md`（P0–P4 已上线，P5 修路等 RCL6 后、每期先问 Misaki）。

## 配置（`src/managers/remote.js` CFG.W45N7）
- 路线：W46N8 (49,21) → W45N8 → 南口 (21,49) → W45N7 (21,0) → container。`route()`/`exitTile()` 通用多跳。
- 能量源 (21,16) 只有两个空邻格：(21,15) = **我们的 container**；(22,15) = BustJetter 的 container 工地，**永不踩、不碰**。
  `utils/move` 的 cost matrix 把所有他人工地设为 255；defender 的 moveTo 用 `move.foreignSites`，kite 也跳过 `avoid` 格。
- 预定者 2CLAIM2MOVE（只在 avail≥1300 时出，CLAIM1 走 150 格基本白跑），提前量 lead 140。
- 矿工 6W1C3M：自己放工地、自己修 container，之后按 W45N8 规则补修到 100k。
- 搬运 8C8M ×6：container 修到 ≥60% 前不出；未修好前出搬运还需 storage ≥1300（启动期给防守兵留能量）；
  两次出生至少间隔 60 tick（`rhGap`），寿命错开。
- 视野兜底：无视野 >100 tick 且无任何 W45N7 creep 时，出 1 MOVE 侦察兵 `rscout` 停在 (19,12)。
- 威胁 FSM：W45N8 作为途经房间也纳入玩家检测；W45N7 readyTimeout 250 / defendTimeout 650。

## 防守兵（`src/roles/remote.js` defender）
- 打完不回收：`Memory.defense.remotePatrol`（默认开）时在 W45N8 南口 (24,43) ↔ W45N7 (20,12) ↔ W45N8 (10,8) 巡逻到寿命结束；
  另一外矿进入 THREAT 时 FSM 直接接管巡逻兵（TTL>300），不再新造。
- 目标：`utils/focus.pickDef` 净伤害，奶妈优先；3 个以上在 2 格内用 rangedMassAttack；快死的目标坚持打。
- 走位：近战保持 3 格风筝（避沼泽、不来回掉头），纯远程直接压到 3 格。
- 打不过（`focus.canWin` 判负）：`threat.request2` 申请第二个防守兵，先退到集合点等队友再一起上。
- 只打 NPC（owner Invader），不打玩家；**Invader core 用近战 buster 打掉**（deploy 46f1804 / #9；不再 WAIT core）。

## 回滚开关（控制台，无需部署）
- `Memory.remotes = Memory.remotes || {}; Memory.remotes.W45N7 = { off: true }` → 不再出生，现有 creep 回家干活。
- `Memory.defense.remotePatrol = false` → 防守兵恢复打完回收。

## 监控
`python3 tools/w45n7_watch.py`：预定、container 工地进度、W45N7 creep 位置、spawn、错误。

## 02:4x (2026-10-22) rhauler birth spacing
5 rhaulers, 1500 TTL -> ideal spacing 300t. Fixed `rhGap: 60` let post-raid respawns stay bunched (TTLs 955/895/835/752/684 at t83789510), giving a ~4k e spawn burst every lifetime and a home storage floor dip. `rhGapSteady: 240` (spawn.js remoteSpawn) applies when <=1 hauler is missing; >=2 missing falls back to 60 for fast refill. Expected to converge within one lifetime (~1500t, ~1.8 h).


## 05:4x (2026-10-30) post-core reclaim — Invader reservation + attackController

**Live after core kill (t~83949840, ~05:40 Asia/Hong_Kong):** threat `SAFE why=killed` since 83948805; **Invader reservation still ~1.4k ticks**; container gone (`cont=null`, sites 0); rminer on stand harvest → **ERR_NOT_OWNER (-1)**; 2CLAIM reserver sat adjacent and did nothing (`never attackController`).

**Also present:** abandoned `fhl` spawn at 13,10 (5k/5k). Far from source 21,16 — **ignore** (not ours, not Invader; dismantling a player structure needs Misaki). Neighbor scan shows `res:Invader`, combat 0.

**Findings:**
1. Screeps docs / wiki: lesser Invader cores reserve with priority; after the core dies the **reservation timer still decays at 1/tick**. Harvest stays blocked until it hits 0 (or is attacked).
2. `attackController`: −1 reservation tick per CLAIM part per tick (plus natural −1). One 2CLAIM reserver → ~3/tick clear (~460 t from 1.4k ≈ **~30–35 min** Asia/Hong_Kong vs ~1.6 h wait-out). Two adjacent → faster. Energy already spent on the bodies.
3. Overmind `ReservingOverlord` only `Tasks.reserve` / sign — no attackController on foreign res. TooAngel / conquest bots do attackController when reclaiming. Our **reserve7 (W47N7)** correctly keeps `NEVER attackController` (BustJetter neighbour). Home remotes may clear **Invader only**.
4. Container: rminer rebuilds once we own the reservation again (site at 21,15; avoid BustJetter 22,15). Haulers stay gated on container ≥60%.

**Shipped:** `reserverAct` — `attackInvader` when `reservation.username === 'Invader'`, else `wait` on any other foreign (players), `reserve` when ours/none. `tests/reserver_invader.js`. reserve7 unchanged.

**Patrol watch:** W45N7 Invader `ticksToEnd` falling ≥2–3/tick while a reserver is adjacent; harvest OK after 0; container site then hits; delivered resumes ~10 e/t. Kill switch: restore the old early-return on foreign reservation in `roles/remote.js`.
