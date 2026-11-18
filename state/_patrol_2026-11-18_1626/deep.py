#!/usr/bin/env python3
"""Deep dives for 15:22 patrol."""
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db

HK = ZoneInfo("Asia/Hong_Kong")
LAST_TIP, TIP = 84336020, 84336830
c = db.connect()

def p(*a):
    print(*a, flush=True)

def hk(ts):
    if ts is None:
        return None
    try:
        return ts.astimezone(HK)
    except Exception:
        return ts

p("=== storage extrema ===")
for room in ("W46N8", "W47N8"):
    for label, hours in (("3h", 3), ("6h", 6), ("12h", 12), ("13h", 13)):
        lo = TIP - int(hours * 3600 / 4.4)
        row = c.execute(
            """
            SELECT min(storage), max(storage)
            FROM room_stats
            WHERE room=%s AND tick BETWEEN %s AND %s AND storage IS NOT NULL
            """,
            (room, lo, TIP),
        ).fetchone()
        mn, mx = row
        tmin = c.execute(
            "SELECT tick, ts, storage FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s AND storage=%s ORDER BY tick LIMIT 1",
            (room, lo, TIP, mn),
        ).fetchone()
        tmax = c.execute(
            "SELECT tick, ts, storage FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s AND storage=%s ORDER BY tick LIMIT 1",
            (room, lo, TIP, mx),
        ).fetchone()
        p(f"  {room} {label} min={mn}@{tmin[0] if tmin else None} {hk(tmin[1]) if tmin else None} max={mx}@{tmax[0] if tmax else None} {hk(tmax[1]) if tmax else None}")
    for th in (20000, 40000):
        rows = c.execute(
            "SELECT tick, storage FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s AND storage IS NOT NULL ORDER BY tick",
            (room, TIP - int(13 * 3600 / 4.4), TIP),
        ).fetchall()
        best_span = 0
        start = None
        n = 0
        for t, s in rows:
            if s >= th:
                n += 1
                if start is None:
                    start = t
                best_span = max(best_span, t - start)
            else:
                start = None
        p(f"  {room} >={th} n_samples={n} best_tick_span={best_span}")

p("=== room_stats gaps >=30t last 2h ===")
for room in ("W46N8", "W47N8"):
    rows = c.execute(
        "SELECT tick, ts FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick",
        (room, LAST_TIP - 200, TIP + 20),
    ).fetchall()
    prev = None
    for t, ts in rows:
        if prev and t - prev[0] >= 30:
            dt = (ts - prev[1]).total_seconds() if ts and prev[1] else None
            p(f"  {room} {prev[0]}->{t} dtick={t-prev[0]} wall={dt:.1f}s {hk(prev[1])} -> {hk(ts)}")
        prev = (t, ts)

p("=== reserve7 creeps ===")
rows = c.execute(
    """
    SELECT tick, ts, name, room, x, y, role, ttl, spawning
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s
      AND (role IN ('reserve7','reserve') OR name ILIKE 'reserve%%')
    ORDER BY tick, name
    """,
    (LAST_TIP - 400, TIP + 50),
).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[2]].append(r)
p(f"  rows={len(rows)} names={list(by)}")
for name, ev in by.items():
    p(f"  {name} role={ev[0][6]} n={len(ev)}")
    p(f"    first t={ev[0][0]} {hk(ev[0][1])} {ev[0][3]} {ev[0][4]},{ev[0][5]} ttl={ev[0][7]} sp={ev[0][8]}")
    p(f"    last  t={ev[-1][0]} {hk(ev[-1][1])} {ev[-1][3]} {ev[-1][4]},{ev[-1][5]} ttl={ev[-1][7]} sp={ev[-1][8]}")
    ticks = [e[0] for e in ev]
    gaps = [(a, b, b - a) for a, b in zip(ticks, ticks[1:]) if b - a > 1]
    p(f"    intra gaps>1: {gaps[:10]} n={len(gaps)}")
    seated = [e for e in ev if e[3] == "W47N7" and e[4] == 39 and e[5] == 27]
    p(f"    seated_39,27 n={len(seated)} first={seated[0][0] if seated else None} last={seated[-1][0] if seated else None}")

# ticks in W47N7 with/without reserve7
p("=== reserve7 vs W47N7 coverage LAST_TIP..TIP ===")
cov = c.execute(
    """
    SELECT tick,
           bool_or(role='reserve7' OR name ILIKE 'reserve7%%') AS has_r7
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s AND room='W47N7'
    GROUP BY tick
    ORDER BY tick
    """,
    (LAST_TIP, TIP),
).fetchall()
has = [t for t, h in cov if h]
no = [t for t, h in cov if not h]
all_t = [t for t, _ in cov]
p(f"  W47N7 distinct ticks={len(all_t)} with_r7={len(has)} without={len(no)}")
# compress no into ranges
def ranges(xs):
    if not xs:
        return []
    out = []
    a = b = xs[0]
    for t in xs[1:]:
        if t == b + 1:
            b = t
        else:
            out.append((a, b, b - a + 1))
            a = b = t
    out.append((a, b, b - a + 1))
    return out
