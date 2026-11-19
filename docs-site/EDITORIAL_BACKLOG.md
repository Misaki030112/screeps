# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-19（Asia/Hong_Kong）。手册现在对照的游戏代码仍是 `289a7f06`（`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -- src/` 的最新一笔就是它。其后的文档提交，包括 `279bf678`（#66）、`f52851ca`（#67）、`cbb8ef49`（#68），都不是 LIVE。这一轮也没有改 `src/`。`now.md` 和页脚已经指向 `289a7f06`，没有改。「现状」里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。

## 这一轮做了什么

加深了已有的 `docs-site/mechanisms/deploy.md`（部署）。地址仍是 `/mechanisms/deploy`。导航标题仍是「部署」，没有改 `config.mts` 的机制名单。新图 `DeployPath.vue` 按现有的 `plate` / `arch-col` / `doors` 画四步：源码、摊平、检查、两条上传。`theme/index.ts` 注册了这个组件。编辑备忘仍被 `srcExclude` 排除。

对照这些文件写的。游戏代码没有改。

- `scripts/build.js`：清空 `dist/`，走 `src/**/*.js`，斜杠换成点。只改写引号里以 `./` 或 `../` 开头的 `require`。目标不在 `src/` 里就抛错。`src/roles/queen.js` 的 `../utils/move` 变成 `utils.move`，文件是 `dist/roles.queen.js`。`src/main.js` 仍是 `main`。
- `scripts/check.js`：顺序是构建、`node --check` 每个摊平文件、`node scripts/sim.js 600`、然后一串写死的 `tests/` 文件。不是扫目录。页面只点了类别：身体、地板、外矿状态机、防御状态机、孵化闸、走不出的孵化格、实验室搬运、指挥官。没有列文件名。
- `scripts/sim.js`：只为弄清检查里的 600 tick 门。快照是 `data/sim_snapshot.json`，地形是 `data/terrain_W46N8.txt`，房间名在模拟里写成 W46N8。检查不去连 shard。门：`Memory.stats.errors` 或未接住的异常；结束时还在、且开局就在的 creep，`acts < 50` 的多于 2 只（新出生的没有 `from`，不计入）；日志要有以 `LAYOUT` 开头的一行（`src/managers/layout.js` 只在这一轮真的记了事情时才打）；只看 `births` 的第一只，角色不是 `queen` / `filler` 且格子落在 `src/layouts/W46N8.js` 印章 A、B、C 的全部格子上就失败；记忆段 90 要能读出角色状态码，长度要大于 100 且小于 90000（`src/utils/trace.js` 的段号是 90）。快照会过时，大改前应更换。页面没有写怎么换，也没有写模拟引擎省掉了什么。
- `upload.js`：先 `scripts/check.js`，失败则不会上传。分支是参数，缺省 `default`，这是游戏分支。检查通过之后才读那台机器上的令牌。模块键是文件名去掉 `.js`。
- `scripts/deploy.py`：分支字面量就是 `default`，没有分支参数。检查之前拿锁，避免两次这个脚本同时上传，并留下一条上传记录。页面只留这一句。`upload.js` 不经过这把锁。不要写锁的路径、等待时间、记录存在哪、提交旁的标记或警告原文。
- 没提交的 `src/` 仍会被摊平并上传，因为构建读的是磁盘。页面只说人应该先提交。不要写内部如何标记脏工作区。
- 根 `.gitignore` 有 `dist/`，仓库里没有被跟踪的 `dist/`。克隆后要跑检查才得到同样的摊平结果。
- 根 `vercel.json`：`npm ci --prefix docs-site`，`npm run build --prefix docs-site`，输出 `docs-site/.vitepress/dist`。仓库根没有 `package.json`。公开地址仍是 https://screeps-handbook-nolove-world.vercel.app 。本地 `npm ci` / `npm run dev` / `npm run build` 留在页上。
- 交叉读了孵化页的「出生方向」。印章里外的规则没有重写，部署页只链过去。

## 下一轮

新开一页给人读的移动 / pathing：`docs-site/mechanisms/move.md`，地址 `/mechanisms/move`。写进 `docs-site/.vitepress/config.mts` 的机制名单，放在「搬运与能量」后面。导读那句机制名单也补上「移动」。主循环页写过「路径怎么缓存，不在这一页」，在那句后面加一句交叉链接。这一轮做这个，是因为它还没有独立页面，而且是最新一笔 `src/`（`289a7f06`）的题目。

写这三块，都对照当前源码，不要把满载停驻再讲一遍。

- `src/utils/move.js`：路径缓存在 creep 记忆里，房间的建筑和工地集合变了才失效。脱困按源码的阶梯写。卡住到 30 只打一行控制台，不自动回收。不要把那一行写成有人在仓库外盯着。
- W47 的 `yieldPost`（`src/rooms/w47n8/fill.js`，`move.matrix` 在房间是 W47N8 时会调用）：filler 的空闲格 **34,32** 被抬到代价 **4**。32,32 那格平地空着时，房间里的路程会走那里，而不是踩上这个岗位。延伸 **32,34** 不在这条对角上，没有挪。
- `289a7f06` 的 `yieldHub`：枢纽容器 **33,33** 被占时，把 **32,32** 和 **33,33** 抬到代价 **8**（高于岗位的 4），搜索改走 **34,32 → 34,33 → 33,34**。这是房间内寻路当次的代价回调，不要写成已经画进那张跨 tick 缓存的矩阵。`C.SPAWN` 仍是 **15,18**。

#64 的满载停驻已经在搬运页（满载停在 34,32）。移动页只留一句链到 [搬运](/mechanisms/haul)，不要重讲。

## 再往后

按读者会先问的顺序。已有的页面缺的是为什么和边界。不要再开一篇日志。

1. **布局 v2**。写现在活着的布局，不要把旧的棋盘格笔记当成现行规则。家的印章和 W47 的枢纽以 `src/layouts/W46N8.js`、`src/rooms/w47n8/layout.js` 为准。
2. **指挥官接管**。`Memory.cmd` 没武装时什么都不接管。实验室页只写了 `react` / `idle` / `hold` 怎么让自动反应让开，矿物页只写了终端被占用时这一拍不送，link 页只写了 `consumeLink` 让自动传送让开，主循环只写了武装时谁先被看、以及 `consumeCreep` 会压过逃跑和角色。还没有一篇把指挥官写成一件事。
3. **站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app 。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。
4. **日期日志不要进给人读的入口**。`STRATEGY`、`docs/REMOTE_*.md`、`docs/CPU.md`、路线、RCL7 这类记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。`docs/CPU.md` 里仍有一句房间视觉在桶低于 2000 时不画，和现在的主循环页不一致。那个文件留在仓库里，不要为了把它改对就搬进导航。
5. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
