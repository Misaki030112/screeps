# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-19（Asia/Hong_Kong）。手册现在对照的游戏代码仍是 `289a7f06`（`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -- src/` 的最新一笔就是它。其后的 `279bf678` 是手册 Link 页的压缩合并 #66，只动文档，不是 LIVE。这一轮也没有改 `src/`。`now.md` 和页脚已经指向 `289a7f06`，没有改。「现状」里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。

## 这一轮做了什么

加深了 `docs-site/mechanisms/remotes.md`（外矿与预定）。地址仍是 `/mechanisms/remotes`。新组件 `RemoteLines.vue`，画三条线归谁、W45N7 借南口、预定补位走 0,23 再走 27,49。没有把邻居的名字写进公开页。`src/managers/remote.js` 开头注释里的 listener 和 alerts.py 没有写进来。

对照这些源码写的。

- `src/managers/remote.js`：`CFG` 只有 W45N8、W45N7，家都是 W46N8。W45N8 的 `rhE` 1800、`pavedHaulers` 1、`roads` 只有 2,12、停车 46,21、出口 49,14 与 0,14。W45N7 的 `via` 是 W45N8，`avoid` 是 22,15，出口四格，`haulers` 5，`rhGap` 60，`rhGapSteady` 240，`lead` 140，`travel` 150，`rt` 230，`scout` 19,12，停车也是 46,21。`GUARD.W47N7` 是 `guardOnly`，家 W47N8，源 17,17，`cont` 24,14 是守卫走进时的落点，控制器 38,26，停车 16,20，岗位 27,19，出生点 Spawn2，出口 18,49 与 18,0。`Memory.remotes.<房间>.off` 只进 `paused`。`Memory.ops.resRooms` 是动态守卫，W47N9 被跳过。`placeRoads` 只放 `CFG.roads`。
- `src/managers/spawn.js`：`RES_SPAWN` 2000，`RES_WAIT` 1000，`reserverBody` 在可用能量至少 1300 时两颗 CLAIM，否则一颗。`waitClaim2` 要容量至少 1300、可用能量不到 1300、并且剩余不少于 1000。W45N7 因为有 `via`，`claim2Only`，可用能量不到 1300 不出。剩余大于 0 且低于 800、又没有 `via` 时 `wantRes` 是 2。矿工先于预定者和搬运工，两条线一起看。`reserve7` 的家补位在外矿循环之前；要人但可用能量不到 1300 时，这一拍家的队列停住。
- `src/roles/reserve7.js`：`LEAD` 260，`W8_CAP` 1800，`FALLBACK` 1000。`Memory.ops.r7.on` 才要人。我们的预定（`by === 'Misaki'`）剩余低于 2500 才要；别人的低于 260。W47 要 `w8Ready`。家在 W47 没准备好时补位；W47 已经准备好时，只有我们的预定且剩余低于 1000 才也要。不看 Spawn2 忙不忙。不调用 `attackController`。走路是 W46N8 的 0,23 向西，再 W47N8 的 27,49 向南。测试 `tests/reserve7_owner.js` 对过这些门，没有把断言抄进正文。
- `src/roles/remote.js`：边界先向内迈。W45N7 的等候、让矿工、不站 22,15、`viaGate`、口袋离开。家的预定者只在名下是 Invader 时攻击控制器，玩家的预定站着等。停矿时 x 在 2 到 47 之间，矿工改建造、搬运工改家搬运，其余去 46,21。`rscout` 只有配置了 `scout` 的房间。
- `src/managers/threat.js`：`paused` 用 `safe`。`EARLY` 是 15% 放行、30% 再停，角色只有 `rminer` 和 `rhauler`，而且要在 DEFEND、点名的防御 creep 已经在房里、任务不是核心。玩家的 WAIT 不提前。没有把整台状态机重写。
- `src/managers/roads.js`：阶段顺序，`paved('W45N8')` 要阶段名晚于 `W45N8`。`swamp7` 是 W45N8 里的 15,39、16,40、25,39。W45N7 没有自己的铺路阶段。停着时不放 W45N8 的路工地。
- `src/rooms/w47n8/config.js` 与 `index.js`、`roles.js`、`threat.js`、`remote_roads.js`：两个源和站位，`ours7` 要 `by === 'Misaki'` 且 `endTime` 晚于现在 200 tick。搬运工的 1 WORK 只留交叉引用。躲避是 `w8flee` 的 20 tick，人靠 Spawn2 15,18，不读外矿状态机的 SAFE。
- 交叉读了 `docs-site/mechanisms/haul.md`、`defense.md`、`spawn.md`、`loop.md`、`reference/rooms.md`、`now.md` 和页脚。搬运页的 24C12M 和 1 个 WORK、防御页的状态机和 20 tick，都还对得上，没有改那些页。防御页开头「不在 SAFE 时矿工和搬运工暂停，停在家里」说的是家的两条线；W47N7 的矿不走这道门。这一轮没有改防御页，外矿页把两道门分开写了。

