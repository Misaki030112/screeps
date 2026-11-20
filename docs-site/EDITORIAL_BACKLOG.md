# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-20（Asia/Hong_Kong）。上一篇是布局页，squash 提交 `ba7b2bb1`，已经在 master 上。这一轮新开「指挥官接管」。手册现在对照的游戏代码仍是 `289a7f06`（`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -- src/` 的最新一笔就是它。不要在页面上写成更新的 LIVE。这一轮没有改 `src/`。`now.md` 里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算，这一轮也没有改 `now.md`。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。卡住 30 的那一行只是控制台的一行字，不要写成有人在仓库外盯着。

## 这一轮做了什么

新开了 `docs-site/mechanisms/commander.md`，地址 `/mechanisms/commander`。导航标题是「指挥官接管」，放在「主循环与 CPU」后面、「孵化与身体」前面。导读的机制名单在「主循环」后面加了「指挥官」。主循环、实验室、矿物、link、房间表、部署各加了一句交叉链接，没有重讲能量、反应、传送门槛或六步发送。`docs/COMMANDER.md` 改成指向这一页，没有进导航。

一张图：`CmdTick.vue`（没武装是一次假值判断；武装后只问点了名的 creep 和建筑；接不住就交还）。`theme/index.ts` 注册了这个组件。样式沿用已有的 `plate`、`node`、`phases`、`legend`，没有新的视觉语言。编辑备忘仍被 `srcExclude` 排除。

对照这些文件写的。游戏代码没有改。

- `src/utils/cmd.js`：`armed` 是 `Memory.cmd` 在且 `on` 为真。缺省 TTL 200。`sticky` 不设 `until`。过期删。单条 `on: 0` 留着；`arm` 只把整层设回 1，不改单条的 `on`。`once` 在返回 0 时放开。`hold` / `move` 已经站进距离也算完成。`fallback` 让这一拍交还，指令还在。`consumeCreep` 有 `act` 才接住，压过 `home.flee` 和角色。`yieldCreep` 先问 consume，再问 `intent.obey`。`suppressed` 在活的 `act` 或 `duty` 上为真。`blocks` 对任何活的建筑指令为真，不调用 `terminal.send`。`runHeldStructures` 只在武装时看观察者、核弹、工厂、Power Spawn、实验室。工厂和 Power Spawn 占住这一拍、什么也不调用，不调用 `processPower`。核弹 `launch` 要 `allow` 和写明的 `pos`。出生点 `spawn` 要 `allow` 和非空 `body`。实验室 `react` 要 `in1` 和 `in2`，不写 `Memory.ops.labs`。link 冷却仍占住并且不送。这一层不写 `Memory.ops`、`raidOrder`、softCap、角色目标，不编战斗身体，不 claim，不开安全模式。
- `src/utils/intent.js`：`obey` 只在理由是 `cmd`、且没有 `act` 时做 `idle` / `hold` / `kite` / `flee` / `fillSpawn` / `fillTower` / `bank`。身上没有能量时，填充和 `bank` 交还角色。`focus` / `haul` / `repair` / `lab` / `upgrade` 是建议，返回假。`steer` 只盖建议，不执行。
- `src/main.js`：`runHeldStructures` 在 creep 之前，且只在武装时调用。`consumeCreep` 在 `home.flee` 之前。解脱和停一拍更早。
- 钩子：`managers/tower.js`、`links.js`、`labs.js`、`spawn.js`，`rooms/w47n8/index.js` 的出生点、终端 `blocks`、link、塔。角色脚本开头的 `yieldCreep`，以及 `raid9` 的 `suppressed`。整层武装时，家和 W47 的孵化闸会打开空闲跳过；没有点名到这座出生点时，自动队列仍排。

## 下一轮

**站点打磨**。排版、标题层级、交叉链接、图。公开地址已经在用：https://screeps-handbook-nolove-world.vercel.app 。它写在 README 和 GitHub 仓库简介里。不要另编一个地址，也不要删掉已有的链接。

为什么是下一轮：现在活着的殖民地，机制页已经齐了。下一轮要的是读起来一致、好找，而不是再新开一篇机制。

## 再往后

按读者会先问的顺序。已有的页面缺的是一致和边界。不要再开一篇日志。

1. **日期日志不要进给人读的入口**。`STRATEGY`、`docs/REMOTE_*.md`、`docs/CPU.md`、路线、RCL7 这类记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。`docs/CPU.md` 里仍有一句房间视觉在桶低于 2000 时不画，和现在的主循环页不一致。那个文件留在仓库里，不要为了把它改对就搬进导航。
2. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
3. **可选，这一轮不做。** 建造、修理和城墙落在哪；或者给 `now.md` 做一次注明日期的重算。两件都留到以后，不要塞进打磨里当新机制来写。
