# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-17（Asia/Hong_Kong）。对照的游戏代码仍是 LIVE `85c19c2e`。其后的仓库提交没有改 `src/`。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。

## 这一轮做了什么

加深了 `docs-site/mechanisms/haul.md`（搬运与能量）。标题没改，侧栏标签也不用改。

对照这些源码，没有把升级工只数、20k/300 tick，或 W47 的软顶闩再讲一遍：

- `src/roles/hauler.js`：`assignPickup` 按名字、离存储门 36,32 更远的优先，跳过贴着存储的矿工。源 A（31,12）挨着源 link 30,11 时立刻 `legacyPickup`，容器 ≥100 仍拿，不等 60 tick。等的三条提前离开只属于没有源 link 的那条路。`noUpgrade` 时改到管理者站位 36,30 抽枢纽 link。卸货一趟一个 `memory.fl` / `memory.dst`。低能量线是有女王 30%、没有 90%、攒防御或战时或 `defenseFill` 为 100%。已有卸货点、女王还在、又不是告警时不改去补延伸。塔只在没有女王或告警时进名单，600 / 900。控制器容器低于 1000 且没在先存银行时挪到最前。`defLow` 且存储空位 >10000 时存储排在控制器前。`noUpgrade` 且有存储时控制器容器不进名单。
- 空手顺序：`mineralRun`（1000 或容器空位 ≤200；手里已标的矿物在 `defLow` 下也送完，不新开）、`boostHaul`（存储能量取完须仍 ≥ `STOR_SAFE` 20000）、`termPark(false)`、`labRun`、`termPark(true)`、`salvage.dump`。`termPark` 不取能量。实验室旗标关着时，紧/松终端和实验室日常不跑；boost 看风筝兵，不看旗标。
- 三道读法分开写，并画在 `HaulReads.vue`。`queen.storageFloor` 用 `threat.reserve` 或能量容量做 base，再和 `walls.defReserve()` 取较大值；`defReserve()` 是 `reserveE`，否则 0。`termPark` 用 `reserveE`，否则 15000。`mineralRun` 和「先存银行」用 `defLow`，储备为 0 时为假。写成 0 和键不在，在各自的 `||` 里是同一种结果。
- `src/roles/queen.js`：容量 ≥1300 两只，中心 35,26 与 32,32，只剩一只覆盖两片。取存储、终端、35,24、34,34、枢纽 link，只取本片缺口。房间满了才把高于 `storageFloor` 的能量送进枢纽或控制器容器。战时地板为 0。身体不在这页推导，链到孵化。`STATIONARY_FILL` 关着，`filler.js` / `manager.js` 不是家的现行路径。
- `src/managers/spawn.js`：`homeHaulMineral` 在 `labs.cfg` 为真时把家搬运工从 450（6C3M）抬到 1200（16C8M）。`parkTask` 本身也要旗标，所以终端只是满、实验室没开，身体不放大。快照里家的 KO 旗标开着，现行身体是 16C8M。RCL6+ 且 link ≥3 时只要 1 只；第四座 link 要 `STATIONARY_FILL` 才会把这只拿掉。
- `src/managers/walls.js` 的 `defReserve` / `defLow` / `noUpgrade`，`src/managers/boost.js` 的 `STOR_SAFE` 与 `haulTask`，`src/managers/labs.js` 的 `cfg` / `task` / `parkTask` 和 3000 缓冲、6000 空位。
- `src/rooms/w47n8/fill.js`：条带、POST 34,32、存储优先。`want` 在职责容量 >2500 时要 2 只。身体 2C:1M，组数约 75% 职责容量，夹在 2 到 12。`FILL_CLUSTER` 不在 `config.js` 里，filler 不去 Spawn2 15,18。灌 link：存储 ≥15000 才开始；≥25000 才看电池 <800 或枢纽 <200；15000 到 25000 只预热枢纽 <200。
- `src/rooms/w47n8/index.js` 与 `roles.js`：`hFloor` 在 `Memory.ops.w8model.links` 为真时是 2，否则 3。link 时期上限平时 3，`looseE` >2000 时 4。超过 1200 才加。这和枢纽建筑在不在不是同一个旗标。卸货时 filler 占着枢纽延伸；存储缓冲不够，或存储 <25000 且控制器容器 ≥1200，先存存储。W47N7 的 `w8rhauler` 用 1 个 WORK 换 1 个 CARRY。
- `src/managers/remote.js` 的 `rhE: 1800` 与 `spawn.js` 的 `roadHauler(..., 16)`：阶段晚于 W45N8 且容量 ≥1200 时是 24C12M。W45N7 不走这具身体。

