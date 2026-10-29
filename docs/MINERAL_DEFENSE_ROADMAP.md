# 矿物线 + 强化 + 城防路线图（2026-10-29 12:4x；14:4x boost；17:4x fundSpend；**23:4x fortify hardening**）

Live refresh **23:50 UTC+8** tick ~83945055。**不自动交易、不开 safe mode。**
围攻已中止；`walls.fundSpend` 仍在推家墙 **~230k→300k**（05:4x ETA ~6 h）；**23:4x** lab ramparts live ~600k；**05:4x** W45N7 Invader-res reclaim。boost 代码仍等殖民地 RCL7+storage。W47N8 seal 300k，spawn2/tower soft ramps ~20–50k 待抬。

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
| 城防 | 墙 11 面 min **300001**；北门 GATE@29,3 **300301**（巡逻 "~20k" 实为 spawn 位 `GATE_TOWER` 地板）；塔 2；Spawn2 only |
| ETA RCL7 | ~23 e/t → ~**11-01**（~49 h）；ideal ~30 → ~33 h |

### 代码/开关
- `plan.RCL6_MINERALS=true`（home 矿物基建已齐）；`plan.RCL7_INDUSTRY=false`（factory+labs4–6 不落点）
- `w47n8.config.RCL6_MINERALS=false` / `HUB_LINK=false`
- `managers/labs.js`：反应 + `task()` 已有；**carrier 未接**（本 PR 接 hauler，仍需 `Memory.ops.labs`）
- **无** `boostCreep` / 战斗预强化 spawn 代码
- `Memory.defense.remoteDefender=true`（#1 已验 W47N7）
- 邻居：BustJetter W47N9 / Evans W48N8 当前 **无视野**；外矿 SAFE；W45N7 残留他户 spawn `fhl`@13,10（非 Invader creep）

---

## 1. 矿物 / 强化分阶段

### 阶段 A · 现在 → W47N8 升 RCL7（优先升级，~1–2 天）
**目标：** 殖民地 RCL7；home 不抢能量。

| 做 | 不做 |
|---|---|
| 保持 home 采 O（或设 `Memory.ops.mineralCap=50000` 省 ~0.9 e/t，库存已远超实验室短期需求） | **不开** W47N8 `RCL6_MINERALS`（terminal+3labs+矿容器 ≈ **255k**，≈ 11–17k tick 升级，拖 RCL7 **半天+**） |
| 保持 `RCL7_INDUSTRY=false` | 不买矿、不卖 O（credits 0；买卖需你批） |
| labs 代码保持 dormant | 不造 factory / labs4–6（+250k） |

**强化现实卡点：** KO 需要 **K+O**。我们有 O，没有 K 库存。K 来源只有两条：
1. W47N8 采 K（需阶段 B 开矿物线 + 矿物角色）
2. 市场：先卖部分 O 换 credits 再买 K（**需你批准**；当前 O 买单约 18–19 cr，K 买单极差 ~0.9，卖价另查）

Loot 里已有微量 UH/KO/ZH —— 只够试验，不够常备强化。

### 阶段 B · W47N8 刚到 RCL7（先基建后矿物）
> 20:4x：`RCL7_INDUSTRY=false` 已写入殖民地 config——**不造 factory@35,30（100k）**；day-of 仅 spawn2@33,30 + tower3@22,7 + 10 ext + spur roads（~53k）。详见 `docs/PLAN_W47N8.md` "RCL7 day-of"。

顺序（能量从紧到松）：
1. **tower3 + spawn2**（~20k）—— 立刻提升殖民地火力与产能
2. 北门 rampart 抬到 ≥100k，seal 墙按 `WALL_TARGET[7]=1M` 慢慢涨（只花盈余）
3. storage 稳住 ≥20k 后，再翻 **`RCL6_MINERALS=true`**：落 terminal + 3 labs + 矿物容器（extractor 已在）。约 **255k**，按殖民地净收入 ~20–30 e/t ≈ **0.5–1 天**
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
| 现在开 W47N8 矿物全套 | ~255k | 殖民地 RCL7 **晚 0.5–1 天** |
| 现在开 home RCL7_INDUSTRY | ~250k | home 墙/升级再少半天；且无 factory 代码 |
| 继续采满本轮 O（~10k 余） | ~4k creep 成本量级 | 可忽略；库存已 130k |
| 墙 142k→300k（41 墙） | ~65k | 受 `reserveE` 卡住，见城防 |

