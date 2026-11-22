#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

with db.connect() as c:
    print("=== room_stats tips ===")
    for r in c.execute("SELECT room, max(tick), max(ts) FROM room_stats GROUP BY room ORDER BY 1"):
        print(" ", r)
    tip = c.execute("SELECT max(tick) FROM room_stats WHERE room='W46N8'").fetchone()[0]
    print("home tip", tip)

    print("=== last-seen reserver-like creeps in last 2000t ===")
    rows = c.execute(
        """SELECT creep, role, min(tick), max(tick)
             FROM creep_ticks
            WHERE tick>=%s
              AND (role IN ('reserver','reserve7') OR creep LIKE 'reserver%%' OR creep LIKE 'reserve7%%')
            GROUP BY 1,2 ORDER BY 4 DESC""",
        (tip - 2000,),
    ).fetchall()
    for r in rows[:40]:
        print(" ", r)
    print("n_creeps", len(rows))

    print("=== reserver counts every 20 ticks last 2000t ===")
    rows = c.execute(
        """SELECT (tick/20)*20 AS bucket,
                  count(DISTINCT creep) FILTER (WHERE role='reserver' OR creep LIKE 'reserver%%') AS n_reserver,
                  count(DISTINCT creep) FILTER (WHERE role='reserve7' OR creep LIKE 'reserve7%%') AS n_reserve7
             FROM creep_ticks
            WHERE tick>=%s AND tick<=%s
              AND (role IN ('reserver','reserve7') OR creep LIKE 'reserver%%' OR creep LIKE 'reserve7%%')
            GROUP BY 1 ORDER BY 1""",
        (tip - 2000, tip),
    ).fetchall()
    prev = None
    for b, nr, n7 in rows:
        if prev is not None and b - prev > 20:
            print(f"  GAP {prev+20}..{b-20}")
        flag = (nr != 3) or (n7 != 0) or prev is None or b >= tip - 300
        if flag:
            print(f"  {b} reserver={nr} reserve7={n7}")
        prev = b
    print("nonzero buckets", len(rows), "first", rows[0] if rows else None, "last", rows[-1] if rows else None)

    print("=== critical role presence last 300t at tip-like ticks ===")
    rows = c.execute(
        """SELECT role, count(DISTINCT creep), min(tick), max(tick)
             FROM creep_ticks
            WHERE tick>=%s
              AND role IN ('reserver','reserve7','miner','queen','rminer','w8filler','w8miner','upgrader','w8upgrader','defender','hauler','w8hauler')
            GROUP BY 1 ORDER BY 1""",
        (tip - 300,),
    )
    for r in rows:
        print(" ", r)

    print("=== incidents since 84419260 ===")
    try:
        cols = [x[0] for x in c.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='incidents' ORDER BY 1"
        ).fetchall()]
        print("cols", cols)
        rows = c.execute("SELECT * FROM incidents WHERE tick>=84419260 ORDER BY tick").fetchall()
        print("n", len(rows))
        for r in rows[:40]:
            print(" ", r)
    except Exception as e:
        print("incidents", e)

    print("=== room_stats columns ===")
    cols = [x[0] for x in c.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name='room_stats' ORDER BY ordinal_position"
    ).fetchall()]
    print(cols)
