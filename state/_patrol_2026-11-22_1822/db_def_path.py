from collections import Counter, defaultdict
from tools.db import connect

c = connect()

# unique tick rows (earliest ts)
with c.cursor() as cur:
    cur.execute(
        """
        select distinct on (tick) tick, room, x, y, hits, store, state
        from creep_ticks
        where creep='defender84418409'
        order by tick, ts
        """
    )
    rows = cur.fetchall()

print("n", len(rows), "first", rows[0], "last", rows[-1])
print("--- path every ~25 ticks + room/state/hits changes ---")
prev = None
for i, r in enumerate(rows):
    tick, room, x, y, hits, store, state = r
    changed = (
        prev is None
        or room != prev[1]
        or state != prev[6]
        or hits != prev[4]
        or (tick - prev[0] >= 25)
        or i == len(rows) - 1
    )
    if changed:
        print(r)
    prev = r

# dwell tiles
print("--- top tiles ---")
tiles = Counter((r[1], r[2], r[3]) for r in rows)
for k, n in tiles.most_common(15):
    ticks = [r[0] for r in rows if (r[1], r[2], r[3]) == k]
    print(k, n, "range", ticks[0], ticks[-1])

print("--- states ---")
print(Counter(r[6] for r in rows))
print("--- rooms ---")
print(Counter(r[1] for r in rows))

# oscillation: same two tiles
print("--- consecutive unique positions (first 40 and last 40) ---")
path = [(r[0], r[1], r[2], r[3], r[6]) for r in rows]
# compress stays
comp = []
for p in path:
    if not comp or comp[-1][1:] != p[1:]:
        comp.append(p)
print("compressed steps", len(comp))
print("first 30 compressed:")
for p in comp[:30]:
    print(" ", p)
print("last 40 compressed:")
for p in comp[-40:]:
    print(" ", p)

# W45N7 any of our creeps / hostiles after 84418350
print("--- W45N7 creeps after 84418350 ---")
with c.cursor() as cur:
    cur.execute(
        """
        select creep, role, min(tick), max(tick), count(distinct tick),
               min(hits), max(hits),
               (array_agg(x order by tick))[1] x0,
               (array_agg(y order by tick))[1] y0,
               (array_agg(x order by tick desc))[1] x1,
               (array_agg(y order by tick desc))[1] y1,
               (array_agg(state order by tick desc))[1] st1
        from (
          select distinct on (creep, tick) creep, role, tick, x, y, hits, state
          from creep_ticks
          where room='W45N7' and tick>=84418350
          order by creep, tick, ts
        ) s
        group by creep, role
        order by min(tick)
        """
    )
    for r in cur.fetchall():
        print(r)

# events table?
print("--- event-like tables ---")
with c.cursor() as cur:
    cur.execute(
        """
        select table_name from information_schema.tables
        where table_schema='public' and (
          table_name ilike '%event%' or table_name ilike '%incident%'
          or table_name ilike '%threat%' or table_name ilike '%alert%'
          or table_name='room_stats'
        )
        order by 1
        """
    )
    print(cur.fetchall())
