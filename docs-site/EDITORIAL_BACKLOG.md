# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-17（Asia/Hong_Kong）。对照的游戏代码仍是 LIVE `85c19c2e`。其后的仓库提交没有改 `src/`。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。

## 这一轮做了什么

加深了 `docs-site/mechanisms/spawn.md`（孵化与身体）。

- 家的身体表按 `src/managers/spawn.js` 核对过。和平时期的女王是 16 CARRY、8 MOVE（预算 1200）；配方上限 24 CARRY、12 MOVE 只在按当前能量来生时出现。`homeHaulMineral` 切换的是同一只搬运工的预算（450 或 1200），不是第二个角色。
- 加了家的队列图 `docs-site/.vitepress/theme/components/SpawnQueue.vue`，并在主题里按 `FlowDiagram` 的方式注册。
- 写进了近满（容量减 100）、第 2 到第 4 只防御身体的 `extrasOk`（15000；W47N8 的 `softCap2` 为真时 25000）、提前换班、出生方向，以及连续 300 tick 没有近满时的缩小。
- 说明了 `spawnOrder` 的名次，和真正孵化时平民放在后勤之后。基础升级名额要抢在外矿前面，靠的是存储高于 `reserveE` 再加 10000 的那一档。第三只升级工和 W47 的闩只留链接，指向 `/mechanisms/upgrade`。
- W47 一节按 `src/rooms/w47n8/index.js` 的 `bodyFor` 和 `spawnRun` 加厚，没有把那份长注释搬进手册。
- 装上了这份备忘。`README.md` 和 `docs-site/mechanisms/deploy.md` 里关于上传令牌的句子，改成「令牌只留在执行上传的那台机器上，不进仓库」。

## 下一轮

加深 `docs-site/mechanisms/upgrade.md`（升级者与能量地板）。

为什么先做这一页：操作时问得最多的就是升级工为什么不加；孵化那一页已经把家的第三只和 W47 的闩指到这里；这一页现在大约 51 行，短于它要托住的规则。下一轮要补上缺的「为什么」和边界，并加一张同样安静的地板图。对照这些源码，不要把整条孵化队列再讲一遍：

- `src/managers/spawn.js` 里的 `upExtraTick` / `extraUpReady`（地板加 5000、300 tick、`ctlEma`，以及容量减 1550）
- `src/roles/queen.js` 的 `storageFloor`
- `src/managers/upgfeed.js`
- `defLowUpgraders` 的滞后
- `src/rooms/w47n8/index.js` 的 `upgTarget`：`UP_STICKY` 40000 连续 500 tick，`UP_REARM` 30000，`threatSoft`，有工地时压到 1，`upgfeed` 与站位

只描述现在的规则。不要在文档里把 15000 的地板改掉，也不要把第三只升级工写成已经改过的代码。

## 再往后

按读者会先问的顺序。已有的页面都还短，缺的是为什么和边界，不是再开一篇日志。

1. **升级者与能量地板**（下一轮，加深 `upgrade.md`）。见上一节。
2. **搬运与能量**。加深 `haul.md`。已经有女王地板和 W47 filler 的轮廓。还缺：女王地板和搬运工 `reserveE` 缺省值为什么不是同一个读法，矿物和实验室插入的顺序，W47 的 filler 与 link 各管哪一段。
3. **防御（现行）**。加深 `defense.md`。Invader 与 Invader Core、威胁状态机、塔、外矿防御预算。`docs/DEFENSE_NOVICE.md` 只当作历史附录留在仓库里，不要放进导航。
4. **实验室与强化**。加深 `labs.md`，对照 `src/managers/labs.js` 和 `src/managers/boost.js`。
5. **矿物与终端**。加深 `minerals.md`。公开文档必须写明：市场订单是玩家的决定，机器人默认不下单。现有「没有市场」一节已经靠近这句话，加深时保持这个说法，不要写成代码会自己挂单。
6. **Link 与枢纽**。加深 `links.md`。
7. **远程采矿**。加深 `remotes.md`，让 W45N8、W45N7、W47N7 停在这一页上。不要把过时的单房间日志再分出去。
8. **CPU 与主循环**。加深 `loop.md`，对照 `src/main.js`。
9. **部署约定**。`deploy.md` 已经有一页。只做措辞上的打磨，继续保持公开、不含令牌。
10. **还没有独立页面的三件**。布局：现行 v2 和 `docs/LAYOUT.md`、`docs/LAYOUT_V2.md` 以及 `docs/` 里的布局图。移动：`src/utils/move.js` 的路径缓存和脱困阶梯。指挥官接管：`docs/COMMANDER.md` 与 `Memory.cmd`；要写明没设置时它不接管。
11. **日期日志不要再进给人读的入口**。`STRATEGY`、路线、RCL7、矿物路线这类日期记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。
12. **站点打磨**。排版、标题层级、交叉链接、图。生产用的 Vercel 地址还没有：没有 Vercel 项目，GitHub 仓库主页也还是空的。不要编一个 URL。`README.md` 可以继续留一句占位，直到真有地址。
13. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把第三只升级工写成已经实现的新规则。只描述当前代码。
