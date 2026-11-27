# 手册编辑备忘

给下一轮写公开手册的人。此文件不在网站导航里。`docs-site/.vitepress/config.mts` 的 `srcExclude` 也不会把它编成页面。保持这个排除。

日期：2026-11-27（Asia/Tokyo）。这一轮改的是防御页开头，把「按键的是人」对齐到房间页和指挥官页。没有改 `src/`。

公开手册只写代码里的规则。不要写入令牌、密码、内网地址，也不要写监听、数据库或仪表盘。能量账是游戏里的 `Memory.ledger`。不要写成有人在仓库外盯着这本账。`src/utils/ledger.js` 文件头指向 `docs/LEDGER.md`，仓库里仍然没有这份文件。不要新建它，公开页也不要指向它。

引用分支时写分支名和短提交号，不要写机器路径。不要把文档提交写成游戏部署。

公开页按已部署、尚未合进 master 的 `feat/rcl8-economy` 尖端 `ab1f9730` 写。master 上的 `src/rooms/w47n8/threat.js` 里，`flee()` 只看 `w8flee` 的 20 拍；尖端还有 `remoteThreatOpen()`。master 的 `plan()` 也还没有 `TOWER_ONLY_T` 那一档。不要用 master 的这两处把防御页改回去。安全模式那一行，尖端和 master 的 `src/roles/conquest.js` 是同一处调用。

## 这一轮做了什么

`docs-site/mechanisms/defense.md` 开头不再写「按键的是人」。三层都自己跑：外矿状态机派防御 creep，家里的塔治疗、开枪、补城门，带攻击、远程、治疗或 WORK 的敌人走进 W46N8 就孵守卫，W47 的塔按自己的名单打。

`assessRun` 只在建议非空时写 `Memory.ops.w8adv`。推演仍赢不了，而且武装已经在封墙里面，`advise` 才是 `safemode`。空建议不删旧键。没有塔就不评估。房间里没有还活着的攻击或远程，并且 `w8invN` 不在最近 60 拍里，删 `w8assess` 和 `w8roster`，`w8adv` 留着。还要估时，10 拍缓存直接返回；没有上一份，或者已经满 10 拍，才把配兵写进 `w8roster`。链到 [房间与常数](/reference/rooms#默认关着的开关)。

`flee()` 为真的两笔，以及矿工必收、搬运工还要空手或不在 W47N8，开头用了一句，细节仍留在「外矿什么时候收」。这一节没有重写。30 tick 的 `towers` 那一句也没有动，尖端 `plan()` 里 `TOWER_ONLY_T` 是 30，对得上。

安全模式缺省不调用。`src/` 里唯一的 `activateSafeMode` 在征服工人 `cqworker`，要 `Memory.ops.cq.autoSafe`，缺省不设。平时的防御不读它。`hold`、`retreat`、身上没有能量、控制器还不是自己的、这一拍要去升级，都到不了那一行。指挥官不打开安全模式，也不 claim。袭击和征服要人把 `Memory.ops` 里的旗标打开才动。家里守卫那一节补了一句，指向同一处，免得读到「防御代码不调用」就停在那里。

塔帽、外矿状态机的数字、城门修理，都没有改。

## 对照的提交

尖端 `ab1f9730`（`feat/rcl8-economy`，2026-11-26）。`activateSafeMode` 在 `src/roles/conquest.js` 的 `runWorker`。`assessRun` 和 `w8adv` 在 `src/rooms/w47n8/index.js`。`advise` 来自 `src/rooms/w47n8/defense.js` 的 `plan`。`flee()` 在 `src/rooms/w47n8/threat.js`，矿工和搬运工的条件在 `src/rooms/w47n8/roles.js`。家里守卫是 `src/managers/home.js` 的 `wantGuards`。`src/utils/cmd.js` 没有 `activateSafeMode`，也没有 `claimController`。`src/roles/raid9.js` 的 `wantSpawn` 要 `raidActive`，也就是 `Memory.ops.w47n9.on === true`。征服的 `wantSpawn` 要 `Memory.ops.cq.armed === true`。

master 的 `conquest.js`、`cmd.js`、`home.js` 和 `roles.js` 里这几处与尖端相同。`threat.js` 的 `flee()` 和 `defense.js` 的 `plan()` 不同，见上面。公开页按尖端。

## 下一轮

**只补孵化页的空闲跳过，把数字写上。** `docs-site/mechanisms/spawn.md` 还没有 `IDLE_EVERY`。矿物页只说出生点不是每一拍都重写 `roleTargets`。指挥官页已经写「整层一武装，家和 W47 的孵化闸都会把这一拍的空闲跳过打开」，孵化页却没有这道闸。

家在 `src/managers/spawn.js`：`IDLE_EVERY` 是 4。敌人、指挥官已经武装、`defenseDue`（外矿要防御、`energyHold`、`holding`、或家里要守卫）、以及 `waitCost` 已经够付，会提前打开。成功孵出一只之后，家把下一次跳过武装到 4 拍之后；这一拍的门已经开着，另一座出生点还能再开始一只。W47 在 `src/rooms/w47n8/index.js` 另有一个 `IDLE_EVERY` 4。提前打开的是敌人、指挥官武装，以及外矿那三笔，没有家里的守卫。真正开始孵的那一笔把 `ne` 清成 0，另一座这一拍还跑。

要写就写在孵化页，家和 W47 分成两句，把矿物页那句链过去。不要改身体配方。

选它是因为防御页开头和房间页、指挥官页已经对齐。`flee()` 和 30 tick 对过尖端，不是错句。孵化页缺的是读者从指挥官页走过来时对不上的那一个数。

## 再往后

1. **塔的后两笔还没进尖端。** `ab1f9730` 的 `src/managers/tower.js` 里，`RAMPART_TARGET` 的 RCL3 是 20000，防御页已经写成「3 级 2 万」。没有「仓库不到 2 万就不加墙」，也没有「修路修容器只派最近、刚好够补满的那一座塔」。合进尖端之后再开一轮，只补新门。
2. **「升级者优先由离控制器最近的空闲出生点孵化」不在尖端。** `ab1f9730` 的 `birthDirs` 仍只排出生方向，`spawnCreep` 用的是这份方向。没有按到控制器的距离挑选空闲出生点。哪一笔提交把它加进 `feat/rcl8-economy` 之后，再只补升级页这一句。
3. **可选，更往后。** 给 `now.md` 做一次注明日期的重算。百分比仍是 2026-11-17 的 RCL7 快照。家当时还不是 RCL8。重算不代替上面几条，也不改 `src/`。
4. **指挥官页没有「关掉指令会消失」。** 对过 `docs-site/mechanisms/commander.md` 和 `CmdLife.vue`。单条 `on` 写成 0，条目留着，不算活，也不算过期。整层 `on` 写成 0，袋子留着，这一拍不扫。不必为这句话再开一轮。
5. **道路不用为英文笔记再开一页。** 40,23 已经写在布局页和主循环页。
6. **跟踪不要写成专页。** 导读已经把监听、数据库、仪表盘留在手册外面。
7. **不要把游戏里的 `RoomVisual` 排进公开的主循环页。** 探针也不在公开手册里。以后只有先确认它每天都在跑，才考虑一句很短的说明。
