# 矿物线 + 强化 + 城防路线图（2026-10-29 12:4x；14:4x boost；17:4x fundSpend；23:4x fortify；08:4x RCL7 hold 300k；11:4x post-300k exit；14:4x soft ramp 100k；20:4x day-of 不预存；23:4x lean KO 脚手架；**08:4x leanBank→stor20k**；**11:4x w8mminer+haul**；**02:4x leanBank hysteresis+soft-cap**；**05:4x soft-cap survives gate**；**08:4x hold-band sink→stor20k**）

Live refresh **08:4x UTC+8 2026-11-01** tick ~83995200。**不自动交易、不开 safe mode。**
home 墙 **HOLD 300k** stor~17.3–17.9k ABOVE；殖民地 **RCL7** prog~120k/10.9M；soft **COMPLETE**；day-crit+missExt0 **DONE**；leanBank **hold** stor~16.7k bankLeft~3.3k（soft-cap≤2）；`flipReady=0` **仅** `stor20k`（homeStor~18k 已绿；04:57 提案 stale）。remotes 全 SAFE。**08:4x** hold-band sink 把 15–20k 段盈余送进 storage。仍 **propose-only** 等 flipReady+她点头。seal 300k 不变。

## 0. 现状（实测）

### W46N8 home RCL7
| 项 | 值 |
|---|---|
| 进度 | ~546k / 10.9M（23:50） |
| 矿物 | **O** @40,24 余 **10136**（正在采）；extractor cd 4；容器 41,24 |
| 库存 | storage O **17324** + terminal O **112476** ≈ **129.8k O**；另有战利品 GO127 KO32 ZH38 UH15 |
| terminal | 有，能量 **0**；credits **0** |
| labs | **3**（34,22 / 33,21 / 35,21），空；**23:4x 已规划 lab 位 rampart**（部署后落点；此前裸 500 hits）；`Memory.ops.labs` **未设** → dormant |
| factory | **0**（`plan.RCL7_INDUSTRY=false`） |
| spawns / towers | Spawn1+Spawn3；**3 塔**能量 ~900–950 |
| 墙 | 41 面墙 min **174401**（STEPS[7]=**300k**→**1M**；fundSpend fund~49.3k；ETA ~12–30 h）；structure ramp min ~345k（核心 ~1M） |
| 墙资金 | fund ~**49.3k** / 50k 封顶；`reserveE=15000`；storage ~15k 振荡 → fundSpend 用 FLOOR 5k 继续推墙 |
| mminer | 1 只在采；`mineralCap` **未设** |

### W47N8 colony RCL6
| 项 | 值 |
|---|---|
| 进度 | **2.791M / 3.645M**（余 ~854k；6h ~23 e/t → ETA RCL7 ~**49 h ≈ 11-01**） |
| 矿物 | **K** **35000** @37,45 **未采**；extractor **已有**（Misaki 自有，layout 门控后未拆） |
| terminal / labs | **无**（`config.RCL6_MINERALS=false`，正确） |
| storage | ~**2.4k** energy |
| 城防 | 墙 11 面 min **300001**；北门 GATE@29,3 **300301**（巡逻曾见 "~20k" 为旧 `GATE_TOWER=20k` 地板；14:4x 已抬到 100k）；塔 2；Spawn2 only |
| ETA RCL7 | ~23 e/t → ~**11-01**（~49 h）；ideal ~30 → ~33 h |

### 代码/开关
- `plan.RCL6_MINERALS=true`（home 矿物基建已齐）；`plan.RCL7_INDUSTRY=false`（factory+labs4–6 不落点）
- `w47n8.config.RCL6_MINERALS=false` / `RCL6_LABS=false` / `HUB_LINK=false`（23:4x lean KO）
- `managers/labs.js`：反应 + `task()` 已有；**carrier 未接**（本 PR 接 hauler，仍需 `Memory.ops.labs`）
- **无** `boostCreep` / 战斗预强化 spawn 代码
- `Memory.defense.remoteDefender=true`（#1 已验 W47N7）
- 邻居：BustJetter W47N9 / Evans W48N8 当前 **无视野**；外矿 SAFE；W45N7 残留他户 spawn `fhl`@13,10（非 Invader creep）

---

## 1. 矿物 / 强化分阶段

### 阶段 A · 现在 → W47N8 升 RCL7（优先升级，~1–2 天）
**目标：** 殖民地 RCL7；home 不抢能量。
> **11:4x 能量闸：** home 墙未到 300k / fundSpend 仍开时，不要指望 storage 稳定 ≥15k 去开矿物或强化。墙 hold 后按 `docs/RCL7.md` 11:4x 回收序列：storage→升级→殖民地 RCL7→soft ramp→再矿物。


| 做 | 不做 |
|---|---|
| 保持 home 采 O（或设 `Memory.ops.mineralCap=50000` 省 ~0.9 e/t，库存已远超实验室短期需求） | **不开** W47N8 `RCL6_MINERALS`（lean KO ≈ **110k**；全开 labs 另 +150k，见 §5） |
| 保持 `RCL7_INDUSTRY=false` | 不买矿、不卖 O（credits 0；买卖需你批） |
| labs 代码保持 dormant | 不造 factory / labs4–6（+250k） |

