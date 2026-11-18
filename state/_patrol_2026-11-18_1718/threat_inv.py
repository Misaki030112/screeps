#!/usr/bin/env python3
import json, sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()
LAST = 84337700

def p(*a):
    print(*a, flush=True)

for room in ("W46N8", "W47N8", "W47N7", "W45N8", "W45N7"):
    p("=======", room, "room_stats since", LAST, "=======")
    rows = c.execute(
        """
        SELECT tick, ts, progress, storage, energy, hostiles, sites, creeps, cpu, bucket
        FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick
        """,
        (room, LAST),
    ).fetchall()
    p("n", len(rows), "first", rows[0][:8] if rows else None, "last", rows[-1][:8] if rows else None)
    if not rows:
        continue
    if rows[0][3] is not None:
        st = [(r[0], r[1], r[3] or 0) for r in rows]
        p(" stor min", min(st, key=lambda x: x[2]), "max", max(st, key=lambda x: x[2]), "last", st[-1])
    h = [r for r in rows if (r[5] or 0) > 0]
    p(" hostiles samples", len(h))
    for r in h[:60]:
        p("  host", r[0], r[1], "host", r[5], "sites", r[6], "stor", r[3], "creeps", r[7])
    gaps = []
    for i in range(1, len(rows)):
        dt = rows[i][0] - rows[i - 1][0]
        if dt >= 30:
            wall = (rows[i][1] - rows[i - 1][1]).total_seconds()
            gaps.append((rows[i - 1][0], rows[i][0], dt, str(rows[i - 1][1]), str(rows[i][1]), wall))
    p(" gaps>=30t", gaps)
    sites = [r for r in rows if (r[6] or 0) > 0]
    p(" sites samples", len(sites), "first", sites[0][:7] if sites else None, "last", sites[-1][:7] if sites else None)

    def cnt(cr, role):
        if not cr:
            return 0
        if isinstance(cr, str):
            cr = json.loads(cr)
        return int(cr.get(role) or 0)

    if room in ("W46N8", "W47N8"):
        roles = ("upgrader", "w8upgrader", "w8defender", "w8guard", "defender", "rdef", "w8filler", "reserve7", "w8rminer")
        for role in roles:
            xs = [(r[0], r[1], cnt(r[7], role), r[3]) for r in rows]
            changes = []
            prev = None
            for t, ts, n, stv in xs:
                if prev is None or n != prev:
                    changes.append((t, str(ts), n, stv))
                    prev = n
            p(f"  {role} changes", changes)

p("======= tables =======")
tabs = [t[0] for t in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")]
p(tabs)

p("======= event-like tables since last =======")
for table in tabs:
    if any(k in table.lower() for k in ("event", "alert", "incident", "threat", "console", "error", "notify")):
        try:
            # discover tick-like col
            cols = [d[0] for d in c.execute(f"SELECT * FROM {table} LIMIT 0").description]
            p(table, "cols", cols)
            tickcol = next((x for x in cols if x in ("tick", "game_tick", "t")), None)
            if tickcol:
                n = c.execute(f"SELECT count(*) FROM {table} WHERE {tickcol}>=%s", (LAST,)).fetchone()[0]
                p("  n", n)
                if n:
                    rows = c.execute(f"SELECT * FROM {table} WHERE {tickcol}>=%s ORDER BY {tickcol} LIMIT 40", (LAST,)).fetchall()
                    for r in rows:
                        p(" ", dict(zip(cols, r)))
            else:
                n = c.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                p("  no tick col, total", n)
                if n and n < 50:
                    rows = c.execute(f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT 10").fetchall()
                    for r in rows:
                        p(" ", dict(zip(cols, r)))
        except Exception as e:
            p(table, "ERR", type(e).__name__, e)
            c.rollback()