旧页上改掉的地方：

- 「家的预定者低于 2000 就孵，容量够 1300 就等两颗、不等一颗」拆开。等 1300 还要剩余不少于 1000。低于 1000，或者容量本身不到 1300，W45N8 够 650 就出一颗。W45N7 永远等 1300。
- 「W47 大约 1000 时家可以补一只」拆开。我们的预定低于 2500 才孵，别人的低于 260。W47 容量到 1800 才自己孵。家在 W47 没准备好时补；W47 准备好了，只有我们的预定且低于 1000 才也要。不看出生点忙不忙。`reserve7` 不攻击控制器。
- 走路出口写上了：0,23，然后 27,49。
- W47N7 的矿不从家出。容器在站位 18,17 和 31,34。24,14 是守卫的落点。停车 16,20 和岗位 27,19 分开。停矿不靠 SAFE，靠 20 tick 的躲避。
- `Memory.remotes.<房间>.off` 只刹家的两条线，不关 W47 的矿，也不关防御 creep。
- 提前回去写成 15% 与 30%，并且 WAIT 里没有。人进家之后矿工和搬运工改做家务，不是都停在 46,21。
- W45N7 的 5 只、60 与 240、借路和 22,15、口袋等候，按现在的配置写上。`placeRoads` 只放 2,12。

## 下一轮

加深 `docs-site/mechanisms/loop.md`（CPU 与主循环）。实验室页和矿物页各只用了一句：W47N8 不调用 `labs.run`。Link 页写了 W47 的 `linkRun` 在 `towerRun` 里，主循环那一页还没有把这件事展开。对照 `src/main.js`，把家和 W47 在一拍里各跑哪一段写清楚。外矿管理器、道路、以及桶低于 2000 时谁先跑，已经有一段，缺的是为什么这样切，以及 W47 的 link 和实验室为什么不在家的那一支里。

## 再往后

按读者会先问的顺序。已有的页面都还短的，缺的是为什么和边界，不是再开一篇日志。

1. **CPU 与主循环**（下一轮，加深 `loop.md`）。见上一节。
2. **部署约定**。`deploy.md` 已经有一页。只做措辞上的打磨，继续保持公开、不含令牌。
3. **还没有独立页面的**。布局：现行 v2。移动：`src/utils/move.js` 的路径缓存和脱困，加上 W47 的 `yieldPost`。`yieldPost` 把 filler 的空闲格 34,32 抬到代价 4，房间里的路程在 32,32 那格平地空着时走那里。#64 的满载停驻写在搬运页。`289a7f06` 在枢纽容器被占时抬高 32,32 和 33,33 的代价，留在这一页，不要插进 link、升级或搬运。`C.SPAWN` 仍是 15,18。延伸 32,34 没有挪。升级页没有把出生口袋写成未解决的现行行为。指挥官接管：`Memory.cmd` 没设置时不接管。实验室页只写了 `react` / `idle` / `hold` 怎么让自动反应让开，矿物页只写了终端被占用时这一拍不送，link 页只写了 `consumeLink` 让自动传送让开，都没有把指挥官写成一篇。
4. **日期日志不要再进给人读的入口**。`STRATEGY`、`docs/REMOTE_*.md`、路线、RCL7 这类日期记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。
5. **站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app 。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。
6. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
