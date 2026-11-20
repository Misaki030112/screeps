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

cols = [x[0] for x in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='events' ORDER BY ordinal_position").fetchall()]
p("event cols", cols)
# last 40 non-watch since 84378900
# guess kind column
kind = "kind" if "kind" in cols else ("ev" if "ev" in cols else cols[2])
p("using kind", kind)
rows = c.execute(f"SELECT * FROM events WHERE tick>=84378900 ORDER BY tick").fetchall()
p("n events since 84378900", len(rows))
for r in rows:
    s = str(r)
    if "watch" in s and "box_pause" not in s and "threat" not in s and "hostile" not in s and "invader" not in s.lower() and "guard" not in s.lower() and "alert" not in s.lower() and "error" not in s.lower():
        continue
    p(s[:400])

p("=== incidents all recent >=84378800 ===")
try:
    for r in c.execute("SELECT * FROM incidents WHERE tick>=84378800 ORDER BY tick").fetchall():
        p(r)
except Exception as e:
    p(e); c.rollback()

p("=== later home/w47 stor after tip ===")
for room in ("W46N8","W47N8"):
    rows = c.execute("SELECT tick, ts, progress, storage, cpu, hostiles, creeps FROM room_stats WHERE room=%s AND tick>=84379000 ORDER BY tick", (room,)).fetchall()
    for r in rows:
        host = r[5]
        creeps = r[6]
        p(room, r[0], r[1], "p", r[2], "stor", r[3], "cpu", r[4], "host", host)

p("=== 12h/24h storage max ===")
tip = 84379010
for room in ("W46N8","W47N8"):
    for label, dt in (("this-hour", 920), ("3h", 2600), ("6h", 5200), ("8h", 7000), ("12h", 10300), ("24h", 20600)):
        row = c.execute("""
          SELECT storage, tick, ts FROM room_stats
          WHERE room=%s AND tick BETWEEN %s AND %s
          ORDER BY storage DESC NULLS LAST LIMIT 1
        """, (room, tip-dt, tip)).fetchone()
        n40 = c.execute("SELECT count(*) FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s AND storage>=40000", (room, tip-dt, tip)).fetchone()[0]
        n20 = c.execute("SELECT count(*) FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s AND storage>=20000", (room, tip-dt, tip)).fetchone()[0]
        p(room, label, "max", row, "n>=40k", n40, "n>=20k", n20)

p("=== retry 404s ===")
now_ts = datetime.now(timezone.utc)
gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
p("game.time", gt, datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"))
results=[]
for room, base in [("W45N8", 84378900), ("W47N7", 84378900), ("W47N7", 84378000), ("W46N8", 84377600)]:
    j = hb.history_get(room, base)
    time.sleep(getattr(hb, "GAP_S", 0.35))
    if not j:
        p(f"  still 404 {room}@{base}")
        results.append({"room":room,"base":base,"status":404,"gt":gt})
        continue
    nt = len(j.get("ticks") or {})
    p(f"  200 {room}@{base} ticks={nt}")
    state = {}
    prev = hb.history_get(room, base-100)
    time.sleep(getattr(hb, "GAP_S", 0.35))
    if prev:
        for _tick, objs in hb.merge_chunk(prev, state):
            pass
    our = hb.uid()
    with db.connect() as cx:
        cm = db.current_commit(cx)
    rows=[]; tmin=tmax=None; TICK_S=4.244
    for tick, objs in hb.merge_chunk(j, state):
        ts = hb.tick_time(now_ts, gt, tick, TICK_S)
        rows.extend(hb.creep_rows(tick, room, objs, our, ts, cm))
        tmin = tick if tmin is None else min(tmin, tick)
        tmax = tick if tmax is None else max(tmax, tick)
    if not rows:
        p("    empty")
        results.append({"room":room,"base":base,"status":200,"inserted":0,"nticks":nt,"gt":gt})
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
from pathlib import Path
Path("/workspace/screeps/state/_patrol_2026-11-20_1923/retry_new404.json").write_text(json.dumps(results, indent=2)+"\n")

p("=== freeze2 fill after possible insert ===")
for room in ("W46N8","W47N8","W45N8","W45N7","W47N7"):
    n = c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN 84378861 AND 84378969", (room,)).fetchone()[0]
    p(room, f"{n}/109")

p("=== w8builder body/trace near tip ===")
for r in c.execute("""
  SELECT creep, min(tick), max(tick), count(*),
    (array_agg(room ORDER BY tick DESC))[1],
    (array_agg(x ORDER BY tick DESC))[1],
    (array_agg(y ORDER BY tick DESC))[1]
  FROM creep_ticks
  WHERE tick>=84378700 AND (creep ILIKE '%w8builder%' OR role ILIKE '%wbuilder%' OR role='wbuilder')
  GROUP BY creep
""").fetchall():
    p(r)

p("=== listener rot / commit_state hint ===")
