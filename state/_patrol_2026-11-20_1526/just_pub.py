import sys, time, json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
TICK_S = 4.168
now_ts = datetime.now(timezone.utc)
gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
print("game.time", gt, "at", datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), flush=True)
our = hb.uid()
with db.connect() as c:
    cm = db.current_commit(c)

def insert_chunk(room, base):
    j = hb.history_get(room, base)
    time.sleep(hb.GAP_S)
    rec = {"room": room, "base": base, "status": 404 if not j else 200}
    if not j:
        print(f"  404 {room}@{base}", flush=True)
        return rec
    rec["nticks"] = len(j.get("ticks") or {})
    rec["ts"] = j.get("timestamp")
    state = {}
    prev = hb.history_get(room, base - 100)
    time.sleep(hb.GAP_S)
    if prev:
        for _tick, objs in hb.merge_chunk(prev, state):
            pass
        rec["seeded"] = True
    else:
        rec["seeded"] = False
    rows = []
    tmin = tmax = None
    for tick, objs in hb.merge_chunk(j, state):
        ts = hb.tick_time(now_ts, gt, tick, TICK_S)
        rows.extend(hb.creep_rows(tick, room, objs, our, ts, cm))
        tmin = tick if tmin is None else min(tmin, tick)
        tmax = tick if tmax is None else max(tmax, tick)
    rec["tmin"] = tmin
    rec["tmax"] = tmax
    rec["nrows"] = len(rows)
    if not rows:
        print(f"  empty {room}@{base} ticks={rec['nticks']}", flush=True)
        return rec
    with db.connect() as c:
        exist = hb.already(c, tmin, tmax, [room])
    new_rows = [r for r in rows if (r[3], r[1]) not in exist]
    if new_rows:
        sql = ("INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) "
               "SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s "
               "WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)")
        packed = [r + (r[3], r[1]) for r in new_rows]
        with db.connect(autocommit=False) as c:
            with c.cursor() as cur:
                cur.executemany(sql, packed)
            c.commit()
    nfix = 0
    with db.connect(autocommit=False) as c:
        nfix = hb.realign_ts(c, tmin, tmax, [room], now_ts, gt, TICK_S)
        c.commit()
    rec["inserted"] = len(new_rows)
    rec["ts_realigned"] = nfix
    print(f"  {room}@{base} status=200 ticks={rec['nticks']} range={tmin}..{tmax} inserted={len(new_rows)} realign={nfix}", flush=True)
    return rec

results = []
print("=== refill W45N7@84375400 ===", flush=True)
results.append(insert_chunk("W45N7", 84375400))
print("=== just-published 84375500 all 5 ===", flush=True)
for room in ROOMS:
    results.append(insert_chunk(room, 84375500))
print("=== coverage after ===", flush=True)
c = db.connect()
for room in ROOMS:
    for lo, hi, lab in [(84375447, 84375499, "75447-499"), (84375501, 84375600, "75501-600"), (84375391, 84375569, "freeze")]:
        n = c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s", (room, lo, hi)).fetchone()[0]
        print(f"  {room} {lab} {n}/{hi-lo+1}")
path = "/workspace/screeps/state/_patrol_2026-11-20_1526/just_published.json"
open(path, "w").write(json.dumps(results, indent=2, default=str)+chr(10))
print("wrote", path, flush=True)
print("done", flush=True)
