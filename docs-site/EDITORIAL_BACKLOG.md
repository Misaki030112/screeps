# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-19（Asia/Hong_Kong）。这是部署页 #69（`807854fc`）之后的晚间文档轮。手册现在对照的游戏代码仍是 `289a7f06`（`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -- src/` 的最新一笔就是它。不要在页面上写成更新的 LIVE。这一轮没有改 `src/`。`now.md` 里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算，这一轮也没有改 `now.md`。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。卡住 30 的那一行只是控制台的一行字，不要写成有人在仓库外盯着。

## 这一轮做了什么

新开了 `docs-site/mechanisms/move.md`，地址 `/mechanisms/move`。导航标题是「移动与寻路」，放在「搬运与能量」后面。导读的机制名单在「搬运」后面加了「移动」。主循环页「路径怎么缓存，不在这一页。」后面加了指向这一页的一句。搬运页满载停在 34,32 的那段末尾加了一句让路的交叉链接，没有重讲停驻。

两张图：`UnstuckLadder.vue`（卡住 2 / 4 / 8 / 30），`HubYield.vue`（枢纽这一角，代价 4 和 8，以及 32,34 不在对角上）。`theme/index.ts` 注册了这两个组件。样式加在 `custom.css`，沿用 `plate`、`node`、`legend`。编辑备忘仍被 `srcExclude` 排除。

对照这些文件写的。游戏代码没有改。

- `src/utils/move.js`：`_m` 一格一个字符。失效看建筑数 × 1000 + 工地数，外加 `invalidate` 的两次调用（`src/managers/layout.js` 这一拍有日志时，`src/roles/builder.js` 工地这一拍就要建完时）。没有按时间过期。`PathFinder` 是平地 2、沼泽 10、`maxRooms` 1、`maxOps` 2000。矩阵：路 1；容器和自己的或公共城墙不挡；其余建筑 255；别人的工地 255；自己的非路、非容器、非城墙工地 255；计划站位 20；四边 50；走不出去的路和容器 255。房间是 W47N8 时才调用 `yieldPost`。堆缓存只给 `avoid=false`，行为不变。卡住不计疲劳：2 绕一次，贵过 `DETOUR` 12 或没搜完就留旧路；4 到 8 之前和自己的非固定、无疲劳阻挡换位；8 按 `Game.time % 8` 迈一个方向并重算，这一拍不走新路；30 打一行 `STUCK`，同时重算，之后每 30 拍再重算，不回收。差一步且是新目标才直走，边上的格子不走捷径。距离 0、旁边是固定 creep 就等着。固定是计划站位上的 `miner` / `filler` / `manager` / `upgrader` / `rminer`，或配置站上的 `w8miner` / `w8rminer`。`w8filler` 不在里面。
- `noDetour` 的调用：`src/rooms/w47n8/fill.js` 的 filler；`src/rooms/w47n8/roles.js` 的 `rmove`（送货、外矿搬运、外矿矿工，以及人不在目标房时的回程出口）；`src/roles/reserve7.js` 的固定出口。W47 房里的 `w8miner` / `w8mminer` 走向站位不带这个选项。`src/roles/raid9.js` 也传了 `noDetour`，但 `raid9` 在 `src/utils/military.js` 的名单里，`move.to` 先走 `military.step`，平民阶梯看不到这个选项。页面没有把袭击写成窄路换位。
- `src/utils/military.js`、`src/utils/combatmove.js`、`src/utils/cpuorder.js`：不读 `_m` 的角色和优先级 0 是同一张名单。`combatmove` 的 `STUCK` 是 3，只属于 `go` 这条引擎 `moveTo`，不是 `move.js` 的 2 / 4 / 8 / 30。`fill.js` 开头注释里的 `STUCK=3` 和 `CMV.to` 指的是这一条，页面按 `combatmove.js` 写，没有把它并进共享阶梯。
- `src/rooms/w47n8/fill.js` 的 `yieldPost` / `yieldHub`，`src/rooms/w47n8/roles.js` 的 `go`，`src/rooms/w47n8/config.js` 的 `HUB_CONT` **33,33**、`SPAWN` **15,18**。`yieldHub` 只有 `go` 这一处生产调用。人在 W47N8 时，`reusePath` 10。升级工、建造工、本地搬运工空手去堆走它。送货走 `go8` → `move.to`。防御、守卫、治疗的 `CMV.to` 用自己的出口回调，不调用 `yieldHub`。岗位 4 在缓存矩阵里。容器被占时的 8 只在当次回调里，而且格子已是 255 则不动。
- `src/rooms/w47n8/layout.js`、`src/rooms/w47n8/roads.js`、`data/terrain_W47N8.txt`：图上的格子都核对过。32,32 是平地，不是路。32,33 是 link。33,32 是终端。33,33、34,32、34,33、33,34、33,31 在路表里。32,31 和 32,34 是延伸。32,34 不在 32,32 → 33,33 的对角上。link、终端、延伸 32,31 立起来之后，32,32 的出口是 33,33 和 33,31。
- 北面大约多 10，是 `fill.js` 里为代价 4 写的那个量。用 `tests/w47n8_spawn_pocket.js` 同一套计划阻挡，从 33,30 到控制器方向，绕北比走一格路的岗位大约多 10。别的终点可以更多。页面写「大约多 10」，没有列成一张路程表，也没有写成每一趟都正好多 10。
- `src/rooms/w47n8/layout.js` 开头仍有一句把 32,33 说成空口袋。那是 2026-11-13 把 link 从 33,34 挪到 32,33 的理由。现行坐标以 `config.js` 的枢纽 link **32,33** 和 `fill.js` 的平地 **32,32** 为准。移动页按现行写。布局那一页不要把这句旧注释写成「32,33 现在还空着」。
- `C.SPAWN` 仍是 **15,18**。`ORDER.spawn` 里的 34,30、33,30、39,30 是布局顺序，移动页没有写成出生点已经搬过去。

