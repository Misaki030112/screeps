#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

c = db.connect()
# columns of creep_ticks
cols = c.execute(
    "SELECT column_name FROM information_schema.columns WHERE table_name='creep_ticks' ORDER BY ordinal_position"
).fetchall()
print("creep_ticks cols", [x[0] for x in cols])

print("\n=== room_stats hostiles>0 since 84443730 ===")
rows = c.execute(
    """
    SELECT room, tick, ts, hostiles, sites, storage, energy
    FROM room_stats
    WHERE tick >= 84443730 AND hostiles > 0
    ORDER BY tick, room
    """
).fetchall()
print("n", len(rows))
for row in rows[:80]:
    print(row)
if len(rows) > 80:
    print("... more", len(rows) - 80)

print("\n=== W47N8 sites>0 last and first-zero after last patrol ===")
for row in c.execute(
    """
    SELECT tick, ts, sites, storage
    FROM room_stats
    WHERE room='W47N8' AND tick>=84443730 AND sites>0
    ORDER BY tick DESC LIMIT 5
    """
):
    print("site", row)
z = c.execute(
    """
    SELECT min(tick), min(ts)
    FROM room_stats
    WHERE room='W47N8' AND tick>=84443730 AND sites=0
    """
).fetchone()
print("first sites=0", z)

print("\n=== events since 84443730 (non-boring) ===")
for row in c.execute(
    """
    SELECT ts, tick, kind, room, severity, episode, msg
    FROM events
    WHERE tick>=84443730 OR ts >= '2026-11-23 23:28:00'
    ORDER BY ts, tick
    """
):
    print(row)

print("\n=== incidents since 84443730 ===")
for row in c.execute(
    """
    SELECT ts, tick, remote, inc, ev, from_state, state, why, inv, inv_ttl, def, dur
    FROM incidents
    WHERE tick>=84443730 OR ts >= '2026-11-23 23:28:00'
    ORDER BY ts, tick
    """
):
    print(row)

print("\n=== defender/guard names since 84443730 ===")
for row in c.execute(
    """
    SELECT name, min(tick) mint, max(tick) maxt, min(room), max(room),
           min(hits), max(hits), count(DISTINCT tick) n
    FROM creep_ticks
    WHERE tick>=84443730
      AND (name LIKE 'rdef%' OR name LIKE '%guard%' OR name LIKE 'w8def%' OR name LIKE 'w8guard%'
           OR role IN ('defender','guard','w8defender','w8guard'))
    GROUP BY name
    ORDER BY min(tick)
    """
):
    print(row)

print("\n=== rdef84444671 first/last/hits-drop ===")
rows = c.execute(
    """
    SELECT tick, ts, room, x, y, hits, role
    FROM creep_ticks
    WHERE name='rdef84444671'
    ORDER BY tick
    """
).fetchall()
print("n", len(rows))
if rows:
    print("first", rows[0])
    print("last", rows[-1])
    prev = None
    for r in rows:
        if prev and (r[2] != prev[2] or r[5] != prev[5]):
            print("change", prev, "->", r)
        prev = r

print("\n=== room_stats max/min storage this window ===")
for room in ("W46N8", "W47N8"):
    row = c.execute(
        """
        SELECT min(storage), max(storage),
               (array_agg(tick ORDER BY storage) )[1] as min_tick,
               (array_agg(ts ORDER BY storage) )[1] as min_ts,
               (array_agg(tick ORDER BY storage DESC) )[1] as max_tick,
               (array_agg(ts ORDER BY storage DESC) )[1] as max_ts
        FROM room_stats
        WHERE room=%s AND tick BETWEEN 84443731 AND 84446200
        """,
        (room,),
    ).fetchone()
    print(room, row)

print("\n=== STATS gaps: room_stats ticks missing in 10-tick grid? look at freeze 02:03 ===")
# last room_stats before 02:03 and first after 02:21
for room in ("W46N8", "W47N8"):
    row = c.execute(
        """
        SELECT tick, ts, storage FROM room_stats
        WHERE room=%s AND ts < '2026-11-24 02:03:03+08' AND tick>=84443730
        ORDER BY tick DESC LIMIT 3
        """,
        (room,),
    ).fetchall()
    print(room, "before freeze", row)
    row = c.execute(
        """
        SELECT tick, ts, storage FROM room_stats
        WHERE room=%s AND ts >= '2026-11-24 02:21:36+08'
        ORDER BY tick LIMIT 3
        """,
        (room,),
    ).fetchall()
    print(room, "after freeze", row)
