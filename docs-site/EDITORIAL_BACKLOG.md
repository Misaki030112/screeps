# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-18（Asia/Hong_Kong）。手册现在对照的仓库是 `a231a208`（`fix(w47n8): park a full filler on 34,32`，#64）。这一笔改过 `src/`。「现状」里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有按新提交重算。这一轮没有改 `src/`。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。

## 这一轮做了什么

加深了 `docs-site/mechanisms/minerals.md`（矿物与终端）。标题和侧栏标签没改。没有新组件。停放的紧和松不再在这一页重讲，只留指向实验室的交叉引用。

对照这些源码写的。搬运的六步空手顺序没有再抄。20000、家的防御地板、实验室的 `ACT_HOME_STOR` 都没有拿到这一页当发送门槛。

- `src/rooms/w47n8/index.js`：`mineralSend`、`layoutRun`（每拍调用）、`spawnRun` 里 `w8mminer` 的位置、`bodyFor`。`LEAN_ARM` 15000。`SEND_BATCH` 5000，`SEND_BATCH_THIN` 1000，`TERM_MIN_SEND` 100。目的地写死 `W46N8`，只送 `RESOURCE_KEANIUM`。批量是 `storE > 0 && storE < LEAN_ARM` 才用 1000，否则 5000。存储不在或能量为 0 走 5000。家终端空位减去 `TERM_FREE_TARGET` 之后不到 100 则 `homeFull`。手续费优先 `Game.market.calcTransactionCost`，否则 `ceil(amt * (1 - exp(-range/30)))`。相邻 1000 是 33，5000 是 164。注释里的「大约 165」是约数。能量不够就减半，掉到 100 以下是 `noE`。`cmd.blocks` 时不送。成功才记 `sent` / `lastAmt`。
- `src/rooms/w47n8/roles.js`：`termFuel`、`mineralRun`、`w8mminer`。`TERM_E_FLOOR` 1000，`TERM_FUEL_STOR` 500（注释写明以前是 2000）。`MIN_RUN` 500。只送进终端。`w8mminer` 没有目标为 0 就回收。
- `src/rooms/w47n8/config.js`：矿物 37,45，容器 37,44。`RCL6_MINERALS` true，`RCL6_LABS` false，`RCL7_INDUSTRY` false。
- `src/roles/mminer.js`：目标为 0 时走回出生点回收。站位来自 `positions.mineralMiner`。
- `src/managers/spawn.js`：`mineralCapped`、`T.mminer`。`Memory.ops.mineralCap` 不设或写成 0 就一直采。只作用于家里的 `T.mminer`。`defLow` 时 `T.mminer = 0`。身体 `(e-150)/100` 夹在 2 和 12，加 3 MOVE，没有 CARRY。
- `src/roles/hauler.js`：家的 `MIN_RUN` 1000，目的地 `terminal || storage`，`memory.mr` 粘到交货。门槛是 `min(MIN_RUN, 携带量)` 或空位不超过 200。防御地板以下不新开，已经标上的要送完。
- `src/managers/labs.js`：`TERM_FREE_TARGET` 是 1000 + 5000。`ACT_O_BUF` / `ACT_K_BUF` 是 3000。停放算法没有重写，指到实验室页。
- `src/layouts/W46N8.js`：萃取器 40,24，矿物容器 41,24，终端 35,31。RCL7 塔是 39,23。`src/utils/plan.js` 有一行旧注释还写着容器 39,23，和布局、`mminer.js` 冲突。手册跟布局。`plan.RCL6_MINERALS` 仍是 true，`RCL7_INDUSTRY` 仍是 false。
- `src/utils/cmd.js` 的 `blocks`：指挥官打开且这座终端有活指令时让出发送。这一阶段不执行 `terminal.send`。
- `src/main.js`：W47 在布局和塔之后 `continue`，不调用 `labs.run`。实验室页已经写了，这一页只用一句。
- `src/rooms/w47n8/fill.js` 的 `park`：只为搬运页那一句。填充职责空了且携带已满时停住，删掉 `_m`。人已经在 34,32 就留着。另一只满载 filler 看见格子上已有自己的 `w8filler` 就不踏进去。填充顺序、softCap、keep、15k、`C.SPAWN` 15,18、延伸 32,34、`yieldPost`、取能量的走法都没有改。
- `src/` 里 `Game.market` 只出现在 `calcTransactionCost`。没有 `deal`，没有 `createOrder`。
- 测试只用来核对边界，没有写进正文：`tests/w47n8_mminer.js`、`tests/mineral_cap.js`、`tests/w47n8_filler_park.js`。
- 交叉读了 `docs-site/mechanisms/labs.md`、`haul.md`、`spawn.md`、`plan.md`、`reference/rooms.md`，以及 `now.md` 和页脚里的对照提交。

