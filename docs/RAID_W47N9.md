# W47N9 进攻（推平优先 / 烧 SM 次之）

Misaki 2026-10-29：目的优先 **有把握则推平 W47N9**；推不平则制造必开压力 **烧掉 safe mode 次数**。覆盖此前对该房的 defend-only。

Code: `src/roles/raid9.js`（已在主线），控制 `tools/raid9.py`，测试 `tests/raid9.js`。
**本文件与 PR 只做策划与可选加固；未经 Misaki / 上级批准不得 `arm`、不得 deploy 出兵。**

## Live 快照（tick ~83936440，Asia/Hong_Kong 2026-10-29 ~12:55）

| | W47N9（BustJetter） | W48N9 | 我方 |
|---|---|---|---|
| RCL | 6（progress ~1.165M） | 6 | home W46N8 RCL7；colony W47N8 RCL6 |
| SM | **无激活**；`safeModeAvailable` **4**；cooldown 已过（可再开） | avail 5；旧 SM 痕迹 tick 字段 83135281（已结束） | home avail **6**；W47N8 **5**；**不自动开我方 SM** |
| 塔 | **2 座，各 10 能量**（废） | 940 / 760 | W47N8 两塔满；home 三塔 |
| 墙 | **0 constructedWall** | 0 | — |
| Rampart | 69 块，**min ~83.7k / med ~84.0k**；核心上 ~84k | min 100k | W47N8 北墙 300k；北门 rampart ~20.8k |
| Spawn | Spawn3 @26,29，能量 **~33**；周围扩展 **40 座合计 0 能量** → **当场几乎不能出兵** | — | Spawn1/3 home 空闲；Spawn2 colony |
| Storage / terminal | stor **36.5k** E + 146k H；term **2.6k** E | stor 20k | home stor **~14.0k**；colony **~2.3k**；reserveE 15k（raid9 **无视地板**） |
| 战斗爬 | **0**（14 民用：hauler/filler/upgrader/scout） | 仅 **bhk1un1** 7H7M 未 boost @2,30（可贴西界进 W47N9）；此前告警的 6RA **已不在** | raid9 **0** 存活；`Memory.ops.w47n9` 仍是 10-21 旧状态 `on/n=4/safe/...` |
| 视野 | 我方 `Game.rooms.W47N9` **无**；情报来自 `game/room-objects` | 同左 | CPU ~15 / bucket 10000 |

南线接近：从 W47N8 北口进 W47N9 后，走廊 **x=20–32、y=35–49 无 rampart 挡路**，可直扑 spawn 26,29。y=42 的 rampart 带在 x=34–44（偏东），不挡西侧核心。

## 优先级怎么打

### 1) 推平（有把握才宣称）

**有把握推的是「核心瘫痪」**，不是 1 波拆光 69 块 rampart：

- 空塔 + 无战斗爬 + 扩展 0 能 + ~84k rampart + 南线畅通 → 同款 2 近战 + 2 远程（合计 ~1160 结构 DPS）约 **~80 tick** 打穿 spawn 上 rampart+spawn，再清两塔/仓库可在 **单波 TTL 内**完成。
- 10-21 同编制已逼出过 1 次 SM；今日防御 **弱于** 当时（塔空、无兵）。
- **完整房清**（69×84k ≈ 5.8M hits）单波做不到；推平定义为：**拆 spawn + 两塔 + 尽可能拆 storage/terminal/扩展，使该房不能再生产**。

若对方 **不开 SM**：按目标序硬拆 → 达成优先级 1。  
若对方 **开 SM**：立即停攻、撤回 W47N8 北墙驻防 → 达成优先级 2（烧掉 1/4）。

### 2) 逼开 SM 的压力点

Screeps 的 SM 由对方脚本/玩家在「基地受严重威胁」时激活。可靠压力：

1. 近战贴上 **spawn（26,29）** 并持续打（同格 rampart 掉血可见）——**主目标，不绕路追 feeder**。
2. spawn 已毁后再点塔、杀塔旁带能 creep（防补塔）。
3. 不恋战民用清理优先级低于 spawn/塔。

对方仍有 4 次 SM 且冷却已好，**开 SM 是理性反应**；我们按烧次数计成功。

### 止损（必须执行）

| 条件 | 动作 |
|---|---|
| W47N9 进入 safe mode | 成功烧 SM；`raid9` 自动 `safe`→W47N8 北墙 garrison；**不派第二波** |
| spawn + 两塔已毁且无 SM | 推平阶段成功；同波继续拆 storage/扩展至 TTL；**不自动 claim** |
| 房内敌方 ATTACK+RA 部件合计 ≥12（侧翼重兵） | 代码 `flee`→garrison；人工评估是否二波 |
| 存活 raid9 ≤1 或三人阵亡 | 一波结束、**不自动补员**；复盘后再说 |
| 进房前塔被补到各 ≥500 且出现战斗爬 | **不要 arm** / 已在集结则 `abort` |
| 我方房间受袭 | 立即 `abort`；**永不自动开我方 SM** |

## 编制（推荐 = 最少成功编制）

与 10-21 probe 相同（已验证能逼 SM）：

| 槽 | 体型 | 造价 |
|---|---|---|
| melee ×2 | 2T 16A 18M | 2200 |
| ranged ×2 | 10RA 11M 1H | 2300 |
| **合计** | 从 **W46N8** 出 | **9000** |

- 集结：W47N8 `30,1` / `31,1`（近战前排）+ `30,2` / `31,2`（远程后排）；齐员再进。
- 进房：**近战先、远程后**（已写在 `raid9.js`）。
- 目标序：**spawn（同格 rampart 吃伤；siege path 无视墙/rampart 阻挡）** → spawn 死后才打塔旁带能 / 近距武装 → 其它非路/墙建筑（塔优先）+ 附近 creep → 其余 creep。**禁止**在 spawn 仍在时西追 feeder/小兵。
- 一波不补员。第二波仅当：无 SM、核心未死、第一波阵亡/TTL 将尽、且 Misaki 再批。

不建议一上来加大体型：9000 已够空塔房；加大只增加 CPU/时间窗口给侧翼反应。

## 风险

- **W48N9 回防**：现仅 1 治疗；真正风险是临时造 6RA/近战从西界进 W47N9。止损阈值防被锤死。
- **终端补能**：W48N9 stor 20k / W47N9 term 在，可能突然补塔；进房后优先打断 feeder。
- **代价**：9000 E ≈ home 半仓；换 1 次 SM 或拆掉 spawn，划算。换不到（空跑）则止损。

## 启动（批准后）

旧 Memory 仍为 10-21 残留（`on:true,n:4,safe,...`）。**必须整表重置**，否则新爬会因 `P.safe` 直接 garrison：

```bash
# 只读
python3 tools/raid9.py status

# 批准后再执行（会写 Memory 并开始从 home 造 4 只）
python3 tools/raid9.py arm

# 紧急停造 + 标记 garrison（已出的爬撤回北墙）
python3 tools/raid9.py abort
```

`arm` 等价于：

`Memory.ops.w47n9 = { on: true, n: 0 }`（清掉 `safe` / `safeUntil` / `garrison` / `go` / `flee`）。

代码已在 master；若本 PR 的止损加固未合并，仍可用旧逻辑（仅 SM 撤退），但侧翼重兵时可能打光。
