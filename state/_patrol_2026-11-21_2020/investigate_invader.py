#!/usr/bin/env python3
import sys, json
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db
HK = ZoneInfo("Asia/Hong_Kong")
OUT = "/workspace/screeps/state/_patrol_2026-11-21_2020/investigate_invader.txt"

# discover event-like tables/columns quickly via information_schema already known from prior patrols
q_tables = """
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND (
  table_name ILIKE '%event%' OR table_name ILIKE '%alert%' OR table_name ILIKE '%threat%'
  OR table_name ILIKE '%hostile%' OR table_name ILIKE '%invader%' OR table_name ILIKE '%console%'
)
ORDER BY 1
"""

def tick_hk(ts):
    if ts is None:
        return None
    if getattr(ts, 'tzinfo', None) is None:
        return str(ts)
    return ts.astimezone(HK).strftime("%Y-%m-%d %H:%M:%S")

lines = []
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    lines.append(s)

with db.connect() as c:
    tables = [r[0] for r in c.execute(q_tables).fetchall()]
    P("tables", tables)
    # room_stats hostiles
    try:
        rows = c.execute("""
          SELECT tick, ts, room, hostiles, energy, storage, bucket, cpu, progress
          FROM room_stats
          WHERE room IN ('W47N7','W47N8') AND tick >= 84399390
          AND (hostiles IS NOT NULL AND hostiles > 0)
          ORDER BY tick
          LIMIT 50
        """).fetchall()
        P("room_stats hostiles>0", len(rows))
        for r in rows[:30]:
            P(" ", dict(r) if hasattr(r,'keys') else r)
    except Exception as e:
        P("room_stats hostiles err", e)
        # probe columns
        cols = c.execute("""
          SELECT column_name FROM information_schema.columns
          WHERE table_name='room_stats' ORDER BY ordinal_position
        """).fetchall()
        P("room_stats cols", [x[0] for x in cols])

    # generic events
    for t in tables:
        cols = [x[0] for x in c.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position",
            (t,)
        ).fetchall()]
        P("schema", t, cols)

    # creep_ticks of the invader and early W47N7 around 84400180..
    rows = c.execute("""
      SELECT tick, ts, room, creep, role, x, y, hits, store, state
      FROM creep_ticks
      WHERE creep LIKE '%invader_W47N7_768%' OR creep LIKE 'invader_W47N7_768'
      ORDER BY tick LIMIT 30
    """).fetchall()
    P("invader rows first", len(rows))
    for r in rows[:20]:
        P(" ", r[0], tick_hk(r[1]), r[2], r[3], r[5], r[6], r[7])
    if rows:
        last = c.execute("""
          SELECT min(tick), max(tick), count(*), min(hits), max(hits)
          FROM creep_ticks WHERE creep LIKE '%invader_W47N7_768%'
        """).fetchone()
        P("invader span", last)

    # room_stats tips
    for tbl, cols in {
        "room_stats": "tick, ts, room",
    }.items():
        pass
    tips = c.execute("""
      SELECT room, max(tick), max(ts) FROM room_stats
      WHERE room IN ('W46N8','W47N8','W45N8','W45N7','W47N7')
      GROUP BY room ORDER BY 1
    """).fetchall()
    P("room_stats tip", tips)

    # console/events last hour mentioning W47N7 / THREAT / invader
    # try several tables
    for t in tables + ["events", "alerts", "console_events"]:
        pass

open(OUT,"w").write("\n".join(lines)+"\n")
print("wrote", OUT)
