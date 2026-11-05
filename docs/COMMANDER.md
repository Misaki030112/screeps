# Commander overlay（指挥接管）

中文摘要：这是指挥层的地基，不是把每个角色重写一遍。平时 `Memory.cmd` 不存在，脚本和现在一样跑。需要手动指挥时，对**单个 creep、一队 creep、或单个建筑**下命令（`CMD.setCreep` / `CMD.setMany` / `CMD.setSquad` / `CMD.setStruct`）。命令有效期间这一个单位听指挥；`release`、到期（默认 200 tick）或 `CMD.disarm()` 之后回到原来的脚本。家里矿工、升级、建造、搬运、女王、filler、远程搬运/预订、以及 `raid9` 都已接上。优先级是：**活着的 cmd > raidOrder > 自动脚本**。不会改 `Memory.ops`（包括 `w47n9`、softCap），也不会改 `raidOrder` 本身。`forceGo` 每 tick 在 creep 行动之前清一次，所以即使全队都是具体 `act` 也不会把小队旗标饿死。征服 / 探针 / 方阵也可以用 duty 指挥。不会自动开安全模式、claim、市场出售或开战。核弹 `launch` 必须带 `allow: 1` 和坐标，否则不发射。

English: a Red Alert-style takeover seam. Automation keeps the colony. A future commander bot (or a human on the console) can grab one creep or one structure, give it an order, then let go. The role script, raid orders, and softCap policy are still there when the order ends.

Home economy, home guard, remote haulers/reservers/defenders, and `raid9` all call `yieldCreep`. When `Memory.cmd` is off that is one falsy check. A live order does not rewrite `raidOrder`.

## What is wired now

| Unit | Concrete `act` | Duty order (`duty`, no `act`) |
|---|---|---|
| Every creep (`main.js`, before `home.flee` and the role) | yes — role is skipped | the role must call `yieldCreep` (the rows below do) |
| Home hauler, miner, mminer, upgrader, builder, harvester, queen, filler, manager | yes | yes — `idle` / `hold` / `flee` / `fillSpawn` / `fillTower` / `bank` |
| Home guard, remote `defender` | yes | yes — `idle` / `hold` / `kite` / `flee` (`focus` falls through to the combat script) |
| Remote `rhauler`, `rminer`, `reserver`, and `reserve7` | yes | same duty list. A live order beats flee / `attackController` for that tick |
| `raid9` | yes. `main.js` skips `run` for an act | yes, and a live duty also skips `raidOrder`. `tickFlags` runs once per tick **before** acts, so `forceGo` is not starved |
| Conquest (`cqsquad`, `cqbreaker`, `cqworker`, `cqhauler`, `cqatk`, `cqrh`, `cqminer`), `cqquad`, `probe`, remote `rscout` | yes | yes. A live order beats that creep's `Memory.ops.cq` / `Memory.ops.probe` script for the tick. Release resumes it. Status pings pause while the order is live |
| Every W47N8 role (`rooms/w47n8/roles.js`), including `w8hauler` and `w8defender` | yes, and it beats `Memory.ops.w8recycle` | same duty list |
| Home towers and W47N8 towers | `attack` / `heal` / `repair` / `idle` / `hold` per tower | — |
| Home links and W47N8 source/hub links | `transfer` / `idle` / `hold` | — |
| Every lab (output and inputs) | `idle` / `hold` skips the auto reaction. `react` on the output needs `in1`+`in2`. Does not set `Memory.ops.labs` | — |
| Observer | `observe` with `room: 'W47N9'`, or `idle` / `hold` | — |
| Nuker | `launch` only with `allow: 1` and `pos`. Otherwise it waits and does not pick a room | — |
| Factory, power spawn | `produce` / `idle` / `hold` own the tick and call nothing (`processPower` is not called) | — |
| Home spawn and Spawn2 | `idle` / `hold` / `recycle` / `spawn` | — |
| W47N8 terminal | any live order **blocks** the automatic K send | this phase does **not** call `terminal.send` |

`act: 'spawn'` runs only when the order sets `allow: 1` and an explicit `body`. The default memory role is `hauler`. The framework does not invent a combat body.

Conflict for a raid creep, highest first: **live `Memory.cmd` (act or duty) > `memory.raidOrder` > the raid script.** Releasing the commander order leaves `raidOrder` as it was. The same order applies to conquest / probe / quad: live `Memory.cmd` beats `Memory.ops.cq.cmd` and `Memory.ops.probe.cmd` for that creep only.