p(f"  without_r7 ranges: {ranges(no)}")
# also ticks missing entirely in W47N7
want = set(range(LAST_TIP, TIP + 1))
got = set(all_t)
miss = sorted(want - got)
p(f"  W47N7 missing ticks n={len(miss)} ranges={ranges(miss)[:12]}")

p("=== W47 upgraders this hour ===")
ups = c.execute(
    """
    SELECT tick, ts, name, room, x, y, ttl, spawning, energy
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s
      AND (role='w8upgrader' OR name ILIKE 'w8upgrader%%')
    ORDER BY tick, name
    """,
    (LAST_TIP - 200, TIP + 50),
).fetchall()
by = defaultdict(list)
for r in ups:
    by[r[2]].append(r)
p(f"  names={list(by)}")
for name, ev in sorted(by.items()):
    p(f"  {name} n={len(ev)}")
    p(f"    first t={ev[0][0]} {hk(ev[0][1])} {ev[0][3]} {ev[0][4]},{ev[0][5]} ttl={ev[0][7]} sp={ev[0][8]} e={ev[0][9]}")
    p(f"    last  t={ev[-1][0]} {hk(ev[-1][1])} {ev[-1][3]} {ev[-1][4]},{ev[-1][5]} ttl={ev[-1][7]} sp={ev[-1][8]} e={ev[-1][9]}")
    # spawn end, first seat near controller (x<=16,y<=30 in W47N8)
    walking = [e for e in ev if not e[8]]
    seats = [(12,25),(14,26),(14,27),(14,28),(13,26),(12,26),(13,25),(15,26),(15,27)]
    first_nonspawn = walking[0] if walking else None
    first_seat = next((e for e in ev if e[3]=='W47N8' and (e[4],e[5]) in seats), None)
    first_loaded = next((e for e in ev if e[3]=='W47N8' and (e[4],e[5]) in seats and (e[9] or 0)>=15), None)
    last_pos_unique = []
    prev = None
    for e in ev[::max(1,len(ev)//20)] + ev[-3:]:
        pos = (e[3], e[4], e[5])
        if pos != prev:
            last_pos_unique.append((e[0], hk(e[1]), pos, e[7], e[8], e[9]))
            prev = pos
    p(f"    first_nonspawn={None if not first_nonspawn else (first_nonspawn[0], first_nonspawn[3], first_nonspawn[4], first_nonspawn[5])}")
    p(f"    first_seat={None if not first_seat else (first_seat[0], first_seat[3], first_seat[4], first_seat[5], 'e', first_seat[9])}")
    if first_nonspawn and first_seat:
        p(f"    hatch_to_seat={first_seat[0]-first_nonspawn[0]}t spawn_tick~{name.replace('w8upgrader','')}")
    # path sample every 10t from hatch to seat
    if first_nonspawn and first_seat:
        path = [e for e in ev if first_nonspawn[0] <= e[0] <= first_seat[0]]
        p("    path:")
        for e in path[::5]:
            p(f"      {e[0]} {e[3]} {e[4]},{e[5]} ttl={e[7]} e={e[9]}")
        p(f"      LAST {first_seat[0]} {first_seat[3]} {first_seat[4]},{first_seat[5]}")

p("=== home upgraders this hour ===")
ups = c.execute(
    """
    SELECT tick, ts, name, room, x, y, ttl, spawning, energy
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s
      AND (role='upgrader' OR name ILIKE 'upgrader%%')
      AND name NOT ILIKE 'w8%%'
    ORDER BY tick, name
    """,
    (LAST_TIP - 50, TIP + 50),
).fetchall()
by = defaultdict(list)
for r in ups:
    by[r[2]].append(r)
p(f"  names={list(by)}")
for name, ev in sorted(by.items()):
    p(f"  {name} n={len(ev)} first={ev[0][0]} {ev[0][3]} {ev[0][4]},{ev[0][5]} sp={ev[0][8]} last={ev[-1][0]} {ev[-1][3]} {ev[-1][4]},{ev[-1][5]} ttl={ev[-1][7]}")
    seats = [(31,30),(30,30),(31,31),(30,31),(29,30),(32,30)]
    first_nonspawn = next((e for e in ev if not e[8]), None)
    first_seat = next((e for e in ev if e[3]=='W46N8' and (e[4],e[5]) in seats and not e[8]), None)
    p(f"    first_nonspawn={None if not first_nonspawn else (first_nonspawn[0], first_nonspawn[4], first_nonspawn[5])} first_seat={None if not first_seat else (first_seat[0], first_seat[4], first_seat[5])}")

p("=== W45N8/W45N7 reservers ===")
rows = c.execute(
    """
    SELECT tick, ts, name, room, x, y, role, ttl, spawning
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s AND (role='reserver' OR name ILIKE 'reserver%%')
    ORDER BY tick, name
    """,
    (LAST_TIP - 50, TIP + 50),
).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[2]].append(r)
p(f"  names={list(by)}")
for name, ev in sorted(by.items()):
    p(f"  {name} n={len(ev)} first={ev[0][0]} {hk(ev[0][1])} {ev[0][3]} {ev[0][4]},{ev[0][5]} ttl={ev[0][7]} last={ev[-1][0]} {hk(ev[-1][1])} {ev[-1][3]} {ev[-1][4]},{ev[-1][5]} ttl={ev[-1][7]}")

p("=== W47N7 miners / R1 R2 containers this hour (sample) ===")
rows = c.execute(
    """
    SELECT tick, ts, name, room, x, y, role, ttl, energy
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s AND (role='w8rminer' OR name ILIKE 'w8rminer%%')
    ORDER BY tick, name
    """,
    (LAST_TIP, TIP),
).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[2]].append(r)
p(f"  rminer names={list(by)}")
for name, ev in sorted(by.items()):
    p(f"  {name} n={len(ev)} first={ev[0][0]} {ev[0][3]} {ev[0][4]},{ev[0][5]} last={ev[-1][0]} {ev[-1][3]} {ev[-1][4]},{ev[-1][5]} ttl={ev[-1][7]}")
    # time in W47N8 vs W47N7 vs swamp-ish movement
    rooms = defaultdict(int)
    for e in ev:
        rooms[e[3]] += 1
    p(f"    rooms={dict(rooms)}")