**强化现实卡点：** KO 需要 **K+O**。我们有 O，没有 K 库存。K 来源只有两条：
1. W47N8 采 K（需阶段 B 开矿物线 + 矿物角色）
2. 市场：先卖部分 O 换 credits 再买 K（**需你批准**；当前 O 买单约 18–19 cr，K 买单极差 ~0.9，卖价另查）

Loot 里已有微量 UH/KO/ZH —— 只够试验，不够常备强化。

### 阶段 B · W47N8 刚到 RCL7（先基建后矿物）
> 20:4x（10-29）：`RCL7_INDUSTRY=false`——**不造 factory@35,30（100k）**；day-of 仅 spawn2@33,30 + tower3@22,7 + 10 ext（spur 已齐 → bill≈**50k**）。**20:4x（10-30）：不预存**——保持 upgrade-first，`siteRem≥3k→≤4 builders`；详见 `docs/RCL7.md` 20:4x / `Memory.ops.w8day`。

顺序（能量从紧到松）：
1. **tower3 + spawn2**（~20k）—— 立刻提升殖民地火力与产能
2. 北门 rampart 抬到 ≥100k，seal 墙按 `WALL_TARGET[7]=1M` 慢慢涨（只花盈余）
3. storage 稳住 ≥20k 后，再翻 **`RCL6_MINERALS=true`**（**不开** `RCL6_LABS`）：落 terminal + 矿物容器 37,44 + trunk（extractor 已在）。约 **110k** ≈ **1–1.5 h**；见 §5 lean KO
4. 接 W47N8 mminer（或复用 home 逻辑）采 K → terminal；用 send/transfer 把 K 运回 W46N8（或就地做 KO 若 labs 落在殖民地）

**推荐反应链（基于实际矿种 O+K）：**
- 主：`KO`（RANGED_ATTACK ×2）—— 防御/外矿最划算
- 有 U/H 后再：`UH`（ATTACK ×2）
- T2/T3（KHO2 / XUH2O 等）要 Z/L/U/H + 更多 labs → **阶段 C + RCL7_INDUSTRY**

Console 开反应（有 K 入库后）：`Memory.ops.labs = { W46N8: 'KO' }`  
关：`delete Memory.ops.labs`

