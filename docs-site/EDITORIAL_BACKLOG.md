# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-17（Asia/Hong_Kong）。对照的游戏代码仍是 LIVE `85c19c2e`。其后的仓库提交没有改 `src/`。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。

## 这一轮做了什么

加深了 `docs-site/mechanisms/upgrade.md`（升级、地板与 softCap）。标题没改，侧栏标签也不用改。

对照这些源码，没有把家的孵化队列再讲一遍：

- `src/managers/spawn.js`：`upExtraTick`（地板加 5000 / 加 3000，滑动平均 1200 / 700，连续 300 tick）、`extra = floor(ctlEma / 700)` 在 1200 是第三只、到 1400 同一行会要第四只、五格座位封顶、容器 2000 到不了第五只。`extraUpReady` 在 RCL7 是容量减 1550 = 4050。`defLowUpgraders` 的 `held` 是 `walls.stepHeld`；台阶没停时是 0 或掉级那一只；台阶停住时 14500 进入、17550 离开，离开线盖住 1550 的身体再加 1000。`bank` / `roads` 和 `noUpgrade` 只点到会改只数。
- `src/roles/queen.js` 的 `storageFloor`：战时为 0；台阶停住时是 base 与 `reserveE` 的较大值；没停时还要加上墙的基金。`reserveE` 缺失时墙模块当 0，和搬运工矿物让路的缺省 15000 不是同一种读法，页内只点到搬运和现状，没有改写那两页。
- `src/managers/upgfeed.js`：每 5 tick 只写家的 `Memory.ops.upgFeed`。写清了 `war`、`remote_pause`、`floor_bank`、`ctl_starved`、`thin_surplus`、`waiting_feed`、`ok`，以及 `boundHint` 的 `energy`（两只 14 WORK 的 28 对着设计净收入约 26）。`allowExtra` 是地板加 5000 那个数，`upExtra` 才是门。
- `src/rooms/w47n8/index.js`：`energyBank` 先于闩（搬迁银行低于 11000，或 `leanBank`）。低于 15000 时掉级不足 20000 才要 1，否则 0。`dayofMiss` 看 33,30 和 22,7，目标为 1。软顶 25000 清除、低于 22000 再武装，不写只数。闩是 40000 连续 500 tick 到 3，低于 30000 回到 2。回收用 `leanBank` 而不是完整的 `energyBank`，所以 0 对 1、缺建筑、搬迁银行这三处出生和回收可以差一只。工地把 RCL7 收成 1，清完不跳。
- `src/rooms/w47n8/threat.js`：`threatSoft` 只是 `localOn`，窗口 1500。邻居的 `w8threatN` 不压升级工。
- `src/rooms/w47n8/config.js` 的站位 12,25 / 14,26 / 14,27，容器 13,26，link 13,25。枢纽 32,33 到控制器 link 距离 19，满载净输送大约 41。家的座位来自 `src/layouts/W46N8.js`：30,30（也是容器）、31,30、29,30、31,31、29,31，link 在 30,31。

加了地板图 `docs-site/.vitepress/theme/components/UpgradeFloors.vue`，并在主题里按 `SpawnQueue` 的方式注册。家的 15000 / 18000 / 20000 和 W47 的三对门分列，不画成一根滑杆。14500 / 17550 留在正文。

旧页上改掉的地方：第三只不是「门开了就只加一只」；地板下留一只只在台阶停住时成立，离开线是 17550 不是含糊的「有滞后」；W47 低于 15000 可以是 0，不是笼统的「最多一只」；缺出生点或塔、以及出生和回收可以不一致，原来没写。

## 下一轮

加深 `docs-site/mechanisms/haul.md`（搬运与能量）。

为什么接着做这一页：升级页把地板说成了几道门，下一问就是谁在搬、各读哪一个数。女王的 `storageFloor` 和搬运工矿物让路的 `reserveE` 缺省不是同一种读法，升级页只点了过去，没有把两条路写开。矿物和实验室插在捡能量之前的顺序，搬运页还只有一段。W47 的 filler 与 link 各管哪一段，升级页指向了搬运和 link，那两段本身还薄。对照 `src/roles/queen.js`、`src/roles/hauler.js`、`src/rooms/w47n8/fill.js` 和 `src/rooms/w47n8/roles.js`，把这三处补上。不要把升级工只数再讲一遍。

## 再往后

按读者会先问的顺序。已有的页面都还短，缺的是为什么和边界，不是再开一篇日志。

1. **搬运与能量**（下一轮，加深 `haul.md`）。见上一节。
2. **防御（现行）**。加深 `defense.md`。Invader 与 Invader Core、威胁状态机、塔、外矿防御预算。`docs/DEFENSE_NOVICE.md` 只当作历史附录留在仓库里，不要放进导航。
3. **实验室与强化**。加深 `labs.md`，对照 `src/managers/labs.js` 和 `src/managers/boost.js`。
4. **矿物与终端**。加深 `minerals.md`。公开文档必须写明：市场订单是玩家的决定，机器人默认不下单。现有「没有市场」一节已经靠近这句话，加深时保持这个说法，不要写成代码会自己挂单。
5. **Link 与枢纽**。加深 `links.md`。升级页已经用了家的 400、W47 枢纽到控制器的距离 19，加深时不要把升级工只数再写一遍，把传送顺序和谁负责灌枢纽写清楚。
6. **远程采矿**。加深 `remotes.md`，让 W45N8、W45N7、W47N7 停在这一页上。不要把过时的单房间日志再分出去。
7. **CPU 与主循环**。加深 `loop.md`，对照 `src/main.js`。
8. **部署约定**。`deploy.md` 已经有一页。只做措辞上的打磨，继续保持公开、不含令牌。
9. **还没有独立页面的三件**。布局：现行 v2 和 `docs/LAYOUT.md`、`docs/LAYOUT_V2.md` 以及 `docs/` 里的布局图。移动：`src/utils/move.js` 的路径缓存和脱困阶梯。指挥官接管：`docs/COMMANDER.md` 与 `Memory.cmd`；要写明没设置时它不接管。
10. **日期日志不要再进给人读的入口**。`STRATEGY`、路线、RCL7、矿物路线这类日期记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。
11. **站点打磨**。排版、标题层级、交叉链接、图。生产用的 Vercel 地址还没有：没有 Vercel 项目，GitHub 仓库主页也还是空的。不要编一个 URL。`README.md` 可以继续留一句占位，直到真有地址。
12. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把第三只升级工写成已经实现的新规则。只描述当前代码。家的第三只现在就是地板加 5000、连续 300 tick 这道门；没有另一套还没写进 `src/` 的政策。
