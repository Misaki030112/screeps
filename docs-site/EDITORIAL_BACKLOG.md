# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-20（Asia/Hong_Kong）。上一篇是移动页 #70，squash 提交 `9a2db9f9`，已经在 master 上。手册现在对照的游戏代码仍是 `289a7f06`（`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -- src/` 的最新一笔就是它。不要在页面上写成更新的 LIVE。这一轮没有改 `src/`。`now.md` 里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算，这一轮也没有改 `now.md`。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。卡住 30 的那一行只是控制台的一行字，不要写成有人在仓库外盯着。

## 这一轮做了什么

新开了 `docs-site/mechanisms/layout.md`，地址 `/mechanisms/layout`。导航标题是「布局与印章」，放在「移动与寻路」后面、「升级、地板与 softCap」前面。导读的机制名单在「移动」后面加了「布局」。导读「两套出生点」、搬运、移动、link、孵化、规划、房间表各加了一句交叉链接，没有重讲能量、填充或寻路。

两张图：`HomeStamps.vue`（印章 A/B/C；F 标成预留，没有画成已经上岗），`HubCore.vue`（核心这一角：32,32 平地，32,33 link，33,32 终端，33,33 容器，34,32 岗位，33,34 旧 link 的路，34,33 核心，35,32 存储，出生点仍在 15,18）。`theme/index.ts` 注册了这两个组件。样式加在 `custom.css`，沿用 `plate`、`node`、`legend`。编辑备忘仍被 `srcExclude` 排除。

对照这些文件写的。游戏代码没有改。坐标和旗标用脚本对过 `plan.get('W46N8')` 合并之后的结果，不单看印章字母。

- `src/layouts/W46N8.js`：`version` 2，`generatedBy` 是 `tools/plan_v2.py + tools/export_v2.py`。印章 A 的 S 是 **35,28**，K 是 **35,24**，L 是 **35,26**。印章 B 的 S 是 **30,34**，K 是 **34,34**，L 是 **32,34**。印章 C 的字母 S 在 **30,23**，字母 K 在 **30,27**。`rcl` 里 RCL1 出生点 **35,28**，RCL7 **30,34**，RCL8 **35,29**。30,23 在 RCL8 是延伸。30,27 在合并后的计划里是 RCL6 的路，容器名单里没有它。存储 **37,31**，终端 **35,31**，提取器 **40,24**。`remove`：容器 38,32 从 RCL4，容器 31,12 从 RCL6。`routes` 和 `positions.queenRoute` 没有被寻路或女王读到。
- `src/utils/plan.js`：`STATIONARY_FILL` 仍是 false。关着时先删掉 `rcl` 里全部 link，再写入 `LINK_PLAN`：枢纽 37,29 RCL5，控制器 30,31 RCL5，源 A 30,11 RCL6，32,34 RCL7，30,25 RCL8，35,26 RCL8。稿子里 RCL5 的 35,26 因此不在 5 级放下。`RCL6_MINERALS` 是 true，RCL6 实验室 34,22 / 35,21 / 33,21 留着。`RCL7_INDUSTRY` 是 false，工厂和 RCL7 起的实验室从会放的名单里删掉。powerSpawn **36,33**、nuker **38,23**、observer **33,31** 仍在 RCL8 名单里。站位集合二十格（十二个 F、manager 36,30、五格升级工、两格矿工），代价 20。矿物矿工 41,24 不在里面。filler 和 manager 的孵化目标是 0。
- `src/managers/layout.js`：每 25 拍，或等级变了，或拆过东西留下 `layoutKick`。最多五个工地。有日志就 `move.invalidate`。计划外工地拿掉；人放下的实验室和工厂工地留下。
- `src/rooms/w47n8/layout.js` 与 `config.js`：`CORE` **34,33**，存储 **35,32**，`ORDER.link` **32,33**，终端 **33,32**，`C.HUB_CONT` **33,33**，`RETIRED_HUB_LINK` **33,34**。`hubLinkPos()` 返回 32,33。文件头把 32,33 说成空口袋的那句是旧理由，页面按现行 link 写。`ORDER.container` 只有 **13,26**。`ORDER.spawn` 是 **34,30**、**33,30**、**39,30**，放置顺序。`C.SPAWN` 仍是 **15,18**。`moveRun` 在没有 `Memory.ops.w8move` 时直接返回。`RCL6_LABS` 和 `RCL7_INDUSTRY` 都是 false。`RCL6_MINERALS` 和 `HUB_LINK` 是 true。`layoutRun` 拆 33,34 上的 link 工地；link 建筑还在，或工地还在，就不放 32,33。W47 这一圈不调用 `move.invalidate`。
- `src/rooms/w47n8/roads.js`、`src/layouts/w8link.js`：32,32 不在路表。33,33、33,34、34,32、34,33、33,31、35,31 在路表。家这一侧的 w8link 跳过 34,34，因为计划里那一格是容器。

## 下一轮

**指挥官接管**（`Memory.cmd`）。实验室、矿物、link、主循环只各自提到被让开的那一个点：反应让开、终端被占用时这一拍不送、`consumeLink` 让自动传送让开、武装时谁先被看、以及 `consumeCreep` 会压过逃跑和角色。还没有一篇把指挥官写成一件事。`Memory.cmd` 没武装时，什么都不接管。

## 再往后

按读者会先问的顺序。已有的页面缺的是为什么和边界。不要再开一篇日志。

1. **站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app 。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。
2. **日期日志不要进给人读的入口**。`STRATEGY`、`docs/REMOTE_*.md`、`docs/CPU.md`、路线、RCL7 这类记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。`docs/CPU.md` 里仍有一句房间视觉在桶低于 2000 时不画，和现在的主循环页不一致。那个文件留在仓库里，不要为了把它改对就搬进导航。
3. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
4. **可选，这一轮不做。** 建造、修理和城墙落在哪；或者给 `now.md` 做一次注明日期的重算。两件都留到以后，不要塞进布局这一页。
