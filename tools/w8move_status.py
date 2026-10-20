#!/usr/bin/env python3
"""W47N8 spawn move status (read-only console query): phase, why, force, spawn site progress, hostiles, energy, towers, walls, builders, guard.
usage: python3 tools/w8move_status.py"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from q import q
H = '(()=>{const r=Game.rooms.W47N8,m=Memory.ops.w8move||{},'
E1 = H + ('ss=r.find(FIND_MY_CONSTRUCTION_SITES,{filter:s=>s.structureType=="spawn"})[0];return JSON.stringify({t:Game.time,phase:m.phase,why:m.why,force:m.force||0,held:m.held,'
     'spawns:r.find(FIND_MY_SPAWNS).map(s=>[s.pos.x,s.pos.y]),site:ss?[ss.progress,ss.progressTotal]:null,'
     'hostiles:r.find(FIND_HOSTILE_CREEPS).map(h=>[h.owner.username,h.pos.x,h.pos.y]),n9ago:Game.time-(Memory.ops.w8n9a||0),'
     'energy:r.energyAvailable+"/"+r.energyCapacityAvailable,storage:r.storage&&r.storage.store.energy})})()')
E2 = H + ('st=r.find(FIND_STRUCTURES),k=t=>_.filter(Game.creeps,c=>c.memory.home=="W47N8"&&c.memory.role==t);return JSON.stringify({'
     'towers:st.filter(s=>s.structureType=="tower").map(s=>s.store.energy),wallMin:_.min(st.filter(s=>(s.structureType=="constructedWall"||s.structureType=="rampart")&&s.pos.y==3).map(s=>s.hits)),'
     'builders:k("w8builder").map(c=>[c.pos.x,c.pos.y,c.store.energy,c.ticksToLive]),guard:k("w8guard").map(c=>[c.pos.x,c.pos.y,c.ticksToLive])})})()')
out = {}
for E in (E1, E2):
    r = q(E); v = r.get('v') if isinstance(r, dict) else r
    out.update(json.loads(v) if isinstance(v, str) else v)
print(json.dumps(out, indent=1))