加了 `HaulOrder.vue`（空手时的六步）和 `HaulReads.vue`（三道读法），并在主题里按 `UpgradeFloors` 的方式注册。`FlowDiagram` 里「过了防御地板才进控制器」改成地板以下存储排在控制器容器前面。

旧页上改掉的地方：家搬运工不总是 6 CARRY、3 MOVE；源 A 有 link 时不等容器；60 tick、半容量和控制器容器 1000 是三条不同的提前离开；卸货不会因为能量晃过 30% 就在半路改道；三道地板缺省不能合成一句；W47 的 filler 有条带、两只的门槛和 15000/25000 两段灌 link；`FILL_CLUSTER` 没开，filler 不到 Spawn2；本地搬运工的地板在 link 旗标下是 2，不是「枢纽 link 开着就三只左右」。

交叉链接只改了说法会和这三道读法打架的句子：`upgrade.md`、`now.md`、`reference/rooms.md`、`minerals.md`。没有改 `src/`。

## 下一轮

加深 `docs-site/mechanisms/defense.md`（防御与威胁）。

为什么接着做这一页：地板和谁在搬已经写开，下一问是有敌人时能量和孵化让给谁。`defense.md` 仍是短的总览。要写清 Invader 与 Invader Core、威胁状态机、塔、外矿防御预算。`docs/DEFENSE_NOVICE.md` 只当作历史附录留在仓库里，不要放进导航。不要把这一页写成新的防御代码。

## 再往后

按读者会先问的顺序。已有的页面都还短，缺的是为什么和边界，不是再开一篇日志。

1. **防御（现行）**（下一轮，加深 `defense.md`）。见上一节。
2. **实验室与强化**。加深 `labs.md`，对照 `src/managers/labs.js` 和 `src/managers/boost.js`。搬运页已经写了空手时的插入顺序和 20000，加深时不要把那六步再抄一遍。
3. **矿物与终端**。加深 `minerals.md`。公开文档必须写明：市场订单是玩家的决定，机器人默认不下单。现有「没有市场」一节已经靠近这句话，加深时保持这个说法，不要写成代码会自己挂单。搬运页已经把家的 `termPark` 缺省和 W47 矿物容器 500 点到了。
4. **Link 与枢纽**。加深 `links.md`。升级页已经用了家的 400、W47 枢纽到控制器的距离 19。搬运页已经写了谁灌枢纽。加深时不要把升级工只数或 filler 条带再写一遍，把传送顺序写清楚。
5. **远程采矿**。加深 `remotes.md`，让 W45N8、W45N7、W47N7 停在这一页上。搬运页只留了 24C12M 和 W47N7 的那 1 个 WORK。不要把过时的单房间日志再分出去。
6. **CPU 与主循环**。加深 `loop.md`，对照 `src/main.js`。
7. **部署约定**。`deploy.md` 已经有一页。只做措辞上的打磨，继续保持公开、不含令牌。
8. **还没有独立页面的三件**。布局：现行 v2 和 `docs/LAYOUT.md`、`docs/LAYOUT_V2.md` 以及 `docs/` 里的布局图。移动：`src/utils/move.js` 的路径缓存和脱困阶梯。指挥官接管：`docs/COMMANDER.md` 与 `Memory.cmd`；要写明没设置时它不接管。
9. **日期日志不要再进给人读的入口**。`STRATEGY`、路线、RCL7、矿物路线这类日期记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。
10. **站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。
11. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把第三只升级工写成已经实现的新规则。只描述当前代码。家的第三只现在就是地板加 5000、连续 300 tick 这道门；没有另一套还没写进 `src/` 的政策。
