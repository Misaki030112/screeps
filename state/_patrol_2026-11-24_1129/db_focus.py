import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()

print("=== all incidents since 84448700 (full) ===")
rows = c.execute("SELECT tick, remote, inc, ev, from_state, state, why, inv, inv_ttl, def, dur FROM incidents WHERE tick>=84448700 ORDER BY tick").fetchall()
for r in rows:
    print(r)

print("=== W45N7 incident 84448747 later events any tick ===")
rows = c.execute("SELECT tick, ev, state, why, inv, def, dur, data FROM incidents WHERE inc=84448747 ORDER BY tick").fetchall()
print("n", len(rows))
for r in rows:
    print(r[0], r[1], r[2], r[3], r[4], r[5], r[6], str(r[7])[:400])

print("=== room_stats hostiles>0 since 84448790 ===")
rows = c.execute("SELECT tick, ts, room, hostiles, storage, energy FROM room_stats WHERE tick>=84448790 AND hostiles>0 ORDER BY tick").fetchall()
print("n", len(rows))
for r in rows[:80]:
    print(r)
if len(rows)>80:
    print("... more", len(rows)-80)

print("=== W47N8 room_stats around 84450050..84450180 ===")
rows = c.execute("SELECT tick, ts, hostiles, storage, energy, cpu, bucket FROM room_stats WHERE room=%s AND tick BETWEEN 84450050 AND 84450180 ORDER BY tick", ("W47N8",)).fetchall()
for r in rows:
    print(r)

print("=== latest room_stats both homes ===")
for room in ("W46N8","W47N8"):
    r = c.execute("SELECT tick, ts, progress, storage, energy, energy_cap, cpu, bucket, hostiles, commit, ctl, creeps FROM room_stats WHERE room=%s ORDER BY tick DESC LIMIT 1", (room,)).fetchone()
    print(room, r)

print("=== events around fights ===")
try:
    names = [d.name for d in c.execute("SELECT * FROM events LIMIT 0").description]
    print("event cols", names)
    rows = c.execute("SELECT * FROM events WHERE tick>=84448700 ORDER BY tick").fetchall()
    print("n events", len(rows))
    for r in rows[:60]:
        print(dict(zip(names, r)))
except Exception as e:
    print("events ERR", type(e).__name__, e)