## Memory schema (`Memory.cmd`)

Additive. Absent on a live server until someone issues an order. Never stored inside `Memory.ops`.

```js
Memory.cmd = {
  v: 1,
  on: 1,            // master switch. 0 => every order is ignored, none are deleted
  steer: 0,         // 1 => stamp an advisory c._duty from rank(). Does not change scripts.
  by: 'Misaki',
  at: 84000000,     // Game.time of the last issue
  c: {              // creeps by name
    Hauler1: {
      on: 1,
      act: 'move',          // concrete. wins over duty
      duty: 'fillSpawn',    // used only when act is absent
      id: 'targetId',       // Game.getObjectById
      pos: { room: 'W46N8', x: 30, y: 29 },
      range: 1,
      res: 'energy',
      amount: 100,
      say: 'go',
      heal: 'self',         // optional side heal during a creep act
      ttl: 200,
      at: 84000000,
      until: 84000200,      // exclusive. live while Game.time < until
      once: 1,              // delete after the action returns OK, or when a move arrives
      sticky: 0,            // 1 => no TTL. release/disarm only
      fallback: 0,          // 1 => missing target lets the role script run this tick
      by: 'console',
      note: 'west rampart'
    }
  },
  s: {              // structures by id (tower, link, lab, spawn, terminal)
    towerId: { on: 1, act: 'attack', id: 'hostileId', ttl: 50, at: 84000000, until: 84000050, by: 'console' }
  }
}
```

Creep marker: while an **act** holds the creep, `Memory.creeps[name]._cmd = 1`. It is removed on the tick the order is gone. Role fields (`role`, `working`, `src`, `dst`, `raidOrder`, `hp`, …) are not written.

In-tick only (not saved): `creep._duty` and `creep._dutyWhy` (`'cmd'` or `'steer'`).

### Creep acts

`idle`, `say`, `hold`, `move`, `harvest`, `pickup`, `withdraw`, `transfer`, `drop`, `repair`, `build`, `upgrade`, `attack`, `rangedAttack`, `rangedMassAttack`, `heal`, `rangedHeal`, `dismantle`, `recycle`.

The executor does not search for a hostile. No `id` (and no `pos` for move/hold) means the creep holds still, unless `fallback: 1`, in which case the role script runs that tick and the order stays.

### Structure acts

| Structure | Acts |
|---|---|
| Tower | `attack`, `heal`, `repair`, `idle`, `hold` |
| Link | `transfer` (target link id), `idle`, `hold` |
| Lab | `react` with `in1` and `in2`, or `idle` / `hold` to skip `runReaction`. Does not set `Memory.ops.labs` |
| Spawn | `idle` / `hold` skip the auto queue without arming the idle-skip window. `recycle` needs a creep `id` adjacent to the spawn. `spawn` needs `allow: 1` and `body` |
| Terminal | any live order sets `w8min.sendWhy = 'cmd'` and does not send. `terminal.send` is phase 2 |

## Priority / intent

Roles stay in `src/roles/*`. The shared scheduler is `src/utils/intent.js` `rank(role, signals)`. It is a table plus modifiers, not another chain of role `if`s. The same signals always return the same order (tests lock this).

Signals are read from memory the colony already publishes (`Memory.ops.w8day`, `w8threat`, `w47n9`, `w8roster`, `room.memory.focus` / `threat8`, storage, `energyAvailable`). `rank` / `signals` do not call `room.find`. Publishing still belongs to the existing tower and spawn code.

Duties, high to low, before modifiers:

| Family | Duty | Base | When |
|---|---|---|---|
| econ | flee | 100 | threat ≥ 3 and the creep has no attack/ranged/heal |
| econ | fillSpawn | 90 | spawn energy &lt; 50% of cap (+20 if &lt; 25%) |
| econ | fillTower | 80 | threat ≥ 1 or a remote is in THREAT/DEFEND (+15 if threat ≥ 2, +10 if remote) |
| econ | bank | 70 | storage &lt; 5k, or &lt; 15k, or softCap while &lt; 25k (+20 under 5k, +10 if softCap) |
| econ | haul | 50 | always |
| econ | repair | 40 | `w8day.contLow` or `roadCrit`, not war, storage ≥ 5k |
| econ | lab | 25 | `Memory.ops.labs` set, no spawn pressure, no war, storage ≥ 15k |
| econ | upgrade | 10 | storage ≥ 25k, softCap off, war off, bucket ≥ 2000 |
| mil | kite | 100 | hits &lt; 60% |
| mil | focus | 90 | threat ≥ 2 or war (+10 if war or threat ≥ 3) |
| mil | hold | 70 | remote defence or threat === 1 (+15 if remote and threat &lt; 2) |
| mil | idle | 10 | quiet: no threat, no war, no remote defence |

