from tools.db import connect
c = connect()
print('=== raw 84418570-84418610 ===')
with c.cursor() as cur:
    cur.execute('''select ts, tick, room, x, y, hits, state, commit from creep_ticks where creep=%s and tick between %s and %s order by tick, ts''', ('defender84418409', 84418570, 84418610))
    for r in cur.fetchall():
        print(r)
print('=== around 84418690-84418700 ===')
with c.cursor() as cur:
    cur.execute('''select ts, tick, room, x, y, hits, state, commit from creep_ticks where creep=%s and tick between %s and %s order by tick, ts''', ('defender84418409', 84418690, 84418700))
    for r in cur.fetchall():
        print(r)
print('=== around 84418890-84418910 ===')
with c.cursor() as cur:
    cur.execute('''select ts, tick, room, x, y, hits, state, commit from creep_ticks where creep=%s and tick between %s and %s order by tick, ts''', ('defender84418409', 84418890, 84418910))
    for r in cur.fetchall():
        print(r)
print('=== incidents cols and recent ===')
with c.cursor() as cur:
    cur.execute("select column_name from information_schema.columns where table_name='incidents' order by 1")
    print('incidents cols', [x[0] for x in cur.fetchall()])
    cur.execute('select * from incidents order by tick desc nulls last limit 8')
    print('inc desc', [d.name for d in cur.description])
    for r in cur.fetchall():
        print(r)
print('=== events cols ===')
with c.cursor() as cur:
    cur.execute("select column_name from information_schema.columns where table_name='events' order by 1")
    print('events cols', [x[0] for x in cur.fetchall()])
