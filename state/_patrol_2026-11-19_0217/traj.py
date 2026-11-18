#!/usr/bin/env python3
import sys, json
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

SH = ZoneInfo("Asia/Shanghai")
c = db.connect()
LAST, TIP = 84344440, None  # previous 1h patrol analysis tip; TIP from latest common room_stats
if TIP is None:
    both = c.execute("""
        SELECT a.tick FROM room_stats a
        JOIN room_stats b ON a.tick=b.tick AND b.room='W47N8'
        WHERE a.room='W46N8'
        ORDER BY a.tick DESC LIMIT 1
    """).fetchone()
    TIP = both[0] if both else c.execute("SELECT max(tick) FROM room_stats WHERE room='W46N8'").fetchone()[0]
    print('AUTO TIP', TIP, flush=True)

out = []

def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.append(s)

for table in ("room_stats", "creep_ticks", "creep_cpu"):
    p(table, c.execute(f"SELECT max(tick), now()-max(ts) FROM {table}").fetchone())

for hours, lo_div in ((12, 12 * 3600 / 4.4), (13, 13 * 3600 / 4.4)):
    lo = int(TIP - lo_div)
    for room in ("W46N8", "W47N8"):
        row = c.execute(
            "SELECT tick, ts, storage FROM room_stats WHERE room=%s AND tick>=%s ORDER BY storage DESC NULLS LAST LIMIT 1",
            (room, lo),
        ).fetchone()
        n40 = c.execute(
            "SELECT count(*) FROM room_stats WHERE room=%s AND tick>=%s AND storage>=40000",
            (room, lo),
        ).fetchone()[0]
        n20 = c.execute(
            "SELECT count(*) FROM room_stats WHERE room=%s AND tick>=%s AND storage>=20000",
            (room, lo),
        ).fetchone()[0]
        p(f"{hours}h", room, "max", row, "n>=40k", n40, "n>=20k", n20)

p("=== room_stats gaps >=30t since last ===")
rows = c.execute(
    "SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick",
    (LAST,),
).fetchall()
prev = None
for t, ts in rows:
    if prev and t - prev[0] >= 30:
        p(" gap", prev[0], prev[1], "->", t, ts, "dt", t - prev[0])
    prev = (t, ts)
p("samples", len(rows), "first", rows[0] if rows else None, "last", rows[-1] if rows else None)

p("=== critical role last/zero_runs since last ===")
rows = c.execute(
    "SELECT tick, ts, creeps FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick",
    (LAST,),
).fetchall()

def cnt(cr, role):
    if not cr:
        return 0
    if isinstance(cr, str):
        cr = json.loads(cr)
    return int(cr.get(role) or 0)

for role in (
    "miner", "queen", "rminer", "reserver", "reserve7", "upgrader",
    "w8filler", "w8miner", "w8rminer", "w8upgrader", "hauler", "builder",
):
    xs = [(r[0], r[1], cnt(r[2], role)) for r in rows]
    if not xs:
        continue
    zero = []
    run = None
    for t, ts, n in xs:
        if n == 0:
            if run is None:
                run = [t, t, ts, ts]
            else:
                run[1] = t
                run[3] = ts
        else:
            if run:
                zero.append((run[0], run[1], run[1] - run[0], str(run[2]), str(run[3])))
                run = None
    if run:
        zero.append((run[0], run[1], run[1] - run[0], str(run[2]), str(run[3])))
    nz = [x for x in xs if x[2] > 0]
    p(f"  {role}: last={xs[-1][2]} last_nz={nz[-1] if nz else None} zero_runs={zero[:6]}")

p("=== upgrader/reserver/guard trajectories ===")
creeps = c.execute(
    """SELECT DISTINCT name, role FROM creep_ticks
    WHERE tick BETWEEN %s AND %s AND role IN ('upgrader','w8upgrader','reserve7','reserver','w8guard','w8defender','rdef')
    ORDER BY role, name""",
    (LAST, TIP + 200),
).fetchall()
p("creeps", creeps)
for name, role in creeps:
    rows = c.execute(
        """SELECT tick, room, x, y, energy, spawning
        FROM creep_ticks WHERE name=%s AND tick BETWEEN %s AND %s ORDER BY tick""",
        (name, LAST - 200, TIP + 200),
    ).fetchall()
    if not rows:
        continue
    first, last = rows[0], rows[-1]
    seats = []
    for t, rm, x, y, e, sp in rows:
        if role == "w8upgrader" and rm == "W47N8" and x is not None and 11 <= x <= 15 and 24 <= y <= 29:
            seats.append((t, x, y, e, sp))
        if role == "upgrader" and rm == "W46N8" and x is not None and 28 <= x <= 32 and 28 <= y <= 32:
            seats.append((t, x, y, e, sp))
    first_seat = seats[0] if seats else None
    last_seat = seats[-1] if seats else None
    spawning = [r for r in rows if r[5]]
    p(
        f"  {name} {role} n={len(rows)} first={first} last={last} spawn_n={len(spawning)} first_seat={first_seat} last_seat={last_seat}"
    )

p("=== hour-window creep_ticks coverage LAST+1..TIP ===")
for room in ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7"):
    ticks = [
        r[0]
        for r in c.execute(
            "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick",
            (room, LAST + 1, TIP),
        ).fetchall()
    ]
    want = set(range(LAST + 1, TIP + 1))
    miss = sorted(want - set(ticks))
    spans = []
    span = None
    for tk in miss:
        if span and tk == span[1] + 1:
            span[1] = tk
        else:
            if span:
                spans.append((span[0], span[1], span[1] - span[0] + 1))
            span = [tk, tk]
    if span:
        spans.append((span[0], span[1], span[1] - span[0] + 1))
    p(room, "distinct", len(ticks), "want", TIP - LAST, "missing_spans", spans[:8], "nmiss", len(miss))

path = "/workspace/screeps/state/_patrol_2026-11-19_0117/traj.txt"
open(path, "w").write("\n".join(out) + "\n")
p("WROTE", path)