Threat levels: 3 = W47N8 `threat8.inBase` in the last 5 ticks; 2 = home `room.memory.focus`, any fresh `threat8`, or `Memory.ops.w8threat` inside 1500; 1 = a fresh `w8roster` or `w8invN` inside 60; else 0. War matches `raid9.pauseCivilians` (read from `Memory.ops.w47n9` only — raid9.js is not required).

`Memory.cmd.steer = 1` stamps the winning duty onto the creep for debugging. Example roles ignore it. They act on a duty only when that creep has a commander duty order (`_dutyWhy === 'cmd'`). Turning steer on does not change peacetime.

Duty execution (`intent.obey`) writes no role memory:

- `idle` — stand. No attack.
- `hold` / `kite` / `flee` — move to `pos` if given, else (kite/flee) toward the room's first spawn. No attack.
- `fillSpawn` / `fillTower` / `bank` — if the creep is carrying energy, deliver there; if it is empty, return false so the normal pickup script runs. The order is still live next tick.
- `focus`, `haul`, `repair`, `lab`, `upgrade` — return false. The role script runs, with `c._duty` set for a later phase.

## Who wins

Highest first:

1. **`Memory.cmd.on` and a live per-unit order with `act`.** That creep or structure does the act and nothing else this tick. Home `flee`, `w8recycle`, tower auto-fire, link transfer, lab reaction, spawn queue, and the role body all yield for that unit only. Neighbours are unchanged.
2. **Live `duty` and no `act`.** Wired roles run the duties listed above. A duty the seam does not execute (`focus`, `haul`, `repair`, `lab`, `upgrade`) falls through to the role script. On `raid9` that fall-through is the raid script, not `raidOrder`: any live act or duty suppresses `raidOrder` for that tick.
3. **`memory.raidOrder`.** Only inside `raid9.run`, and only when this creep has no live commander order. The overlay never deletes `raidOrder`.
4. **Automation policy** — `Memory.ops.w47n9`, softCap / `w8day`, `w8recycle`, remote threat FSM, tower focus. The overlay does not write these.
5. **The role script.**

`disarm()` sets `on: 0` and keeps the maps. `arm()` resumes every order that has not expired. `releaseCreep(name)` / `releaseStruct(id)` delete that one key. `releaseAll()` clears both maps and any `_cmd` flags.

TTL: setters default `ttl: 200` and `until: now + ttl` (`Game.time < until`). `sticky: 1` does not expire. A hand-written order with `on: 1` but no `sticky`, `until`, or `at`+`ttl` is dropped on the next sweep so a typo cannot pin a unit. Paused entries (`on: 0`) are kept.

`once: 1` deletes the order after the call returns `OK` (0), or when a move/hold has arrived.

Replacement: `setCreep` / `setStruct` replace that unit's order. They do not merge.

### Raid / forceGo

`raid9.tickFlags()` runs once from `main.js` before any creep act. It applies `Memory.ops.w47n9.forceGo` (clear flee / garrison / recycle / safe, fallback → breach, delete the flag) and drops a stale overrun flee. A concrete act on every raid creep no longer skips that. The same call is idempotent inside `raid9.run`, so a duty still sees the flag already cleared. It does not create `Memory.ops.w47n9` and it does not move a creep. Use `setSquad` + a duty when you want the squad to hold or kite; use `act` when you want one exact intent (`rangedAttack`, `move`, …). Both are safe next to `forceGo`.

A live order also beats `Memory.ops.w47n9.recycle` for that creep. The flag stays. Release resumes the recycle walk. Builder `recycleCivilian` works the same way.

### Recycle caveat

A W47N8 creep listed in `Memory.ops.w8recycle` is not recycled while its commander order is live. The name stays on the list. Release resumes the recycle walk. Commanding the queen still stamps `room.memory.queenAlive`, so haulers do not treat her as dead.

## Console

`require('./utils/cmd')` publishes `global.CMD` (the flattened bundle still shares the global).

