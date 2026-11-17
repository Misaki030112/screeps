# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-18（Asia/Hong_Kong）。手册现在对照的仓库是 `c6d43491`（`fix(w47n8): keep spawn-pocket trips off the filler post`，#61）。这一笔改过 `src/`。「现状」里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有按新提交重算。这一轮没有改 `src/`。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。

## 这一轮做了什么

加深了 `docs-site/mechanisms/labs.md`（实验室与 boost）。标题和侧栏标签没改。加了 `LabGates.vue`（15000、20000、3000、6000 四道门），在主题里按 `DefenseEnergy` 的方式注册，并给 `.gates` 加了两列。

对照这些源码写的。搬运的六步空手顺序没有再抄。20000 在这一页是 `STOR_SAFE`，不是搬运地板。15000 在这一页是 `ACT_HOME_STOR`。

- `src/managers/labs.js`：`cfg`、`roles`、`task`、`parkTask`、`readyObs`、`run`。`R` 只有 KO、LO、UH、OH、ZO、UO。`PROPOSE_K` / `PROPOSE_O` 是 1000。`ACT_HOME_STOR` 15000，`ACT_K_BUF` / `ACT_O_BUF` 3000。`TERM_FREE_TARGET` 是 1000 + 5000。`READY_EVERY` 是 20。
- `src/managers/boost.js`：`isKite`、`pickLab`、`plan`、`haulTask`、`blocksReaction`、`hold`。角色是 defender、guard、rdef、w8defender、w8guard。要有未强化的远程，且没有攻击部件。`PART_KO` 30，`PART_E` 20，`KO_FILL` 900，`STOR_SAFE` 20000。19 远程是 570 KO、380 能量，源码注释里的例子。
- `src/roles/hauler.js` 只用来确认谁执行：`labRun` 跑 `task`，`termPark` 跑 `parkTask`，`boostHaul` 跑 `haulTask`，并且存储低于 `reserveE`（否则 15000）时不新开停放。六步顺序留在搬运页。
- `src/main.js`：W47N8 在布局和塔之后 `continue`，不调用 `labs.run`。`src/utils/plan.js` 的 `RCL7_INDUSTRY` 仍是 false，RCL7 的工厂和实验室不自动放；`src/managers/layout.js` 不删人已经放下的实验室和工厂工地。`src/rooms/w47n8/config.js` 的 `RCL6_LABS` 仍是 false。
- `src/layouts/W46N8.js`：RCL6 实验室是 34,22、35,21、33,21，和 `labs.js` 注释一致，彼此距离不超过 2。RCL7 还写着 33,22、34,20、34,23。34,20 与 34,23 距离是 3。快照里的六座没有按现场坐标再对一次，页上把多出来的三格写成布局，不写成已经核实的站位。
- `src/utils/cmd.js` 的 `consumeLab`：`react` 先处理，`idle` / `hold` 跳过自动反应。不写 `Memory.ops.labs`。
- 交叉只读了 `docs-site/mechanisms/haul.md`、`minerals.md`、`defense.md`，以及 `now.md` 里会和这页打架的那一句。

旧页上改掉的地方：

