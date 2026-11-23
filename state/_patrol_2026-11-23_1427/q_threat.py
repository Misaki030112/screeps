#!/usr/bin/env python3
import json, sys
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
import db

OUT = Path("/workspace/screeps/state/_patrol_2026-11-23_1427")

def run(name, expr, slen=3500):
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=40)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:slen], flush=True)
        return r
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
        return None

run("host", "(()=>{const rooms=['W46N8','W47N8','W45N8','W45N7','W47N7'];const out={t:Game.time};for(const n of rooms){const rm=Game.rooms[n];if(!rm){out[n]={vis:false};continue;}const hc=rm.find(FIND_HOSTILE_CREEPS);const hs=rm.find(FIND_HOSTILE_STRUCTURES).filter(s=>s.structureType==STRUCTURE_INVADER_CORE||s.owner);out[n]={vis:true,hc:hc.length,hs:hs.length,host:hc.map(c=>({n:c.name,o:c.owner&&c.owner.username,x:c.pos.x,y:c.pos.y,hits:c.hits,bl:c.body.length})),core:hs.filter(s=>s.structureType==STRUCTURE_INVADER_CORE).length};}return out;})()")

run("ups", "(()=>{const out={t:Game.time,up:[],w8up:[],guards:[],res:[]};for(const n in Game.creeps){const cr=Game.creeps[n];const r=(cr.memory&&cr.memory.role)||'';const rec={n,r,rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,sp:!!cr.spawning,ttl:cr.ticksToLive||0,e:cr.store&&cr.store.energy,hits:cr.hits,st:cr.memory&&cr.memory.st};if(r==='upgrader')out.up.push(rec);else if(r==='w8upgrader')out.w8up.push(rec);else if(r==='w8guard'||r==='guard'||/def/i.test(r))out.guards.push(rec);else if(r==='reserver'||r==='reserve7')out.res.push(rec);}return out;})()")

run("opsx", "(()=>{const o=Memory.ops||{};const d=o.w8day||{};return {t:Game.time,w8threat:o.w8threat,w8flee:o.w8flee,w8inv:o.w8inv,sealPark:o.w8sealPark,labReady:o.labReady,r7:o.r7,recycle:o.w8recycle,w8soft:o.w8soft,day:{sealPark:d.sealPark,threatSoft:d.threatSoft,softCap2:d.softCap2,bankWhy:d.bankWhy,upgKeep:d.upgKeep,upgCeil:d.upgCeil,upLatched:d.upLatched,upArm:d.upArm,storE:d.storE,feedOk:d.feedOk,hubReady:d.hubReady,nf:d.nf,upgraders:d.upgraders}};})()")

# DB section even if live queries fail
c = db.connect()
print("=== room_stats hostiles/storage around threat 84410850 ===", flush=True)
for room in ("W46N8","W47N8","W47N7","W45N8","W45N7"):
    print(f"-- {room} --", flush=True)
    rows = c.execute("""
        SELECT tick, ts, storage, progress, cpu, bucket, hostiles, energy, creeps
        FROM room_stats
        WHERE room=%s AND tick BETWEEN 84411300 AND 84412500
        ORDER BY tick
    """, (room,)).fetchall()
    if not rows:
        print("  no rows")
        continue
    print("  n", len(rows), "range", rows[0][0], rows[-1][0], "host_max", max((r[6] or 0) for r in rows),
          "stor", min((r[2] or 0) for r in rows), max((r[2] or 0) for r in rows))
    prev = None
    for r in rows:
        tick, ts, stor, prog, cpu, bkt, host, en, crp = r
        flag = False
        if (host or 0) > 0: flag = True
        if prev and tick - prev > 15: flag = True
        if tick in (84411380, 84411420, 84411621, 84411889, 84411900, 84412000, 84412100, 84412200): flag = True
        if flag:
            gap = (tick - prev) if prev else 0
            print(f"  t={tick} ts={ts} stor={stor} host={host} cpu={cpu} bkt={bkt} e={en} creeps={crp} dtick={gap}")
        prev = tick

print("=== W46N8 storage since last tip 84411380 ===", flush=True)
rows = c.execute("""
    SELECT tick, ts, storage, progress FROM room_stats
    WHERE room='W46N8' AND tick>=84411380 ORDER BY tick
""").fetchall()
unders = [r for r in rows if (r[2] or 0) < 15000]
print("n", len(rows), "min", min(r[2] for r in rows) if rows else None, "max", max(r[2] for r in rows) if rows else None,
      "under_n", len(unders), "first_under", unders[0] if unders else None, "last_under", unders[-1] if unders else None,
      "last", rows[-1] if rows else None)
span = None
spans = []
for r in rows:
    if (r[2] or 0) < 15000:
        if span is None: span = [r, r]
        else: span[1] = r
    else:
        if span: spans.append(span); span=None
if span: spans.append(span)
for a,b in spans:
    print(f"  under span {a[0]}@{a[1]} stor={a[2]} -> {b[0]}@{b[1]} stor={b[2]} ticks={b[0]-a[0]+1}")

print("=== W47N8 storage since last tip ===", flush=True)
rows = c.execute("""
    SELECT tick, ts, storage FROM room_stats
    WHERE room='W47N8' AND tick>=84411380 ORDER BY tick
""").fetchall()
if rows:
    print("n", len(rows), "min", min(r[2] for r in rows), "max", max(r[2] for r in rows), "last", rows[-1])
    n40 = [r for r in rows if (r[2] or 0) >= 40000]
    print("n>=40k", len(n40))

print("=== defender/guard roles around threat ===", flush=True)
for row in c.execute("""
    SELECT room, role, count(distinct creep), count(*), min(tick), max(tick)
    FROM creep_ticks
    WHERE tick BETWEEN 84411380 AND 84412500
      AND (role ILIKE '%def%' OR role ILIKE '%guard%' OR creep ILIKE '%def%' OR creep ILIKE '%guard%')
    GROUP BY 1,2
    ORDER BY 1,2
"""):
    print(" ", row)

print("=== defender/guard names ===", flush=True)
for row in c.execute("""
    SELECT distinct room, creep, role FROM creep_ticks
    WHERE tick BETWEEN 84411380 AND 84412500
      AND (role ILIKE '%def%' OR role ILIKE '%guard%' OR creep ILIKE '%def%' OR creep ILIKE '%guard%')
    ORDER BY 1,2
"""):
    print(" ", row)

print("=== STATS gaps (freeze fill check) ===", flush=True)
for label, fr, to in [
    ("freeze 09:41-09:59", "2026-11-22 09:41:41", "2026-11-22 09:59:05"),
    ("freeze 10:16-10:22", "2026-11-22 10:16:39", "2026-11-22 10:22:23"),
]:
    print(f"-- {label} --")
    for room in ("W46N8","W47N8","W45N8","W45N7","W47N7"):
        rows = c.execute("""
            SELECT min(tick), max(tick), count(*) FROM room_stats
            WHERE room=%s AND ts >= %s AND ts <= %s
        """, (room, fr, to)).fetchone()
        before = c.execute("""
            SELECT tick, ts FROM room_stats WHERE room=%s AND ts < %s ORDER BY ts DESC LIMIT 1
        """, (room, fr)).fetchone()
        after = c.execute("""
            SELECT tick, ts FROM room_stats WHERE room=%s AND ts > %s ORDER BY ts ASC LIMIT 1
        """, (room, to)).fetchone()
        print(f"  {room} inside={rows} before={before} after={after}")
