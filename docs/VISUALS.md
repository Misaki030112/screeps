# In-game route overlay (`src/managers/visuals.js`)

Shows the routes creeps **actually walk right now** (not planned roads), as thin (0.09) dashed lines, opacity 0.5,
one colour per route, split per room so routes cross room edges. Chinese legend (route + current length in tiles) in W46N8 top-left.

## How the path is derived (live, heap only)
- **Remote haul (外矿 W45N8 / W45N7)**: every tick each `rhauler`'s position is appended while it carries energy; when it is
  empty again the trip (remote container -> home drop-off, across rooms) is complete. The latest complete trip per remote is drawn.
- **Home routes**: every movement leg of home roles (hauler, queen, filler, manager, upgrader, builder, miner) is recorded —
  a leg = one `move.js` target key (`_m.k`) from start tile to arrival. Legs are grouped by role + unordered {previous target, target}
  (e.g. 运输 仓库↔能量源(x,y)); the latest leg per group is drawn. Up to 6 busiest groups (trips x length, last 1500 ticks).
- Snapshot rebuilt every 50 ticks; drawn every tick. A global reset clears the heap: lines reappear after the next trips.
- `Memory.routesLive` (refreshed every 50 ticks): `[{key,label,color,len,n,age,pts:'room:x:y;...'}]` for verification.

| Group | Colours |
|---|---|
| 外矿 (sorted by room) | #ffd400 yellow, #ff66cc pink |
| 家里路线 (by rank) | #33ccff, #66ff66, #ff9933, #b388ff, #ff4d4d, #00e6b8 |

- Toggle: `Memory.visuals = { routes: false }` (off) / `delete Memory.visuals` (on, default).
- Planned roads/trunks (old overlay, grey dotted): `Memory.visuals = { planned: true }`, off by default.
- Skipped when `Game.cpu.bucket < 2000` (recording continues, ~0.003 ms/creep). CPU per tick: `Memory.visualsCpu`.
- Test: `tests/visuals.js`.
