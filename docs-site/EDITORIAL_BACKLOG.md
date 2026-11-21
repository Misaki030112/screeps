# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-21（Asia/Hong_Kong）。这一轮改的是「房间与常数」里「默认关着的开关」的安全模式那一格，没有新开机制页。手册对照的游戏代码仍是 `289a7f066127a5a8b256df4ecda3771433d8a89c`（`289a7f06`，`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -1 -- src/` 的最新一笔仍是它。不要在页面上写成更新的 LIVE。这一轮没有改 `src/`。`now.md` 里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。能量账是游戏里的 `Memory.ledger`。不要写成有人在仓库外盯着这本账。`src/utils/ledger.js` 文件头指向 `docs/LEDGER.md`，仓库里仍然没有这份文件。不要新建它，公开页也不要指向它。注释里的毫秒数没有写进公开页。

## 这一轮做了什么

「房间与常数」的安全模式那一格原来写「代码不调用」。这句比源码更绝对。公开页改成代码实际做的事：防御只写建议，建议键会留下；`src/` 里唯一的调用在征服工人，而且 `autoSafe` 缺省不设。图是 `SafeModeNote`。没有新开机制页，没有改防御页和指挥官页，用的是交叉引用。没有把征服或 raid9 写成出击步骤，也没有写成有人在仓库外收到警报。

对过的行为，按代码留下来的有这些：

- `src/rooms/w47n8/index.js` 文件头写本模块不自己开安全模式。`assessRun` 调用 `defense.plan`。`advise` 只有在推演仍赢不了、而且 `o.inside` 为真时才是 `'safemode'`，否则是空字符串。非空才写 `Memory.ops.w8adv = { t: Game.time, advise, why, n: force.length }`。不调用 `activateSafeMode`。`defense.assess` 用同一条建议条件，房间写入这个键的是 `plan` 的返回。
- 空字符串不会清掉已经写下的键。上一次 `w8assess` 还不到 10 拍，函数在推演之前返回，也不重写 `w8adv`。
- 威胁清空的条件比「没有武装」更窄：房间里没有活着的攻击或远程部件，并且 `Memory.ops.w8invN` 不在最近 60 拍里（没写、写成 0，或已经过了 60 拍，都算）。这时删 `room.memory.w8assess` 和 `Memory.ops.w8roster`，不删 `w8adv`。只带 WORK 或治疗的 creep 不挡住这次删除。`src/` 里没有第二处写入或删除 `w8adv`，也没有别处再读它来决定开不开。代码不给这个键加过期标记。旧不旧只看 `t`。
- `src/` 里唯一的 `activateSafeMode()` 在 `src/roles/conquest.js` 的 `runWorker`。`Memory.ops.cq.autoSafe` 缺省不设，文件头写明缺省关闭。走到那一行还要可用次数大于 0、当前不在安全模式、控制器至少 2 级。`cmd` 还是缺省的 `hold` 或是 `retreat`、身上没有能量、控制器还不是自己的、或这一拍要去升级控制器，都会提前返回。安全模式结束且次数还在，工人再次走到这里会再试。`wantSpawn` 要 `Memory.ops.cq.armed === true` 才孵人。调用那一行不再读 `armed`。平时的防御不读 `autoSafe`。
- `src/roles/raid9.js` 文件头写 NEVER 调用。它只读目标房间控制器上的 `safeMode`。`tests/raid9.js` 断言这份源码里没有 `.activateSafeMode(`。公开页一笔带过，不写破墙、入口或编制。
- `src/utils/cmd.js` 不打开安全模式。`src/managers/stats.js` 把控制器上现成的 `safeMode` 和 `safeModeAvailable` 放进房间统计。`src/managers/alerts.js` 在警报载荷里带上这两个数，也不调用，也不读 `w8adv`。公开页不写这两处，以免写成监听或仓库外的警报。
- `tools/conquest.py` 只改 `autoSafe` 旗标，不调用 `activateSafeMode`。公开页不写这个工具怎么用。

## 路线叠加：不要再排

