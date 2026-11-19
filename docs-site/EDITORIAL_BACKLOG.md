# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-19（Asia/Hong_Kong）。手册现在对照的游戏代码仍是 `289a7f06`（`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -- src/` 的最新一笔就是它。其后的 `279bf678`（#66）和 `f52851ca`（#67）都只动文档，不是 LIVE。这一轮也没有改 `src/`。`now.md` 和页脚已经指向 `289a7f06`，没有改。「现状」里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。

## 这一轮做了什么

加深了 `docs-site/mechanisms/loop.md`（主循环与 CPU）。地址仍是 `/mechanisms/loop`。`ArchDiagram.vue` 改成一列顺序，第 3 步画出已占领房间的分叉：W47 只跑布局和 `towerRun`，家和其他属于我们的房间才跑 link、实验室、警报。新组件 `CpuOrder.vue` 画桶低于 2000 时的 0 / 1 / 2。导读的机制名单补上「主循环」。Link 页「两种节拍」末尾加了一句，指向这一页解释为什么 W47 不在家的那张名单里。没有改传送门槛，也没有改实验室的门。

对照这些源码写的。

- `src/main.js`：整段循环。W47 在 `layoutRun` 和 `towerRun` 之后 `continue`。家的已占领房间才是布局、塔、`links.run`、`labs.run`、`alerts.run`。外矿没有 `controller.my`，不进这支。`remote.run()` 之后是道路，再是只对 `remote.CFG` 的 `alerts.run`。`Memory.cmd` 武装才 `runHeldStructures`。`raid9.tickFlags` 在 creep 之前。creep：跳过正在出生的，`freeTrapped` 在 `shed` 之前，然后缺角色写成 harvester，再做 v2 迁移，然后 `consumeCreep`，然后 `home.flee`，然后 `military.block` 和角色脚本。换位 `flush`、能量账、跟踪、统计、报告在最后。主要段落包在 `utils/errors`。
- `src/utils/cpuorder.js`：`LOW = 2000`，`MARGIN = 5`。优先级 0 是 guard、defender、w8defender、w8healer、w8guard、cqsquad、cqbreaker、cqatk、cqquad、raid9。1 是 queen、w8filler。其余是 2。桶不低于 2000 保持 `Object.keys` 的顺序，并且 `shed` 为假。`shed` 要桶低于 2000、优先级大于等于 2、并且已用 CPU 大于 `tickLimit - 5`。源码读 `Game.cpu.tickLimit` 和 `Game.cpu.bucket`，不写死 20。
- `src/rooms/w47n8/index.js`：`towerRun` 先 `TH.mark(room)`，再 `TH.mark(Game.rooms[C.REMOTE.room])`，然后 `linkRun()`，然后才找塔。没有塔也会先看 link。模块注释写明只为 W47N8 跑。
- `src/rooms/w47n8/threat.js`：`mark` 在房间为空时直接返回。记号的含义没有从防御页抄过来。
- `src/rooms/w47n8/config.js`：`RCL6_LABS` 仍是 false。`ROOM` 是 W47N8，外矿房是 W47N7。
- `src/managers/labs.js`：家的反应。开头坐标是 W46N8 的 34,22、33,21、35,21。`readyObs` 只写 W46N8。`run` 按 `Memory.ops.labs[房间名]` 取化合物，没有「房间是 W47 就返回」。W47 到不了 `run`，是主循环的 `continue`。
- `src/managers/threat.js`：`minBucket` 3000。`gateReason` 先看武装，再看 `bucket < minBucket` 返回 `cpu`。SAFE 里因此进入 WAIT，不进入 THREAT。已经在 THREAT 或 DEFEND 的，`wantDefender` 只看状态和名额，不再读这道桶。
- `src/managers/visuals.js`：文件里 `MIN_BUCKET = 2000`，`run` 在桶低于 2000 时不画。全库只有 `tests/visuals.js` 引用它。`main.js` 和其他 `src/` 模块都不调用。公开页不再把「房间视觉在桶低于 2000 时不画」写成这一拍的行为。
- `src/utils/errors.js`、`src/utils/cmd.js` 的 `armed` / `runHeldStructures` / `consumeCreep`、`src/roles/raid9.js` 的 `tickFlags`、`src/utils/military.js` 的 `block` / `flush`（军事名单和优先级 0 是同一批）、`src/managers/home.js` 的 `flee`（主循环传入 4；只在我们的房间；攻击或远程）、`src/roles/queen.js` 的 `freeTrapped`、`src/roles/index.js`。
- `src/managers/remote.js`：`CFG` 只有 W45N8、W45N7。`check` 在状态变化时自己打 `ALERT`。W47N7 走 `guardRooms`，不进后面的 `alerts.run`。
- `src/managers/alerts.js`：敌对 creep 和事件日志每拍，建筑血量差每 5 拍。`src/managers/roads.js`：家的控制器低于 6 直接返回。`src/managers/stats.js` 与 `src/utils/report.js`：统计每拍写，`STATS` 每 10 拍一行，不驱动下一只 creep。
- 交叉读了 `docs-site/mechanisms/links.md`、`labs.md`、`minerals.md`、`remotes.md`、`defense.md`、`spawn.md`、`haul.md`、`deploy.md`、`now.md` 和页脚。实验室页和矿物页已经写了 W47 不调用 `labs.run`。防御页已经写了 3000 和 `mark`。搬运页已经写了女王和 `w8filler`。那些页没有重写。`docs/CPU.md` 仍写着房间视觉在桶低于 2000 时不画。那个文件不在公开导航里，这一轮没有改它。

