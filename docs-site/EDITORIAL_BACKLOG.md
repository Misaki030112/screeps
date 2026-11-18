# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-18（Asia/Hong_Kong）。手册现在对照的仓库是 `289a7f06`（`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。这一笔改过 `src/`，动的是枢纽容器被占时的寻路，没有改 `linkRun` 或 `managers/links.js`。「现状」里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有按新提交重算。这一轮没有改 `src/`。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。

## 这一轮做了什么

加深了 `docs-site/mechanisms/links.md`（Link 与枢纽）。标题和侧栏改成「Link 与枢纽」，地址仍是 `/mechanisms/links`。新组件 `LinkFlow.vue`，画两间房的发送顺序。升级工只数、filler 条带、softCap、keep、40000 的闩都没有在这一页重写，只留交叉引用。`yieldPost`、`POST_COST`、枢纽容器被占时抬高 32,32 和 33,33 的代价，没有写进这一页。

对照这些源码写的。

- `src/managers/links.js`：`CTL_LOW = 400`，`SEND = 400`。`Game.time % 3` 才继续，link 少于两座也返回。源先循环，目标空就退回枢纽。枢纽只在 `target()` 非空时送，不送给自己。`target()`：`noUpgrade` 时控制器退出；否则控制器低于 400；再否则能量最低且低于 400 的 filler。`STATIONARY_FILL` 关着，`fillers` 为空。其余 link 都算源。
- `src/utils/plan.js`：`LINK_PLAN` 六座，`STATIONARY_FILL` 是 false。关着时删掉 v2 稿里的 link，只放这份计划。RCL5 稿上的 35,26 要到 RCL8。
- `src/main.js`：家每拍调用 `links.run`。W47 在布局和 `towerRun` 之后 `continue`，不进这段。
- `src/rooms/w47n8/index.js`：`towerRun` 第一行调用 `linkRun`，每拍，不等 3。源 A 至少 50、控制器空位大于 0，送 `min(已有, 空位)`，不看 400。枢纽要控制器低于 400、自己至少 200、还有空位。`h !== a`。注释里的距离 19、大约 42 毛 / 41 净。坐标算下来横差 19、竖差 8。800×0.97 = 776，776÷19 大约 40.8。`hubLinkLive` 要旗标开着并且 32,33 上有建筑。33,34 的工地会拆，建好的不拆；旧建筑还在时不放 32,33。
- `src/rooms/w47n8/layout.js`：`ORDER.link[0]` 是 32,33。`RETIRED_HUB_LINK` 是 33,34。`hubLinkPos()` 在名单不是旧格时用名单，否则回落 32,33。
- `src/rooms/w47n8/config.js`：源 A 27,11 / 站 26,11 / link 26,12。源 B 11,44 / 站 11,43，没有 link。控制器 link 13,25。枢纽容器 33,33。`HUB_LINK` true。
- `src/rooms/w47n8/roles.js`：`NORTH_FEED` 600。站位四格以内的己方塔低于 600，且脚下容器低于 1500，矿工跳过 link。北塔 24,8 距离 3。22,7 距离 4，注释只点了 24,8，代码认四格内任何一座。矿工空位 `<= 2 * WORK` 才送 link。升级工挨着 13,25、身上能量 `< 2 * WORK` 时可以从 link 取。
- `src/rooms/w47n8/index.js` 的 `bodyFor('w8miner')`：源 A 的 link 已在且预算 `>= 750` 时加 1 个 CARRY。两只矿工共用这次判断。
- `src/rooms/w47n8/fill.js`：存储 `>= 15000` 才灌枢纽。`< 25000` 只在枢纽 `< 200` 时预热。`>= 25000` 时电池薄也灌。职责顺序没有抄过来。
- `src/rooms/w47n8/index.js` 的 `hFloor`：`Memory.ops.w8model.links` 为真是 2，否则 3。不改变传送。
- `src/roles/queen.js` 的 `standby`：房间满（可用能量到容量，塔都不低于 900）才进。`ctlLinkLow` 是枢纽和控制器都在、控制器 `< 400`。有空位才从高出 `storageFloor` 的存储灌枢纽。`noUpgrade` 时不灌；枢纽 `> 400`、手里是空的、没有家搬运工，才从枢纽抽出。
- `src/roles/hauler.js`：`noUpgrade` 且存储在、又有源 link 时，`hubPickup` 返回枢纽。人走到 `positions.manager` 36,30，枢纽至少 `min(空位, 400)` 才取。控制器容器的 1000 是搬运工的 `CTL_LOW`，和 link 的 400 不是同一个常数。
- `src/roles/miner.js`：家的矿工空位 `< WORK * 2` 且有携带容量，送相邻 link，否则相邻存储。源 B 38,32 旁边是存储 37,31。
- `src/roles/upgrader.js`：家的升级工身上能量 `<= WORK` 时先取控制器 link。
- `src/managers/walls.js` 的 `noUpgrade`：阶段在升级页，这一页只写它怎样把控制器 link 移出目标。
- `src/utils/cmd.js` 的 `consumeLink`：`idle` / `hold` / `transfer` 让自动传送让开。没开指挥官时不改变行为。
- 测试只用来核对边界，没有写进正文：`tests/rcl5_gate.js`、`tests/w47n8_flow.js`、`tests/w47n8_hub_link.js`、`tests/queen_standby.js`。
- 交叉读了 `docs-site/mechanisms/upgrade.md`、`haul.md`、`reference/rooms.md`，以及 `now.md` 和页脚里的对照提交。`rooms.md` 里枢纽 37,29 / 32,33、控制器 30,31 / 13,25 这两格和代码一致，没有改。