### 阶段 C · 有稳定 KO 库存后
1. 给 labs 充能；写 **boost 入口**（建议先：defender / rdef / w8defender 出生或出征前 `lab.boostCreep`）
2. 优先序：**战斗 > 外矿防守 > 升级(UO 需 U) > 建造(LH 需 L/H，市场贵）**
3. 再评估 `RCL7_INDUSTRY=true`（factory + labs4–6，+250k）：仅当 T2 反应或 factory 有代码需求时

### 机会成本粗算
| 选项 | 能量 | 约等于 |
|---|---|---|
| 现在开 W47N8 lean KO（无 labs） | ~110k | 仍拖 RCL7；等 day-of 后再开（§5） |
| 现在开 home RCL7_INDUSTRY | ~250k | home 墙/升级再少半天；且无 factory 代码 |
| 继续采满本轮 O（~10k 余） | ~4k creep 成本量级 | 可忽略；库存已 130k |
| 墙 142k→300k（41 墙） | ~65k | 受 `reserveE` 卡住，见城防 |

---

## 2. 城防 / 加固分阶段（**23:4x hardening**）

### 2.1 深挖结论（相对 Overmind / Screeps docs）
- **Overmind：** RCL7 `barrierHits = 1M`，`fortifyDutyThreshold = 500k`（storage 够才全力抬墙）。我们用 **STEPS + 50k fund + fundSpend FLOOR 5k**；**08:4x** 另加 peacetime `HOLD_STEP_RCL7=300k`（storage≪500k 时不自动开 1M）。
- **软目标矩阵（home live 23:50 → 02:4x 复核）：** spawn/tower/storage/terminal **有** rampart；**3 labs rampart 已落地**（live ~423k，23:4x 规划）。extractor/links/containers 仍无（extractor 在环外，可接受）。
- **W47N8：** seal 墙 + GATE@29,3 均已 **≥300k**。巡逻日志 "~20k GATE" 是 **spawn 位空 rampart 的 `GATE_TOWER=20k` 地板**，不是北门——已纠正。
- **塔覆盖：** home 3 塔足够核心；殖民地 RCL7 当天落 tower3@22,7（北线）。不扩 4 塔直到 RCL8。
- **优先级插入：** lab 盖板（廉价、立刻消除最软点）→ 环墙 300k → 殖民地 RCL7 tower3+spawn2 → 矿物 → 屏障 1M。

### Home W46N8
| 阶段 | 目标 | 备注 |
|---|---|---|
| **现在** | **lab@34,22 / 35,21 / 33,21 落 rampart** | **✅ 23:4x** 写入 `layouts/W46N8` RCL6(+7/8) rampart 列表；`layout.js` 自动落点；塔先抬到 `RAMPART_FLOOR` 5k（storage<reserve 时），有余粮再往 RCL 目标 |
| 并行 | 环墙 min→**300k**（STEPS[7]） | **✅ fundSpend** live；08:50 min **~241k**，fund ~36.5k；ETA **~3–6 h**；**达 300k 后 peacetime hold**（`HOLD_STEP_RCL7`） |
| 稳后 | 全屏障 **1M** | **非自动**：需 `Memory.defense.pushBarrier` 或后续评审；Overmind 等价 `fortifyDutyThreshold=500k` |
| 姿态 | 3 塔满能；SM **永不自动**；remoteDefender on | BustJetter：**defend-only** W47N9 |

**已落地：** 17:4x fundSpend；**23:4x lab rampart 布局**（+ `tests/lab_ramparts.js`）；**02:4x** labs 盖板 live ~423k；`STATIONARY_FILL` 仍 false（`docs/RCL7.md`）。`reserveE=15k` 保留。

### Colony W47N8
| 阶段 | 目标 |
|---|---|
| RCL6 现在 | seal 墙 + GATE **已 ≥300k**（live 确认 GATE 300301）；保持；spawn 位 rampart 目标 `GATE_TOWER` **100k**（14:4x） |
| RCL7 当天 | tower3(22,7) + spawn2(33,30)；`WALL_TARGET`→1M（盈余抬）；factory **OFF** |
| 之后 | hub/spawn/storage/tower rampart 补齐；开矿物线后再给 labs 盖板；仍不主动打 BustJetter |

### 外矿 / 预订
- 已有：home `defender`（预订房敌情）+ W47N7 `rdef`（#1）
- 缺口：无主动观察 W47N9/W48N8（novis）；north_watch 继续；不扩兵种直到有 boost
- 外矿容器被拆时按现有 builder/remote 逻辑重建即可

---

## 3. 代码落地清单（给执行者）

| 优先级 | 改动 | 文件 | 何时 |
|---|---|---|---|
| ✅ 本 PR | 规划文档 + hauler 执行 `labs.task`（dormant） | `docs/MINERAL_DEFENSE_ROADMAP.md`, `src/roles/hauler.js`, `tests/labs_hauler.js` | 现在 |
| 运行时 | `mineralCap=50000`（可选） | Memory | 任意 |
| 运行时 | 降 `reserveE` 修墙 | Memory | 外矿 SAFE 时 |
| RCL7 后 | `w47n8/config.js` `RCL6_MINERALS=true`（**不开** `RCL6_LABS`） | config | storage≥20k + §5 checklist |
| RCL7 后 | W47N8 w8mminer / haul / send（容器站位 **✅ 23:4x** `MINERAL_CONT=[37,44]`） | roles | 与上同步 |
| 有 K 后 | `Memory.ops.labs={W46N8:'KO'}` | Memory | — |
| KO≥900 后 | boostCreep 接线（§4 状态机） | 新 `managers/boost.js` + defender 族 | 围攻结束后 |
| 更晚 | `RCL7_INDUSTRY=true` | `plan.js` | 有 T2/factory 需求 |

**明确不做：** 市场 deal；自动 safe mode；把密钥写进仓。

---

## 4. Boost 管线设计（strategy 14:4x · Overmind/TooAngel + Screeps docs）

**为何现在深挖矿物/强化而不是城防：** 围攻中 `reserveE=15k` + 邻居 HIGH 已锁死修墙预算；改城防代码会抢 spawn/能量。矿物管线可纯文档落地，且 Misaki 已要矿物+强化计划。城防仍按 §2，RCL7/围攻后再推墙。

### 4.1 常量（docs.screeps.com）
| 常量 | 值 | 含义 |
|---|---|---|
| `LAB_BOOST_MINERAL` | **30** | 强化 1 个身体部件消耗的化合物 |
| `LAB_BOOST_ENERGY` | **20** | 同时消耗能量 |
| `LAB_REACTION_AMOUNT` | **5** | 每次反应产出 |
| `REACTION_TIME.KO` | **10** | T1 KO 冷却 → 净产 **0.5 KO/t**（单 output lab） |
| `LAB_MINERAL_CAPACITY` | 3000 | 一满罐 KO ≈ 强化 **100** 个 RA 部件 |
| terminal 邻房 | W46N8↔W47N8 dist **1** | 传 1000 矿 ≈ **33** 能量（几乎免费） |

### 4.2 参考 bot 模式（裁剪到我们 3 lab）
- **Overmind EvolutionChamber：** creep/overlord `requestBoost` → 预留 product lab → 终端网补矿 → `Tasks.getBoosted`；反应队列与 boost 抢 lab 时 **boost 优先预留**。多房间终端网 + 市场买缺矿（我们 credits=0，市场支路关闭）。
- **TooAngel：** 本房矿存到 terminal 高水位（~100–500k），他矿 ~1k 够反应；专用 mineral creep 填 lab；**出生前订 boost，出生后自动去 lab**。
- **我们的裁剪（3 lab，无多房网）：** 同一时刻只做一件事 —— `REACT` 或 `BOOST`，用 `Memory.ops.labsMode` 切换（默认 REACT）。不能像 RCL8 十 lab 那样边产边强化。

### 4.3 推荐状态机（`managers/boost.js` 待写，围攻后再写）
```
Memory.ops.labs = { W46N8: 'KO' }     # 已有：开反应
Memory.ops.labsMode = 'react'|'boost' # 新增：三 lab 互斥
Memory.ops.boost = {                  # 新增：排队
  // creepName: { compound: 'KO', parts: 'ranged_attack' }
}
```
1. **REACT：** 现有 `labs.js`：ins=[33,21],[35,21] 装 K/O，out=34,22 `runReaction`；hauler `labRun` 已接 `task()`。
2. **切 BOOST：** 停反应 → hauler 清空三 lab → 把 KO+能量灌进 **out lab（34,22）**（或任一邻接 spawn 的 lab）→ 目标 creep 站邻格 `lab.boostCreep(creep)`。
3. **谁先强化：** `defender` / `rdef` / `w8defender` 的 **RANGED_ATTACK** 部件（KO ×2）→ 有存量后再考虑 `raid9` RA；**不**强化平民直到 KO 库存 ≥ 一次满编防守（建议门槛 **900 KO** ≈ 30 RA 部件）。
4. **TTL 门槛（Overmind）：** `ticksToLive < 0.2 * lifetime` 则跳过强化，避免浪费。

### 4.4 产量与库存账
| 目标 | KO 需求 | K+O | 反应时间（0.5/t） | 墙钟（~4.3 s/t） |
|---|---|---|---|---|
| 试跑 10 RA | 300 | 300+300 | 600 t | ~43 min |
| 防守门槛 30 RA | 900 | 900+900 | 1800 t | ~2.2 h |
| 满罐 100 RA | 3000 | 3000+3000 | 6000 t | ~7.2 h |

W47N8 本轮 **K 35000** 采完 → 邻房 send 回家 → 可产 **35000 KO**（O 库存 ~130k 足够）。一轮 K 够强化约 **1166** 个 RA 部件，远超近期作战需求。

### 4.5 K 获取路径（无市场）
1. **主路径（推荐，零 credits / lean KO §5）：** 等 W47N8 **RCL7** → tower3+spawn2（~20k）→ storage≥20k → 翻 **`RCL6_MINERALS=true`**（terminal+extractor+矿容器 37,44 + trunk ≈ **105k**；**`RCL6_LABS` 保持 false**）→ w8mminer 采 K → `terminal.send('W46N8', K, n)`（33 e/1k）→ home `Memory.ops.labs={W46N8:'KO'}`。殖民地 3 labs 延后。
2. **市场捷径（需 Misaki 批）：** 卖部分 O 换 credits 再买 K。当前 O 买单 ~18–21、K 买单极差；**不自动 deal**。围攻期不做。
3. **Loot：** terminal 里 UH15/KO32/ZH38/GO127 —— 只够单次试验，不够常备。

### 4.6 与围攻/RCL 的时序（14:41）
| 何时 | 做什么 | 不做 |
|---|---|---|
| **现在（围攻已中止）** | 采 O（无 mineralCap）；home 墙 fundSpend→300k；殖民地冲 RCL7 | 不写 boost 代码、不开 `ops.labs`、不开 W47N8 矿物、不卖矿 |
| W47N8 → RCL7（~10-31/11-01） | 立刻 tower3(22,7)+spawn2；修 GATE ramp≥100k | 仍不开矿物直到 storage≥20k |
| storage 稳住后 | `RCL6_MINERALS=true` + w8mminer；K→home；**不开** `RCL6_LABS` | 不开 `RCL7_INDUSTRY` |
| K≥1000 @ home terminal | `ops.labs={W46N8:'KO'}`；产到 ≥900 | 不切 BOOST 直到门槛 |
| KO≥900 | 实现 `boost.js`；defender 线先强化 | 不强化 upgrader/builder |

### 4.7 代码清单补丁（相对 §3）
| 优先级 | 改动 | 何时 |
|---|---|---|
| 文档 ✅ | 本节 | 14:4x |
| 运行时可选 | `mineralCap=50000`（O 已 ≫ Overmind 25k 过剩线） | 围攻能量紧时由巡逻/父代理设 |
| RCL7+storage | W47N8 矿物线 + send K | 自动按路线，不逐项问 Misaki |
| 有 K | 开 `ops.labs` KO 反应 | Memory |
| KO≥900 | **新建** `src/managers/boost.js` + spawn 后 hook（defender 族）+ 测试 | 单独 PR；围攻结束后 |
| 更晚 | labs4–6 / T2（KHO2 需 OH+H）/ factory | `RCL7_INDUSTRY` |

** fortification（17:4x）：** home 墙经 `fundSpend` 推进 142k→300k（不必降 reserveE）；W47N8 屏障已 300k。矿物/boost 仍不阻塞，等殖民地 RCL7+storage≥20k。

---

## 5. Lean KO 脚手架（strategy **23:4x** · 2026-10-30 ~23:40 Asia/Hong_Kong）

### 5.1 选了什么问题
W47N8 在翻 `RCL6_MINERALS` **之前**，矿物线代码缺口有多大？是否必须同时落殖民地 3 labs？

### 5.2 现状缺口（翻 gate 前）
| 项 | 状态 | 注 |
|---|---|---|
| K 矿物 | @37,45（墙格） | 可走站位仅 **37,44 / 38,44**（plain） |
| extractor | live（Misaki 已放） | layout ORDER 有 `extractor:[[37,45]]` |
| terminal | **未放** | `RCL6_MINERALS=false` |
| 矿物容器 | **未放**（ORDER 原先只有 ctl cont） | **23:4x** 加 `MINERAL_CONT=[37,44]`，随 minOk 落点 |
| MINERAL trunk | roads.MINERAL=`[[36,43],[37,42],[37,44]]` **不在** ROADS 里 | **23:4x** layout 在 minOk 时 `baseRoads.concat(MINERAL)`（修了「翻 gate 也不铺 trunk」的旧 bug） |
| 3 colony labs | ORDER 有；gate 默认关 | **23:4x 拆出 `RCL6_LABS=false`** |
| w8mminer / haul / send | **✅ 11:4x** miner+haul（dormant）；**send 未写** | `w8mminer` + `w8hauler.mineralRun`；`terminal.send` 下一刀 |
| `Memory.ops.w8min` | **✅ 23:4x** | dayObs：gaps=`gate,terminal,extractor,minCont,miner,rcl,stor20k` |

### 5.3 参考（Screeps docs / Overmind / TooAngel）
- **terminal.send** 邻房 range1 ≈ **33 e / 1k** 矿 — K→home 几乎免费（docs.screeps.com Market）。
- **Overmind** `storageBuffer` ~100k 才开工业；我们用更紧的 **colony stor≥20k**（升级优先后的恢复线）。
- **TooAngel** 本房矿进 terminal 高水位、他矿 ~1k 够反应；反应/boost 抢 lab 时 boost 优先 — 我们 3 home labs 已够 T1 KO（§4）。
- 殖民地再造 3 labs ≈ **150k** + 无反应代码 → 纯浪费；**lean KO = 物流到 home，反应留 home**。

### 5.4 成本对比
| 方案 | 结构 | 能量 | 相对 RCL7 后净收 ~20–30 e/t |
|---|---|---|---|
| **Lean KO（推荐）** | terminal 100k + extractor 5k + 矿容器 5k + trunk roads | ≈ **110k** | ~1–1.5 h |
| Full（旧文档 255k） | 上 + 3 labs 150k | ≈ **260k** | ~0.5–1 天 |
| 另：RCL7 day-of | spawn2+tower3+10ext | ≈ **50k**（`w8day.bill`） | 优先于矿物 |

### 5.5 Gate 语义（23:4x）
| Flag | 默认 | 打开后落点 |
|---|---|---|
| `RCL6_MINERALS` | false | terminal + extractor + `MINERAL_CONT` 37,44 + MINERAL trunk |
| `RCL6_LABS` | false | 3 colony labs（ORDER lab[0..2]）；**KO 不需要** |
| `HUB_LINK` | false | hub link 33,34（无关矿物） |
| `RCL7_INDUSTRY` | false | factory / PS / nuker / observer |

### 5.6 翻 `RCL6_MINERALS` 前 checklist（仍 **propose**；不自动翻）
1. W47N8 **RCL7** + tower3 + spawn2 落完（`w8day.why=done`）
2. colony storage **≥20k**（且 home 墙 HOLD 300k、home stor 稳在 ≥15k）
3. **代码：** `w8mminer` 站 37,44 + 把 K 搬进 terminal **✅ 11:4x**；`terminal.send`→W46N8 **✅ 14:4x**（dormant）
4. `Memory.ops.w8min.why` 只剩 `miner`/`stor20k` 类可解缺口
5. **不**开 `RCL6_LABS` / `RCL7_INDUSTRY` / `ops.labs` / `mineralCap`（除非 Misaki 改口）

### 5.7 本轮交付
- config：`MINERAL`/`MINERAL_CONT`/`RCL6_LABS`
- layout：minOk 落矿容器 + concat MINERAL roads；labs 独立 gate
- obs：`Memory.ops.w8min`
- tests：`w47n8_rcl6_gate` lean-on；`w47n8_dayobs` w8min
- **未**翻任何 gate；**未**写 w8mminer；**未**设 mineralCap / ops.labs

### 5.8 leanBank → stor≥20k（08:4x 2026-10-31；**20:4x 修正 arming**）
- **问题：** day-of 完成后 stor 卡在 0.5–3k，自然攒不到 20k（满升级净≈0）。
- **做法：** `leanBank` 默认开（RCL7 + **spawn2+tower3（day-crit）** + stor<20k + `!RCL6_MINERALS`）。**不等 50ext**（20:4x；08:4x 原文「50ext齐」已废）。节流升级（≤1 upgrader、回收多余、idle builder 停车），obs：`w8day.phase/bankLeft/bankEta/leanBank`；`bankEta` 含 `siteRem`。
- **退出：** stor≥20k → `phase=ready`，恢复满升级；cushion 留给 lean KO。
- **仍不自动翻 gate**；§5.6 checklist：w8mminer+haul ✅；send ✅ 14:4x。
- 关闭：`Memory.ops.w8leanBank=false`。详见 `docs/RCL7.md` 08:4x / 20:4x。

### 5.9 w8mminer + haul→terminal（11:4x 2026-10-31 ~11:4x Asia/Hong_Kong）
- **问题：** leanBank 之后翻 gate 仍被「没有采/运代码」挡住（08:4x next open / 23:4x §5.6#3）。
- **做法（Overmind ExtractorOverlord 同构，send 另开）：**
  - `roles.w8mminer`：站 `MINERAL_CONT` 37,44，extractor 冷却外 `harvest`；无 CARRY（掉进容器）。
  - `bodyFor('w8mminer')`：`WORK*n + 3 MOVE`（同 home mminer）；spawn 仅当 `RCL6_MINERALS` + extractor + minCont + K>0 + cont free>400。
  - `w8hauler.mineralRun`：空载时把容器非能量矿（≥500 或近满）搬进 **terminal**（不进 storage）；gate 关时整段 dormant。
  - obs：`w8min.hasCode=1`，`sendOk=0`，gaps 恒含 `send`。
- **未做：** `terminal.send('W46N8', K, n)`；**未翻** `RCL6_MINERALS` / labs / industry。
- **测试：** `tests/w47n8_mminer.js`（body / mineralRun gate / spawn want）；dayobs hasCode/send。

### 5.10 terminal.send K→W46N8（14:4x 2026-10-31 ~14:4x Asia/Hong_Kong）
- **问题：** lean KO 代码缺口只剩跨房 `terminal.send`（11:4x next open / §5.6#3）。
- **参考：** Overmind `TerminalNetwork` — surplus room sends to deficit; `Game.market.calcTransactionCost`; `TERMINAL_MIN_SEND=100`, cooldown 10. TooAngel parks energy in terminal for transfer fees. Adjacent (range 1) ≈ ceil(amt × (1−e^(−1/30))) ≈ 33e/1k.
- **做法（全部 behind `RCL6_MINERALS=false`）：**
  - `mineralSend(room)` in `w47n8/index.js`：每 tick 从 layoutRun 调用；gate 关 → `sendWhy=gate` 立刻返回；gate 开时检查 cooldown / K≥100 / home terminal free / energy≥cost，batch≤5000，`term.send('K', amt, 'W46N8')`。
  - `w8hauler.termFuel`：terminal 有矿等待且 `termE < 1000` 时从 storage 补能量（不抽干 stor<2k）。
  - obs：`w8min.sendOk=1`；`sendWhy` ∈ gate|noTerm|cd|noK|noHome|homeFull|noE|sent|err*；`termE/lastSend/lastAmt/needE/cd`；gaps **不再**恒含 `send`。
- **Home 接收：** `managers/labs` KO 已从 home terminal 抽 K/O — send 落点正确，无需新 receive 代码。
- **未做：** 翻 `RCL6_MINERALS` / labs / industry；不在 live 发矿。
- **测试：** `tests/w47n8_mminer.js`（send gate/noK/noE/sent/cd + termFuel）；`w47n8_dayobs` sendOk=1。

### 5.11 day-of north tower ≥600 / close hubNeedy residual（17:4x 2026-10-31 ~17:4x Asia/Hong_Kong）
- **问题：** day-of 建设期北塔会不会掉到 <600？要不要 filler 在 towerE<500 时忽略 `hubNeedy`？
- **结论：不要改 hubNeedy。** 北塔 24,8 / 22,7 由 `northFeed`（阈值=600）供能，filler 只管 hub 塔。Live towerMinE~860。obs：`w8day.towerHubE/towerNorthE/nf`。
- **翻 gate 时机（仍 propose）：** day-of done + leanBank `phase=ready`（stor≥20k）+ towerMinE 健康。不需要再等 ext 波次单独完成。

### 5.12 leanBank arming vs 50ext（20:4x 2026-10-31 ~20:4x Asia/Hong_Kong）
- **问题：** live spawn2+tower3 DONE、ext~40/50、storE=0，但 `leanBank=0` / `why=dayof` / `bankEta=-1`。§5.8 写「50ext齐」；17:4x 写 bank/flip 只需 day-of=spawn2+tower3。
- **根因：** `leanBank()` 与 `why` 把 `missExt>0`（及 `siteRem`）算进 day-of，和 `dayCrit`（只看 spawn/tower）不一致，把整个 10ext 波次挡在 bank 外；3 upgrader 继续吃净收入 → stor 贴 0。
- **参考：** Overmind UpgradeSite 用 `storageBuffer`~100k 缩放 upgrader（有盈余才猛升）；TooAngel 建设期砍 upgrader。我们 post-daycrit 用更紧的 20k cushion + 显式 throttle，应在 **crit 完成后立刻** 生效，建设与攒库并行。
- **修法：** `leanBank` / `why` / `phase` 只看 day-crit；`missExt`/`siteRem` 仍上报；`bankEta = ceil((bankLeft+siteRem)/20)`。Builders 继续啃站点，多余 upgrader 回收。
- **未做：** 翻任何 gate；不改 home throttle；不改 hubNeedy。
- **测试：** `w47n8_dayobs` mid-ext leanBank；`w47n8_move_bank` 40ext arm。

### 5.13 RCL6_MINERALS flip-ready + post-flip leanBank hold（23:4x 2026-10-31 ~23:4x Asia/Hong_Kong）

**选了什么问题：** leanBank 快结束（missExt0 DONE，bankLeft~6.7k / ~0.4 h）时，§5.6 checklist 是否齐全？翻 gate 后 ~110k terminal+minCont 建设会不会被满升级饿死？

**Live（t~83987300）：**
| 项 | 值 |
|---|---|
| W47N8 | RCL7；missExt**0** siteRem0；storE~13.3k；phase=**bank20** leanBank=1 towerMinE~820 |
| Home | RCL7 ~10.9%；stor~15.5k ABOVE；walls HOLD 300k；O 本轮采空；term O~122k；labs idle |
| Remotes | W45N8/W45N7/W47N7 **SAFE**（W45N7 ep83986359 cleared） |
| w8min.gaps | `gate,terminal,minCont,stor20k`（code hasCode/sendOk=1） |
| CPU | ~12–14 / 20；bucket 10000 — 矿物线 +1 w8mminer 可承受 |

**参考（Overmind / Screeps docs）：**
- Overmind 在 RCL6 **有 extractor 就采**，不要求 stor≥20k；TerminalNetwork 另管跨房。我们更紧：先 bank 20k 再落 terminal（~100k），避免 day-of 后贴零。
- Overmind `storageBuffer`~100k 才猛升工业；我们 20k 只是 lean KO **开工门槛**，不是工业水位。
- 翻 gate 后若 `leanBank` 因 `RCL6_MINERALS` 立刻关掉，stor 被站点抽到 <20k 时**不会再 arm** → 满升级与 ~110k 建设抢能量（TooAngel 建设期砍 upgrader 的反面）。

**结论 / 交付：**
1. **`w8min.flipReady` / `flipGaps` / `homeStor`**：编码 §5.6 propose checklist（daycrit + stor≥20k + towerMinE≥600 + homeStor≥15k；**不含** gate/terminal/minCont — 那些是翻 gate 才落的）。`flipReady=1` 时巡逻应 **WakeParent propose**，**不自动翻**。
2. **`leanMinBuild` + phase=`minBuild`**：gate 开且缺 terminal 或矿容器时 **继续 leanBank**，直到两者落成；之后 phase=`ready`、leanBank off。
3. **仍不开** `RCL6_LABS` / `RCL7_INDUSTRY` / `ops.labs` / 市场。
4. **时机：** bankEta~0.4 h 后 `phase=ready`；若 homeStor≥15k 且 towerMinE≥600 → `flipReady=1` → **propose** 翻。翻后预计 1–1.5 h 建完 lean KO 物流，再采 K→send home。

**测试：** `w47n8_dayobs` flipReady / minBuild / post-complete；move_bank + mminer 回归。

### 5.14 leanBank hysteresis + soft-cap（02:4x 2026-11-01 ~02:4x Asia/Hong_Kong）

**选了什么问题：** leanBank 到 20k 后立刻拉满 3–4 upgrader，浅跌破 20k 就重 arm；紧接着 remote DEFEND 把 cushion 抽干，`bankEta@~20 e/t` 失真，flipReady 反复抖动。

**实测（room_stats t83987300–83989900）：**
| 事件 | tick | stor | w8upg | 备注 |
|---|---|---|---|---|
| up20 / ready | ~83987530 | ≥20k | 4 | phase=ready，满升级 |
| dn20 | ~83988460 | <20k | 4 | 浅跌仍满升级 |
| re-arm | ~83988750 | ~16.4k | 3→0 | leanBank 重开 |
| W47N7 DEFEND | ~83988798 | →1.7k | 0 | mining pause；prog 冻@74778 |

**对照：** Overmind `UpgradeSite.storageBuffer=100k`，只在 surplus 上按 `energyPerBodyUnit` 加 WORK；spawn 条件 `assets > buffer`。我们的 20k cushion 更紧，但不能二进制 thrash。

**修法（SAFE，不翻 gate）：**
1. **`LEAN_ARM=15000` 回滞：** disarm@20k；仅当上一拍 `leanBank=0` 且 stor&lt;15k 才再 arm。15–20k = hold（phase=`ready`，`bankWhy=hold`）。
2. **`LEAN_SOFT=25000` soft-cap：** stor&lt;25k 时 base upgrader ≤2，禁 surplus spawn；`leanBankRecycle` 在非 bank 时收到 ≤2。
3. **obs：** `w8day.{bankArm,bankSoft,bankWhy}`（`ready|hold|bank|threat|minBuild|gate|off`）。threat 下 `bankEta` 仍按 20 e/t，但 why=threat 提示不可信。

**测试：** `w47n8_dayobs` hold/soft-recycle/re-arm；`w47n8_move_bank` hysteresis。

**仍不自动翻 gate。** flipReady 仍要 stor≥20k + homeStor≥15k + towerMinE≥600 + 她点头。

### 5.15 soft-cap must survive RCL6_MINERALS flip（05:4x 2026-11-01 ~05:4x Asia/Hong_Kong）

**选了什么问题：** 02:4x 的 `LEAN_SOFT` soft-cap 在 `!C.RCL6_MINERALS` 守卫下；翻 gate → minBuild 结束后 leanBank 立刻关，若 stor 被 ~110k 站点抽到 ≪25k，会不会再次满升级 thrash？

**Live（t~83992670，Asia/Hong_Kong ~05:48）：**
| 项 | 值 |
|---|---|
| W47N8 | RCL7 prog~90.6k；phase=**ready** leanBank=0 bankWhy=**hold** storE~18k bankLeft~1.8k；towerMinE~880；2 upg soft |
| Home | RCL7 ~11.9%；stor~14.8k thin；upgFeed why=`remote_pause`（W45N7 DEFEND core）；term O~124k；K=0 |
| flipReady | **0** gaps=`stor20k,homeStor`（04:57 曾=1 → 提案 **stale**，勿重复轰炸） |
| Remotes | W45N8 SAFE；W45N7 **DEFEND** core@83992605；W47N7 SAFE |
| Roads | W47 soft hits&lt;50% **134**（维修债，已知）；home walls HOLD 300001 |

**对照 Overmind：** `UpgradeSite.storageBuffer=100k` **与矿物线无关**——assets 不够就不起满 upgrader。我们的 soft-cap 应对齐：门槛更低（25k）但 **不因 gate 关掉**。minBuild 期间 leanBank≤1 已覆盖建设；缺口在 **minBuild 完成后、stor 仍薄** 的窗口。

**修法（SAFE，不翻 gate）：**
1. spawn soft-cap 与 `leanBankRecycle` 去掉 `!C.RCL6_MINERALS` 守卫；stor&lt;LEAN_SOFT 时一律 ≤2 upgrader（leanBank 仍优先 ≤1）。
2. 不改 LEAN_STOR/ARM、不改 flipReady、不改 minBuild。
3. **仍不自动翻 gate**；下次 flipReady=1 再 propose（当前 stale）。

**测试：** `w47n8_dayobs` post-gate soft recycle @stor5k。

### 5.16 hold-band sink → finish stor20k（08:4x 2026-11-01 ~08:4x Asia/Hong_Kong）

**选了什么问题：** soft-cap + hysteresis 之后，为什么 `phase=ready` / `bankWhy=hold` 仍卡在 stor~16–18k（`flipReady` 只差 `stor20k`），而 source cont / drops 里长期趴着 ~6–7k（`w8lo7`~7k）？

**实测（t~83995200，Asia/Hong_Kong ~08:40）：**
| 项 | 值 |
|---|---|
| W47N8 | storE~16.7k bankLeft~3.3k leanBank=0 bankWhy=**hold** soft≤2 upg；towerMinE~960；prog~120k |
| homeStor | ~18.0k **ABOVE** → flipGaps **只剩** `stor20k` |
| loose | `ops.w8lo7`~7.0k + 巡逻 drop~6–7k（source conts） |
| Remotes | W45N8/W45N7/W47N7 **SAFE**；CPU~12–15/20 |
| 3h 趋势 | home upg ~18 e/t stor ABOVE；W47 upg ~12 e/t（soft-cap）；W47 stor 3h avg~17.8k 振荡不破 20k |

**根因：** `w8hauler.sink()` 在 filler buffer 满足后 **永远优先 ctl/hub cont**。soft-cap≤2 时 ctl 常有空位（≥1200 但仍未满）→ 盈余循环喂升级，**永远到不了 storage**。leanBank 只在 &lt;15k 节流；15–20k hold 带靠「少 spawn」不够把已采出的 6–7k 搬进 stor。

**对照：**
- **Overmind** `UpgradeSite.storageBuffer` / LogisticsNetwork：资产默认进 **storage**，upgrader 只吃 surplus；storage 是 cushion 的家。
- **TooAngel**：建设/lean 期砍 upgrader，haul 目标仍是 storage/terminal，不是「永远优先 controller container」。
- 我们的 ctl-first 在 leanBank/满升级期合理，但在 **hold 带** 与 flipReady 目标冲突。

**修法（SAFE，不翻 gate）：**
1. **hold-band sink：** `stor ∈ [LEAN_ARM=15k, LEAN_STOR=20k)` **且** ctl cont ≥1200 → hauler sink 选 **storage**（sticky 在 hold 带内保留）。&lt;15k 仍 ctl-first（leanBank 节流）；≥20k 恢复 ctl-first；ctl&lt;1200 仍喂 ctl。
2. **obs：** `w8day.looseE`（drops + source conts，排除 ctl/hub）方便巡逻对比 bankLeft。
3. **不改** LEAN_*、flipReady、minBuild、gates。

**预期：** 把 ~3.3k shortfall 从已有 loose 里搬进 storage → `flipReady=1`（homeStor 已绿）→ 下次巡逻/策略 **re-propose**（04:57 stale，勿重复轰炸直到真正=1）。

**测试：** `w47n8_filler` sink hold-band；`w47n8_dayobs` looseE；move_bank/mminer 回归。

**仍不自动翻 gate。**

