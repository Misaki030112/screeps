#!/usr/bin/env python3
import sys, json, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
import q as qmod

HK = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
jp_base = 84382400
OUT = Path("/workspace/screeps/state/_patrol_2026-11-21_0622")
gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
print("game.time", gt, "at", datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), flush=True)

with db.connect() as c:
    rows = c.execute(
        "SELECT tick,ts,remote,ev,from_state,state,why,inv,inv_ttl,def,dur FROM incidents WHERE inc=84381721 OR tick>=84381541 ORDER BY tick"
    ).fetchall()
    print("incidents related n", len(rows), flush=True)
    for r in rows:
        print(" ", r, flush=True)

    rows = c.execute(
        "SELECT tick, room, x, y, hits, state FROM creep_ticks WHERE creep='rdef84381722' ORDER BY tick LIMIT 15"
    ).fetchall()
    print("rdef first 15", flush=True)
    for r in rows:
        print(" ", r, flush=True)

    rows = c.execute(
        "SELECT tick, room, x, y, hits, state FROM creep_ticks WHERE creep='rdef84381722' ORDER BY tick DESC LIMIT 8"
    ).fetchall()
    print("rdef last 8", flush=True)
    for r in rows:
        print(" ", r, flush=True)

qs = [
    (
        "later",
        "({t:Game.time,b:Game.cpu.bucket,hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hp:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progress,wp:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progress,nUp:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.nUp,why:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.why,work:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.work,err:Memory.stats&&Memory.stats.lastErrorTick,alert:Memory.stats&&Memory.stats.lastAlertTick})",
    ),
    (
        "w8ups",
        "(()=>{const out={};for(const n in Game.creeps){const cr=Game.creeps[n];const role=(cr.memory||{}).role||'';if(role!=='w8upgrader'&&!n.startsWith('w8upgrader')&&role!=='w8miner'&&!n.startsWith('w8miner')&&role!=='reserve7'&&!n.startsWith('reserve7')&&role!=='defender'&&!n.startsWith('rdef')&&!n.startsWith('defender')&&role!=='reserver'&&!n.startsWith('reserver')&&role!=='upgrader'&&!n.startsWith('upgrader'))continue;out[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,sp:!!cr.spawning,e:cr.store&&cr.store.energy||0,hits:cr.hits,role:role||n};}return {t:Game.time,out};})()",
    ),
    (
        "resv2",
        "(()=>{const r={}; for (const n of ['W45N8','W45N7','W47N7']){ const rm=Game.rooms[n]; if(!rm){r[n]={vis:false}; continue;} const res=rm.controller&&rm.controller.reservation; r[n]={vis:true,res:res&&res.ticksToEnd,own:res&&res.username,host:rm.find(FIND_HOSTILE_CREEPS).length,core:rm.find(FIND_HOSTILE_STRUCTURES).filter(s=>s.structureType==STRUCTURE_INVADER_CORE).length};} return {t:Game.time,r};})()",
    ),
]
for name, expr in qs:
    print("QUERY", name, flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:3000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)

results = []
if gt >= jp_base + 100:
    print("=== just-published %s ===" % jp_base, flush=True)
    now_ts = datetime.now(timezone.utc)
    TICK_S = 4.263
    for room in ROOMS:
        j = hb.history_get(room, jp_base)
        time.sleep(hb.GAP_S)
        if not j:
            print("  404 %s@%s" % (room, jp_base), flush=True)
            results.append({"room": room, "status": 404})
            continue
        state = {}
        prev = hb.history_get(room, jp_base - 100)
        time.sleep(hb.GAP_S)
        if prev:
            for _t, _o in hb.merge_chunk(prev, state):
                pass
        our = hb.uid()
        with db.connect() as c:
            cm = db.current_commit(c)
        rows = []
        tmin = tmax = None
        for tick, objs in hb.merge_chunk(j, state):
            ts = hb.tick_time(now_ts, gt, tick, TICK_S)
            rows.extend(hb.creep_rows(tick, room, objs, our, ts, cm))
            tmin = tick if tmin is None else min(tmin, tick)
            tmax = tick if tmax is None else max(tmax, tick)
        if not rows:
            print("  empty %s@%s ticks=%s" % (room, jp_base, len(j.get("ticks") or {})), flush=True)
            results.append({"room": room, "status": 200, "inserted": 0, "nticks": len(j.get("ticks") or {})})
            continue
        with db.connect() as c:
            exist = hb.already(c, tmin, tmax, [room])
        new_rows = [r for r in rows if (r[3], r[1]) not in exist]
        if new_rows:
            sql = (
                "INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) "
                "SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s "
                "WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)"
            )
            packed = [r + (r[3], r[1]) for r in new_rows]
            with db.connect(autocommit=False) as c:
                with c.cursor() as cur:
                    cur.executemany(sql, packed)
                c.commit()
        print(
            "  %s@%s status=200 ticks=%s range=%s..%s inserted=%s"
            % (room, jp_base, len(j.get("ticks") or {}), tmin, tmax, len(new_rows)),
            flush=True,
        )
        results.append({"room": room, "status": 200, "inserted": len(new_rows), "tmin": tmin, "tmax": tmax})
    (OUT / "just_published_84382400.json").write_text(json.dumps({"gt": gt, "results": results}, indent=2) + "\n")
else:
    print("skip just-published, gt", gt, flush=True)