- `roles` 不是「到另外两座的距离都不超过 2」再取那两座。它找一座离其余每一座都不超过 2 的当输出，其余按 (x, y) 排序后 `.slice(0, 2)` 当输入。找不到则 `roles` 为空，`run` 返回 0，`task` 也是空的。三座实验室都在范围内时，旧句子才和这条重合。
- `task` 的顺序补全了：输入里的错误矿物先倒回终端，然后才是「低于 1000 且终端至少还有 100」的灌料，两座输入都没有这两件事，输出不少于 1000 才倒回终端。`task` 只走终端和实验室。停放是另一个 `parkTask`。
- `parkTask` 分成紧和松。紧只在终端空位低于 6000：多余的氧，然后多余的钾，然后全部 KO。松的时候先把存储里的氧、钾补回终端的 3000，再按同样顺序把多余的收走。不搬能量，也不把钾或氧抽到 3000 以下。KO 没有 3000 的缓冲。
- `readyObs` 只跑 W46N8。旗标关着时每 20 tick 重数，中间沿用上一份，刚关掉的不到 20 tick 里理由可能仍是 `active`。`why` 是 active、noLabs、noTerm、noK、noO、ready。`propose` 为 1 也不写旗标。`actOk` 和 `propose` 分开。`kBuf` 只看终端的钾；`oBuf` 是终端加存储的氧。提出来让人看的 1000 是终端加存储，两种都算。旧页这处不对称是对的，这一轮写了为什么，没有收成「终端里各 3000」。
- 反应不看存储能量。低于 15000 不冻结已经装进输入的原料。`ACT_HOME_STOR` 不拦搬运工。搬运工的 15000 是 `reserveE` 缺省，仍指到搬运页，没有把六步或三道地板重讲一遍。
- 指挥官：`Memory.cmd` 打开时，输出上的 `react` 先处理，自动反应跳过；输出或输入上的 `idle` / `hold` 也跳过。不写旗标。
- `blocksReaction` 只在计划是 `wait` 或 `ready`、并且 `pick.pause` 时停下 `runReaction`。`pause` 只在没有空闲实验室、不得不用输出时才为真。空闲实验室按 `memory.bl` 粘住，否则取 KO 最多的一座。有攻击部件，或不在 W46N8，记下 `noBoost`，不占实验室。
- 填充：殖民地 KO 不少于 900 就填到 900，否则只填到部件数乘 30。能量是部件数乘 20。`fromStor = max(0, 存储能量 - 20000)`。终端能量和实验室里已有的能量仍算。三笔不够就是 `skip`，不把存储取到 20000 以下。`haulTask` 先 KO（终端、存储、其他实验室），再能量（存储高出 20000 的部分，然后终端）。谁去跑，指到搬运页。

`now.md` 里「15000 让 actOk 变成 0，并让矿物停放让路」改成两道：`ACT_HOME_STOR` 只进观察清单，搬运工的地板另见搬运页。同一页把「目标库存是 900」改成：殖民地 KO 不少于 900 才填到 900，不够就只填这次要用的。百分比和对照提交没动。`minerals.md` 没有改。没有改 `src/`、`scripts/`、`dist/`。

## 下一轮

加深 `docs-site/mechanisms/minerals.md`（矿物与终端）。为什么钾送回家，而不是在 W47 做反应；一次送 1000 还是 5000；`TERM_FREE_TARGET`；以及公开规则：市场订单是人的决定，机器人默认不下单。现有「没有市场」一节已经靠近这句话，加深时保持这个说法，不要写成代码会自己挂单。

实验室页已经写了家里的停放怎么分紧和松，以及 6000 为什么是 1000 的 KO 倒出加 5000 的下一次钾。矿物页不要把那两档停放再讲成一篇，把发送本身和「为什么不在 W47 反应」写清楚。

## 再往后

按读者会先问的顺序。已有的页面都还短的，缺的是为什么和边界，不是再开一篇日志。

1. **矿物与终端**（下一轮，加深 `minerals.md`）。见上一节。
2. **Link 与枢纽**。加深 `links.md`。升级页已经用了家的 400、W47 枢纽到控制器的距离 19。搬运页已经写了谁灌枢纽。加深时不要把升级工只数或 filler 条带再写一遍，把传送顺序写清楚。
3. **远程采矿**。加深 `remotes.md`，让 W45N8、W45N7、W47N7 停在这一页上。搬运页只留了 24C12M 和 W47N7 的那 1 个 WORK。防御页只留了状态机、巡逻和「防御从哪间房的出生点出」。不要把过时的单房间日志再分出去。
4. **CPU 与主循环**。加深 `loop.md`，对照 `src/main.js`。实验室页只用了一句：W47N8 不调用 `labs.run`。
5. **部署约定**。`deploy.md` 已经有一页。只做措辞上的打磨，继续保持公开、不含令牌。
6. **还没有独立页面的**。布局：现行 v2。移动：`src/utils/move.js` 的路径缓存和脱困，加上 W47 的 `yieldPost`。`yieldPost` 把 filler 的空闲格 34,32 抬到代价 4，房间里的路程在 32,32 那格平地空着时走那里。`C.SPAWN` 仍是 15,18。延伸 32,34 没有挪。升级页没有把出生口袋写成未解决的现行行为，所以这一笔留在移动那一页，不插进升级。指挥官接管：`Memory.cmd` 没设置时不接管。实验室页只写了 `react` / `idle` / `hold` 怎么让自动反应让开，没有把指挥官写成一篇。
7. **日期日志不要再进给人读的入口**。`STRATEGY`、路线、RCL7 这类日期记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。
8. **站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app 。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。
9. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