---

## 2. 城防 / 加固分阶段（**23:4x hardening**）

### 2.1 深挖结论（相对 Overmind / Screeps docs）
- **Overmind：** RCL7 `barrierHits = 1M`，`fortifyDutyThreshold = 500k`（storage 够才全力抬墙）。我们用 **STEPS + 50k fund + fundSpend FLOOR 5k**，等价但更抠能量。
- **软目标矩阵（home live 23:50 → 02:4x 复核）：** spawn/tower/storage/terminal **有** rampart；**3 labs rampart 已落地**（live ~423k，23:4x 规划）。extractor/links/containers 仍无（extractor 在环外，可接受）。
- **W47N8：** seal 墙 + GATE@29,3 均已 **≥300k**。巡逻日志 "~20k GATE" 是 **spawn 位空 rampart 的 `GATE_TOWER=20k` 地板**，不是北门——已纠正。
- **塔覆盖：** home 3 塔足够核心；殖民地 RCL7 当天落 tower3@22,7（北线）。不扩 4 塔直到 RCL8。
- **优先级插入：** lab 盖板（廉价、立刻消除最软点）→ 环墙 300k → 殖民地 RCL7 tower3+spawn2 → 矿物 → 屏障 1M。

### Home W46N8
| 阶段 | 目标 | 备注 |
|---|---|---|
| **现在** | **lab@34,22 / 35,21 / 33,21 落 rampart** | **✅ 23:4x** 写入 `layouts/W46N8` RCL6(+7/8) rampart 列表；`layout.js` 自动落点；塔先抬到 `RAMPART_FLOOR` 5k（storage<reserve 时），有余粮再往 RCL 目标 |
| 并行 | 环墙 min→**300k**（STEPS[7]） | **✅ 17:4x `walls.fundSpend`** 仍 live；02:4x min **~197k**，fund ~43k；ETA **~12–18 h**（~16:30 Asia/Hong_Kong） |
| 稳后 | 全屏障 **1M** | Overmind RCL7 1M；我们 STEPS 下一档；structure ramp 已有 ~345k–1M |
| 姿态 | 3 塔满能；SM **永不自动**；remoteDefender on | BustJetter：**defend-only** W47N9 |

**已落地：** 17:4x fundSpend；**23:4x lab rampart 布局**（+ `tests/lab_ramparts.js`）；**02:4x** labs 盖板 live ~423k；`STATIONARY_FILL` 仍 false（`docs/RCL7.md`）。`reserveE=15k` 保留。

### Colony W47N8
| 阶段 | 目标 |
|---|---|
| RCL6 现在 | seal 墙 + GATE **已 ≥300k**（live 确认 GATE 300301）；保持；spawn 位 rampart 维持 `GATE_TOWER` 20k 即可 |
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
| RCL7 后 | `w47n8/config.js` `RCL6_MINERALS=true` | config | storage≥20k |
| RCL7 后 | W47N8 mminer / mineral 容器站位 | roles + layout | 与上同步 |
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
1. **主路径（推荐，零 credits）：** 等 W47N8 **RCL7** → tower3+spawn2（~20k）→ storage≥20k → 翻 `RCL6_MINERALS=true`（terminal+3labs+矿容器 ~255k）→ mminer 采 K → `terminal.send('W46N8', K, n)`（33 e/1k）→ home `Memory.ops.labs={W46N8:'KO'}`。
2. **市场捷径（需 Misaki 批）：** 卖部分 O 换 credits 再买 K。当前 O 买单 ~18–21、K 买单极差；**不自动 deal**。围攻期不做。
3. **Loot：** terminal 里 UH15/KO32/ZH38/GO127 —— 只够单次试验，不够常备。

### 4.6 与围攻/RCL 的时序（14:41）
| 何时 | 做什么 | 不做 |
|---|---|---|
| **现在（围攻已中止）** | 采 O（无 mineralCap）；home 墙 fundSpend→300k；殖民地冲 RCL7 | 不写 boost 代码、不开 `ops.labs`、不开 W47N8 矿物、不卖矿 |
| W47N8 → RCL7（~10-31/11-01） | 立刻 tower3(22,7)+spawn2；修 GATE ramp≥100k | 仍不开矿物直到 storage≥20k |
| storage 稳住后 | `RCL6_MINERALS=true` + mminer；K→home | 不开 `RCL7_INDUSTRY` |
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
