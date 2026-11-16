#!/usr/bin/env python3
"""Deep quantitative checks for 2026-11-17 07:26 1h patrol."""
from __future__ import annotations
import json, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
LAST_TIP = 84311550
TIP = None  # will refresh from db
T0, T1 = 84311701, 84312400  # official backfill window
OUT = Path("/workspace/screeps/state/_patrol_2026-11-17_0726")

def p(*a):
    print(*a)

def main():
    conn = db.connect()
    c = conn.cursor()
    # tip
    # discover columns actually present
    c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='room_stats' ORDER BY ordinal_position")
    cols = [r[0] for r in c.fetchall()]
    p("room_stats columns:", cols)

    c.execute("""
      SELECT room, max(tick), max(ts) FROM room_stats GROUP BY room ORDER BY 1
    """)
    p("room_stats max:", c.fetchall())

    c.execute("SELECT max(tick), max(ts) FROM room_stats WHERE room='W46N8'")
    tip, tip_ts = c.fetchone()
    p("HOME tip", tip, tip_ts)
    last = LAST_TIP

    # storage series + consec under 15k at tip and max consec
    c.execute("""
      SELECT tick, ts, storage, (creeps->>'upgrader')::int AS nup
      FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s
      ORDER BY tick
    """, (last-50, tip))
    rows = c.fetchall()
    under_runs=[]; cur=None
    max_under=0; tip_under=0
    last_under=False
    for tick,ts,stor,nup in rows:
        if stor is None: continue
        if stor < 15000:
            if cur is None: cur=[tick,tick,ts,ts,stor,stor,nup]
            else:
                cur[1]=tick; cur[3]=ts; cur[5]=min(cur[5],stor)
            last_under=True
        else:
            if cur:
                span=cur[1]-cur[0]+1
                under_runs.append(cur+[span])
                max_under=max(max_under, span)
                cur=None
            last_under=False
    if cur:
        span=cur[1]-cur[0]+1
        under_runs.append(cur+[span])
        max_under=max(max_under, span)
        tip_under = span
    p(f"storage under15k runs since {last-50} (n_runs={len(under_runs)} max_span={max_under} tip_consec_under={tip_under if last_under else 0}):")
    for r in under_runs:
        p(f"  {r[0]}..{r[1]} span={r[-1]} minstor={r[5]} {r[2]} -> {r[3]}")

    # 20k consecutive spans last 3h / 6h
    for hours,label in ((3,'3h'),(6,'6h')):
        c.execute("""
          SELECT tick, ts, storage FROM room_stats
          WHERE room='W46N8' AND ts >= %s ORDER BY tick
        """, (tip_ts - timedelta(hours=hours),))
        srows=c.fetchall()
        best=0; best_run=None; cur=None
        mx=0
        for tick,ts,stor in srows:
            if stor is None: continue
            mx=max(mx, stor)
            if stor>=20000:
                if cur is None: cur=[tick,tick,ts,ts,stor]
                else:
                    cur[1]=tick; cur[3]=ts; cur[4]=max(cur[4],stor)
            else:
                if cur:
                    span=cur[1]-cur[0]
                    if span>best:
                        best=span; best_run=cur+[span]
                cur=None
        if cur:
            span=cur[1]-cur[0]
            if span>best:
                best=span; best_run=cur+[span]
        p(f"20k/{label} maxstor={mx} best_span={best} run={best_run}")

    # CPU last 1h/2h from room_stats (sparse) and any cpu table
    c.execute("""
      SELECT count(*), min(cpu), max(cpu), avg(cpu), min(bucket), max(bucket), min(tick), max(tick)
      FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s AND cpu IS NOT NULL
    """, (tip-800, tip))
    p("cpu 1h-ish room_stats:", c.fetchall()[0])
    c.execute("""
      SELECT count(*), min(cpu), max(cpu), avg(cpu), min(bucket), max(bucket)
      FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s AND cpu IS NOT NULL
    """, (tip-1600, tip))
    p("cpu 2h-ish room_stats:", c.fetchall()[0])

    # room_stats gaps >=30t since last tip
    c.execute("""
      SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick
    """, (last-20,))
    prev=None
    p("room_stats gaps >=30t since last-20:")
    for tick,ts in c.fetchall():
        if prev and tick-prev[0]>=30:
            dt=(ts-prev[1]).total_seconds() if ts and prev[1] else None
            p(f"  {prev[0]}..{tick} dtick={tick-prev[0]} wall_s={None if dt is None else round(dt)} {prev[1]} -> {ts}")
        prev=(tick,ts)

    # nUp timeseries since last, compressed
    c.execute("""
      SELECT tick, ts, storage, (creeps->>'upgrader')::int nup,
             (creeps->>'w8upgrader')::int w8
      FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s
      ORDER BY tick
    """, (last, tip))
    rows=c.fetchall()
    p(f"nUp samples {len(rows)} from {last}..{tip}:")
    last_state=None
    for tick,ts,stor,nup,w8 in rows:
        st=(nup,w8)
        if st!=last_state:
            p(f"  {tick} {ts} stor={stor} nUp={nup} w8={w8}")
            last_state=st
    if rows:
        tick,ts,stor,nup,w8=rows[-1]
        p(f"  TIP {tick} {ts} stor={stor} nUp={nup} w8={w8}")

    # upgrader trajectories last hour from creep_ticks
    c.execute("""
      SELECT name, min(tick), max(tick), min(x) filter (where x is not null), max(x),
             min(y) filter (where y is not null), max(y),
             count(*), count(distinct tick),
             min(room), max(room)
      FROM creep_ticks
      WHERE tick BETWEEN %s AND %s
        AND (name LIKE 'upgrader%%' OR name LIKE 'w8upgrader%%')
      GROUP BY name ORDER BY min(tick)
    """, (last, tip))
    p("upgrader/w8upgrader presence:")
    for r in c.fetchall():
        p(" ", r)

    # last positions of living-ish home upgraders near tip
    c.execute("""
      SELECT name, tick, room, x, y, energy, hits, saying, intent
      FROM creep_ticks
      WHERE tick>=%s AND (name LIKE 'upgrader%%')
      ORDER BY tick DESC, name
      LIMIT 20
    """, (tip-30,))
    p("recent home upgrader ticks:")
    for r in c.fetchall():
        p(" ", r)

    # creep_ticks coverage per room official window and hour
    for tmin,tmax,label in ((T0,T1,'official40m'), (last+1, tip, 'hour_since_last')):
        p(f"=== coverage {label} {tmin}..{tmax} ===")
        for room in ROOMS:
            c.execute("""
              SELECT count(distinct tick), min(tick), max(tick), count(*)
              FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s
            """, (room, tmin, tmax))
            n,mn,mx,rows=c.fetchone()
            want=tmax-tmin+1
            p(f"  {room} distinct={n}/{want} min={mn} max={mx} rows={rows}")
            # missing spans
            c.execute("""
              WITH s AS (
                SELECT generate_series(%s,%s) AS tick
              ), g AS (
                SELECT s.tick, CASE WHEN c.tick IS NULL THEN 1 ELSE 0 END AS miss
                FROM s LEFT JOIN (SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s) c
                  ON c.tick=s.tick
              )
              SELECT min(tick), max(tick), count(*) FROM (
                SELECT tick, tick - row_number() OVER (ORDER BY tick) AS grp
                FROM g WHERE miss=1
              ) x GROUP BY grp ORDER BY 1
            """, (tmin,tmax,room,tmin,tmax))
            holes=c.fetchall()
            if holes:
                p(f"    holes ({len(holes)}): " + ", ".join(f"{a}..{b}({n})" for a,b,n in holes[:12]) + (" ..." if len(holes)>12 else ""))

    # W45N7 mid holes context: who was in room around 84309420-84309460
    p("=== W45N7 around mid holes 84309420-84309470 ===")
    c.execute("""
      SELECT tick, name, x, y, energy FROM creep_ticks
      WHERE room='W45N7' AND tick BETWEEN 84309400 AND 84309480
      ORDER BY tick, name
    """)
    rows=c.fetchall()
    # compress: presence by tick
    from collections import defaultdict
    by=defaultdict(list)
    for tick,name,x,y,en in rows:
        by[tick].append(f"{name}@{x},{y}")
    lastk=None
    for t in range(84309400,84309481):
        k=tuple(by.get(t,['EMPTY']))
        if k!=lastk:
            p(f"  {t} {list(k)}")
            lastk=k

    # remotes: rminer/reserver last positions
    p("=== remotes last positions (latest tick per name) ===")
    c.execute("""
      SELECT DISTINCT ON (name) name, tick, room, x, y, energy
      FROM creep_ticks
      WHERE tick>=%s AND (
        name LIKE 'rminer%%' OR name LIKE 'reserver%%' OR name LIKE 'reserve%%'
        OR name LIKE 'w8rminer%%' OR name LIKE 'defender%%' OR name LIKE 'w8guard%%'
        OR name LIKE 'rdef%%'
      )
      ORDER BY name, tick DESC
    """, (tip-500,))
    for r in c.fetchall():
        p(" ", r)

    # harvest / dropped? skip
    # ticks_to_downgrade / sma if columns exist
    for col in cols:
        if 'downgrade' in col.lower() or 'safe' in col.lower() or 'hostil' in col.lower() or 'controller' in col.lower():
            c.execute(f"SELECT room, tick, {col} FROM room_stats WHERE room IN ('W46N8','W47N8') AND tick=%s", (tip,))
            p(f"col {col}:", c.fetchall())

    # hostility in room_stats
    if 'n_hostiles' in cols or 'hostiles' in cols:
        hcol = 'n_hostiles' if 'n_hostiles' in cols else 'hostiles'
        c.execute(f"""
          SELECT room, tick, ts, {hcol} FROM room_stats
          WHERE tick BETWEEN %s AND %s AND {hcol} IS NOT NULL AND {hcol}::text NOT IN ('0','{{}}.','{{}}')
          ORDER BY tick
        """, (last, tip))
        hs=c.fetchall()
        p(f"nonzero hostiles since last: {len(hs)}")
        for r in hs[:30]:
            p(" ", r)

    # mineral / lab from room_stats if any
    for col in cols:
        if 'mineral' in col.lower() or 'lab' in col.lower() or 'term' in col.lower():
            p("maybe", col)

    conn.close()

if __name__ == '__main__':
    main()