旧页上改掉的地方：

- 「存储能量低于 15000 时最多 1000，否则最多 5000」改成：看的是 W47 自己的存储。`storE > 0 && storE < LEAN_ARM` 才是 1000。存储不在，或能量是 0，走 5000。15000 整也走 5000。这 15000 标明是 W47 的 `LEAN_ARM`。
- 家终端不是「有空位就发」。空位先减 6000，剩下不到 100 则 `homeFull`。4300 的那次写成注释里的例子，不写成正在发生的巡逻。7000 空位、批量上限 5000 时，实际只送 1000。
- `termFuel` 原来整段没有。补上：终端能量到 1000 不做；终端里至少 100 的非能量在等才搬能量；存储至少 500 才取；不搬矿物；旗标关着休眠。
- 家里的停放两档从这一页拿掉，只留指向实验室的交叉引用。6000 在这一页是发送预留。
- `mineralCap` 写明只作用于家的 `mminer`。W47 的 `w8mminer` 不读这个键。不设或写成 0 就一直采，没有默认数字。
- 家的矿工在目标变成 0 时回收，不只是不再孵。W47 的矿工没有这段回收。容器空位大于 400 在 W47 只是孵化门。
- 家的坐标写成萃取器 40,24、站位和容器 41,24、终端 35,31。不写 39,23。
- 500 和 1000 的差写在这一页：门槛还要和携带量取小。家在实验室身体下携带 800，W47 满预算携带 500。
- 「没有市场」保持：订单是人的决定，代码默认不下单。

`now.md` 只把手册基线改成 `a231a208`（#64）。百分比和 2026-11-17 的快照没动。页脚 `Layout.vue` 的对照提交跟着改成同一个 SHA，否则每页底部仍写着 `c6d43491`。`reference/rooms.md` 里「W47 发送批量」那一格跟着改了，否则查表的人仍会读到「存储低于 15000 就 1000」。`haul.md` 只加了一句满载停驻。没有改 `src/`、`scripts/`、`dist/`。

写这一轮时，`origin/master` 的 tip 已经是 `289a7f06`（枢纽容器 33,33 被占时，把 32,32 和 33,33 的代价抬高）。那一笔在 `a231a208` 之后，没有改 `mineralSend`、`termFuel` 或 `park`。手册基线按本轮要求停在 `a231a208`，搬运页没有改 `yieldPost` 的那句。

## 下一轮

加深 `docs-site/mechanisms/links.md`（Link 与枢纽）。升级页已经用了家的 400、W47 枢纽到控制器的距离 19。搬运页已经写了谁灌枢纽。下一轮不要把升级工只数或 filler 条带再写一遍，把传送顺序写清楚。

## 再往后

按读者会先问的顺序。已有的页面都还短的，缺的是为什么和边界，不是再开一篇日志。

1. **Link 与枢纽**（下一轮，加深 `links.md`）。见上一节。
2. **远程采矿**。加深 `remotes.md`，让 W45N8、W45N7、W47N7 停在这一页上。搬运页只留了 24C12M 和 W47N7 的那 1 个 WORK。防御页只留了状态机、巡逻和「防御从哪间房的出生点出」。不要把过时的单房间日志再分出去。
3. **CPU 与主循环**。加深 `loop.md`，对照 `src/main.js`。实验室页和矿物页各只用了一句：W47N8 不调用 `labs.run`。
4. **部署约定**。`deploy.md` 已经有一页。只做措辞上的打磨，继续保持公开、不含令牌。
5. **还没有独立页面的**。布局：现行 v2。移动：`src/utils/move.js` 的路径缓存和脱困，加上 W47 的 `yieldPost`。`yieldPost` 把 filler 的空闲格 34,32 抬到代价 4，房间里的路程在 32,32 那格平地空着时走那里。#64 的满载停驻这一轮只在搬运页补了一句，移动页仍待写。`289a7f06` 在枢纽容器被占时抬高 32,32 和 33,33 的代价，也留在这一页，不要插进升级或搬运。`C.SPAWN` 仍是 15,18。延伸 32,34 没有挪。升级页没有把出生口袋写成未解决的现行行为。指挥官接管：`Memory.cmd` 没设置时不接管。实验室页只写了 `react` / `idle` / `hold` 怎么让自动反应让开，矿物页只写了终端被占用时这一拍不送，都没有把指挥官写成一篇。
6. **日期日志不要再进给人读的入口**。`STRATEGY`、路线、RCL7 这类日期记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。
7. **站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app 。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。
8. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
