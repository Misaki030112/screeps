# W46N8 外层防御 + RCL8 成型规划 v2（设计稿，未部署）

更新：2026-10-15 09:50 (UTC+8)。脚本 `tools/defense_plan2.py`（v1 `defense_plan.py` 已被取代），渲染 `tools/render_defense2.py`，
数据 `data/defense_plan2.json`，图 `docs/final_layout_defense.png`。**不放工地、不拆建筑、不急着修墙；塔位改动只是提案。**

## 中文摘要（给 Misaki）
1. **墙和 rampart 的真实区别**（数字核对过官方 constants）：两者造价都是 1 能量，加血都是每 100 血 1 能量，墙的上限是 300M。
   rampart 每 100 tick 掉 300 血，折合每格每 tick 0.03 能量，30 格一天（约 2.9 万 tick）大约 260 能量，几乎可以忽略。
   rampart 的血量上限随等级涨（RCL4 3M、RCL5 10M、RCL8 300M），这对我们暂时不是限制。
   真正的区别有两点：rampart 能让自己人通过，防守 creep 也能站在上面打人，站在上面时它不会受伤；墙则谁都过不去。
   所以大神的普遍做法是：门和防守者要站的位置放 rampart，其它位置放墙也行。到了 RCL8，Overmind 会把整圈都换成 rampart。
2. **边界要再往外推一格**：远程攻击的射程是 3，所以边界离建筑至少要 3 格，这是 Overmind 的 padding=3，也是 Jon Winsley 的建议。
   v1 只留了 2 格，现在改成 3 格，割线从 30 格变成 **32 格**。东边那条线移到了 x=47 附近，把东边的平地也围了进来。
3. **能源 A 怎么保护（第 1 点）**：
   | 方案 | 外圈格数 | 门 | 额外 | 50k血成本 | 能源A处塔伤 | 风险 |
   |---|---|---|---|---|---|---|
   | **B 留在外面，局部 rampart（推荐）** | 32 | (33,15) 去能源A，(47,20) 去外矿 | 容器/矿工格 (31,12) + link (30,11) 两格 rampart | ~17k | 1830/tick | 矿工站在容器上会被 rampart 罩住，打不到；但运输路线要出门 |
   | A 把能源 A 一起围进来 | 37 | (47,20) | 无 | ~18.5k | 1530–1980 | 西北多出 9 格，其中 5 格在 x=28 一线，离塔远（塔伤低）；整圈最弱点从 1680 掉到 ≤1530 |
   | C 什么都不做 | 30–32 | — | — | 最便宜 | — | 被围攻时能源 A 会停产，矿工会死 |
   能源 A 的能量是靠 link 送回家的，运输不用出门，所以 B 方案只多花 2 格，就能守住矿工、容器和 link。
   A 方案多 5 格，整圈还会变弱，所以推荐 B。
4. **塔位多指标评分（第 2 点）**：已建的 (36,29) 和 (37,33) 不动。评分权重如下：
   - 边界最低塔伤 35%；
   - 核心最低塔伤 15%；
   - 门的塔伤 10%；
   - 修 rampart 的平均能力 10%；
   - 补能距离 20%：从仓库门走到塔要几格，路线全程不出墙；manager 旁边的塔算 0；
   - 暴露度 10%：塔离墙外敌人能站的格子 ≤3 就算暴露。
   - 两个硬条件：补能距离 ≤10 格，离墙外 ≥4 格。

   | 方案 | 总分 | 边界最低 | 核心最低 | 门最低 | 修墙平均 | 补能平均格 | 暴露 |
   |---|---|---|---|---|---|---|---|
   | 现行 (36,29)(37,33)(35,34)(36,34)(32,30)(32,31) | 0.613 | **990** | 3240 | 1470 | 2795 | 1.3 | 0 |
   | **推荐** (36,29)(37,33)(39,23)(40,23)(41,24)(32,30) | **0.644** | **1680 (+70%)** | 2760 | 2340 | 3315 | 5.2 | 0 |
   | 只看伤害的方案 | 0.640 | 1710 | 2760 | 2370 | 3272 | 5.7 | 0 |

   推荐方案把 (35,34)、(36,34)、(32,31) 三座未建的塔挪到矿物旁的东北角 (39,23)、(40,23)、(41,24)，保留 (32,30)。
   新塔位都挨着 srcA/矿物主路，补能 9–10 格，全程在墙内。
   代价是核心最低塔伤从 3240 降到 2760，但仍然远高于边界。
   现行方案下东墙 x=47 只有 990，是明显短板。