旧页上改掉的地方：

- 「房间视觉在桶低于 2000 时不画」删掉。判断在 `visuals.js` 里，主循环不调用。
- 3000 写成进入 THREAT 之前的闸：武装且桶低于 3000，`gateReason` 返回 `cpu`。已经在 THREAT 或 DEFEND 的，不因这行被拉回等待。
- 停一拍写成三件同时成立，并且是已用 CPU **大于** `tickLimit - 5`。剩下正好 5 仍跑。桶不低于 2000 时不排序，也不停，哪怕这一拍已经用得很满。
- 补能只点名 `queen` 和 `w8filler`。家的角色名 `filler` 不在表里。
- 逃跑名单和优先级拆开。`probe`、`cqworker`、`cqhauler`、`cqminer`、`reserve7`、`cqrh` 不逃跑，优先级仍是 2。`memory.home` 为 W47N8 的都不走 `home.flee`。距离是传入的 4。
- W47 的 `continue` 同时跳过 `alerts.run`。外矿的 `alerts.run` 只覆盖 CFG 的两间，且在 `remote.run()` 和道路之后。W47N7 只有状态机那一行 `ALERT`。`alerts.run` 不读状态机刚写下的态。
- `linkRun` 写进 `towerRun` 的顺序：mark、mark、link、然后塔。实验室不调用，是主循环没送进去；`labs.js` 没有一条拒绝 W47 的返回。`RCL6_LABS` 仍是 false。
- 解脱写成任何走不出去的角色，在停一拍之前，就地捡、送、回收或自杀，不寻路。正在出生的连这一步都跳过。
- `STATS` 写成每 10 拍一行。5000 仍只是人的习惯，代码不读。

## 下一轮

打磨 `docs-site/mechanisms/deploy.md`（部署约定）。只做措辞，继续保持公开、不含令牌。不要把检查脚本、锁或上传记录写成一套新的操作手册。游戏代码不动。

## 再往后

按读者会先问的顺序。已有的页面都还短的，缺的是为什么和边界，不是再开一篇日志。

1. **部署约定**（下一轮，打磨 `deploy.md`）。见上一节。公开、不含令牌。
2. **还没有独立页面的**。布局：现行 v2。移动：`src/utils/move.js` 的路径缓存和脱困，加上 W47 的 `yieldPost`。`yieldPost` 把 filler 的空闲格 34,32 抬到代价 4，房间里的路程在 32,32 那格平地空着时走那里。#64 的满载停驻写在搬运页。`289a7f06` 在枢纽容器被占时抬高 32,32 和 33,33 的代价，留在这一页，不要插进主循环、link、升级或搬运。`C.SPAWN` 仍是 15,18。延伸 32,34 没有挪。升级页没有把出生口袋写成未解决的现行行为。指挥官接管：`Memory.cmd` 没设置时不接管。实验室页只写了 `react` / `idle` / `hold` 怎么让自动反应让开，矿物页只写了终端被占用时这一拍不送，link 页只写了 `consumeLink` 让自动传送让开，主循环只写了武装时谁先被看、以及 `consumeCreep` 会压过逃跑和角色。都没有把指挥官写成一篇。
3. **日期日志不要再进给人读的入口**。`STRATEGY`、`docs/REMOTE_*.md`、`docs/CPU.md`、路线、RCL7 这类记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。`docs/CPU.md` 里那句房间视觉，和现在的主循环页不一致，留在仓库里，不要为了把它改对就搬进导航。
4. **站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app 。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。
5. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
