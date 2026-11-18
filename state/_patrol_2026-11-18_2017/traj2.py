#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()
LAST, TIP = 84339840, 84340620

def traj(name, lo=LAST-400, hi=TIP+200):
    rows = c.execute(
        """SELECT tick, room, x, y, store, state, role
        FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick""",
        (name, lo, hi),
    ).fetchall()
    if not rows:
        print(name, "NO ROWS")
        return
    first, last = rows[0], rows[-1]
    print(f"{name} n={len(rows)} first={first} last={last}")
    # compact path: print when pos/state/room changes, plus every ~40t
    prev = None
    shown = 0
    for i, r in enumerate(rows):
        t, rm, x, y, st, state, role = r
        key = (rm, x, y, state, st)
        if prev is None or key[:4] != prev[:4] or (i % 80 == 0) or i == len(rows)-1:
            print(f"  {t} {rm} {x},{y} store={st} state={state}")
            shown += 1
        prev = key
    # seat detect for w8 / home upgraders
    seats = [r for r in rows if r[1]=="W47N8" and r[2] is not None and 11<=r[2]<=15 and 24<=r[3]<=29]
    hseats = [r for r in rows if r[1]=="W46N8" and r[2] is not None and 28<=r[2]<=32 and 28<=r[3]<=32]
    r7 = [r for r in rows if r[1]=="W47N7" and r[2] is not None and r[2]>=35 and r[3]>=25]
    n7 = [r for r in rows if r[1]=="W45N7" and r[2] is not None and r[2]<=8 and r[3]>=36]
    if seats:
        loaded = next((r for r in seats if (r[4] or 0) > 0), None)
        print(f"  W47seat first={seats[0][:5]} last={seats[-1][:5]} first_loaded={loaded[:5] if loaded else None}")
    if hseats:
        loaded = next((r for r in hseats if (r[4] or 0) > 0), None)
        print(f"  HOMEseat first={hseats[0][:5]} last={hseats[-1][:5]} first_loaded={loaded[:5] if loaded else None}")
    if r7:
        print(f"  r7seat first={r7[0][:5]} last={r7[-1][:5]}")
    if n7:
        print(f"  W45N7seat first={n7[0][:5]} last={n7[-1][:5]}")

for name in [
    "w8upgrader84339813", "w8upgrader84339311", "w8upgrader84338374",
    "upgrader84339923", "upgrader84340223", "upgrader84338454",
    "reserve784339755", "reserver84340009", "reserver84340531", "reserver84339541",
    "w8guard84338872",
    "w8hauler84338988",
]:
    print("=" * 60)
    traj(name)

# later room_stats after TIP
print("=== later room_stats after TIP ===")
for room in ("W46N8", "W47N8"):
    rows = c.execute(
        "SELECT tick, ts, storage, progress, cpu, bucket, creeps FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick",
        (room, TIP),
    ).fetchall()
    print(room, "n", len(rows))
    for r in rows[-6:]:
        print(" ", r)
