#!/usr/bin/env python3
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db, history_backfill as hb, api

HK = ZoneInfo("Asia/Hong_Kong")
c = db.connect()

def p(*a):
    print(*a, flush=True)

p("=== W47 progress samples 84378400..now ===")
rows = c.execute("""
  SELECT tick, ts, progress, storage FROM room_stats
  WHERE room='W47N8' AND tick>=84378400 ORDER BY tick
""").fetchall()
prev=None
for tick,ts,prog,stor in rows:
    dprog = (prog-prev[2]) if prev else None
    dt = (tick-prev[0]) if prev else None
    et = (round(dprog/dt,2) if dprog is not None and dt else None)
    p(f"  {tick} {ts} p={prog} stor={stor} d={dprog} dt={dt} et={et}")
    prev=(tick,ts,prog,stor)

p("=== events around 84379000 (non-watch) ===")
rows = c.execute("""
  SELECT tick, ts, type, room, creep, data
  FROM events
  WHERE tick>=84378900
  ORDER BY tick
""").fetchall()
# filter watch spam
n=0
for r in rows:
    typ = r[2]
    if typ in ("watch","stats","cpu"): 
        continue
    p(r)
    n+=1
p("nonwatch n", n, "total", len(rows))

p("=== incidents since 84378900 ===")
try:
    for r in c.execute("SELECT * FROM incidents WHERE tick>=84378900 ORDER BY tick").fetchall():
        p(r)
except Exception as e:
    p("inc err", e)
    c.rollback()

p("=== hostiles in room_stats W47 since 84378800 ===")
for r in c.execute("""
  SELECT tick, ts, hostiles, storage, cpu FROM room_stats
  WHERE room='W47N8' AND tick>=84378800 AND (hostiles IS NOT NULL)
  ORDER BY tick
""").fetchall():
    if r[2] and r[2] != 0 and r[2] != '0' and r[2] != {}:
        p("nonzero", r)
# also print last 15
p("-- last 15 --")
for r in c.execute("""
  SELECT tick, ts, hostiles, storage FROM room_stats
  WHERE room='W47N8' AND tick>=84378950 ORDER BY tick
""").fetchall()[-20:]:
    p(r)

p("=== 12h/24h/8h/6h/3h storage max ===")
for room in ("W46N8","W47N8"):
    for label, ticks in (("3h", 2600), ("6h", 5200), ("8h", 7000), ("12h", 10300), ("24h", 20600)):
        row = c.execute("""
          SELECT max(storage), (array_agg(tick ORDER BY storage DESC))[1],
                 (array_agg(ts ORDER BY storage DESC))[1]
          FROM room_stats WHERE room=%s AND tick>= (SELECT max(tick) FROM room_stats WHERE room=%s) - %s
        """, (room, room, ticks)).fetchone()
        p(room, label, row)

p("=== retry new 404s ===")
now_ts = datetime.now(timezone.utc)
gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
p("game.time", gt, "at", datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"))
results=[]
for room, base in [("W45N8", 84378900), ("W47N7", 84378900), ("W47N7", 84378000), ("W46N8", 84377600)]:
    j = hb.history_get(room, base)
    time.sleep(getattr(hb, "GAP_S", 0.35))
    if not j:
        p(f"  still 404 {room}@{base}")
        results.append({"room":room,"base":base,"status":404,"gt":gt})
        continue
    p(f"  200 {room}@{base} ticks={len(j.get('ticks') or {})}")
    # insert
    rec_status = 200
    state = {}
    prev = hb.history_get(room, base-100)
    time.sleep(getattr(hb, "GAP_S", 0.35))
    if prev:
        for _tick, objs in hb.merge_chunk(prev, state):
            pass
    our = hb.uid()
    with db.connect() as cx:
        cm = db.current_commit(cx)
    rows=[]
    tmin=tmax=None
    TICK_S=4.244
    for tick, objs in hb.merge_chunk(j, state):
        ts = hb.tick_time(now_ts, gt, tick, TICK_S)
        rows.extend(hb.creep_rows(tick, room, objs, our, ts, cm))
        tmin = tick if tmin is None else min(tmin, tick)
        tmax = tick if tmax is None else max(tmax, tick)
    if not rows:
        p(f"    empty rows ticks={len(j.get('ticks') or {})}")
        results.append({"room":room,"base":base,"status":200,"inserted":0,"gt":gt})
        continue
    with db.connect() as cx:
        exist = hb.already(cx, tmin, tmax, [room])
    new_rows = [r for r in rows if (r[3], r[1]) not in exist]
    if new_rows:
        sql = ("INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) "
               "SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s "
               "WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)")
        packed = [r + (r[3], r[1]) for r in new_rows]
        with db.connect(autocommit=False) as cx:
            with cx.cursor() as cur:
                cur.executemany(sql, packed)
            cx.commit()
    p(f"    inserted={len(new_rows)} range={tmin}..{tmax}")
    results.append({"room":room,"base":base,"status":200,"inserted":len(new_rows),"tmin":tmin,"tmax":tmax,"gt":gt})

Path = __import__("pathlib").Path
Path("/workspace/screeps/state/_patrol_2026-11-20_1923/retry_new404.json").write_text(__import__("json").dumps(results, indent=2)+"\n")
p("wrote retry_new404.json")
