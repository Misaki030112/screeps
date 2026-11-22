#!/usr/bin/env python3
import json, sys
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod

D = Path("/workspace/screeps/state/_patrol_2026-11-23_0216")
qs = [
    ("host2", "({t:Game.time,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,hc:Game.rooms.W47N8&&Game.rooms.W47N8.find(FIND_HOSTILE_CREEPS).map(c=>({n:c.name,x:c.pos.x,y:c.pos.y,hits:c.hits,ttl:c.ticksToLive,own:c.owner&&c.owner.username}))})"),
    ("nup", "(Memory.ops&&Memory.ops.upgFeed&&({t:Game.time,nUp:Memory.ops.upgFeed.nUp,why:Memory.ops.upgFeed.why,storE:Memory.ops.upgFeed.storE,rem:Memory.ops.upgFeed.rem}))"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (D / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:2000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
print("ROT", Path("/workspace/screeps/metrics/listener_rot.json").read_text())
