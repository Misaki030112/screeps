# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。

日期：2026-11-21（Asia/Hong_Kong）。这一轮新开了「建造、修理和城墙」，页面是 `docs-site/mechanisms/build.md`。手册对照的游戏代码仍是 `289a7f06`（`fix(w47n8): take the filler post when hub container 33,33 is occupied`）。`git log -- src/` 的最新一笔就是它。不要在页面上写成更新的 LIVE。这一轮没有改 `src/`。`now.md` 里的百分比仍是 2026-11-17、对照 `85c19c2e` 的快照，没有重算，正文里的数字也没有改。

公开手册只写 `src/` 里现在生效的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。卡住 30 的那一行只是控制台的一行字，不要写成有人在仓库外盯着。

## 这一轮做了什么

新页从家的四段墙（`off`、`roads`、`bank`、`build`）和七段路（`core` 到 `done`）写起，说明升级何时写成 0、建造工留下哪一层存储、城墙台阶停在哪，以及 W47 的 `w8builder` 不走 `walls.js`。图是 `BuildYield`。导航放在布局后面、升级前面。升级页原有的 `noUpgrade` 那一句没有改，只在后面加了链接。W47 的 keep=2、15000 地板、40000 连续 500 tick 的闩，没有写成已经松开。

写的时候对过这些文件：`src/managers/walls.js`、`src/managers/roads.js`、`src/managers/spawn.js`、`src/roles/builder.js`、`src/managers/threat.js`、`src/managers/tower.js`、`src/roles/queen.js`、`src/rooms/w47n8/index.js`、`src/rooms/w47n8/roles.js`、`src/rooms/w47n8/threat.js`、`src/managers/layout.js`。上一份备忘里的阶段名是对的。需要收住的一点：`targets` 里城墙阶段可以把建造工写成最多 6 只，但 `fundSpend` 或围城成立时，孵化会把这个数收成正好 1。和平时期墙还在往台阶上抬、基金不少于 3000，走的是这一只。

## 下一轮

**掉落、墓碑和废墟。** 写成新的机制页，或把搬运页里那一句展开成能独立读的一节。不要做成建造页的补丁。

为什么是下一轮：建造页只写了建造工拿够得着的地上能量（不少于 100，围死的不拿）。搬运页有一句，家的搬运工在捡容器之前会看值得绕路的掉落、墓碑和废墟。规则在 `src/utils/salvage.js`，调用在 `src/roles/hauler.js`、`src/roles/queen.js`、`src/roles/remote.js`、`src/rooms/w47n8/roles.js`。至少 50，每远一格扣 8，能量堆最远 25 格，带攻击或远程的敌人 5 格内不捡。矿物和强化物按 5 点能量计，家里有存储时可以跨房，最远 49。非能量先送回存储。`retire` 的第二个参数是寿命门槛：建造工传入 1500，等于满寿命，真正的等待是空转 50 拍。这些数还没有一页。

## 再往后

1. **日期日志不要进给人读的入口**。`STRATEGY`、`docs/REMOTE_*.md`、`docs/CPU.md`、路线、RCL7 这类记录留在仓库里。公开导航已经是新站点。不要把那些英文变更记录引进网站。`docs/CPU.md` 里仍有一句房间视觉在桶低于 2000 时不画，和主循环页的写法对不上。活代码在 `src/managers/visuals.js`，`MIN_BUCKET` 是 2000，画的是房间里的路线。那个英文文件留在仓库里，不要为了把它改对就搬进导航。路线叠加要不要单独写一小节，排在掉落页之后，也不要写成有人在仓库外盯着。
2. **不要把文档写成代码变更**。不要在手册里修改 15000 的地板，也不要把 W47 的 keep=2 写成已经松开。那道闩要存储连续 500 tick 不低于 40000 才到 3。没有常设的第三只升级工。只描述当前代码。
3. **W47 塔的软抬升还薄。** 防御页写了城门和出生点上的城门先补到 10 万。`rampHold` 还有关键建筑上的城门抬到 `SOFT_RAMP`（100000）、衰减回补 `HOLD_SLACK`（1000），实验室和工厂上的盖停在 300000。掉落页写完之后，若要加深防御，从这里补，不要另起一套城门数字。
4. **`commander.md` 的粘性指令。** 「一条指令活多久」里，`sticky` 那句仍写关掉就「消失」。后面写明单条 `on` 写成 0 时清扫不删。两句还没对齐。改的时候只改这一处措辞。
5. **可选，更往后。** 给 `now.md` 做一次注明日期的重算。不是掉落页的替代。
