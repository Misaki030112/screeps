# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。保持这个排除。

日期：2026-11-22（Asia/Hong_Kong）。这一轮只加深「主循环与 CPU」末尾那一句控制台 `STATS`。没有新开页面，没有新的导航项，没有改 `src/`。手册对照的游戏代码仍是 `289a7f066127a5a8b256df4ecda3771433d8a89c`（`289a7f06`，`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -1 -- src/` 的最新一笔仍是它。不要在页面上写成更新的 LIVE，也不要把这次文档改动写成一次游戏部署。`now.md` 里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。能量账是游戏里的 `Memory.ledger`。不要写成有人在仓库外盯着这本账。`src/utils/ledger.js` 文件头指向 `docs/LEDGER.md`，仓库里仍然没有这份文件。不要新建它，公开页也不要指向它。注释里的毫秒数没有写进公开页。

## 这一轮做了什么

「主循环与 CPU」里，能量账两节（「结尾不指挥下一只」「账上没有的进出」）没有改写。安全模式那一格也没有动。页末原来那句把控制台一行说成：时间、用掉的 CPU、桶、GCL、房间、各角色的数量、错误数。少了 `tr`，也没有说清 `nerr` 数的是什么。

现在仍是同一处。控制台 `STATS` 是给人看的摘要，`report.run` 缺省每 **10** 拍才打；`Memory.stats` 每拍都写，里面有这一拍收集到的警报和错误，没打那一行的拍统计照写。八个字段用一张安静的表：`t`、`cpu`、`b`、`gcl`、`rooms`、`creeps`、`nerr`、`tr`。表后没有再列别的键。没有新组件，没有路线叠加，没有记忆段 90，也没有把 `rooms` 拆成一张房间表。

对过的行为，按代码留下来的有这些：

- `src/utils/report.js` 是整个模块。`run(every = 10)`。`Game.time % every` 非 0 就返回。否则 `console.log('STATS ' + JSON.stringify({...}))`。主循环调用的是 `report.run()`，没有另传间隔。公开页不写文件头里的 websocket。
- 这一行的顶层字段就是 `t`、`cpu`、`b`、`gcl`、`rooms`、`creeps`、`nerr`、`tr`。`s = Memory.stats || {}`。
- `t` 是 `Game.time`。统计里另有 `s.time`，这一行不读它。
- `cpu` 是 `+(s.cpu || 0).toFixed(2)`。`src/managers/stats.js` 在 `stats.run` 里写 `s.cpu = Game.cpu.getUsed()`，位置在房间、creep、错误和警报之后。
- `b` 是打印时的 `Game.cpu.bucket`。`stats.js` 也写 `s.bucket`，这一行不读那个副本。
- `gcl` 是 `s.gcl`，形状是 `{ level, progress, progressTotal }`，取自 `Game.gcl`。
- `rooms` 是 `s.rooms`。房间对象里字段很多，其中有控制器上现成的 `safeMode` / `safeModeAvailable`。那是统计对象里的数。这一轮没有拆开，也没有回头改安全模式那一格。房间详情大多在 `Game.time % 5 === 0` 或还没有 `s.rooms` 时整块重写；已有房间的 `energy` 和 `progress` 每拍另写。公开页不写这个节奏。
- `creeps` 是 `s.creeps = _.countBy(Game.creeps, c => c.memory.role)`。
- `nerr` 是 `(s.errors || []).length`：留下的条数，不是这一拍新发生的条数。`stats.run` 先接到这一拍 `err.flush()` 交来的新错误，再 `slice(-10)`。最多 **10** 条。这一拍没有新的，旧的还在。`src/managers/stats.js` 文件头写 “keeps last 20 errors”，和代码不符。公开页跟代码，写 10。**不要为了这句注释去改 `src/`。**
- `tr` 是 `Memory.traceCpu`。`src/main.js` 在统计和报告之前计时：`err.wrap('trace', () => { trace.tick(); trace.run(); })`，然后 `Memory.traceCpu = Math.round((Game.cpu.getUsed() - tt) * 1000) / 1000`。这是跟踪这一步本拍用掉的 CPU，三位小数。不是 creep 循环里逐只累加的那份。公开页不展开记忆段 90。
- `s.alerts` 是 `concat` 再 `slice(-12)`。`s.prof` 以及 `remote`、`lastErrorTick`、`lastAlertTick` 也在 `Memory.stats` 里。它们都不是 `STATS` 那一行的顶层字段。公开页只说警报留在统计里，没有把 `prof` 写进字段表。

## 路线叠加：不要再排

公开手册不写游戏里的 `RoomVisual`。它不是现在在跑的机制。下一轮不要把这件事再选成要写的一节，也不要写进 [主循环与 CPU](/mechanisms/loop)。

对过的记录：