## 下一轮

**布局 v2**。写现在活着的布局，不要把旧的棋盘格笔记当成现行规则。家的印章和站位以 `src/layouts/W46N8.js` 为准（`version` 2，印章 A、B、C，`positions` 里的 filler、manager、升级工、矿工）。W47 的枢纽以 `src/rooms/w47n8/layout.js` 为准：`CORE` **34,33**，存储 **35,32**，枢纽 link **32,33**，终端 **33,32**，容器在 `config.js` 的 **33,33**，`RETIRED_HUB_LINK` 是 **33,34**，不是 link。再对 `src/utils/plan.js`：`STATIONARY_FILL` 仍是 false，link 坐标跟 `LINK_PLAN`，不跟 v2 稿里被删掉的那份。出生点锚点仍看 `config.js` 的 **15,18**，不要靠布局文件头的旧搬迁注释把 Spawn2 写成已经站在 34,30。

这一页还没有独立地址。写进机制名单时放在读者会去找地图的地方，不要另编一个公开 URL。已有页面里的坐标（搬运的 34,32，link 的 32,33，孵化的印章）只链过去，不重写。

## 再往后

按读者会先问的顺序。已有的页面缺的是为什么和边界。不要再开一篇日志。

1. **指挥官接管**。`Memory.cmd` 没武装时什么都不接管。实验室页只写了 `react` / `idle` / `hold` 怎么让自动反应让开，矿物页只写了终端被占用时这一拍不送，link 页只写了 `consumeLink` 让自动传送让开，主循环只写了武装时谁先被看、以及 `consumeCreep` 会压过逃跑和角色。还没有一篇把指挥官写成一件事。
2. **站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app 。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。
3. **日期日志不要进给人读的入口**。`STRATEGY`、`docs/REMOTE_*.md`、`docs/CPU.md`、路线、RCL7 这类记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。`docs/CPU.md` 里仍有一句房间视觉在桶低于 2000 时不画，和现在的主循环页不一致。那个文件留在仓库里，不要为了把它改对就搬进导航。
4. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