5. **时间**：不急着修。等你点头后，最早也是 RCL6 开始放墙，每格先加到 5 万血，共约 1.7 万能量；新手保护 10-28 03:33 结束前后可以考虑先只放 2 个门和能源 A 的 2 格 rampart。
   每格加血的总能量：30 万血约 10 万，100 万血约 34 万，300 万血约 100 万。

## 已核对的机制和来源
- `screeps/common` 的 constants.js：RAMPART_DECAY_AMOUNT 300 / RAMPART_DECAY_TIME 100；RAMPART_HITS_MAX {2:300k,3:1M,4:3M,5:10M,6:30M,7:100M,8:300M}；
  WALL_HITS_MAX 300M；CONSTRUCTION_COST wall/rampart = 1；REPAIR_POWER 100、REPAIR_COST 0.01；
  TOWER_POWER_ATTACK 600 / HEAL 400 / REPAIR 800，OPTIMAL_RANGE 5，FALLOFF_RANGE 20，FALLOFF 0.75（20 格外只剩 25%）；TOWER_CAPACITY 1000，每次行动 10 能量；
  塔的数量上限是 RCL7 3 座、RCL8 6 座。https://raw.githubusercontent.com/screeps/common/master/lib/constants.js
- 官方 API 文档 StructureRampart / StructureWall / StructureTower：https://docs.screeps.com/api/
- min-cut 算法：Saruss 的 `minCutWallRampartsPlacement.js`（https://github.com/screepers/screeps-snippets），
  Josef37 的 `screeps-min-cut-wall`（每个格子拆成两个点再求最小割）。
- Overmind 的 BarrierPlanner：用 min-cut 围住 bunker 和控制器，padding 3，RCL7 以后只维护 bunker 和控制器旁的 rampart。
  https://github.com/bencbartlett/Overmind/blob/2eae97b/src/roomPlanner/BarrierPlanner.ts ，Bunker 说明：https://github.com/bencbartlett/Overmind/wiki/Bunkers
- Jon Winsley《Screeps #21 Patrolling the Perimeter》：边界要离建筑 3 格以上，否则远程攻击能隔墙打到；补能 creep 不应该需要出墙。https://jonwinsley.com/notes/screeps-patrolling-perimeter
- Tigga 和 Harabi：这次没有找到公开的详细布局文档，所以不引用，避免编造。

## 数据
- B 方案的割线（32 格）：`(23,27-29) (23,35-38) (31,16) (32,16) (33,15) (33,16) (42,28) (43,28) (44,26-28) (45,26) (46,26) (47,11-24)`
- A 方案在 B 的基础上去掉 (31,16)(32,16)(33,15)(33,16)，换成 x=28/29 一线的 9 格，共 37 格。
- 门：(33,15) 去能源 A，(47,20) 去外矿 W45N8 方向；可选 (23,28) 往西。
- 局部 rampart：(31,12) 容器兼矿工位，(30,11) 能源 A 的 link。

## 需要批准的提案
1. 采用 B 方案（能源 A 在墙外，加 2 格局部 rampart）。
2. 塔位：RCL7 的第 3 座塔从 (35,34) 改到 (39,23)；RCL8 的另外两座从 (36,34)、(32,31) 改到 (40,23)、(41,24)，保留 (32,30)。
3. 什么时候开始放墙由你决定，建议不早于 RCL6。
