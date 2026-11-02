# W47N9 wartime raid (east line)

Misaki ordered GO. This build is the wartime controller. **Do not arm or deploy from a cloud agent.** Parent merges, deploys, then runs `arm`. The code never calls `activateSafeMode`.

Code: `src/roles/raid9.js`. Console: `tools/raid9.py`. Tests: `node tests/raid9.js` (also `scripts/check.js`).

## Arm (after deploy)

```bash
python3 tools/raid9.py status          # read-only intel + Memory.ops.w47n9
python3 tools/raid9.py defaults        # print the arm payload, no Memory write
python3 tools/raid9.py arm             # NEEDS APPROVAL. Sets on:true and the knobs below. Clears safe/garrison/flee/go.
python3 tools/raid9.py abort           # on:false, garrison, flee.why=abort
```

`arm` replaces `Memory.ops.w47n9`. It does not upload code. While `on` is true (and the assault is not safe/garrison/flee), both rooms pause upgraders and builders. Miners, fillers, haulers, and remotes keep their spawn priority.

Knobs are read every tick. Change them with `set` — no redeploy:

```bash
python3 tools/raid9.py set phase=punch pauseSpawn=false pullSoft=0.7 pullHard=0.45
python3 tools/raid9.py set max.d=4 minDps=1240 maxY43=2 kite=true
python3 tools/raid9.py set 'mouths=[{"x":38,"y":42},{"x":39,"y":42}]'
python3 tools/raid9.py set 'focusSeal={"x":39,"y":42}'
python3 tools/raid9.py pause           # pauseCivilians=true even if on is false
python3 tools/raid9.py resume-civ      # pauseCivilians=false (development continues while on)
python3 tools/raid9.py order raid9_d_1 moveTo=38,43,W47N9 dismantle=38,42 until=500
python3 tools/raid9.py clear raid9_d_1
```

`order` writes `Memory.creeps[<name>].raidOrder`. Fields: `moveTo` (`x,y` or `x,y,room`), `attack`, `dismantle` (id or `x,y`), `heal` (`self`, `lowest`, id, or `x,y`), `hold`, `until` (Game.time), `clear`. The creep follows that order instead of the formation AI until `clear` or `until`.

## Memory.ops.w47n9

| Knob | Default | Effect |
|---|---|---|
| `on` | arm sets true | Spawn the field. `false` stops new raid creeps. |
| `go` | AI | Set when ≥ `need.d` dismantlers (default 2) and one melee or healer are on the W47N8 north lip (`y≤3`) or already in W47N9. Cleared only when W47N9 is empty and no d/m/r remain on that lip. Deaths do not clear it. |
| `safe` / `safeUntil` | AI on enemy safe mode | Garrison, stop spawn. Does not open our safe mode. |
| `flee` | AI on overrun, or `abort` | Any truthy `flee` forces garrison. Overrun = hostile ATTACK+RA parts ≥ 40. |
| `garrison` | AI with flee/safe | Stop spawn. Living creeps walk to the W47N8 north-wall slots. |
| `phase` | `breach` | `breach` \| `punch` \| `inside_towers` \| `inside_clean` \| `fallback`. AI only advances the ladder. An operator phase sticks until the room reaches a later step. `fallback` (or flee/garrison/safe) pulls everyone out through (38,49). |
| `need` | `{d:2,m:0,r:0,h:0}` | Soft GO gate. `need.d` is how many dismantlers must be up before `go`. |
| `max` | `{d:4,m:6,r:6,h:10}` | Field cap. Spawn keeps streaming until each kind is full. |
| `mouths` | dual `(38,42)+(39,42)`; wide `37–40` once inside | Seal order. |
| `focusSeal` | first mouth | Moved to the front of `mouths`. |
| `minDps` | `1240` | Two-tower repair. A mouth opens only when assigned dismantlers beat this. One 24W is 1200 and is not given a seal alone. |
| `towerOrder` | `(39,37)` then `(34,28)` | Tower hull order (T1 then T2). |
| `prio` | fight, filler, towerRampart, tower, blocker, econ | Inside focus classes. Sticky: keep the current target until it dies or a higher class appears. |
| `kite` | true | `false` disables pull and the healer emergency. |
| `pullSoft` / `pullHard` | `0.70` / `0.45` | Worst front creep (d/m) at or under soft: do not advance. At or under hard: d/m/r step south together. |
| `maxY43` | `2` | Dismantlers on y=43. The rest wait on y=45. |
| `pauseSpawn` | false | `true` stops raid spawns. Creeps already up keep fighting. |
| `pauseCivilians` | while `on` and not stood down | `true` forces the pause. `false` lets upgraders/builders spawn during the assault. |
| `note` | free text | Not read by AI. |