旧页上改掉的地方：

- 「源和枢纽都是至少 400 才传送，没有目标就退回枢纽」拆开。源没有目标才退回枢纽。枢纽没有目标就留着，不送给自己。
- 家是每 3 拍，而且 `main.js` 每拍都会调用、函数自己返回。W47 的 `linkRun` 在 `towerRun` 里每拍都跑。旧页没写这道差别。
- 「这一段短，所以 W47 的源用 50」改掉。源 A 到控制器的距离是 13，枢纽段是 19。50 是注释里的「避免零碎小传送」，并且不再要求空位至少 400。注释里的死锁例子是控制器大约 486、空位 314。
- 毛输送从「大约 40」改成满载 800÷19 大约 42.1，扣 3% 后 776÷19 大约 40.8。注释和升级页的大约 41 是这个数的约数。升级页那一句跟着改了，避免两页各写一个约数。
- 「不够突然多出来的一排」改成：满载够现在这两只 10 WORK。再加一只够不够、闩怎么合，留在升级页。升级页写过满载盖得住 30 个 WORK。
- 源 B 没有 link，写明了。家的源 B 也没有，矿工送进存储。
- 北塔跳过 link 补上：600 和容器 1500。代码认站位四格内任何塔，所以 22,7 也算，不只注释里的 24,8。
- `HUB_LINK` 只放工地。`hubLinkLive` 要旗标和 32,33 上的建筑。旧页「工地还在时就把升级工加上去」改成：代码不按旗标加人。
- 33,34 不发送、不灌、不当 `hubLinkLive`。工地会拆，建好的建筑不拆，还在时不放第二座。
- 女王的门写清：房间满、`storageFloor`、控制器 link 低于 400、枢纽有空位。暂停升级时是枢纽多于 400 且没有家搬运工才抽。搬运工等在 36,30 仍保留，和搬运页一致。

`now.md` 只把手册基线改成 `289a7f06`。百分比和 2026-11-17 的快照没动。页脚 `Layout.vue` 的对照提交跟着改成同一个 SHA。搬运页和升级页只改了指向这一页的链接文字，升级页多改了 40.8 那一句。导读里的机制名单改成「Link 与枢纽」。没有改 `src/`、`scripts/`、`dist/`。

## 下一轮

加深 `docs-site/mechanisms/remotes.md`（外矿与预定）。把 W45N8、W45N7、W47N7 停在这一页上。搬运页已经有 24C12M 和 W47N7 的那 1 个 WORK。防御页已经有状态机、巡逻，以及防御从哪间房的出生点出。不要把过时的单房间日志再分进公开导航。

## 再往后

按读者会先问的顺序。已有的页面都还短的，缺的是为什么和边界，不是再开一篇日志。

1. **外矿与预定**（下一轮，加深 `remotes.md`）。见上一节。
2. **CPU 与主循环**。加深 `loop.md`，对照 `src/main.js`。实验室页和矿物页各只用了一句：W47N8 不调用 `labs.run`。这一轮的 link 页写了 W47 的 `linkRun` 在 `towerRun` 里，主循环那一页还没有把这件事展开。
3. **部署约定**。`deploy.md` 已经有一页。只做措辞上的打磨，继续保持公开、不含令牌。
4. **还没有独立页面的**。布局：现行 v2。移动：`src/utils/move.js` 的路径缓存和脱困，加上 W47 的 `yieldPost`。`yieldPost` 把 filler 的空闲格 34,32 抬到代价 4，房间里的路程在 32,32 那格平地空着时走那里。#64 的满载停驻写在搬运页。`289a7f06` 在枢纽容器被占时抬高 32,32 和 33,33 的代价，留在这一页，不要插进 link、升级或搬运。`C.SPAWN` 仍是 15,18。延伸 32,34 没有挪。升级页没有把出生口袋写成未解决的现行行为。指挥官接管：`Memory.cmd` 没设置时不接管。实验室页只写了 `react` / `idle` / `hold` 怎么让自动反应让开，矿物页只写了终端被占用时这一拍不送，link 页只写了 `consumeLink` 让自动传送让开，都没有把指挥官写成一篇。
5. **日期日志不要再进给人读的入口**。`STRATEGY`、路线、RCL7 这类日期记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。
6. **站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app 。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。
7. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