```js
CMD.setCreep('Hauler1', { duty: 'fillSpawn', ttl: 80, say: 'spawn' })
CMD.setCreep('Guard1', { act: 'rangedAttack', id: '...hostile...', ttl: 40, heal: 'self', say: 'ra' })
CMD.setCreep('w8defender1', { duty: 'hold', pos: { room: 'W47N8', x: 29, y: 6 }, ttl: 100 })
CMD.setStruct('towerId', { act: 'attack', id: '...hostile...', ttl: 30 })
CMD.setStruct('linkId', { act: 'idle', ttl: 20 })          // skip one transfer
CMD.releaseCreep('Hauler1')   // role memory unchanged
CMD.disarm()                  // pause every order; put this back when the fight is over
CMD.arm()
CMD.releaseAll()
```

Direct writes work if they match the schema (`on`, and `sticky` or `until`). Prefer the setters so `until` is filled in.

Issuing an order sets `Memory.cmd.on = 1`. When the session is over, `CMD.disarm()` so the live loop goes back to a single falsy check per creep. Leaving `on: 1` with an empty map is still only a hash lookup, but disarm is the peacetime shape.

## CPU

- `Memory.cmd` missing or `on` falsy: `main.js` does not call `Game.cpu.getUsed` and does not stamp duties. One property check per creep, plus the same check at the top of the example roles and structure managers.
- Armed: one order lookup per creep. An act skips the rest of that creep (often cheaper than the role). Towers, links, labs, spawns, and the terminal check out the same way, and only when armed.
- `intent.rank` / `signals` run only for `steer` or for a creep that already has a duty order. No extra `find`.

## How automation resumes

1. The order is deleted (release, `once`, or TTL sweep) or the master switch is turned off.
2. Next tick `consumeCreep` / `consumeTower` return false and delete `_cmd` if it was set.
3. The role reads whatever it already had: `working`, `dst`, `raidOrder`, raid phase, tower `threat8`. The overlay never cleared them, so there is no orphaned commander target in role memory.
4. `w8recycle` and `raidOrder` apply again on their own.

A missing target does not delete the role's target. The creep waits (or falls through, if `fallback: 1`) until the order ends.

## Migration

| Phase | What | Status |
|---|---|---|
| 0 | This contract, `Memory.cmd`, `rank()`, examples above, tests | this PR |
| 1 | Commander bot or console uses the setters in a real fight. Still no auto safe mode, claim, market, or arming `w47n9` | next |
| 2 | Measure CPU, then let selected roles obey `Memory.cmd.steer` (advisory becomes behavior). One role per PR, with that role's existing tests | later |
| 3 | Replace the biggest in-role `if` ladders (hauler deliver, builder job pick) with `rank()` once phase 2 matches live priorities | later |
| 4 | `terminal.send`, lab boosts, named spawn presets — explicit orders only | later |

Do not flip `steer` on for the whole colony in one deploy. Do not fold `Memory.cmd` into `Memory.ops.w47n9`.

Takeover of every current creep role is in this foundation. Still out: `steer` actually changing peacetime behavior, `terminal.send`, factory / power-spawn production, and a commander bot. Those are later phases, not blockers for reviewing the overlay.

## War-command cookbook

Squad helpers issue the same order object shape as `setCreep` (each creep gets its own copy, its own TTL). They do not read or write `raidOrder` or `Memory.ops.w47n9`. An empty selector matches nobody.

```js
// Preferred while a squad flag may also be set this tick: duty, not a raw act.
// forceGo is cleared by tickFlags even if every creep is under an act; a duty
// still lets the creep path itself (hold / kite) instead of one hard intent.
Memory.ops.w47n9.forceGo = 1
CMD.setSquad({ role: 'raid9', kind: 'h' }, { duty: 'hold', pos: { room: 'W47N8', x: 38, y: 46 }, ttl: 80, say: 'hold' })

// Named list. Names may be issued before the creep exists; it obeys on the tick it spawns.
CMD.setMany(['d1', 'm1', 'h1'], { duty: 'kite', pos: { room: 'W47N9', x: 20, y: 40 }, ttl: 40 })

// One exact shot. Safe beside forceGo: the flag is cleared before this act runs.
CMD.setSquad({ role: 'raid9', room: 'W47N9' }, { act: 'rangedMassAttack', ttl: 15 })

// Conquest / probe / quad take the same duty orders.
CMD.setSquad({ role: 'cqsquad' }, { duty: 'hold', pos: { room: 'W47N8', x: 24, y: 8 }, ttl: 50 })
CMD.setCreep('probe1', { duty: 'idle', ttl: 30, say: 'wait' })

// Release the squad. raidOrder and ops.cq.cmd resume on the next tick.
CMD.releaseMany(['d1', 'm1', 'h1'])
CMD.disarm()
```