Per-creep `raidOrder` overrides that creep only. Squad knobs still apply to everyone else.

## Economy pause

`pauseCivilians()` is true when `pauseCivilians===true`, or when `on` and not `safe` / `garrison` / `flee` / `safeUntil`, unless `pauseCivilians===false`.

Both rooms then:

- builder target 0, and living builders walk to spawn and recycle (colony via `Memory.ops.w8recycle`)
- upgrader target 0, except **one** upgrader if `ticksToDowngrade < 20000`
- miners, fillers, haulers, queens, and remotes stay on their normal targets

## Spawn

| Kind | Body | Cost | Cap |
|---|---|---|---|
| dismantler `d` | 2T 24W 24M | 3620 | 4 |
| melee `m` | 2T 24A 24M | 3140 | 6 |
| ranged `r` | 15RA 15M 1H | 3250 | 6 |
| heal `h` | 18H 18M spec | 5400 | 10 |

RCL7 `energyCapacityAvailable` is 5300, so the healer that actually spawns is **17H17M (5100)** until the cap can hold 5400. Home (`W46N8`) prefers `d` then `m` then `r` then `h`. Colony (`W47N8`) prefers `h` then the combat kinds. Both keep spawning any kind still under `max`.

A fat body is not spawned while a miner, hauler, filler, or remote is short. If `energyAvailable` is under the body cost and logistics are full, that room banks energy instead of spawning an upgrader with the partial pile.

## East line

- Enter only at **(38,49)**. Do not step on swamp **(38,47)**; go through **(37,47)** or **(39,47)**.
- Formation until the hole opens: ≤2 dismantlers on **y=43** (adjacent to the open seal), melee **y=44**, extra dismantlers **y=45**, ranged **y=46**, healers **y=47–48**.
- First seals are (38,42) and (39,42), but both dismantlers stack on the focus seal while `minDps` is 1240. The second mouth waits. Raising `maxY43` (or lowering `minDps`) opens the next mouth. Inside, the mouth list widens to x=37–40.
- Pre-breach the towers repair. Threat is enemy ranged on the rampart, handled by `pullSoft` / `pullHard`. If the front is at hard pull, at most two healers step to y=44 for 3 ticks, then those two leave together.
- The tick the focus seal is gone, phase becomes `punch`: melee and dismantlers step through, hit a creep on that rampart first, otherwise finish the rampart. Healers follow to y=45.
- Inside, focus is sticky and ordered: fighting creeps → tower fillers → rampart on the tower → tower hull (T1 then T2) → path blockers → economy. Ranged and healers yield the lane if they are closer to the focus than a dismantler or melee.

## Stop

| Condition | Result |
|---|---|
| Enemy safe mode | `safe`, garrison, stop spawn |
| ATTACK+RA parts ≥ 40 | `flee` → garrison, stop spawn |
| `raid9.py abort` | same, `flee.why=abort` |
| `phase=fallback` | pull out; spawn continues unless garrison/pauseSpawn |
| `pauseSpawn` | no new raid creeps |
| Under `max` and logistics are met | keep spawning |
