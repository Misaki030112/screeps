# W47N8 one-off probe (manual)
Plan: /workspace/probe_w47n8_plan_cn.md. Code: src/roles/probe.js, spawn hook in managers/spawn.js (after miners/threat hold), tests/probe.js.
Body 4R 3H 1C 8M = 1800 (one MOVE swapped for CARRY so `steal` can carry 50; full speed empty, ~1 stall/2 tiles loaded off-road).
Spawn once: `python3 tools/probe.py spawn` (Memory.ops.probe.spawn=true; waits for storage>=3100; clears flag, sets spawned=name).
Commands (`python3 tools/probe.py cmd ...`): observe | hold [x y [room]] | steal | attack | retreat | guard. Default before any cmd: hold at W46N8 3,20.
Waypoints W47N8: 47,20 -> 40,16 -> 29,14 -> 11,24 -> 12,40 -> 20,35 -> 30,35 -> 40,30 -> 46,24 (loop). Plan's 19,24 and 15,40 are walls.
Pathing: W47N9/W48N9/W48N8 fully blocked; W47N8 rows y<8 blocked.
Safety (all cmds except guard): armed hostile dps (30/ATTACK, 10/RANGED, x4 if boosted) > our heal 36, hits<70%, or hostile tower with >=10 energy
-> cmd=retreat (to W46N8 28,24 under towers), Memory.ops.probe.auto={why,t}. To go back in, set a cmd again manually.
Memory.ops.probe.status every tick; Memory.ops.probe.log (cap 200): cmd, hostile (body), damage, kill, withdraw, delivered, auto-retreat, guard.
guard: role switches to 'defender' with remote W45N8 (patrol W45N8<->W45N7 until TTL, existing code).