`setSquad` filters: `role`, `kind` (`memory.kind`), `home`, `room` (where it stands now). A function is also a filter: `CMD.setSquad(c => c.hits < c.hitsMax * 0.5, { duty: 'flee', ttl: 30 })`.

Structures in the same fight:

```js
CMD.setStruct(towerId, { act: 'attack', id: hostileId, ttl: 25 })
CMD.setStruct(outputLabId, { act: 'idle', ttl: 50 })          // skip KO this tick; ops.labs stays
CMD.setStruct(inputLabId, { act: 'hold', ttl: 50 })           // also skips the auto reaction
CMD.setStruct(observerId, { act: 'observe', room: 'W48N9', ttl: 20 })
CMD.setStruct(nukerId, { act: 'launch', allow: 1, pos: { room: 'W47N9', x: 25, y: 25 }, ttl: 5 })
```

`launch` without `allow: 1` does not fire. Do not leave a nuker order armed by accident. `CMD.disarm()` when the order is done.

## Websocket room slots (ops listener vs 指挥官)

中文：平时分析监听只占 **一个** 官方房间订阅名额，按墙钟 **W46N8 : W47N8 : W45N8 : W45N7 = 5 : 5 : 1 : 1** 轮转（600s / 600s / 120s / 120s），第二个名额留给 Screeps指挥官。指挥官正在实战接管时，ops 必须把房间订阅全部停掉；这一场的战斗房间由指挥官自己订阅（两个官方名额按需要用）。交还之后删掉 yield 文件，ops 恢复这条单槽轮转。这是盒子上的操作，不是 `Memory.cmd`，也不改游戏代码。

The official Screeps websocket allows two room subscriptions per user. Console (`user:<id>/console`) and cpu are not room slots. The listener keeps those in both peacetime and wartime, so STATS, alerts, and the memory-segment poll stay up.

Peacetime (`tools/room_rot.py`, `tools/listener.py`):

- Ops holds exactly one room. Schedule, wall clock: W46N8 600s, W47N8 600s, W45N8 120s, W45N7 120s, then repeat.
- `metrics/live.json` is the W46N8 map only while that room holds the slot (`roomSlot` names the current room). Creep trails for the other three rooms still land in `creep_ticks` during their turns.
- The other official slot stays empty for the commander bot. Do not start a second `listener.py` (it would take the slot and double-write `creep_ticks`).

Wartime, when the commander bot is live-commanding a local campaign:

1. Ops stops room subscriptions entirely: `touch metrics/listener_yield_rooms`. The listener drops its room within about 5 seconds. Console and cpu stay.
2. The commander bot subscribes the battle rooms. A fight in two rooms uses both official slots. Ops must not also be subscribed, or the server answers `subscribe limit reached` and both sides lose ticks.
3. Handback: the commander unsubscribes, then `rm metrics/listener_yield_rooms`. Ops resumes the same single-slot 5:5:1:1 schedule on the room it was holding, and that room's hold starts over. Do not leave the yield file in place during peacetime — home and W47N8 sampling stay off until it is removed.

`Memory.cmd` does not subscribe rooms and does not read this file. Safe mode, claims, and attacks are still not armed from here.

## Files

- `src/utils/cmd.js` — overlay, `yieldCreep`, `setMany` / `setSquad`, executors
- `src/utils/intent.js` — `rank` / `stamp` / `obey`
- `src/main.js` — act gate before flee and the role; `runHeldStructures` when armed
- `src/roles/hauler.js`, `miner.js`, `mminer.js`, `upgrader.js`, `builder.js`, `harvester.js`, `queen.js`, `filler.js`, `manager.js`, `guard.js`
- `src/roles/remote.js` — `rhauler`, `rminer`, `reserver`, `defender`
- `src/roles/reserve7.js`, `src/roles/raid9.js` (`tickFlags` before acts)
- `src/roles/conquest.js`, `src/roles/quad.js`, `src/roles/probe.js` — duty as well as act
- `src/rooms/w47n8/roles.js` — colony wrapper (all `w8*` roles)
- `src/managers/tower.js`, `links.js`, `labs.js`, `spawn.js` — home structures
- `src/rooms/w47n8/index.js` — colony towers, links, Spawn2, terminal yield
- `tests/commander.js`, `tests/commander_tower.js`, `tests/commander_roles.js`
- `tools/room_rot.py`, `tools/listener.py` — peacetime one room slot; wartime `metrics/listener_yield_rooms`. Not game code. `tests/listener_rot_test.py`
