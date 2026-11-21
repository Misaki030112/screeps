# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-21（Asia/Hong_Kong）。这一轮改的是「指挥官接管」里「一条指令活多久」，仍是 `docs-site/mechanisms/commander.md`，没有新开机制页。手册对照的游戏代码是 `289a7f066127a5a8b256df4ecda3771433d8a89c`（`289a7f06`，`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -1 -- src/` 的最新一笔就是它，和 `origin/master` 上的 `src/` 一致。不要在页面上写成更新的 LIVE。这一轮没有改 `src/`。`now.md` 里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算，正文里的数字也没有改。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。卡住 30 的那一行只是控制台的一行字，不要写成有人在仓库外盯着。

## 这一轮做了什么

把一条指令的几种结局分开写。旧句是：`sticky` 要人放开，或把这一条关掉，它才消失。后面又写单条 `on` 写成 0 时不算活、清扫不删、打开整层也不会把这一条的 `on` 改回 1。两句对不齐。公开页不再用「消失」说 `on: 0`。

对着 `src/utils/cmd.js` 写的，图是 `CmdLife`。`once` 和 `fallback` 两段没有改。导航没有加页。页首 `CmdTick` 的图注补了一句：到点就删，发生在整层开着的时候。

和字面容易写错、按代码留下来的有这些：

- 没写 `sticky` 时，`ttl` 是正数才用那个数，否则是 **200**。`until` 是数字就用写下的数，否则是写下的那一拍加上 `ttl`。`sticky` 不写 `ttl`，也不写 `until`。旁边若手写了 `until`，粘性指令仍不看它。
- 时间小于 `until` 才算活。到了 `until` 那一拍（大于或等于）算过期。没有数字 `until`、但 `at` 和 `ttl` 都是数字时，用 `at` 加 `ttl`，仍是小于才活。
- 自己的 `on` 是假：不算活，也不算过期，清扫留下。打开整层只把 `Memory.cmd.on` 写成 1，不把这一条的 `on` 改回 1。`until` 不因为停着而改写。已经到点的非粘性指令，把自己的 `on` 写回真之后，下一次清扫会删掉。
- `sticky` 在自己的 `on` 为真时一直算活。要离开袋子，得放开。放开一只、一座，或一次放开全部，删的是条目。
- 整层 `on` 写成 0 时，这一拍不扫，袋子留着。再打开的当时不删。下一次清扫会重新走，哪怕这一拍刚才已经扫过。整层开着时，只问到一条已经过期的，也会删那一条。
- 开着、又不是 `sticky`、既没有数字 `until`、也凑不齐数字 `at` 和 `ttl` 的，算过期。整层关着时来问，不删。

## 路线叠加：不要再排

公开手册不写游戏里的 `RoomVisual`。它不是现在在跑的机制。下一轮不要把这件事再选成要写的一节，也不要写进 [主循环与 CPU](/mechanisms/loop)。

对过的记录：

- `46e615ef`（2026-10-16，`visuals: remove in-game route drawing entirely (Misaki no longer wants it)`）删了 `src/managers/visuals.js` 和 `tests/visuals.js`。`src/main.js` 去掉了 `const visuals = require('./managers/visuals')`，也去掉了 trace 之后、stats 之前的那一行：`err.wrap('visuals', () => visuals.run())` 和 `Memory.visualsCpu`。`scripts/check.js` 里跑 `tests/visuals.js` 的那一行同时删了。
- `4694bbe8`（2026-10-18 02:22 +0800，`feat(walls v5): ...`）把 `src/managers/visuals.js` 和 `tests/visuals.js` 作为新文件加回来。没有恢复 `main.js` 的挂钩，也没有把测试放回 `scripts/check.js`。备忘初稿写成 2026-10-17，以这次 `git show` 的作者日期为准。
- 当前 `master` 和 `289a7f06` 的 `src/main.js` 都没有 visuals 的 require，也没有 `visuals.run`。`src/` 里没有任何文件 require `managers/visuals`。`tests/visuals.js` 会直接 require 这个模块，检查脚本不跑它。
- 模块里的 `run()` 会先 `record()`，再看桶低于 **2000** 就返回。主循环不调用 `run`，所以记录和绘制都不发生。人在游戏里看不到这条线。桶低于 2000 时主循环页写的重排和停一拍，仍是 `src/utils/cpuorder.js`。
- `docs/CPU.md` 仍有「房间视觉在桶低于 2000 时不画」。`docs/VISUALS.md` 仍把画面写成会画。两份都留在仓库里，不进公开导航，也不要摘进公开的主循环页。

## 下一轮

**在「主循环与 CPU」的「结尾不指挥下一只」里，把能量账写成它实际记什么。** 公开页现在只在顺序里点到「收能量账」。`src/main.js` 在循环开头调用 `ledger.wrap()`，creep 结束、换位的 `flush` 之后调用 `ledger.tick()`。实现在 `src/utils/ledger.js`。文件头注释指向 `docs/LEDGER.md`，仓库里没有这份文件。不要新开机制页。不要改这一节已经写对的顺序，除非对着 `main.js` 发现顺序句本身有错。不要写成有人在仓库外盯着这本账。写之前再对一遍 `wrap` 里每次成功意图加上的分类，和 `tick` 只在源的 `ticksToRegeneration === 1` 时把剩下的能量记进浪费。注释里的毫秒数不要写成公开页的承诺。桶的 2000、指挥官的寿命，这一轮都不要重写。

它排在路线叠加前面，是因为账本已经在主循环里跑，公开页却只点了名字。路线叠加没有接进循环。

## 再往后

1. **不要把文档写成代码变更。** 不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。防御页里「升级工保持 2 只」是现在的本地窗口，不是一次发布说明。
2. **可选，更往后。** 给 `now.md` 做一次注明日期的重算。不是能量账这一轮的替代。百分比仍对照 `85c19c2e`。
3. **道路不用为英文笔记再开一页。** `docs/ROADS.md` 只是指到公开的外矿页。家的路网已经写在 [外矿与预定](/mechanisms/remotes) 的「路」，主循环和建造页也点过阶段名。不要把这份短笔记展开成新的机制页。