p("=== defender84335584 this hour ===")
rows = c.execute(
    """
    SELECT tick, ts, room, x, y, ttl, hits
    FROM creep_ticks
    WHERE name='defender84335584' AND tick BETWEEN %s AND %s
    ORDER BY tick
    """,
    (LAST_TIP, TIP + 50),
).fetchall()
if rows:
    p(f"  n={len(rows)} first={rows[0][0]} {hk(rows[0][1])} {rows[0][2]} {rows[0][3]},{rows[0][4]} ttl={rows[0][5]} last={rows[-1][0]} {hk(rows[-1][1])} {rows[-1][2]} {rows[-1][3]},{rows[-1][4]} ttl={rows[-1][5]} hits={rows[-1][6]}")
    # room changes
    prev = None
    for r in rows:
        key = r[2]
        if key != prev:
            p(f"    enter {r[0]} {hk(r[1])} {r[2]} {r[3]},{r[4]}")
            prev = key
else:
    p("  no rows")

p("=== hostiles / incidents tables ===")
for table in ("incidents", "threat_incidents", "alerts", "events"):
    try:
        n = c.execute(f"SELECT count(*) FROM {table} WHERE tick BETWEEN %s AND %s", (LAST_TIP, TIP + 50)).fetchone()
        p(f"  {table} n={n}")
        if n and n[0] and n[0] < 20:
            cols = [d[0] for d in c.execute(f"SELECT * FROM {table} LIMIT 0").cursor.description] if False else None
    except Exception as e:
        p(f"  {table} ERR {type(e).__name__} {e}")

# try information_schema
tabs = c.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema='public' AND (table_name ILIKE '%incid%' OR table_name ILIKE '%alert%' OR table_name ILIKE '%threat%' OR table_name ILIKE '%event%')
    ORDER BY 1
""").fetchall()
p(f"  matching tables: {tabs}")

p("=== later room_stats after TIP ===")
for room in ("W46N8", "W47N8"):
    rows = c.execute(
        "SELECT tick, ts, storage, progress, cpu, bucket FROM room_stats WHERE room=%s AND tick>%s ORDER BY tick",
        (room, TIP),
    ).fetchall()
    p(f"  {room} later_n={len(rows)}")
    for r in rows[-3:]:
        p(f"    {r[0]} {hk(r[1])} stor={r[2]} p={r[3]} cpu={r[4]} bkt={r[5]}")

p("=== live listener creep_ticks freshness now ===")
for room in ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7"):
    row = c.execute("SELECT max(tick), max(ts), now()-max(ts) FROM creep_ticks WHERE room=%s", (room,)).fetchone()
    p(f"  {room} {row}")

p("DONE")