公开手册不写游戏里的 `RoomVisual`。它不是现在在跑的机制。下一轮不要把这件事再选成要写的一节，也不要写进 [主循环与 CPU](/mechanisms/loop)。

对过的记录：

- `46e615ef`（2026-10-16，`visuals: remove in-game route drawing entirely (Misaki no longer wants it)`）删了 `src/managers/visuals.js` 和 `tests/visuals.js`。`src/main.js` 去掉了 `const visuals = require('./managers/visuals')`，也去掉了 trace 之后、stats 之前的那一行：`err.wrap('visuals', () => visuals.run())` 和 `Memory.visualsCpu`。`scripts/check.js` 里跑 `tests/visuals.js` 的那一行同时删了。
- `4694bbe8`（2026-10-18 02:22 +0800，`feat(walls v5): ...`）把 `src/managers/visuals.js` 和 `tests/visuals.js` 作为新文件加回来。没有恢复 `main.js` 的挂钩，也没有把测试放回 `scripts/check.js`。备忘初稿写成 2026-10-17，以这次 `git show` 的作者日期为准。
- 当前 `master` 和 `289a7f06` 的 `src/main.js` 都没有 visuals 的 require，也没有 `visuals.run`。`src/` 里没有任何文件 require `managers/visuals`。`tests/visuals.js` 会直接 require 这个模块，检查脚本不跑它。
- 模块里的 `run()` 会先 `record()`，再看桶低于 **2000** 就返回。主循环不调用 `run`，所以记录和绘制都不发生。人在游戏里看不到这条线。桶低于 2000 时主循环页写的重排和停一拍，仍是 `src/utils/cpuorder.js`。
- `docs/CPU.md` 仍有「房间视觉在桶低于 2000 时不画」。`docs/VISUALS.md` 仍把画面写成会画。两份都留在仓库里，不进公开导航，也不要摘进公开的主循环页。

## 下一轮

**在已有的「主循环与 CPU」页，补上结尾那一行 `STATS` 实际有哪些字段。** 现在那句写的是：时间、用掉的 CPU、桶、GCL、房间、各角色的数量、错误数。`src/utils/report.js` 打出的顶层字段是 `t`、`cpu`、`b`、`gcl`、`rooms`、`creeps`、`nerr`、`tr`。`tr` 是 `Memory.traceCpu`。`nerr` 是 `(Memory.stats.errors || []).length`，也就是留下的条数，不是这一拍新发生的条数。`src/managers/stats.js` 用 `slice(-10)` 留下这些错误，文件头注释写的 20 已经过时。写之前再对这两处。只补字段名字，以及 `nerr` 数的是什么。`rooms` 里面还有控制器上现成的 `safeMode` 数字，那是统计对象里的数，不要在这一句里拆成仪表盘，也不要回头改安全模式那一格。不要展开记忆段 90。不要写成监听、数据库或仪表盘。文件头提到 websocket，公开页不写。路线叠加不要再排。

它排在安全模式这一格后面，是因为主循环页已经点了这行摘要的名字，却少了 `tr`，也没有说清 `nerr` 数的是留下的条数。改的是已有页末的一句，不开专页。

## 再往后

1. **不要把文档写成代码变更。** 不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。防御页里「升级工保持 2 只」是现在的本地窗口，不是一次发布说明。
2. **可选，更往后。** 给 `now.md` 做一次注明日期的重算。百分比仍对照 `85c19c2e`。不是 `STATS` 字段这一句的替代。
3. **道路不用为英文笔记再开一页。** `docs/ROADS.md` 只是指到公开的外矿页。家的路网已经写在 [外矿与预定](/mechanisms/remotes) 的「路」，主循环和建造页也点过阶段名。不要把这份短笔记展开成新的机制页。
4. **矿物与终端不用新开一页。** 现有页已经写了一次送多少、手续费，以及 `Game.market` 只用于算手续费、没有订单。不要把「市场规则还薄」再排成新页。
5. **跟踪不要写成专页。** 导读已经把监听、数据库、仪表盘留在手册外面。`STATS` 那一句补完字段之后，也不要为此再开一页，不要展开记忆段 90。
