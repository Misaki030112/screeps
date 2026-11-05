# Commander overlay（指挥接管）

中文摘要：这是指挥层的地基，不是把每个角色重写一遍。平时 `Memory.cmd` 不存在，脚本和现在一样跑。需要手动指挥时，对**单个 creep 或单个建筑**下一道命令（控制台 `CMD.setCreep` / `CMD.setStruct`，或直接写 `Memory.cmd`）。命令有效期间，这一个单位听指挥；`release`、到期（默认 200 tick）或 `CMD.disarm()` 之后，它回到原来的角色脚本。不会改 `Memory.ops`（包括 `w47n9`、softCap、`raidOrder`），不会自动开安全模式、claim、市场出售或开战。

English: a Red Alert-style takeover seam. Automation keeps the colony. A future commander bot (or a human on the console) can grab one creep or one structure, give it an order, then let go. The role script, raid orders, and softCap policy are still there when the order ends.

This PR is phase 0: the contract, the memory key, the priority table, and a few wired examples. It does not move every role onto the scheduler.

## What is wired now

| Unit | Concrete `act` | Duty order (`duty`, no `act`) |
|---|---|---|
| Every creep (`main.js`, before `home.flee` and the role) | yes — role is skipped | stamp only, unless the role calls `intent.obey` |
| Home hauler `roles/hauler.js` | yes | yes — `idle` / `hold` / `flee` / `fillSpawn` / `fillTower` / `bank` |
| Home guard `roles/guard.js` | yes | yes — `idle` / `hold` / `kite` / `flee` (`focus` falls through to the guard script) |
| Every W47N8 role (`rooms/w47n8/roles.js` wrapper), including `w8hauler` and `w8defender` | yes, and it beats `Memory.ops.w8recycle` | same duty list as above |
| Home towers and W47N8 towers | `attack` / `heal` / `repair` / `idle` / `hold` per tower | — |
| Home links and W47N8 source/hub links | `transfer` / `idle` / `hold` | — |
| Home output lab | `idle` / `hold` / `react` (explicit `in1`+`in2` only) | — |
| Home spawn and Spawn2 | `idle` / `hold` / `recycle` / `spawn` | — |
| W47N8 terminal | any live order **blocks** the automatic K send | phase 1 does **not** call `terminal.send` |

`act: 'spawn'` runs only when the order sets `allow: 1` and an explicit `body`. The default memory role is `hauler`. The framework does not invent a combat body.

Unwired roles (miner, upgrader, builder, raid9 body, remotes, …) still accept a concrete `act` from `main.js`. A duty-only order on those roles is advisory until a later phase adds `intent.obey`. `raid9` is deliberately not edited: a live **act** skips that creep's `raid9.run` for the tick (so it cannot also apply `forceGo`), and `memory.raidOrder` is left untouched for the release.

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
2. **Live `duty` and no `act`, on a role that calls `intent.obey`.** The duties listed above run. Anything `obey` does not handle falls through to the role.
3. **`memory.raidOrder`.** Only inside `raid9.run`, and only when this creep has no live commander act. The overlay never deletes `raidOrder`.
4. **Automation policy** — `Memory.ops.w47n9`, softCap / `w8day`, `w8recycle`, remote threat FSM, tower focus. The overlay does not write these.
5. **The role script.**

`disarm()` sets `on: 0` and keeps the maps. `arm()` resumes every order that has not expired. `releaseCreep(name)` / `releaseStruct(id)` delete that one key. `releaseAll()` clears both maps and any `_cmd` flags.

TTL: setters default `ttl: 200` and `until: now + ttl` (`Game.time < until`). `sticky: 1` does not expire. A hand-written order with `on: 1` but no `sticky`, `until`, or `at`+`ttl` is dropped on the next sweep so a typo cannot pin a unit. Paused entries (`on: 0`) are kept.

`once: 1` deletes the order after the call returns `OK` (0), or when a move/hold has arrived.

Replacement: `setCreep` / `setStruct` replace that unit's order. They do not merge.

### Raid / forceGo caveat

`main.js` skips `raid9.run` for a creep that has a live act. Squad-level `Memory.ops.w47n9.forceGo` still runs if any other raid creep ticks. If every raid creep is under an act on that tick, `forceGo` waits until one of them is released. Prefer a duty/act on the creeps you are steering, not a blanket act on the whole squad in the same tick as `forceGo`.

### Recycle caveat

A W47N8 creep listed in `Memory.ops.w8recycle` is not recycled while its commander order is live. The name stays on the list. Release resumes the recycle walk.

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

## Files

- `src/utils/cmd.js` — overlay, setters, executors
- `src/utils/intent.js` — `rank` / `stamp` / `obey`
- `src/main.js` — act gate before flee and the role
- `src/roles/hauler.js`, `src/roles/guard.js` — home examples
- `src/rooms/w47n8/roles.js` — colony wrapper (all `w8*` roles)
- `src/managers/tower.js`, `links.js`, `labs.js`, `spawn.js` — home structures
- `src/rooms/w47n8/index.js` — colony towers, links, Spawn2, terminal yield
- `tests/commander.js`, `tests/commander_tower.js`