- `46e615ef`（2026-10-16，`visuals: remove in-game route drawing entirely (Misaki no longer wants it)`）删了 `src/managers/visuals.js` 和 `tests/visuals.js`。`src/main.js` 去掉了 `const visuals = require('./managers/visuals')`，也去掉了 trace 之后、stats 之前的那一行：`err.wrap('visuals', () => visuals.run())` 和 `Memory.visualsCpu`。`scripts/check.js` 里跑 `tests/visuals.js` 的那一行同时删了。
- `4694bbe8`（2026-10-18 02:22 +0800，`feat(walls v5): ...`）把 `src/managers/visuals.js` 和 `tests/visuals.js` 作为新文件加回来。没有恢复 `main.js` 的挂钩，也没有把测试放回 `scripts/check.js`。备忘初稿写成 2026-10-17，以这次 `git show` 的作者日期为准。
- 当前 `master` 和 `289a7f06` 的 `src/main.js` 都没有 visuals 的 require，也没有 `visuals.run`。`src/` 里没有任何文件 require `managers/visuals`。`tests/visuals.js` 会直接 require 这个模块，检查脚本不跑它。
- 模块里的 `run()` 会先 `record()`，再看桶低于 **2000** 就返回。主循环不调用 `run`，所以记录和绘制都不发生。人在游戏里看不到这条线。桶低于 2000 时主循环页写的重排和停一拍，仍是 `src/utils/cpuorder.js`。
- `docs/CPU.md` 仍有「房间视觉在桶低于 2000 时不画」。`docs/VISUALS.md` 仍把画面写成会画。两份都留在仓库里，不进公开导航，也不要摘进公开的主循环页。

## 下一轮

**把 `docs-site/plan.md` 里「绝不自动开安全模式」改得和房间页一样具体。** 短改措辞，加一处指向 [房间与常数](/reference/rooms) 的交叉引用。不要重写安全模式那一格，不要改防御页，不要把征服或 raid9 写成出击步骤。

它排在 `STATS` 字段后面，是因为规划页「已经在跑」里这句仍比代码更绝对。房间页已经写成：缺省不调用；防御只写建议；唯一调用要征服工人的 `autoSafe`，而且缺省不设。规划页不该停在「绝不」。

写之前再读这几处。这一轮对过、下一轮仍要自己再看一眼的有：

- `docs-site/plan.md`「已经在跑」仍有「低 CPU 桶时的执行顺序，以及「绝不自动开安全模式」」。同页「明确没有开始」还有一条「主动开战、为矿物新占外矿、自动安全模式」，后一句是旗标要人打开才动。那一条不要展开成用法。若同一小段改完后，「自动安全模式」仍比房间页更绝对，只把那一个说法对齐，仍用交叉引用。
- `src/` 里 `activateSafeMode` 的调用只在 `src/roles/conquest.js` 的 `runWorker`。条件是 `P.autoSafe && ctl.safeModeAvailable > 0 && !ctl.safeMode && ctl.level >= 2`。文件头写明 `autoSafe` 缺省关闭。`cmd` 缺省 `hold`，`hold` 和 `retreat` 在这一行之前返回。身上没有能量、控制器还不是自己的、或这一拍要去升级，也会提前返回。
- `src/roles/raid9.js` 文件头写 NEVER 调用。防御写建议、不调用，房间页已经写了。不要在规划页把建议键再讲一遍。
- `docs-site/now.md` 仍有「不自动开安全模式」和「真正按下去的是人」。那不是这一轮要改的句子，也不是下一轮规划页这一句的替代。

## 再往后

1. **不要把文档写成代码变更。** 不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。防御页里「升级工保持 2 只」是现在的本地窗口，不是一次发布说明。
2. **可选，更往后。** 给 `now.md` 做一次注明日期的重算。百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，已经明显落后于现在的进度。重算不是 `STATS` 字段那一句的替代，也不是规划页安全模式措辞的替代。同页「真正按下去的是人」比房间页更绝对。若重算时碰到这句，跟房间页对齐，不要写成出击步骤。
3. **道路不用为英文笔记再开一页。** `docs/ROADS.md` 只是指到公开的外矿页。家的路网已经写在 [外矿与预定](/mechanisms/remotes) 的「路」，主循环和建造页也点过阶段名。不要把这份短笔记展开成新的机制页。
4. **矿物与终端不用新开一页。** 现有页已经写了一次送多少、手续费，以及 `Game.market` 只用于算手续费、没有订单。不要把「市场规则还薄」再排成新页。
5. **跟踪不要写成专页。** 导读已经把监听、数据库、仪表盘留在手册外面。`STATS` 那一行的字段已经补在主循环页上。不要为此再开一页，不要展开记忆段 90，也不要把 `rooms` 拆成仪表盘。`Memory.stats` 里的 `prof`、`remote`、`s.bucket`、`s.time` 都不是那一行的顶层字段，不要回头补进字段表。
6. **不要把游戏里的 `RoomVisual` / 路线叠加排进公开的主循环页。** 模块没有从 `main.js` 挂上，人在游戏里看不到那条线。仓库里的 `docs/CPU.md` 和 `docs/VISUALS.md` 在这一点上是旧的，以后可以只在仓库内改正，仍不进公开导航，也不要摘到公开的主循环页。
7. **探针不在公开手册里。** `docs/PROBE.md` 和 `src/` 里的角色都还没写进公开页。以后只有先确认它是每天都在跑的机制，才考虑一句很短的公开说明。不要写成侦察或进攻的步骤。
