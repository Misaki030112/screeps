#!/usr/bin/env python3
import json, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
ROOMS=("W46N8","W47N8","W45N8","W45N7","W47N7")
JP=84396800
HK=ZoneInfo("Asia/Hong_Kong")
TICK_S=4.279
OUT="/workspace/screeps/state/_patrol_2026-11-21_1618/late_retry.json"

def db_range(c, room, base):
    t0,t1=base+1,base+100
    row=c.execute("SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",(room,t0,t1)).fetchone()
    return row[0] or 0, row[1], row[2], row[3] or 0

gt=api.game_time() if hasattr(api,'game_time') else None
# fallback
if gt is None:
    # history_backfill / api typical
    try:
        gt=hb.game_time()
    except Exception:
        import inspect
        print('api attrs', [a for a in dir(api) if not a.startswith('_')])
        print('hb game', [a for a in dir(hb) if 'time' in a.lower() or 'now' in a.lower() or 'gt'==a])
        raise
print('gt', gt, 'at', datetime.now(HK).strftime('%Y-%m-%d %H:%M:%S Asia/Hong_Kong'), flush=True)
now_ts=time.time()
recs=[]
for room in ROOMS:
    j=hb.history_get(room, JP)
    time.sleep(hb.GAP_S)
    rec={"room":room,"base":JP,"status":404 if not j else 200,"at":datetime.now(HK).strftime('%Y-%m-%d %H:%M:%S Asia/Hong_Kong'),"gt":gt}
    print(('  404' if not j else '  200')+f' {room}@{JP}', flush=True)
    if not j:
        rec['inserted']=0
        recs.append(rec)
        continue
    rec['nticks']=len(j.get('ticks') or {})
    state={}
    prev=hb.history_get(room, JP-100)
    time.sleep(hb.GAP_S)
    if prev:
        for _t, objs in hb.merge_chunk(prev, state):
            pass
        rec['seeded']=True
    our=hb.uid()
    with db.connect() as c:
        cm=db.current_commit(c)
    rows=[]
    tmin=tmax=None
    for tick, objs in hb.merge_chunk(j, state):
        ts=hb.tick_time(now_ts, gt, tick, TICK_S)
        rows.extend(hb.creep_rows(tick, room, objs, our, ts, cm))
        tmin=tick if tmin is None else min(tmin, tick)
        tmax=tick if tmax is None else max(tmax, tick)
    rec['tmin']=tmin; rec['tmax']=tmax; rec['nrows']=len(rows)
    if rows:
        with db.connect() as c:
            n=hb.insert_creeps(c, rows) if hasattr(hb,'insert_creeps') else None
            if n is None:
                # fallback to history_backfill insert path
                n=0
                try:
                    n=hb.upsert_creep_ticks(c, rows)
                except Exception as e:
                    # try common names
                    print('  insert method?', e)
                    n=0
            rec['inserted']=n
            print(f"  {room}@{JP} ticks={rec['nticks']} range={tmin}..{tmax} inserted={n}", flush=True)
    else:
        rec['inserted']=0
        print(f"  empty {room}@{JP} ticks={rec.get('nticks')}", flush=True)
    recs.append(rec)

with db.connect() as c:
    post={}
    for room in ROOMS:
        d,mn,mx,n=db_range(c, room, JP)
        post[room]={"distinct":d,"min":mn,"max":mx,"rows":n}
        print(f"  post {room}@{JP} distinct={d}/100 min={mn} max={mx} rows={n}", flush=True)
open(OUT,'w').write(json.dumps({"gt":gt,"recs":recs,"post":post}, indent=2, default=str)+"\n")
print('wrote', OUT)
