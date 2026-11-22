#!/usr/bin/env python3
import json, sys
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import db, q as qmod

D = Path("/workspace/screeps/state/_patrol_2026-11-23_0216")

# later room_stats after analysis tip
conn = db.connect(); cur = conn.cursor()
print("=== later room_stats after 84426210 ===")
for room in ("W46N8", "W47N8"):
    cur.execute(
        """select tick, ts, progress, storage, energy, cpu, bucket, hostiles, creeps
           from room_stats where room=%s and tick>=84426210 order by tick""",
        (room,),
    )
    rows = cur.fetchall()
    print(room, "n", len(rows))
    for r in rows:
        print(" ", r)

# compare deploy regression
old = Path("/workspace/screeps/state/_patrol_2026-11-22_2316/audit_patrol.txt").read_text()
new = (D / "audit_patrol.txt").read_text()
def deploy_line(t):
    for line in t.splitlines():
        if line.startswith("REGRESSION [deploy]"):
            return line
    return None
ol, nl = deploy_line(old), deploy_line(new)
print("=== deploy regression identical? ===")
print("OLD", ol)
print("NEW", nl)
print("IDENTICAL", ol == nl)

# model key lines
for name in ("model_1h.txt", "model_2h.txt"):
    print("===", name, "===")
    for line in (D / name).read_text().splitlines():
        if any(k in line.lower() for k in ("upgrade", "storage", "alloc", "window", "rcl", "ideal", "harvest", "waste")):
            print(line)

# live later host / stor / nUp
print("=== live later ===")
expr = "({t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hp:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progress,wp:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progress,host:(()=>{const o=[]; const r=Game.rooms.W47N8; if(!r) return {vis:false}; r.find(FIND_HOSTILE_CREEPS).forEach(c=>o.push({n:c.name,own:c.owner&&c.owner.username,x:c.pos.x,y:c.pos.y,hits:c.hits,hitsMax:c.hitsMax,ttl:c.ticksToLive})); return {vis:true,n:o.length,o:o};})(),nUp:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.nUp,why:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.why,storE:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.storE,w8up:Memory.ops&&Memory.ops.w8up,w8inv:Memory.ops&&Memory.ops.w8inv,w8t:Memory.ops&&Memory.ops.w8threat,guards:Object.keys(Game.creeps).filter(n=>Game.creeps[n].memory&& (Game.creeps[n].memory.role=='w8guard'||Game.creeps[n].memory.role=='w8defender'||Game.creeps[n].memory.role=='defender')).map(n=>({n,rm:Game.creeps[n].pos.roomName,x:Game.creeps[n].pos.x,y:Game.creeps[n].pos.y,hits:Game.creeps[n].hits,ttl:Game.creeps[n].ticksToLive,sp:Game.creeps[n].spawning}))})"
try:
    r = qmod.q(expr, timeout=35)
    (D / "q_later_host.json").write_text(json.dumps(r, indent=2, default=str) + "\n")
    print(json.dumps(r, default=str)[:4000])
except Exception as e:
    print("LIVE FAIL", type(e).__name__, e)

# listener rot
print("=== listener ===")
print(Path("/workspace/screeps/metrics/listener_rot.json").read_text())
