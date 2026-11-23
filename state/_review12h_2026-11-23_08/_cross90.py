#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db as dbmod
CAP = 10935000
THRESH = int(CAP * 0.90)  # 9841500
conn = dbmod.connect()
cur = conn.cursor()
cur.execute("""
SELECT tick, ts, progress, storage
FROM room_stats
WHERE room='W46N8' AND progress >= %s
ORDER BY tick ASC
LIMIT 3
""", (THRESH,))
print("first >=90% rows:")
for r in cur.fetchall():
    print(r)
cur.execute("""
SELECT tick, ts, progress, storage
FROM room_stats
WHERE room='W46N8' AND tick >= 84420960 AND tick <= 84430950 AND progress < %s
ORDER BY tick DESC
LIMIT 3
""", (THRESH,))
print("last <90% in window:")
for r in cur.fetchall():
    print(r)
# pause sum
cur.execute("""
SELECT count(*), sum((data->>'sec')::int)
FROM events
WHERE kind='box_pause' AND ts >= '2026-11-22 20:30:49+08' AND ts <= '2026-11-23 08:23:33+08'
""")
print("box_pause from events table:", cur.fetchone())
# maybe different table - just print count of what we have
conn.close()

secs = [596,1120,1334,459,595,378,672,901,515,421,432,371,878,332,545,1075,251,307,1300,200]
print("manual sum pauses", len(secs), sum(secs), sum(secs)/3600)
print("90% thresh", THRESH)
