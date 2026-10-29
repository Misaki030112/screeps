# 矿物线 + 强化 + 城防路线图（2026-10-29 12:4x live）

Live tick ~83936205。**不自动交易、不开 safe mode。** 数字来自 `tools/market.py` + console query。

## 0. 现状（实测）

### W46N8 home RCL7
| 项 | 值 |
|---|---|
| 进度 | ~400.4k / 10.9M |
| 矿物 | **O** @40,24 余 **10136**（正在采）；extractor cd 4；容器 41,24 |
| 库存 | storage O **17324** + terminal O **112476** ≈ **129.8k O**；另有战利品 GO127 KO32 ZH38 UH15 |
| terminal | 有，能量 **0**；credits **0** |
| labs | **3**（34,22 / 33,21 / 35,21），空，500 hits；`Memory.ops.labs` **未设** → `labs.js` dormant |
| factory | **0**（`plan.RCL7_INDUSTRY=false`） |
| spawns / towers | Spawn1+Spawn3；**3 塔**能量 ~900–950 |
| 墙 | 41 面墙 min **142101**（下一阶 STEPS[7]=**300k**→**1M**）；rampart 13 面 min **328501**（核心已 ~1M） |
| 墙资金 | fund **50k** 封顶；`Memory.defense.reserveE=15000`，storage ~**14.8–15k** → 常触 `defLow`，和平期修墙几乎停 |
| mminer | 1 只在采；`mineralCap` **未设** |

### W47N8 colony RCL6
| 项 | 值 |
|---|---|
| 进度 | **2.616M / 3.645M**（余 ~1.029M） |
| 矿物 | **K** **35000** @37,45 **未采**；extractor **已有**（Misaki 自有，layout 门控后未拆） |
| terminal / labs | **无**（`config.RCL6_MINERALS=false`，正确） |
| storage | ~**1.2k** energy |
| 城防 | 墙 11 面 min **300001**（= RCL6 `WALL_TARGET`）；rampart 4 面 min **~20k**（北门 GATE）；塔 2；Spawn2 only |
| ETA RCL7 | 按 ~15–23 e/t → 约 **10-31 上午～下午**（storage 紧时偏慢） |

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

## 2. 城防 / 加固分阶段

### Home W46N8
| 阶段 | 目标 | 备注 |
|---|---|---|
| 现在 | 环墙 min→**300k**，外门 rampart→**1M** | STEPS[7]；fund 满但 **reserveE=15k** 常令 `budgetE=0` |
| 稳后 | 全屏障 **1M** | 约需再投六位数能量；和平期 rate 0.10×23≈2.3 e/t 很慢 |
| 姿态 | 3 塔满能；SM×6 **永不自动**；remoteDefender on | 对 BustJetter：**defend-only** W47N9 |

**建议（运行时，非本 PR）：** 外矿平稳、无玩家压境时，把 `Memory.defense.reserveE` 降到 **10000** 或临时删掉，让 builder 吃 fund 把墙推到 300k；有警报再加回 15k。

### Colony W47N8
| 阶段 | 目标 |
|---|---|
| RCL6 现在 | seal 墙保持 ≥300k；GATE rampart 从 ~20k → **≥100k**（塔已 GATE_TOWER 20k） |
| RCL7 当天 | tower3 + spawn2；`WALL_TARGET` 升到 1M（config 已按 RCL 索引） |
| 之后 | 关键 hub/spawn/storage/tower 补 rampart（layout ORDER.rampart）；仍不主动打 BustJetter |

### 外矿 / 预订
- 已有：home `defender`（预订房敌情）+ W47N7 `rdef`（#1）
- 缺口：无主动观察 W47N9/W48N8（novis）；可继续 north_watch；不建议再扩兵种直到有 boost
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
| 有 KO 后 | boostCreep 接线 | 新 `managers/boost.js` + spawn/roles | — |
| 更晚 | `RCL7_INDUSTRY=true` | `plan.js` | 有 T2/factory 需求 |

**明确不做：** 市场 deal；自动 safe mode；把密钥写进仓。
