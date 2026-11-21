# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-21（Asia/Hong_Kong）。这一轮加深的是「主循环与 CPU」里已有的「结尾不指挥下一只」，没有新开机制页。手册对照的游戏代码仍是 `289a7f066127a5a8b256df4ecda3771433d8a89c`（`289a7f06`，`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -1 -- src/` 的最新一笔仍是它。不要在页面上写成更新的 LIVE。这一轮没有改 `src/`。`now.md` 里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。能量账是游戏里的 `Memory.ledger`。不要写成有人在仓库外盯着这本账。`src/utils/ledger.js` 文件头指向 `docs/LEDGER.md`，仓库里仍然没有这份文件。不要新建它，公开页也不要指向它。注释里的毫秒数没有写进公开页。

## 这一轮做了什么

保留原来的顺序句，补上能量账实际记什么。顺序句对着 `src/main.js` 重新对过，没有改：全部 creep 之后是换位 `flush`，然后 `ledger.tick()`，然后 trace，然后 stats，然后 report。图是 `LedgerWhen`。桶的 2000、停一拍、3000 的闸，以及指挥官那一页，都没有重写。页末那句「能量账包在 `utils/errors` 里」指的是结尾的 `tick`。开头的 `wrap()` 不在 `err.wrap` 里，正文里分开写了，没有改页末那句。

和文件头、和容易写错的地方，按代码留下来的有这些：

- `Memory.ledger.s[id]` 运行时是四个数：房间名、挖到的能量、浪费、遇上再生前最后一拍的次数。文件头写成 `[room, harvested, wastedAtRegen]`，少了第四格。`tick` 在 `ticksToRegeneration === 1` 时做 `e[2] += s.energy`，并且 `e[3] = (e[3] || 0) + 1`。剩下 0，次数仍加 1。这一行还不存在时，`tick` 会建出来，挖到的先是 0。
- 挖矿在 `Memory.ledger` 还不存在时直接返回，不创建账本。`add` 和 `tick` 会创建。成功回调仍要返回值是 `OK`。挖矿多这一道。`spawnCreep` 的 `dryRun` 即使返回 `OK` 也不加。
- 回收估算：每个部件 `min(125, 造价)`，再乘 `min(1, ttl / 寿命)`。身体里有 CLAIM，寿命用 600，否则用 1500。整段 `Math.floor` 一次。身上的能量不加。注释写引擎还会掉落携带。公开页只按这条式子写，并写明身上的能量不在式子里。
- 修理的房间键是 `home`（`memory.home`，没有则用当前房间）。三元表达式两边都落到 home。人在别的房间时，只在分类名后加 `@房间`。
- 塔的 `tr` 是墙和城门以外的全部修理，包括路、容器和其他。攻击和治疗都是 `th`，成功一次加 10。
- link 损耗是 `Math.ceil((n || 现有能量) * 0.03)`。家的 `transferEnergy` 不传数量，所以按 link 里当时的全部能量，不按出手门槛 400。W47 传 `min(已有, 对面空位)`。账不按对面结算后再改。
- `rcat` 在目标为空时返回 `'ro'`。前面再加 `'r'` 会变成 `rro`。成功的修理有目标，公开页写的是 `rw`、`rr`、`rc`、`ro`。没有把 `rro` 写成账上会出现的分类。
- 文件头注释里的毫秒成本没有写成公开页的承诺。`reset` 有导出，主循环不调用。公开页写的是主循环每拍不清空。
- 矿物页已经写了发送批量、手续费和「没有市场」。这一轮没有许诺新开矿物页，也没有新开道路页。

## 路线叠加：不要再排

公开手册不写游戏里的 `RoomVisual`。它不是现在在跑的机制。下一轮不要把这件事再选成要写的一节，也不要写进 [主循环与 CPU](/mechanisms/loop)。

对过的记录：

- `46e615ef`（2026-10-16，`visuals: remove in-game route drawing entirely (Misaki no longer wants it)`）删了 `src/managers/visuals.js` 和 `tests/visuals.js`。`src/main.js` 去掉了 `const visuals = require('./managers/visuals')`，也去掉了 trace 之后、stats 之前的那一行：`err.wrap('visuals', () => visuals.run())` 和 `Memory.visualsCpu`。`scripts/check.js` 里跑 `tests/visuals.js` 的那一行同时删了。
- `4694bbe8`（2026-10-18 02:22 +0800，`feat(walls v5): ...`）把 `src/managers/visuals.js` 和 `tests/visuals.js` 作为新文件加回来。没有恢复 `main.js` 的挂钩，也没有把测试放回 `scripts/check.js`。备忘初稿写成 2026-10-17，以这次 `git show` 的作者日期为准。
- 当前 `master` 和 `289a7f06` 的 `src/main.js` 都没有 visuals 的 require，也没有 `visuals.run`。`src/` 里没有任何文件 require `managers/visuals`。`tests/visuals.js` 会直接 require 这个模块，检查脚本不跑它。
- 模块里的 `run()` 会先 `record()`，再看桶低于 **2000** 就返回。主循环不调用 `run`，所以记录和绘制都不发生。人在游戏里看不到这条线。桶低于 2000 时主循环页写的重排和停一拍，仍是 `src/utils/cpuorder.js`。
- `docs/CPU.md` 仍有「房间视觉在桶低于 2000 时不画」。`docs/VISUALS.md` 仍把画面写成会画。两份都留在仓库里，不进公开导航，也不要摘进公开的主循环页。

## 下一轮

**在「房间与常数」里，把安全模式那一格写成代码实际做的事。** 现在这一格写着「代码不调用」。防御评估不调用 `activateSafeMode`。打不赢、而且武装已经在封墙里面时，`src/rooms/w47n8/index.js` 的 `assessRun` 把建议写到 `Memory.ops.w8adv`。`src/` 里没有另一处删掉这个键。征服工人只有 `Memory.ops.cq.autoSafe` 为真才调用 `activateSafeMode`，`src/roles/conquest.js` 写明缺省关闭。`raid9.js` 的文件头写它不调用。写之前再对这三处，包括建议消失之后 `w8adv` 留不留。不要新开机制页，不要把征服或 raid9 写成出击步骤，也不要写成有人在仓库外收到警报。

它排在能量账后面，是因为速查表上这一句比源码更绝对，改一格就够。跟踪不要展开成记忆段 90、监听或数据库。路线叠加不要再排。

## 再往后

1. **不要把文档写成代码变更。** 不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。防御页里「升级工保持 2 只」是现在的本地窗口，不是一次发布说明。
2. **可选，更往后。** 给 `now.md` 做一次注明日期的重算。百分比仍对照 `85c19c2e`。不是安全模式这一格的替代。
3. **道路不用为英文笔记再开一页。** `docs/ROADS.md` 只是指到公开的外矿页。家的路网已经写在 [外矿与预定](/mechanisms/remotes) 的「路」，主循环和建造页也点过阶段名。不要把这份短笔记展开成新的机制页。
4. **矿物与终端不用新开一页。** 现有页已经写了一次送多少、手续费，以及 `Game.market` 只用于算手续费、没有订单。不要把「市场规则还薄」再排成新页。
5. **跟踪不要写成专页。** 导读已经把监听、数据库、仪表盘留在手册外面。若以后只补主循环结尾那一行 `STATS`：`src/utils/report.js` 还会打出 `tr`（`Memory.traceCpu`），`nerr` 是 `Memory.stats.errors` 留下的条数。`stats.js` 用 `slice(-10)`，文件头注释写的 20 已经过时。补字段即可，不要展开记忆段 90。
